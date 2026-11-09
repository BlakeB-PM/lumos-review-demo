"""Local synthetic adapter for the shared access review workflow."""
import argparse
from pathlib import Path
from chatgpt_review import DECISION, serve_chatgpt
from mcp_stdio import array, obj, string, validate
from reviews import ROOT, SCENARIOS, Reviews

# Kept for the browser API until its two-stage preview is handled by the shared workflow.
DECISION_REQUEST = obj(("review_id", "decisions", "idempotency_key", "reviewer_confirmed", "run_id"),
    review_id=string(), decisions=array(DECISION, 50), idempotency_key=string(),
    reviewer_confirmed={"type": "boolean"}, run_id=string())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["serve", "reset", "advance-snapshot", "report"], nargs="?", default="serve")
    parser.add_argument("--state", type=Path)
    parser.add_argument("--scenario", choices=SCENARIOS, default="chatgpt", help="Synthetic data only; tools are identical for every fixture.")
    parser.add_argument("--assistant-host", choices=["chatgpt_work", "claude_cowork"], default="chatgpt_work", help="Receipt attribution only; workflow is host-neutral.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()
    state_name = {"tour": "tour.sqlite3", "warehouse": "demo.sqlite3", "chatgpt": "chatgpt.sqlite3", "slack": "slack.sqlite3"}[args.scenario]
    reviews = Reviews(args.state or ROOT / "state" / state_name, scenario=args.scenario)
    if args.action == "reset":
        reviews.reset()
        print("Synthetic review reset. Decisions and audit activity cleared.")
    elif args.action == "advance-snapshot":
        print(reviews.advance_sandbox_snapshot())
    elif args.action == "report":
        from report import serve_report
        serve_report(reviews, args.port, args.open, DECISION_REQUEST, validate)
    else:
        serve_chatgpt(reviews, args.assistant_host)
