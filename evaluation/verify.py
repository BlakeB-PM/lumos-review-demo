"""Exercise the demo via its stdio MCP transport using isolated SQLite state."""

import json
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

SERVER = Path(__file__).resolve().parents[1] / "server/src/main.py"
PERSONAL_SERVER = SERVER.with_name("personal_context.py")


@contextmanager
def client(state, *options, scenario="warehouse"):
    command = [sys.executable, str(PERSONAL_SERVER), *options] if state is None else [
        sys.executable, str(SERVER), "--state", str(state), *options,
        *(["--scenario", scenario] if scenario else []),
    ]
    with subprocess.Popen(
        command,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding="utf-8",
    ) as process:
        request_id = 0

        def rpc(method, **params):
            nonlocal request_id
            request_id += 1
            request = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
            process.stdin.write(json.dumps(request) + "\n")
            process.stdin.flush()
            response = json.loads(process.stdout.readline())
            assert response["id"] == request_id, response
            return response["result"]

        handshake = rpc("initialize", protocolVersion="2025-11-25", capabilities={},
                        clientInfo={"name": "demo-verifier", "version": "1.0"})
        assert handshake["protocolVersion"] == "2025-11-25"
        process.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
        process.stdin.flush()

        def tool(name, error=False, **arguments):
            result = rpc("tools/call", name=name, arguments=arguments)
            payload = result["content"][0]["text"]
            assert result.get("isError", False) == error, payload
            return payload if error else json.loads(payload)

        try:
            yield rpc, tool
        finally:
            process.stdin.close()
            assert process.wait(timeout=10) == 0


def operator(state, command):
    subprocess.run([sys.executable, str(SERVER), command, "--state", str(state),
                    "--scenario", "warehouse"], check=True)


@contextmanager
def browser_report(state, scenario="warehouse"):
    with subprocess.Popen(
        [sys.executable, str(SERVER), "report", "--port", "0", "--state", str(state),
         *(["--scenario", scenario] if scenario else [])],
        stdout=subprocess.PIPE, text=True, encoding="utf-8",
    ) as process:
        try:
            url = process.stdout.readline().removeprefix("Audit report: ").strip()
            with urlopen(url, timeout=5) as response:
                assert b"Audit activity" in response.read()

            def snapshot():
                with urlopen(url + "api/report", timeout=5) as response:
                    assert response.headers["Cache-Control"] == "no-store"
                    return json.load(response)

            def record(payload, origin=None, path="api/decisions"):
                request = Request(url + path, data=json.dumps(payload).encode(),
                                  headers={"Content-Type": "application/json",
                                           "Origin": origin or url.rstrip("/")})
                with urlopen(request, timeout=5) as response:
                    return json.load(response)

            yield snapshot, record
        finally:
            process.terminate()
            process.wait(timeout=10)



def verify_transport(state, scenario):
    with client(state, scenario=scenario) as (rpc, tool):
        discovered=rpc('tools/list')['tools']
        names={t['name'] for t in discovered}
        assert names == {'open_access_review','get_review_group','get_review_context','get_evidence',
            'search_review_evidence','prepare_review_batch','record_review_batch','defer_review_items','get_review_status'}
        assert not any(word in json.dumps(discovered) for word in ('Alex','Dana','invoice_follow_up','preview_offboarding'))
        uri=discovered[0]['_meta']['ui']['resourceUri']
        assert 'Edit decisions' in rpc('resources/read',uri=uri)['contents'][0]['text']
        opening=tool('open_access_review'); review=opening['review']; rid=review['review_id']; run=review['run_id']
        assert sum(g['count'] for g in review['groups'])==review['pending']
        assert tool('open_access_review')['review']['run_id']==run
        assert 'unavailable' in tool('open_access_review',review_id='OTHER',error=True)
        items=[]
        for g in review['groups']:
            cursor=0
            while True:
                page=tool('get_review_group',review_id=rid,group_id=g['id'],cursor=cursor,limit=3)
                items.extend(page['items']);cursor=page['next_cursor']
                if cursor is None:break
        assert len({i['id'] for i in items})==review['total']
        assert 'unavailable' in tool('get_review_context',review_id=rid,item_ids=['OTHER'],error=True)
        assert tool('get_evidence',evidence_ids=['PRIVATE'])['records']==[]
        briefs=tool('get_review_context',review_id=rid,item_ids=[i['id'] for i in items])['briefs']
        assert all(b['context_status']=='not_assessed' and b['evidence'] for b in briefs)
        first=items[0]
        decision={'item_id':first['id'],'snapshot_version':first['snapshot_version'],
            'outcome':first['allowed_actions'][0],'reason':'Verified against the current scoped policy.',
            'evidence_refs':first['evidence_refs'],'assessment_source':'personal_agent'}
        args={'review_id':rid,'run_id':run,'decisions':[decision]}
        assert tool('prepare_review_batch',**(args|{'decisions':[decision,decision]}),error=True)
        assert tool('prepare_review_batch',**(args|{'decisions':[decision|{'evidence_refs':[]}]}),error=True)
        assert tool('prepare_review_batch',**(args|{'decisions':[decision|{'transcript':'private'}]}),error=True)
        draft=tool('prepare_review_batch',**args)
        assert tool('open_access_review')['review']['recorded']==0
        assert draft['decisions'][0]['reason']==decision['reason']
        with client(state,'--assistant-host','claude_cowork',scenario=scenario) as (_,other):
            assert 'unavailable' in other('record_review_batch',proposal_id=draft['proposal_id'],error=True)
        recorded=tool('record_review_batch',proposal_id=draft['proposal_id'])
        assert recorded['results'][0]['status']=='recorded'
        assert tool('record_review_batch',proposal_id=draft['proposal_id'])==recorded
        assert tool('prepare_review_batch',**args,error=True)
        second=items[1]
        deferred=tool('defer_review_items',review_id=rid,run_id=run,item_ids=[second['id']],reason='Current owner assignment is unverified.')
        assert deferred['review']['deferred']==1 and deferred['review']['recorded']==1
        deferred_group=tool('get_review_group',review_id=rid,group_id='deferred')
        assert deferred_group['items'][0]['id']==second['id']
        status=tool('get_review_status',review_id=rid)
        assert status['recorded'][0]['receipt_id']==recorded['results'][0]['receipt_id']
        with browser_report(state,scenario=scenario) as (report,post):
            assert report()['items'][0]['id'] in {i['id'] for i in items}
            browser_decision={'item_id':second['id'],'snapshot_version':second['snapshot_version'],
                'outcome':second['allowed_actions'][0],'reason':'Reviewer verified policy eligibility.',
                'evidence_refs':second['evidence_refs'],'assessment_source':'reviewer'}
            preview=post({'review_id':rid,'run_id':run,'decisions':[browser_decision]},path='api/prepare')
            assert report()['items'] and tool('open_access_review')['review']['recorded']==1
            result=post({'proposal_id':preview['proposal_id']},path='api/record')
            assert result['results'][0]['status']=='recorded'
            assert tool('open_access_review')['review']['deferred']==0
            for path,payload in [('api/record',{'proposal_id':preview['proposal_id']}),('api/reset',{'run_id':run})]:
                try:post(payload,origin='https://example.com',path=path)
                except HTTPError as e:assert e.code==403
                else:raise AssertionError('Cross-origin write accepted')
            post({'run_id':run},path='api/reset')
            assert tool('record_review_batch',proposal_id=draft['proposal_id'],error=True)
            assert tool('open_access_review')['review']['recorded']==0
    return names


def verify_generalization(state):
    sys.path.insert(0,str(SERVER.parent))
    from reviews import Reviews
    from chatgpt_review import ReviewWorkflow
    from copy import deepcopy
    r=Reviews(state,scenario='warehouse')
    # Entirely different identities, grants and policy: same workflow, no server branches.
    r.reviewer={'id':'reviewer-robin','name':'Robin Chen'}
    r.items={};r.recommendations={};r.sources={}
    for n in range(4):
        key=f'NEW-{n}'; ref=f'POL-{n}'
        r.items[key]={'id':key,'review_id':r.campaign_id,'person':f'Person {n}',
            'entitlement':f'Build permission {n}','snapshot_version':1,'evidence_refs':[ref],
            'allowed_actions':['retain','revoke'],'open_questions':['Is the current on-call assignment active?']}
        r.recommendations[key]={'item_id':key,'outcome':'accept','basis':'Recorded on-call assignment.', 'snapshot_version':1}
        r.sources[ref]={'id':ref,'title':'Build operations policy','version':1,'item_ids':[key],
            'effective_from':'2026-11-01','source_system':'Fixture','excerpt':'Current on-call engineers may retain access.'}
    w=ReviewWorkflow(r); start=w.open_access_review()['review'];rid=r.campaign_id;run=start['run_id']
    assert start['reviewer']=='Robin Chen' and start['groups'][0]['count']==4
    def d(n,outcome='retain'):
        return {'item_id':f'NEW-{n}','snapshot_version':1,'outcome':outcome,'reason':'Current assignment checked against policy.',
            'evidence_refs':[f'POL-{n}'],'assessment_source':'personal_agent'}
    # Agreement, reversal, and a generic optional summary all use the same schema.
    a=d(0);b=d(1,'revoke')|{'context_summary':'Reviewer verified that build operations duties ended.'}
    proposal=w.prepare_review_batch(rid,run,[a,b])
    assert [x['stance'] for x in proposal['decisions']]==['agree','different']
    # A source changes without changing the item version: only that row is blocked.
    r.sources['POL-1']['excerpt']='New requirement: owner approval is also required.'
    result=w.record_review_batch(proposal['proposal_id'])
    assert [x['status'] for x in result['results']]==['recorded','refresh_required']
    assert w.record_review_batch(proposal['proposal_id'])['results']==result['results']
    assert result['results'][0]['reviewer_id']=='reviewer-robin'
    fresh=w.prepare_review_batch(rid,run,[b]); receipt=w.record_review_batch(fresh['proposal_id'])['results'][0]
    assert receipt['context_summary']==b['context_summary'] and 'not_verified_by_lumos' in receipt['context_authority']
    # Missing/conflicting evidence is represented by a durable unresolved state, not a fake decision.
    w.defer_review_items(rid,run,['NEW-2'],'Assignment evidence conflicts; ask the owner to clarify.')
    assert w.open_access_review()['review']['deferred']==1
    expiry=w.prepare_review_batch(rid,run,[d(2)])
    with r.db(write=True) as db:
        db.execute("UPDATE proposal_guards SET expires_at='2000-01-01T00:00:00+00:00' WHERE id=?",(expiry['proposal_id'],))
    assert w.record_review_batch(expiry['proposal_id'])['results'][0]['status']=='proposal_expired'
    # Successful receipt retries remain recoverable after expiry.
    with r.db(write=True) as db:
        db.execute("UPDATE proposal_guards SET expires_at='2000-01-01T00:00:00+00:00'")
    assert w.record_review_batch(fresh['proposal_id'])['results'][0]==receipt
    pending=w.prepare_review_batch(rid,run,[d(3)])
    r.items['NEW-3']['snapshot_version']=2
    assert w.record_review_batch(pending['proposal_id'])['results'][0]['status']=='refresh_required'
    # Fresh proposal cannot be used by a different principal even with the same client label.
    blocked=w.prepare_review_batch(rid,run,[d(2)])
    r.reviewer={'id':'other','name':'Someone else'}
    try:w.record_review_batch(blocked['proposal_id'])
    except ValueError:pass
    else:raise AssertionError('Reviewer binding missing')


def verify_large_queue(state):
    with client(state, scenario="slack") as (_, tool):
        review = tool("open_access_review")["review"]
        assert review["total"] == 240 and len(review["groups"]) == 3
        scope = {"review_id": review["review_id"]}
        assert sum(g["count"] for g in review["groups"]) == 240
        ready = [g for g in review["groups"] if g["batch_ready"]]
        assert {g["outcome"] for g in ready} == {"retain", "revoke"}
        assert review["recommended_group"] == ready[0]["id"]
        decisions = []
        for group in ready:
            page = tool("get_review_group", **scope, group_id=group["id"])
            assert len(page["items"]) == 25 and page["next_cursor"] == 25 and page["sources"]
            assert all(not row.get("restricted") and not row.get("open_questions") for row in page["items"])
            for row in page["items"]:
                decisions.append(dict(item_id=row["id"], snapshot_version=row["snapshot_version"],
                    outcome=group["outcome"], reason=group["reason"], evidence_refs=row["evidence_refs"]))
        preview = tool("prepare_review_batch", **scope, run_id=review["run_id"], decisions=decisions)
        assert len(preview["decisions"]) == 50 and preview["review"]["recorded"] == 0
        recorded = tool("record_review_batch", proposal_id=preview["proposal_id"])
        assert recorded["review"]["pending"] == 190
        assert all(row["status"] == "recorded" for row in recorded["results"])


if __name__ == '__main__':
    from uuid import uuid4
    import shutil
    # mkdir avoids Windows TemporaryDirectory ACL inheritance problems in restricted shells.
    scratch=SERVER.parents[2] / 'work' / ('verify-'+str(uuid4()))
    scratch.mkdir(parents=True)
    try:
        schemas=[verify_transport(scratch/(scenario+'.sqlite3'),scenario) for scenario in ('chatgpt','tour','warehouse')]
        assert schemas[0]==schemas[1]==schemas[2]
        verify_generalization(scratch/'new-identities.sqlite3')
        verify_large_queue(scratch/'slack.sqlite3')
    finally:
        shutil.rmtree(scratch)
    print('PASS: generic tools across three fixtures; arbitrary identities; pagination; scope; editable proposals; browser confirmation; deferrals; receipts; idempotency; expiry; reviewer/client binding; partial and stale evidence writes; reset isolation; 240-grant Slack queue and combined confirmation.')
