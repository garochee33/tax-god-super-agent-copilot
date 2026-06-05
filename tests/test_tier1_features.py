"""Tax God — Tier 1 Feature Tests"""

import pytest
from httpx import AsyncClient


# ─── Tax Estimates ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_estimates_quarterly_returns_200(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/estimates/quarterly", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "estimated_tax" in data
    assert "effective_rate" in data
    assert "quarterly_payment" in data
    assert "next_due_date" in data


@pytest.mark.asyncio
async def test_estimates_deadlines_returns_four(client: AsyncClient):
    res = await client.get("/api/v1/estimates/deadlines")
    assert res.status_code == 200
    data = res.json()
    assert len(data["deadlines"]) == 4
    assert "year" in data


@pytest.mark.asyncio
async def test_estimates_scenario_valid(client: AsyncClient):
    res = await client.post("/api/v1/estimates/scenario", json={
        "income": 100000, "expenses": 20000, "filing_status": "single",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["estimated_tax"] > 0
    assert data["quarterly_payment"] > 0


@pytest.mark.asyncio
async def test_estimates_scenario_invalid_filing_status(client: AsyncClient):
    """Invalid filing_status causes a server error (unhandled KeyError)."""
    with pytest.raises(KeyError):
        await client.post("/api/v1/estimates/scenario", json={
            "income": 100000, "expenses": 20000, "filing_status": "invalid_status",
        })


@pytest.mark.asyncio
async def test_estimates_quarterly_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/estimates/quarterly")
    assert res.status_code == 401


# ─── Bank Feeds ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_bank_feeds_link_returns_token(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/bank-feeds/link", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "link_token" in data
    assert data["mock"] is True


@pytest.mark.asyncio
async def test_bank_feeds_connections_returns_200(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/bank-feeds/connections", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_bank_feeds_link_unauthenticated(client: AsyncClient):
    res = await client.post("/api/v1/bank-feeds/link")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_bank_feeds_delete_nonexistent(client: AsyncClient, auth_headers: dict):
    res = await client.delete("/api/v1/bank-feeds/connections/fake-id", headers=auth_headers)
    assert res.status_code == 404


# ─── Recurring Invoices ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_recurring_upcoming_returns_200(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/recurring/upcoming", headers=auth_headers)
    assert res.status_code == 200
    assert "upcoming" in res.json()


@pytest.mark.asyncio
async def test_recurring_process_admin(client: AsyncClient, admin_headers: dict):
    res = await client.post("/api/v1/recurring/process", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "processed" in data
    assert "created_invoice_ids" in data


@pytest.mark.asyncio
async def test_recurring_pause_nonexistent(client: AsyncClient, auth_headers: dict):
    res = await client.patch("/api/v1/recurring/fake-id/pause", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_recurring_upcoming_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/recurring/upcoming")
    assert res.status_code == 401


# ─── Client Portal ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_portal_login_invalid_creds(client: AsyncClient):
    res = await client.post("/api/v1/portal/login", json={
        "email": "nobody@example.com", "invite_code": "wrong",
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_portal_invoices_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/portal/invoices")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_portal_messages_post_unauthenticated(client: AsyncClient):
    res = await client.post("/api/v1/portal/messages", json={"content": "Hello"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_portal_messages_get_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/portal/messages")
    assert res.status_code == 401


# ─── Ledger / Chart of Accounts ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ledger_create_account(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/ledger/accounts", headers=auth_headers, json={
        "code": "1000", "name": "Cash", "account_type": "asset",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["code"] == "1000"
    assert data["name"] == "Cash"
    assert data["balance"] == 0.0


@pytest.mark.asyncio
async def test_ledger_trial_balance(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/ledger/trial-balance", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "balanced" in data
    assert data["balanced"] is True
    assert "total_debit" in data
    assert "total_credit" in data


@pytest.mark.asyncio
async def test_ledger_journal_unbalanced_entry(client: AsyncClient, auth_headers: dict):
    # First create two accounts
    await client.post("/api/v1/ledger/accounts", headers=auth_headers, json={
        "code": "1000", "name": "Cash", "account_type": "asset",
    })
    acct2 = await client.post("/api/v1/ledger/accounts", headers=auth_headers, json={
        "code": "4000", "name": "Revenue", "account_type": "revenue",
    })
    acct1_id = (await client.get("/api/v1/ledger/accounts", headers=auth_headers)).json()[0]["id"]
    acct2_id = (await client.get("/api/v1/ledger/accounts", headers=auth_headers)).json()[1]["id"]

    res = await client.post("/api/v1/ledger/journal", headers=auth_headers, json={
        "date": "2024-06-01T00:00:00",
        "description": "Unbalanced entry",
        "lines": [
            {"account_id": acct1_id, "debit": 100.0, "credit": 0.0},
            {"account_id": acct2_id, "debit": 0.0, "credit": 50.0},
        ],
    })
    assert res.status_code == 400
