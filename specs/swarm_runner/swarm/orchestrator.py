"""
Orchestrator for the Agent Swarm.

Manages agent execution (sequential or parallel), fractal memory, oracle integration,
patch application, and reflection loops for self-correction.
"""

from __future__ import annotations

import json
import os
import re
import shlex
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from swarm.agents.base import AgentContext, LLMRuntime
from swarm.agents.bot_agent import BotAgent
from swarm.agents.review import ReviewAgent
from swarm.bots import build_bots, default_bots
from swarm.config import AppConfig, ModelSpec
from swarm.fractal import (
    FractalMemoryStore,
    NodeArchetype,
    decompose_goal,
    energy_cost_for_agent,
    get_subtask_goal_for_role,
    order_agents_least_action,
)
from swarm.state import AgentResult, SwarmState
from swarm.tools.oracle import format_search_results_for_context, web_search
from swarm.tools.repo_map import build_repo_map

BOT_SPECS = default_bots()

# Reflection trigger patterns - indicate agent output needs improvement
REFLECTION_TRIGGERS = [
    r"\bFAIL\b",
    r"\berror\b",
    r"\bfailed\b",
    r"\bincomplete\b",
    r"\bunable to\b",
    r"\bcannot\b",
    r"\bTODO\b",
    r"\bmissing\b",
]


def _needs_reflection(result: AgentResult) -> bool:
    """Check if agent result indicates a need for reflection/retry."""
    if not result.summary:
        return True
    summary_lower = result.summary.lower()
    for pattern in REFLECTION_TRIGGERS:
        if re.search(pattern, summary_lower, re.IGNORECASE):
            return True
    return False


def _build_reflection_prompt(
    original_goal: str,
    previous_result: AgentResult,
    extra_notes: str = "",
) -> str:
    """Build a reflection prompt to improve the previous result."""
    extra = (extra_notes or "").strip()
    extra_section = f"\n\nAdditional notes:\n{extra}\n" if extra else ""
    return f"""[REFLECTION MODE]

Your previous output had issues that need correction.

Previous summary: {previous_result.summary[:500]}
{extra_section}

Issues detected:
- The output may contain errors, failures, or incomplete information
- Please re-analyze and provide a corrected, complete response

Original goal: {original_goal}

Instructions:
1. Identify what went wrong in your previous attempt
2. Correct any errors or misunderstandings
3. Provide a complete, accurate response
4. Ensure your SUMMARY line indicates success (PASS) if the task is achievable

Respond with an improved analysis."""


def _resolve_model_for_agent(agent_name: str, config: AppConfig) -> str:
    """Resolve model string: model_by_role -> models[name] or literal, else default."""
    model_key = config.swarm.model_by_role.get(agent_name)
    if model_key:
        spec = config.swarm.models.get(model_key)
        if isinstance(spec, ModelSpec) and spec.model:
            return spec.model
        return model_key
    return config.openai.model


def _spec_to_runtime(spec: ModelSpec, config: AppConfig) -> LLMRuntime:
    """Convert a ModelSpec to LLMRuntime with provider-specific params."""
    base_url = spec.base_url
    if base_url is None and spec.provider in {"openai", "openai_compatible"}:
        base_url = config.openai.base_url
    params = dict(spec.params or {})
    if (
        config.swarm.use_chat_completions is not None
        and spec.provider in {"openai", "openai_compatible"}
    ):
        params.setdefault("use_chat_completions", config.swarm.use_chat_completions)
    model_value = spec.model or config.openai.model
    return LLMRuntime(
        provider=spec.provider,
        model=model_value,
        base_url=base_url,
        params=params,
        fallback_models=[],
        fallback_runtimes=[],
    )


def _resolve_runtime_for_agent(agent_name: str, config: AppConfig) -> LLMRuntime:
    model_key = config.swarm.model_by_role.get(agent_name)
    if model_key and model_key in config.swarm.models:
        spec = config.swarm.models[model_key]
    elif model_key:
        spec = ModelSpec(provider="openai", model=model_key)
    else:
        spec = ModelSpec(provider="openai", model=config.openai.model)

    runtime = _spec_to_runtime(spec, config)

    # Build fallback_runtimes from fallback_models (AUTO: cross-provider fallback chain)
    fallback_runtimes: List[LLMRuntime] = []
    for key in spec.fallback_models or []:
        if key in config.swarm.models:
            fallback_spec = config.swarm.models[key]
            fallback_runtimes.append(_spec_to_runtime(fallback_spec, config))
        else:
            fallback_runtimes.append(
                _spec_to_runtime(ModelSpec(provider="openai", model=key), config)
            )
    runtime.fallback_runtimes = fallback_runtimes

    return runtime


def _format_prior_summaries(results: Dict[str, Any]) -> str:
    """Format current results as prior-agent summaries for context."""
    if not results:
        return ""
    lines = ["[Prior agent summaries]", ""]
    for name, r in results.items():
        summary = r.summary if hasattr(r, "summary") else str(r.get("summary", ""))
        lines.append(f"- {name}: {summary[:500]}{'...' if len(summary) > 500 else ''}")
    return "\n".join(lines)


def _apply_patches(
    repo_root: Path, patch_paths: List[Path], allowlist: List[str]
) -> Tuple[List[Path], List[str]]:
    """Apply patches via allowlisted git apply or patch. Returns (applied_paths, failed_errors)."""
    import shlex

    from swarm.tools.shell import run_shell
    applied: List[Path] = []
    failed: List[str] = []
    for p in patch_paths:
        if not p.exists():
            failed.append(f"{p}: file not found")
            continue
        path_str = shlex.quote(str(p.resolve()))
        tried = False
        success = False
        errors: List[str] = []
        for cmd in [f"git apply {path_str}", f"patch -p1 -i {path_str}"]:
            if any(cmd == a or cmd.startswith(a + " ") for a in allowlist):
                tried = True
                res = run_shell(cmd, repo_root, allowlist)
                if res.exit_code == 0:
                    applied.append(p)
                    success = True
                    break
                err = (res.stderr or res.stdout or "unknown error").strip()
                if not err:
                    err = f"exit {res.exit_code}"
                errors.append(f"{cmd}: {err}")
        if not tried:
            failed.append(f"{p}: no allowlisted apply command (need 'git apply' or 'patch')")
        elif not success:
            combined = " | ".join(errors)
            failed.append(f"{p}: {combined[:500]}")
    return applied, failed


def _validate_patch_apply_check(
    repo_root: Path,
    patch_path: Path,
    allowlist: List[str],
) -> Tuple[bool, str]:
    """
    Validate that a patch is a syntactically correct unified diff and would apply cleanly.

    This is stricter than "we managed to extract a ```diff``` block": it guards against
    hallucinated/corrupt diffs and mismatched file paths.
    """
    from swarm.tools.shell import run_shell

    if not patch_path.exists():
        return (False, f"patch not found: {patch_path}")
    cmd = f"git apply --check {shlex.quote(str(patch_path.resolve()))}"
    res = run_shell(cmd, repo_root, allowlist)
    if res.exit_code == 0:
        return (True, "ok")
    msg = (res.stderr or res.stdout or "").strip()
    if not msg:
        msg = f"exit {res.exit_code}"
    return (False, msg[:500])


@dataclass
class Orchestrator:
    repo_root: Path

    def run(self, goal: str, config: AppConfig, seed_prior_agent_summaries: str = "") -> SwarmState:
        state = SwarmState(repo_root=self.repo_root, goal=goal)
        state.mark_started()
        repo_map = build_repo_map(self.repo_root, goal=goal)
        # Use microseconds to avoid collisions when multiple runs start in the same second.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        # Optional multi-tenant workspace partitioning (used by runner_server.py).
        # This is intentionally a *single safe path segment* to avoid traversal.
        raw_workspace_id = (
            os.environ.get("AGENT_SWARM_WORKSPACE_SUBDIR")
            or os.environ.get("AGENT_SWARM_WORKSPACE_ID")
            or ""
        ).strip()
        safe_workspace_id = re.sub(r"[^a-zA-Z0-9._-]+", "_", raw_workspace_id).strip("._-")
        safe_workspace_id = safe_workspace_id[:64] if safe_workspace_id else ""

        workspace_root = (config.swarm.repo_root / config.swarm.workspace_dir).resolve()
        if safe_workspace_id:
            workspace = (workspace_root / safe_workspace_id / timestamp).resolve()
        else:
            workspace = (workspace_root / timestamp).resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        state.workspace = workspace

        # Fractal memory store (load existing if any)
        fractal_memory: Optional[FractalMemoryStore] = None
        if getattr(config.swarm, "fractal_memory", True):
            fractal_memory = FractalMemoryStore(
                workspace,
                use_vector_store=getattr(config.swarm, "use_vector_memory", True),
                database_url=getattr(config.swarm, "database_url", None),
                memory_backend=getattr(config.swarm, "memory_backend", None),
            )
            fractal_memory.load()

        # Oracle: web search if enabled
        oracle_results_str = ""
        if getattr(config.oracle, "enabled", False) and getattr(
            config.oracle, "search_api_key", None
        ):
            try:
                results = web_search(
                    goal,
                    api_key=config.oracle.search_api_key,
                    provider=getattr(config.oracle, "search_provider", "serper"),
                    max_results=getattr(config.oracle, "max_search_results", 5),
                )
                oracle_results_str = format_search_results_for_context(results)
            except Exception:
                pass

        # Planner: subtasks by role when fractal_planner=True
        subtasks: List[Any] = []
        if getattr(config.swarm, "fractal_planner", False):
            subtasks = decompose_goal(goal, len(repo_map))

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
            prior_agent_summaries=seed_prior_agent_summaries or "",
            model_key=None,
            fractal_memory_context=(
                fractal_memory.format_relevant_for_context(goal, limit=5)
                if fractal_memory
                else ""
            ),
            subtask_goal=None,
            oracle_results=oracle_results_str,
            llm_runtime=None,
        )
        if config.swarm.promotion_ladder:
            ctx.constraints["promotion_ladder"] = " > ".join(config.swarm.promotion_ladder)

        specs = build_bots(config.swarm.bots) if config.swarm.bots else BOT_SPECS
        if config.swarm.enabled_bots:
            enabled = set(config.swarm.enabled_bots)
            specs = [s for s in specs if s.name in enabled]
        if config.swarm.disabled_bots:
            disabled = set(config.swarm.disabled_bots)
            specs = [s for s in specs if s.name not in disabled]

        active_cluster = config.swarm.active_cluster
        cluster_specs = {c.name: c for c in config.swarm.clusters}
        cluster = cluster_specs.get(active_cluster) if active_cluster else None
        if cluster and cluster.bots:
            spec_by_name = {s.name: s for s in specs}
            specs = [spec_by_name[n] for n in cluster.bots if n in spec_by_name]

        agents = [BotAgent(spec) for spec in specs]
        if getattr(config.swarm, "fractal_routing", True) and not (cluster and cluster.bots):
            agent_names = [a.name for a in agents]
            ordered_names = order_agents_least_action(agent_names, ctx.constraints)
            name_to_agent = {a.name: a for a in agents}
            agents = [name_to_agent[n] for n in ordered_names if n in name_to_agent]

        inter_agent = getattr(config.swarm, "inter_agent_context", True)
        if cluster and cluster.execution in {"sequential", "parallel"}:
            inter_agent = cluster.execution == "sequential"
        agent_timeout: Optional[int] = getattr(config.swarm, "agent_timeout_seconds", None)
        max_reflections: int = getattr(config.swarm, "max_reflection_iterations", 2)
        enable_reflection: bool = getattr(config.swarm, "enable_reflection", True)

        def _run_agent_with_timeout(agent: Any, run_ctx: AgentContext) -> Any:
            if agent_timeout is None or agent_timeout <= 0:
                return agent.run(run_ctx)
            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(agent.run, run_ctx)
                return fut.result(timeout=agent_timeout)

        def _run_agent_with_reflection(
            agent: Any,
            run_ctx: AgentContext,
            max_iterations: int = 2,
        ) -> Any:
            """Run agent with reflection loop for self-correction."""
            result = _run_agent_with_timeout(agent, run_ctx)

            def _enforce_patch_validity(r: Any) -> Tuple[Any, str]:
                """
                Enforce that any produced patches are valid unified diffs that apply cleanly.

                If a patch is invalid, mark the result as FAIL so reflection reruns the agent.
                """
                patch_paths = list(getattr(r, "patches", []) or [])
                if not patch_paths:
                    return (r, "")
                errors: List[str] = []
                ok_all = True
                for p in patch_paths:
                    ok, msg = _validate_patch_apply_check(self.repo_root, p, config.swarm.allowlist)
                    if not ok:
                        ok_all = False
                        errors.append(f"{p.name}: {msg}")
                if ok_all:
                    return (r, "")

                # Prevent later apply phase from attempting invalid patches.
                try:
                    r.patches = []
                except Exception:
                    pass
                note = (
                    "Invalid patch output detected. The PATCH must be a valid unified diff that "
                    "passes `git apply --check`. Errors:\n- " + "\n- ".join(errors)
                )
                # Force reflection via FAIL trigger.
                try:
                    r.summary = "SUMMARY: FAIL (invalid patch; see patch_check errors)"
                except Exception:
                    pass
                try:
                    r.evidence["patch_check"] = note
                except Exception:
                    pass
                return (r, note)

            if not enable_reflection or max_iterations <= 0:
                result, _note = _enforce_patch_validity(result)
                return result

            iteration = 0
            # Enforce patch validity before deciding whether to reflect.
            result, patch_note = _enforce_patch_validity(result)
            while iteration < max_iterations and _needs_reflection(result):
                iteration += 1
                # Add reflection context
                reflection_prompt = _build_reflection_prompt(
                    run_ctx.subtask_goal or run_ctx.goal,
                    result,
                    extra_notes=patch_note,
                )
                run_ctx.prior_agent_summaries = (
                    (run_ctx.prior_agent_summaries or "")
                    + f"\n\n{reflection_prompt}"
                )

                # Re-run agent
                try:
                    result = _run_agent_with_timeout(agent, run_ctx)
                    result.reflection_count = iteration
                    # Re-enforce patch validity after rerun.
                    result, patch_note = _enforce_patch_validity(result)
                except Exception:
                    break

            return result

        if inter_agent:
            # Sequential: pass prior summaries and update fractal memory each step
            for agent in agents:
                ctx.subtask_goal = (
                    get_subtask_goal_for_role(agent.name, subtasks, goal)
                    if subtasks
                    else goal
                )
                ctx.model_key = _resolve_model_for_agent(agent.name, config)
                runtime = _resolve_runtime_for_agent(agent.name, config)
                ctx.llm_runtime = runtime
                ctx.openai_model = runtime.model
                if runtime.base_url:
                    ctx.openai_base_url = runtime.base_url
                if fractal_memory:
                    ctx.fractal_memory_context = fractal_memory.format_relevant_for_context(
                        ctx.subtask_goal or goal,
                        limit=5,
                    )
                try:
                    # Use reflection-enabled runner for improved results
                    result = _run_agent_with_reflection(agent, ctx, max_reflections)
                    state.results[agent.name] = result
                    energy = energy_cost_for_agent(agent.name, ctx.constraints)
                    reflection_note = (
                        f" (reflected {result.reflection_count}x)"
                        if getattr(result, "reflection_count", 0) > 0
                        else ""
                    )
                    state.trace_events.append({
                        "agent": agent.name,
                        "energy": energy,
                        "timestamp": datetime.now().isoformat(),
                        "summary_snippet": result.summary[:300] if result.summary else "",
                        "reflection_count": getattr(result, "reflection_count", 0),
                        "provider": ctx.llm_runtime.provider if ctx.llm_runtime else None,
                        "model": ctx.llm_runtime.model if ctx.llm_runtime else None,
                    })
                    if fractal_memory and result.summary:
                        fractal_memory.add_node(
                            NodeArchetype.ARTIFACT.value,
                            agent.name,
                            {
                                "summary": result.summary + reflection_note,
                                "agent": agent.name,
                            },
                            energy_cost=energy,
                        )
                    ctx.prior_agent_summaries = _format_prior_summaries(state.results)
                except FuturesTimeoutError:
                    err = f"{agent.name}: timeout after {agent_timeout}s"
                    state.errors.append(err)
                    state.trace_events.append(
                        {
                            "agent": agent.name,
                            "error": err,
                            "timestamp": datetime.now().isoformat(),
                            "provider": ctx.llm_runtime.provider if ctx.llm_runtime else None,
                            "model": ctx.llm_runtime.model if ctx.llm_runtime else None,
                        }
                    )
                except Exception as exc:
                    state.errors.append(f"{agent.name}: {exc}")
                    state.trace_events.append(
                        {
                            "agent": agent.name,
                            "error": str(exc),
                            "timestamp": datetime.now().isoformat(),
                            "provider": ctx.llm_runtime.provider if ctx.llm_runtime else None,
                            "model": ctx.llm_runtime.model if ctx.llm_runtime else None,
                        }
                    )
        else:
            # Parallel: no prior context; each agent gets its own ctx copy
            # with subtask_goal and model
            def make_ctx_for_agent(a: Any) -> AgentContext:
                runtime = _resolve_runtime_for_agent(a.name, config)
                c = AgentContext(
                    repo_root=ctx.repo_root,
                    goal=ctx.goal,
                    repo_map=ctx.repo_map,
                    constraints=dict(ctx.constraints),
                    allowlist=ctx.allowlist,
                    workspace=ctx.workspace,
                    openai_api_key=ctx.openai_api_key,
                    openai_model=runtime.model,
                    openai_base_url=runtime.base_url or ctx.openai_base_url,
                    prior_agent_summaries="",
                    model_key=_resolve_model_for_agent(a.name, config),
                    fractal_memory_context=ctx.fractal_memory_context,
                    subtask_goal=(
                        get_subtask_goal_for_role(a.name, subtasks, goal)
                        if subtasks
                        else goal
                    ),
                    oracle_results=ctx.oracle_results,
                    llm_runtime=runtime,
                )
                return c

            concurrency = config.swarm.concurrency
            if cluster and cluster.concurrency:
                concurrency = cluster.concurrency
            if concurrency and concurrency > 1:
                with ThreadPoolExecutor(max_workers=concurrency) as executor:
                    futures = {}
                    for agent in agents:
                        agent_ctx = make_ctx_for_agent(agent)
                        futures[
                            executor.submit(
                                _run_agent_with_reflection,
                                agent,
                                agent_ctx,
                                max_reflections,
                            )
                        ] = (
                            agent,
                            agent_ctx,
                        )
                    for future in as_completed(futures):
                        agent, agent_ctx = futures[future]
                        runtime = agent_ctx.llm_runtime or _resolve_runtime_for_agent(
                            agent.name, config
                        )
                        try:
                            result = future.result()
                            state.results[agent.name] = result
                            state.trace_events.append({
                                "agent": agent.name,
                                "energy": energy_cost_for_agent(agent.name, ctx.constraints),
                                "timestamp": datetime.now().isoformat(),
                                "summary_snippet": result.summary[:300] if result.summary else "",
                                "reflection_count": getattr(result, "reflection_count", 0),
                                "provider": runtime.provider if runtime else None,
                                "model": runtime.model if runtime else None,
                            })
                        except FuturesTimeoutError:
                            err = f"{agent.name}: timeout after {agent_timeout}s"
                            state.errors.append(err)
                            state.trace_events.append(
                                {
                                    "agent": agent.name,
                                    "error": err,
                                    "timestamp": datetime.now().isoformat(),
                                    "provider": runtime.provider if runtime else None,
                                    "model": runtime.model if runtime else None,
                                }
                            )
                        except Exception as exc:
                            err = f"{agent.name}: {exc}"
                            state.errors.append(err)
                            state.trace_events.append(
                                {
                                    "agent": agent.name,
                                    "error": str(exc),
                                    "timestamp": datetime.now().isoformat(),
                                    "provider": runtime.provider if runtime else None,
                                    "model": runtime.model if runtime else None,
                                }
                            )
                if fractal_memory:
                    for name, r in state.results.items():
                        if r.summary:
                            fractal_memory.add_node(
                                NodeArchetype.ARTIFACT.value,
                                name,
                                {"summary": r.summary, "agent": name},
                                energy_cost_for_agent(name, ctx.constraints),
                            )
            else:
                for agent in agents:
                    agent_ctx = make_ctx_for_agent(agent)
                    runtime = agent_ctx.llm_runtime or _resolve_runtime_for_agent(
                        agent.name, config
                    )
                    try:
                        result = _run_agent_with_reflection(agent, agent_ctx, max_reflections)
                        state.results[agent.name] = result
                        state.trace_events.append({
                            "agent": agent.name,
                            "energy": energy_cost_for_agent(agent.name, ctx.constraints),
                            "timestamp": datetime.now().isoformat(),
                            "summary_snippet": result.summary[:300] if result.summary else "",
                            "reflection_count": getattr(result, "reflection_count", 0),
                            "provider": runtime.provider if runtime else None,
                            "model": runtime.model if runtime else None,
                        })
                    except FuturesTimeoutError:
                        err = f"{agent.name}: timeout after {agent_timeout}s"
                        state.errors.append(err)
                        state.trace_events.append(
                            {
                                "agent": agent.name,
                                "error": err,
                                "timestamp": datetime.now().isoformat(),
                                "provider": runtime.provider if runtime else None,
                                "model": runtime.model if runtime else None,
                            }
                        )
                    except Exception as exc:
                        err = f"{agent.name}: {exc}"
                        state.errors.append(err)
                        state.trace_events.append(
                            {
                                "agent": agent.name,
                                "error": str(exc),
                                "timestamp": datetime.now().isoformat(),
                                "provider": runtime.provider if runtime else None,
                                "model": runtime.model if runtime else None,
                            }
                        )
                if fractal_memory:
                    for name, r in state.results.items():
                        if r.summary:
                            fractal_memory.add_node(
                                NodeArchetype.ARTIFACT.value,
                                name,
                                {"summary": r.summary, "agent": name},
                                energy_cost_for_agent(name, ctx.constraints),
                            )

        # Reviewer: gets full prior summaries
        ctx.prior_agent_summaries = _format_prior_summaries(state.results)
        ctx.subtask_goal = None
        ctx.model_key = _resolve_model_for_agent("review", config)
        runtime = _resolve_runtime_for_agent("review", config)
        ctx.llm_runtime = runtime
        ctx.openai_model = runtime.model
        if runtime.base_url:
            ctx.openai_base_url = runtime.base_url
        reviewer = ReviewAgent()
        try:
            review = _run_agent_with_timeout(reviewer, ctx)
            state.results[reviewer.name] = review
            state.reviewer_notes = review.summary
            state.trace_events.append({
                "agent": "review",
                "energy": 3.0,
                "timestamp": datetime.now().isoformat(),
                "summary_snippet": review.summary[:300] if review.summary else "",
                "provider": ctx.llm_runtime.provider if ctx.llm_runtime else None,
                "model": ctx.llm_runtime.model if ctx.llm_runtime else None,
            })
        except FuturesTimeoutError:
            state.errors.append(f"review: timeout after {agent_timeout}s")
            state.reviewer_notes = "(review timed out)"
        except Exception as exc:
            state.errors.append(f"review: {exc}")
            state.reviewer_notes = f"(review failed: {exc})"

        # Apply patches if configured (or dry-run)
        apply_patches = getattr(config.swarm, "apply_patches", False)
        dry_run = getattr(config.swarm, "apply_patches_dry_run", False)
        if apply_patches or dry_run:
            all_patches: List[Path] = []
            for r in state.results.values():
                all_patches.extend(getattr(r, "patches", []) or [])
            if dry_run:
                # Write planned commands to workspace; do not modify repo
                if state.workspace and all_patches:
                    plan_lines = [f"# Dry run: would apply from repo_root={self.repo_root}", ""]
                    for p in all_patches:
                        plan_lines.append(f"git apply {p.resolve()}")
                        plan_lines.append(f"# or: patch -p1 -i {p.resolve()}")
                    (state.workspace / "apply_plan.txt").write_text(
                        "\n".join(plan_lines),
                        encoding="utf-8",
                    )
                state.applied_patches = []
                state.patch_errors = []
                state.dry_run_patch_count = len(all_patches)
            else:
                applied, failed = _apply_patches(
                    self.repo_root,
                    all_patches,
                    config.swarm.allowlist,
                )
                state.applied_patches = applied
                state.patch_errors = failed
                for e in failed:
                    state.errors.append(f"Patch apply: {e}")

        # Set memory backend in metrics if fractal memory is active
        if fractal_memory:
            state.metrics.memory_backend = getattr(
                fractal_memory, "backend", "json"
            )

        state.final_report = self._compile_report(state, dry_run=dry_run)
        self._write_artifacts(state, agents)
        self._write_fractal_trace(state, agents)

        # Mark completion and aggregate metrics
        state.mark_completed()
        return state

    def _compile_report(self, state: SwarmState, dry_run: bool = False) -> str:
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
        if dry_run:
            n = getattr(state, "dry_run_patch_count", None) or 0
            lines.append(
                f"Dry run: {n} patches would be applied "
                "(see workspace/apply_plan.txt; repo not modified)"
            )
        elif state.applied_patches:
            lines.append(f"Applied patches: {len(state.applied_patches)}")
        if state.patch_errors:
            lines.append("Patch apply failures:")
            lines.extend([f"- {e}" for e in state.patch_errors])
        return "\n".join(lines)

    def _write_artifacts(self, state: SwarmState, agents: List[Any]) -> None:
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
                    content += (
                        "[openai_headers]\n"
                        + result.openai_headers_path.read_text(encoding="utf-8").strip()
                        + "\n\n"
                    )
                except Exception:
                    pass
            evidence_path.write_text(content.strip() + "\n", encoding="utf-8")

    def _write_fractal_trace(self, state: SwarmState, agents: List[Any]) -> None:
        if not state.workspace:
            return
        trace = {
            "goal": state.goal,
            "phases": ["fan_out", "review"],
            "agent_order": [a.name for a in agents],
            "trace_events": state.trace_events,
            "errors": state.errors,
            "applied_patches": [str(p) for p in state.applied_patches],
            "patch_errors": state.patch_errors,
        }
        (state.workspace / "fractal_trace.json").write_text(
            json.dumps(trace, indent=2),
            encoding="utf-8",
        )
