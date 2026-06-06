"""Tests for /api/v1/vendors CRUD endpoints."""

import pytest
from httpx import AsyncClient

BASE = "/api/v1/vendors"

VENDOR_DATA = {"name": "Acme Corp", "category": "supplies", "is_1099": True, "total_paid": 750.0}


@pytest.mark.asyncio
async def test_create_vendor(client: AsyncClient, auth_headers: dict):
    r = await client.post(BASE, headers=auth_headers, json=VENDOR_DATA)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Acme Corp"
    assert data["category"] == "supplies"
    assert data["is_1099"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_list_vendors(client: AsyncClient, auth_headers: dict):
    await client.post(BASE, headers=auth_headers, json=VENDOR_DATA)
    r = await client.get(BASE, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert len(data["vendors"]) >= 1


@pytest.mark.asyncio
async def test_list_1099_vendors(client: AsyncClient, auth_headers: dict):
    await client.post(BASE, headers=auth_headers, json=VENDOR_DATA)
    r = await client.get(f"{BASE}/1099", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "vendors" in data
    for v in data["vendors"]:
        assert v["is_1099"] is True
        assert v["total_paid"] >= 600


@pytest.mark.asyncio
async def test_update_vendor(client: AsyncClient, auth_headers: dict):
    create = await client.post(BASE, headers=auth_headers, json=VENDOR_DATA)
    vendor_id = create.json()["id"]
    r = await client.patch(f"{BASE}/{vendor_id}", headers=auth_headers, json={"name": "Renamed"})
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed"


@pytest.mark.asyncio
async def test_update_vendor_not_found(client: AsyncClient, auth_headers: dict):
    r = await client.patch(f"{BASE}/nonexistent-id", headers=auth_headers, json={"name": "X"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_vendor(client: AsyncClient, auth_headers: dict):
    create = await client.post(BASE, headers=auth_headers, json=VENDOR_DATA)
    vendor_id = create.json()["id"]
    r = await client.delete(f"{BASE}/{vendor_id}", headers=auth_headers)
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_delete_vendor_not_found(client: AsyncClient, auth_headers: dict):
    r = await client.delete(f"{BASE}/nonexistent-id", headers=auth_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated(client: AsyncClient):
    r = await client.get(BASE)
    assert r.status_code == 401
    r = await client.post(BASE, json=VENDOR_DATA)
    assert r.status_code == 401
