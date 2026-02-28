from __future__ import annotations

import argparse
from pathlib import Path

from swarm.config import load_config
from swarm.orchestrator import Orchestrator


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Agent Swarm CLI")
    p.add_argument("command", choices=["init", "run"], help="Command")
    p.add_argument("--repo", required=True, help="Repo root")
    p.add_argument("--goal", required=False, default="", help="Goal")
    p.add_argument(
        "--enable-network",
        action="store_true",
        help="Allow external network calls (disabled by default)",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    repo_root = Path(args.repo).resolve()
    cfg = load_config()
    if args.enable_network:
        cfg.openai.enable_network = True

    if args.command == "init":
        print(f"Initialized swarm for repo: {repo_root}")
        return

    if not args.goal:
        raise SystemExit("--goal is required for run")

    cfg.swarm.repo_root = repo_root
    orchestrator = Orchestrator(repo_root=repo_root)
    state = orchestrator.run(args.goal, cfg)
    print(state.final_report or "No report")
    if state.workspace:
        print(f"Artifacts: {state.workspace}")


if __name__ == "__main__":
    main()
