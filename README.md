# Lumos access review demo

A ChatGPT plugin demo for a synthetic Active Directory review. Start in ChatGPT with **Help me do my access review**. The inline panel helps the reviewer inspect and confirm **15 verified offboarding rejects** in one batch, then compare Albus and ChatGPT on **Alex Rivera’s two remaining grants**. A private call transcript shows why Alex’s latest invoice lookup supports a handoff rather than a continuing need for access.

## Run the ChatGPT plugin

The demo uses Python 3.10+ and a ChatGPT Work workspace that supports custom MCP plugins, embedded MCP Apps UI, and write tools. The review simulator uses synthetic data and needs no Lumos account.

```sh
git clone https://github.com/BlakeB-PM/lumos-review-demo.git
cd lumos-review-demo
```

1. Follow [the ChatGPT setup guide](docs/connect-reviewer.md) to connect **Lumos Access Reviews** and **Dana Personal Context** separately.
2. In a fresh ChatGPT chat, select both plugins and say **Help me do my access review.** Follow the [17-grant walkthrough](docs/demo-script.md).
3. Use the panel to inspect the roster, preview the exact rejection batch, confirm it, and check Alex’s grants against the private transcript and Lumos policy.

For an optional audit view or a clean rehearsal:

```sh
python server/src/main.py report --scenario chatgpt --open
python server/src/main.py reset --scenario chatgpt
python evaluation/verify.py
```

The reset is an operator action. Opening the review in ChatGPT resumes the existing state.

## Legacy local tour

The earlier 36-permission fixture remains available as the default local `tour` scenario. To run the legacy Codex walkthrough, install the Codex CLI, sign in to Codex desktop, register the connector below, and open this clone’s **personal-workspace** folder as a local project.

### Register the local connector

Windows PowerShell:

```powershell
$demoPython = (Get-Command python).Source
$demoServer = (Resolve-Path .\server\src\main.py).Path
codex mcp add lumos_review_demo -- $demoPython $demoServer
```

macOS or Linux:

```sh
codex mcp add lumos_review_demo -- "$(command -v python3)" "$PWD/server/src/main.py"
```

[Codex MCP setup](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)

### Open the audit report

```sh
python server/src/main.py report --open
```

Use `python3` on systems where that is the Python command. The report runs at [127.0.0.1:8765](http://127.0.0.1:8765/) and refreshes about once a second. Keep the process running during the demo. Use `--port` if 8765 is occupied. If you pass `--state` to the MCP server, point the report at the same file.

The workspace follows the product tour’s permissions table. Use **Needs Review**, **Reviewed**, or **All**, and use **Show Filters** to narrow by suggestion. Each write requires an audit note and explicit confirmation. **Audit Activity** shows receipts and blocked attempts. Click a row’s note icon to see its evidence and decision.

After confirming both decisions in the assistant, switch to **Reviewed**. Open the audit note on either row to show the saved action, rationale, and evidence. The workspace records synthetic decisions without changing anyone's actual access.

## Start in one message

Open **personal-workspace** as a local project in Codex desktop. In a chat in that project, say:

> Help me complete my access review.

In the local Codex mode, the phrase calls `start_demo` and resets the campaign. In Work and Cowork, it resumes the existing review. Reset a rehearsal separately with the operator command below.

If the tools are missing in an existing chat after registration, start a new chat in the project or restart Codex desktop. For a read-only connection check, ask Codex to call `list_my_reviews` directly.

If an existing session still shows the Q4 warehouse review, restart the local report and the connector host (Codex desktop or the Work tunnel), then open a fresh chat. Existing registrations use the new default when they relaunch the server.

## Operator controls

Run these from this folder in PowerShell.

~~~powershell
python .\server\src\main.py reset
python .\evaluation\verify.py
~~~

The command-line reset clears the demo decisions for a fresh run. The verifier uses temporary state and leaves presentation data alone.

## Boundaries

The server scopes access to a fixed synthetic identity. The panel shows the exact proposal before invoking the ChatGPT-approved record action. The signed batch binds its decisions to the current synthetic run. The transcript is read through a separate connector and the Lumos tools accept only bounded judgment codes for Alex. Revocation decisions and connector remediation are represented separately, with remediation set to `not_performed_in_simulation`.

[Tool contracts](docs/tool-contracts.md) · [Flow diagram](docs/diagrams.md) · [Lumos Access Reviews](https://www.lumos.com/products/access-reviews)
