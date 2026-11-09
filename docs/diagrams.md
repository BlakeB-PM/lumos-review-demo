# ChatGPT access review

~~~mermaid
flowchart LR
    H[Reviewer] <--> U[Inline review panel]
    H <--> C[ChatGPT conversation]
    U <-->|Selected grants and focused follow-up| C
    U <-->|Queue, preview, confirmation and receipts| S[Lumos MCP]
    C <-->|Assigned grants, Albus rationale and policy| S
    C <-->|Read-only transcript lookup| P[Dana Personal Context MCP]
    T[Private synthetic call transcript] --> P
    S --> D[(Review and audit state)]
~~~

ChatGPT combines the authorized transcript and Lumos’s records. The review panel calls the Lumos tools through the MCP Apps bridge. The signed preview binds exact item IDs, outcomes, evidence and versions to a single run. ChatGPT and the panel show progress from Lumos receipts.

~~~mermaid
sequenceDiagram
    participant R as Reviewer
    participant C as ChatGPT
    participant U as Inline panel
    participant L as Lumos MCP
    participant P as Private context MCP
    R->>C: Help me do my access review
    C->>L: Open assigned review
    L-->>U: 15 offboarding grants and Alex’s two permissions
    R->>U: Select and preview offboarding grants
    U->>L: Preview exact selection
    R->>U: Confirm batch
    U->>L: Record signed batch
    L-->>U: 15 of 17 recorded
    R->>U: Check my work context for Alex
    U->>C: Ask about Alex’s current invoice follow-up duties
    C->>L: Read Albus’s original reasoning and policy
    C->>P: Find the call transcript
    P-->>C: Sales Ops took over invoice follow-up
    C->>L: Preview supported judgments using policy reason codes
    L-->>U: Accounts Receivable disagreement and Finance Admin agreement
    R->>U: Confirm both decisions
    U->>L: Record signed batch
    L-->>U: 17 of 17 recorded
~~~
