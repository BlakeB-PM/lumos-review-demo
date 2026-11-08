"""Exercise the demo via its stdio MCP transport using isolated SQLite state."""

import json
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen

SERVER = Path(__file__).resolve().parents[1] / "server/src/main.py"


@contextmanager
def client(state, *options):
    with subprocess.Popen(
        [sys.executable, str(SERVER), "--state", str(state), *options],
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
    subprocess.run([sys.executable, str(SERVER), command, "--state", str(state)], check=True)


@contextmanager
def browser_report(state):
    with subprocess.Popen(
        [sys.executable, str(SERVER), "report", "--port", "0", "--state", str(state)],
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

            yield snapshot
        finally:
            process.terminate()
            process.wait(timeout=10)


def run(state, report):
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
        result = tool("submit_decisions", **review, reviewer_confirmed=True, idempotency_key="refreshed",
                      decisions=[corrected, forbidden, wrong_scope], run_id=run_id)["results"]
        assert [r["status"] for r in result] == ["recorded", "item_unavailable", "invalid_evidence"]
        assert result[0]["remediation_status"] == "not_performed_in_simulation"

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


if __name__ == "__main__":
    scratch = SERVER.parents[1] / 'state'
    scratch.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=scratch) as temp:
        state = Path(temp) / "test.sqlite3"
        with browser_report(state) as report:
            run(state, report)
    print("PASS: stdio discovery, reviewer scope, evidence, confirmation, partial/stale writes, "
          "idempotency across process restarts, phrase-triggered clean runs, simulation and live audit report.")
