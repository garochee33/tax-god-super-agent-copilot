# Tax God Practical Next Backlog

This list keeps only high-value, near-term items for the current build.

## Keep (Already Valuable, Continue Hardening)

1. Cost governor with cache-first routing and budget modes.
2. AI orchestrator confidence scoring + escalation path.
3. OAuth integration manager with encrypted credential persistence.
4. ROI analytics endpoints (`/roi/calculate`, `/roi/project`).
5. Celery scheduler lane for token refresh and budget watchdog.

## Add Next (Highest Value, Build-Ready)

1. Durable conversation memory
   - Persist `ConversationState` into PostgreSQL.
   - Add retention policy and replay endpoint for support/audit.

2. Integration sync pipelines
   - Google: pull Gmail headers + Drive file metadata into normalized tables.
   - QuickBooks: nightly P&L, balance sheet snapshots with diffing.

3. OpenClaw execution bridge
   - Add queue-based handoff API for `routing_path=openclaw_swarm`.
   - Track per-subtask latency/cost and aggregate into analytics.

4. Regulatory monitor v1
   - Add actual source collectors (IRS newsroom + selected state feeds).
   - Hash-based change detection + alert generation endpoint.

5. Security hardening
   - Rotate integration encryption key via key versioning.
   - Add HMAC request signatures for internal task endpoints.
   - Add strict RBAC around integration endpoints.

6. Delivery reliability
   - Retries/backoff policy for all outbound API integrations.
   - Dead-letter queue for failed Celery tasks with replay command.

7. CI quality gate
   - Add pipeline: `pytest`, compile check, Ruff, and minimal API smoke tests.

## Defer (Lower Immediate ROI)

1. Full CRM and outbound campaign automation.
2. Multi-region deployment and advanced autoscaling.
3. Complex frontend redesign beyond current usability needs.

