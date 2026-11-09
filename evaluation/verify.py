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


def run(state, report, record):
    review = {"review_id": "Q4-DATA"}
    with client(state) as (rpc, tool):
        assert len(rpc("tools/list")["tools"]) == 7
        assert "unavailable" in tool("ask_albus", error=True)
        campaigns = tool("list_my_reviews")["records"]
        assert [c["id"] for c in campaigns] == ["Q4-DATA"]
        assert campaigns[0]["counts"]["pending"] == 8
        assert "unavailable" in tool("get_review_items", review_id="OTHER", error=True)
        assert "unsupported" in tool("list_my_reviews", reviewer_id="reviewer-other", error=True)
        page = tool("get_review_items", **review, limit=4)
        run_id = page["run_id"]
        assert page["next_cursor"] == 4
        items = page["records"] + tool("get_review_items", **review, cursor=4)["records"]
        assert len({i["person"] for i in items}) == 6
        assert len({i["id"] for i in items}) == 8
        assert [i["original_recommendation"]["outcome"] for i in items] == [
            "accept", "accept", "accept", "accept", "reject", "review", "accept", "review",
        ]
        assert {category for i in items for category in i["insight_categories"]} == {
            "Role Aligned", "Inactive", "Unusual Access",
        }
        initial_report = report()
        assert initial_report["run_id"] == run_id
        assert len(initial_report["items"]) == 8
        assert not initial_report["events"]
        evidence = tool("get_evidence", evidence_ids=["PRIVATE", "OBS-AR-107-V2", "POL-READER"])
        assert evidence["unavailable"] == ["PRIVATE", "OBS-AR-107-V2"]
        assert evidence["records"][0]["id"] == "POL-READER"
        found = tool("search_review_evidence", **review, item_id="AR-105", query="Atlas migration exception")
        assert found["records"][0]["id"] == "EX-MIGRATION"
        assert found["records"][0]["effective_to"] > campaigns[0]["as_of"]
        found = tool("search_review_evidence", **review, item_id="AR-106", query="export exception")
        assert found["records"][0]["id"] == "EX-EXPIRED"
        assert found["records"][0]["effective_to"] < campaigns[0]["as_of"]

        decisions = [
            {"item_id": i["id"], "snapshot_version": i["snapshot_version"],
             "outcome": "retain", "reason": "Fixture-backed verification.",
             "evidence_refs": i["evidence_refs"]}
            for i in items if i["id"] not in ("AR-106", "AR-108")
        ]
        decisions[4]["evidence_refs"].append("EX-MIGRATION")
        batch = {**review, "decisions": decisions, "idempotency_key": "rehearsal", "run_id": run_id}
        assert "confirmation" in tool("submit_decisions", **batch, reviewer_confirmed=False, error=True)
        assert tool("get_review_status", **review)["counts"]["recorded"] == 0
        operator(state, "advance-snapshot")
        result = tool("submit_decisions", **batch, reviewer_confirmed=True)
        assert [r["status"] for r in result["results"]] == ["recorded"] * 5 + ["refresh_required"]
        assert result["results"][4]["original_recommendation"]["outcome"] == "reject"
        assert result["results"][4]["evidence"][-1] == {"id": "EX-MIGRATION", "version": 1}
        assert tool("submit_decisions", **batch, reviewer_confirmed=True) == result
        audit = report()
        assert len(audit["events"]) == 6
        assert audit["events"][0]["status"] == "refresh_required"
        nora = next(i for i in audit["items"] if i["id"] == "AR-105")
        assert nora["receipt"] == result["results"][4]
        assert nora["original_recommendation"]["outcome"] == "reject"
        exception = next(s for s in nora["evidence_sources"] if s["id"] == "EX-MIGRATION")
        assert exception["version"] == 1 and "SEC-217" in exception["excerpt"]
        assert "different payload" in tool("submit_decisions", **(batch | {"decisions": decisions[:1]}),
                                            reviewer_confirmed=True, error=True)

    with client(state) as (_, tool):
        assert tool("submit_decisions", **batch, reviewer_confirmed=True) == result
        status = tool("get_review_status", **review)
        assert status["counts"] == {"recorded": 5, "pending": 3, "failed_pending": 1}
        assert status["pending"] == ["AR-106", "AR-107", "AR-108"]
        assert status["failed_pending"][0]["current_snapshot_version"] == 2
        refreshed = next(i for i in tool("get_review_items", **review, status="pending")["records"]
                         if i["id"] == "AR-107")
        assert refreshed["original_recommendation"]["snapshot_version"] == 1
        assert "OBS-AR-107-V2" in refreshed["evidence_refs"]
        corrected = {"item_id": "AR-107", "snapshot_version": 2, "outcome": "revoke",
                     "reason": "Owner closed the sandbox assignment.", "evidence_refs": ["OBS-AR-107-V2"]}
        forbidden = {**corrected, "item_id": "AR-999"}
        wrong_scope = {**corrected, "item_id": "AR-108", "snapshot_version": 1}
        browser_batch = {**review, "reviewer_confirmed": True, "idempotency_key": "refreshed",
                         "decisions": [corrected, forbidden, wrong_scope], "run_id": run_id}
        try:
            record(browser_batch, origin="https://example.com")
        except HTTPError as error:
            assert error.code == 403
        else:
            raise AssertionError("Cross-origin review write was accepted")
        result = record(browser_batch)["results"]
        assert [r["status"] for r in result] == ["recorded", "item_unavailable", "invalid_evidence"]
        assert result[0]["remediation_status"] == "not_performed_in_simulation"
        assert result[0]["client"] == "local_review_ui"
        assert record(browser_batch)["results"] == result
        assert result[0] in tool("get_review_status", **review)["recorded"]

    with client(state, "--simulated-albus") as (rpc, tool):
        assert len(rpc("tools/list")["tools"]) == 8
        investigation = {"item_id": "AR-106", "snapshot_version": 1, "question": "Was the exception renewed?"}
        result = tool("ask_albus", **investigation)
        assert result["mode"] == "fixture_simulation"
        assert result["status"] == "needs_context"
        assert result["source_refs"][0]["id"] == "EX-EXPIRED"
        assert result["usage"]["model_calls"] == 0
        shared = {"claim": "The project team expects a renewal.", "source": "Project notes",
                  "date": "2026-11-07", "sharing_intent": "share_for_this_investigation"}
        result = tool("ask_albus", **investigation, shared_context=shared)
        assert result["status"] == "insufficient_evidence"
        assert shared["claim"] not in json.dumps(result)
        assert tool("get_review_status", **review)["counts"]["recorded"] == 6

    with client(state) as (_, tool):
        tool("start_demo", trigger_phrase="show my receipts", error=True)
        assert tool("get_review_status", **review)["counts"]["recorded"] == 6
        restarted = tool("start_demo", trigger_phrase="Help me complete my access review")
        assert restarted["run_id"] != run_id
        assert restarted["counts"] == {"recorded": 0, "pending": 8, "failed_pending": 0}
        assert report()["run_id"] == restarted["run_id"]
        assert not report()["events"]
        assert all(item["snapshot_version"] == 1 for item in restarted["items"])
        assert "restarted" in tool("submit_decisions", **batch, reviewer_confirmed=True, error=True)
        fresh = batch | {"run_id": restarted["run_id"], "decisions": decisions[:1]}
        assert tool("submit_decisions", **fresh, reviewer_confirmed=True)["results"][0]["status"] == "recorded"
        again = tool("start_demo", trigger_phrase="Help me complete my access review")
        assert again["run_id"] != restarted["run_id"]
        assert again["counts"]["pending"] == 8
        assert tool("get_review_status", **review)["counts"]["recorded"] == 0

    operator(state, "reset")
    with client(state) as (_, tool):
        assert tool("get_review_status", **review)["counts"] == {
            "recorded": 0, "pending": 8, "failed_pending": 0,
        }
        assert tool("get_evidence", evidence_ids=["OBS-AR-107-V2"])["records"] == []


def verify_assistant(state, report, record):
    review = {"review_id": "Q4-DATA"}
    with client(state, "--assistant-host", "chatgpt_work") as (rpc, tool):
        tools = {t["name"]: t for t in rpc("tools/list")["tools"]}
        assert "start_demo" not in tools and "submit_decisions" not in tools
        assert not tools["record_review_batch"]["annotations"]["readOnlyHint"]
        assert tools["record_review_batch"]["annotations"]["destructiveHint"]
        page = tool("get_review_items", **review, status="pending")
        run_id = page["run_id"]
        assert tool("list_my_reviews")["records"][0]["counts"]["pending"] == 8
        search = tool("search_review_evidence", **review, item_id="AR-105", query="SEC-217")
        assert [source["id"] for source in search["records"]] == ["EX-MIGRATION"]
        assert "primary cutover operator" in search["records"][0]["excerpt"]
        nora = {"item_id": "AR-105", "snapshot_version": 1, "outcome": "retain",
                "reason": "The Security exception covers the exact grant.",
                "evidence_refs": ["EX-MIGRATION", "POL-ELEVATED"],
                "context_summary": "Reviewer confirmed Nora is the primary operator for the November 12 cutover."}
        sandbox = {"item_id": "AR-107", "snapshot_version": 1, "outcome": "retain",
                   "reason": "Original snapshot shows an active assignment.",
                   "evidence_refs": ["POL-SANDBOX"]}
        prepared = tool("prepare_review_batch", **review, run_id=run_id, decisions=[nora, sandbox])
        assert prepared["status"] == "awaiting_confirmation"
        assert not report()["events"]
        assert prepared["decisions"][0]["original_recommendation"] == "reject"
        assert tool("record_review_batch", proposal_id="missing", error=True)
        assert tool("record_review_batch", proposal_id=prepared["proposal_id"], decisions=[nora], error=True)
        with client(state, "--assistant-host", "claude_cowork") as (_, cowork):
            assert cowork("record_review_batch", proposal_id=prepared["proposal_id"], error=True)

        operator(state, "advance-snapshot")
        written = tool("record_review_batch", proposal_id=prepared["proposal_id"])
        assert [r["status"] for r in written["results"]] == ["recorded", "refresh_required"]
        assert written["results"][0]["client"] == "chatgpt_work"
        assert written["results"][0]["context_summary"] == nora["context_summary"]
        assert tool("record_review_batch", proposal_id=prepared["proposal_id"]) == written
        assert len(report()["events"]) == 2
        assert next(row for row in report()["items"] if row["id"] == "AR-105")["receipt"] == written["results"][0]

        sandbox.update(snapshot_version=2, outcome="revoke", reason="The assignment is closed.",
                       evidence_refs=["OBS-AR-107-V2"])
        browser = record({**review, "run_id": run_id, "idempotency_key": "ui-after-work",
                          "reviewer_confirmed": True, "decisions": [sandbox]})
        assert browser["results"][0] in tool("get_review_status", **review)["recorded"]
        operator(state, "reset")
        assert tool("record_review_batch", proposal_id=prepared["proposal_id"], error=True)

    with client(state, "--assistant-host", "claude_cowork") as (_, cowork):
        run_id = cowork("get_review_items", **review)["run_id"]
        prepared = cowork("prepare_review_batch", **review, run_id=run_id, decisions=[nora])
        written = cowork("record_review_batch", proposal_id=prepared["proposal_id"])
        assert written["results"][0]["client"] == "claude_cowork"


def verify_default(state, report):
    with client(state, scenario=None) as (_, codex):
        started = codex("start_demo", trigger_phrase="Help me complete my access review")
        review = {"review_id": started["campaign"]["id"]}
        run_id = started["run_id"]
        assert started["campaign"]["app"] == "Active Directory"
        assert [(row["entitlement"], row["original_recommendation"]["outcome"])
                for row in started["items"][:2]] == [("Finance Admin", "reject"), ("Accounts Receivable", "accept")]
        assert started["counts"]["pending"] == 36
        assert len({row["person"] for row in started["items"]}) == 18
        assert report()["run_id"] == run_id and all(row["receipt"] is None for row in report()["items"])
        decisions = [
            {"item_id": row["id"], "snapshot_version": row["snapshot_version"],
             "outcome": "revoke", "evidence_refs": row["evidence_refs"],
             "reason": ("No current business need under the invoice follow-up policy."
                        if row["entitlement"] == "Accounts Receivable" else row["original_recommendation"]["basis"])}
            for row in started["items"][:2]
        ]
        for row in decisions:
            evidence = codex("get_evidence", evidence_ids=row["evidence_refs"])
            assert row["item_id"] in evidence["records"][0]["item_ids"]
        invoice_policy = codex("get_evidence", evidence_ids=["AD-INVOICE-POLICY"])["records"][0]
        assert "currently handle" in invoice_policy["excerpt"]
        hub_entry = codex("get_evidence", evidence_ids=["AD-KH-SALES"])["records"][0]
        assert hub_entry["source_system"] == "Simulated Lumos Knowledge Hub"
        assert "Sales Ops" not in hub_entry["excerpt"]
        assert not codex("search_review_evidence", **review, query="Casey Brooks")["records"]
        assert not codex("get_evidence", evidence_ids=["DANA-SALES-HANDOFF"])["records"]

        with client(None) as (rpc, personal):
            tools = rpc("tools/list")["tools"]
            assert [tool["name"] for tool in tools] == ["search_personal_context"]
            assert tools[0]["annotations"]["readOnlyHint"]
            result = personal("search_personal_context", person="Alex Rivera", topic="invoice follow-up")
            assert result["results"][0]["source_id"] == "DANA-SALES-HANDOFF"
            assert "Sales Ops handles" in result["results"][0]["excerpt"]
            assert not personal("search_personal_context", person="Alex Rivera", topic="parking")["results"]
            assert not personal("search_personal_context", person="Jordan Lee", topic="invoice")["results"]

        with client(state, "--assistant-host", "chatgpt_work", scenario=None) as (_, work):
            assert work("list_my_reviews")["records"][0]["counts"]["pending"] == 36
            first = work("get_review_items", **review, status="pending", limit=20)
            second = work("get_review_items", **review, status="pending", cursor=first["next_cursor"], limit=20)
            assert second["next_cursor"] is None
            assert len({row["id"] for row in first["records"] + second["records"]}) == 36
            proposal = work("prepare_review_batch", **review, run_id=run_id, decisions=decisions)
            assert proposal["decisions"][1]["original_recommendation"] == "accept"
            assert proposal["decisions"][1]["outcome"] == "revoke"
            assert report()["events"] == []
            work("record_review_batch", proposal_id=proposal["proposal_id"])

        rows = report()["items"]
        assert [(row["receipt"]["outcome"], row["receipt"]["reason"]) for row in rows if row["receipt"]] == [
            (entry["outcome"], entry["reason"]) for entry in decisions]
        assert rows[1]["original_recommendation"]["outcome"] == "accept"
        assert "Casey Brooks" not in json.dumps(report())
        assert codex("get_review_status", **review)["counts"]["pending"] == 34


def verify_chatgpt(state, report, post):
    with client(state, "--assistant-host", "chatgpt_work", scenario="chatgpt") as (rpc, tool):
        tools = {entry["name"]: entry for entry in rpc("tools/list")["tools"]}
        uri = tools["open_access_review"]["_meta"]["ui"]["resourceUri"]
        assert rpc("resources/list")["resources"][0]["uri"] == uri
        resource = rpc("resources/read", uri=uri)["contents"][0]
        assert resource["mimeType"] == "text/html;profile=mcp-app"
        assert "ui/initialize" in resource["text"] and "Check my work context" in resource["text"]
        assert "left to review" in resource["text"] and "Suggested review order" in resource["text"]
        assert "Work context to save with this decision" in resource["text"]
        assert "Knowledge Hub follow-up" not in resource["text"]
        assert tools["preview_offboarding_batch"]["annotations"]["readOnlyHint"]
        assert not tools["record_review_batch"]["annotations"]["readOnlyHint"]
        assert "start_demo" not in tools and "submit_decisions" not in tools

        opening = rpc("tools/call", name="open_access_review")["structuredContent"]
        assert opening["view"] == "overview" and "decisions" not in opening
        opened = opening["review"]
        assert opened["total"] == 17 and opened["recorded"] == 0
        assert opened["groups"] == {"offboarding": 15, "alex": 2}
        assert opened["recommended_group"] == "offboarding"
        assert report()["run_id"] == opened["run_id"] and len(report()["items"]) == opened["total"]
        run = {"run_id": opened["run_id"]}
        roster = tool("get_review_group", group="offboarding")
        assert len(roster["items"]) == 15 and "HR confirmed" in roster["albus_basis"]
        ids = [item["id"] for item in roster["items"]]
        by_id = {item["id"]: item for item in report()["items"]}
        assert [(by_id[item["id"]]["person"], by_id[item["id"]]["entitlement"]) for item in roster["items"]] == [
            (item["person"], item["entitlement"]) for item in roster["items"]
        ]
        assert "outside" in tool("preview_offboarding_batch", **run, item_ids=["AD-ACCOUNTS-RECEIVABLE"], error=True)
        excluded = tool("preview_offboarding_batch", **run, item_ids=ids[:-1])
        assert [row["item_id"] for row in excluded["decisions"]] == ids[:-1]
        proposal = tool("preview_offboarding_batch", **run, item_ids=ids)
        assert len(proposal["decisions"]) == 15
        assert all(row["stance"] == "agree" and row["outcome"] == "revoke" for row in proposal["decisions"])
        assert report()["events"] == []
        token = proposal["batch_token"]
        assert "invalid" in tool("record_review_batch", batch_token=token + "x", error=True)
        bulk = tool("record_review_batch", batch_token=token)
        assert bulk["review"]["groups"] == {"offboarding": 0, "alex": 2}
        assert bulk["review"]["recorded"] == 15
        assert bulk["review"]["recommended_group"] == "alex"
        browser_receipts = {item["id"]: item["receipt"] for item in report()["items"] if item["receipt"]}
        assert browser_receipts.keys() == set(ids)
        assert all(browser_receipts[row["item_id"]]["receipt_id"] == row["receipt_id"] and
                   browser_receipts[row["item_id"]]["outcome"] == "revoke" for row in bulk["results"])
        assert tool("record_review_batch", batch_token=token) == bulk
        assert tool("open_access_review")["review"]["run_id"] == opened["run_id"]

        with client(None, "--transcript") as (_, personal):
            transcript = personal("search_personal_context", person="Alex Rivera", topic="invoice follow-up")["results"][0]
            assert transcript["source_type"] == "call_transcript"
            assert "Sales Ops owns invoice" in transcript["excerpt"]
            assert not tool("get_evidence", evidence_ids=[transcript["source_id"]])["records"]

        alex = tool("get_review_group", group="alex")
        assert [item["original_recommendation"]["outcome"] for item in alex["items"]] == ["accept", "reject"]
        ids_and_codes = zip(alex["items"], ["no_current_invoice_duty", "no_finance_admin_assignment"])
        judgments = [{"item_id": item["id"], "snapshot_version": item["snapshot_version"],
                      "reason_code": code} for item, code in ids_and_codes]
        handoff = "invoice_follow_up_transferred_to_sales_ops"
        assert "unsupported fields" in tool("preview_alex_batch", **run, error=True,
                                            judgments=[judgments[0] | {"transcript": transcript["excerpt"]}])
        assert "does not apply" in tool("preview_alex_batch", **run, error=True,
                                        judgments=[judgments[0] | {"reason_code": judgments[1]["reason_code"]}])
        assert "does not apply" in tool("preview_alex_batch", **run, error=True,
                                        judgments=[judgments[1] | {"work_context": handoff}])
        assert "outside the allowed values" in tool("preview_alex_batch", **run, error=True,
                                                   judgments=[judgments[0] | {"work_context": transcript["excerpt"]}])
        without_context = tool("preview_alex_batch", **run, judgments=judgments)
        assert all("context_summary" not in row for row in without_context["decisions"])
        judgments[0]["work_context"] = handoff
        proposal = tool("preview_alex_batch", **run, judgments=judgments)
        assert [row["stance"] for row in proposal["decisions"]] == ["disagree", "agree"]
        summary = proposal["decisions"][0]["context_summary"]
        assert "Sales Ops took over invoice follow-up" in summary and "part of the handoff" in summary
        assert "context_summary" not in proposal["decisions"][1]
        assert tool("open_access_review")["review"]["recorded"] == 15
        final = tool("record_review_batch", batch_token=proposal["batch_token"])
        assert final["review"]["recorded"] == 17 and final["review"]["pending"] == 0
        assert final["results"][0]["context_summary"] == summary
        audit = report()
        assert len(audit["events"]) == 17
        ar = next(item for item in audit["items"] if item["id"] == "AD-ACCOUNTS-RECEIVABLE")
        assert ar["original_recommendation"]["outcome"] == "accept" and ar["receipt"]["outcome"] == "revoke"
        assert ar["receipt"]["context_summary"] == summary
        finance = next(item for item in audit["items"] if item["id"] == "AD-FINANCE-ADMIN")
        assert "context_summary" not in finance["receipt"]
        assert all(value not in json.dumps(audit) for value in (transcript["source_id"], "Casey Brooks", "transition call"))
        try:
            post(run, origin="https://example.com", path="api/reset")
        except HTTPError as error:
            assert error.code == 403
        else:
            raise AssertionError("A cross-origin reset was accepted")
        assert len(report()["events"]) == 17
        restarted = post(run, path="api/reset")
        assert restarted["run_id"] != run["run_id"]
        try:
            post(run, path="api/reset")
        except HTTPError as error:
            assert error.code == 409
        else:
            raise AssertionError("A stale reset was accepted")
        clean = report()
        assert clean["run_id"] == restarted["run_id"] and not clean["events"]
        assert len(clean["items"]) == 17 and all(item["receipt"] is None for item in clean["items"])
        assert "restarted" in tool("record_review_batch", batch_token=proposal["batch_token"], error=True)
        assert tool("open_access_review")["review"]["recorded"] == 0


if __name__ == "__main__":
    scratch = SERVER.parents[1] / 'state'
    scratch.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=scratch) as temp:
        state = Path(temp) / "test.sqlite3"
        with browser_report(state) as (report, record):
            run(state, report, record)
            verify_assistant(state, report, record)
        state = Path(temp) / "tour.sqlite3"
        with browser_report(state, scenario="tour") as (report, _):
            verify_default(state, report)
        state = Path(temp) / "chatgpt.sqlite3"
        with browser_report(state, scenario=None) as (report, post):
            verify_chatgpt(state, report, post)
    print("PASS: 36-permission tour, stdio discovery, reviewer scope, evidence, confirmation, partial/stale writes, "
          "idempotency, clean runs, simulation, browser round trip, Work/Cowork MCP proposals, and the 17-grant ChatGPT app.")
