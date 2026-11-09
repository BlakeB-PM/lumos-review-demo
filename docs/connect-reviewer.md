# Connect the ChatGPT review plugin

This walkthrough targets a ChatGPT Work workspace with custom MCP plugins, embedded MCP Apps UI, and write-capable tools enabled. Install Python 3.10+ and OpenAI’s Secure MCP Tunnel client. Use a workspace where the administrator has authorized this synthetic demo. [Custom MCP setup](https://developers.openai.com/api/docs/guides/custom-mcp-server) · [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)

## Lumos Access Reviews

1. Create a workspace-scoped tunnel in [OpenAI Platform](https://platform.openai.com/settings/organization/tunnels). Provide the tunnel client's restricted runtime credential through the `CONTROL_PLANE_API_KEY` environment variable. Use the official tunnel guide for credential setup.
2. In PowerShell from the repository root, configure and run the Lumos connector.

   ```powershell
   $demoPython = (Get-Command python -CommandType Application | Select-Object -First 1).Source.Replace('\', '/')
   $demoServer = (Resolve-Path ./server/src/main.py).Path.Replace('\', '/')
   $demoCommand = "`"$demoPython`" `"$demoServer`" --scenario chatgpt --assistant-host chatgpt_work"
   tunnel-client init --sample sample_mcp_stdio_local --profile lumos-review --tunnel-id '<lumos-tunnel-id>' --mcp-command $demoCommand
   tunnel-client doctor --profile lumos-review --explain
   tunnel-client run --profile lumos-review
   ```

3. In [ChatGPT Plugins](https://chatgpt.com/#settings/Connectors), add a custom MCP server named **Lumos Access Reviews**, select **Tunnel**, and choose the Lumos tunnel. Verify discovery of `open_access_review`, `get_review_group`, the two preview tools, and `record_review_batch`. Install the plugin. The overview tool references the embedded review panel as an MCP Apps UI resource.

## Dana Personal Context

1. Create a second workspace-scoped tunnel for private context. Use a separate local health port if both profiles run on the same machine. Configure its stdio command as `python /absolute/path/to/server/src/personal_context.py --transcript`.
2. In ChatGPT, add that tunnel as **Dana Personal Context** and install it. The only tool is the read-only `search_personal_context`. As an alternative for a rehearsal, add the [synthetic transcript](../personal-workspace/context/sales-ops-call-transcript.md) as a source in the reviewer’s ChatGPT project.
3. Keep both tunnel processes running. Start a fresh ChatGPT Work chat, select the two plugins and use the [demo prompt](demo-script.md). The panel’s **Check my work context** action asks ChatGPT to retrieve the transcript through the separate connection. Lumos receives only bounded decision reason codes.

## Rehearsal and troubleshooting

- Reset with `python server/src/main.py reset --scenario chatgpt` before starting a clean rehearsal. The chat prompt opens or resumes the campaign.
- Optionally start the audit report with `python server/src/main.py report --scenario chatgpt --open`. Pass the same `--state` path to the report, reset command and Lumos connector if you override the default database.
- After changing the connector, restart its tunnel process, refresh the plugin’s tools, and start a fresh ChatGPT Work chat. If the tool discovery shows the earlier `list_my_reviews` flow, check the connector’s `--scenario chatgpt --assistant-host chatgpt_work` flags.
- In the target workspace, verify the embedded overview, roster selection, **Check my work context** follow-up, write approval and progress update. If the UI is unavailable, the tools also return structured data for the conversation. Workspace settings control connector access and approval prompts.
- The earlier 36-permission tour and [warehouse scenario](warehouse-scenario.md) remain available for local regression and legacy rehearsals. They use different state files and do not expose the new panel.
