# Shared tool contract

All fixture scenarios and host profiles expose the same tools. The host flag affects receipt attribution only. Structured results advertise `ui://lumos/access-review-v11.html` for overview, group, proposal and progress views; text-only hosts receive the same facts.

| Tool | Contract |
| --- | --- |
| open_access_review | Resume the assigned campaign; optional review ID is checked against scope. Return counts, dynamically generated groups and a suggested starting group. |
| get_review_group | Campaign and group ID, optional cursor/limit. Return exact paginated grants, original recommendations and allowed actions. |
| get_review_context | Campaign and exact item IDs. Return decision briefs, scoped source excerpts and dates, open questions, and an explicit not-assessed context status. |
| get_evidence | Read authorized Lumos sources by ID. Private personal sources are not in Lumos. |
| search_review_evidence | Search within the assigned campaign or exact item. |
| prepare_review_batch | Stage 1–50 supported decisions with run ID, item version, retain/revoke outcome, audit reason and scoped citations. Optional authorized context summary and assessment attribution. Return immutable proposal ID, exact rows and expiry. |
| record_review_batch | Record an explicitly confirmed proposal ID. Returns per-item results and receipts. |
| defer_review_items | Save a reviewer-requested reason for deferring. Items remain pending and can be revisited. |
| get_review_status | Read receipts, failures, pending items and current overview. |

Groups are derived from matching recommendation, rationale and evidence, or explicit open questions/deferrals. Grouping is navigation, not an agent assessment. No agent agreement is synthesized by the UI.

Preparing does not record decisions. Proposals expire after 30 minutes and are bound to run, campaign, reviewer and client profile. At each write, the server checks the exact item and evidence content plus original recommendation against the proposal fingerprint. This catches changed evidence even if its version was not bumped. Each item commits independently with its attempt. Reusing a proposal recovers existing receipts/errors and completes unattempted rows; stale/expired errors need a new preview. Completed receipts remain recoverable after expiry. Reset invalidates prior proposals. Editing anything requires a replacement proposal.

The server validates citation scope and freshness, not the semantic truth of agent reasoning. Personal source excerpts and identifiers should stay in the host. A minimal optional summary is authorized before transmission and shown in the final preview; receipts label it externally supplied and not independently verified by Lumos. Free text cannot technically guarantee privacy; see the production boundary.

Both the browser and panel prepare exact proposals before confirmation. Browser writes use `/api/prepare`, `/api/record`, and `/api/defer`, with same-origin checks. There is no direct public submit endpoint. Reset remains a separate local operator control.

The local simulator trusts client-reported confirmation; it does not prove that a human clicked a button. Reviewer identity comes from fixtures, not authentication. Tool hints and proposal IDs are not authorization credentials. No actual access removal occurs.
