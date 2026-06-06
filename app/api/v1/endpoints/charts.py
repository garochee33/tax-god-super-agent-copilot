"""Tax God API - Chart Data Endpoints"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter
from sqlalchemy import extract, func, select

from app.api.deps import CurrentUser, DBSession
from app.models.expense import Expense
from app.models.invoice import Invoice

router = APIRouter()


@router.get("/revenue-monthly")
async def revenue_monthly(current_user: CurrentUser, db: DBSession):
    """Last 12 months revenue from paid invoices."""
    now = datetime.now(UTC)
    start = now.replace(day=1) - timedelta(days=365)
    result = await db.execute(
        select(
            extract("year", Invoice.paid_date).label("y"),
            extract("month", Invoice.paid_date).label("m"),
            func.sum(Invoice.amount).label("total"),
        )
        .where(Invoice.owner_id == current_user.id, Invoice.status == "paid", Invoice.paid_date >= start)
        .group_by("y", "m")
        .order_by("y", "m")
    )
    rows = result.all()
    return [{"month": f"{int(r.y)}-{int(r.m):02d}", "amount": round(r.total or 0, 2)} for r in rows]


@router.get("/expenses-by-category")
async def expenses_by_category(current_user: CurrentUser, db: DBSession):
    """Expense totals grouped by category."""
    result = await db.execute(
        select(Expense.category, func.sum(Expense.amount).label("total"))
        .where(Expense.owner_id == current_user.id)
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
    )
    return [{"category": r.category, "total": round(r.total or 0, 2)} for r in result.all()]


@router.get("/cash-flow")
async def cash_flow(current_user: CurrentUser, db: DBSession):
    """Monthly income vs expenses for last 12 months."""
    now = datetime.now(UTC)
    start = now.replace(day=1) - timedelta(days=365)

    inc_result = await db.execute(
        select(
            extract("year", Invoice.paid_date).label("y"),
            extract("month", Invoice.paid_date).label("m"),
            func.sum(Invoice.amount).label("total"),
        )
        .where(Invoice.owner_id == current_user.id, Invoice.status == "paid", Invoice.paid_date >= start)
        .group_by("y", "m")
    )
    income_map = {f"{int(r.y)}-{int(r.m):02d}": round(r.total or 0, 2) for r in inc_result.all()}

    exp_result = await db.execute(
        select(
            extract("year", Expense.date).label("y"),
            extract("month", Expense.date).label("m"),
            func.sum(Expense.amount).label("total"),
        )
        .where(Expense.owner_id == current_user.id, Expense.date >= start)
        .group_by("y", "m")
    )
    expense_map = {f"{int(r.y)}-{int(r.m):02d}": round(r.total or 0, 2) for r in exp_result.all()}

    months = sorted(set(list(income_map.keys()) + list(expense_map.keys())))
    return [
        {
            "month": m,
            "income": income_map.get(m, 0),
            "expenses": expense_map.get(m, 0),
            "net": round(income_map.get(m, 0) - expense_map.get(m, 0), 2),
        }
        for m in months
    ]


@router.get("/income-vs-expenses")
async def income_vs_expenses(current_user: CurrentUser, db: DBSession):
    """YTD income vs expenses comparison."""
    now = datetime.now(UTC)
    ytd_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    inc = await db.execute(
        select(func.sum(Invoice.amount)).where(
            Invoice.owner_id == current_user.id, Invoice.status == "paid", Invoice.paid_date >= ytd_start
        )
    )
    exp = await db.execute(
        select(func.sum(Expense.amount)).where(Expense.owner_id == current_user.id, Expense.date >= ytd_start)
    )
    income = round(inc.scalar_one() or 0, 2)
    expenses = round(exp.scalar_one() or 0, 2)
    return {"income": income, "expenses": expenses, "net": round(income - expenses, 2), "year": now.year}
