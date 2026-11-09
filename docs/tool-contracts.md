# Tool contracts

## ChatGPT plugin

Run with `--scenario chatgpt --assistant-host chatgpt_work`. The scenario shares its default SQLite file and 17-grant queue with the browser report. The overview, group, preview and record tools advertise the inline `ui://lumos/access-review-v3.html` resource. The tools return structured results for both ChatGPT and the component.

| Tool | Contract |
| --- | --- |
| `open_access_review` | Open or resume the synthetic review. Return recorded and pending counts and next groups. |
| `get_review_group` | Read either the verified offboarding roster or Alex’s remaining grants with original Albus reasoning and Lumos evidence references. |
| `get_evidence` | Read item-scoped evidence from Lumos. The private transcript lives in a separate connector. |
| `preview_offboarding_batch` | Validate the selected termination grants and preview the exact rejects. |
| `preview_alex_batch` | Preview supported judgments using item IDs, versions and allowlisted policy reason codes. When the work call verifies the handoff and explains the lookup, include the bounded `work_context` finding for Accounts Receivable. The resulting summary appears before confirmation and is saved on that grant's receipt. |
| `record_review_batch` | Submit the signed preview after explicit reviewer confirmation. Return per-grant receipts or conflicts and the updated queue. |

Previewing does not write decisions or drafts. The server signs the exact decisions and run ID. The signature also identifies an idempotent submission. A reset invalidates previews, and an item changed or recorded since preview returns a conflict. ChatGPT owns its approval UI. The simulator records the authenticated host's confirmation assertion rather than acting as a production authorization service.

## Legacy tour and warehouse tools

| Tool | Inputs and result |
| --- | --- |
| start_demo | Canonical trigger phrase `Help me complete my access review`. Clears local synthetic state and returns a new run ID, campaign and clean items. |
| list_my_reviews | Optional campaign status, cursor and limit. Returns assigned campaigns and counts. |
| get_review_items | Campaign ID plus optional pending/recorded status, cursor and limit. Returns the run ID, exact grants, original recommendation with its recorded version, and the current item snapshot. |
| get_evidence | Evidence IDs. Returns authorized Markdown excerpts and metadata. Unknown and unassigned sources both appear as unavailable. |
| search_review_evidence | Campaign ID, query, optional item ID and limit. Returns ranked source matches in the authorized scope. |
| submit_decisions | Campaign ID, run ID, confirmation assertion, idempotency key and explicit item decisions. Each decision includes item ID, snapshot version, outcome, reason and evidence IDs. Optional investigation ID must match item and snapshot. |
| get_review_status | Campaign ID. Returns receipts, pending IDs, most recent failures for still-pending items, and remediation status. |
| prepare_review_batch | Work and Cowork. Validates an explicit, evidence-backed decision draft and returns a proposal ID and reviewable rows. No decision is recorded. |
| record_review_batch | Work and Cowork. Accepts only the proposal ID and records that exact proposal after reviewer confirmation in the host. Retries use the same ID. |
| ask_albus | Simulation only. Item ID, snapshot version, specific question and optional bounded attributed claim with explicit sharing intent. Returns a labeled investigation with cited source versions, checks, open issues and timing. |

A submission reserves its idempotency key for the exact ordered payload within a run. Each item and its audit attempt commit together in an independent SQLite transaction. Replaying the same key and payload returns the saved receipts and errors and can finish work interrupted between items. A changed payload needs a new key. An item can have only one recorded decision. A stale write returns refresh_required with the current snapshot. A reset invalidates earlier run IDs, including those of submissions interrupted between items. Keep pending items out of the decision payload.

Original recommendation outcomes are `accept`, `reject`, and `review`, following Lumos's documented Albus suggestions. Insight categories explain the suggestion. The demo submission contract uses `retain` and `revoke` for the two supported reviewer decisions. The report labels them **Approve** and **Reject**. An item awaiting a human decision remains **Pending**, including when Albus suggests **Review**. [Lumos reviewer workflow](https://support.lumos.com/articles/8143225870-reviewing-user-access-in-lumos)

Source IDs and versions must be authorized for the specific item. The demo validates citation scope and availability. The reviewer verifies that the cited material supports the proposed decision.
