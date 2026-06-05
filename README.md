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
├── api/v1/endpoints/   # REST endpoints (chat, documents, audit, analytics, auth)
├── core/               # Config, database, security, crypto
├── middleware/          # Security middleware
├── models/             # SQLAlchemy models
├── services/           # Agent services, integrations, engines
├── static/             # Frontend (CSS, JS)
└── templates/          # Jinja2 templates
alembic/                # Database migrations
tests/                  # Test suite
specs/                  # Implementation specs & swarm runner
docs/                   # Documentation
```

## License

Private — Trinity Consortium / Enzo Garoche (EGD33)
