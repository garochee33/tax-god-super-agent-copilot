"""
Tax God — Chat/AI Endpoint Tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_query_requires_auth(client: AsyncClient):
    res = await client.post("/api/v1/chat/query", json={"query": "What is Section 199A?"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_chat_query_success(client: AsyncClient, auth_headers: dict):
    # Mock the orchestrator response
    from app.main import app
    mock_msg = MagicMock()
    mock_msg.content = "Section 199A provides a 20% deduction for qualified business income."
    mock_msg.agent = None
    mock_msg.model_used = "gpt-4o-mini"
    mock_msg.confidence = 0.92
    mock_msg.cost_usd = 0.003
    mock_msg.citations = []
    mock_msg.metadata = {"conversation_id": "conv-123", "confidence_level": "high"}
    app.state.ai_orchestrator.query = AsyncMock(return_value=mock_msg)

    res = await client.post("/api/v1/chat/query", json={
        "query": "What is Section 199A?",
    }, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "199A" in data["content"]
    assert data["model_used"] == "gpt-4o-mini"
    assert data["confidence"] == 0.92


@pytest.mark.asyncio
async def test_chat_query_empty(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/chat/query", json={"query": ""}, headers=auth_headers)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_chat_god_mode_unavailable(client: AsyncClient, auth_headers: dict):
    from app.main import app
    # Ensure advanced_orchestrator is not set
    if hasattr(app.state, "advanced_orchestrator"):
        delattr(app.state, "advanced_orchestrator")

    res = await client.post("/api/v1/chat/query", json={
        "query": "Complex multi-state tax scenario",
        "use_god_mode": True,
    }, headers=auth_headers)
    assert res.status_code == 503


@pytest.mark.asyncio
async def test_citation_search_requires_auth(client: AsyncClient):
    res = await client.post("/api/v1/chat/citations/search", json={"query": "199A"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_citation_search(client: AsyncClient, auth_headers: dict):
    from app.main import app
    mock_result = MagicMock()
    mock_result.query = "qualified business income"
    mock_result.total_found = 1
    mock_result.search_time_ms = 12.5
    mock_citation = MagicMock()
    mock_citation.reference = "IRC § 199A"
    mock_citation.title = "Qualified Business Income Deduction"
    mock_citation.summary = "Provides 20% deduction"
    mock_citation.citation_type = MagicMock(value="irc")
    mock_citation.year = 2017
    mock_citation.relevance_score = 0.95
    mock_citation.url = None
    mock_result.citations = [mock_citation]
    app.state.citation_engine.search = MagicMock(return_value=mock_result)

    res = await client.post("/api/v1/chat/citations/search", json={
        "query": "qualified business income",
    }, headers=auth_headers)
    assert res.status_code == 200
