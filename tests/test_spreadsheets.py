"""Tax God — Spreadsheets CRUD Endpoint Tests"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_spreadsheet(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/spreadsheets", headers=auth_headers, json={
        "name": "Q4 Expenses",
        "sheet_type": "expenses",
        "data": '{"rows": []}',
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Q4 Expenses"
    assert data["sheet_type"] == "expenses"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_spreadsheets(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/spreadsheets", headers=auth_headers, json={
        "name": "Sheet1", "sheet_type": "general",
    })
    res = await client.get("/api/v1/spreadsheets", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert len(data["spreadsheets"]) >= 1


@pytest.mark.asyncio
async def test_get_spreadsheet(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/spreadsheets", headers=auth_headers, json={
        "name": "GetMe", "sheet_type": "income",
    })
    sid = create.json()["id"]
    res = await client.get(f"/api/v1/spreadsheets/{sid}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "GetMe"


@pytest.mark.asyncio
async def test_get_spreadsheet_not_found(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/spreadsheets/nonexistent-id", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_update_spreadsheet(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/spreadsheets", headers=auth_headers, json={
        "name": "Old", "sheet_type": "general",
    })
    sid = create.json()["id"]
    res = await client.patch(f"/api/v1/spreadsheets/{sid}", headers=auth_headers, json={
        "name": "Updated Sheet",
    })
    assert res.status_code == 200
    assert res.json()["name"] == "Updated Sheet"


@pytest.mark.asyncio
async def test_delete_spreadsheet(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/spreadsheets", headers=auth_headers, json={
        "name": "DeleteMe", "sheet_type": "temp",
    })
    sid = create.json()["id"]
    res = await client.delete(f"/api/v1/spreadsheets/{sid}", headers=auth_headers)
    assert res.status_code == 204
    res = await client.get(f"/api/v1/spreadsheets/{sid}", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_spreadsheets_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/spreadsheets")
    assert res.status_code == 401
