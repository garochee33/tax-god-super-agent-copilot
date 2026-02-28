"""
Tax God API - Analytics, Cost Governance, and ROI Endpoints
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, model_validator

from app.core.config import get_settings
from app.services.roi_engine import compute_roi, project_incremental_revenue

router = APIRouter()


class EstimateRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000)
    client_id: str = ""
    task_type: str = ""
    context: dict = Field(default_factory=dict)


class ROICalculateRequest(BaseModel):
    investment_cost: float = Field(..., gt=0)
    incremental_revenue: float | None = Field(default=None, ge=0)
    incremental_gross_profit: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _validate_sources(self):
        if self.incremental_revenue is None and self.incremental_gross_profit is None:
            raise ValueError("Provide incremental_revenue or incremental_gross_profit")
        return self


class ROIProjectRequest(BaseModel):
    monthly_traffic: float = Field(..., ge=0)
    current_conversion_rate: float = Field(..., ge=0, le=1)
    target_conversion_rate: float = Field(..., ge=0, le=1)
    average_deal_value: float = Field(..., ge=0)
    close_rate: float = Field(..., ge=0, le=1)
    investment_cost: float = Field(..., gt=0)

    @model_validator(mode="after")
    def _validate_rates(self):
        if self.target_conversion_rate < self.current_conversion_rate:
            raise ValueError("target_conversion_rate must be >= current_conversion_rate")
        return self


@router.get("/usage")
async def get_usage_analytics(client_id: Optional[str] = None, request: Request = None):
    """Get usage analytics and cost breakdown."""
    governor = request.app.state.cost_governor
    return await governor.get_analytics(client_id)


@router.get("/budget/{client_id}")
async def get_client_budget(client_id: str, request: Request):
    """Get remaining budget for a specific client."""
    governor = request.app.state.cost_governor
    settings = get_settings()

    month_spend = await governor.budget.get_client_month_spend(client_id)
    daily_spend = await governor.budget.get_daily_spend()

    return {
        "client_id": client_id,
        "month_spend": round(month_spend, 4),
        "month_limit": settings.COST_SOFT_LIMIT_PER_CLIENT_MONTH,
        "month_remaining": round(settings.COST_SOFT_LIMIT_PER_CLIENT_MONTH - month_spend, 4),
        "daily_system_spend": round(daily_spend, 4),
        "daily_system_limit": settings.COST_HARD_LIMIT_DAILY,
        "budget_mode": await governor.budget.get_budget_mode(),
    }


@router.post("/estimate")
async def estimate_query_cost(
    request: Request,
    body: EstimateRequest | None = None,
    query: str = "",
    client_id: str = "",
    task_type: str = "",
):
    """Pre-flight cost estimate for a query (without executing it)."""
    governor = request.app.state.cost_governor
    if body is None:
        if not query.strip():
            raise HTTPException(status_code=400, detail="query is required")
        effective = EstimateRequest(
            query=query,
            client_id=client_id,
            task_type=task_type,
            context={},
        )
    else:
        effective = body

    estimate = await governor.estimate(
        query=effective.query,
        client_id=effective.client_id,
        task_type=effective.task_type,
        context=effective.context,
    )

    return {
        "model": estimate.model_name,
        "tier": estimate.model_tier.value,
        "routing_path": estimate.routing_path,
        "estimated_swarm_agents": estimate.estimated_swarm_agents,
        "estimated_cost_usd": estimate.estimated_cost_usd,
        "estimated_latency_sec": estimate.estimated_latency_sec,
        "cache_hit": estimate.cache_hit,
        "cache_tier": estimate.cache_tier,
        "budget_mode": estimate.budget_mode,
        "budget_remaining": estimate.budget_remaining_usd,
        "approved": estimate.approved,
        "rejection_reason": estimate.rejection_reason,
        "downgrade_reason": estimate.downgrade_reason,
    }


@router.post("/roi/calculate")
async def calculate_roi(body: ROICalculateRequest):
    """Compute ROI using incremental revenue or gross profit baseline."""
    try:
        result = compute_roi(
            investment_cost=body.investment_cost,
            incremental_revenue=body.incremental_revenue,
            incremental_gross_profit=body.incremental_gross_profit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "roi_percent": result.roi_percent,
        "multiple": result.multiple,
        "band": result.band,
        "baseline": result.baseline,
    }


@router.post("/roi/project")
async def project_roi(body: ROIProjectRequest):
    """
    Project incremental revenue from funnel assumptions, then calculate ROI.
    """
    try:
        incremental_revenue = project_incremental_revenue(
            monthly_traffic=body.monthly_traffic,
            current_conversion_rate=body.current_conversion_rate,
            target_conversion_rate=body.target_conversion_rate,
            average_deal_value=body.average_deal_value,
            close_rate=body.close_rate,
        )
        roi = compute_roi(
            investment_cost=body.investment_cost,
            incremental_revenue=incremental_revenue,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "assumptions": {
            "monthly_traffic": body.monthly_traffic,
            "current_conversion_rate": body.current_conversion_rate,
            "target_conversion_rate": body.target_conversion_rate,
            "average_deal_value": body.average_deal_value,
            "close_rate": body.close_rate,
            "investment_cost": body.investment_cost,
        },
        "incremental_revenue": incremental_revenue,
        "roi_percent": roi.roi_percent,
        "multiple": roi.multiple,
        "band": roi.band,
        "executive_summary": (
            f"Projected ROI is {roi.roi_percent}% ({roi.multiple}x return) "
            f"with a '{roi.band}' performance band."
        ),
    }
