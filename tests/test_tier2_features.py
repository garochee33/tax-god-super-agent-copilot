"""Tax God — Tier 2 Feature Tests"""

import pytest
from httpx import AsyncClient


# ─── AI Document Generation ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_documents_templates_returns_list(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/documents/templates", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert all("doc_type" in t and "description" in t for t in data)


@pytest.mark.asyncio
async def test_documents_generate_valid_doc_type(client: AsyncClient, auth_headers: dict):
    templates = await client.get("/api/v1/documents/templates", headers=auth_headers)
    doc_type = templates.json()[0]["doc_type"]
    res = await client.post("/api/v1/documents/generate", headers=auth_headers, json={
        "doc_type": doc_type,
    })
    assert res.status_code == 200
    data = res.json()
    assert "content" in data or "doc_type" in data


@pytest.mark.asyncio
async def test_documents_generate_invalid_doc_type(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/documents/generate", headers=auth_headers, json={
        "doc_type": "nonexistent_type_xyz",
    })
    assert res.status_code in (400, 422)


@pytest.mark.asyncio
async def test_documents_generate_batch(client: AsyncClient, auth_headers: dict):
    templates = await client.get("/api/v1/documents/templates", headers=auth_headers)
    doc_type = templates.json()[0]["doc_type"]
    res = await client.post("/api/v1/documents/generate-batch", headers=auth_headers, json={
        "doc_type": doc_type,
    })
    assert res.status_code == 200
    data = res.json()
    assert "documents" in data
    assert "count" in data


@pytest.mark.asyncio
async def test_documents_generate_unauthenticated(client: AsyncClient):
    res = await client.post("/api/v1/documents/generate", json={"doc_type": "engagement_letter"})
    assert res.status_code == 401


# ─── Tax Planning ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tax_planning_projection(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/tax-planning/projection", headers=auth_headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_tax_planning_forecast(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/tax-planning/forecast", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_tax_planning_optimize(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/tax-planning/optimize", headers=auth_headers, json={
        "income": 150000, "filing_status": "single",
    })
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_tax_planning_retirement_impact(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/tax-planning/retirement-impact", headers=auth_headers, json={
        "income": 150000, "contribution": 20000, "filing_status": "single",
    })
    assert res.status_code == 200
    data = res.json()
    assert "tax_savings" in data


@pytest.mark.asyncio
async def test_tax_planning_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/tax-planning/projection")
    assert res.status_code == 401


# ─── Audit Trail ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_audit_trail_events_admin(client: AsyncClient, admin_headers: dict):
    res = await client.get("/api/v1/audit-trail/events", headers=admin_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_audit_trail_compliance(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/audit-trail/compliance", headers=auth_headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_audit_trail_export(client: AsyncClient, admin_headers: dict):
    res = await client.get("/api/v1/audit-trail/export", headers=admin_headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_audit_trail_entity_history(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/audit-trail/events/client/test-id-123", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_audit_trail_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/audit-trail/events")
    assert res.status_code == 401


# ─── Teams ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_teams_create(client: AsyncClient, admin_headers: dict):
    res = await client.post("/api/v1/teams", headers=admin_headers, json={"name": "Alpha Team"})
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Alpha Team"
    assert "id" in data


@pytest.mark.asyncio
async def test_teams_list(client: AsyncClient, admin_headers: dict):
    await client.post("/api/v1/teams", headers=admin_headers, json={"name": "List Team"})
    res = await client.get("/api/v1/teams", headers=admin_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) >= 1


@pytest.mark.asyncio
async def test_teams_workload(client: AsyncClient, admin_headers: dict):
    res = await client.get("/api/v1/teams/workload", headers=admin_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_teams_my_assignments(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/teams/my-assignments", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_teams_assign_client_unauthorized_role(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/teams/assign-client", headers=auth_headers, json={
        "client_id": "nonexistent-client-id",
        "preparer_id": "nonexistent-preparer-id",
    })
    assert res.status_code == 403
