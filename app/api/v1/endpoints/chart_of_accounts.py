"""Tax God API - Chart of Accounts & Journal Entries (Double-Entry Bookkeeping)"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.models.chart_of_accounts import AccountType, ChartOfAccount, JournalEntry, JournalLine

router = APIRouter()


# --- Schemas ---

class AccountCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    account_type: AccountType
    parent_id: str | None = None
    business_id: str | None = None
    description: str | None = None


class AccountResponse(BaseModel):
    id: str
    code: str
    name: str
    account_type: str
    parent_id: str | None
    business_id: str | None
    description: str | None
    balance: float
    created_at: datetime


class JournalLineCreate(BaseModel):
    account_id: str
    debit: float = 0.0
    credit: float = 0.0
    memo: str | None = None

    @model_validator(mode="after")
    def check_debit_credit(self):
        if self.debit > 0 and self.credit > 0:
            raise ValueError("A line must have either debit or credit, not both")
        if self.debit <= 0 and self.credit <= 0:
            raise ValueError("A line must have either debit > 0 or credit > 0")
        return self


class JournalEntryCreate(BaseModel):
    date: datetime
    description: str = Field(..., min_length=1, max_length=500)
    reference: str | None = None
    business_id: str | None = None
    lines: list[JournalLineCreate] = Field(..., min_length=2)


class JournalEntryResponse(BaseModel):
    id: str
    date: datetime
    description: str
    reference: str | None
    lines: list[dict]
    created_at: datetime


# --- Chart of Accounts CRUD ---

@router.get("/accounts", response_model=list[AccountResponse])
async def list_accounts(current_user: CurrentUser, db: DBSession, business_id: str | None = None):
    query = select(ChartOfAccount).where(ChartOfAccount.owner_id == current_user.id)
    if business_id:
        query = query.where(ChartOfAccount.business_id == business_id)
    results = (await db.execute(query.order_by(ChartOfAccount.code))).scalars().all()
    return [AccountResponse.model_validate(a, from_attributes=True) for a in results]


@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(body: AccountCreate, current_user: CurrentUser, db: DBSession):
    account = ChartOfAccount(
        owner_id=current_user.id,
        code=body.code,
        name=body.name,
        account_type=body.account_type.value,
        parent_id=body.parent_id,
        business_id=body.business_id,
        description=body.description,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return AccountResponse.model_validate(account, from_attributes=True)


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(account_id: str, current_user: CurrentUser, db: DBSession):
    account = (
        await db.execute(select(ChartOfAccount).where(ChartOfAccount.id == account_id, ChartOfAccount.owner_id == current_user.id))
    ).scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    await db.delete(account)
    await db.commit()


# --- Journal Entries ---

@router.get("/journal", response_model=list[JournalEntryResponse])
async def list_journal_entries(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    query = (
        select(JournalEntry)
        .where(JournalEntry.owner_id == current_user.id)
        .order_by(JournalEntry.date.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    entries = (await db.execute(query)).scalars().all()
    result = []
    for entry in entries:
        lines = (await db.execute(select(JournalLine).where(JournalLine.entry_id == entry.id))).scalars().all()
        result.append(JournalEntryResponse(
            id=entry.id,
            date=entry.date,
            description=entry.description,
            reference=entry.reference,
            lines=[{"account_id": l.account_id, "debit": l.debit, "credit": l.credit, "memo": l.memo} for l in lines],
            created_at=entry.created_at,
        ))
    return result


@router.post("/journal", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(body: JournalEntryCreate, current_user: CurrentUser, db: DBSession):
    # Validate: debits must equal credits
    total_debit = sum(l.debit for l in body.lines)
    total_credit = sum(l.credit for l in body.lines)
    if abs(total_debit - total_credit) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Debits ({total_debit:.2f}) must equal credits ({total_credit:.2f})",
        )

    entry = JournalEntry(
        owner_id=current_user.id,
        business_id=body.business_id,
        date=body.date,
        description=body.description,
        reference=body.reference,
    )
    db.add(entry)
    await db.flush()

    lines_out = []
    for line in body.lines:
        # Verify account exists and belongs to user
        account = (
            await db.execute(select(ChartOfAccount).where(ChartOfAccount.id == line.account_id, ChartOfAccount.owner_id == current_user.id))
        ).scalar_one_or_none()
        if not account:
            raise HTTPException(status_code=400, detail=f"Account {line.account_id} not found")

        jl = JournalLine(entry_id=entry.id, account_id=line.account_id, debit=line.debit, credit=line.credit, memo=line.memo)
        db.add(jl)

        # Update account balance
        account.balance += line.debit - line.credit
        lines_out.append({"account_id": line.account_id, "debit": line.debit, "credit": line.credit, "memo": line.memo})

    await db.commit()
    await db.refresh(entry)

    return JournalEntryResponse(
        id=entry.id,
        date=entry.date,
        description=entry.description,
        reference=entry.reference,
        lines=lines_out,
        created_at=entry.created_at,
    )


# --- Trial Balance ---

@router.get("/trial-balance")
async def trial_balance(current_user: CurrentUser, db: DBSession, business_id: str | None = None):
    """Get trial balance (all accounts with their debit/credit totals)."""
    query = select(ChartOfAccount).where(ChartOfAccount.owner_id == current_user.id)
    if business_id:
        query = query.where(ChartOfAccount.business_id == business_id)
    accounts = (await db.execute(query.order_by(ChartOfAccount.code))).scalars().all()

    total_debit = 0.0
    total_credit = 0.0
    rows = []
    for a in accounts:
        debit = max(0, a.balance)
        credit = max(0, -a.balance)
        total_debit += debit
        total_credit += credit
        rows.append({"code": a.code, "name": a.name, "type": a.account_type, "debit": debit, "credit": credit})

    return {"accounts": rows, "total_debit": total_debit, "total_credit": total_credit, "balanced": abs(total_debit - total_credit) < 0.01}
