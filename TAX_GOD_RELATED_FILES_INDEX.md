# Tax God / Tax Copilot / Tax Assistant / Agent Cost — File & Code Index

This index lists **all files and code** in this workspace related to **Tax God**, **tax copilot**, **tax assistant**, **agent cost**, and **tax-god-agent**. The project root is `tax-god-super-agent-copilot` (GitHub: garochee33/tax-god-super-agent-copilot).

---

## 1. Repo & project identity

| Item | Location / value |
|------|------------------|
| **Workspace** | `~/DSH/projects/tax-god-super-agent-copilot` |
| **App name** | `Tax God` (see `app/core/config.py`: `APP_NAME`, `APP_VERSION = "3.0.0"`) |
| **Database default** | `taxgod` / `taxgod123` (config.py) |
| **Celery app name** | `tax_god` (app/tasks/celery_app.py) |
| **Prometheus metrics** | `taxgod_http_requests_total`, `taxgod_http_request_latency_seconds`, `taxgod_service_up` (app/main.py) |
| **Frontend client id** | `taxgod_client_id`, `taxgod_api_base`, `window.taxGodApp` (app/static/js/app.js) |

---

## 2. Specs & documentation (Tax God / deployment / backlog)

| File | Description |
|------|-------------|
| **specs/TAX-GOD-COMPLETE-DEPLOYMENT-SPEC.md** | Full deployment spec: multi-agent architecture, Cost Governor, 79+ services, OpenClaw swarm, cost governance |
| **specs/TAX-GOD-COMPLETE-DEPLOYMENT-SPEC.html** | HTML version of the same spec |
| **specs/TAX_GOD_IMPLEMENTATION_SUMMARY_v2.md** | Implementation package summary (FastAPI backend, Docker stack, models, API list) |
| **specs/TAX_GOD_IMPLEMENTATION_SUMMARY.md** | Same content (v1) |
| **specs/TAX_GOD_IMPLEMENTATION_SUMMARY_v1.md** | Same content (v1) |
| **specs/PRACTICAL_NEXT_BACKLOG.md** | Tax God backlog: Cost Governor, Agent Gabriel, ROI, OpenClaw, regulatory monitor, etc. |
| **specs/BACKEND_INTEGRATIONS_AND_ALGORITHMS.md** | Tax God backend: OAuth, ROI, Cost Governance routing metadata, env vars |
| **specs/DEEP-RESEARCH-ANALYSIS.md** | Deep research for the system |
| **specs/README_ADDED_FILES.md** | README for added spec files (incl. swarm/repo_map) |
| **specs/tax-god-ui-mockup-dashboard.html** | Tax God UI mockup dashboard |
| **IMPLEMENTATION_PLAN.md** | Tax God v3.0 implementation plan: DTDA/IMRA/SHVA, Trinity, Cost Governor, copilot |
| **LOCAL_DOCKER_SETUP.md** | Local Docker setup for the stack |
| **COMMANDS.md** | Project commands |
| **QUICKSTART.md** | Quick start guide |

---

## 3. Cost Governor (agent cost / budget / routing)

| File | Role |
|------|------|
| **app/services/cost_governor.py** | **Tax God – Cost Governor**: pre-flight cost estimation, model selection, 4-tier cache, per-client/system budget, usage tracking, progressive complexity. Defines `CostGovernor`, `CostEstimate`, `UsageRecord`, `ModelSpec`, `ComplexityLevel`, `RoutingPath`. |
| **app/core/config.py** | Cost Governor settings: `COST_SOFT_LIMIT_*`, `COST_HARD_LIMIT_DAILY`, `COST_EMERGENCY_RESERVE`, `CACHE_HIT_TARGET`, `SWARM_*`, `COST_SWARM_*`. |
| **app/main.py** | Instantiates `CostGovernor(redis_client)`, attaches to `app.state.cost_governor`, wires to `AIOrchestrator` and `AdvancedTaxOrchestrator`. |
| **app/services/ai_service.py** | Uses `CostGovernor`: estimate → select model → record usage. All LLM flow goes through governor. |
| **app/services/advanced_orchestrator.py** | Holds `cost_governor: CostGovernor`, passes to fallback `AIOrchestrator`. |
| **app/api/v1/endpoints/analytics.py** | **Tax God API – Analytics, Cost Governance, ROI**: `/usage`, `/budget/{client_id}`, `/estimate` (pre-flight cost estimate). All use `request.app.state.cost_governor`. |
| **app/tasks/ops_tasks.py** | Background tasks use `CostGovernor(redis_client)` for budget watchdog. |

---

## 4. Agent Gabriel (tax audit / review agent)

| File | Role |
|------|------|
| **app/services/agent_gabriel.py** | **Tax God – Agent Gabriel**: audit & review agent. Flags errors, audit risk, savings; scores return quality; generates recommendations. Defines `AgentGabriel`, `AuditReport`, `AuditFlag`, `FlagSeverity`, `FlagCategory`. |
| **app/main.py** | Creates `AgentGabriel(ai_orchestrator, citation_engine)`, exposes as `app.state.agent_gabriel`. |
| **app/api/v1/endpoints/audit.py** | **Tax God API – Agent Gabriel (Audit)**: endpoints to run Gabriel audit on a tax return. |
| **app/static/js/pages/tribunal.js** | UI: “Agent Gabriel is weighing the evidence...” |

---

## 5. Tax God AI / copilot / assistant (orchestration & chat)

| File | Role |
|------|------|
| **app/services/ai_service.py** | **Tax God – AI Orchestration**: “brain” of Tax God. Multi-role prompts (Tax God co-pilot, Tax Compliance, Legal Counsel, Financial Analyst, Research, Audit Defense). Cost Governor–aware execution. |
| **app/api/v1/endpoints/chat.py** | **Tax God API – AI Chat**: submit tax/legal/financial questions to Tax God. |
| **app/services/advanced_orchestrator.py** | **Tax God – Advanced AI Orchestrator** with DTDA integration; uses Cost Governor. |
| **app/services/citation_engine.py** | **Tax God – Citation Engine**: grounds responses in verifiable sources. |
| **app/services/tax_writer.py** | **Tax God – Tax Writer**: “Tax God AI Advisory”, “Generated by Tax God AI Advisory System v3.0”, firm_name="Tax God AI Advisory". |
| **app/services/parallel_processor.py** | **Tax God – Parallel Processor**. |

---

## 6. Core app & config (Tax God branding / DB)

| File | Role |
|------|------|
| **app/main.py** | **Tax God v3.0** FastAPI entry: lifespan, Cost Governor, Agent Gabriel, metrics (`taxgod_*`), health (“cost_governor”, “agent_gabriel”). |
| **app/core/config.py** | **Tax God** config: `APP_NAME = "Tax God"`, `APP_VERSION`, DB URLs (`taxgod`), Cost Governor section. |
| **app/core/database.py** | **Tax God – Database Setup**. |
| **app/core/security.py** | **Tax God – Security Utilities**. |
| **app/core/crypto.py** | Crypto utilities (used by integrations). |

---

## 7. API endpoints (all Tax God API)

| File | Description |
|------|-------------|
| **app/api/v1/endpoints/advanced.py** | Tax God – Advanced Tax Processing API. |
| **app/api/v1/endpoints/analytics.py** | Analytics, Cost Governance, ROI. |
| **app/api/v1/endpoints/audit.py** | Agent Gabriel (Audit). |
| **app/api/v1/endpoints/auth.py** | Authentication (register, login, JWT tokens, refresh, dev-token). |
| **app/api/v1/endpoints/clients.py** | Client Management (Agora) — full CRUD, pagination, search. |
| **app/api/v1/endpoints/chat.py** | AI Chat. |
| **app/api/v1/endpoints/documents.py** | Tax God API – Document Processing. |
| **app/api/v1/endpoints/integrations.py** | Tax God API – Integrations (“Tax God Integration Connected”, “return to Tax God”). |

---

## 8. Frontend / static (Tax God UI)

| File | Role |
|------|------|
| **app/templates/index.html** | Title “Tax God - Olympus Dashboard”, logo “TAX GOD”. |
| **app/static/css/olympus.css** | “Tax God - Greek Mythology Theme”. |
| **app/static/js/app.js** | `taxgod_client_id`, `taxgod_api_base`, `window.taxGodApp`. |
| **app/static/js/pages/pantheon.js** | “Tax God control plane”. |
| **app/static/js/pages/oracle.js** | AI Chat Interface — conversation, citations. |
| **app/static/js/pages/tribunal.js** | Agent Gabriel audit defense UI. |
| **app/static/js/pages/hermes.js** | Client communication interface. |
| **app/static/js/pages/scrolls.js** | Document generation — memos, IRS responses. |
| **app/static/js/pages/archives.js** | Tax law search & archives. |
| **app/static/js/pages/agora.js** | Client Management — CRUD, search, pagination. |

---

## 9. Tasks & workers

| File | Role |
|------|------|
| **app/tasks/celery_app.py** | Celery bootstrap for **Tax God** background processing (`tax_god`). |
| **app/tasks/ops_tasks.py** | **Tax God** operational tasks; uses Cost Governor. |
| **app/tasks/__init__.py** | Tax God task package. |

---

## 10. Algorithms (DTDA, IMRA, SHVA – referenced by Tax God spec)

| File | Role |
|------|------|
| **specs/algorithms/dtda.py** | Dynamic Task Decomposition Algorithm. |
| **specs/algorithms/imra.py** | Intelligent Memory Retrieval Algorithm. |
| **specs/algorithms/shva.py** | Self-Healing Validation Algorithm. |
| **specs/algorithms/README.md** | Algorithms overview. |
| **test_algorithms.py** | Tests for algorithms. |

---

## 11. Swarm / orchestration (OpenClaw / multi-agent)

| Path | Description |
|------|-------------|
| **specs/swarm/** | Swarm tools (repo_map, openai_responses, shell, llm, codex_cli, etc.), config, agents (refactor, bugfix, docs, feature, review, tests), orchestrator, state. |
| **specs/swarm_runner/** | Swarm runner: providers (OpenAI, Anthropic, xAI, Gemini), agents (e.g. implementer, security), supervisor, fractal, oracle. |
| **integrations/trinity-consortium-full/** | Trinity Consortium (55-agent architecture) integration docs; referenced in implementation plan. |

---

## 12. Other related files

| File | Role |
|------|------|
| **app/services/roi_engine.py** | ROI calculation and projection (used by analytics endpoints). |
| **app/services/integrations/** | Google, QuickBooks, manager, base (OAuth, encrypted credentials). |
| **requirements.txt** | "Tax God v3.1 - Python Dependencies" (includes aiosqlite for test support). |
| **Dockerfile** | Backend image. |
| **docker-compose.yml** | Full stack (API, Postgres, Redis, Neo4j, Elasticsearch, etc.). |
| **launch_docker.sh**, **launch_simple.sh** | Launch scripts. |
| **monitoring/prometheus.yml** | Prometheus config for metrics. |
| **test_trinity_integration.py** | Trinity integration tests. |
| **app/models/client.py** | Client model — owner_id, name, email, phone, company, tax_id, filing_type, status, notes. |
| **alembic/versions/002_add_clients.py** | Clients table migration. |

---

## 13. Test suite (46 tests)

| File | Coverage |
|------|----------|
| **tests/conftest.py** | Fixtures: async SQLite in-memory DB, user/admin creation, auth headers, rate limiter bypass, mock services. |
| **tests/test_auth.py** | Auth endpoints — register, login, refresh, /me, logout, dev-token, invalid inputs (14 tests). |
| **tests/test_chat.py** | Chat/AI endpoints — query, god mode, citations search, auth enforcement (6 tests). |
| **tests/test_documents.py** | Document processing — PDF ingest, batch, multi-state, scenario analysis (7 tests). |
| **tests/test_analytics.py** | Analytics — circuit breaker, kill switch, usage, ROI calculate/project, RBAC (8 tests). |
| **tests/test_e2e_pipeline.py** | Full pipeline — register → login → create client → chat → scenario → ROI → refresh (1 test). |
| **tests/test_cost_governor.py** | Cost governor unit tests. |
| **tests/test_roi_engine.py** | ROI engine unit tests. |
| **tests/test_integration_manager.py** | Integration manager unit tests. |
| **test_algorithms.py** | Standalone algorithm tests (DTDA, IMRA, SHVA). |
| **test_trinity_integration.py** | Trinity Consortium integration tests. |

---

## 14. Grep-style reference (terms that appear in code)

- **Tax God** – app/main.py, config.py, ai_service.py, cost_governor.py, agent_gabriel.py, tax_writer.py, citation_engine.py, security.py, database.py, advanced_orchestrator.py, parallel_processor.py, audit.py, chat.py, documents.py, advanced.py, analytics.py, integrations.py; index.html, pantheon.js, olympus.css.
- **taxgod** – config.py (DB, S3), main.py (metrics), app.js (client id / api base).
- **Cost Governor / cost_governor** – cost_governor.py, config.py, main.py, ai_service.py, advanced_orchestrator.py, analytics.py, ops_tasks.py.
- **Agent Gabriel / agent_gabriel** – agent_gabriel.py, main.py, audit.py, tribunal.js.
- **copilot / co-pilot** – ai_service.py system prompt (“Tax God, an elite AI tax, legal, and financial advisory co-pilot”).
- **tax-god-agent** – no separate repo in this workspace; the **tax-god-copilot** folder is the single project containing both “Tax God” and “copilot” functionality.

---

**Summary:** Everything in this workspace is part of one **Tax God / tax copilot** system: backend (`app/`), specs (`specs/`), algorithms, swarm/Trinity-related code, and integrations. **Agent cost** is implemented in **Cost Governor** (`app/services/cost_governor.py`) and exposed via **analytics** endpoints; **tax assistant** behavior is in **AI orchestration** and **chat**; **Agent Gabriel** is the audit/review agent. There is no separate “tax-god-agent” repo here—only **tax-god-copilot** (this folder).
