"""
Circuit Breaker (Trinity GEM port).

Per-"agent" (e.g. quickbooks, research API) circuit: closed → open on high
error rate, then half-open for probes. Protects against cascading failures.

States:
  - closed: normal; calls allowed
  - open: tripped; calls blocked until pause_duration_ms elapses
  - half-open: probe mode; limited calls allowed to test recovery
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerConfig:
    """Configuration for the circuit breaker."""
    error_threshold_percent: float = 50.0
    window_sec: float = 300.0  # 5 min
    pause_duration_sec: float = 300.0  # 5 min
    min_calls_before_trip: int = 4
    half_open_max_probes: int = 2


@dataclass
class CircuitState:
    """State for one agent's circuit."""
    agent_id: str
    state: str  # "closed" | "open" | "half-open"
    total_calls: int = 0
    total_failures: int = 0
    window_calls: int = 0
    window_failures: int = 0
    window_start: float = field(default_factory=time.monotonic)
    opened_at: float | None = None
    closes_at: float | None = None
    half_open_successes: int = 0
    half_open_probes: int = 0
    last_failure: str | None = None
    last_failure_time: float | None = None
    trip_count: int = 0


@dataclass
class CanExecuteResult:
    """Result of can_execute check."""
    allowed: bool
    state: str
    reason: str | None = None


class CircuitBreaker:
    """
    Trinity-style circuit breaker. Use one agent_id per external dependency
    (e.g. "quickbooks", "research_api").
    """

    def __init__(self, config: CircuitBreakerConfig | None = None):
        self._config = config or CircuitBreakerConfig()
        self._circuits: dict[str, CircuitState] = {}
        self._overrides: dict[str, CircuitBreakerConfig] = {}
        self._on_trip: Callable[[str, str], None] | None = None

    def set_on_trip(self, cb: Callable[[str, str], None] | None) -> None:
        """Set callback when a circuit trips (agent_id, 'open')."""
        self._on_trip = cb

    def _get_config(self, agent_id: str) -> CircuitBreakerConfig:
        over = self._overrides.get(agent_id)
        if over:
            c = CircuitBreakerConfig()
            for k, v in vars(self._config).items():
                setattr(c, k, getattr(over, k, v))
            return c
        return self._config

    def _get_or_create(self, agent_id: str) -> CircuitState:
        if agent_id not in self._circuits:
            self._circuits[agent_id] = CircuitState(agent_id=agent_id, state="closed")
        return self._circuits[agent_id]

    def _reset_window(self, circuit: CircuitState) -> None:
        circuit.window_calls = 0
        circuit.window_failures = 0
        circuit.window_start = time.monotonic()

    def _check_window(self, circuit: CircuitState) -> None:
        cfg = self._get_config(circuit.agent_id)
        if time.monotonic() - circuit.window_start > cfg.window_sec:
            self._reset_window(circuit)

    def can_execute(self, agent_id: str) -> CanExecuteResult:
        """
        Check if a call is allowed. Call before invoking the external service.
        """
        circuit = self._get_or_create(agent_id)
        cfg = self._get_config(agent_id)
        now = time.monotonic()

        if circuit.state == "closed":
            return CanExecuteResult(allowed=True, state="closed")

        if circuit.state == "open":
            if circuit.closes_at is not None and now >= circuit.closes_at:
                circuit.state = "half-open"
                circuit.half_open_successes = 0
                circuit.half_open_probes = 0
                logger.info('CircuitBreaker agent "%s" → half-open (probe)', agent_id)
                return CanExecuteResult(allowed=True, state="half-open")
            remaining = int(circuit.closes_at - now) if circuit.closes_at else 0
            return CanExecuteResult(
                allowed=False,
                state="open",
                reason=f'Agent "{agent_id}" is paused due to high error rate ({remaining}s remaining)',
            )

        # half-open
        if circuit.half_open_probes >= cfg.half_open_max_probes:
            return CanExecuteResult(
                allowed=False,
                state="half-open",
                reason=f'Agent "{agent_id}" in probe mode — max probes reached',
            )
        circuit.half_open_probes += 1
        return CanExecuteResult(allowed=True, state="half-open")

    def record_success(self, agent_id: str) -> None:
        """Call after a successful request."""
        circuit = self._get_or_create(agent_id)
        cfg = self._get_config(agent_id)
        self._check_window(circuit)
        circuit.total_calls += 1
        circuit.window_calls += 1

        if circuit.state == "half-open":
            circuit.half_open_successes += 1
            if circuit.half_open_successes >= cfg.half_open_max_probes:
                circuit.state = "closed"
                circuit.opened_at = None
                circuit.closes_at = None
                self._reset_window(circuit)
                logger.info('CircuitBreaker agent "%s" recovered → closed', agent_id)

    def record_failure(
        self,
        agent_id: str,
        error: str | None = None,
        *,
        is_rate_limit: bool = False,
    ) -> None:
        """
        Call after a failed request. If is_rate_limit=True (e.g. 429),
        the failure does not count toward tripping the circuit.
        """
        circuit = self._get_or_create(agent_id)
        cfg = self._get_config(agent_id)
        self._check_window(circuit)
        circuit.total_calls += 1
        circuit.total_failures += 1
        circuit.window_calls += 1
        if not is_rate_limit:
            circuit.window_failures += 1
        circuit.last_failure = error or "Unknown error"
        circuit.last_failure_time = time.monotonic()

        if circuit.state == "half-open":
            self._trip(circuit)
            return

        if circuit.state == "closed" and circuit.window_calls >= cfg.min_calls_before_trip:
            rate = (circuit.window_failures / circuit.window_calls) * 100
            if rate >= cfg.error_threshold_percent:
                self._trip(circuit)

    def _trip(self, circuit: CircuitState) -> None:
        cfg = self._get_config(circuit.agent_id)
        now = time.monotonic()
        circuit.state = "open"
        circuit.opened_at = now
        circuit.closes_at = now + cfg.pause_duration_sec
        circuit.trip_count += 1
        self._reset_window(circuit)
        duration_min = round(cfg.pause_duration_sec / 60)
        logger.warning(
            'CircuitBreaker agent "%s" TRIPPED (trip #%d) → paused %s min. Last: %s',
            circuit.agent_id,
            circuit.trip_count,
            duration_min,
            circuit.last_failure,
        )
        if self._on_trip:
            try:
                self._on_trip(circuit.agent_id, "open")
            except Exception:
                pass

    def reset_agent(self, agent_id: str) -> bool:
        """Manually reset a circuit to closed."""
        circuit = self._circuits.get(agent_id)
        if not circuit:
            return False
        circuit.state = "closed"
        circuit.opened_at = None
        circuit.closes_at = None
        circuit.half_open_successes = 0
        circuit.half_open_probes = 0
        self._reset_window(circuit)
        logger.info('CircuitBreaker agent "%s" manually reset → closed', agent_id)
        return True

    def reset_all(self) -> None:
        """Reset all circuits."""
        for agent_id in list(self._circuits):
            self.reset_agent(agent_id)

    def _peek_state(self, agent_id: str) -> str:
        """Return the current state string for *agent_id* without side effects."""
        circuit = self._circuits.get(agent_id)
        if circuit is None:
            return "closed"
        if circuit.state != "open":
            return circuit.state
        if circuit.closes_at is not None and time.monotonic() >= circuit.closes_at:
            return "half-open"
        return "open"

    def get_status(self) -> dict[str, Any]:
        """Return status for all agents (config, agents, tripped, healthy)."""
        tripped: list[str] = []
        healthy: list[str] = []
        agents: dict[str, dict[str, Any]] = {}
        for aid, circuit in self._circuits.items():
            current_state = self._peek_state(aid)
            agents[aid] = {
                "agent_id": circuit.agent_id,
                "state": current_state,
                "total_calls": circuit.total_calls,
                "total_failures": circuit.total_failures,
                "window_calls": circuit.window_calls,
                "window_failures": circuit.window_failures,
                "trip_count": circuit.trip_count,
                "last_failure": circuit.last_failure,
            }
            if current_state == "open":
                tripped.append(aid)
            else:
                healthy.append(aid)
        return {
            "config": {
                "error_threshold_percent": self._config.error_threshold_percent,
                "window_sec": self._config.window_sec,
                "pause_duration_sec": self._config.pause_duration_sec,
                "min_calls_before_trip": self._config.min_calls_before_trip,
                "half_open_max_probes": self._config.half_open_max_probes,
            },
            "agents": agents,
            "tripped_agents": tripped,
            "healthy_agents": healthy,
        }


# Default agent id for QuickBooks
QB_AGENT_ID = "quickbooks"
