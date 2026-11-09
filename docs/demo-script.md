# ChatGPT access review walkthrough

Reset the synthetic run before the audience joins. Open **personal-workspace** as a local project in the desktop app and start a fresh local chat. Follow the [local connection guide](connect-reviewer.md) to register both MCP servers.

> Help me do my access review.

| Reviewer action | What the audience sees |
| --- | --- |
| Open the assigned review and pause at the overview. | The inline panel shows **17 left to review** and **0 of 17 recorded**. It recommends starting with **15 offboarding grants** and shows **two grants for Alex Rivera** as the other group. |
| Select **Review 15 offboarding grants**. Expand the roster or inspect the Lumos evidence. Select **Preview 15 rejects**. | Albus says **Reject** based on verified HR terminations and offboarding policy. ChatGPT agrees. The preview contains the exact people and permissions. |
| Select **Record 15 decisions** and approve the write if ChatGPT prompts. Open **Reviewed** in the local browser report. | Progress moves to **15 of 17 recorded**, with Alex’s two grants remaining. The browser shows those same 15 grants as **Reject**. |
| Select **Review individual grants**, then **Check my work context**. | ChatGPT checks Lumos policy, activity and Knowledge Hub guidance, then retrieves the private call transcript from Dana Personal Context. Albus saw a recent invoice lookup and suggested **Accept**. The call explains that Alex looked up the invoice while handing work to Sales Ops. |
| Compare the two proposed decisions and read the work context summary before recording. | For **Accounts Receivable**, the proposal shows the Sales Ops handoff and why the activity does not demonstrate a current business need. For **Finance Admin**, ChatGPT agrees with **Reject** because Alex lacks the required assignment. |
| In the browser, open **Reviewed**, then open **Accounts Receivable** for Alex. | The audit shows Albus’s Accept, the recorded Reject, the reviewer-approved work context summary, and the Lumos evidence. The agent may suggest a Knowledge Hub update in conversation if useful. |

To exercise an exception, deselect one offboarding grant before preview. Confirm that it stays in the queue and that the recorded count reflects the selection. To exercise missing context, disable Dana Personal Context and open the review in a chat without the transcript. Accounts Receivable should stay pending. Finance Admin can still be decided from Lumos evidence.

If the local client presents only tool results, ask for the offboarding group, preview and confirm the exact batch in chat, then ask it to check Alex against your work context. The same tool calls update the same review.

The transcript, speakers and private source ID stay out of Lumos calls and the audit. All people, evidence and decisions are synthetic. No real access changes.
