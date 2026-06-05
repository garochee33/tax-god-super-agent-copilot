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

# Setup
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Database
alembic upgrade head

# Run
uvicorn app.main:app --reload --port 8000
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
