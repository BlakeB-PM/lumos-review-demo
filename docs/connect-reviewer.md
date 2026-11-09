# Connect an assistant to Access Reviews

The Work and Cowork connectors expose the same synthetic review data, evidence search and audit records as the local product workspace. They open the current campaign, stage an exact proposal, and record that proposal after reviewer confirmation. The host supplies the model and any native question or confirmation UI. Use the [reviewer skill](../reviewer-skill/SKILL.md) to guide tool selection and the conversation.

## ChatGPT Work · private connection

Hosted Work uses an installed custom MCP plugin. The Codex stdio registration does not install a Work plugin. Use OpenAI's Secure MCP Tunnel to keep the synthetic review service on the demo machine.

1. In [Platform tunnel settings](https://platform.openai.com/settings/organization/tunnels), create or select a tunnel associated with your target ChatGPT workspace. Install the official tunnel client and provide a restricted runtime key through the local `CONTROL_PLANE_API_KEY` environment. Follow the official guide for permissions and installation. [Secure MCP Tunnel guide](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
2. From the repo root, configure the client. Replace the tunnel ID with the ID from Platform. The following is for PowerShell. On macOS or Linux, use the absolute paths to Python 3 and `server/src/main.py` in the quoted MCP command.

   ```powershell
   $demoPython = (Get-Command python).Source.Replace('\', '/')
   $demoServer = (Resolve-Path ./server/src/main.py).Path.Replace('\', '/')
   $demoCommand = "`"$demoPython`" `"$demoServer`" --assistant-host chatgpt_work"
   tunnel-client init --sample sample_mcp_stdio_local --profile lumos-review --tunnel-id '<your-tunnel-id>' --mcp-command $demoCommand
   tunnel-client doctor --profile lumos-review --explain
   tunnel-client run --profile lumos-review
   ```

3. In [ChatGPT Plugins](https://chatgpt.com/#settings/Connectors), add a custom MCP server named **Lumos Access Reviews**, select **Tunnel**, and choose that workspace's tunnel. For this isolated synthetic demo, use workspace-scoped tunnel access and no additional upstream authentication. Review the discovered tools and install the plugin. [OpenAI's custom MCP plugin setup](https://developers.openai.com/plugins/deploy/connect-chatgpt)
4. Create a ChatGPT project for Dana’s personal context. Add [sales-handoff.md](../personal-workspace/context/sales-handoff.md) under **Sources**. In the project instructions, tell Work to read that source before proposing actions and to use Lumos MCP for review records, Knowledge Hub guidance, and policy. Start a Work chat inside the project, select **Lumos Access Reviews** via `@`, and use the [demo prompt](demo-script.md).

The tunnel needs to stay running during the demo. The tool caller is a fixed synthetic reviewer. Use a separate checkout or state file for each independent rehearsal. The browser report must use the same state path as the connector.

### Give Work a separate personal context connector

Create a second workspace-scoped tunnel and use a distinct local health port. Configure its stdio command as `python /absolute/path/to/server/src/personal_context.py`. Install it in ChatGPT as **Dana Personal Context**, then select both plugins in a fresh Work chat. This path retrieves the handoff through a read-only MCP call and does not require a project source. [Secure MCP Tunnel guide](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)

### Run both connectors locally in Codex

Register the review connector using the README, then add the separate personal inbox connector. In PowerShell from the repo root:

```powershell
$python = (Get-Command python -CommandType Application | Select-Object -First 1).Source
$contextServer = (Resolve-Path ./server/src/personal_context.py).Path
codex mcp add dana_personal_context -- $python $contextServer
```

Open a fresh Codex chat with both MCP servers enabled. Use the demo prompt and look for `search_personal_context` in the tool activity.

## Claude Cowork · local connector plugin

Generate a local plugin with both MCP connections and the reviewer skill. The archive uses this checkout's absolute paths so Claude and the product browser share the same review state. Generate it on the machine where Cowork runs.

```sh
python scripts/package-cowork.py lumos-cowork.zip
```

In Claude Desktop, open **Cowork → Customize → Plugins**, upload the archive, and enable the plugin. Use the demo’s `personal-workspace` folder as Cowork’s project context, then use the same reviewer prompt. [Claude local connector support](https://support.claude.com/en/articles/11725091-when-to-use-desktop-and-web-connectors) · [Claude plugin setup](https://support.claude.com/en/articles/13837440-use-plugins-in-claude)

## Browser and reset

Start the product workspace with `python server/src/main.py report --open`. Run `python server/src/main.py reset` before a clean rehearsal. The phrase “Help me complete my access review” resumes the campaign in Work and Cowork. The operator reset clears the synthetic run and invalidates unsubmitted proposals.

## Confirm the installed host behavior

In each host, make the handoff available as personal workspace context. Verify that the assistant reads all 36 Active Directory permissions, uses the handoff and the Knowledge Hub entry as separate sources, and proposes decisions for Alex’s two grants. After confirmation, the decisions should appear in the browser.
