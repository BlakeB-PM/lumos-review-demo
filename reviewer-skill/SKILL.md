---
name: access-review
description: Help the assigned reviewer investigate and complete a Lumos access review through the connected review tools.
---

# Access review

When asked to help complete an access review, use the connected Access Reviews tools. Start with list_my_reviews and get_review_items for the relevant assigned campaign. Resume its current state. Follow pagination. If multiple campaigns are assigned, ask which to open.

Group permissions with the same well-supported rationale. Keep identities and exact permissions distinct. Check source excerpts and versions with get_evidence. For uncertain items, inspect relevant context the reviewer has supplied or authorized in the host, such as an attached conversation or project notes. Use a ticket ID, owner, or date from that context to target search_review_evidence. Keep private context on the host. Search with the smallest useful clue, such as an approval ID, and avoid copying private messages into tool calls.

Check person, exact entitlement, effective date, expiry and conditions before relying on an exception. Compare Albus's suggestion with your own evidence-based judgment. Explicitly identify what the personal context added and explain why it changes or reinforces your recommendation. A personal conversation can establish business context, such as a staffing handoff. Check formal authorization separately against product evidence.

Ask the reviewer a focused question only when their answer could change an unresolved decision. For example, ask whether they have a current renewal reference for a particular permission or want to leave that item pending. Use the host's native question choices when available and allow a typed answer. Otherwise ask in chat and wait. Treat personal notes or answers as leads to verify. Leave a grant pending when needed evidence or judgment is missing.

Call prepare_review_batch for the exact decisions you propose. Use retain to approve and revoke to reject. Show the prepared rows with person, permission, action, reason and evidence IDs. Show pending items separately. Keep the private conversation out of the draft. Add context_summary only if the reviewer expressly approved the specific audit-safe wording for sharing with the product. Ask for explicit confirmation of the final proposal. Use the host's native confirmation affordance when available. If the reviewer changes anything, prepare a replacement proposal and show it before asking again.

Only after confirmation call record_review_batch with the approved proposal ID. Report recorded, pending and blocked items separately. Use get_review_status to read the saved receipts. On a stale item, fetch its new evidence, prepare a new proposal, and ask again. On an uncertain delivery, retry the same confirmed proposal ID. If a reviewer handles an item in the product, refresh the review and honor that decision. Explain that this synthetic workspace records decisions and receipts without changing real access.
