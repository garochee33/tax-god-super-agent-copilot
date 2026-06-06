"""Tax God — Audit (Agent Gabriel) Endpoint Tests"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient


def _mock_audit_report():
    report = MagicMock()
    report.report_id = "rpt-001"
    report.overall_score = 85.0
    report.risk_level = "low"
    report.total_errors_found = 1
    report.total_savings_found = 500.0
    report.ai_summary = "Looks good"
    report.red_flags = []
    report.yellow_flags = []
    report.green_flags = []
    report.flags = []
    return report


def _mock_document():
    doc = MagicMock()
    doc.document_id = "doc-001"
    doc.title = "Tax Memo"
    doc.content = "Memo content here"
    doc.citations = ["IRC §199A"]
    doc.word_count = 50
    doc.confidence = 0.9
    doc.model_used = "gpt-4o-mini"
    doc.disclaimer = "Not legal advice"
    return doc


@pytest.mark.asyncio
async def test_run_audit_as_admin(client: AsyncClient, admin_headers: dict):
    from app.main import app
    app.state.agent_gabriel = MagicMock()
    app.state.agent_gabriel.audit_individual_return = AsyncMock(return_value=_mock_audit_report())

    res = await client.post("/api/v1/audit/run", headers=admin_headers, json={
        "client_id": "client-1",
        "tax_year": 2024,
        "return_data": {"income": 100000, "deductions": 20000},
    })
    assert res.status_code == 200
    data = res.json()
    assert data["report_id"] == "rpt-001"
    assert data["overall_score"] == 85.0


@pytest.mark.asyncio
async def test_run_audit_unauthorized_client_role(client: AsyncClient, auth_headers: dict):
    """CLIENT role should be rejected by PreparerOrAdmin."""
    res = await client.post("/api/v1/audit/run", headers=auth_headers, json={
        "client_id": "c1", "tax_year": 2024, "return_data": {},
    })
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_run_audit_unauthenticated(client: AsyncClient):
    res = await client.post("/api/v1/audit/run", json={
        "client_id": "c1", "tax_year": 2024, "return_data": {},
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_generate_memo_as_admin(client: AsyncClient, admin_headers: dict):
    from app.main import app
    app.state.tax_writer = MagicMock()
    app.state.tax_writer.generate_tax_memo = AsyncMock(return_value=_mock_document())

    res = await client.post("/api/v1/audit/memo", headers=admin_headers, json={
        "subject": "Hobby Loss Rules",
        "facts": "Taxpayer has a side business losing money for 5 years",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["document_id"] == "doc-001"
    assert data["title"] == "Tax Memo"


@pytest.mark.asyncio
async def test_generate_irs_response_as_admin(client: AsyncClient, admin_headers: dict):
    from app.main import app
    app.state.tax_writer = MagicMock()
    app.state.tax_writer.generate_audit_response = AsyncMock(return_value=_mock_document())

    res = await client.post("/api/v1/audit/irs-response", headers=admin_headers, json={
        "notice_type": "CP2000",
        "case_number": "12345",
        "notice_date": "2024-03-15",
        "issues": ["Unreported 1099 income"],
        "taxpayer_name": "John Doe",
        "tax_years": "2023",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["document_id"] == "doc-001"


@pytest.mark.asyncio
async def test_generate_memo_unauthorized_client_role(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/audit/memo", headers=auth_headers, json={
        "subject": "Test", "facts": "Test facts",
    })
    assert res.status_code == 403
