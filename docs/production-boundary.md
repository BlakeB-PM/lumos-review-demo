# Production integration boundary

## Implemented locally

A host-neutral workflow and panel; data-derived groups; policy/evidence briefs; editable/excludable proposals; durable deferral; externally attributed optional context summaries; same proposal contract in browser and chat; run/reviewer/client binding; 30-minute expiry; per-item evidence fingerprints; partial results; idempotent receipts. The verification suite exercises different fixtures and entirely new identities and permissions without changing tool schemas.

## Required for a deployed service

- Replace the single assigned fixture campaign with authenticated tenant/reviewer scope and assigned-campaign discovery. Enforce permissions on every read, prepare, defer and record; never trust IDs or host labels as credentials.
- Use an authenticated remote transport and the MCP authorization model. Bind proposals to tenant, authenticated principal, session and permitted action scopes. Determine whether the chosen host's confirmation signal is sufficient or whether an authenticated approval surface is required.
- Load live grants, policy, exceptions and recommendations through product adapters. Persist immutable evidence revisions and use transactional version checks across workers. Cache invalidation and the remediation job lifecycle need production storage/queue integration.
- Separate recorded decisions from queued, succeeded and failed remediation. Implement reconciliation and an auditable correction/reversal workflow rather than overwriting receipts.
- Define context-sharing policy and retention. The prototype restricts structure and asks for minimal authorized summaries, but free-text fields can still contain sensitive material. Production needs suitable redaction, access controls and disclosure enforcement. Do not claim the absence of raw context merely from use of this schema.
- Verify host capability negotiation and approval behavior on each supported client. Test keyboard, screen-reader, narrow-layout and reconnect behavior in those hosts. The local UI harness verifies the component bridge, not every host integration.
- Run agent evaluations with unavailable, stale, conflicting and malicious source text. Tool tests verify mechanics; they do not prove semantic judgment or private-source handling by every model.

Do not call this adapter production-ready. It models the intended reusable experience without pretending fixture identity is authentication or a client assertion is human proof.
