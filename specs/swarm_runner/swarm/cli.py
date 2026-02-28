from __future__ import annotations

import argparse
from pathlib import Path

from swarm.config import apply_preset, apply_swarm_overrides, load_config
from swarm.orchestrator import Orchestrator


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Agent Swarm CLI")
    p.add_argument("command", choices=["init", "run"], help="Command")
    p.add_argument("--repo", required=True, help="Repo root")
    p.add_argument("--goal", required=False, default="", help="Goal")
    p.add_argument("--config", required=False, default=None, help="Path to config.toml (optional)")
    p.add_argument("--preset", required=False, default=None, help="Preset name from config")
    p.add_argument("--cluster", required=False, default=None, help="Cluster name from config")
    p.add_argument(
        "--clusters",
        required=False,
        default="",
        help="Comma-separated cluster plan to run sequentially (e.g. focus,speed).",
    )
    p.add_argument("--enable-bot", action="append", default=[], help="Enable bot (repeatable)")
    p.add_argument("--disable-bot", action="append", default=[], help="Disable bot (repeatable)")
    p.add_argument(
        "--set-model",
        action="append",
        default=[],
        help="Override model for bot: <bot>=<model_key_or_id>",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    repo_root = Path(args.repo).resolve()
    if not repo_root.exists():
        raise SystemExit(f"Repo path does not exist: {repo_root}")
    if args.command == "run" and not repo_root.is_dir():
        raise SystemExit(f"Repo path is not a directory: {repo_root}")

    cfg = load_config(path=args.config)
    if cfg.swarm.active_preset:
        apply_preset(cfg, cfg.swarm.active_preset)
    if args.preset:
        apply_preset(cfg, args.preset)
    if args.cluster:
        apply_swarm_overrides(cfg, {"active_cluster": args.cluster})
    if args.enable_bot:
        apply_swarm_overrides(cfg, {"enabled_bots": args.enable_bot})
    if args.disable_bot:
        apply_swarm_overrides(cfg, {"disabled_bots": args.disable_bot})
    if args.set_model:
        overrides: dict[str, dict[str, str]] = {}
        for item in args.set_model:
            if "=" not in item:
                raise SystemExit("--set-model must be <bot>=<model_key_or_id>")
            bot, model = item.split("=", 1)
            overrides.setdefault("model_by_role", {})[bot] = model
        apply_swarm_overrides(cfg, overrides)

    if args.command == "init":
        print(f"Initialized swarm for repo: {repo_root}")
        return

    if not args.goal:
        raise SystemExit("--goal is required for run")

    cfg.swarm.repo_root = repo_root

    clusters = [c.strip() for c in str(args.clusters or "").split(",") if c.strip()]
    if clusters:
        from swarm.supervisor import Supervisor

        supervisor = Supervisor(repo_root=repo_root)
        sup_state = supervisor.run(args.goal, cfg, clusters=clusters)
        print(sup_state.final_report or "No report")
        if sup_state.runs and sup_state.runs[-1].state.workspace:
            print(f"Artifacts: {sup_state.runs[-1].state.workspace}")
        return

    orchestrator = Orchestrator(repo_root=repo_root)
    state = orchestrator.run(args.goal, cfg)
    print(state.final_report or "No report")
    if state.workspace:
        print(f"Artifacts: {state.workspace}")


if __name__ == "__main__":
    main()
