"""
Tax God — Documents Endpoint Tests
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ingest_pdf_requires_auth(client: AsyncClient):
    res = await client.post("/api/v1/documents/ingest")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_ingest_pdf_no_file(client: AsyncClient, auth_headers: dict):
    """Submitting ingest with no file and no body should fail."""
    res = await client.post("/api/v1/documents/ingest", headers=auth_headers)
    # Should return 400 or 422 — no content provided
    assert res.status_code in (400, 422)


@pytest.mark.asyncio
async def test_batch_process_requires_auth(client: AsyncClient):
    res = await client.post("/api/v1/documents/batch-process", json={
        "client_id": "x", "documents": [],
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_batch_process(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/documents/batch-process", json={
        "client_id": "test-client",
        "documents": [{"type": "w2", "year": 2024}],
    }, headers=auth_headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_multi_state_research(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/documents/multi-state-research", json={
        "client_id": "test-client",
        "entity_type": "individual",
        "income_by_state": {"CA": 100000, "NY": 50000},
    }, headers=auth_headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_scenario_analysis(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/documents/scenario-analysis", json={
        "client_id": "test-client",
        "base_income": 150000,
        "base_deductions": 25000,
        "scenarios": [{"adjustment": "max_401k", "value": 23000}],
    }, headers=auth_headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_job_status_not_found(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/documents/jobs/nonexistent-id", headers=auth_headers)
    assert res.status_code in (200, 404)
