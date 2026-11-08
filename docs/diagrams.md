# Reviewer workflow across surfaces

~~~mermaid
flowchart LR
    H[Reviewer] <--> C[ChatGPT Work or Claude Cowork]
    P[Personal sales handoff] --> C
    C <-->|Assigned review, evidence, staged and confirmed decisions| S[Lumos demo MCP server]
    F[Albus suggestions, directory and usage evidence] --> S
    S --> D[(Shared SQLite audit and decisions)]
    R[Access Reviews workspace] <-->|Read and record decisions| D
~~~

ChatGPT Work reaches MCP through a workspace-associated Secure MCP Tunnel. Claude Cowork can use a local stdio plugin. Codex retains its original local connector.

~~~mermaid
sequenceDiagram
    participant H as Reviewer
    participant C as Work or Cowork
    participant S as Access Reviews MCP
    participant U as Product workspace
    H->>C: Help me complete my access review
    C->>S: Read assigned permissions and Albus suggestions
    C->>S: Verify the reasons against the evidence
    S-->>C: Sales role, Finance Admin policy, recent invoice lookup
    Note over C: Personal handoff says invoice follow-up moved to Sales Ops
    C->>S: Stage two rejections with audit notes
    C->>H: Show both actions and notes for confirmation
    H-->>C: Confirm
    C->>S: Record the approved proposal ID
    S-->>C: Decision receipts
    H->>U: Open Reviewed and inspect the saved decisions
~~~
