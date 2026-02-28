from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from swarm.agents.base import LLMRuntime
from swarm.providers.registry import ProviderRegistry


def _is_retryable_error(error: Optional[str]) -> bool:
    """True if the error is transient (rate limit, timeout, 5xx) and fallback is sensible."""
    if not error:
        return False
    lower = error.lower()
    if "rate limit" in lower or "429" in error or "408" in error:
        return True
    if "timeout" in lower or "timed out" in lower:
        return True
    if "temporarily unavailable" in lower or "server error" in lower:
        return True
    if "bad gateway" in lower or "gateway timeout" in lower or "503" in error:
        return True
    if "500" in error or "502" in error or "504" in error:
        return True
    return False


def _run_llm(
    system: str,
    user: str,
    api_key: str | None,
    model: str,
    base_url: str,
    llm_runtime: Optional[LLMRuntime] = None,
    headers_path: str | None = None,
) -> str:
    runtime = llm_runtime or LLMRuntime(
        provider="openai",
        model=model,
        base_url=base_url,
        params={},
        fallback_models=[],
        fallback_runtimes=[],
    )
    registry = ProviderRegistry()
    timeout = int(runtime.params.get("timeout", 120)) if runtime.params else 120

    def _fresh_params(r: LLMRuntime) -> Dict[str, object]:
        return dict(r.params or {})

    def _base_url_for(r: LLMRuntime) -> Optional[str]:
        if r.base_url is not None:
            return r.base_url
        if r.provider in {"openai", "openai_compatible"}:
            return base_url
        return None

    def _try_provider(rt: LLMRuntime) -> Any:
        prov = registry.get(rt.provider, api_key_override=api_key)
        return prov.generate(
            system=system,
            user=user,
            model=rt.model or model,
            params=_fresh_params(rt),
            timeout=timeout,
            base_url=_base_url_for(rt),
        )

    res = _try_provider(runtime)

    # AUTO fallback: try fallback_runtimes (cross-provider) then fallback_models (legacy)
    if not res.ok and _is_retryable_error(res.error):
        if runtime.fallback_runtimes:
            for fb_rt in runtime.fallback_runtimes:
                res = _try_provider(fb_rt)
                if res.ok:
                    break
        if not res.ok and runtime.fallback_models:
            for fallback in runtime.fallback_models:
                res = _try_provider(
                    LLMRuntime(
                        provider=runtime.provider,
                        model=fallback,
                        base_url=_base_url_for(runtime),
                        params=_fresh_params(runtime),
                        fallback_models=[],
                        fallback_runtimes=[],
                    )
                )
                if res.ok:
                    break
    if headers_path:
        try:
            payload = {
                "headers": res.headers,
            }
            Path(headers_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass
    if not res.ok:
        return f"SUMMARY: LLM unavailable ({res.error})\nPATCH:\n```diff\n\n```\nTESTS:\nRISKS:\n"
    return res.output_text


def _build_user_sections(
    goal: str,
    repo_map: List[str],
    constraints: str,
    prior_summaries: str = "",
    fractal_memory: str = "",
    oracle_results: str = "",
) -> str:
    """Build user message with optional context sections."""
    repo_listing = "\n".join(repo_map[:200])
    parts = [
        f"Goal:\n{goal}\n",
        f"Repo map (top files):\n{repo_listing}\n",
        f"Constraints:\n{constraints}\n",
    ]
    if prior_summaries:
        parts.append(f"{prior_summaries}\n")
    if fractal_memory:
        parts.append(f"{fractal_memory}\n")
    if oracle_results:
        parts.append(f"{oracle_results}\n")
    return "\n".join(parts)


def run_reasoner_llm(
    goal: str,
    repo_map: List[str],
    constraints: str,
    api_key: str | None,
    model: str,
    base_url: str,
    headers_path: str | None = None,
    prior_agent_summaries: str = "",
    fractal_memory_context: str = "",
    oracle_results: str = "",
    llm_runtime: Optional[LLMRuntime] = None,
) -> str:
    """
    Fractal Reasoner: deep cognition and multi-step reasoning.
    Chain-of-thought, hypothesis formation, then actionable conclusion.
    """
    system = (
        "You are the Fractal Reasoner in a multi-agent AGI swarm. "
        "Decompose the goal, weigh evidence from the repo map, and propose concrete, "
        "high-impact improvements. Keep reasoning concise and actionable."
    )
    base = _build_user_sections(
        goal,
        repo_map,
        constraints,
        prior_agent_summaries,
        fractal_memory_context,
        oracle_results,
    )
    user = base + """
Return format:
- SUMMARY: <1–3 sentences>
- ANALYSIS: <3–7 bullets, concise>
- IMPROVEMENTS: <exactly 5 bullets>
- PATCH (if needed):
```diff
<unified diff here>
```
- TESTS: <commands to run>
- RISKS: <residual risks>
"""
    return _run_llm(system, user, api_key, model, base_url, llm_runtime, headers_path)


def run_critic_llm(
    goal: str,
    repo_map: List[str],
    constraints: str,
    api_key: str | None,
    model: str,
    base_url: str,
    headers_path: str | None = None,
    prior_agent_summaries: str = "",
    fractal_memory_context: str = "",
    oracle_results: str = "",
    llm_runtime: Optional[LLMRuntime] = None,
) -> str:
    """
    Critic agent: review, risk, consistency, pass/fail gate.
    """
    system = (
        "You are the Critic agent (review gate) in a multi-agent AGI swarm. "
        "Evaluate outputs for correctness, risk, and consistency. Return PASS or FAIL in SUMMARY."
    )
    base = _build_user_sections(
        goal,
        repo_map,
        constraints,
        prior_agent_summaries,
        fractal_memory_context,
        oracle_results,
    )
    user = base + """
Return format:
- SUMMARY: PASS or FAIL (1–3 sentences)
- RISKS: <residual risks>
- RECOMMENDATIONS: <optional>
"""
    return _run_llm(system, user, api_key, model, base_url, llm_runtime, headers_path)


def run_teacher_llm(
    goal: str,
    repo_map: List[str],
    constraints: str,
    api_key: str | None,
    model: str,
    base_url: str,
    headers_path: str | None = None,
    prior_agent_summaries: str = "",
    fractal_memory_context: str = "",
    oracle_results: str = "",
    llm_runtime: Optional[LLMRuntime] = None,
) -> str:
    """
    Teacher agent: explanations, curricula, onboarding.
    """
    system = (
        "You are the Teacher agent in a multi-agent AGI swarm. "
        "Explain concepts clearly, suggest learning order, and document decisions."
    )
    base = _build_user_sections(
        goal,
        repo_map,
        constraints,
        prior_agent_summaries,
        fractal_memory_context,
        oracle_results,
    )
    user = base + """
Return format:
- EXPLANATION: <clear explanation>
- LEARNING_ORDER: <optional steps for onboarding>
- SUMMARY: <1–3 sentences>
- DOCS_PATCH (if needed):
```diff
<unified diff here>
```
"""
    return _run_llm(system, user, api_key, model, base_url, llm_runtime, headers_path)


def run_agent_llm(
    role: str,
    goal: str,
    repo_map: List[str],
    constraints: str,
    api_key: str | None,
    model: str,
    base_url: str,
    headers_path: str | None = None,
    prior_agent_summaries: str = "",
    fractal_memory_context: str = "",
    oracle_results: str = "",
    llm_runtime: Optional[LLMRuntime] = None,
) -> str:
    system = (
        f"You are the {role} agent in a multi-agent code assistant swarm. "
        "Be concise, actionable, and output a patch if appropriate. "
        "Use clear reasoning when the task is complex."
    )
    base = _build_user_sections(
        goal,
        repo_map,
        constraints,
        prior_agent_summaries,
        fractal_memory_context,
        oracle_results,
    )
    user = base + """
Return format:
- SUMMARY: <1-3 sentences>
- PATCH (if needed):
```diff
<unified diff here>
```
- TESTS: <commands to run>
- RISKS: <residual risks>
"""
    return _run_llm(system, user, api_key, model, base_url, llm_runtime, headers_path)
