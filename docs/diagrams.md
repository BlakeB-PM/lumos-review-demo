# Reviewer workflow across surfaces

~~~mermaid
flowchart LR
    H[Reviewer] <--> C[ChatGPT Work or Claude Cowork]
    P[Private reviewer inbox] --> C
    C <-->|Assigned review, evidence search, staged and confirmed decisions| S[Lumos demo MCP server]
    F[Albus suggestions, policies and approvals] --> S
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
    Note over H,C: Private handoff says Nora is the primary operator
    C->>S: Look up approval SEC-217
    S-->>C: Exact grant, effective dates and operator condition
    C->>H: Explain proposed override and ask about missing renewal
    H-->>C: Leave renewal pending and authorize audit-safe summary
    C->>S: Stage exact batch
    C->>H: Show decisions and ask for confirmation
    H-->>C: Confirm
    C->>S: Record the approved proposal ID
    S-->>C: Decision receipts
    H->>U: Open Reviewed and inspect Nora's receipt
    H->>U: Complete remaining sandbox permission
    C->>S: Fetch current status
    S-->>C: Receipts from both surfaces
~~~
