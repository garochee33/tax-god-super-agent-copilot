# Tax God Quickstart

## Python version (important)

Use **Python 3.10, 3.11, 3.12, or 3.13**. **Python 3.14 is not supported** yet (pydantic-core and other deps rely on PyO3, which supports up to 3.13).

If your default `python3` is 3.14, create the venv with an older interpreter:

```bash
# macOS with Homebrew (install if needed: brew install python@3.12)
python3.12 -m venv .venv
# or
python3.13 -m venv .venv

source .venv/bin/activate
pip install -r requirements.txt
npm run start
```

Check version: `python --version` or `python3.12 --version`.

## 1. Configure Environment

```bash
cp .env.example .env
```

Set at least:
- `OPENAI_API_KEY` — required for Oracle chat when using GPT-4o / gpt-4o-mini (default)
- `ANTHROPIC_API_KEY` — required if using Claude models or escalation
- `SECRET_KEY`
- `INTEGRATION_ENCRYPTION_KEY` (recommended for production)

For QuickBooks (Hermes): `QUICKBOOKS_CLIENT_ID`, `QUICKBOOKS_CLIENT_SECRET`, `QUICKBOOKS_REDIRECT_URI`. Use Sandbox for testing; production keys for deploy. See `specs/BACKEND_INTEGRATIONS_AND_ALGORITHMS.md` for rate limits and endpoints.

## 2. Run Locally (no Docker)

**Option A – `tax-god` command (from anywhere):**

Add the project `bin` to your PATH, then run `tax-god`:

```bash
# One-time: add to ~/.zshrc (or ~/.bashrc)
export PATH="./bin:$PATH"

# Then from any directory:
tax-god           # uses port 8000
tax-god 8001      # if 8000 is in use
```

**Option B – manual:**

```bash
cd tax-god-super-agent-copilot
# Use Python 3.10–3.13 (see Python version section above)
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm run start
```

Or run uvicorn directly (reload only watches `app/` and `specs/`, not `.venv`):

```bash
uvicorn app.main:app --reload --reload-dir app --reload-dir specs --port 8000
```

**If you see "Address already in use" (port 8000):** free the port or use another:
```bash
lsof -ti:8000 | xargs kill    # free 8000
# or
tax-god 8001                  # run on 8001
```

Open:
- API docs: `http://localhost:8000/api/docs`
- Health: `http://localhost:8000/health/detailed`
- Metrics: `http://localhost:8000/metrics`

## 3. Run Full Stack (Docker Compose)

```bash
docker-compose up -d --build
```

**Note:** A `.dockerignore` is included so `venv/` and other heavy folders are not sent to the Docker daemon (avoids "Can't add file ... to tar" and speeds up build). If you see "Docker Compose requires buildx plugin", install [Docker Desktop](https://www.docker.com/products/docker-desktop) or the Docker Buildx plugin.

Open:
- API docs: `http://localhost:8000/api/docs`
- Readiness: `http://localhost:8000/readiness`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (`admin/admin`)
- Flower: `http://localhost:5555`

## 4. Verify Background Ops

Check Celery scheduler tasks are active:
- `refresh_integration_tokens` (15 min)
- `budget_guard_watchdog` (5 min)
- `regulatory_scan_heartbeat` (60 min)

Latest checkpoints are visible under `/health/detailed` -> `checks.ops_checkpoints`.

## 5. Run better (memory & ports)

- **Single dev server on fixed port:** `npm run dev:mac` → http://127.0.0.1:8000
- **Kill stray dev processes:** `npm run cleanup:ports:aggressive` or `./scripts/cleanup-dev-ports.sh`
- **If Cursor uses a lot of RAM:** see `docs/RUN_BETTER.md` and ensure `.cursorignore` exists, then restart Cursor.


## 6. Run Tests

```bash
source .venv/bin/activate
pytest tests/ -v              # full suite (46 tests)
pytest tests/ --cov=app       # with coverage
```

## 7. Verify GUI

After starting the server, open `http://localhost:8000` in a browser:
- Login with dev-token (auto-created admin in dev mode)
- Check all 7 pages: Oracle, Tribunal, Pantheon, Hermes, Scrolls, Archives, Agora (Clients)
- Agora should allow full client CRUD (create, edit, delete, search)
