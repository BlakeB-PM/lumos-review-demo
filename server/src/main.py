import argparse
import json
from pathlib import Path

from mcp_stdio import array, integer, obj, serve_stdio, string, validate
from reviews import ROOT, SCENARIOS, Reviews


ID = string()
VERSION = integer(1)
PAGING = {"cursor": integer(), "limit": integer(1, 20)}
DECISION = obj(
    ("item_id", "snapshot_version", "outcome", "reason", "evidence_refs"),
    item_id=ID, snapshot_version=VERSION, outcome=string(), reason=string(800),
    evidence_refs=array(ID), investigation_id=ID, context_summary=string(400),
)
TOOLS = {
    "start_demo": ("Reset this local synthetic review and open its clean campaign. Call only when the "
                   "user says 'Help me complete my access review' as a request to start.",
                   obj(("trigger_phrase",),
                       trigger_phrase={"enum": ["Help me complete my access review"]})),
    "list_my_reviews": ("List campaigns assigned to the fixed synthetic reviewer.",
                        obj(status=string(), **PAGING)),
    "get_review_items": ("Read assigned items with exact entitlements and recorded recommendations.",
                         obj(("review_id",), review_id=ID, status={"enum": ["pending", "recorded"]}, **PAGING)),
    "get_evidence": ("Retrieve authorized source excerpts, dates, scope and versions by ID.",
                     obj(("evidence_ids",), evidence_ids=array(ID))),
    "search_review_evidence": ("Search authorized evidence and policy within a campaign or item.",
                               obj(("review_id", "query"), review_id=ID, item_id=ID,
                                   query=string(500), limit=integer(1, 20))),
    "submit_decisions": ("Record explicit local decisions only after the human confirms this exact batch. "
                         "Repeat an identical payload and key to recover its receipts.",
                         obj(("review_id", "decisions", "idempotency_key", "reviewer_confirmed", "run_id"),
                             review_id=ID, decisions=array(DECISION, 50), idempotency_key=ID,
                             reviewer_confirmed={"type": "boolean"}, run_id=ID)),
    "get_review_status": ("Read decision receipts, pending items, failed pending writes and remediation status.",
                          obj(("review_id",), review_id=ID)),
}
ALBUS = ("Run a clearly labeled scripted investigation for a specific unresolved policy question. "
         "Use only context the human expressly permits sharing.",
         obj(("item_id", "snapshot_version", "question"), item_id=ID, snapshot_version=VERSION,
             question=string(800), shared_context=obj(
                 ("claim", "source", "date", "sharing_intent"), claim=string(500),
                 source=string(), date=string(40), sharing_intent={"enum": ["share_for_this_investigation"]},
             )))
ASSISTANT_TOOLS = {
    "prepare_review_batch": (
        "Stage and validate an exact decision proposal for human review. Copy run_id verbatim from "
        "the latest get_review_items result. If the run changed, refresh and retry before asking "
        "for confirmation. Does not record any decision.",
        obj(("review_id", "run_id", "decisions"), review_id=ID, run_id=ID, decisions=array(DECISION, 50)),
    ),
    "record_review_batch": (
        "Record exactly the previously staged proposal. Call only after the human sees its items, outcomes "
        "and evidence and explicitly confirms that exact proposal. A retry returns the same receipts.",
        obj(("proposal_id",), proposal_id=ID),
    ),
}


def serve(reviews, assistant_host=None):
    tools = dict(TOOLS)
    instructions = (
        "Synthetic access reviews. When the user asks to start by saying "
        "'Help me complete my access review', call start_demo before any review reads. "
        "For Active Directory, first call search_personal_context on the separate Dana Personal Context "
        "connector for Alex Rivera and invoice follow-up if that connector is available. "
        "In a local demo project, explicitly open context/sales-handoff.md under personal-workspace "
        "before deciding that context is missing. Compare the original suggestion with the current "
        "permission policy and the handoff. Summarize routine grants, review exceptions first, and honor "
        "the user's chosen decision scope. If the handoff is missing, "
        "ask for it instead of assuming duties changed. Explain any reversal in plain English, "
        "keep raw personal context in the host, and obtain explicit confirmation before writing. "
        "After recording a confirmed Accounts Receivable reversal, suggest a separate IT request to "
        "verify the handoff and update the Active Directory review context in the Lumos Knowledge Hub. "
        "Show an unsent draft without personal details."
    )
    if assistant_host:
        for name in ("start_demo", "submit_decisions"):
            del tools[name]
        tools.update(ASSISTANT_TOOLS)
        instructions = (ROOT.parent / "reviewer-skill/SKILL.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
    elif reviews.albus is not None:
        tools["ask_albus"] = ALBUS
    def call(name, arguments):
        if name in ASSISTANT_TOOLS:
            arguments = {**arguments, "client": assistant_host}
        return getattr(reviews, name)(**arguments)

    serve_stdio("lumos-review-demo", instructions, tools, call,
                writes=("submit_decisions", "start_demo", *ASSISTANT_TOOLS),
                destructive=("start_demo", "record_review_batch"),
                non_idempotent=("ask_albus", "start_demo", "prepare_review_batch"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local Lumos review simulator")
    parser.add_argument("action", choices=["serve", "reset", "advance-snapshot", "report"], nargs="?", default="serve")
    parser.add_argument("--state", type=Path)
    parser.add_argument("--scenario", choices=SCENARIOS, default="tour")
    parser.add_argument("--simulated-albus", action="store_true")
    parser.add_argument("--assistant-host", choices=["chatgpt_work", "claude_cowork"],
                        help="Expose the reviewer workflow without demo reset or direct submission")
    parser.add_argument("--port", type=int, default=8765, help="Local audit report port")
    parser.add_argument("--open", action="store_true", help="Open the audit report in your browser")
    args = parser.parse_args()
    if args.simulated_albus or args.action == "advance-snapshot":
        args.scenario = "warehouse"
    state_name = "tour.sqlite3" if args.scenario == "tour" else "demo.sqlite3"
    reviews = Reviews(args.state or ROOT / "state" / state_name, args.simulated_albus, args.scenario)
    if args.action == "reset":
        reviews.reset()
        print("Demo decisions, investigations, attempts and snapshot changes cleared.")
    elif args.action == "advance-snapshot":
        print(json.dumps(reviews.advance_sandbox_snapshot()))
    elif args.action == "report":
        from report import serve_report

        serve_report(reviews, args.port, args.open, TOOLS["submit_decisions"][1], validate)
    else:
        serve(reviews, args.assistant_host)
