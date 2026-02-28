from __future__ import annotations

from typing import List

from swarm.tools.openai_responses import run_openai


def run_agent_llm(
    role: str,
    goal: str,
    repo_map: List[str],
    constraints: str,
    api_key: str | None,
    model: str,
    base_url: str,
    enable_network: bool = False,
    headers_path: str | None = None,
) -> str:
    system = (
        f"You are the {role} agent in a multi-agent code assistant swarm. "
        "Be concise, actionable, and output a patch if appropriate."
    )
    repo_listing = "\n".join(repo_map[:200])
    user = f"""
Goal:
{goal}

Repo map (top files):
{repo_listing}

Constraints:
{constraints}

Return format:
- SUMMARY: <1-3 sentences>
- PATCH (if needed):
```diff
<unified diff here>
```
- TESTS: <commands to run>
- RISKS: <residual risks>
"""
    res = run_openai(
        api_key,
        model,
        system,
        user,
        base_url=base_url,
        enable_network=enable_network,
    )
    if headers_path:
        try:
            from pathlib import Path
            import json

            payload = {
                "client_request_id": res.client_request_id,
                "headers": res.headers,
            }
            Path(headers_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass
    if not res.ok:
        return f"SUMMARY: LLM unavailable ({res.error})\nPATCH:\n```diff\n\n```\nTESTS:\nRISKS:\n"
    return res.output_text
