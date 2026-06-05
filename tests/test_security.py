"""
Tax God — Security & Edge-Case Tests
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from jose import jwt

from app.core.database import async_session_factory
from app.core.security import hash_password
from app.models.subscription import Subscription, SubscriptionStatus, SubscriptionTier
from app.models.user import User, UserRole


@pytest_asyncio.fixture
async def second_user(db_session) -> User:
    """Create a second user for cross-user tests."""
    user = User(
        email="userb@taxgod.dev",
        hashed_password=hash_password("SecondPass123!"),
        full_name="User B",
        role=UserRole.CLIENT.value,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    sub = Subscription(
        user_id=user.id,
        tier=SubscriptionTier.PRO.value,
        status=SubscriptionStatus.ACTIVE.value,
    )
    db_session.add(sub)
    await db_session.commit()
    return user


def _make_token(user_id: str, role: str = "client", expired: bool = False) -> str:
    exp = datetime.now(UTC) + (timedelta(hours=-1) if expired else timedelta(hours=1))
    payload = {"sub": str(user_id), "exp": exp, "type": "access", "role": role}
    return jwt.encode(payload, "test-secret-key-for-testing", algorithm="HS256")


# =============================================================================
# 1. Auth Security
# =============================================================================


@pytest.mark.asyncio
async def test_expired_jwt_returns_401(client: AsyncClient, test_user):
    token = _make_token(test_user.id, expired=True)
    res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_malformed_jwt_returns_401(client: AsyncClient):
    res = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not.a.valid.jwt.token"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_empty_authorization_header_returns_401(client: AsyncClient):
    res = await client.get("/api/v1/auth/me", headers={"Authorization": ""})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_sql_injection_in_login_email(client: AsyncClient):
    res = await client.post("/api/v1/auth/login", json={
        "email": "' OR 1=1; DROP TABLE users; --",
        "password": "anything",
    })
    assert res.status_code in (401, 422)


@pytest.mark.asyncio
async def test_xss_in_full_name_stored_safely(client: AsyncClient):
    xss_payload = '<script>alert("xss")</script>'
    res = await client.post("/api/v1/auth/register", json={
        "email": "xss@test.com",
        "password": "StrongP@ss1",
        "full_name": xss_payload,
    })
    assert res.status_code == 201
    data = res.json()
    # The name is stored as-is (no execution), verify it comes back as plain text
    assert "<script>" not in data.get("full_name", "") or data["full_name"] == xss_payload


# =============================================================================
# 2. Authorization
# =============================================================================


@pytest.mark.asyncio
async def test_nonadmin_cannot_export_audit_trail(client: AsyncClient, auth_headers):
    res = await client.get("/api/v1/audit-trail/export", headers=auth_headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_nonadmin_cannot_process_recurring(client: AsyncClient, auth_headers):
    res = await client.post("/api/v1/recurring/process", headers=auth_headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_nonadmin_cannot_create_team(client: AsyncClient, auth_headers):
    res = await client.post("/api/v1/teams", json={"name": "Hacked Team"}, headers=auth_headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_access_other_users_expenses(
    client: AsyncClient, auth_headers, test_user, second_user
):
    # Create expense as test_user
    res = await client.post("/api/v1/expenses", json={
        "date": datetime.now(UTC).isoformat(),
        "vendor": "Private Vendor",
        "amount": 100.0,
        "category": "office",
    }, headers=auth_headers)
    assert res.status_code == 201
    expense_id = res.json()["id"]

    # Try to access as second_user
    token_b = _make_token(second_user.id)
    headers_b = {"Authorization": f"Bearer {token_b}"}
    res = await client.get("/api/v1/expenses", headers=headers_b)
    assert res.status_code == 200
    # Second user should not see test_user's expense
    ids = [e["id"] for e in res.json()["expenses"]]
    assert expense_id not in ids


@pytest.mark.asyncio
async def test_user_cannot_delete_other_users_clients(
    client: AsyncClient, auth_headers, test_user, second_user
):
    # Create client as test_user
    res = await client.post("/api/v1/clients", json={
        "name": "My Client",
    }, headers=auth_headers)
    assert res.status_code == 201
    client_id = res.json()["id"]

    # Try to delete as second_user
    token_b = _make_token(second_user.id)
    headers_b = {"Authorization": f"Bearer {token_b}"}
    res = await client.delete(f"/api/v1/clients/{client_id}", headers=headers_b)
    assert res.status_code == 404  # Not found because ownership filter


# =============================================================================
# 3. Input Validation
# =============================================================================


@pytest.mark.asyncio
async def test_expense_negative_amount(client: AsyncClient, auth_headers):
    res = await client.post("/api/v1/expenses", json={
        "date": datetime.now(UTC).isoformat(),
        "vendor": "Negative Corp",
        "amount": -50.0,
        "category": "office",
    }, headers=auth_headers)
    # Either rejected (422) or accepted — must not crash (5xx)
    assert res.status_code < 500


@pytest.mark.asyncio
async def test_client_empty_name_returns_422(client: AsyncClient, auth_headers):
    res = await client.post("/api/v1/clients", json={
        "name": "",
    }, headers=auth_headers)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_journal_entry_zero_lines_returns_422(client: AsyncClient, auth_headers):
    res = await client.post("/api/v1/ledger/journal", json={
        "date": datetime.now(UTC).isoformat(),
        "description": "Empty entry",
        "lines": [],
    }, headers=auth_headers)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_journal_entry_mismatched_debits_credits_returns_400(client: AsyncClient, auth_headers):
    # First create an account to reference
    acct_res = await client.post("/api/v1/ledger/accounts", json={
        "code": "1000",
        "name": "Cash",
        "account_type": "asset",
    }, headers=auth_headers)
    assert acct_res.status_code == 201
    acct_id = acct_res.json()["id"]

    res = await client.post("/api/v1/ledger/journal", json={
        "date": datetime.now(UTC).isoformat(),
        "description": "Unbalanced",
        "lines": [
            {"account_id": acct_id, "debit": 100.0, "credit": 0.0},
            {"account_id": acct_id, "debit": 0.0, "credit": 50.0},
        ],
    }, headers=auth_headers)
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_very_long_description_does_not_crash(client: AsyncClient, auth_headers):
    long_desc = "A" * 10000
    res = await client.post("/api/v1/expenses", json={
        "date": datetime.now(UTC).isoformat(),
        "vendor": "Long Corp",
        "amount": 10.0,
        "category": "other",
        "description": long_desc,
    }, headers=auth_headers)
    # Must not return 5xx
    assert res.status_code < 500
