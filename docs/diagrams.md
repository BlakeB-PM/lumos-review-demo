# Reviewer workflow across surfaces

~~~mermaid
flowchart LR
    H[Reviewer] <--> C[Personal agent]
    P[Simulated private inbox] --> M[Dana Personal Context MCP]
    C <-->|Read-only lookup by person and topic| M
    C <-->|Assigned review, evidence, staged and confirmed decisions| S[Lumos demo MCP server]
    F[Albus suggestions, directory and usage evidence] --> S
    K[Simulated Lumos Knowledge Hub] --> S
    S --> D[(Shared SQLite audit and decisions)]
    R[Access Reviews workspace] <-->|Read and record decisions| D
~~~

The two services run in separate processes. The personal context service reads the synthetic inbox. The Lumos service reads the campaign, policy and Knowledge Hub fixtures, and writes confirmed decisions. The agent combines the results. The personal message stays on the agent side of the review.

Codex and Claude Cowork can run both connections locally. Hosted ChatGPT Work can run the same flow with two workspace-scoped Secure MCP Tunnels and two plugins.

~~~mermaid
sequenceDiagram
    participant H as Reviewer
    participant C as Personal agent
    participant P as Dana Personal Context MCP
    participant S as Access Reviews MCP
    participant U as Product workspace
    H->>C: Help me complete my access review
    C->>S: Read the 36-permission queue and Albus suggestions
    C->>S: Verify the reasons against the evidence
    S-->>C: Knowledge Hub guidance, policy, recent invoice lookup
    C->>P: Search Alex Rivera for invoice follow-up
    P-->>C: Private handoff says the work moved to Sales Ops
    C->>S: Stage Alex’s two rejections with policy-based notes
    C->>H: Show both actions and notes for confirmation
    H-->>C: Confirm
    C->>S: Record the approved proposal ID
    S-->>C: Decision receipts
    H->>U: Open Reviewed and inspect the saved decisions
    C->>H: Draft an IT request to update the Knowledge Hub
~~~
