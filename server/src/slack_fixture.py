"""Larger synthetic review for checking batch navigation and exceptions."""

def load_slack_fixture(reviews):
    policies = {
        "SLACK-HR": ("Verified offboarding roster", "Employment ended. Remove standard channel memberships."),
        "SLACK-PROJECT": ("Current project assignment", "Current project assignment covers standard project channels."),
    }
    for ref, (title, reason) in policies.items():
        reviews.sources[ref] = {
            "id": ref, "title": title, "excerpt": reason, "version": 1,
            "source_system": "Synthetic Slack policy and directory",
            "effective_from": "2026-11-07", "observed_at": "2026-11-07T15:00:00Z", "item_ids": [],
        }
    for i in range(240):
        item_id = f"SLACK-{i+1:03}"
        ref = "SLACK-HR" if i < 144 else "SLACK-PROJECT"
        channel = ("#operations", "#project-launch", "#team-help", "#release")[i % 4]
        item = {
            "id": item_id, "review_id": reviews.campaign_id, "person": f"Member {i // 4 + 1:02}",
            "entitlement": channel, "access_type": "Channel membership", "snapshot_version": 1, "allowed_actions": ["retain", "revoke"],
            "batch_eligible": True, "evidence_refs": [ref], "insight_categories": [],
        }
        if i % 17 == 0:
            item.update(restricted=True, entitlement="#restricted-incident",
                        open_questions=["Does the restricted-channel exception still apply?"])
        elif i % 19 == 0:
            item["open_questions"] = ["Can the channel owner verify the current assignment?"]
        reviews.items[item_id] = item
        reviews.sources[ref]["item_ids"].append(item_id)
        reviews.recommendations[item_id] = {
            "item_id": item_id, "outcome": "reject" if i < 144 else "accept",
            "basis": policies[ref][1], "snapshot_version": 1, "recorded_at": "2026-11-07T15:00:00Z",
        }
