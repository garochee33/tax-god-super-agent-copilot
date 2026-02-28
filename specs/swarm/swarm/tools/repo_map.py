from __future__ import annotations

from pathlib import Path
from typing import List


def build_repo_map(repo_root: Path, max_files: int = 200) -> List[str]:
    entries: List[str] = []
    for path in sorted(repo_root.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(repo_root)
        entries.append(str(rel))
        if len(entries) >= max_files:
            break
    return entries
