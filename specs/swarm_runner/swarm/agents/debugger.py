from __future__ import annotations

from swarm.agents.base import AgentContext, BaseAgent
from swarm.state import AgentResult
from swarm.tools.llm import run_agent_llm
from swarm.tools.offline import rg_command, run_offline_checks


class DebuggerAgent(BaseAgent):
    name = "debugger"

    def run(self, ctx: AgentContext) -> AgentResult:
        constraints = "No destructive ops. File scope: repo root only."
        if not ctx.openai_api_key:
            summary = "SUMMARY: Offline debug scan complete (no LLM)."
            evidence = run_offline_checks(
                ctx.repo_root,
                ctx.allowlist,
                [
                    rg_command("\"Traceback|Exception|ERROR|stacktrace|panic\""),
                    rg_command("\"log|logging|logger|debug\""),
                ],
            )
            result = AgentResult(name=self.name, summary=summary)
            result.evidence["offline"] = evidence
            return result

        text = run_agent_llm(
            "DEBUGGER",
            ctx.goal,
            ctx.repo_map,
            constraints,
            ctx.openai_api_key,
            ctx.openai_model,
            ctx.openai_base_url,
            headers_path=str(ctx.workspace / f"{self.name}_openai_headers.json"),
        )
        patch = self._extract_patch(text)
        patch_path = self._write_patch(ctx, patch)
        result = AgentResult(name=self.name, summary=text.splitlines()[0] if text else "")
        result.openai_headers_path = ctx.workspace / f"{self.name}_openai_headers.json"
        if patch_path:
            result.patches.append(patch_path)
        result.evidence["llm_output"] = text
        return result
