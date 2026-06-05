"""Tax God API - Multi-Year Tax Planning Endpoints"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentUser, DBSession
from app.services.tax_planner import (
    bracket_optimizer,
    multi_year_forecast,
    project_annual_tax,
    retirement_contribution_impact,
)

router = APIRouter()


class OptimizeRequest(BaseModel):
    income: float
    filing_status: str = "single"


class RetirementImpactRequest(BaseModel):
    income: float
    contribution: float
    filing_status: str = "single"


@router.get("/projection")
async def get_projection(current_user: CurrentUser, db: DBSession, filing_status: str = "single"):
    return await project_annual_tax(db, current_user.id, filing_status)


@router.get("/forecast")
async def get_forecast(
    current_user: CurrentUser, db: DBSession, years: int = 3, growth_rate: float = 0.05
):
    return await multi_year_forecast(db, current_user.id, years, growth_rate)


@router.post("/optimize")
async def optimize_bracket(body: OptimizeRequest):
    return bracket_optimizer(body.income, body.filing_status)


@router.post("/retirement-impact")
async def get_retirement_impact(body: RetirementImpactRequest):
    return retirement_contribution_impact(body.income, body.contribution, body.filing_status)
