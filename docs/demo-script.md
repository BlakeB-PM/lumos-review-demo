# The one-minute access review demo

Open the review workspace beside the assistant. A fresh campaign shows **36 permissions across 18 people**. Start a Work chat from a ChatGPT project that has [Dana’s sales handoff](../personal-workspace/context/sales-handoff.md) in **Sources**. Select **Lumos Access Reviews** and use the prompt below. In local Codex, the same file lives in the personal workspace.

> Help me complete my access review. Start with Alex Rivera’s permissions.

The project source simulates the personal agent’s context. The [simulated Knowledge Hub entry](../server/data/knowledge/knowledge-hub/AD-KH-SALES.md) is available separately through Lumos. It treats recent invoice lookups as a signal of ongoing work. Dana’s handoff explains why that signal is misleading for Alex.

| Say or do | What this shows |
| --- | --- |
| Show the **36** pending permissions, then search for **Alex Rivera** and point to **Accept** on Accounts Receivable. | Lumos sees a recent invoice lookup. That activity supports keeping the permission until you learn why the lookup happened. |
| Start the review from Dana’s project. | The assistant finds the Sales Ops handoff in the project’s Sources, summarizes the queue, and checks the Knowledge Hub entry and policy through MCP. It proposes **Reject Accounts Receivable**, reversing Lumos, and agrees with Lumos on **Reject Finance Admin**. |
| Read the proposed actions and say **“Confirm those two decisions.”** | The reviewer makes the call. The assistant records the decisions and the audit notes. Dana’s message stays in the personal workspace. |
| Switch to **Reviewed** and open the Accounts Receivable audit note. **“Same employee, same title. The assistant knew the work had changed.”** | Show **Accept** in Suggestion and **Reject** in Review Action, with the audit note and cited policy. **34** permissions are still pending. |
| Close with **“Draft an IT request to update the Lumos Knowledge Hub so the next review gets this right.”** | Show the assistant’s unsent IT request. The individual decision is already recorded. This separate request would carry the verified handoff into future reviews. |

**Draft IT request — Update Active Directory review context in the Lumos Knowledge Hub**

Please confirm that Sales Ops now owns customer invoice follow-up. Then add this to the **Active Directory** access review context in the Knowledge Hub:

> Sales Ops owns customer invoice follow-up. Recommend keeping Accounts Receivable access for people who currently handle that work. Use current responsibilities to assess access when a Sales title or past lookup is the only signal.

Re-sync the review and check that the suggestions reflect who does the work today. [Lumos Knowledge Hub guidance](https://support.lumos.com/articles/6323349102-knowledge-hub-access-reviews)

The permission examples come from the [Lumos product tour](https://www.lumos.com/product-tours/user-access-reviews). Alex and the handoff are fictional. The demo records decisions without changing real access.
