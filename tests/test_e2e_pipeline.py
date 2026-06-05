"""
Tax God — End-to-End Integration Test
Full pipeline: register → login → create client → chat query → document processing
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_tax_pipeline(client: AsyncClient):
    """
    E2E: register user → login → create client → ask tax question → run scenario analysis.
    """
    from app.main import app

    # 1. Register
    reg = await client.post("/api/v1/auth/register", json={
        "email": "e2e@taxgod.dev",
        "password": "E2eTestP@ss1",
        "full_name": "E2E Tester",
    })
    assert reg.status_code == 201

    # 2. Login
    login = await client.post("/api/v1/auth/login", json={
        "email": "e2e@taxgod.dev",
        "password": "E2eTestP@ss1",
    })
    assert login.status_code == 200
    tokens = login.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 3. Verify identity
    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "e2e@taxgod.dev"

    # 4. Create client
    create = await client.post("/api/v1/clients", json={
        "name": "Acme Corp",
        "email": "cfo@acme.com",
        "company": "Acme Corp",
        "filing_type": "business",
        "status": "active",
    }, headers=headers)
    assert create.status_code == 201
    client_data = create.json()
    assert client_data["name"] == "Acme Corp"
    client_id = client_data["id"]

    # 5. List clients
    listing = await client.get("/api/v1/clients", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    # 6. Chat query (mocked AI)
    mock_msg = MagicMock()
    mock_msg.content = "For Acme Corp (C-Corp), the corporate tax rate is 21% under IRC §11."
    mock_msg.agent = None
    mock_msg.model_used = "gpt-4o-mini"
    mock_msg.confidence = 0.95
    mock_msg.cost_usd = 0.004
    mock_msg.citations = []
    mock_msg.metadata = {"conversation_id": "conv-e2e", "confidence_level": "high"}
    app.state.ai_orchestrator.query = AsyncMock(return_value=mock_msg)

    chat = await client.post("/api/v1/chat/query", json={
        "query": "What is Acme Corp's corporate tax rate?",
        "client_id": client_id,
    }, headers=headers)
    assert chat.status_code == 200
    assert "21%" in chat.json()["content"]

    # 7. Scenario analysis
    scenario = await client.post("/api/v1/documents/scenario-analysis", json={
        "client_id": client_id,
        "base_income": 500000,
        "base_deductions": 50000,
        "scenarios": [
            {"adjustment": "bonus_depreciation", "value": 100000},
            {"adjustment": "r_and_d_credit", "value": 25000},
        ],
    }, headers=headers)
    assert scenario.status_code == 200

    # 8. ROI calculation
    roi = await client.post("/api/v1/analytics/roi/calculate", json={
        "investment_cost": 5000,
        "incremental_revenue": 125000,
    }, headers=headers)
    assert roi.status_code == 200
    assert roi.json()["roi_percent"] > 0

    # 9. Update client
    update = await client.patch(f"/api/v1/clients/{client_id}", json={
        "notes": "Annual filing due March 15. R&D credits pending.",
    }, headers=headers)
    assert update.status_code == 200
    assert "R&D credits" in update.json()["notes"]

    # 10. Refresh token
    refresh = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": tokens["refresh_token"],
    })
    assert refresh.status_code == 200
    assert "access_token" in refresh.json()
