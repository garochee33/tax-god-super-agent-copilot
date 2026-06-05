"""
Tax God API - Agent Gabriel (Audit) Endpoints
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.api.deps import PreparerOrAdmin, resolve_client_id

router = APIRouter()


class AuditRequest(BaseModel):
    client_id: str = Field(..., description="Client identifier")
    tax_year: int = Field(default=2024, description="Tax year to audit")
    return_data: dict[str, Any] = Field(..., description="Tax return data to audit")


class MemoRequest(BaseModel):
    subject: str = Field(..., description="Research topic")
    facts: str = Field(..., description="Relevant facts")
    client_name: str = Field(default="Client")
    client_id: str = Field(default="")
    tax_year: int = Field(default=2024)


class AuditResponseRequest(BaseModel):
    notice_type: str = Field(..., description="Type of IRS notice")
    case_number: str = Field(..., description="IRS case/notice number")
    notice_date: str = Field(..., description="Date of the notice")
    issues: list[str] = Field(..., description="Issues raised by IRS")
    taxpayer_name: str = Field(...)
    tax_years: str = Field(..., description="Tax year(s) under examination")
    supporting_facts: str = Field(default="")
    client_id: str = Field(default="")


@router.post("/run")
async def run_audit(body: AuditRequest, request: Request, current_user: PreparerOrAdmin):
    """Run Agent Gabriel audit on a tax return. Requires preparer or admin role."""
    gabriel = request.app.state.agent_gabriel

    report = await gabriel.audit_individual_return(
        client_id=resolve_client_id(body.client_id, current_user),
        tax_year=body.tax_year,
        return_data=body.return_data,
    )

    return {
        "report_id": report.report_id,
        "overall_score": report.overall_score,
        "risk_level": report.risk_level,
        "total_errors": report.total_errors_found,
        "total_savings": report.total_savings_found,
        "summary": report.ai_summary,
        "red_flags": [_flag_to_dict(f) for f in report.red_flags],
        "yellow_flags": [_flag_to_dict(f) for f in report.yellow_flags],
        "green_flags": [_flag_to_dict(f) for f in report.green_flags],
        "all_flags": [_flag_to_dict(f) for f in report.flags],
    }


@router.post("/memo")
async def generate_memo(body: MemoRequest, request: Request, current_user: PreparerOrAdmin):
    """Generate a tax research memorandum. Requires preparer or admin role."""
    writer = request.app.state.tax_writer

    doc = await writer.generate_tax_memo(
        subject=body.subject,
        facts=body.facts,
        client_name=body.client_name,
        client_id=resolve_client_id(body.client_id, current_user),
        tax_year=body.tax_year,
    )

    return {
        "document_id": doc.document_id,
        "title": doc.title,
        "content": doc.content,
        "citations": doc.citations,
        "word_count": doc.word_count,
        "confidence": doc.confidence,
        "model_used": doc.model_used,
    }


@router.post("/irs-response")
async def generate_irs_response(body: AuditResponseRequest, request: Request, current_user: PreparerOrAdmin):
    """Generate an IRS audit response letter. Requires preparer or admin role."""
    writer = request.app.state.tax_writer

    doc = await writer.generate_audit_response(
        notice_type=body.notice_type,
        case_number=body.case_number,
        notice_date=body.notice_date,
        issues=body.issues,
        taxpayer_name=body.taxpayer_name,
        tax_years=body.tax_years,
        supporting_facts=body.supporting_facts,
        client_id=resolve_client_id(body.client_id, current_user),
    )

    return {
        "document_id": doc.document_id,
        "title": doc.title,
        "content": doc.content,
        "citations": doc.citations,
        "word_count": doc.word_count,
        "confidence": doc.confidence,
        "disclaimer": doc.disclaimer,
    }


def _flag_to_dict(flag) -> dict:
    return {
        "severity": flag.severity.value,
        "category": flag.category.value,
        "title": flag.title,
        "description": flag.description,
        "recommendation": flag.recommendation,
        "form_reference": flag.form_reference,
        "irc_reference": flag.irc_reference,
        "estimated_impact_usd": flag.estimated_impact_usd,
        "confidence": flag.confidence,
    }
