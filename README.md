# Tax God Super Agent Co-Pilot

AI-powered **local** GUI app & multi-agent system for **law, taxes, finance, and accounting**.

100% sovereign — runs entirely on your machine. Your data never leaves your computer.

## Quick Start

```bash
git clone https://github.com/garochee33/tax-god-super-agent-copilot.git
cd tax-god-super-agent-copilot
./setup.sh
```

That's it. Setup auto-installs dependencies, generates secrets, creates the database, and runs migrations.

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000** → Register → 7-day free trial starts immediately.

## Desktop App

Double-click **Tax God.app** in Applications (or create it):

```bash
# Creates /Applications/Tax God.app
./bin/tax-god install
```

## Architecture

- **Backend:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL (local) + Redis (local)
- **Auth:** JWT with auto-generated secrets
- **AI Agents:** Multi-agent orchestration
- **Frontend:** Single-page Olympus Dashboard
- **Billing:** Optional Stripe integration

## Agents

| Agent | Domain |
|-------|--------|
| Gabriel | Primary orchestrator — routes to specialists |
| Oracle | Tax law research & citation engine |
| Tribunal | Audit defense & compliance |
| Pantheon | Financial planning & estimation |
| Hermes | Integrations & client communication |
| Scrolls | Document generation & forms |
| Agora | Client management |

## Configuration

All settings are manageable from the **⚙️ Settings** page in the app (admin only):

- AI API Keys (OpenAI, Anthropic)
- Stripe billing keys
- OAuth integrations (Google, QuickBooks)
- Database connections
- Key rotation, connection testing, audit logs

Or edit `.env` directly.

## Subscription (Optional)

| Tier | Access | Price |
|------|--------|-------|
| Free Trial | All features for 7 days | $0 |
| Pro | Unlimited | $29/month |

To enable Stripe payments, add keys in Settings. Without Stripe configured, the app runs in unlimited local mode.

## Structure

```
app/
├── api/v1/endpoints/   # REST endpoints
├── core/               # Config, database, security
├── middleware/          # Security middleware
├── models/             # SQLAlchemy models
├── services/           # Agent services, AI, integrations
├── static/             # Frontend (CSS, JS)
└── templates/          # Jinja2 templates
alembic/                # Database migrations
tests/                  # Test suite
```

## Testing

```bash
pytest tests/ -v
```

246 tests covering all 28 endpoint groups. Pre-deploy gate: `bash scripts/run-all-checks.sh`

## License

Private — Trinity Consortium / Enzo Garoche (EGD33)
