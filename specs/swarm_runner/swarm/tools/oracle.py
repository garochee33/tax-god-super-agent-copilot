"""
Oracle & Tools Layer (Fractal AGI Web of Life).

Web search (Serper/Tavily), code execution sandbox,
evidence distillation into new seeds. See docs/FRACTAL_AGI_OMNISYNTH_INGEST.md.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class OracleSearchResult:
    """Single web-search result for evidence distillation."""
    title: str
    snippet: str
    url: str
    score: float = 0.0


def web_search(
    query: str,
    api_key: Optional[str] = None,
    provider: str = "serper",
    max_results: int = 5,
) -> List[OracleSearchResult]:
    """
    Oracle: web search via Serper or Tavily when api_key is set.
    Returns empty list if no key or on error.
    """
    if not api_key or not query.strip():
        return []
    results: List[OracleSearchResult] = []
    try:
        if provider == "serper":
            import urllib.request
            req = urllib.request.Request(
                "https://google.serper.dev/search",
                data=json.dumps({"q": query.strip(), "num": max_results}).encode("utf-8"),
                headers={
                    "X-API-KEY": api_key,
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            for i, o in enumerate(data.get("organic", [])[:max_results]):
                results.append(OracleSearchResult(
                    title=o.get("title", ""),
                    snippet=o.get("snippet", ""),
                    url=o.get("link", ""),
                    score=1.0 / (i + 1),
                ))
        elif provider == "tavily":
            import urllib.request
            payload = {
                "api_key": api_key,
                "query": query.strip(),
                "search_depth": "basic",
                "max_results": max_results,
            }
            req = urllib.request.Request(
                "https://api.tavily.com/search",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            for r in data.get("results", [])[:max_results]:
                results.append(OracleSearchResult(
                    title=r.get("title", ""),
                    snippet=r.get("content", ""),
                    url=r.get("url", ""),
                ))
    except Exception:
        pass
    return results


def web_search_stub(query: str, max_results: int = 5) -> List[OracleSearchResult]:
    """Stub when no API key: returns empty list."""
    return []


def sandbox_execute_stub(
    command: str,
    cwd: Path,
    allowlist: List[str],
    timeout_seconds: int = 30,
) -> tuple[int, str, str]:
    """
    Oracle: code execution sandbox. Stub: delegates to swarm.tools.shell.run_shell
    when command is allowlisted; otherwise returns (1, "", "Blocked").
    """
    from swarm.tools.shell import run_shell
    res = run_shell(command, cwd, allowlist)
    return res.exit_code, res.stdout, res.stderr


def distill_evidence_to_seeds(results: List[OracleSearchResult]) -> List[dict]:
    """
    Evidence distillation into new seeds (Fractal Knowledge Core).
    Returns list of seed payloads for indexing.
    """
    return [{"title": r.title, "snippet": r.snippet, "url": r.url} for r in results]


def format_search_results_for_context(results: List[OracleSearchResult]) -> str:
    """Format search results as a string for injection into agent context."""
    if not results:
        return ""
    lines = ["[Oracle web search results]", ""]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r.title}\n   {r.snippet}\n   {r.url}")
    return "\n".join(lines)
