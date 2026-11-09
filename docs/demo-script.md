# The one-minute access review demo

Open the review workspace beside your assistant. It should show two permissions for Alex Rivera under **Needs Review**. In Work or Cowork, attach [Dana’s synthetic sales handoff](../personal-workspace/context/sales-handoff.md) to the chat. In the local Codex project, the assistant reads the note from its own workspace. The Lumos connector sees the permission records, policy, and usage.

| Say or do | What this shows |
| --- | --- |
| Point to **Accept** on Accounts Receivable. **“Lumos sees that Alex is in Sales and looked up an invoice recently. Based on that, keeping access makes sense.”** | Accounts Receivable lets Alex see whether customers have paid. The review table shows why Lumos suggested keeping it. |
| Say **“Help me complete my access review.”** | The assistant finds Dana’s handoff: Sales Ops took over invoice follow-up. It checks the policy, which limits access to people who still do that work. It proposes **Reject Accounts Receivable**, reversing Lumos. It agrees with Lumos on **Reject Finance Admin**. |
| Read the proposed actions and say **“Confirm those two decisions.”** | The reviewer makes the call. The assistant records the decisions and the audit notes. Dana’s message stays in the personal workspace. |
| Switch to **Reviewed** and open the Accounts Receivable audit note. **“Same employee, same title. The assistant knew the work had changed. I could see why, make the call, and leave a record.”** | Show **Accept** in Suggestion and **Reject** in Review Action, with the audit note and cited policy. |
| Close with **“Draft an IT request to update the Lumos Knowledge Hub so the next review gets this right.”** | Show the assistant’s unsent IT request. The individual decision is already recorded. This separate request would carry the verified handoff into future reviews. |

**Draft IT request — Update Active Directory review context in the Lumos Knowledge Hub**

Please confirm that Sales Ops now owns customer invoice follow-up. Then add this to the **Active Directory** access review context in the Knowledge Hub:

> Sales Ops owns customer invoice follow-up. Recommend keeping Accounts Receivable access for people who currently handle that work. Use current responsibilities to assess access when a Sales title or past lookup is the only signal.

Re-sync the review and check that the suggestions reflect who does the work today. [Lumos Knowledge Hub guidance](https://support.lumos.com/articles/6323349102-knowledge-hub-access-reviews)

The permission examples come from the [Lumos product tour](https://www.lumos.com/product-tours/user-access-reviews). Alex and the handoff are fictional. The demo records decisions without changing real access.
