# The one-minute access review demo

Open the review workspace beside your assistant. It should show two permissions for Alex Rivera under **Needs Review**. In Work or Cowork, attach [Dana’s synthetic sales handoff](../personal-workspace/context/sales-handoff.md) to the chat. In the local Codex project, the assistant reads the note from its own workspace. The Lumos connector sees the permission records, policy, and usage.

| Say or do | What this shows |
| --- | --- |
| Point to **Accept** on Accounts Receivable. **“Lumos sees that Alex is in Sales and looked up an invoice recently. Based on that, keeping access makes sense.”** | Accounts Receivable lets Alex see whether customers have paid. The review table shows why Lumos suggested keeping it. |
| Say **“Help me complete my access review.”** | The assistant finds Dana’s handoff: Sales Ops took over invoice follow-up. It checks the policy, which limits access to people who still do that work. It proposes **Reject Accounts Receivable**, reversing Lumos. It agrees with Lumos on **Reject Finance Admin**. |
| Read the proposed actions and say **“Confirm those two decisions.”** | The reviewer makes the call. The assistant records the decisions and the audit notes. Dana’s message stays in the personal workspace. |
| Switch to **Reviewed** and open the Accounts Receivable audit note. **“Same employee, same title. The assistant knew the work had changed. I could see why, make the call, and leave a record.”** | Show **Accept** in Suggestion and **Reject** in Review Action, with the audit note and cited policy. |
| Close with **“The assistant also suggests asking IT to update the Knowledge Hub, so the next review starts with the right context.”** | Show the draft below in chat. The reviewer can decide whether to submit it separately. |

**Draft IT request — Update Active Directory review context in the Lumos Knowledge Hub**

Please confirm with Sales Ops that it now owns customer invoice follow-up. Then update the Active Directory review context so the Accounts Receivable suggestion reflects who currently handles invoice follow-up; a Sales title or prior invoice lookup alone is not enough. Re-sync the review and check the suggestions. [Lumos Knowledge Hub guidance](https://support.lumos.com/articles/6323349102-knowledge-hub-access-reviews)

The permission examples come from the [Lumos product tour](https://www.lumos.com/product-tours/user-access-reviews). Alex and the handoff are fictional. The demo records decisions without changing real access.
