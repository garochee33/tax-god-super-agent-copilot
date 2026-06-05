"""Tax God — Logs & Knowledge Base Endpoint Tests"""

import pytest
from httpx import AsyncClient


# ─── Activity Logs ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_activity_logs(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/logs/activity", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_activity_logs_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/logs/activity")
    assert res.status_code == 401


# ─── Build Logs ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_build_logs_admin(client: AsyncClient, admin_headers: dict):
    res = await client.get("/api/v1/logs/builds", headers=admin_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_get_build_logs_non_admin(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/logs/builds", headers=auth_headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_create_build_log(client: AsyncClient, admin_headers: dict):
    res = await client.post("/api/v1/logs/builds", headers=admin_headers, json={
        "agent_name": "Gabriel",
        "action": "refactor",
        "commit_sha": "abc1234",
        "detail": "Refactored auth module",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["agent_name"] == "Gabriel"
    assert data["action"] == "refactor"


@pytest.mark.asyncio
async def test_create_build_log_non_admin(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/logs/builds", headers=auth_headers, json={
        "agent_name": "Gabriel", "action": "test",
    })
    assert res.status_code == 403


# ─── Knowledge Base ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_kb_entry(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/logs/kb", headers=auth_headers, json={
        "title": "Tax Deduction Rules",
        "content": "Section 179 allows...",
        "category": "note",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Tax Deduction Rules"
    assert data["category"] == "note"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_kb_entries(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/logs/kb", headers=auth_headers, json={
        "title": "Entry1", "content": "Content1", "category": "doc"
    })
    res = await client.get("/api/v1/logs/kb", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) >= 1


@pytest.mark.asyncio
async def test_get_kb_entry(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/logs/kb", headers=auth_headers, json={
        "title": "Specific Entry", "content": "Details here", "category": "note"
    })
    eid = create.json()["id"]
    res = await client.get(f"/api/v1/logs/kb/{eid}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["title"] == "Specific Entry"


@pytest.mark.asyncio
async def test_get_kb_entry_not_found(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/logs/kb/nonexistent-id", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_kb_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/logs/kb")
    assert res.status_code == 401
