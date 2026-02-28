from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

from swarm.agents.base import AgentContext
from swarm.agents.bugfix import BugfixAgent
from swarm.agents.docs import DocsAgent
from swarm.agents.feature import FeatureAgent
from swarm.agents.refactor import RefactorAgent
from swarm.agents.review import ReviewAgent
from swarm.agents.tests import TestsAgent
from swarm.state import SwarmState
from swarm.config import AppConfig
from swarm.tools.repo_map import build_repo_map


FANOUT = [
    FeatureAgent(),
    RefactorAgent(),
    BugfixAgent(),
    TestsAgent(),
    DocsAgent(),
]


@dataclass
class Orchestrator:
    repo_root: Path

    def run(self, goal: str, config: AppConfig) -> SwarmState:
        state = SwarmState(repo_root=self.repo_root, goal=goal)
        repo_map = build_repo_map(self.repo_root)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        workspace = (config.swarm.repo_root / config.swarm.workspace_dir / timestamp).resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        state.workspace = workspace
        ctx = AgentContext(
            repo_root=self.repo_root,
            goal=goal,
            repo_map=repo_map,
            constraints={
                "file_scope": "repo_root_only",
                "no_destructive_ops": "true",
            },
            allowlist=config.swarm.allowlist,
            workspace=workspace,
            openai_api_key=config.openai.api_key,
            openai_model=config.openai.model,
            openai_base_url=config.openai.base_url,
            openai_enable_network=config.openai.enable_network,
        )

        for agent in FANOUT:
            try:
                result = agent.run(ctx)
                state.results[agent.name] = result
            except Exception as exc:
                state.errors.append(f"{agent.name}: {exc}")

        reviewer = ReviewAgent()
        review = reviewer.run(ctx)
        state.results[reviewer.name] = review
        state.reviewer_notes = review.summary

        state.final_report = self._compile_report(state)
        self._write_artifacts(state)
        return state

    def _compile_report(self, state: SwarmState) -> str:
        lines: List[str] = []
        lines.append(f"Goal: {state.goal}")
        if state.errors:
            lines.append("Errors:")
            lines.extend([f"- {e}" for e in state.errors])
        lines.append("Results:")
        for name, result in state.results.items():
            lines.append(f"- {name}: {result.summary}")
        if state.reviewer_notes:
            lines.append(f"Reviewer: {state.reviewer_notes}")
        return "\n".join(lines)

    def _write_artifacts(self, state: SwarmState) -> None:
        if not state.workspace:
            return
        report_path = state.workspace / "report.txt"
        report_path.write_text(state.final_report or "", encoding="utf-8")
        for name, result in state.results.items():
            evidence_path = state.workspace / f"{name}.txt"
            content = result.summary + "\n\n"
            for key, value in result.evidence.items():
                content += f"[{key}]\n{value}\n\n"
            if result.openai_headers_path and result.openai_headers_path.exists():
                try:
                    header_text = result.openai_headers_path.read_text(encoding="utf-8")
                    content += "[openai_headers]\n" + header_text.strip() + "\n\n"
                except Exception:
                    pass
            evidence_path.write_text(content.strip() + "\n", encoding="utf-8")
