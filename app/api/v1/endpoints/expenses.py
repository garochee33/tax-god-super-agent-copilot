"""Tax God API - Expense Management Endpoints"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DBSession
from app.models.expense import Expense, ExpenseCategory

router = APIRouter()


class ExpenseCreate(BaseModel):
    date: datetime
    vendor: str = Field(..., min_length=1, max_length=255)
    amount: float
    category: ExpenseCategory
    business_id: str | None = None
    description: str | None = None
    receipt_url: str | None = Field(default=None, max_length=500)
    tax_deductible: bool = True
    account_id: str | None = None


class ExpenseUpdate(BaseModel):
    date: datetime | None = None
    vendor: str | None = Field(default=None, max_length=255)
    amount: float | None = None
    category: ExpenseCategory | None = None
    business_id: str | None = None
    description: str | None = None
    receipt_url: str | None = Field(default=None, max_length=500)
    tax_deductible: bool | None = None
    account_id: str | None = None


class ExpenseResponse(BaseModel):
    id: str
    owner_id: str
    business_id: str | None
    date: datetime
    vendor: str
    amount: float
    category: str
    description: str | None
    receipt_url: str | None
    tax_deductible: bool
    account_id: str | None
    created_at: datetime
    updated_at: datetime


class ExpenseListResponse(BaseModel):
    expenses: list[ExpenseResponse]
    total: int
    page: int
    per_page: int


class ExpenseSummaryResponse(BaseModel):
    items: list[dict]
    grand_total: float
    period: str


@router.get("/summary", response_model=ExpenseSummaryResponse)
async def expense_summary(
    current_user: CurrentUser,
    db: DBSession,
    year: int | None = None,
    month: int | None = None,
):
    now = datetime.now(UTC)
    y, m = year or now.year, month or now.month
    query = (
        select(Expense.category, func.sum(Expense.amount))
        .where(
            Expense.owner_id == current_user.id,
            func.extract("year", Expense.date) == y,
            func.extract("month", Expense.date) == m,
        )
        .group_by(Expense.category)
    )
    rows = (await db.execute(query)).all()
    items = [{"category": r[0], "total": r[1] or 0} for r in rows]
    return ExpenseSummaryResponse(items=items, grand_total=sum(i["total"] for i in items), period=f"{y}-{m:02d}")


@router.get("", response_model=ExpenseListResponse)
async def list_expenses(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: ExpenseCategory | None = None,
    business_id: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    query = select(Expense).where(Expense.owner_id == current_user.id)
    if category:
        query = query.where(Expense.category == category.value)
    if business_id:
        query = query.where(Expense.business_id == business_id)
    if date_from:
        query = query.where(Expense.date >= date_from)
    if date_to:
        query = query.where(Expense.date <= date_to)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    results = (
        (await db.execute(query.order_by(Expense.date.desc()).offset((page - 1) * per_page).limit(per_page)))
        .scalars()
        .all()
    )

    return ExpenseListResponse(
        expenses=[ExpenseResponse.model_validate(e, from_attributes=True) for e in results],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(body: ExpenseCreate, current_user: CurrentUser, db: DBSession):
    expense = Expense(
        owner_id=current_user.id,
        business_id=body.business_id,
        date=body.date,
        vendor=body.vendor,
        amount=body.amount,
        category=body.category.value,
        description=body.description,
        receipt_url=body.receipt_url,
        tax_deductible=body.tax_deductible,
        account_id=body.account_id,
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return ExpenseResponse.model_validate(expense, from_attributes=True)


@router.patch("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(expense_id: str, body: ExpenseUpdate, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(Expense).where(Expense.id == expense_id, Expense.owner_id == current_user.id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    updates = body.model_dump(exclude_unset=True)
    if "category" in updates and updates["category"] is not None:
        updates["category"] = updates["category"].value
    for field, value in updates.items():
        setattr(expense, field, value)
    await db.commit()
    await db.refresh(expense)
    return ExpenseResponse.model_validate(expense, from_attributes=True)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: str, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(Expense).where(Expense.id == expense_id, Expense.owner_id == current_user.id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    await db.delete(expense)
    await db.commit()
