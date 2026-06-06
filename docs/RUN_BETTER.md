# Run Better — Less memory, no port fights

Quick reference so one dev server runs on a fixed port and cleanup is easy.

## Commands

| What | Command | How it helps |
|------|---------|--------------|
| **Kill heavy dev processes** | `npm run cleanup:ports:aggressive` | Frees memory from Node/Vite/uvicorn on ports 5000, 5050, 8000, etc. |
| **Single dev server, fixed port** | `npm run dev:mac` | One process on 127.0.0.1:8000, avoids port fights and extra servers. |
| **Single worker (lighter)** | `npm run dev:safe` | Same as dev:mac with one uvicorn worker. |
| **Cleanup script (same as npm)** | `./scripts/cleanup-dev-ports.sh` | Same as the npm script; frees ports and kills dev processes. |

## Cursor using a lot of RAM (e.g. tens of GB)

Cursor indexes the whole project. If the repo is big (e.g. node_modules, dist, archives), indexing can use a lot of memory.

1. **Add a `.cursorignore`** in the repo root (create it if it doesn’t exist) with at least:
   ```
   node_modules/
   dist/
   archive/
   attached_assets/
   *.log
   package-lock.json
   __pycache__/
   .venv/
   venv/
   ```
2. **Restart Cursor** so it reindexes without those paths. This often drops RAM use a lot.
3. **Close other Cursor windows/projects** when you only need this repo.

## Memory and port audit

See **docs/MEMORY_AUDIT.md** for what uses memory and ports and the full cleanup workflow.
