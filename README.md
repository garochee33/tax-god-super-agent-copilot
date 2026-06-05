# Tax God Super Agent Co-Pilot

AI-powered local GUI app & multi-agent system for **law, taxes, finance, and accounting**.

## Overview

Tax God is a multi-agent AI co-pilot that combines domain expertise across tax law, financial planning, accounting standards, and legal compliance into a single sovereign application.

## Architecture

- **Backend:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL + Alembic migrations
- **Auth:** JWT-based authentication
- **AI Agents:** Multi-agent orchestration (Gabriel, Oracle, Tribunal, Pantheon)
- **Integrations:** QuickBooks, Google Services
- **Deployment:** Railway, Docker, CI/CD (GitHub Actions)

## Agents

| Agent | Domain |
|-------|--------|
| Gabriel | Primary orchestrator — routes to specialists |
| Oracle | Tax law research & citation engine |
| Tribunal | Audit defense & compliance |
| Pantheon | Financial planning & estimation |
| Hermes | Client communication |
| Scrolls | Document generation & forms |
| Agora | Client management (CRUD, search, status tracking) |

## Quick Start

```bash
# Clone
git clone https://github.com/garochee33/tax-god-super-agent-copilot.git
cd tax-god-super-agent-copilot

# One-command setup (installs deps, creates DB, runs migrations)
./setup.sh

# Run
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000, register an account, and you're in with a **7-day free trial**.

## Subscription & Access

| Tier | Access | Price |
|------|--------|-------|
| Free Trial | All features for 7 days | $0 |
| Pro | Unlimited access | $29/month |

After trial expires, subscribe via the in-app billing page (Stripe). Admins can manage users directly in the database.

### Stripe Setup (for operators)

To enable payments, add to `.env`:
```
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_MONTHLY=price_...  # Create a $29/month recurring price in Stripe Dashboard
```

## Structure

```
app/
├── api/v1/endpoints/   # REST endpoints (auth, chat, audit, documents, analytics, integrations, advanced, clients)
├── core/               # Config, database, security, crypto
├── middleware/          # Rate limiting, security headers, request ID
├── models/             # SQLAlchemy models (User, Integration, Client)
├── services/           # Agent services, AI orchestration, integrations, engines
├── static/             # Frontend (CSS, JS pages: oracle, tribunal, pantheon, hermes, scrolls, archives, agora)
└── templates/          # Jinja2 templates (Olympus Dashboard)
alembic/                # Database migrations
tests/                  # Comprehensive test suite (46 tests)
specs/                  # Implementation specs & swarm runner
docs/                   # Documentation
```

## Testing

```bash
# Run full test suite
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=term-missing

# Individual modules
pytest tests/test_auth.py -v
pytest tests/test_chat.py -v
pytest tests/test_documents.py -v
pytest tests/test_analytics.py -v
pytest tests/test_e2e_pipeline.py -v
```

## License

Private — Trinity Consortium / Enzo Garoche (EGD33)
