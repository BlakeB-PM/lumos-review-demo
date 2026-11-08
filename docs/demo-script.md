# Five-minute desktop rehearsal

Start the report with `python server/src/main.py report --open` and keep it open beside a Codex chat rooted in personal-workspace. The opening line resets the review even if a previous rehearsal recorded decisions. Use a fresh chat for a blank transcript. Open a separate terminal only if you're showing the stale-write step.

| Time | Say or do | Show |
| --- | --- | --- |
| 0:00 | “Help me complete my access review.” | A clean run, Dana's assigned campaign, eight pending items, and the report at 0 of 8 recorded. |
| 0:45 | “Which four can I review together, and what evidence backs them?” | AR-101 through AR-104 share an Accept suggestion and Role Aligned insight. Show the role policy and individual usage records. |
| 1:30 | “What changes the recommendation on Nora? Where does that leave Eli?” | Nora starts at Reject. EX-MIGRATION covers her exact grant. Eli starts at Review. EX-EXPIRED and the missing renewal explain why he stays pending. |
| 2:30 | Include AR-107 in the proposed version 1 batch. Leave AR-106 and AR-108 pending. After the proposal is visible, run `python .\server\src\main.py advance-snapshot` in PowerShell. | The batch still displays version 1 of AR-107. |
| 3:00 | “I confirm the exact batch you showed.” | Switch to the report. It updates to five recorded, three pending, and one needing attention. Click Nora's name to show Albus's original Reject suggestion, the reviewer's recorded Approve decision, and the cited exception. |
| 3:45 | “Retry the identical batch with the same key, then refresh AR-107 and show me what changed.” | Same receipt IDs, original recommendation preserved, new owner closure, and a new proposal awaiting confirmation. |
| 4:30 | “Show me the audit record and what remains pending.” | Show the blocked write in Audit activity and unchanged receipt count after the retry. Use the Pending filter to isolate open work. |

If the agent finds the new AR-107 snapshot before submitting, accept its refreshed proposal for the live flow and use the verifier to show a stale submission separately.

## Optional comparison branch

In the simulated configuration, ask one narrow question about Eli's expired exception. Show the structured request for an authoritative renewal. If you want to demonstrate the context exchange, explicitly allow sharing only the attributed claim that the team expected an extension. The fixture returns insufficient evidence and leaves the item pending. Baseline and simulation can both cite EX-EXPIRED and POL-ELEVATED.

## Evaluation and backup

Use the same cases and evidence in both modes. Record decision correctness, appropriate deferrals, source support, policy violations, interventions, reviewer comprehension, time, tool calls, cost and receipt completeness. Keep the answer key out of the presentation workspace. Set numerical go/no-go thresholds before testing a live model. Fixture runs exercise the contract and cannot measure model quality.

After a successful desktop rehearsal, capture a five-minute backup recording by starting with the same opening line.
