"""
Swarm Cost Planner (Trinity GEM port).

Non-linear swarm cost multiplier from worker fanout, delegation depth,
tool usage, and historical variance. Used for multi-agent / swarm tax
workflows and Pantheon cost estimates.

Formula:
  swarm_multiplier = 1
    + fanout_weight   * log2(worker_count + 1)
    + depth_weight    * delegation_depth
    + tool_weight    * expected_tool_calls
    + uncertainty_weight * historical_variance

Clamped to [1.0, 4.0]. Dependency-free.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal


# Weights (match Trinity server/ai/swarm-cost-planner.ts)
FANOUT_WEIGHT = 0.3
DEPTH_WEIGHT = 0.4
TOOL_WEIGHT = 0.1
UNCERTAINTY_WEIGHT = 0.5
MULTIPLIER_MIN = 1.0
MULTIPLIER_MAX = 4.0

# Token budgets and rates (USD per token, ~per 1k)
MODEL_RATES = {
    "premium": 0.03 / 1000,
    "standard": 0.01 / 1000,
    "economy": 0.003 / 1000,
}
PLANNER_TOKENS = 1024
WORKER_TOKENS = 2048
SYNTHESIS_TOKENS = 2048
TOOL_CALL_COST = 0.005
RETRY_RESERVE_PCT = 0.15


@dataclass
class SwarmCostFactors:
    """Factors that influence the swarm cost multiplier."""
    worker_count: int
    delegation_depth: int
    expected_tool_calls: int
    historical_variance: float  # 0.0–1.0


@dataclass
class SwarmCostPlan:
    """Full cost breakdown for a swarm dispatch plan."""
    planner_cost: float
    worker_count: int
    worker_cost_estimate: float
    swarm_multiplier: float
    synthesis_cost: float
    tool_execution_cost: float
    retry_reserve: float
    total_estimate: float
    factors: SwarmCostFactors
    quality_tier: Literal["full", "reduced", "minimal"] = "full"


def _round6(value: float) -> float:
    return round(value, 6)


def calculate_swarm_multiplier(factors: SwarmCostFactors) -> float:
    """
    Compute non-linear swarm cost multiplier.
    Returns multiplier clamped to [1.0, 4.0].
    """
    raw = (
        1.0
        + FANOUT_WEIGHT * math.log2(factors.worker_count + 1)
        + DEPTH_WEIGHT * factors.delegation_depth
        + TOOL_WEIGHT * factors.expected_tool_calls
        + UNCERTAINTY_WEIGHT * factors.historical_variance
    )
    return _round6(min(MULTIPLIER_MAX, max(MULTIPLIER_MIN, raw)))


def create_swarm_cost_plan(
    worker_count: int,
    delegation_depth: int = 1,
    expected_tool_calls: int = 2,
    historical_variance: float = 0.2,
    model_tier: Literal["premium", "standard", "economy"] = "standard",
) -> SwarmCostPlan:
    """
    Build a SwarmCostPlan for budget governance.

    Base costs use model tier token rates. Total = planner + (workers * worker_cost * multiplier)
    + synthesis + tool_execution + retry_reserve.
    """
    worker_count = max(1, worker_count)
    historical_variance = min(1.0, max(0.0, historical_variance))
    rate = MODEL_RATES.get(model_tier, MODEL_RATES["standard"])

    factors = SwarmCostFactors(
        worker_count=worker_count,
        delegation_depth=delegation_depth,
        expected_tool_calls=expected_tool_calls,
        historical_variance=historical_variance,
    )
    swarm_multiplier = calculate_swarm_multiplier(factors)

    planner_cost = _round6(PLANNER_TOKENS * rate)
    worker_cost_estimate = _round6(WORKER_TOKENS * rate)
    synthesis_cost = _round6(SYNTHESIS_TOKENS * rate)
    tool_execution_cost = _round6(expected_tool_calls * worker_count * TOOL_CALL_COST)
    adjusted_worker_cost = _round6(worker_count * worker_cost_estimate * swarm_multiplier)
    retry_reserve = _round6(RETRY_RESERVE_PCT * adjusted_worker_cost)
    total_estimate = round(
        planner_cost + adjusted_worker_cost + synthesis_cost + tool_execution_cost + retry_reserve,
        2,
    )

    return SwarmCostPlan(
        planner_cost=planner_cost,
        worker_count=worker_count,
        worker_cost_estimate=worker_cost_estimate,
        swarm_multiplier=swarm_multiplier,
        synthesis_cost=synthesis_cost,
        tool_execution_cost=tool_execution_cost,
        retry_reserve=retry_reserve,
        total_estimate=total_estimate,
        factors=factors,
        quality_tier="full",
    )
