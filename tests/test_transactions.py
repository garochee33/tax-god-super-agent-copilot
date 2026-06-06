"""Tests for /api/v1/transactions endpoints."""

import pytest
from httpx import AsyncClient

BASE = "/api/v1/transactions"

TXN_DATA = {
    "account_id": "test-account-1",
    "date": "2026-01-15T00:00:00",
    "description": "Office supplies",
    "amount": -49.99,
    "category": "office",
    "source": "manual",
}


@pytest.mark.asyncio
async def test_create_transaction(client: AsyncClient, auth_headers: dict):
    r = await client.post(BASE, headers=auth_headers, json=TXN_DATA)
    assert r.status_code == 201
    data = r.json()
    assert data["description"] == "Office supplies"
    assert data["amount"] == -49.99
    assert "id" in data


@pytest.mark.asyncio
async def test_list_transactions(client: AsyncClient, auth_headers: dict):
    await client.post(BASE, headers=auth_headers, json=TXN_DATA)
    r = await client.get(BASE, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert len(data["transactions"]) >= 1


@pytest.mark.asyncio
async def test_delete_transaction(client: AsyncClient, auth_headers: dict):
    create = await client.post(BASE, headers=auth_headers, json=TXN_DATA)
    txn_id = create.json()["id"]
    r = await client.delete(f"{BASE}/{txn_id}", headers=auth_headers)
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_delete_transaction_not_found(client: AsyncClient, auth_headers: dict):
    r = await client.delete(f"{BASE}/nonexistent-id", headers=auth_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_reconcile_transaction(client: AsyncClient, auth_headers: dict):
    create = await client.post(BASE, headers=auth_headers, json=TXN_DATA)
    txn_id = create.json()["id"]
    r = await client.patch(f"{BASE}/{txn_id}/reconcile", headers=auth_headers, json={})
    assert r.status_code == 200
    assert r.json()["reconciled"] is True


@pytest.mark.asyncio
async def test_reconcile_not_found(client: AsyncClient, auth_headers: dict):
    r = await client.patch(f"{BASE}/nonexistent-id/reconcile", headers=auth_headers, json={})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_import_csv(client: AsyncClient, auth_headers: dict):
    csv_text = "date,description,amount\n2026-01-01,Rent,-1200\n2026-01-02,Coffee,-5.50"
    r = await client.post(
        f"{BASE}/import-csv",
        headers=auth_headers,
        json={"account_id": "test-account", "csv_text": csv_text},
    )
    assert r.status_code == 201
    assert r.json()["imported"] == 2


@pytest.mark.asyncio
async def test_unauthenticated(client: AsyncClient):
    r = await client.get(BASE)
    assert r.status_code == 401
    r = await client.post(BASE, json=TXN_DATA)
    assert r.status_code == 401
