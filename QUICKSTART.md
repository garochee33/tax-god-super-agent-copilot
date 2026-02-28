# Tax God Quickstart

## 1. Configure Environment

```bash
cd /Users/enzogaroche/tax-god-copilot
cp .env.example .env
```

Set at least:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `SECRET_KEY`
- `INTEGRATION_ENCRYPTION_KEY` (recommended for production)

## 2. Run Locally (no Docker)

**Option A – `tax-god` command (from anywhere):**

Add the project `bin` to your PATH, then run `tax-god`:

```bash
# One-time: add to ~/.zshrc (or ~/.bashrc)
export PATH="/Users/enzogaroche/Desktop/AI_AGENTS/tax-god-copilot/bin:$PATH"

# Then from any directory:
tax-god           # uses port 8000
tax-god 8001      # if 8000 is in use
```

**Option B – manual:**

```bash
cd /Users/enzogaroche/Desktop/AI_AGENTS/tax-god-copilot
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
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

