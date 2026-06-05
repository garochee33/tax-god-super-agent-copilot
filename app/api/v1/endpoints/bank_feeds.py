"""Tax God - Bank Feeds (Plaid-ready) API"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.core.crypto import get_fernet
from app.models.bank_connection import BankConnection
from app.models.transaction import Transaction

router = APIRouter()

PLAID_CONFIGURED = bool(os.environ.get("PLAID_CLIENT_ID"))


class LinkResponse(BaseModel):
    link_token: str
    mock: bool = False


class ExchangeRequest(BaseModel):
    public_token: str = Field(..., min_length=1)
    institution_name: str
    account_name: str
    account_mask: str


class ConnectionOut(BaseModel):
    id: str
    institution_name: str
    account_name: str
    account_mask: str
    last_synced: datetime | None
    status: str
    created_at: datetime


class SyncResult(BaseModel):
    transactions_added: int


@router.post("/link", response_model=LinkResponse)
async def create_link_token(user: CurrentUser):
    """Initiate Plaid Link — returns mock token when Plaid is not configured."""
    if PLAID_CONFIGURED:
        # Production: call Plaid /link/token/create
        return LinkResponse(link_token="real-link-token-placeholder", mock=False)
    return LinkResponse(link_token=f"mock-link-token-{uuid4().hex[:8]}", mock=True)


@router.post("/exchange", response_model=ConnectionOut, status_code=status.HTTP_201_CREATED)
async def exchange_token(body: ExchangeRequest, user: CurrentUser, db: DBSession):
    """Exchange public_token for access_token and store connection."""
    if PLAID_CONFIGURED:
        access_token = "real-access-token-placeholder"
        item_id = "real-item-id-placeholder"
    else:
        access_token = f"mock-access-{uuid4().hex[:12]}"
        item_id = f"mock-item-{uuid4().hex[:8]}"

    encrypted = get_fernet().encrypt(access_token.encode()).decode()
    conn = BankConnection(
        owner_id=user.id,
        institution_name=body.institution_name,
        account_name=body.account_name,
        account_mask=body.account_mask,
        plaid_access_token=encrypted,
        plaid_item_id=item_id,
        status="active",
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)
    return conn


@router.get("/connections", response_model=list[ConnectionOut])
async def list_connections(user: CurrentUser, db: DBSession):
    """List user's connected bank accounts."""
    result = await db.execute(
        select(BankConnection).where(BankConnection.owner_id == user.id)
    )
    return result.scalars().all()


@router.post("/sync/{connection_id}", response_model=SyncResult)
async def sync_transactions(connection_id: str, user: CurrentUser, db: DBSession):
    """Pull latest transactions from Plaid (or mock) into Transaction table."""
    result = await db.execute(
        select(BankConnection).where(
            BankConnection.id == connection_id, BankConnection.owner_id == user.id
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Mock transactions for dev
    mock_txns = [
        {"date": datetime.now(UTC), "description": "Coffee Shop", "amount": -4.50, "category": "Food"},
        {"date": datetime.now(UTC), "description": "Direct Deposit", "amount": 3200.00, "category": "Income"},
    ]

    for t in mock_txns:
        db.add(Transaction(
            owner_id=user.id,
            account_id=conn.id,
            date=t["date"],
            description=t["description"],
            amount=t["amount"],
            category=t["category"],
            source="plaid",
            reconciled=False,
        ))

    conn.last_synced = datetime.now(UTC)
    await db.commit()
    return SyncResult(transactions_added=len(mock_txns))


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(connection_id: str, user: CurrentUser, db: DBSession):
    """Disconnect a bank account."""
    result = await db.execute(
        select(BankConnection).where(
            BankConnection.id == connection_id, BankConnection.owner_id == user.id
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    conn.status = "disconnected"
    await db.commit()
