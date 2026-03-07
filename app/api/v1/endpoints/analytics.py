"""
Tax God API - Analytics, Cost Governance, and ROI Endpoints
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, model_validator

from app.api.deps import AdminUser, CurrentUser, resolve_client_id
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


class KillSwitchBody(BaseModel):
    engage: bool = Field(True, description="True = engage (block all), False = disengage")


@router.get("/governance/circuit-breaker")
async def circuit_breaker_status(request: Request, current_user: AdminUser):
    """Trinity GEM: Circuit breaker status for external APIs. Requires admin."""
    cb = getattr(request.app.state, "circuit_breaker", None)
    if not cb:
        return {"config": {}, "agents": {}, "tripped_agents": [], "healthy_agents": []}
    return cb.get_status()


@router.post("/governance/circuit-breaker/reset")
async def circuit_breaker_reset(
    request: Request,
    current_user: AdminUser,
    agent_id: str | None = None,
):
    """Trinity GEM: Reset circuit(s). Requires admin. If agent_id omitted, reset all."""
    cb = getattr(request.app.state, "circuit_breaker", None)
    if not cb:
        raise HTTPException(status_code=503, detail="Circuit breaker not available")
    if agent_id:
        ok = cb.reset_agent(agent_id)
        if not ok:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
        return {"reset": agent_id}
    cb.reset_all()
    return {"reset": "all"}


@router.post("/governance/kill-switch")
async def cost_governor_kill_switch(
    request: Request,
    current_user: AdminUser,
    body: KillSwitchBody | None = None,
):
    """Trinity GEM: Engage or disengage the cost governor kill switch. Requires admin."""
    governor = request.app.state.cost_governor
    engage = body.engage if body is not None else True
    if engage:
        governor.engage_kill_switch()
        return {"status": "engaged", "message": "Kill switch engaged — all dispatches halted"}
    governor.disengage_kill_switch()
    return {"status": "disengaged", "message": "Kill switch disengaged"}


@router.get("/usage")
async def get_usage_analytics(request: Request, current_user: CurrentUser, client_id: Optional[str] = None):
    """Get usage analytics and cost breakdown. Requires authentication."""
    governor = request.app.state.cost_governor
    resolved_id = resolve_client_id(client_id, current_user)
    return await governor.get_analytics(resolved_id)


@router.get("/budget/{client_id}")
async def get_client_budget(client_id: str, request: Request, current_user: CurrentUser):
    """Get remaining budget for a specific client. Requires authentication."""
    governor = request.app.state.cost_governor
    settings = get_settings()
    client_id = resolve_client_id(client_id, current_user)

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
    current_user: CurrentUser,
    body: EstimateRequest | None = None,
    query: str = "",
    client_id: str = "",
    task_type: str = "",
):
    """Pre-flight cost estimate for a query (without executing it). Requires authentication."""
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
        client_id=resolve_client_id(effective.client_id, current_user),
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
        "gate_code": getattr(estimate, "gate_code", "ALLOW"),
        "swarm_plan": getattr(estimate, "swarm_plan", None),
    }


@router.post("/roi/calculate")
async def calculate_roi(body: ROICalculateRequest, current_user: CurrentUser):
    """Compute ROI using incremental revenue or gross profit baseline. Requires authentication."""
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
async def project_roi(body: ROIProjectRequest, current_user: CurrentUser):
    """
    Project incremental revenue from funnel assumptions, then calculate ROI.
    Requires authentication.
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
