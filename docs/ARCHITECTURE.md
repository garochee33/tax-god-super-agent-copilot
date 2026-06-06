# Tax God — System Architecture

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.11+) |
| Database | PostgreSQL (production) / SQLite (local dev) |
| Cache | Redis (session, rate limiting) |
| Auth | JWT (HS256, auto-generated secrets) |
| Frontend | Vanilla JS SPA, Jinja2 templates |
| Task Queue | Celery + Redis broker |
| Migrations | Alembic |
| AI | OpenAI / Anthropic (configurable) |
| Billing | Stripe (optional) |

## Auth Flow

1. **Registration** → User created with `viewer` role → 7-day free trial starts
2. **Login** → JWT issued (access token stored in localStorage)
3. **Role Check** → Middleware validates role (`admin`, `preparer`, `reviewer`, `client`)
4. **Subscription Gate** → Active subscription or trial required for protected endpoints
5. **Key Rotation** → Admin can rotate SECRET_KEY from settings UI (invalidates all sessions)

Roles hierarchy: `admin > preparer > reviewer > client`

## Agent System

| Agent | Role | Module |
|-------|------|--------|
| Gabriel | Primary orchestrator — routes queries to specialist agents | `app/services/agent_gabriel.py` |
| Oracle | Tax law research, IRC citation engine, multi-jurisdiction | `app/services/citation_engine.py` |
| Tribunal | Audit defense, compliance memos, penalty abatement | `app/services/tax_writer.py` |
| Pantheon | Financial planning, ROI estimation, projections | `app/services/roi_engine.py` |
| Hermes | Integration management, client communication | `app/services/integrations/` |
| Scrolls | Document generation, form filling, ingestion | `app/services/document_intelligence.py` |
| Agora | Client CRM, contact management | `app/api/v1/endpoints/` |

Orchestration: Gabriel receives all chat queries, classifies intent, delegates to the appropriate specialist, then synthesizes the response.

## Database Tables

| Table | Purpose |
|-------|---------|
| `users` | Accounts, hashed passwords, roles (admin/preparer/reviewer/client) |
| `subscriptions` | Tier, Stripe customer/subscription IDs, trial expiry |
| `clients` | CRM contacts (name, email, phone, company, tax_id, notes) |
| `invoices` | Billing records (client_id, amount, status, due_date) |
| `activity_logs` | All user/system actions with timestamps |
| `build_logs` | Agent coding contributions (SHA, message, author, files) |
| `knowledge_entries` | Persistent KB (documents, reports, notes, memories) |
| `settings_audit_log` | Every .env key change with before/after hashes |
| `expenses` | Categorized expenses with receipt tracking |
| `accounts` | Chart of accounts (assets, liabilities, equity, revenue) |
| `projects` | Client project tracking with budgets |
| `transactions` | Financial transactions (debit/credit) |
| `vendors` | Vendor/supplier records |
| `time_entries` | Billable time tracking per project |
| `notes` | Internal notes (linked to clients/projects) |
| `spreadsheets` | Stored spreadsheet data |
| `user_settings` | Per-user preferences |
| `integrations` | OAuth tokens and integration configs |
| `businesses` | Multi-business support |

## API Structure

```
/api/v1/
├── /auth          — Register, login, token refresh, profile
├── /billing       — Subscription status, Stripe checkout, webhook
├── /chat          — Agent conversations (Gabriel orchestrator)
├── /audit         — Audit defense memos, compliance checks
├── /documents     — Document upload, ingestion, generation
├── /analytics     — Dashboard KPIs, reports, trends
├── /integrations  — OAuth connect/disconnect, sync status
├── /advanced      — Multi-agent orchestration, scenario analysis
├── /settings      — App config (admin), key rotation, audit log
├── /logs          — Activity logs, build logs viewer
├── /dev           — Health, hooks, consensus, locks, integrity, deploy gate
├── /clients       — CRM CRUD, search, export
```

## Dev Tracking System

| Feature | Endpoint | Purpose |
|---------|----------|---------|
| Health Check | `GET /dev/health` | System status + dependency check |
| Pre-commit Hook | `POST /dev/hooks/pre-commit` | Format validation + secret scan |
| Post-commit Hook | `POST /dev/hooks/post-commit` | Log commit to build_logs |
| Consensus | `POST /dev/consensus/propose` | Propose high-risk changes |
| File Locks | `POST /dev/locks/acquire` | Prevent multi-agent collisions |
| Integrity | `GET /dev/integrity/verify` | SHA256 snapshot comparison |
| Deploy Gate | `GET /dev/deploy/gate` | Tests + lint + integrity + clean tree |
| Agent Registry | `GET/POST /dev/agents` | Register and list active agents |

## Frontend

- **Type:** Single-page application (SPA) with vanilla JS
- **Theme:** Olympus (dark/gold aesthetic)
- **Template:** `app/templates/index.html` (Jinja2 shell)
- **Modules:** `app/static/js/` (page-specific modules loaded dynamically)
- **Styling:** `app/static/css/` (custom Olympus theme)

Page modules:
- Dashboard (KPIs, recent activity, quick actions)
- Chat (agent conversations)
- Clients (CRM)
- Documents (upload/generate)
- Analytics (charts, reports)
- Settings (admin config)
- Profile (user preferences)
- Onboarding (first-run wizard)

## Testing & Quality

| Metric | Value |
|--------|-------|
| Total tests | 246 |
| Test files | 30 |
| Endpoint groups covered | 28/28 |
| Lint errors | 0 (ruff E,F,W) |
| Pre-deploy gate | GO 4/4 (lint, pytest, git clean, integrity) |

### Test Categories

- **Auth & Security**: 29 tests (JWT, RBAC, rate limiting, headers, injection)
- **CRUD Endpoints**: 72 tests (clients, businesses, expenses, invoices, vendors, accounts, transactions, time, notes, projects, spreadsheets)
- **AI & Agents**: 15 tests (chat, advanced orchestration, subscription gating)
- **Finance**: 19 tests (payments, receipts, audit, billing)
- **Infrastructure**: 28 tests (settings, dev tracking, logs, integrity)
- **Feature Tiers**: 40 tests (tier 1 + tier 2 feature packs)
- **E2E**: 2 tests (full pipeline, workflow)

### Pre-Deploy Gate

```bash
bash scripts/run-all-checks.sh
# [ruff lint]    ✅ PASS
# [pytest]       ✅ PASS (246 tests)
# [git clean]    ✅ PASS
# [integrity]    ✅ PASS (76 files hashed)
# Result: ✅ GO (4/4)
```

## Security Middleware Stack

| Layer | File | Purpose |
|-------|------|---------|
| Rate Limiter | `security.py` | Per-IP + per-user request throttling |
| Security Headers | `security_headers.py` | CSP, X-Frame-Options, HSTS, XSS protection |
| Audit Logger | `audit_middleware.py` | Request/response audit trail |
| Request ID | `request_id.py` | Correlation ID for distributed tracing |
| Error Handler | `error_handler.py` | Safe error responses (no stack traces) |
| Timeout | `timeout.py` | Request timeout enforcement |
