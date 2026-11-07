# Local access review flow

~~~mermaid
flowchart LR
    H[Reviewer] <--> C[Codex desktop]
    P[Synthetic personal notes] --> C
    C <-->|stdio MCP| S[Local review server]
    F[Assigned items and stored recommendations] --> S
    K[Markdown policies, approvals and evidence] --> S
    S -->|Scoped item and evidence| A[Optional scripted Ask Albus]
    A -->|Cited investigation| S
    S -->|Version checks and per-item transactions| D[(SQLite audit and decisions)]
    D -->|Read-only live view| R[Browser audit report]
~~~

~~~mermaid
sequenceDiagram
    participant H as Reviewer
    participant C as Codex
    participant S as Review server
    H->>C: Help me complete my access review
    C->>S: Start demo and reset synthetic state
    S-->>C: Clean campaign, eight items and new run ID
    C->>S: Read assigned reviews and evidence
    C->>H: Show proposed batch and pending questions
    H->>C: Confirm exact batch
    C->>S: Submit item IDs, versions, evidence and key
    S-->>C: Receipts and refresh required for stale item
    C->>S: Read fresh snapshot and owner evidence
    C->>H: Show recorded receipts and revised proposal
~~~
