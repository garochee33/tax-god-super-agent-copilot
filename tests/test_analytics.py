"""
Tax God — Analytics Endpoint Tests
"""

import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_circuit_breaker_requires_admin(client: AsyncClient, auth_headers: dict):
    """Regular user cannot access circuit breaker."""
    res = await client.get("/api/v1/analytics/governance/circuit-breaker", headers=auth_headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_circuit_breaker_admin(client: AsyncClient, admin_headers: dict):
    res = await client.get("/api/v1/analytics/governance/circuit-breaker", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "tripped_agents" in data


@pytest.mark.asyncio
async def test_kill_switch_requires_admin(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/analytics/governance/kill-switch", headers=auth_headers, json={"engage": True})
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_usage_analytics(client: AsyncClient, auth_headers: dict):
    from app.main import app
    app.state.cost_governor.get_analytics = AsyncMock(return_value={
        "total_queries": 42, "total_cost_usd": 1.23,
    })
    res = await client.get("/api/v1/analytics/usage", headers=auth_headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_roi_calculate(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/analytics/roi/calculate", json={
        "investment_cost": 10000,
        "incremental_revenue": 50000,
    }, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "roi_percent" in data
    assert data["roi_percent"] > 0


@pytest.mark.asyncio
async def test_roi_calculate_missing_fields(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/analytics/roi/calculate", json={
        "investment_cost": 10000,
    }, headers=auth_headers)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_roi_project(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/analytics/roi/project", json={
        "monthly_traffic": 10000,
        "current_conversion_rate": 0.02,
        "target_conversion_rate": 0.04,
        "average_deal_value": 5000,
        "close_rate": 0.3,
        "investment_cost": 15000,
    }, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "roi_percent" in data


@pytest.mark.asyncio
async def test_analytics_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/analytics/usage")
    assert res.status_code == 401
