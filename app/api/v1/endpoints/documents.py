"""
Tax God API - Document Processing Endpoints
Batch processing, multi-state research, scenario analysis.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.services.parallel_processor import JobType

router = APIRouter()


class BatchDocumentRequest(BaseModel):
    client_id: str = Field(..., description="Client identifier")
    documents: list[dict[str, Any]] = Field(..., description="List of documents to process")


class MultiStateRequest(BaseModel):
    client_id: str = Field(...)
    entity_type: str = Field(default="individual")
    income_by_state: Optional[dict[str, float]] = Field(default=None)


class ScenarioRequest(BaseModel):
    client_id: str = Field(...)
    base_income: float = Field(...)
    base_deductions: float = Field(default=0)
    scenarios: list[dict[str, Any]] = Field(..., description="List of what-if adjustments")


@router.post("/batch-process")
async def batch_process_documents(body: BatchDocumentRequest, request: Request):
    """Process a batch of uploaded documents (W-2s, 1099s, receipts) in parallel."""
    processor = request.app.state.parallel_processor

    job = await processor.batch_process_documents(
        client_id=body.client_id,
        documents=body.documents,
    )

    return processor.get_job_results(job.job_id)


@router.post("/multi-state-research")
async def multi_state_research(body: MultiStateRequest, request: Request):
    """Research tax implications across all 50 states in parallel."""
    processor = request.app.state.parallel_processor

    job = await processor.multi_state_research(
        client_id=body.client_id,
        entity_type=body.entity_type,
        income_by_state=body.income_by_state,
    )

    return processor.get_job_results(job.job_id)


@router.post("/scenario-analysis")
async def scenario_analysis(body: ScenarioRequest, request: Request):
    """Run multiple what-if tax scenarios in parallel."""
    processor = request.app.state.parallel_processor

    job = await processor.run_scenario_analysis(
        client_id=body.client_id,
        base_income=body.base_income,
        base_deductions=body.base_deductions,
        scenarios=body.scenarios,
    )

    return processor.get_job_results(job.job_id)


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, request: Request):
    """Check the status of a parallel processing job."""
    processor = request.app.state.parallel_processor
    result = processor.get_job_results(job_id)
    if not result:
        return {"error": "Job not found"}
    return result
