"""Tests for /api/v1/profile endpoints."""

import pytest
from httpx import AsyncClient

BASE = "/api/v1/profile"


@pytest.mark.asyncio
async def test_get_profile_unauthenticated(client: AsyncClient):
    r = await client.get(BASE)
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_profile(client: AsyncClient, auth_headers: dict):
    r = await client.get(BASE, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert "email" in data
    assert "role" in data


@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient, auth_headers: dict):
    r = await client.patch(BASE, headers=auth_headers, json={"full_name": "Updated Name"})
    assert r.status_code == 200
    assert r.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_profile_unauthenticated(client: AsyncClient):
    r = await client.patch(BASE, json={"full_name": "Hacker"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient, auth_headers: dict):
    r = await client.post(
        f"{BASE}/password",
        headers=auth_headers,
        json={"current_password": "TestPass123!", "new_password": "newpassword123"},
    )
    assert r.status_code == 200
    assert r.json()["message"] == "Password updated successfully"


@pytest.mark.asyncio
async def test_change_password_wrong_current(client: AsyncClient, auth_headers: dict):
    r = await client.post(
        f"{BASE}/password",
        headers=auth_headers,
        json={"current_password": "wrongpassword", "new_password": "newpassword123"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_change_password_too_short(client: AsyncClient, auth_headers: dict):
    r = await client.post(
        f"{BASE}/password",
        headers=auth_headers,
        json={"current_password": "TestPass123!", "new_password": "short"},
    )
    assert r.status_code == 422
