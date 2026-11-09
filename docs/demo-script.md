# The one-minute access review demo

Open the review workspace beside the assistant. A fresh campaign shows **36 permissions across 18 people**. Enable **Lumos Access Reviews** and **Dana Personal Context** in your assistant and use the prompt below. The [connection guide](connect-reviewer.md) covers each host.

> Help me complete my access review. Start with Alex Rivera’s permissions.

Dana Personal Context searches a [simulated private inbox](../personal-workspace/context/sales-handoff.md). Lumos provides the [simulated Knowledge Hub entry](../server/data/knowledge/knowledge-hub/AD-KH-SALES.md), which treats recent invoice lookups as a signal of ongoing work. Dana’s handoff explains why that signal is misleading for Alex.

| Say or do | What this shows |
| --- | --- |
| Show the **36** pending permissions, then search for **Alex Rivera** and point to **Accept** on Accounts Receivable. | Lumos sees a recent invoice lookup. That activity supports keeping the permission until you learn why the lookup happened. |
| Start the review and show the personal-context lookup in the assistant’s tool activity. | The assistant searches for Alex and invoice follow-up. It uses the handoff to reinterpret the invoice lookup and checks the policy through Lumos. It proposes **Reject Accounts Receivable**, reversing Lumos, and agrees with Lumos on **Reject Finance Admin**. |
| Read the proposed actions and say **“Confirm those two decisions.”** | The reviewer makes the call. The assistant records the decisions and the audit notes. Dana’s message stays in the personal workspace. |
| Switch to **Reviewed** and open the Accounts Receivable audit note. **“Same employee, same title. The assistant knew the work had changed.”** | Show **Accept** in Suggestion and **Reject** in Review Action, with the audit note and cited policy. **34** permissions are still pending. |
| Close with **“Draft an IT request to update the Lumos Knowledge Hub so the next review gets this right.”** | Show the assistant’s unsent IT request. The individual decision is already recorded. This separate request would carry the verified handoff into future reviews. |

**Draft IT request — Update Active Directory review context in the Lumos Knowledge Hub**

Please confirm that Sales Ops now owns customer invoice follow-up. Then add this to the **Active Directory** access review context in the Knowledge Hub:

> Sales Ops owns customer invoice follow-up. Recommend keeping Accounts Receivable access for people who currently handle that work. Use current responsibilities to assess access when a Sales title or past lookup is the only signal.

Re-sync the review and check that the suggestions reflect who does the work today. [Lumos Knowledge Hub guidance](https://support.lumos.com/articles/6323349102-knowledge-hub-access-reviews)

The permission examples come from the [Lumos product tour](https://www.lumos.com/product-tours/user-access-reviews). Alex and the handoff are fictional. The demo records decisions without changing real access.
