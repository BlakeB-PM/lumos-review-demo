# Tool contracts

| Tool | Inputs and result |
| --- | --- |
| start_demo | Canonical trigger phrase `Help me complete my access review`. Clears local synthetic state and returns a new run ID, campaign and clean items. |
| list_my_reviews | Optional campaign status, cursor and limit. Returns assigned campaigns and counts. |
| get_review_items | Campaign ID plus optional pending/recorded status, cursor and limit. Returns the run ID, exact grants, original recommendation with its recorded version, and the current item snapshot. |
| get_evidence | Evidence IDs. Returns authorized Markdown excerpts and metadata. Unknown and unassigned sources both appear as unavailable. |
| search_review_evidence | Campaign ID, query, optional item ID and limit. Returns ranked source matches in the authorized scope. |
| submit_decisions | Campaign ID, run ID, confirmation assertion, idempotency key and explicit item decisions. Each decision includes item ID, snapshot version, outcome, reason and evidence IDs. Optional investigation ID must match item and snapshot. |
| get_review_status | Campaign ID. Returns receipts, pending IDs, most recent failures for still-pending items, and remediation status. |
| ask_albus | Simulation only. Item ID, snapshot version, specific question and optional bounded attributed claim with explicit sharing intent. Returns a labeled investigation with cited source versions, checks, open issues and timing. |

A submission reserves its idempotency key for the exact ordered payload within a run. Each item and its audit attempt commit together in an independent SQLite transaction. Replaying the same key and payload returns the saved receipts and errors and can finish work interrupted between items. A changed payload needs a new key. An item can have only one recorded decision. A stale write returns refresh_required with the current snapshot. A reset invalidates earlier run IDs, including those of submissions interrupted between items. Keep pending items out of the decision payload.

Original recommendation outcomes are `accept`, `reject`, and `review`, following Lumos's documented Albus suggestions. Insight categories explain the suggestion. The demo submission contract uses `retain` and `revoke` for the two supported reviewer decisions. The report labels them **Approve** and **Reject**. An item awaiting a human decision remains **Pending**, including when Albus suggests **Review**. [Lumos reviewer workflow](https://support.lumos.com/articles/8143225870-reviewing-user-access-in-lumos)

Source IDs and versions must be authorized for the specific item. The demo validates citation scope and availability. The reviewer verifies that the cited material supports the proposed decision.
