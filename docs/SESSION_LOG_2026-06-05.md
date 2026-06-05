# Tax God Session Memory — 2026-06-05

## Summary
Full platform build session. Tax God Super Agent Co-Pilot v3.1.0 completed.
Local-first sovereign tax/financial management app with AI advisory.

## Key Facts
- Repo: github.com/garochee33/tax-god-super-agent-copilot
- Path: ~/DSH/projects/tax-god-super-agent-copilot
- Server: http://127.0.0.1:8000
- Admin: enzo@trinity-consortium.com / TaxGod-Tmp-8x7K!
- DB: SQLite at db/taxgod.db (19 tables)
- Launch: /Applications/Tax God.app or bin/tax-god

## Architecture
- FastAPI + SQLAlchemy async + SQLite
- Vanilla JS SPA (dynamic imports, no framework)
- JWT auth (key: taxgod_access_token in localStorage)
- 22 API routers, 18 pages, 17 models
- AI: OpenAI + Anthropic with auto-fallback, 6 specialist agents

## Brand
- Olympian theme: Navy, Gold, Marble, Parchment
- Fonts: Cinzel + Inter
- App name: Tax God Super Agent Co-Pilot

## Dev Coordination
- Agent ID: kiro-cli-01
- Dev API: /api/v1/dev/ (agents, consensus, locks, integrity)
- Integrity: 76 files snapshotted
- Cross-repo sync: scripts/cross-repo-sync.sh

## What Works
- All financial CRUD (accounts, invoices, expenses, projects, notes, spreadsheets)
- Multi-business sandbox
- Time tracking, vendors (1099), transactions (CSV import)
- Tax God AI agent with 6 specialists
- Reports (P&L, expenses, deductions)
- User tiers (admin/pro/trial/expired) all tested
