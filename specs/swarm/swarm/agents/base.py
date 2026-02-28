from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from typing import Dict, List

from swarm.state import AgentResult


@dataclass
class AgentContext:
    repo_root: Path
    goal: str
    repo_map: List[str]
    constraints: Dict[str, str]
    allowlist: List[str]
    workspace: Path
    openai_api_key: str | None
    openai_model: str
    openai_base_url: str
    openai_enable_network: bool


class BaseAgent:
    name: str = "base"

    def run(self, ctx: AgentContext) -> AgentResult:
        return AgentResult(name=self.name, summary="No-op")

    def _extract_patch(self, text: str) -> str:
        match = re.search(r"```diff\\n(.*?)\\n```", text, re.DOTALL)
        if not match:
            return ""
        return match.group(1).strip()

    def _write_patch(self, ctx: AgentContext, patch: str) -> Path | None:
        if not patch:
            return None
        patches_dir = ctx.workspace / "patches"
        patches_dir.mkdir(parents=True, exist_ok=True)
        path = patches_dir / f"{self.name}.patch"
        path.write_text(patch + "\n", encoding="utf-8")
        return path
