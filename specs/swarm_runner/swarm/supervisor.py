from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from swarm.config import AppConfig, apply_swarm_overrides
from swarm.orchestrator import Orchestrator
from swarm.state import SwarmState, generate_correlation_id


@dataclass(frozen=True)
class SubSwarmRun:
    """One layer/run of the swarm (typically one cluster)."""

    cluster: Optional[str]
    state: SwarmState


@dataclass
class SupervisorState:
    """Aggregated state across multiple sub-swarm layers."""

    repo_root: Path
    goal: str
    correlation_id: str = field(default_factory=generate_correlation_id)
    runs: List[SubSwarmRun] = field(default_factory=list)
    final_report: str = ""


def _format_state_as_prior_context(state: SwarmState, cluster: Optional[str]) -> str:
    """Compact context passed from one sub-swarm to the next."""
    lines: List[str] = []
    lines.append("[Prior sub-swarm summary]")
    lines.append(f"- cluster: {cluster or '(default)'}")
    if state.workspace:
        lines.append(f"- artifacts: {state.workspace}")
    if state.reviewer_notes:
        lines.append(f"- reviewer: {state.reviewer_notes[:400]}")
    if state.errors:
        lines.append(f"- errors: {len(state.errors)}")
        for err in state.errors[:3]:
            lines.append(f"  - {str(err)[:200]}")
    lines.append("")
    for name, result in state.results.items():
        # Keep it short; this is prompt context.
        summary = (result.summary or "").strip().replace("\n", " ")
        if not summary:
            continue
        lines.append(f"- {name}: {summary[:400]}")
    return "\n".join(lines).strip()


class Supervisor:
    """
    Local-first supervisor that runs multiple swarms (clusters) in sequence.

    This is the bridge between:
    - Option A: single process (today)
    - Option B: multi-process workers (future; swap execution backend)
    - Option C: distributed nodes (future; queue + leases)
    """

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def run(self, goal: str, config: AppConfig, clusters: List[str]) -> SupervisorState:
        # Normalize cluster list (strip blanks, preserve order)
        cluster_order = [c.strip() for c in clusters if c and c.strip()]
        if not cluster_order:
            cluster_order = [""]

        cluster_names = {c.name for c in config.swarm.clusters} if config.swarm.clusters else set()
        unknown = [c for c in cluster_order if c and c not in cluster_names]
        if unknown:
            raise ValueError(f"Unknown clusters: {', '.join(unknown)}")

        sup = SupervisorState(repo_root=self.repo_root, goal=goal)
        prior_context = ""

        for cluster in cluster_order:
            cfg = copy.deepcopy(config)
            if cluster:
                apply_swarm_overrides(cfg, {"active_cluster": cluster})
            o = Orchestrator(repo_root=self.repo_root)
            state = o.run(goal, cfg, seed_prior_agent_summaries=prior_context)
            sup.runs.append(SubSwarmRun(cluster=cluster or None, state=state))
            prior_context = _format_state_as_prior_context(state, cluster or None)

        sup.final_report = self._compile_report(sup)
        return sup

    def _compile_report(self, sup: SupervisorState) -> str:
        lines: List[str] = []
        lines.append(f"Goal: {sup.goal}")
        lines.append(f"Supervisor correlation_id: {sup.correlation_id}")
        lines.append("")
        lines.append("Layers:")
        for i, run in enumerate(sup.runs, 1):
            state = run.state
            lines.append(f"- {i}. cluster={run.cluster or '(default)'}")
            if state.workspace:
                lines.append(f"  artifacts: {state.workspace}")
            if state.errors:
                lines.append(f"  errors: {len(state.errors)}")
            if state.reviewer_notes:
                lines.append(f"  reviewer: {state.reviewer_notes}")
        return "\n".join(lines).strip() + "\n"

