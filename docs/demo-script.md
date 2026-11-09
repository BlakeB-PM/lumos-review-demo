# ChatGPT access review walkthrough

Reset the synthetic ChatGPT run before the audience joins. Open a fresh ChatGPT Work chat with **Lumos Access Reviews** and **Dana Personal Context** selected. Follow the [connection guide](connect-reviewer.md) to install both.

> Help me do my access review.

| Reviewer action | What the audience sees |
| --- | --- |
| Open the assigned review. | The inline panel shows **17 permissions across nine people**, with **15 offboarding grants** and **two grants for Alex Rivera**. |
| Select **Review 15 offboarding grants**. Expand the roster or inspect the Lumos evidence. Select **Preview 15 rejects**. | Albus says **Reject** based on verified HR terminations and offboarding policy. ChatGPT agrees. The preview contains the exact people and permissions. |
| Select **Record 15 decisions** and approve the write if ChatGPT prompts. | Lumos returns receipts. Progress moves to **15 of 17 recorded**, with Alex’s two grants remaining. |
| Select **Review Alex’s permissions**, then **Check my work context**. | ChatGPT checks Lumos policy, activity and Knowledge Hub guidance, then retrieves the private call transcript from Dana Personal Context. Albus saw a recent invoice lookup and suggested **Accept**. The call explains that Alex looked up the invoice while handing work to Sales Ops. |
| Compare the two proposed decisions, then select **Record 2 decisions**. | For **Accounts Receivable**, ChatGPT disagrees and recommends **Reject** because the policy requires a current invoice follow-up responsibility. For **Finance Admin**, ChatGPT agrees with **Reject** because Alex lacks the required assignment. |
| Show **17 of 17 recorded**. Optionally open the audit report or select **Draft Knowledge Hub follow-up**. | The audit retains the original Albus Accept, the recorded Reject and a policy-based reason. The suggested follow-up asks IT to verify the role-level handoff and update the Active Directory Knowledge Hub. |

To exercise an exception, deselect one offboarding grant before preview. Confirm that it stays in the queue and that the recorded count reflects the selection. To exercise missing context, disable Dana Personal Context and open the review in a chat without the transcript. Accounts Receivable should stay pending. Finance Admin can still be decided from Lumos evidence.

The transcript, speakers and private source ID stay out of Lumos calls and the audit. All people, evidence and decisions are synthetic. No real access changes.
