"""Tests for /api/v1/time-entries endpoints."""

import pytest
from httpx import AsyncClient

BASE = "/api/v1/time-entries"

ENTRY_DATA = {
    "description": "Client meeting",
    "hours": 1.5,
    "date": "2026-01-15T00:00:00",
    "billable": True,
    "rate": 150.0,
}


@pytest.mark.asyncio
async def test_create_time_entry(client: AsyncClient, auth_headers: dict):
    r = await client.post(BASE, headers=auth_headers, json=ENTRY_DATA)
    assert r.status_code == 201
    data = r.json()
    assert data["description"] == "Client meeting"
    assert data["hours"] == 1.5
    assert data["billable"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_list_time_entries(client: AsyncClient, auth_headers: dict):
    await client.post(BASE, headers=auth_headers, json=ENTRY_DATA)
    r = await client.get(BASE, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert len(data["time_entries"]) >= 1


@pytest.mark.asyncio
async def test_update_time_entry(client: AsyncClient, auth_headers: dict):
    create = await client.post(BASE, headers=auth_headers, json=ENTRY_DATA)
    entry_id = create.json()["id"]
    r = await client.patch(f"{BASE}/{entry_id}", headers=auth_headers, json={"hours": 2.0})
    assert r.status_code == 200
    assert r.json()["hours"] == 2.0


@pytest.mark.asyncio
async def test_update_time_entry_not_found(client: AsyncClient, auth_headers: dict):
    r = await client.patch(f"{BASE}/nonexistent-id", headers=auth_headers, json={"hours": 1.0})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_time_entry(client: AsyncClient, auth_headers: dict):
    create = await client.post(BASE, headers=auth_headers, json=ENTRY_DATA)
    entry_id = create.json()["id"]
    r = await client.delete(f"{BASE}/{entry_id}", headers=auth_headers)
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_delete_time_entry_not_found(client: AsyncClient, auth_headers: dict):
    r = await client.delete(f"{BASE}/nonexistent-id", headers=auth_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_summary(client: AsyncClient, auth_headers: dict):
    await client.post(BASE, headers=auth_headers, json=ENTRY_DATA)
    r = await client.get(f"{BASE}/summary", headers=auth_headers)
    assert r.status_code == 200
    assert "items" in r.json()


@pytest.mark.asyncio
async def test_unauthenticated(client: AsyncClient):
    r = await client.get(BASE)
    assert r.status_code == 401
    r = await client.post(BASE, json=ENTRY_DATA)
    assert r.status_code == 401
