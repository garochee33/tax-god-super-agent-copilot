from __future__ import annotations

from swarm.agents.base import BaseAgent, AgentContext
from swarm.state import AgentResult
from swarm.tools.llm import run_agent_llm
from swarm.tools.offline import run_offline_checks


class ReviewAgent(BaseAgent):
    name = "review"

    def run(self, ctx: AgentContext) -> AgentResult:
        constraints = "Critic gate: return PASS or FAIL in SUMMARY."
        if not ctx.openai_api_key:
            summary = "SUMMARY: PASS (offline mode)."
            evidence = run_offline_checks(
                ctx.repo_root,
                ctx.allowlist,
                [
                    "git status",
                ],
            )
            result = AgentResult(name=self.name, summary=summary)
            result.evidence["offline"] = evidence
            return result

        text = run_agent_llm(
            "REVIEWER",
            ctx.goal,
            ctx.repo_map,
            constraints,
            ctx.openai_api_key,
            ctx.openai_model,
            ctx.openai_base_url,
            enable_network=ctx.openai_enable_network,
            headers_path=str(ctx.workspace / f"{self.name}_openai_headers.json"),
        )
        result = AgentResult(name=self.name, summary=text.splitlines()[0] if text else "")
        result.openai_headers_path = ctx.workspace / f"{self.name}_openai_headers.json"
        result.evidence["llm_output"] = text
        return result
