# Optional warehouse scenario · ChatGPT Work

## Before the audience joins

This earlier scenario is separate from the default walkthrough. Add `--scenario warehouse` to the connector command, report command, and operator reset. Attach [Dana's synthetic reviewer inbox](../personal-workspace/context/reviewer-inbox.md) to Work.

| Beat | What the reviewer does | What the audience sees |
| --- | --- | --- |
| Find my work | In Work, select **Lumos Access Reviews** and say, “Help me complete my access review.” | The model finds Dana's assigned campaign through MCP. It groups the four routine reader permissions, and separates the elevated and unclear grants. |
| Investigate | “Use my inbox to investigate the migration and export grants. What does it change?” | Albus originally suggested Reject for Nora. The private message says Nora took over as primary operator and points straight to SEC-217. The model searches that ID through MCP, checks its scope, dates, and operator condition, and distinguishes it from the sandbox-only SEC-214. It proposes Approve because the latest assignment satisfies the verified approval. |
| Answer as the reviewer | “No current renewal for Eli. Leave him and Leah pending. I'll handle Mateo in the product. You may include ‘Reviewer confirmed Nora is the primary operator for the November 12 cutover’ in the audit note. Show me the proposed batch.” | The model should ask about Eli's renewal after finding the expired exception. His private message offers a possibility and leaves him pending. Work stages four routine approvals and Nora's override. The preview contains the specific summary you authorized and product evidence IDs. The raw inbox stays in Work. |
| Confirm and inspect | Review the proposed batch and say, “Confirm that batch.” Then switch to **Reviewed** in the product. | Five permissions now have receipts marked **ChatGPT Work**. Open Nora's row and expand SEC-217. Show **Reject → Approve**, the verified product evidence and the separately labeled reviewer-approved context. |
| Finish in the product | In **Unreviewed**, approve Mateo's sandbox permission after checking the active assignment evidence. Enter a note and confirm. Back in Work, ask, “What's still unreviewed?” | Work reads six recorded permissions and two pending. Audit Activity shows five receipts from **ChatGPT Work** and one from **Review workspace**. |

Ask the model to show citations or the source excerpt if it summarizes an exception without evidence. If it tries to submit before showing the exact proposal, stop the run and treat that as a failed rehearsal.

## Optional stale-write branch

Before confirming a batch that includes Mateo's sandbox permission, run `python server/src/main.py advance-snapshot`. Confirm the prepared batch. Mateo's row is blocked while valid rows record. Ask Work to refresh the item, show the owner closure, and prepare a new proposal. Confirm that proposal separately or resolve the item in the product. This branch shows write safety without interrupting the main reviewer walkthrough.

## Alternate clients

In Claude Cowork, use the same walkthrough with the [local connector](connect-reviewer.md). Receipts are marked **Claude Cowork**. The older Codex demo can still run locally with its original registration. Its starter phrase resets the demo and receipts are marked **Codex MCP**.
