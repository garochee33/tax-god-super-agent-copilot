"""Tax God — Dev Tracking Endpoint Tests"""

import uuid

import pytest
from httpx import AsyncClient


def _unique_file():
    return f"test/{uuid.uuid4().hex[:8]}.py"


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/dev/agents", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_register_agent_admin(client: AsyncClient, admin_headers: dict):
    res = await client.post("/api/v1/dev/agents", headers=admin_headers, json={
        "name": "TestAgent",
        "capabilities": ["testing", "linting"]
    })
    assert res.status_code == 200
    assert res.json()["status"] == "registered"


@pytest.mark.asyncio
async def test_register_agent_non_admin(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/dev/agents", headers=auth_headers, json={
        "name": "TestAgent",
        "capabilities": ["testing"]
    })
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_lock_file_admin(client: AsyncClient, admin_headers: dict):
    fname = _unique_file()
    res = await client.post("/api/v1/dev/locks", headers=admin_headers, json={
        "file": fname,
        "agent": "TestAgent"
    })
    assert res.status_code == 200
    assert res.json()["locked"] == fname


@pytest.mark.asyncio
async def test_lock_file_conflict(client: AsyncClient, admin_headers: dict):
    fname = _unique_file()
    await client.post("/api/v1/dev/locks", headers=admin_headers, json={
        "file": fname, "agent": "Agent1"
    })
    res = await client.post("/api/v1/dev/locks", headers=admin_headers, json={
        "file": fname, "agent": "Agent2"
    })
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_unlock_file(client: AsyncClient, admin_headers: dict):
    fname = _unique_file()
    await client.post("/api/v1/dev/locks", headers=admin_headers, json={
        "file": fname, "agent": "Agent1"
    })
    res = await client.delete(f"/api/v1/dev/locks/{fname}", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["unlocked"] == fname


@pytest.mark.asyncio
async def test_unlock_file_not_found(client: AsyncClient, admin_headers: dict):
    res = await client.delete(f"/api/v1/dev/locks/{_unique_file()}", headers=admin_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_integrity_snapshot_admin(client: AsyncClient, admin_headers: dict):
    res = await client.post("/api/v1/dev/integrity/snapshot", headers=admin_headers)
    assert res.status_code == 200
    assert "files_hashed" in res.json()


@pytest.mark.asyncio
async def test_integrity_verify(client: AsyncClient, admin_headers: dict, auth_headers: dict):
    await client.post("/api/v1/dev/integrity/snapshot", headers=admin_headers)
    res = await client.get("/api/v1/dev/integrity/verify", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["integrity"] == "ok"


@pytest.mark.asyncio
async def test_integrity_verify_no_snapshot(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/dev/integrity/verify", headers=auth_headers)
    # May return 404 if no snapshot exists (depends on .dev state)
    assert res.status_code in (200, 404)


@pytest.mark.asyncio
async def test_consensus_propose_admin(client: AsyncClient, admin_headers: dict):
    res = await client.post("/api/v1/dev/consensus/propose", headers=admin_headers, json={
        "description": "Add caching layer",
        "files_affected": ["app/core/cache.py"],
        "risk_level": "low"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_consensus_pending(client: AsyncClient, admin_headers: dict, auth_headers: dict):
    await client.post("/api/v1/dev/consensus/propose", headers=admin_headers, json={
        "description": "Refactor database layer",
        "files_affected": ["app/core/database.py"],
        "risk_level": "high"
    })
    res = await client.get("/api/v1/dev/consensus/pending", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert any(p["description"] == "Refactor database layer" for p in data)


@pytest.mark.asyncio
async def test_conflicts(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/dev/conflicts", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "active_locks" in data
    assert "conflicts" in data
