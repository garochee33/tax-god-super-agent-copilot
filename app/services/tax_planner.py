"""Tax God - Multi-Year Tax Planning Service"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense
from app.models.invoice import Invoice
from app.services.tax_calculator import (
    BRACKETS_2024,
    SE_NET_FACTOR,
    SE_TAX_RATE,
    STANDARD_DEDUCTION_2024,
    _compute_federal_tax,
)


def _get_bracket_info(taxable_income: float, filing_status: str) -> dict:
    brackets = BRACKETS_2024[filing_status]
    prev = 0.0
    for ceiling, rate in brackets:
        if taxable_income <= ceiling:
            return {
                "bracket_rate": rate,
                "bracket_floor": prev,
                "bracket_ceiling": ceiling,
                "room_in_bracket": round(ceiling - taxable_income, 2),
            }
        prev = ceiling
    last_rate = brackets[-1][1]
    return {"bracket_rate": last_rate, "bracket_floor": prev, "bracket_ceiling": float("inf"), "room_in_bracket": 0}


async def project_annual_tax(db: AsyncSession, user_id: str, filing_status: str = "single") -> dict:
    now = datetime.now(UTC)
    year = now.year
    day_of_year = now.timetuple().tm_yday
    fraction = day_of_year / 365

    income_result = await db.execute(
        select(func.coalesce(func.sum(Invoice.amount), 0)).where(
            Invoice.owner_id == user_id,
            func.extract("year", Invoice.created_at) == year,
        )
    )
    ytd_income = float(income_result.scalar_one())

    expense_result = await db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.owner_id == user_id,
            Expense.tax_deductible.is_(True),
            func.extract("year", Expense.date) == year,
        )
    )
    ytd_expenses = float(expense_result.scalar_one())

    projected_income = ytd_income / fraction if fraction > 0 else 0
    projected_expenses = ytd_expenses / fraction if fraction > 0 else 0
    net = projected_income - projected_expenses

    se_base = net * SE_NET_FACTOR
    se_tax = max(se_base * SE_TAX_RATE, 0)
    deduction = STANDARD_DEDUCTION_2024.get(filing_status, 14600)
    taxable = max(net - deduction - se_tax / 2, 0)

    federal_tax = _compute_federal_tax(taxable, filing_status)
    total_liability = federal_tax + se_tax
    effective_rate = (total_liability / projected_income * 100) if projected_income > 0 else 0
    bracket_info = _get_bracket_info(taxable, filing_status)

    return {
        "year": year,
        "ytd_income": round(ytd_income, 2),
        "ytd_expenses": round(ytd_expenses, 2),
        "projected_income": round(projected_income, 2),
        "projected_expenses": round(projected_expenses, 2),
        "taxable_income": round(taxable, 2),
        "projected_liability": round(total_liability, 2),
        "effective_rate": round(effective_rate, 2),
        "marginal_rate": bracket_info["bracket_rate"],
        "bracket_ceiling": bracket_info["bracket_ceiling"],
        "room_in_bracket": bracket_info["room_in_bracket"],
    }


async def multi_year_forecast(db: AsyncSession, user_id: str, years: int = 3, growth_rate: float = 0.05) -> list[dict]:
    base = await project_annual_tax(db, user_id)
    base_income = base["projected_income"]
    base_expenses = base["projected_expenses"]
    current_year = base["year"]
    results = []

    for i in range(1, years + 1):
        factor = (1 + growth_rate) ** i
        income = base_income * factor
        expenses = base_expenses * factor
        net = income - expenses
        se_base = net * SE_NET_FACTOR
        se_tax = max(se_base * SE_TAX_RATE, 0)
        deduction = STANDARD_DEDUCTION_2024.get("single", 14600)
        taxable = max(net - deduction - se_tax / 2, 0)
        federal_tax = _compute_federal_tax(taxable, "single")
        total = federal_tax + se_tax
        effective = (total / income * 100) if income > 0 else 0
        bracket_info = _get_bracket_info(taxable, "single")
        results.append(
            {
                "year": current_year + i,
                "projected_income": round(income, 2),
                "projected_expenses": round(expenses, 2),
                "taxable_income": round(taxable, 2),
                "projected_liability": round(total, 2),
                "effective_rate": round(effective, 2),
                "marginal_rate": bracket_info["bracket_rate"],
            }
        )
    return results


def bracket_optimizer(income: float, filing_status: str = "single") -> dict:
    deduction = STANDARD_DEDUCTION_2024.get(filing_status, 14600)
    net = income
    se_base = net * SE_NET_FACTOR
    se_tax = max(se_base * SE_TAX_RATE, 0)
    taxable = max(net - deduction - se_tax / 2, 0)

    bracket_info = _get_bracket_info(taxable, filing_status)
    strategies = []
    if bracket_info["room_in_bracket"] < 10000:
        strategies.append("Consider deferring income to next year to stay in current bracket")
    strategies.append("Maximize retirement contributions (401k: $23,000, IRA: $7,000, SEP: up to $69,000)")
    strategies.append("Accelerate deductible expenses before year-end")
    if taxable > 100000:
        strategies.append("Consider S-Corp election to reduce self-employment tax")

    return {
        "current_taxable_income": round(taxable, 2),
        "current_bracket_rate": bracket_info["bracket_rate"],
        "bracket_ceiling": bracket_info["bracket_ceiling"],
        "room_in_bracket": bracket_info["room_in_bracket"],
        "income_to_reduce_bracket": round(max(taxable - bracket_info["bracket_floor"], 0), 2),
        "strategies": strategies,
    }


def retirement_contribution_impact(income: float, contribution: float, filing_status: str = "single") -> dict:
    deduction = STANDARD_DEDUCTION_2024.get(filing_status, 14600)

    # Without contribution
    net = income
    se_base = net * SE_NET_FACTOR
    se_tax = max(se_base * SE_TAX_RATE, 0)
    taxable_before = max(net - deduction - se_tax / 2, 0)
    tax_before = _compute_federal_tax(taxable_before, filing_status) + se_tax

    # With contribution (reduces taxable income)
    taxable_after = max(taxable_before - contribution, 0)
    tax_after = _compute_federal_tax(taxable_after, filing_status) + se_tax

    savings = tax_before - tax_after
    effective_benefit = (savings / contribution * 100) if contribution > 0 else 0

    return {
        "income": round(income, 2),
        "contribution": round(contribution, 2),
        "tax_without_contribution": round(tax_before, 2),
        "tax_with_contribution": round(tax_after, 2),
        "tax_savings": round(savings, 2),
        "effective_benefit_pct": round(effective_benefit, 2),
        "limits": {
            "401k": 23000,
            "ira": 7000,
            "sep_ira": min(round(income * 0.25, 2), 69000),
        },
    }
