# Agent Instructions — Tax God Repo

## Rules for All Agents

### 1. Always Rebase Before Push
```bash
git pull origin main --rebase
git push origin main
```
Never force-push. If rebase conflicts, resolve manually and verify tests pass.

### 2. Use Consensus Protocol for High-Risk Changes
High-risk = schema migrations, auth changes, breaking API changes, config rewrites.
```
POST /dev/consensus/propose
# Wait for approval before executing
```

### 3. Lock Files You're Modifying
```
POST /dev/locks/acquire  {"file": "app/main.py", "agent": "your-id"}
# ... make changes ...
POST /dev/locks/release  {"file": "app/main.py"}
```

### 4. Run Health Check Before Committing
```bash
curl http://localhost:8000/api/v1/dev/health
# Or run the full check script:
./scripts/run-all-checks.sh
```

### 5. Register Yourself
```
POST /dev/agents {"name": "your-agent-name", "session": "unique-id"}
```
Check `.dev/agents.json` for currently active agents.

### 6. Log Major Work
All significant features, fixes, and refactors should be logged:
- Commits are auto-logged via post-commit hook
- Update `docs/BUILD_LOG.md` for session summaries
- Major decisions go in `docs/DEV_LOG.md`

## Conventions

- **Commit messages:** `type: description` (feat, fix, refactor, docs, test, chore)
- **Branch:** Work on `main` (single-branch workflow for now)
- **Tests:** Add tests for new endpoints. Run `pytest tests/ -v` before commit.
- **Lint:** `ruff check app/ tests/` must pass clean.
- **Secrets:** Never commit real keys. Use `.env` (gitignored) or env vars.

## Quick Reference

| Action | Command/Endpoint |
|--------|-----------------|
| Health | `GET /dev/health` |
| Lock file | `POST /dev/locks/acquire` |
| Propose change | `POST /dev/consensus/propose` |
| Verify integrity | `GET /dev/integrity/verify` |
| Deploy gate | `GET /dev/deploy/gate` |
| Run checks | `./scripts/run-all-checks.sh` |
