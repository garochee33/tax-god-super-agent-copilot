"""Tax God — Notes CRUD Endpoint Tests"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_note(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/notes", headers=auth_headers, json={
        "title": "Tax Research",
        "content": "Notes on IRC 199A deduction",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Tax Research"
    assert data["content"] == "Notes on IRC 199A deduction"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_notes(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/notes", headers=auth_headers, json={
        "title": "Note1", "content": "Content1",
    })
    res = await client.get("/api/v1/notes", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert len(data["notes"]) >= 1


@pytest.mark.asyncio
async def test_get_note(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/notes", headers=auth_headers, json={
        "title": "GetMe", "content": "body",
    })
    nid = create.json()["id"]
    res = await client.get(f"/api/v1/notes/{nid}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["title"] == "GetMe"


@pytest.mark.asyncio
async def test_get_note_not_found(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/notes/nonexistent-id", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_update_note(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/notes", headers=auth_headers, json={
        "title": "Old Title", "content": "old",
    })
    nid = create.json()["id"]
    res = await client.patch(f"/api/v1/notes/{nid}", headers=auth_headers, json={"title": "New Title"})
    assert res.status_code == 200
    assert res.json()["title"] == "New Title"


@pytest.mark.asyncio
async def test_delete_note(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/notes", headers=auth_headers, json={
        "title": "DeleteMe", "content": "x",
    })
    nid = create.json()["id"]
    res = await client.delete(f"/api/v1/notes/{nid}", headers=auth_headers)
    assert res.status_code == 204
    res = await client.get(f"/api/v1/notes/{nid}", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_notes_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/notes")
    assert res.status_code == 401
