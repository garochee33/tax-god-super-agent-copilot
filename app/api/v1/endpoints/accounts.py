"""Tax God API - Account Management Endpoints"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DBSession
from app.models.account import Account

router = APIRouter()


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    account_type: str = Field(..., max_length=50)
    provider: str | None = Field(default=None, max_length=255)
    account_number_last4: str | None = Field(default=None, max_length=4)
    currency: str = Field(default="USD", max_length=10)
    balance: float = 0
    status: str = Field(default="active", max_length=50)
    notes: str | None = None


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    account_type: str | None = Field(default=None, max_length=50)
    provider: str | None = Field(default=None, max_length=255)
    account_number_last4: str | None = Field(default=None, max_length=4)
    currency: str | None = Field(default=None, max_length=10)
    balance: float | None = None
    status: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class AccountResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    account_type: str
    provider: str | None
    account_number_last4: str | None
    currency: str
    balance: float
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class AccountListResponse(BaseModel):
    accounts: list[AccountResponse]
    total: int
    page: int
    per_page: int


@router.get("", response_model=AccountListResponse)
async def list_accounts(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    account_type: str | None = Query(default=None),
):
    query = select(Account).where(Account.owner_id == current_user.id)
    if account_type:
        query = query.where(Account.account_type == account_type)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()
    query = query.order_by(Account.updated_at.desc()).offset((page - 1) * per_page).limit(per_page)
    results = (await db.execute(query)).scalars().all()
    return AccountListResponse(
        accounts=[AccountResponse.model_validate(a, from_attributes=True) for a in results],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(body: AccountCreate, current_user: CurrentUser, db: DBSession):
    account = Account(owner_id=current_user.id, **body.model_dump())
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return AccountResponse.model_validate(account, from_attributes=True)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: str, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(Account).where(Account.id == account_id, Account.owner_id == current_user.id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountResponse.model_validate(account, from_attributes=True)


@router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(account_id: str, body: AccountUpdate, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(Account).where(Account.id == account_id, Account.owner_id == current_user.id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    await db.commit()
    await db.refresh(account)
    return AccountResponse.model_validate(account, from_attributes=True)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(account_id: str, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(Account).where(Account.id == account_id, Account.owner_id == current_user.id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    await db.delete(account)
    await db.commit()
