from __future__ import annotations

from swarm.agents.base import AgentContext, BaseAgent
from swarm.bots import BotSpec
from swarm.state import AgentResult
from swarm.tools.llm import run_agent_llm, run_reasoner_llm, run_teacher_llm
from swarm.tools.offline import run_offline_checks


class BotAgent(BaseAgent):
    def __init__(self, spec: BotSpec) -> None:
        self.spec = spec
        self.name = spec.name

    def run(self, ctx: AgentContext) -> AgentResult:
        constraints = (
            "Non-destructive changes are allowed (edits/additions within this repo). "
            "Do NOT delete files, rewrite huge sections, or run shell commands. "
            "File scope: repo root only. "
            "If you propose a change, include a unified diff in PATCH."
        )
        ladder = ctx.constraints.get("promotion_ladder", "")
        if ladder:
            constraints += f" Promotion ladder: {ladder}."
        provider_name = ctx.llm_runtime.provider if ctx.llm_runtime else "openai"
        if provider_name in {"openai", "openai_compatible"} and not ctx.openai_api_key:
            summary = f"SUMMARY: Offline {self.spec.name} scan complete (no LLM)."
            evidence = run_offline_checks(
                ctx.repo_root,
                ctx.allowlist,
                self.spec.offline_checks,
            )
            result = AgentResult(name=self.name, summary=summary)
            result.evidence["offline"] = evidence
            return result

        goal = ctx.subtask_goal or ctx.goal
        headers_path = str(ctx.workspace / f"{self.name}_openai_headers.json")
        prior = getattr(ctx, "prior_agent_summaries", "") or ""
        fractal_ctx = getattr(ctx, "fractal_memory_context", "") or ""
        oracle = getattr(ctx, "oracle_results", "") or ""
        if self.spec.role == "REASONER":
            text = run_reasoner_llm(
                goal,
                ctx.repo_map,
                constraints,
                ctx.openai_api_key,
                ctx.openai_model,
                ctx.openai_base_url,
                headers_path=headers_path,
                prior_agent_summaries=prior,
                fractal_memory_context=fractal_ctx,
                oracle_results=oracle,
                llm_runtime=ctx.llm_runtime,
            )
        elif self.spec.role == "TEACHER":
            text = run_teacher_llm(
                goal,
                ctx.repo_map,
                constraints,
                ctx.openai_api_key,
                ctx.openai_model,
                ctx.openai_base_url,
                headers_path=headers_path,
                prior_agent_summaries=prior,
                fractal_memory_context=fractal_ctx,
                oracle_results=oracle,
                llm_runtime=ctx.llm_runtime,
            )
        else:
            text = run_agent_llm(
                self.spec.role,
                goal,
                ctx.repo_map,
                constraints,
                ctx.openai_api_key,
                ctx.openai_model,
                ctx.openai_base_url,
                headers_path=headers_path,
                prior_agent_summaries=prior,
                fractal_memory_context=fractal_ctx,
                oracle_results=oracle,
                llm_runtime=ctx.llm_runtime,
            )
        patch = self._extract_patch(text)
        patch_path = self._write_patch(ctx, patch)
        result = AgentResult(name=self.name, summary=text.splitlines()[0] if text else "")
        result.openai_headers_path = ctx.workspace / f"{self.name}_openai_headers.json"
        if patch_path:
            result.patches.append(patch_path)
        result.evidence["llm_output"] = text
        return result
