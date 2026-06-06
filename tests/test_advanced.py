"""Tax God — Advanced Tax Processing Endpoint Tests"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient


def _mock_orchestrator():
    """Create a mock AdvancedTaxOrchestrator."""
    orch = MagicMock()

    # process_advanced_query
    result = MagicMock()
    result.to_dict.return_value = {
        "request_id": "req-001",
        "query": "test query",
        "response": {
            "role": "assistant",
            "content": "Answer here",
            "agent": "oracle",
            "model_used": "gpt-4o-mini",
            "confidence": 0.9,
            "citations": [],
            "cost_usd": 0.003,
            "latency_sec": 1.1,
            "metadata": {},
        },
        "decomposition": None,
        "memory_context": [],
        "validation": None,
        "final_confidence": 0.9,
        "processing_time": 1.5,
        "requires_human_review": False,
        "fallback_used": False,
        "error_message": None,
    }
    orch.process_advanced_query = AsyncMock(return_value=result)

    # _decompose_task
    decomp = MagicMock()
    decomp.execution_plan.value = "direct"
    decomp.task_type.value = "general"
    decomp.complexity = 0.3
    decomp.subtasks = []
    decomp.dependency_graph = {}
    decomp.swarm_size = None
    decomp.agents_needed = None
    decomp.estimated_cost = 0.003
    decomp.estimated_time = 2
    decomp.parallelization_score = 0.0
    orch._decompose_task = AsyncMock(return_value=decomp)

    # _retrieve_context
    orch._retrieve_context = AsyncMock(return_value=[])

    # _validate_response
    validation = MagicMock()
    validation.is_valid = True
    validation.confidence_score = 0.95
    validation.errors = []
    validation.healing_log = []
    validation.requires_human_review = False
    orch._validate_response = AsyncMock(return_value=validation)

    return orch


@pytest.mark.asyncio
async def test_advanced_query_subscribed(client: AsyncClient, auth_headers: dict):
    """SubscribedUser (PRO test_user) can access /query."""
    from app.main import app
    app.state.advanced_orchestrator = _mock_orchestrator()

    res = await client.post("/api/v1/advanced/query", headers=auth_headers, json={
        "query": "How to optimize S-Corp taxes?",
        "client_id": "c1",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["request_id"] == "req-001"
    assert data["final_confidence"] == 0.9


@pytest.mark.asyncio
async def test_advanced_query_unauthenticated(client: AsyncClient):
    res = await client.post("/api/v1/advanced/query", json={"query": "test"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_decompose_task(client: AsyncClient, auth_headers: dict):
    from app.main import app
    app.state.advanced_orchestrator = _mock_orchestrator()

    res = await client.post("/api/v1/advanced/decompose", headers=auth_headers, json={
        "query": "Multi-state tax optimization",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["execution_plan"] == "direct"
    assert data["complexity"] == 0.3


@pytest.mark.asyncio
async def test_memory_retrieval(client: AsyncClient, auth_headers: dict):
    from app.main import app
    app.state.advanced_orchestrator = _mock_orchestrator()

    res = await client.post("/api/v1/advanced/memory", headers=auth_headers, json={
        "query": "Previous S-Corp filings",
    })
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_validate_response(client: AsyncClient, auth_headers: dict):
    from app.main import app
    app.state.advanced_orchestrator = _mock_orchestrator()

    res = await client.post("/api/v1/advanced/validate", headers=auth_headers, json={
        "query": "Check this tax calculation",
        "context": {"task_type": "calculation"},
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True


@pytest.mark.asyncio
async def test_advanced_status(client: AsyncClient, auth_headers: dict):
    from app.main import app
    app.state.advanced_orchestrator = _mock_orchestrator()

    res = await client.get("/api/v1/advanced/status", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["available"] is True


@pytest.mark.asyncio
async def test_advanced_health_admin_only(client: AsyncClient, admin_headers: dict):
    from app.main import app
    app.state.advanced_orchestrator = _mock_orchestrator()

    res = await client.get("/api/v1/advanced/health", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_advanced_health_rejected_for_normal_user(client: AsyncClient, auth_headers: dict):
    from app.main import app
    app.state.advanced_orchestrator = _mock_orchestrator()

    res = await client.get("/api/v1/advanced/health", headers=auth_headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_advanced_query_no_orchestrator(client: AsyncClient, auth_headers: dict):
    """If orchestrator not available, should return 503."""
    from app.main import app
    if hasattr(app.state, "advanced_orchestrator"):
        delattr(app.state, "advanced_orchestrator")

    res = await client.post("/api/v1/advanced/query", headers=auth_headers, json={
        "query": "test",
    })
    assert res.status_code == 503
