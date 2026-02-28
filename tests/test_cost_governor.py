import asyncio

from app.services.cost_governor import CostGovernor, RoutingPath


def test_estimate_prefers_cache_when_present():
    governor = CostGovernor(redis_client=None)
    asyncio.run(
        governor.cache.set(
        query="What is the standard deduction?",
        result={"content": "Cached response"},
        client_id="c1",
        )
    )

    estimate = asyncio.run(
        governor.estimate(
            query="What is the standard deduction?",
            client_id="c1",
        )
    )

    assert estimate.cache_hit is True
    assert estimate.routing_path == RoutingPath.CACHE.value
    assert estimate.model_name == "cache"


def test_estimate_routes_to_swarm_for_parallel_batch():
    governor = CostGovernor(redis_client=None)
    estimate = asyncio.run(
        governor.estimate(
            query="Validate 100 forms",
            client_id="client_swarm",
            context={"parallelizable_score": 95, "batch_size": 100},
        )
    )

    assert estimate.routing_path == RoutingPath.OPENCLAW_SWARM.value
    assert estimate.estimated_swarm_agents == 100
    assert estimate.model_name == "openclaw_swarm"
    assert estimate.estimated_cost_usd > 0


def test_budget_tracker_reserve_mode_when_near_hard_limit():
    governor = CostGovernor(redis_client=None)
    asyncio.run(governor.budget.record_spend("c2", 191.0))
    mode = asyncio.run(governor.budget.get_budget_mode())
    assert mode == "reserve"
