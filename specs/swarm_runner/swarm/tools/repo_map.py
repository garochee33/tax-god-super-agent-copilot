"""
Repo map: list of repo paths for agent context.
Respects .gitignore (pathspec when available, else simple patterns) and ranks by relevance to goal.
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import List, Set, Tuple, Union

# Optional: full gitignore semantics (negation, **, etc.)
_PATHSPEC_SPEC = None
try:
    import pathspec
    _PATHSPEC_SPEC = pathspec
except Exception:
    pass

# Prefer these extensions (code/config) when ranking
CODE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".go", ".rs", ".rb", ".java", ".kt", ".swift", ".c", ".h", ".cpp", ".hpp",
    ".md", ".rst", ".toml", ".yaml", ".yml", ".json", ".cfg", ".ini", ".env",
    ".sql", ".sh", ".bash", ".zsh", ".css", ".scss", ".html", ".vue", ".svelte",
}


def _read_gitignore(repo_root: Path) -> Tuple[Union["pathspec.PathSpec", Set[str]], bool]:
    """
    Return (spec, use_pathspec). If pathspec is available, return PathSpec
    from .gitignore lines; else set of patterns.
    """
    gitignore = repo_root / ".gitignore"
    lines: List[str] = []
    if gitignore.exists():
        try:
            for line in gitignore.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                lines.append(line)
        except Exception:
            pass
    if _PATHSPEC_SPEC and lines:
        try:
            spec = _PATHSPEC_SPEC.PathSpec.from_lines("gitignore", lines)
            return (spec, True)
        except Exception:
            pass
    # Fallback: simple pattern set (legacy behavior)
    ignore: Set[str] = set()
    for line in lines:
        if line.startswith("/"):
            line = line[1:]
        ignore.add(line)
        if "/" in line:
            ignore.add(line.split("/")[0])
    return (ignore, False)


def _is_ignored(rel_path: str, ignore_patterns: Set[str]) -> bool:
    """Check if path is ignored by any pattern (simple prefix/suffix match)."""
    parts = rel_path.split("/")
    for pattern in ignore_patterns:
        # Basic glob support (e.g., *.egg-info, **/*.min.js)
        if "*" in pattern and fnmatch.fnmatch(rel_path, pattern):
            return True
        if pattern.startswith("**"):
            if pattern[2:] in rel_path or rel_path.endswith(pattern[2:].strip("*")):
                return True
        elif pattern.endswith("/"):
            pat = pattern.rstrip("/")
            if rel_path.startswith(pat) or parts[0] == pat:
                return True
        elif "/" in pattern:
            if rel_path.startswith(pattern) or pattern in rel_path:
                return True
        else:
            # Treat bare patterns as "ignore any path segment named pattern".
            # This makes defaults like "venv" / "__pycache__" work even when nested.
            if (
                pattern in parts
                or parts[0] == pattern
                or rel_path == pattern
                or rel_path.endswith("/" + pattern)
            ):
                return True
    return False


def _relevance_score(rel_path: str, goal: str) -> float:
    """Higher = more relevant. Code extensions + keyword overlap with goal."""
    score = 0.0
    path_lower = rel_path.lower()
    goal_lower = goal.lower() if goal else ""
    depth = path_lower.count("/")

    # Prefer project "core" dirs over vendored/external code.
    if path_lower.startswith(("swarm/", "src/", "app/", "tests/", "test/", "docs/")):
        score += 25.0
    if any(
        seg in path_lower
        for seg in ("/external_modules/", "/vendor/", "/third_party/", "/externals/")
    ):
        score -= 25.0
    if any(seg in path_lower for seg in ("/dist/", "/build/", "/.swarm_work/")):
        score -= 10.0

    # Prefer top-level metadata/config docs.
    if path_lower in {"pyproject.toml", "setup.py", "requirements.txt", "readme.md"}:
        score += 30.0
    if path_lower.endswith((".toml", ".yaml", ".yml")) and depth <= 2:
        score += 5.0

    # Prefer code files
    suffix = Path(rel_path).suffix.lower()
    if suffix in CODE_EXTENSIONS:
        score += 10.0
    if suffix in (".py", ".ts", ".tsx", ".js", ".go", ".rs"):
        score += 5.0
    # Keyword overlap (simple word tokenization)
    goal_words = set(re.findall(r"[a-z0-9_]+", goal_lower))
    path_words = set(re.findall(r"[a-z0-9_]+", path_lower))
    overlap = len(goal_words & path_words)
    score += overlap * 3.0

    # Slightly prefer shallower paths when ties happen.
    score -= depth * 0.25
    return score


def build_repo_map(
    repo_root: Path,
    goal: str = "",
    max_files: int = 200,
    use_gitignore: bool = True,
    rank_by_relevance: bool = True,
) -> List[str]:
    """
    Build list of repo file paths for agent context.
    Respects .gitignore (pathspec when installed, else simple patterns);
    optionally ranks by relevance.
    """
    # Always ignore common build/venv/cache folders (even if .gitignore is absent or incomplete).
    # These are matched as path segments anywhere in the tree by _is_ignored().
    default_ignores: Set[str] = {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        "site-packages",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "dist",
        "build",
        ".swarm_work",
        "*.egg-info",
    }
    spec_or_patterns: Union[object, Set[str]] = set()
    use_pathspec = False
    extra_ignores = set(default_ignores)
    if use_gitignore:
        spec_or_patterns, use_pathspec = _read_gitignore(repo_root)
        # If we don't have full pathspec semantics, merge default ignores into the
        # simple pattern set so we always skip venv/cache/build folders.
        if not use_pathspec and isinstance(spec_or_patterns, set):
            spec_or_patterns = set(spec_or_patterns) | set(default_ignores)
    else:
        spec_or_patterns = set()

    def _file_ignored(rel_str: str) -> bool:
        if not use_gitignore:
            return _is_ignored(rel_str, extra_ignores)
        if extra_ignores and _is_ignored(rel_str, extra_ignores):
            return True
        if use_pathspec and _PATHSPEC_SPEC and hasattr(spec_or_patterns, "match_file"):
            return bool(spec_or_patterns.match_file(rel_str))
        if isinstance(spec_or_patterns, set):
            return _is_ignored(rel_str, spec_or_patterns)
        return False

    entries: List[tuple[str, float]] = []
    for path in sorted(repo_root.rglob("*")):
        if path.is_dir():
            continue
        try:
            rel = path.relative_to(repo_root)
            rel_str = str(rel).replace("\\", "/")
        except ValueError:
            continue
        if _file_ignored(rel_str):
            continue
        score = _relevance_score(rel_str, goal) if rank_by_relevance else 0.0
        entries.append((rel_str, score))

    if rank_by_relevance and goal:
        entries.sort(key=lambda x: -x[1])
    else:
        entries.sort(key=lambda x: x[0])

    return [e[0] for e in entries[:max_files]]
