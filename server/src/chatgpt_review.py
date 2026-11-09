"""ChatGPT MCP App tools for the bulk offboarding and Alex review."""

import base64
import binascii
import hmac
import json
from secrets import token_bytes

from chatgpt_fixture import ACCOUNTS_RECEIVABLE, FINANCE_ADMIN, OFFBOARDING_EVIDENCE
from mcp_stdio import array, integer, obj, serve_stdio, string
from reviews import REMEDIATION, ROOT


RESOURCE_URI = "ui://lumos/access-review-v3.html"
MIME_TYPE = "text/html;profile=mcp-app"
CLIENT = "chatgpt_work"
HANDOFF_FINDING = "invoice_follow_up_transferred_to_sales_ops"
HANDOFF_SUMMARY = (
    "A work call confirmed that Sales Ops took over invoice follow-up and that the recent invoice lookup "
    "was part of the handoff. That activity no longer indicates an ongoing need for Accounts Receivable access."
)
JUDGMENTS = {
    "no_current_invoice_duty": (ACCOUNTS_RECEIVABLE, "revoke",
                               "No current invoice follow-up responsibility under the Accounts Receivable access policy."),
    "current_invoice_duty": (ACCOUNTS_RECEIVABLE, "retain",
                            "Current invoice follow-up responsibility meets the Accounts Receivable access policy."),
    "no_finance_admin_assignment": (FINANCE_ADMIN, "revoke",
                                    "Finance Admin is reserved for Finance administrators. No assignment was verified."),
}
TOOLS = {
    "open_access_review": (
        "Open or resume the assigned access review when the reviewer asks to start, do or complete it. "
        "Shows the full queue, progress, and suggested order. For an opening request, show this overview "
        "and wait for the reviewer to choose a group. Never resets the review.", obj(),
    ),
    "get_review_group": (
        "Open one group after the reviewer chooses it in the panel or in chat. "
        "Offboarding shows the exact HR-verified rejection roster. "
        "Alex shows both grants and Albus's recommendation and rationale.", obj(("group",), group={"enum": ["offboarding", "alex"]}),
    ),
    "get_evidence": (
        "Read Lumos policy, activity and scoped evidence by ID. Use this to verify the basis of a decision.",
        obj(("evidence_ids",), evidence_ids=array(string())),
    ),
    "preview_offboarding_batch": (
        "After the reviewer inspects a group and asks to preview, show Reject for the exact selected grants. "
        "Use the current run ID and exact selected item IDs. This does not record decisions.",
        obj(("run_id", "item_ids"), run_id=string(), item_ids=array(string(), 15)),
    ),
    "preview_alex_batch": (
        "Show ChatGPT's comparison with Albus and preview only the decisions supported by evidence. "
        "Read Lumos evidence and check the separate private work context first for Accounts Receivable. "
        "Use reason codes and include work_context only for a verified, decision-relevant finding. "
        "Set it to invoice_follow_up_transferred_to_sales_ops only if the call confirms the handoff "
        "and explains the lookup. The reviewer sees the resulting summary before confirmation. "
        "Omit any grant awaiting evidence. This does not record decisions.",
        obj(("run_id", "judgments"), run_id=string(), judgments=array(
            obj(("item_id", "snapshot_version", "reason_code"), item_id=string(),
                snapshot_version=integer(1), reason_code={"enum": list(JUDGMENTS)},
                work_context={"enum": [HANDOFF_FINDING]}), 2)),
    ),
    "record_review_batch": (
        "Record exactly the signed batch the reviewer saw and explicitly confirmed. Call only after confirmation. "
        "Retry the same token to recover receipts. Never change the selection without a fresh preview.",
        obj(("batch_token",), batch_token=string(20000)),
    ),
}
INSTRUCTIONS = """For a general request to start, do or complete an access review, call only open_access_review
and end the turn after the overview. Show total, recorded and remaining counts, and how many grants are
in each remaining group. Recommend a starting group and wait for the reviewer to choose. Do not load
a roster, investigate Alex, preview, or ask for confirmation on this opening turn.

Once the reviewer chooses a group, show that group and let them inspect or change its selection. Preview
only when requested. Obtain explicit confirmation of the exact preview before recording decisions. Then
show progress from the receipts and recommend the next step.

For Alex Rivera, read get_review_group(group="alex") and retrieve its Lumos evidence. For Accounts Receivable,
search the separate Dana Personal Context connector for Alex Rivera and invoice follow-up, or read the
authorized call transcript supplied in the ChatGPT project. The private transcript can explain the recent
lookup. Verify eligibility against the Lumos policy. If work context is unavailable or inconclusive, leave
Accounts Receivable pending and say what evidence is needed. Do not assume there was a handoff.

Compare each proposed judgment with Albus. Use preview_alex_batch for the supported judgments so the reviewer
sees the exact grants, original rationale, ChatGPT's judgment, audit reason and proposed actions in the panel.
Keep the transcript, speaker, title, excerpts and private source ID out of every Lumos call. If the work
call confirms the Sales Ops transfer and explains the lookup, pass work_context=invoice_follow_up_transferred_to_sales_ops
on Accounts Receivable so the reviewer can approve the summary as part of that decision. Leave work_context
off grants it did not inform. Explain how the finding changes Albus's interpretation of the lookup.
Respect exclusions and leave unresolved grants pending.

If the investigation exposes a useful update to shared review guidance, you may suggest it in conversation
when relevant. Record only synthetic review decisions. Access removal is simulated."""


class ChatGPTReview:
    def __init__(self, reviews):
        self.reviews = reviews
        with reviews.db(write=True) as db:
            db.execute("CREATE TABLE IF NOT EXISTS chatgpt_signing_key (id INTEGER PRIMARY KEY, secret BLOB NOT NULL)")
            db.execute("INSERT OR IGNORE INTO chatgpt_signing_key VALUES (1, ?)", (token_bytes(32),))
            self.secret = db.execute("SELECT secret FROM chatgpt_signing_key WHERE id = 1").fetchone()[0]

    def overview(self, db):
        reviews = self.reviews
        recorded = {row[0] for row in db.execute("SELECT item_id FROM decisions")}
        pending = [item for item in reviews.items.values() if item["id"] not in recorded]
        bulk = sum(OFFBOARDING_EVIDENCE in item["evidence_refs"] for item in pending)
        context_people = {item["person"] for item in pending if OFFBOARDING_EVIDENCE not in item["evidence_refs"]}
        return {
            "run_id": reviews.run_id(db),
            "review_id": reviews.campaign_id,
            "title": reviews.campaign(reviews.campaign_id)["title"],
            "total": len(reviews.items),
            "people": len({item["person"] for item in reviews.items.values()}),
            "recorded": len(reviews.items) - len(pending),
            "pending": len(pending),
            "groups": {"offboarding": bulk, "alex": len(pending) - bulk},
            "recommended_group": "offboarding" if bulk else "alex" if pending else None,
            "context_review_label": next(iter(context_people)) if len(context_people) == 1 else "Individual review",
        }

    def open_access_review(self):
        with self.reviews.db() as db:
            db.execute("BEGIN")
            return {"view": "overview", "review": self.overview(db)}

    def get_review_group(self, group):
        reviews = self.reviews
        with reviews.db() as db:
            db.execute("BEGIN")
            overview = self.overview(db)
            recorded = {row[0] for row in db.execute("SELECT item_id FROM decisions")}
            items = [
                reviews.item_record(db, item, "pending") for item in reviews.items.values()
                if item["id"] not in recorded and (OFFBOARDING_EVIDENCE in item["evidence_refs"]) == (group == "offboarding")
            ]
        if group == "offboarding":
            items = [{"id": item["id"], "person": item["person"], "entitlement": item["entitlement"]} for item in items]
            basis = reviews.recommendations[items[0]["id"]]["basis"] if items else ""
            return {"view": group, "review": overview, "items": items, "albus_basis": basis,
                    "evidence_ids": [OFFBOARDING_EVIDENCE]}
        return {"view": group, "review": overview, "items": items}

    def preview_offboarding_batch(self, run_id, item_ids):
        reviews = self.reviews
        with reviews.db() as db:
            db.execute("BEGIN")
            reviews.require_current_run(db, run_id)
            decisions = []
            for item_id in item_ids:
                item = reviews.items.get(item_id)
                evidence = reviews.source_for(db, OFFBOARDING_EVIDENCE, item_id) if item else None
                if not evidence or item["employment_status"] != "Terminated":
                    raise ValueError("The selection includes a grant outside the verified offboarding group.")
                decisions.append({
                    "item_id": item_id, "snapshot_version": reviews.version(db, item_id), "outcome": "revoke",
                    "reason": reviews.recommendations[item_id]["basis"], "evidence_refs": [OFFBOARDING_EVIDENCE],
                })
            return self.preview(db, run_id, decisions, "offboarding")

    def preview_alex_batch(self, run_id, judgments):
        reviews = self.reviews
        with reviews.db() as db:
            db.execute("BEGIN")
            reviews.require_current_run(db, run_id)
            decisions = []
            for judgment in judgments:
                item_id, outcome, reason = JUDGMENTS[judgment["reason_code"]]
                if item_id != judgment["item_id"]:
                    raise ValueError("That reason does not apply to this grant.")
                decision = {"item_id": item_id, "snapshot_version": judgment["snapshot_version"],
                            "outcome": outcome, "reason": reason,
                            "evidence_refs": reviews.items[item_id]["evidence_refs"]}
                if "work_context" in judgment:
                    if judgment["reason_code"] != "no_current_invoice_duty":
                        raise ValueError("The work-context finding does not apply to this judgment.")
                    decision["context_summary"] = HANDOFF_SUMMARY
                decisions.append(decision)
            return self.preview(db, run_id, decisions, "alex")

    def preview(self, db, run_id, decisions, group):
        reviews = self.reviews
        rows = reviews.preview_decisions(db, reviews.campaign_id, decisions)
        for row in rows:
            recommendation = reviews.recommendations[row["item_id"]]
            outcome = "reject" if row["outcome"] == "revoke" else "accept"
            row["albus_basis"] = recommendation["basis"]
            row["stance"] = "agree" if outcome == recommendation["outcome"] else "disagree"
        payload = json.dumps([run_id, decisions], separators=(",", ":")).encode()
        token = base64.urlsafe_b64encode(payload).decode() + "." + hmac.digest(self.secret, payload, "sha256").hex()
        return {"view": "proposal", "group": group, "review": self.overview(db),
                "batch_token": token, "decisions": rows}

    def record_review_batch(self, batch_token):
        encoded, separator, signature = batch_token.partition(".")
        try:
            payload = base64.b64decode(encoded, altchars=b"-_", validate=True)
        except (ValueError, binascii.Error):
            raise ValueError("This batch preview is invalid. Open a new preview.") from None
        expected = hmac.digest(self.secret, payload, "sha256").hex()
        if not separator or not hmac.compare_digest(expected.encode(), signature.encode()):
            raise ValueError("This batch preview is invalid. Open a new preview.")
        run_id, decisions = json.loads(payload)
        result = self.reviews.submit_decisions(self.reviews.campaign_id, decisions, expected, True, run_id, CLIENT)
        overview = self.open_access_review()
        if overview["review"]["run_id"] != run_id:
            raise ValueError("The demo restarted. Open the current review.")
        return {**overview, "results": [
            {key: row[key] for key in ("item_id", "status", "receipt_id", "outcome", "context_summary") if key in row}
            for row in result["results"]
        ], "remediation_status": REMEDIATION}

    def get_evidence(self, evidence_ids):
        return self.reviews.get_evidence(evidence_ids)


def serve_chatgpt(reviews):
    workflow = ChatGPTReview(reviews)
    panel = ROOT / "chatgpt" / "review.html"
    serve_stdio(
        "lumos-access-reviews", INSTRUCTIONS, TOOLS, lambda name, args: getattr(workflow, name)(**args),
        writes=("record_review_batch",), destructive=("record_review_batch",),
        resources={RESOURCE_URI: (
            {"uri": RESOURCE_URI, "name": "Lumos access review", "mimeType": MIME_TYPE},
            lambda: panel.read_text(encoding="utf-8"),
        )},
        tool_resources={name: RESOURCE_URI for name in TOOLS if name != "get_evidence"},
        structured=True,
    )
