# Tax God — Hooks & Protocols

## Git Hooks

### Pre-Commit (`.githooks/pre-commit`)
Validates code before commit is accepted:
1. **Format check** — Sends diff to `/dev/hooks/pre-commit` for lint validation
2. **Secret scan** — Scans staged files for API keys, tokens, passwords
3. **Exit code** — Non-zero blocks the commit with error details

### Post-Commit (`.githooks/post-commit`)
Logs commit to the dev tracking system:
1. Extracts SHA, message, author, changed files
2. POSTs to `/dev/hooks/post-commit`
3. Stored in `build_logs` table for audit trail

### Installation
```bash
./scripts/install-hooks.sh
# Sets core.hooksPath to .githooks/
```

## Consensus Protocol

For high-risk changes (schema migrations, auth modifications, breaking API changes):

```
PROPOSE → APPROVE → EXECUTE
```

1. **Propose** — Agent submits change proposal to `POST /dev/consensus/propose`
   - Includes: description, files affected, risk level, rollback plan
   - Stored in `.dev/proposals.json`
2. **Approve** — Another agent or admin reviews and approves
   - Requires majority if multiple agents active
3. **Execute** — Change is applied only after approval
   - Logged with full audit trail

## File Locking

Prevents multi-agent edit collisions:

- **Acquire** — `POST /dev/locks/acquire` with file path and agent ID
- **Release** — `POST /dev/locks/release` with file path
- **Check** — `GET /dev/locks/status` shows all active locks
- **Timeout** — Locks auto-expire after 10 minutes
- **State** — Stored in `.dev/locks.json`

Rules:
- Lock before modifying shared files
- One lock per file at a time
- Stale locks are auto-cleaned on health check

## Integrity Verification

SHA256 snapshot system for detecting unauthorized changes:

- **Snapshot** — `POST /dev/integrity/snapshot` computes hashes for all tracked files
- **Verify** — `GET /dev/integrity/verify` compares current state to last snapshot
- **State** — Stored in `.dev/integrity.json`
- **Scope** — Covers: `app/`, `alembic/`, `scripts/`, `tests/`, config files

Triggered automatically by deploy gate and available on-demand.

## Deployment Gate

All checks must pass before code ships:

```bash
# Runs via: GET /dev/deploy/gate
1. ✅ ruff check (lint clean)
2. ✅ pytest (all tests pass)
3. ✅ integrity verify (no unexpected changes)
4. ✅ git status clean (no uncommitted files)
5. ✅ no active file locks
```

Returns `GO` or `NO-GO` with detailed failure reasons.

## Cross-Repo Sync Protocol

Coordinates state across Trinity Consortium repositories:

```bash
./scripts/cross-repo-sync.sh
```

- Fetches all configured repos
- Reports branch, ahead/behind, uncommitted status
- Generates `BUILD_STATUS.md` report
- Configured repos: tax-god-copilot, DSH, DOME-HUB, trinity-unified-ai, dome-brain, dome-console

## Agent Registry

Active agents register themselves at startup:

- **Register** — `POST /dev/agents` with agent name, capabilities, session ID
- **List** — `GET /dev/agents` shows all active agents
- **State** — `.dev/agents.json`
- **Purpose** — Coordination, lock ownership, consensus voting
