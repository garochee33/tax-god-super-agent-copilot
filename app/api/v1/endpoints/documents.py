"""
Tax God API - Document Processing Endpoints
Batch processing, multi-state research, scenario analysis.
Trinity GEM: PDF ingest (advanced PDF + document intelligence).
"""

from __future__ import annotations

import asyncio
import base64
from typing import Any

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, resolve_client_id
from app.services.document_intelligence import (
    extract_entities_tax_doc,
    extract_text_from_pdf,
)

router = APIRouter()

MAX_PDF_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


class BatchDocumentRequest(BaseModel):
    client_id: str = Field(..., description="Client identifier")
    documents: list[dict[str, Any]] = Field(..., description="List of documents to process")


class MultiStateRequest(BaseModel):
    client_id: str = Field(...)
    entity_type: str = Field(default="individual")
    income_by_state: dict[str, float] | None = Field(default=None)


class ScenarioRequest(BaseModel):
    client_id: str = Field(...)
    base_income: float = Field(...)
    base_deductions: float = Field(default=0)
    scenarios: list[dict[str, Any]] = Field(..., description="List of what-if adjustments")


class IngestPdfResponse(BaseModel):
    """Response for PDF ingest (Trinity GEM: advanced PDF + document intelligence)."""

    text: str = Field(..., description="Extracted full text")
    num_pages: int = Field(..., description="Number of pages")
    tables: list[dict[str, Any]] = Field(default_factory=list, description="Extracted tables (headers, rows, raw_text)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="PDF metadata and any error hint")
    entities: list[dict[str, str]] = Field(
        default_factory=list, description="Tax-doc entity hints (SSN/EIN/year patterns)"
    )


class IngestPdfBody(BaseModel):
    """Optional body for POST /documents/ingest (when not using file upload)."""

    content_base64: str | None = Field(None, description="PDF content as base64")
    extract_entities: bool = Field(True, description="Run tax-doc entity extraction on text")


@router.post("/ingest", response_model=IngestPdfResponse)
async def ingest_pdf(
    request: Request,
    current_user: CurrentUser,
    file: UploadFile | None = File(None),
    body: IngestPdfBody | None = None,
):
    """
    Ingest a PDF: extract full text, tables, and optional tax-doc entity hints.
    Trinity GEM: Advanced PDF + Document Intelligence. Use for client docs (W-2, 1099, workpapers).
    Send either multipart form with 'file' or JSON body with 'content_base64'.
    """
    raw: bytes
    extract_entities = True
    if file is not None and file.filename:
        if file.content_type and "pdf" not in file.content_type.lower():
            raise HTTPException(status_code=400, detail="File must be a PDF")
        raw = await file.read()
        if body is not None:
            extract_entities = body.extract_entities
    elif body and body.content_base64:
        try:
            raw = base64.b64decode(body.content_base64, validate=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64: {e}") from e
        extract_entities = body.extract_entities
    else:
        raise HTTPException(status_code=400, detail="Provide either 'file' (upload) or body.content_base64")
    if len(raw) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(status_code=400, detail=f"PDF too large (max {MAX_PDF_SIZE_BYTES // (1024 * 1024)} MB)")
    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="Empty PDF")
    result = await asyncio.to_thread(extract_text_from_pdf, raw)
    entities: list[dict[str, str]] = []
    if extract_entities and result.text:
        entities = await asyncio.to_thread(extract_entities_tax_doc, result.text)
    tables_dict = [{"headers": t.headers, "rows": t.rows, "raw_text": t.raw_text} for t in result.tables]
    return IngestPdfResponse(
        text=result.text,
        num_pages=result.num_pages,
        tables=tables_dict,
        metadata=result.metadata,
        entities=entities,
    )


@router.post("/batch-process")
async def batch_process_documents(body: BatchDocumentRequest, request: Request, current_user: CurrentUser):
    """Process a batch of uploaded documents (W-2s, 1099s, receipts) in parallel. Requires authentication."""
    processor = request.app.state.parallel_processor

    job = await processor.batch_process_documents(
        client_id=resolve_client_id(body.client_id, current_user),
        documents=body.documents,
    )

    return processor.get_job_results(job.job_id)


@router.post("/multi-state-research")
async def multi_state_research(body: MultiStateRequest, request: Request, current_user: CurrentUser):
    """Research tax implications across all 50 states in parallel. Requires authentication."""
    processor = request.app.state.parallel_processor

    job = await processor.multi_state_research(
        client_id=resolve_client_id(body.client_id, current_user),
        entity_type=body.entity_type,
        income_by_state=body.income_by_state,
    )

    return processor.get_job_results(job.job_id)


@router.post("/scenario-analysis")
async def scenario_analysis(body: ScenarioRequest, request: Request, current_user: CurrentUser):
    """Run multiple what-if tax scenarios in parallel. Requires authentication."""
    processor = request.app.state.parallel_processor

    job = await processor.run_scenario_analysis(
        client_id=resolve_client_id(body.client_id, current_user),
        base_income=body.base_income,
        base_deductions=body.base_deductions,
        scenarios=body.scenarios,
    )

    return processor.get_job_results(job.job_id)


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, request: Request, current_user: CurrentUser):
    """Check the status of a parallel processing job. Requires authentication."""
    processor = request.app.state.parallel_processor
    result = processor.get_job_results(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    return result
