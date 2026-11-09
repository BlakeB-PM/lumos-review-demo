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

The commands update existing registrations under the same names. The `chatgpt_work` flag selects the tool and UI profile. The connectors still run locally.

## Start the demo

1. Restart the desktop app after registering the servers.
2. Open **personal-workspace** from this clone as a local project and start a fresh local chat.
3. Say **Help me do my access review.** The chat should call `open_access_review` and wait at the overview. A fresh run shows **17 left to review**, with **15 offboarding grants** and **two grants for Alex**.
4. Follow the [walkthrough](demo-script.md). The connector supplies an inline review panel to hosts that render MCP Apps resources. If your local client shows only tool results, continue in chat with the same review and batch tools.

If the first call is `list_my_reviews` or the overview shows 36 grants, run `codex mcp get lumos_review_demo` and verify the scenario and host flags above. Restart the app and start a fresh chat after fixing the registration.

To inspect saved decisions in the browser, run `python server/src/main.py report --open`. The report defaults to the same 17-grant campaign and database as the chat connector. Add `--port 8766` if that is the port you use for the demo. If you override the SQLite path, use the same `--state` with the connector, report, and reset. To start a clean rehearsal, run `python server/src/main.py reset --scenario chatgpt`.
