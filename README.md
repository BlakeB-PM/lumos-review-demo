# Lumos access reviews

A local prototype of a reusable reviewer experience: Lumos provides exact grants, recommendations, policy and evidence; the personal agent resolves open questions using its authorized context. The reviewer edits and confirms an exact proposal. Decisions and remediation remain separate.

All scenarios use the same MCP tools and inline panel. Names, permissions and scenario facts live in fixture data, not tool schemas or workflow instructions. The default fixture includes 17 permissions; `tour` has 36, `warehouse` has eight, and `slack` has 240 synthetic memberships. The personal-context connector is an optional synthetic source, not a required product integration.

## Run locally

Clone the repository and enter it:

```sh
git clone https://github.com/BlakeB-PM/lumos-review-demo.git
cd lumos-review-demo
```

**Browser-only:** Run `python server/src/main.py report --open` with Python 3.10+ (use `python3` where applicable). The report runs on localhost and supports synthetic review decisions and audit receipts.

**Agent and inline panel:** The clone includes the local Lumos MCP server, the optional synthetic personal-context connector, and the panel. Register the connectors using the guide below. You need a compatible desktop host and the Codex CLI for the documented setup. The inline panel requires MCP Apps support. The local prototype uses synthetic fixtures and needs no Lumos credentials.

Use Python 3.10+ and follow [connection setup](docs/connect-reviewer.md). Start with any natural request, for example:

> Investigate my pending access review and prepare supported recommendations.

The inline panel separates permissions ready for batch review from those needing individual investigation. The page checkbox selects or clears only the displayed page. Open evidence from a permission row or a shared batch, ask the agent to investigate, or choose **Decide manually** to enter actions and audit reasons alongside the selected rows. Unresolved grants can stay pending.

Before recording, **Review audit entries** shows exactly what will be saved for each permission. After recording, verify the saved reasons and receipt IDs before continuing. Hosts that render MCP Apps show the inline panel. The same tools support text-only hosts.

Run `python evaluation/verify.py` to check the local workflow with isolated state.

Reset is a separate operator action, never part of opening a review:

```sh
python server/src/main.py reset --scenario chatgpt
```

For rendered UI checks, install Playwright in your test environment and run `node evaluation/ui.cjs` (set `CHROME` to your browser executable on other platforms). This uses isolated state and a simulated MCP Apps host; it does not replace testing inside each supported host.

The browser workspace and MCP share proposals, receipt state, evidence freshness checks, and deferrals. Use the same `--scenario` and `--state` for both.

**Architecture and workflows:** [Six detailed Mermaid diagrams](docs/diagrams.md) cover the system boundaries, reviewer experience, MCP interaction sequence, confirmation and retry lifecycle, evidence provenance, and production integration gaps. See also the [Miro implementation diagram](https://miro.com/app/board/uXjVESqFoRg=/?moveToWidget=3458764689933058696) for the canvas view.

[Tool contracts](docs/tool-contracts.md) · [Example walkthrough](docs/demo-script.md) · [Production boundary](docs/production-boundary.md)

This is a synthetic local adapter: no production Lumos authentication or live remediation is implemented. The generalized workflow is executable; multi-tenant identity, remote authorization, and live product adapters remain production integration work.
