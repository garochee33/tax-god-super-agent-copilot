"""Tax God — Projects CRUD Endpoint Tests"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/projects", headers=auth_headers, json={
        "name": "Q4 Tax Filing",
        "status": "active",
        "budget": 5000.0,
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Q4 Tax Filing"
    assert data["budget"] == 5000.0
    assert "id" in data


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/projects", headers=auth_headers, json={"name": "Proj1"})
    res = await client.get("/api/v1/projects", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert len(data["projects"]) >= 1


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/projects", headers=auth_headers, json={"name": "GetMe"})
    pid = create.json()["id"]
    res = await client.get(f"/api/v1/projects/{pid}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "GetMe"


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/projects/nonexistent-id", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/projects", headers=auth_headers, json={"name": "Old"})
    pid = create.json()["id"]
    res = await client.patch(f"/api/v1/projects/{pid}", headers=auth_headers, json={
        "name": "Renamed", "status": "completed",
    })
    assert res.status_code == 200
    assert res.json()["name"] == "Renamed"
    assert res.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/projects", headers=auth_headers, json={"name": "DeleteMe"})
    pid = create.json()["id"]
    res = await client.delete(f"/api/v1/projects/{pid}", headers=auth_headers)
    assert res.status_code == 204
    res = await client.get(f"/api/v1/projects/{pid}", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_projects_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/projects")
    assert res.status_code == 401
