# Connect the local review

Use Python 3.10+, the Codex CLI, and a **local chat in the ChatGPT desktop app**. Both connectors run over local stdio.

## Register the two connectors

From the repository root in PowerShell:

~~~powershell
$demoPython = (Get-Command python -CommandType Application | Select-Object -First 1).Source
$demoServer = (Resolve-Path ./server/src/main.py).Path
$contextServer = (Resolve-Path ./server/src/personal_context.py).Path
codex mcp add lumos_review_demo -- $demoPython $demoServer --scenario chatgpt --assistant-host chatgpt_work
codex mcp add dana_personal_context -- $demoPython $contextServer --transcript
~~~

The commands update existing registrations under the same names. The host flag labels receipts; all hosts use the same tools and UI resource. The connectors still run locally.

## Start the demo

1. Restart the desktop app after registering the servers.
2. Open **personal-workspace** from this clone as a local project and start a fresh local chat.
3. Ask to see your review, or ask to investigate and prepare recommendations. A fresh default fixture contains 17 grants. The agent follows your requested scope; it does not need an exact trigger phrase.
4. Use the inline panel if the host supports MCP Apps, or continue in conversation with the same tools. Confirm the exact proposal before recording.

Existing connector processes cache tool definitions and instructions. After updating this checkout, restart the desktop app and start a fresh chat so it discovers the generic tools. `preview_alex_batch` and `preview_offboarding_batch` are no longer exposed.

To inspect saved decisions in the browser, run `python server/src/main.py report --open`. The report defaults to the same 17-grant campaign and database as the chat connector. Add `--port 8766` if that is the port you use for the demo. If you override the SQLite path, use the same `--state` with the connector, report, and reset. To start a clean rehearsal, run `python server/src/main.py reset --scenario chatgpt`.
