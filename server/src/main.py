import argparse
import json
import sys
from pathlib import Path

from reviews import ROOT, SCENARIOS, Reviews


def string(max_length=200):
    return {"type": "string", "minLength": 1, "maxLength": max_length}


def integer(minimum=0, maximum=1000):
    return {"type": "integer", "minimum": minimum, "maximum": maximum}


def array(items, max_items=20):
    return {"type": "array", "items": items, "minItems": 1, "maxItems": max_items}


def obj(required=None, **properties):
    return {"type": "object", "properties": properties, "required": list(required or ()),
            "additionalProperties": False}


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
        "Stage and validate an exact decision proposal for human review. Does not record any decision.",
        obj(("review_id", "run_id", "decisions"), review_id=ID, run_id=ID, decisions=array(DECISION, 50)),
    ),
    "record_review_batch": (
        "Record exactly the previously staged proposal. Call only after the human sees its items, outcomes "
        "and evidence and explicitly confirms that exact proposal. A retry returns the same receipts.",
        obj(("proposal_id",), proposal_id=ID),
    ),
}


def validate(value, schema, path="arguments"):
    kind = schema.get("type")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path} is outside the allowed values.")
    if kind == "object":
        if not isinstance(value, dict):
            raise ValueError(f"{path} must be an object.")
        fields = schema["properties"]
        if set(value) - fields.keys() or set(schema["required"]) - value.keys():
            raise ValueError(f"{path} has missing or unsupported fields.")
        for key, entry in value.items():
            validate(entry, fields[key], f"{path}.{key}")
    if kind == "array":
        if not isinstance(value, list) or not schema["minItems"] <= len(value) <= schema["maxItems"]:
            raise ValueError(f"{path} has an invalid list length.")
        for entry in value:
            validate(entry, schema["items"], f"{path}[]")
    if kind == "string" and (not isinstance(value, str) or not value.strip()
                             or not schema["minLength"] <= len(value) <= schema["maxLength"]):
        raise ValueError(f"{path} must be a nonempty string of the allowed length.")
    if kind == "integer" and (type(value) is not int or not schema["minimum"] <= value <= schema["maximum"]):
        raise ValueError(f"{path} must be an integer in the allowed range.")
    if kind == "boolean" and type(value) is not bool:
        raise ValueError(f"{path} must be a boolean.")


def send(response):
    print(json.dumps({"jsonrpc": "2.0", **response}, ensure_ascii=True), flush=True)


def serve(reviews, assistant_host=None):
    tools = dict(TOOLS)
    instructions = (
        "Synthetic access reviews. When the user asks to start by saying "
        "'Help me complete my access review', call start_demo before any review reads. "
        "For Active Directory, open sales-handoff.md from the personal agent's project sources. "
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
    for line in sys.stdin.buffer:
        try:
            request = json.loads(line)
        except (ValueError, UnicodeError):
            send({"id": None, "error": {"code": -32700, "message": "Invalid JSON."}})
            continue
        if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" or not isinstance(request.get("method"), str):
            send({"id": None, "error": {"code": -32600, "message": "Invalid request."}})
            continue
        if "id" not in request:
            continue
        response = {"id": request["id"]}
        params = request.get("params", {})
        if not isinstance(params, dict):
            send({**response, "error": {"code": -32602, "message": "Invalid parameters."}})
            continue
        method = request["method"]
        if method == "initialize":
            requested = params.get("protocolVersion")
            supported = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
            result = {"protocolVersion": requested if requested in supported else supported[0],
                      "capabilities": {"tools": {}},
                      "serverInfo": {"name": "lumos-review-demo", "version": "1.0.0"},
                      "instructions": instructions}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": [
                {"name": name, "description": description, "inputSchema": schema,
                 "annotations": {"readOnlyHint": name not in ("submit_decisions", "start_demo", *ASSISTANT_TOOLS),
                                 "destructiveHint": name in ("start_demo", "record_review_batch"),
                                 "idempotentHint": name not in ("ask_albus", "start_demo", "prepare_review_batch"),
                                 "openWorldHint": False}}
                for name, (description, schema) in tools.items()
            ]}
        elif method == "tools/call":
            try:
                name = params.get("name")
                if not isinstance(name, str) or name not in tools:
                    raise ValueError("Tool unavailable in this mode.")
                arguments = params.get("arguments", {})
                validate(arguments, tools[name][1])
                if name in ASSISTANT_TOOLS:
                    arguments = {**arguments, "client": assistant_host}
                data = getattr(reviews, name)(**arguments)
                result = {"content": [{"type": "text", "text": json.dumps(data)}]}
            except ValueError as error:
                result = {"isError": True, "content": [{"type": "text", "text": str(error)}]}
            except Exception:
                result = {"isError": True, "content": [
                    {"type": "text", "text": "Local server error. Retry the same submission and key if needed."}
                ]}
        else:
            send({**response, "error": {"code": -32601, "message": "Method not found."}})
            continue
        send({**response, "result": result})


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
