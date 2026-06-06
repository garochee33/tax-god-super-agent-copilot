# Memory & Port Audit

What uses memory and ports in this repo, and how to clean up.

## What uses memory

| Source | What it is | What to do |
|--------|------------|------------|
| **uvicorn** | Tax God FastAPI server (Python) | One process is enough. Use `npm run dev:mac` on 8000 to avoid port fights. |
| **Cursor** | IDE indexing (can use a lot of RAM on big trees) | Add `.cursorignore` so Cursor skips `node_modules`, `dist`, `archive`, etc. Restart Cursor after adding. Close other project windows when you only need this repo. |
| **node_modules** | If present (e.g. from a frontend or tooling) | Ignored by .cursorignore. Run `npm run cleanup:ports:aggressive` to kill any Node/Vite dev servers. |
| **Python venv** | Virtual env for dependencies | In .cursorignore. Don’t index it. |
| **Docker/Colima** | Containers and images | Stop when not needed: `docker-compose down` or `colima stop`. |

## What uses ports

Common dev ports this repo uses or frees:

- **8000** — Recommended for Tax God: `npm run dev:mac` (single server, 127.0.0.1:8000)
- **8000** — Default uvicorn: `npm run start`
- **5000, 5001, 3000, 8080, 5173** — Often used by other tools (Vite, Node, etc.). The cleanup script kills processes on these so they don’t stick around.

## Cleanup workflow

1. **Free ports and kill stray dev processes**
   - `npm run cleanup:ports:aggressive`
   - Or: `./scripts/cleanup-dev-ports.sh`

2. **Run one server on a fixed port**
   - `npm run dev:mac` → Tax God on http://127.0.0.1:8000

3. **If Cursor is using a lot of RAM**
   - Ensure `.cursorignore` exists and includes `node_modules/`, `dist/`, `archive/`, `*.log`, etc.
   - Restart Cursor so it reindexes without those paths.
   - Close other Cursor windows/projects.

See **docs/RUN_BETTER.md** for the full “run better” guide.
