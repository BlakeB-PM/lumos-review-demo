# Lumos access reviews

A local prototype of a reusable reviewer experience: Lumos provides exact grants, recommendations, policy and evidence; the personal agent resolves open questions using its authorized context. The reviewer edits and confirms an exact proposal. Decisions and remediation remain separate.

All scenarios use the same MCP tools and inline panel. Names, permissions and scenario facts live in fixture data, not tool schemas or workflow instructions. The default fixture includes 17 permissions; `tour` has 36, `warehouse` has eight, and `slack` has 240 synthetic memberships. The personal-context connector is an optional synthetic source, not a required product integration.

## Run locally

Use Python 3.10+ and follow [connection setup](docs/connect-reviewer.md). Start with any natural request, for example:

> Investigate my pending access review and prepare supported recommendations.

The inline panel separates permissions ready for batch review from those needing individual investigation. The page checkbox selects or clears only the displayed page. Open evidence from a permission row or a shared batch, ask the agent to investigate, or choose **Decide manually** to enter actions and audit reasons alongside the selected rows. Use **More actions → Defer selected** to leave grants pending with a reason.

Before recording, **Review audit entries** shows exactly what will be saved for each permission. After recording, verify the saved reasons and receipt IDs before continuing. Hosts that render MCP Apps show the inline panel. The same tools support text-only hosts.

```sh
python server/src/main.py report --open
python evaluation/verify.py
```

Reset is a separate operator action, never part of opening a review:

```sh
python server/src/main.py reset --scenario chatgpt
```

For rendered UI checks, install Playwright in your test environment and run `node evaluation/ui.cjs` (set `CHROME` to your browser executable on other platforms). This uses isolated state and a simulated MCP Apps host; it does not replace testing inside each supported host.

The browser workspace and MCP share proposals, receipt state, evidence freshness checks, and deferrals. Use the same `--scenario` and `--state` for both. [Tool contracts](docs/tool-contracts.md) · [Example walkthrough](docs/demo-script.md) · [Production boundary](docs/production-boundary.md)

This is a synthetic local adapter: no production Lumos authentication or live remediation is implemented. The generalized workflow is executable; multi-tenant identity, remote authorization, and live product adapters remain production integration work.
