"""Tax God API - Transaction Endpoints"""

from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DBSession
from app.models.transaction import Transaction

router = APIRouter()


class TransactionCreate(BaseModel):
    account_id: str | None = None
    date: datetime
    description: str = Field(..., max_length=500)
    amount: float
    category: str | None = Field(default=None, max_length=100)
    source: str = Field(default="manual", max_length=50)


class TransactionResponse(BaseModel):
    id: str
    owner_id: str
    account_id: str
    date: datetime
    description: str
    amount: float
    category: str | None
    reconciled: bool
    expense_id: str | None
    invoice_id: str | None
    source: str
    created_at: datetime


class ReconcileBody(BaseModel):
    expense_id: str | None = None


class CsvImportBody(BaseModel):
    account_id: str
    csv_text: str


@router.get("")
async def list_transactions(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    account_id: str | None = None,
    reconciled: bool | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    query = select(Transaction).where(Transaction.owner_id == current_user.id)
    if account_id:
        query = query.where(Transaction.account_id == account_id)
    if reconciled is not None:
        query = query.where(Transaction.reconciled == reconciled)
    if date_from:
        query = query.where(Transaction.date >= date_from)
    if date_to:
        query = query.where(Transaction.date <= date_to)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    results = (
        (await db.execute(query.order_by(Transaction.date.desc()).offset((page - 1) * per_page).limit(per_page)))
        .scalars()
        .all()
    )
    return {
        "transactions": [TransactionResponse.model_validate(t, from_attributes=True) for t in results],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(body: TransactionCreate, current_user: CurrentUser, db: DBSession):
    txn = Transaction(owner_id=current_user.id, **body.model_dump())
    db.add(txn)
    await db.commit()
    await db.refresh(txn)
    return TransactionResponse.model_validate(txn, from_attributes=True)


@router.post("/import-csv", status_code=status.HTTP_201_CREATED)
async def import_csv(body: CsvImportBody, current_user: CurrentUser, db: DBSession):
    reader = csv.DictReader(io.StringIO(body.csv_text))
    created = []
    for row in reader:
        txn = Transaction(
            owner_id=current_user.id,
            account_id=body.account_id,
            date=datetime.fromisoformat(row["date"]),
            description=row["description"],
            amount=float(row["amount"]),
            source="csv_import",
        )
        db.add(txn)
        created.append(txn)
    await db.commit()
    for t in created:
        await db.refresh(t)
    return {"imported": len(created)}


@router.patch("/{txn_id}/reconcile", response_model=TransactionResponse)
async def reconcile_transaction(txn_id: str, body: ReconcileBody, current_user: CurrentUser, db: DBSession):
    result = await db.execute(
        select(Transaction).where(Transaction.id == txn_id, Transaction.owner_id == current_user.id)
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    txn.reconciled = True
    if body.expense_id:
        txn.expense_id = body.expense_id
    await db.commit()
    await db.refresh(txn)
    return TransactionResponse.model_validate(txn, from_attributes=True)


@router.delete("/{txn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(txn_id: str, current_user: CurrentUser, db: DBSession):
    result = await db.execute(
        select(Transaction).where(Transaction.id == txn_id, Transaction.owner_id == current_user.id)
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    await db.delete(txn)
    await db.commit()
