from __future__ import annotations

from swarm.agents.base import AgentContext, BaseAgent
from swarm.state import AgentResult
from swarm.tools.llm import run_critic_llm
from swarm.tools.offline import run_offline_checks


class ReviewAgent(BaseAgent):
    name = "review"

    def run(self, ctx: AgentContext) -> AgentResult:
        constraints = "Critic gate: return PASS or FAIL in SUMMARY."
        provider_name = ctx.llm_runtime.provider if ctx.llm_runtime else "openai"
        if provider_name in {"openai", "openai_compatible"} and not ctx.openai_api_key:
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

        goal = getattr(ctx, "subtask_goal", None) or ctx.goal
        prior = getattr(ctx, "prior_agent_summaries", "") or ""
        fractal_ctx = getattr(ctx, "fractal_memory_context", "") or ""
        oracle = getattr(ctx, "oracle_results", "") or ""
        text = run_critic_llm(
            goal,
            ctx.repo_map,
            constraints,
            ctx.openai_api_key,
            ctx.openai_model,
            ctx.openai_base_url,
            headers_path=str(ctx.workspace / f"{self.name}_openai_headers.json"),
            prior_agent_summaries=prior,
            fractal_memory_context=fractal_ctx,
            oracle_results=oracle,
            llm_runtime=ctx.llm_runtime,
        )
        result = AgentResult(name=self.name, summary=text.splitlines()[0] if text else "")
        result.openai_headers_path = ctx.workspace / f"{self.name}_openai_headers.json"
        result.evidence["llm_output"] = text
        return result
