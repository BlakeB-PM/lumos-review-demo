"""The focused 17-grant campaign used by the ChatGPT plugin."""

from reviews import DATA, read_json


OFFBOARDING_EVIDENCE = "AD-HRIS-OFFBOARDING"
ACCOUNTS_RECEIVABLE = "AD-ACCOUNTS-RECEIVABLE"
FINANCE_ADMIN = "AD-FINANCE-ADMIN"


def load_chatgpt_fixture(reviews):
    fixture = read_json(DATA / "chatgpt-offboarding.json")
    date = fixture["effective_on"]
    grants = fixture["grants"]
    reason = "HR confirmed employment ended. Offboarding policy requires removal of remaining access."
    items = {}
    recommendations = {}
    for item_id, person, entitlement in grants:
        items[item_id] = {
            "id": item_id, "review_id": reviews.campaign_id, "person": person,
            "entitlement": entitlement, "snapshot_version": 1, "employment_status": "Terminated",
            "insight_categories": ["Terminated"], "key_facts": [f"HR verified termination effective {date}."],
            "batch_eligible": True, "allowed_actions": ["revoke"], "evidence_refs": [OFFBOARDING_EVIDENCE],
        }
        recommendations[item_id] = {
            "item_id": item_id, "outcome": "reject", "basis": reason, "snapshot_version": 1,
            "recorded_at": f"{date}T18:00:00Z",
        }
    reviews.items = items | {key: reviews.items[key] for key in (ACCOUNTS_RECEIVABLE, FINANCE_ADMIN)}
    reviews.recommendations = recommendations | {
        key: reviews.recommendations[key] for key in (ACCOUNTS_RECEIVABLE, FINANCE_ADMIN)
    }
    roster = "\n".join(f"- {person} · {entitlement}" for _, person, entitlement in grants)
    reviews.sources[OFFBOARDING_EVIDENCE] = {
        "id": OFFBOARDING_EVIDENCE, "title": "Verified HR offboarding roster and access policy",
        "source_system": "Synthetic HRIS and access policy", "version": 1,
        "item_ids": list(items), "effective_from": date, "effective_to": None,
        "observed_at": f"{date}T18:00:00Z",
        "excerpt": f"{reason}\n\nVerified effective {date} for the people and grants below.\n{roster}",
    }
    reviews.campaigns[reviews.campaign_id]["scope"] = "Review remaining offboarding grants and Alex Rivera’s access."
