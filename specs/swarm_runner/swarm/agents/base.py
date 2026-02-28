from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from swarm.state import AgentResult


@dataclass
class LLMRuntime:
    provider: str = "openai"
    model: str = ""
    base_url: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    fallback_models: List[str] = field(default_factory=list)
    # Resolved fallback runtimes (provider+model per fallback); used for cross-provider AUTO fallback
    fallback_runtimes: List["LLMRuntime"] = field(default_factory=list)


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
    # Inter-agent: prior agents' summaries (formatted string)
    prior_agent_summaries: str = ""
    # Per-agent model override (resolved model name string)
    model_key: str | None = None
    # Fractal memory: retrieved context to inject into prompt
    fractal_memory_context: str = ""
    # Planner: when fractal_planner=True, this agent's subtask goal (else same as goal)
    subtask_goal: str | None = None
    # Oracle: optional web search results for this run
    oracle_results: str = ""
    # Provider routing (new, optional)
    llm_runtime: Optional[LLMRuntime] = None


class BaseAgent:
    name: str = "base"

    def run(self, ctx: AgentContext) -> AgentResult:
        return AgentResult(name=self.name, summary="No-op")

    def _extract_patch(self, text: str) -> str:
        match = re.search(r"```diff\s*(.*?)\s*```", text, re.DOTALL)
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
