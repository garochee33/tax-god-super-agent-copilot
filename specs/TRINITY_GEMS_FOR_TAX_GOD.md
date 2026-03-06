# Trinity Consortium — GEMs for Tax God Upgrade

Source folder: **`/Users/enzogaroche/Downloads/TRINITY APP SOURCE /Trinity-Consortium`**

These components from the Trinity codebase are strong candidates to upgrade the current Tax God (AI Tax Copilot) system. Paths below are relative to that Trinity root.

---

## Implemented (wired in)

- **Step 1 — Cost Governor + Swarm Cost Planner**
  - `app/services/swarm_cost_planner.py`: `calculate_swarm_multiplier`, `create_swarm_cost_plan` (factors: worker_count, delegation_depth, expected_tool_calls, historical_variance; clamp 1.0–4.0).
  - `app/services/cost_governor.py`: `CostGateCode`, `CostGateResult`; `CostEstimate.gate_code`, `CostEstimate.swarm_plan`; kill switch (`engage_kill_switch` / `disengage_kill_switch`); swarm path uses `create_swarm_cost_plan` for cost and plan breakdown.
  - `POST /api/v1/analytics/estimate`: response includes `gate_code`, `swarm_plan`.
  - `POST /api/v1/analytics/governance/kill-switch`: body `{ "engage": true|false }` to engage/disengage kill switch.
  - Chat flow: estimate metadata includes `gate_code`, `swarm_plan` for observability.

- **Step 2 — Circuit Breaker**
  - `app/services/circuit_breaker.py`: `CircuitBreaker` with `can_execute`, `record_success`, `record_failure`, `reset_agent`, `get_status`. States: closed → open (on error threshold) → half-open (probe). 429/rate-limit failures do not count toward tripping.
  - QuickBooks: all four endpoints (company, profit-loss, balance-sheet, vendors) check circuit before call, `record_success` on success, `record_failure` in error path (with `is_rate_limit=True` for 429).
  - `app.state.circuit_breaker` registered in `main.py` with default config (50% threshold, 5 min window, 5 min pause, min 4 calls, 2 half-open probes).
  - `GET /api/v1/analytics/governance/circuit-breaker`: status. `POST /api/v1/analytics/governance/circuit-breaker/reset`: optional `agent_id` to reset one or all.

- **Step 3 — Advanced PDF + Document Intelligence**
  - `app/services/document_intelligence.py`: `extract_text_from_pdf(buffer)` → `PdfExtractionResult` (text, num_pages, tables, metadata); `extract_tables_from_text(text)` (Trinity ragflow-style pipe tables); `extract_pdf_text_only(buffer)`; `extract_entities_tax_doc(text)` for SSN/EIN/year hints.
  - `POST /api/v1/documents/ingest`: accepts PDF via multipart `file` or JSON `body.content_base64`; returns extracted text, tables, metadata, and optional `entities` (tax-doc hints). Max 20 MB. Used for client docs (W-2, 1099, workpapers) and RAG/Scrolls pipeline.
  - Dependency: `pypdf>=5.0.0` in requirements.txt.

---

## 1. AI cost & governance

| Gem | Path | What it does | Use in Tax God |
|-----|------|--------------|-----------------|
| **Cost Governor** | `server/ai/cost-governor.ts` | Hard/soft caps, approval flow, kill switch, budget reservation & settlement, idempotency. Dependency-free, deterministic. | Extend current `cost_governor.py`: add reservation/settlement phases, approval tokens, gate codes (e.g. `APPROVAL_REQUIRED`, `BUDGET_EXCEEDED_DAILY`). |
| **Swarm Cost Planner** | `server/ai/swarm-cost-planner.ts` | Non-linear swarm cost (fanout, delegation depth, tool usage, variance). Formula with weights; clamp 1.0–4.0. | Use for multi-agent / swarm tax workflows: estimate cost before dispatch; align with Pantheon cost estimate. |
| **Cost Enforcement Gate** | `server/ai/cost-enforcement-gate.ts` | Gate that blocks/approves based on cost governor. | Single place to “check before run” for chat and tools. |
| **Governance Gatekeeper** | `server/ai/governance-gatekeeper.ts` | Budget approval requests, threshold (e.g. $0.50), pending approvals, timeout, admin override. | Optional “approve over $X” for expensive research or batch jobs. |
| **Circuit Breaker** | `server/ai/circuit-breaker.ts` | Per-agent circuit (closed/open/half-open), error threshold %, window, pause, half-open probes. | Protect against repeated failures from one provider (e.g. research API, QuickBooks). |

---

## 2. Document intelligence & RAG

| Gem | Path | What it does | Use in Tax God |
|-----|------|--------------|-----------------|
| **Document Intelligence** | `server/ai/document-intelligence.ts` | Multimodal doc processing: extract text, entities, tables; optional chart/map analysis (Gemini). Writes to `documentVisualMetadata`. | Client doc intake: auto-extract from W-2s, 1099s, PDFs; feed Scrolls/Archives and RAG. |
| **Advanced PDF** | `server/ai/advanced-pdf.ts` | `pdf-parse` + table extraction (ragflow-style). Returns text, page count, tables, metadata. | Replace or complement current PDF handling for workpapers and client uploads. |
| **LlamaIndex RAG** | `server/integrations/llamaindex-rag.ts` | Vector index from Drive docs, `queryIndex()` with source nodes, document summaries. | RAG over tax docs and internal knowledge; cited answers in Oracle. |
| **Data Room** | `server/integrations/data-room.ts` | Drive + Object Storage: list/get docs, export MIME types, chunking, search. | Pattern for “client data room” (documents by client/year) plus caching. |

---

## 3. Agent tools & orchestration

| Gem | Path | What it does | Use in Tax God |
|-----|------|--------------|-----------------|
| **Oracle-style tools** | `server/ai/oracle-tools.ts` | Vault search (relational + text score, ACL, visual metadata), knowledge files, graph entities. Rich tool definitions with zod. | Template for “tax vault” search and cited retrieval in chat. |
| **Reporter tools** | `server/ai/reporter-tools.ts` | `generate_detailed_report` (PDF/DOCX/HTML/MD, sections, depth), `create_spreadsheet`, dashboard. Simulated but schema is production-ready. | Tax report generation (client letters, one-pagers, spreadsheets) as tools. |
| **Execution logger** | `server/ai/execution-logger.ts` | Start/complete execution, log tool calls (cost, latency, tokens), persist to DB, EventEmitter for streaming. | Audit trail and cost attribution per conversation/tool in Tax God. |
| **Composable tool engine** | `server/ai/composable-tool-engine.ts` | (Inferred from file list.) Composable tool registration and execution. | Central registry for research, compliance, documents, planning tools. |

---

## 4. Auth, security & middleware

| Gem | Path | What it does | Use in Tax God |
|-----|------|--------------|-----------------|
| **RBAC** | `server/auth/rbac.ts` | Roles (admin, operator, qp, legal, collaborator, investor), permissions (portal, docs, deals, compliance, swarm, admin). `expandPermissions()`. | Tax God roles: e.g. admin, preparer, reviewer, client; map to docs/chat/approvals. |
| **Rate limiter** | `server/middleware/rate-limiter.ts` | Sliding window per category (auth/api/admin), violation tracking, progressive penalty, Retry-After, threat tracker integration. | Stricter auth limits, per-route API limits, 429 with backoff. |
| **Governance rules** | `server/core/governance.ts` | Central constants: revenue split, fees, thresholds, compliance (retention, expiry). | Tax-specific rules: retention years, fee caps, client thresholds. |
| **Error handler** | `server/middleware/errorHandler.ts` | Central error handling and not-found. | Consistent API error shape and logging. |
| **Request context** | `server/middleware/requestContext.ts` | Request-scoped context (e.g. tenant, user). | Thread user_id / client_id through all AI and integration calls. |

---

## 5. Integrations (patterns)

| Gem | Path | What it does | Use in Tax God |
|-----|------|--------------|-----------------|
| **Google** | `server/integrations/google-*.ts` | Drive, Docs, Sheets, Calendar, Meet, Forms, Slides, Gmail, service account. | Same pattern for Gmail/Drive already in Tax God; extend with Sheets/Forms for questionnaires. |
| **SendGrid / Email** | `server/integrations/sendgrid.ts`, `email-service.ts` | Transactional email. | Client notifications, secure link emails. |
| **Stripe** | `server/integrations/stripe.ts` | Payments. | Billing for premium or per-return features. |

---

## 6. Observability & quality

| Gem | Path | What it does | Use in Tax God |
|-----|------|--------------|-----------------|
| **Braintrust swarm tracer** | `server/ai/braintrust-swarm-tracer.ts` | Braintrust integration for swarm traces. | Optional observability for multi-step tax workflows. |
| **Agent analytics** | `server/ai/agent-analytics.ts` | Analytics over agent runs. | Dashboards for usage, cost, and tool success. |
| **System log buffer** | `server/ai/system-log-buffer.ts` | In-memory log buffer for debugging. | Dev and support: recent request/response log. |

---

## Suggested adoption order

1. **Cost Governor + Swarm Cost Planner** — Align with existing cost governor; add reservation and swarm estimates.
2. **Circuit Breaker** — Wrap QuickBooks and future research/compliance APIs.
3. **Advanced PDF + Document Intelligence** — Client document pipeline for Scrolls/Archives and RAG.
4. **LlamaIndex RAG (or equivalent)** — RAG over tax docs and 2026 roadmap tools; cited Oracle answers.
5. **Execution logger** — Persist execution and tool calls for audit and cost.
6. **RBAC** — Introduce roles and permissions for preparer/reviewer/client.
7. **Rate limiter (progressive)** — Harden auth and API routes.
8. **Reporter tools** — Report generation (PDF/DOCX) as Oracle tools.

---

## Notes

- Trinity is **Node/Express + TypeScript**; Tax God is **Python/FastAPI**. Reuse **logic and contracts**, not code verbatim (port algorithms, API shapes, and DB schemas).
- Trinity uses **Drizzle** and a large `shared/schema`; Tax God uses **SQLAlchemy**. Map table ideas (e.g. `agent_executions`, `document_visual_metadata`) to existing or new models.
- References: Trinity `CURSOR_HANDOFF.md`, `package.json` (deps: LlamaIndex, pdf-parse, Braintrust, etc.).
