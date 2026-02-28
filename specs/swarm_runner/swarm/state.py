"""
State management for the Agent Swarm.

Defines AgentResult and SwarmState dataclasses for tracking execution state,
results, errors, and metrics across the swarm run.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing."""
    return f"swarm-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"


@dataclass
class AgentResult:
    """Result from a single agent execution."""

    name: str
    summary: str
    patches: List[Path] = field(default_factory=list)
    evidence: Dict[str, str] = field(default_factory=dict)
    openai_headers_path: Optional[Path] = None
    # Enhanced metrics
    latency_ms: Optional[float] = None
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    reflection_count: int = 0  # Number of reflection iterations


@dataclass
class SwarmMetrics:
    """Aggregated metrics for the swarm run."""

    total_latency_ms: float = 0.0
    total_tokens_used: int = 0
    agents_succeeded: int = 0
    agents_failed: int = 0
    agents_timed_out: int = 0
    reflection_iterations: int = 0
    memory_backend: str = "json"


@dataclass
class SwarmState:
    """
    Complete state of a swarm execution.

    Tracks all agent results, errors, patches, and provides correlation IDs
    for distributed tracing across the system.
    """

    repo_root: Path
    goal: str
    # Correlation ID for distributed tracing
    correlation_id: str = field(default_factory=generate_correlation_id)
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    # Workspace and results
    workspace: Optional[Path] = None
    results: Dict[str, AgentResult] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    reviewer_notes: Optional[str] = None
    final_report: Optional[str] = None
    # Structured Fractal-Trace: phases, agent order, energy, timestamps
    trace_events: List[Dict[str, Any]] = field(default_factory=list)
    # Patches that were successfully applied (when apply_patches=True)
    applied_patches: List[Path] = field(default_factory=list)
    # Patch apply failures: list of "path: error_message" (when apply_patches=True)
    patch_errors: List[str] = field(default_factory=list)
    # When apply_patches_dry_run: number of patches that would be applied (for report)
    dry_run_patch_count: Optional[int] = None
    # Aggregated metrics
    metrics: SwarmMetrics = field(default_factory=SwarmMetrics)

    def mark_started(self) -> None:
        """Mark the swarm run as started."""
        self.started_at = datetime.now()

    def mark_completed(self) -> None:
        """Mark the swarm run as completed and calculate metrics."""
        self.completed_at = datetime.now()
        # Aggregate metrics from results
        for result in self.results.values():
            if result.latency_ms:
                self.metrics.total_latency_ms += result.latency_ms
            if result.tokens_used:
                self.metrics.total_tokens_used += result.tokens_used
            if result.reflection_count:
                self.metrics.reflection_iterations += result.reflection_count
        # Count failures from errors
        self.metrics.agents_succeeded = 0
        self.metrics.agents_failed = 0
        self.metrics.agents_timed_out = 0
        for error in self.errors:
            if "timeout" in error.lower():
                self.metrics.agents_timed_out += 1
            else:
                self.metrics.agents_failed += 1
        # Successes are total results minus failures/timeouts (clamped at 0).
        self.metrics.agents_succeeded = max(
            0, len(self.results) - self.metrics.agents_failed - self.metrics.agents_timed_out
        )

    def duration_seconds(self) -> Optional[float]:
        """Return total duration in seconds, or None if not completed."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_summary_dict(self) -> Dict[str, Any]:
        """Return a summary dict for JSON serialization."""
        return {
            "correlation_id": self.correlation_id,
            "goal": self.goal,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds(),
            "agents_run": len(self.results),
            "errors_count": len(self.errors),
            "patches_applied": len(self.applied_patches),
            "metrics": {
                "total_latency_ms": self.metrics.total_latency_ms,
                "total_tokens_used": self.metrics.total_tokens_used,
                "agents_succeeded": self.metrics.agents_succeeded,
                "agents_failed": self.metrics.agents_failed,
                "agents_timed_out": self.metrics.agents_timed_out,
                "reflection_iterations": self.metrics.reflection_iterations,
                "memory_backend": self.metrics.memory_backend,
            },
        }
