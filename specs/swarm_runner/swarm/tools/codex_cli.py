from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class CodexCLI:
    repo_root: Path

    def run(self, prompt: str) -> str:
        # Placeholder for a local codex/cli adapter if needed.
        # In offline mode, this can be extended to call a local model.
        return f"[codex_cli not configured] {prompt[:200]}"
