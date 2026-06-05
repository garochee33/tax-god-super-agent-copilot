"""Tax God — Settings Endpoint Tests"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_settings_admin(client: AsyncClient, admin_headers: dict):
    res = await client.get("/api/v1/settings", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "sections" in data
    assert "ai" in data["sections"]
    assert "stripe" in data["sections"]


@pytest.mark.asyncio
async def test_get_settings_non_admin(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/settings", headers=auth_headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_get_settings_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/settings")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_update_settings_invalid_key(client: AsyncClient, admin_headers: dict):
    res = await client.put("/api/v1/settings", headers=admin_headers, json={
        "updates": {"NOT_A_REAL_KEY": "value"}
    })
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_update_settings_non_admin(client: AsyncClient, auth_headers: dict):
    res = await client.put("/api/v1/settings", headers=auth_headers, json={
        "updates": {"OPENAI_API_KEY": "sk-new"}
    })
    assert res.status_code == 403
