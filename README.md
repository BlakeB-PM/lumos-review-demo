# Lumos access review demo

A synthetic Active Directory review inspired by the [Lumos product tour](https://www.lumos.com/product-tours/user-access-reviews). Lumos suggests keeping a Sales Account Executive’s invoice access based on role and recent usage. The personal assistant finds a handoff Lumos did not see, checks the policy, and proposes reversing that suggestion. The reviewer confirms and inspects the recorded decision and evidence in the browser. The demo needs Python 3.10+ and uses the standard library.

## Run the demo locally

For the full assistant walkthrough, install Python 3.10 or newer and the Codex CLI, and sign in to Codex desktop. The local demo server uses synthetic fixtures and needs no API key or Lumos account.

```sh
git clone https://github.com/BlakeB-PM/lumos-review-demo.git
cd lumos-review-demo
```

1. Register the local connector using the command below.
2. Start the browser workspace and leave it open beside Codex.
3. Open this clone’s **personal-workspace** folder as a local project in Codex desktop and say **Help me complete my access review.** Follow the [one-minute walkthrough](docs/demo-script.md).

To explore just the review table and record synthetic decisions from the browser, skip connector setup and run the browser command below. For the full assistant walkthrough in ChatGPT Work or Claude Cowork, follow [Connect an assistant to Access Reviews](docs/connect-reviewer.md).

### Register the connector once

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

The server scopes access to a fixed synthetic identity. The chat asks the reviewer to confirm the exact proposal. The server requires the client's confirmation assertion and records it as such. Directory separation illustrates how context moves. A local agent with broad filesystem access can still read sibling files. Revocation decisions and connector remediation are represented separately, with remediation set to `not_performed_in_simulation`.

[Tool contracts](docs/tool-contracts.md) · [Flow diagram](docs/diagrams.md) · [Lumos Access Reviews](https://www.lumos.com/products/access-reviews)
