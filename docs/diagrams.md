# Lumos access reviews — architecture and workflow diagrams

**Scope:** This document illustrates the **synthetic local prototype**, not a deployed Lumos integration. It complements the [interactive architecture in Miro](https://miro.com/app/board/uXjVESqFoRg=/?moveToWidget=3458764689933058696), [shared tool contracts](tool-contracts.md), [demo walkthrough](demo-script.md), and [production integration boundary](production-boundary.md).

The product idea is consistent across hosts and fixtures: **Lumos supplies authoritative access grants, Albus recommendations, policies, and dated evidence; a personal agent can add permitted reviewer-specific context; the human reviews an exact proposal; Lumos records decisions and receipts.** A chat conversation is useful for investigation, while the panel supports high-volume queue management and batch decisions.

**Notation:** Solid paths are represented in the local prototype. The last diagram explicitly labels additional production controls as **required / not implemented**. Diagram names represent logical roles; the fixture identity and SQLite state are *not* production identity or storage.

## 1. System context and trust boundaries

The inline panel and conversational agent reach the **same review workflow** through an MCP-capable host. The local browser report also uses that workflow against shared scenario state.

```mermaid
flowchart LR
  subgraph personal["Reviewer environment"]
    Human["Reviewer"]
    Sources["Authorized private work context<br/>notes, handoffs, optional connector"]
    Agent["Personal AI agent"]
    UI["Inline review panel<br/>queue, evidence, audit preview"]
    Human --> Agent
    Human --> UI
    Sources -->|"read when authorized"| Agent
    UI <-->|"investigate prompts"| Agent
  end
  subgraph host["MCP-capable host"]
    Bridge["MCP client and UI bridge<br/>tools/call, structuredContent, UI resource"]
  end
  subgraph demo["Synthetic Lumos adapter - local"]
    Server["Local Lumos MCP server"]
    Workflow["Shared review workflow"]
    Fixtures[("Fixture grants, Albus recommendations,<br/>policy and dated evidence")]
    DB[("SQLite: run, proposals, fingerprints,<br/>deferrals, attempts and receipts")]
    Report["Browser review and audit report"]
    Server <--> Workflow
    Workflow --> Fixtures
    Workflow <--> DB
    Report <--> Workflow
  end
  Agent <--> Bridge
  UI <--> Bridge
  Bridge <-->|"MCP tools and panel resource"| Server
```

**Important:** The personal agent does not grant access. The server owns review records and decision recording. Actual downstream access removal is **simulated** and separate from the recorded decision. Private source excerpts should stay in the reviewer environment; the tool can receive only an optional, reviewer-authorized minimal summary, which Lumos labels as external information.
## 2. Reviewer experience — fast queue plus targeted investigation

The panel is deliberately **not** a hundred-message chatbot. Dynamic grouping, pagination, shared rationale, and individual overrides make routine work fast while leaving unclear items open.

```mermaid
flowchart TD
  Start["Reviewer asks to open or resume access review"] --> Open["open_access_review<br/>counts, derived groups, suggested start"]
  Open --> Queue["Inline panel: progress, groups, exact permissions"]
  Queue --> Group["get_review_group<br/>paged records and original recommendations"]
  Group --> Choice{"How does reviewer handle item or group?"}
  Choice -->|"Enough Lumos evidence"| Direct["Direct or shared-batch decision<br/>with per-permission overrides"]
  Choice -->|"Need investigation"| Context["get_review_context / get_evidence<br/>policy, dates, source excerpts and open questions"]
  Context --> Agent["Agent checks relevant authorized work context<br/>and explains where assessment differs"]
  Agent --> Supported{"Sufficient current evidence?"}
  Supported -->|"Yes"| Direct
  Supported -->|"No or conflicting"| Pending["Keep pending or defer_review_items<br/>with reviewer-requested reason"]
  Choice -->|"Not ready"| Pending
  Direct --> Prepare["prepare_review_batch<br/>stage 1-50 exact decisions"]
  Prepare --> Preview["Review audit entries<br/>actions, reasons, source refs, optional shared summary"]
  Preview --> Edit{"Reviewer confirms exact proposal?"}
  Edit -->|"Edit or exclude"| Direct
  Edit -->|"Confirm"| Record["record_review_batch<br/>revalidate proposal and evidence"]
  Record --> Status["get_review_status<br/>receipts, failures and remaining queue"]
  Pending --> Queue
  Status --> Queue
```

**Product behavior:** Grouping is navigation based on recommendations and evidence; the interface must not imply the AI independently endorsed every grouped item. A deferral is not an approval, revocation, or change to underlying access.
## 3. MCP interaction sequence — investigation to audited decision

This is the detailed handoff between chat, UI, MCP tools and the shared review workflow. **Preparation is not submission.** The demo accepts client-reported confirmation; deployed verification must be stronger.

```mermaid
sequenceDiagram
  autonumber
  actor R as Reviewer
  participant P as Inline panel
  participant A as Personal agent
  participant H as Host MCP bridge
  participant L as Lumos MCP adapter
  participant W as Review workflow / SQLite
  participant C as Authorized work sources
  R->>A: Help me with my access review
  A->>H: open_access_review
  H->>L: tools/call
  L->>W: Read assigned synthetic campaign and group counts
  W-->>L: Run ID, review, groups and progress
  L-->>H: structuredContent + panel resource
  H-->>P: Render review overview
  R->>P: Open group and view evidence
  P->>H: get_review_group / get_review_context
  H->>L: tools/call
  L->>W: Read exact grants, recommendations, policy and evidence
  W-->>P: Evidence via MCP bridge
  R->>P: Investigate selected permission
  P->>A: ui/message with selected scope
  A->>H: get_review_context / get_evidence
  H->>L: tools/call
  L-->>A: Lumos evidence through host
  opt Reviewer authorized relevant external sources
    A->>C: Consult private context
    C-->>A: Relevant work facts, possibly conflicting
  end
  A-->>R: Explain evidence, uncertainty and proposed rationale
  opt Explicit authorization to share minimal external summary
    R-->>A: Approve proposed summary wording
  end
  A->>H: prepare_review_batch with exact rows and citations
  H->>L: tools/call
  L->>W: Validate scope, versions, cited sources; stage proposal
  W-->>L: Immutable proposal ID and expiry
  L-->>P: Preview via host bridge
  P-->>R: Review audit entries and edit or exclude
  alt Reviewer changes rows
    R->>P: Amend selection, decision or reason
    P->>H: prepare_review_batch with revised exact rows
    H->>L: tools/call
    L-->>P: New proposal through host
  else Reviewer confirms exact proposal
    R->>P: Confirm
    P->>H: record_review_batch(proposal_id)
    H->>L: tools/call
    L->>W: Recheck proposal, evidence and item fingerprints
    W-->>L: Per-item receipts or refresh-required failures
    L-->>P: Results via host
    P-->>R: Recorded decisions, unresolved items and receipts
  end
```

**Safety boundary:** The personal agent may reason using work context, but server-side evidence/version checks do **not** establish that the agent's semantic judgment is correct. Actual proof of human confirmation and permission enforcement across tenants require production integration.
## 4. Exact proposal lifecycle — edits, expiry and safe retries

The workflow is intentionally two-stage. A proposal is tied to the current run, campaign, reviewer, client profile, original recommendation and evidence fingerprint; edits create a **new proposal**. Recording can return partial results.

```mermaid
flowchart TD
  Items["Current items, run ID, versions and evidence refs"] --> Stage["prepare_review_batch<br/>1-50 supported decisions"]
  Stage --> Valid{"Inputs and citation scope valid?"}
  Valid -->|"No"| Fix["Correct affected decisions or leave pending"]
  Fix --> Stage
  Valid -->|"Yes"| Frozen["Stored proposal ID<br/>exact rows + 30-min expiry + fingerprints"]
  Frozen --> Preview["Reviewer inspects full audit preview"]
  Preview -->|"Edit / exclude"| Stage
  Preview -->|"Decline or leave"| Pending["No decision recorded; items remain pending"]
  Preview -->|"Explicit confirm"| Record["record_review_batch using proposal ID"]
  Record --> Recheck{"Current run, client, expiry,<br/>record and evidence still match?"}
  Recheck -->|"Stale, expired or reset"| Refresh["Refresh evidence / review status<br/>prepare and confirm new proposal"]
  Refresh --> Stage
  Recheck -->|"Valid"| Attempt["Record each item independently<br/>with idempotent per-item attempt"]
  Attempt --> Outcome{"Item result"}
  Outcome -->|"Recorded"| Receipt["Immutable decision receipt"]
  Outcome -->|"Already recorded"| Receipt
  Outcome -->|"Item error"| Retry["Surface item failure; pending<br/>or refresh as required"]
  Retry --> Stage
  Receipt --> Status["get_review_status<br/>progress, attempts and receipts"]
  Status --> Remediation["Separate remediation lifecycle<br/>not performed in simulation"]
```

**Retry semantics:** When delivery is uncertain, retry the **same** confirmed proposal ID instead of creating a second write. Successful per-item receipts are recoverable; a stale or expired item needs refreshed evidence and new confirmation. This does not imply atomic, all-or-nothing batches.
## 5. Evidence provenance, privacy and audit responsibilities

The two evidence domains are intentionally distinct. **Lumos evidence** is authoritative for grants, recommendations and policy. **Work-context information** is independently assessed by the agent and must not be represented as Lumos-verified evidence.

```mermaid
flowchart LR
  subgraph ext["Reviewer-controlled environment"]
    E["Private work sources<br/>notes, messages, handoffs"]
    A["Personal agent<br/>assess relevance, freshness and conflicts"]
    S["Minimal optional summary<br/>explicit reviewer authorization"]
    E --> A --> S
  end
  subgraph lumos["Lumos decision system"]
    F["Grants, Albus recommendation,<br/>policy and dated Lumos evidence"]
    P["Scoped proposal with exact action,<br/>rationale and cited evidence"]
    G["Recheck run, item and evidence<br/>at record time"]
    R["Decision receipt and audit history"]
    F --> P --> G --> R
  end
  S -->|"If authorized; external/unverified"| P
  Human["Human reviewer"] -->|"inspect and confirm exact proposal"| G
  R --> Ops["Remediation tracking - separate<br/>simulated only in prototype"]
```

**Limit:** The local tool schema does not guarantee that free text is redacted or privacy-safe. The reviewer/agent process must avoid transmitting raw private source excerpts; a production service needs its own disclosure controls, retention policy and provenance validation.
## 6. Production deployment gap — not built by this prototype

This diagram is **requirements architecture**, not a claim of deployed functionality. It separates what the demo proves from the work necessary before a real enterprise access review can safely run through customers' agents.

```mermaid
flowchart LR
  subgraph simulated["Demonstrated locally"]
    Demo["Synthetic campaigns and identity<br/>local stdio MCP + panel"]
    Workflow["Common review workflow<br/>prepared proposals and receipts"]
    Store["SQLite and fixture evidence"]
    Demo --> Workflow --> Store
  end
  subgraph needed["Required for production - not implemented"]
    Auth["Authenticated remote MCP transport<br/>tenant + principal + delegated scopes"]
    Adapter["Live Lumos grants, Albus,<br/>policy and immutable evidence revisions"]
    Approval["Verifiable reviewer approval<br/>bound to exact proposal"]
    Data["Transactional shared persistence<br/>idempotency and audit retention"]
    Privacy["Personal-context disclosure policy<br/>redaction, provenance, retention"]
    Remediate["Asynchronous remediation<br/>status, failure and reconciliation"]
    Eval["Host compatibility + accessibility<br/>adversarial and semantic evaluations"]
    Auth --> Adapter
    Adapter --> Approval
    Approval --> Data
    Data --> Remediate
    Privacy --> Approval
    Eval --> Approval
  end
  Workflow -.->|"replace local assumptions with"| Auth
```

**First pilot boundary:** Focus on assigned reviewer decisions with human confirmation, not autonomous campaign scoping/launch or unrestricted agent delegation. See [production-boundary.md](production-boundary.md) for the release prerequisites and limitations.

## Demo and implementation references

- [Demo walkthrough](demo-script.md) — step-by-step review and exception investigation.
- [MCP tool contracts](tool-contracts.md) — exact tool names, proposal constraints and evidence rules.
- [Production integration boundary](production-boundary.md) — explicit local-versus-deployed limitations.
- [Miro implementation architecture](https://miro.com/app/board/uXjVESqFoRg=/?moveToWidget=3458764689933058696) — canvas view of the current local architecture.
