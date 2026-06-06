"""Tests for /api/v1/accounts CRUD endpoints."""

import pytest
from httpx import AsyncClient

BASE = "/api/v1/accounts"

ACCOUNT_DATA = {"name": "Test Checking", "account_type": "checking", "balance": 1000.0, "currency": "USD"}


@pytest.mark.asyncio
async def test_create_account(client: AsyncClient, auth_headers: dict):
    r = await client.post(BASE, headers=auth_headers, json=ACCOUNT_DATA)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Test Checking"
    assert data["account_type"] == "checking"
    assert data["balance"] == 1000.0
    assert "id" in data


@pytest.mark.asyncio
async def test_list_accounts(client: AsyncClient, auth_headers: dict):
    await client.post(BASE, headers=auth_headers, json=ACCOUNT_DATA)
    r = await client.get(BASE, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert len(data["accounts"]) >= 1


@pytest.mark.asyncio
async def test_get_account(client: AsyncClient, auth_headers: dict):
    create = await client.post(BASE, headers=auth_headers, json=ACCOUNT_DATA)
    account_id = create.json()["id"]
    r = await client.get(f"{BASE}/{account_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["id"] == account_id


@pytest.mark.asyncio
async def test_get_account_not_found(client: AsyncClient, auth_headers: dict):
    r = await client.get(f"{BASE}/nonexistent-id", headers=auth_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_account(client: AsyncClient, auth_headers: dict):
    create = await client.post(BASE, headers=auth_headers, json=ACCOUNT_DATA)
    account_id = create.json()["id"]
    r = await client.patch(f"{BASE}/{account_id}", headers=auth_headers, json={"name": "Renamed"})
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed"


@pytest.mark.asyncio
async def test_delete_account(client: AsyncClient, auth_headers: dict):
    create = await client.post(BASE, headers=auth_headers, json=ACCOUNT_DATA)
    account_id = create.json()["id"]
    r = await client.delete(f"{BASE}/{account_id}", headers=auth_headers)
    assert r.status_code == 204
    r2 = await client.get(f"{BASE}/{account_id}", headers=auth_headers)
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated(client: AsyncClient):
    r = await client.get(BASE)
    assert r.status_code == 401
    r = await client.post(BASE, json=ACCOUNT_DATA)
    assert r.status_code == 401
