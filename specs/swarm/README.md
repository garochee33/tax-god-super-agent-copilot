# Agent Swarm

Supervisor-orchestrated code assistant swarm with specialized agents and a critic gate.

## Architecture

You → SUPERVISOR
↓ (task graph)
[Repo Map + Constraints]
↓
FAN OUT (parallel)
ARCHITECT • IMPLEMENTER • DEBUGGER • TEST ENG • OPTIMIZER • SECURITY
↓
patches/PRs/worktrees + evidence (tests, benchmarks)
↓
REVIEWER / CRITIC GATE
↓
INTEGRATOR merges
↓
Final report

## Quick Start

```bash
cd /path/to/repo
agent-swarm init --repo /path/to/repo
agent-swarm run --repo /path/to/repo --goal "Fix bugs and improve quality"
```

## Config

Config is read from:
- Environment: `OPENAI_API_KEY`

## Local-only mode

External network calls are disabled by default. To enable them explicitly:

```bash
agent-swarm run --repo /path/to/repo --goal "..." --enable-network
```
- Optional config: `~/.config/agent_swarm/config.toml`

Example config:

```toml
[openai]
api_key = "..."
model = "gpt-5"

[swarm]
max_parallel = 4
allowlist = ["pytest", "ruff", "mypy", "rg", "git status", "git diff", "git log"]
```

## Safety

- Shell commands are strictly allowlisted.
- No destructive ops by default.
- File scope is restricted to repo root.
