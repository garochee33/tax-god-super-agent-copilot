from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class AgentResult:
    name: str
    summary: str
    patches: List[Path] = field(default_factory=list)
    evidence: Dict[str, str] = field(default_factory=dict)
    openai_headers_path: Optional[Path] = None


@dataclass
class SwarmState:
    repo_root: Path
    goal: str
    workspace: Optional[Path] = None
    results: Dict[str, AgentResult] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    reviewer_notes: Optional[str] = None
    final_report: Optional[str] = None
