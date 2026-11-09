# Lumos access review demo

A synthetic Active Directory review for a local chat in the ChatGPT desktop app. The reviewer inspects and confirms **15 verified offboarding rejects** in one batch, then compares Albus and ChatGPT on **Alex Rivera’s two remaining grants**. A private call transcript explains that Alex looked up an invoice while handing work to Sales Ops.

## Run locally

Install Python 3.10+ and the Codex CLI, then follow the [local connection guide](docs/connect-reviewer.md). Open this repository’s **personal-workspace** folder as a local project. Start a fresh local chat in that project and say:

> Help me do my access review.

The first tool call should be `open_access_review`, with **17 grants** in the overview. The MCP ships an inline review panel for hosts that render MCP Apps UI. The same tools support review and confirmation in conversation when a local client renders only tool results. [Demo walkthrough](docs/demo-script.md)

## Audit, reset, and verify

Run these commands from the repository root as needed.

~~~sh
python server/src/main.py report --open
python server/src/main.py reset --scenario chatgpt
python evaluation/verify.py
~~~

The local audit report shares state with the connector and shows original recommendations, recorded decisions, and evidence. Reset is a separate operator action that clears the synthetic run. Opening the review resumes existing state. The verifier uses temporary state.

The transcript is read through a separate connector. Lumos accepts bounded judgment codes for Alex and records a policy-based reason. All data and decisions are synthetic. Access removal is simulated. [Tool contracts](docs/tool-contracts.md) · [Workflow diagram](docs/diagrams.md)
