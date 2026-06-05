"""Tax God — CRUD Endpoint Tests (Clients, Businesses, Expenses, Invoices)"""

import pytest
from httpx import AsyncClient


# ─── Clients ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_client(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/clients", headers=auth_headers, json={
        "name": "Acme Corp",
        "email": "acme@example.com",
        "company": "Acme Inc",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Acme Corp"
    assert data["email"] == "acme@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_clients(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/clients", headers=auth_headers, json={"name": "Client1"})
    res = await client.get("/api/v1/clients", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert len(data["clients"]) >= 1


@pytest.mark.asyncio
async def test_get_client(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/clients", headers=auth_headers, json={"name": "GetMe"})
    cid = create.json()["id"]
    res = await client.get(f"/api/v1/clients/{cid}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "GetMe"


@pytest.mark.asyncio
async def test_get_client_not_found(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/clients/nonexistent-id", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_update_client(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/clients", headers=auth_headers, json={"name": "Old Name"})
    cid = create.json()["id"]
    res = await client.patch(f"/api/v1/clients/{cid}", headers=auth_headers, json={"name": "New Name"})
    assert res.status_code == 200
    assert res.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_client(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/clients", headers=auth_headers, json={"name": "DeleteMe"})
    cid = create.json()["id"]
    res = await client.delete(f"/api/v1/clients/{cid}", headers=auth_headers)
    assert res.status_code == 204
    res = await client.get(f"/api/v1/clients/{cid}", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_clients_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/clients")
    assert res.status_code == 401


# ─── Businesses ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_business(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/businesses", headers=auth_headers, json={
        "name": "My LLC",
        "business_type": "llc",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "My LLC"
    assert data["business_type"] == "llc"


@pytest.mark.asyncio
async def test_list_businesses(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/businesses", headers=auth_headers, json={
        "name": "Biz1", "business_type": "sole_prop"
    })
    res = await client.get("/api/v1/businesses", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["total"] >= 1


@pytest.mark.asyncio
async def test_update_business(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/businesses", headers=auth_headers, json={
        "name": "OldBiz", "business_type": "llc"
    })
    bid = create.json()["id"]
    res = await client.patch(f"/api/v1/businesses/{bid}", headers=auth_headers, json={"name": "NewBiz"})
    assert res.status_code == 200
    assert res.json()["name"] == "NewBiz"


@pytest.mark.asyncio
async def test_delete_business(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/businesses", headers=auth_headers, json={
        "name": "GoneBiz", "business_type": "corporation"
    })
    bid = create.json()["id"]
    res = await client.delete(f"/api/v1/businesses/{bid}", headers=auth_headers)
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_delete_business_not_found(client: AsyncClient, auth_headers: dict):
    res = await client.delete("/api/v1/businesses/fake-id", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_businesses_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/businesses")
    assert res.status_code == 401


# ─── Expenses ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_expense(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/expenses", headers=auth_headers, json={
        "date": "2026-01-15T00:00:00Z",
        "vendor": "Office Depot",
        "amount": 125.50,
        "category": "office",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["vendor"] == "Office Depot"
    assert data["amount"] == 125.50


@pytest.mark.asyncio
async def test_list_expenses(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/expenses", headers=auth_headers, json={
        "date": "2026-02-01T00:00:00Z", "vendor": "AWS", "amount": 50.0, "category": "software"
    })
    res = await client.get("/api/v1/expenses", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["total"] >= 1


@pytest.mark.asyncio
async def test_update_expense(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/expenses", headers=auth_headers, json={
        "date": "2026-03-01T00:00:00Z", "vendor": "Uber", "amount": 30.0, "category": "travel"
    })
    eid = create.json()["id"]
    res = await client.patch(f"/api/v1/expenses/{eid}", headers=auth_headers, json={"amount": 45.0})
    assert res.status_code == 200
    assert res.json()["amount"] == 45.0


@pytest.mark.asyncio
async def test_delete_expense(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/expenses", headers=auth_headers, json={
        "date": "2026-04-01T00:00:00Z", "vendor": "Target", "amount": 20.0, "category": "other"
    })
    eid = create.json()["id"]
    res = await client.delete(f"/api/v1/expenses/{eid}", headers=auth_headers)
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_delete_expense_not_found(client: AsyncClient, auth_headers: dict):
    res = await client.delete("/api/v1/expenses/fake-id", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_expenses_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/expenses")
    assert res.status_code == 401


# ─── Invoices ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_invoice(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/invoices", headers=auth_headers, json={
        "invoice_number": "INV-001",
        "amount": 1500.00,
        "status": "draft",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["invoice_number"] == "INV-001"
    assert data["amount"] == 1500.00


@pytest.mark.asyncio
async def test_list_invoices(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/invoices", headers=auth_headers, json={
        "invoice_number": "INV-002", "amount": 200.0
    })
    res = await client.get("/api/v1/invoices", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["total"] >= 1


@pytest.mark.asyncio
async def test_get_invoice(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/invoices", headers=auth_headers, json={
        "invoice_number": "INV-003", "amount": 300.0
    })
    iid = create.json()["id"]
    res = await client.get(f"/api/v1/invoices/{iid}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["invoice_number"] == "INV-003"


@pytest.mark.asyncio
async def test_update_invoice(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/invoices", headers=auth_headers, json={
        "invoice_number": "INV-004", "amount": 400.0
    })
    iid = create.json()["id"]
    res = await client.patch(f"/api/v1/invoices/{iid}", headers=auth_headers, json={"status": "sent"})
    assert res.status_code == 200
    assert res.json()["status"] == "sent"


@pytest.mark.asyncio
async def test_mark_invoice_paid(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/invoices", headers=auth_headers, json={
        "invoice_number": "INV-005", "amount": 500.0
    })
    iid = create.json()["id"]
    res = await client.post(f"/api/v1/invoices/{iid}/mark-paid", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "paid"
    assert res.json()["paid_date"] is not None


@pytest.mark.asyncio
async def test_delete_invoice(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/invoices", headers=auth_headers, json={
        "invoice_number": "INV-006", "amount": 100.0
    })
    iid = create.json()["id"]
    res = await client.delete(f"/api/v1/invoices/{iid}", headers=auth_headers)
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_invoice_not_found(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/invoices/fake-id", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_invoices_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/invoices")
    assert res.status_code == 401
