"""Tax God API - Tax Estimates Endpoints"""

from __future__ import annotations

from datetime import UTC, date, datetime
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DBSession
from app.models.expense import Expense
from app.models.invoice import Invoice
from app.services.tax_calculator import (
    QUARTERLY_DEADLINES,
    calculate_quarterly_estimate,
)

router = APIRouter()


class FilingStatus(str, Enum):
    single = "single"
    married_filing_jointly = "married_filing_jointly"
    married_filing_separately = "married_filing_separately"
    head_of_household = "head_of_household"


class ScenarioRequest(BaseModel):
    income: float
    expenses: float
    filing_status: FilingStatus = FilingStatus.single
    state: str | None = None


@router.get("/quarterly")
async def quarterly_estimate(current_user: CurrentUser, db: DBSession):
    year = datetime.now(UTC).year
    income_result = await db.execute(
        select(func.coalesce(func.sum(Invoice.amount), 0)).where(
            Invoice.owner_id == current_user.id,
            func.extract("year", Invoice.created_at) == year,
        )
    )
    income = income_result.scalar_one()

    expense_result = await db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.owner_id == current_user.id,
            Expense.tax_deductible.is_(True),
            func.extract("year", Expense.date) == year,
        )
    )
    expenses = expense_result.scalar_one()

    try:
        return calculate_quarterly_estimate(income, expenses)
    except KeyError:
        return calculate_quarterly_estimate(income, expenses, "single")


@router.get("/projection")
async def full_year_projection(current_user: CurrentUser, db: DBSession):
    now = datetime.now(UTC)
    year = now.year
    day_of_year = now.timetuple().tm_yday
    fraction = day_of_year / 365

    income_result = await db.execute(
        select(func.coalesce(func.sum(Invoice.amount), 0)).where(
            Invoice.owner_id == current_user.id,
            func.extract("year", Invoice.created_at) == year,
        )
    )
    ytd_income = income_result.scalar_one()

    expense_result = await db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.owner_id == current_user.id,
            Expense.tax_deductible.is_(True),
            func.extract("year", Expense.date) == year,
        )
    )
    ytd_expenses = expense_result.scalar_one()

    projected_income = ytd_income / fraction if fraction > 0 else 0
    projected_expenses = ytd_expenses / fraction if fraction > 0 else 0

    estimate = calculate_quarterly_estimate(projected_income, projected_expenses)
    estimate["projected_income"] = round(projected_income, 2)
    estimate["projected_expenses"] = round(projected_expenses, 2)
    estimate["ytd_income"] = round(ytd_income, 2)
    estimate["ytd_expenses"] = round(ytd_expenses, 2)
    return estimate


@router.post("/scenario")
async def scenario_estimate(body: ScenarioRequest):
    return calculate_quarterly_estimate(body.income, body.expenses, body.filing_status.value, body.state)


@router.get("/deadlines")
async def get_deadlines():
    year = date.today().year
    today = date.today()
    deadlines = []
    for month, day in QUARTERLY_DEADLINES:
        d = date(year, month, day)
        deadlines.append({"date": d.isoformat(), "passed": d <= today})
    return {"year": year, "deadlines": deadlines}
