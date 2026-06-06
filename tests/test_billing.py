"""Tax God — Billing Endpoint Tests"""

from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_subscription_status_authenticated(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/billing/status", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "tier" in data
    assert "status" in data
    assert data["tier"] == "pro"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_subscription_status_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/billing/status")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_checkout_creates_session(client: AsyncClient, auth_headers: dict):
    """Checkout endpoint creates a Stripe session when keys are configured."""
    mock_customer = MagicMock(id="cus_test123")
    mock_session = MagicMock(url="https://checkout.stripe.com/test")
    with patch("stripe.Customer.create", return_value=mock_customer), \
         patch("stripe.checkout.Session.create", return_value=mock_session), \
         patch("app.api.v1.endpoints.billing.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test_fake"
        mock_settings.STRIPE_PRICE_MONTHLY = "price_test_fake"
        res = await client.post("/api/v1/billing/checkout", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["checkout_url"] == "https://checkout.stripe.com/test"


@pytest.mark.asyncio
async def test_checkout_unauthenticated(client: AsyncClient):
    res = await client.post("/api/v1/billing/checkout")
    assert res.status_code == 401
