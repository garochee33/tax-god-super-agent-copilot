"""
Tax God API - AI Document Generation Endpoints
Generate professional tax/accounting documents from templates with optional AI enhancement.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.models.client import Client
from app.services.doc_generator import TEMPLATES, generate_document

router = APIRouter()


class GenerateDocRequest(BaseModel):
    doc_type: str = Field(..., description="Document type to generate")
    client_id: str | None = Field(None, description="Client ID to pull context from")
    custom_data: dict[str, Any] | None = Field(None, description="Custom context data")
    instructions: str | None = Field(None, description="Additional AI instructions")


class BatchGenerateRequest(BaseModel):
    doc_type: str = Field(..., description="Document type to generate for all matching clients")
    filter: dict[str, Any] | None = Field(None, description="Filter criteria (e.g. missing_tax_id: true)")
    custom_data: dict[str, Any] | None = Field(None, description="Shared custom data")
    instructions: str | None = Field(None, description="Additional AI instructions")


@router.post("/generate")
async def generate_doc(body: GenerateDocRequest, current_user: CurrentUser, db: DBSession):
    """Generate a single document, optionally pulling client data."""
    if body.doc_type not in TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Unknown doc_type. Available: {list(TEMPLATES.keys())}")

    context_data: dict[str, Any] = dict(body.custom_data or {})

    if body.client_id:
        result = await db.execute(select(Client).where(Client.id == body.client_id, Client.owner_id == current_user.id))
        client = result.scalar_one_or_none()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        context_data.setdefault("client_name", client.name)
        context_data.setdefault("email", client.email or "")
        context_data.setdefault("company", client.company or "")
        context_data.setdefault("tax_id", client.tax_id or "")
        context_data.setdefault("filing_type", client.filing_type or "")

    doc = await generate_document(body.doc_type, context_data, body.instructions)
    return doc


@router.get("/templates")
async def list_templates(current_user: CurrentUser):
    """List all available document templates."""
    return [{"doc_type": k, "description": v["description"]} for k, v in TEMPLATES.items()]


@router.post("/generate-batch")
async def generate_batch(body: BatchGenerateRequest, current_user: CurrentUser, db: DBSession):
    """Generate documents for multiple clients matching a filter."""
    if body.doc_type not in TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Unknown doc_type. Available: {list(TEMPLATES.keys())}")

    query = select(Client).where(Client.owner_id == current_user.id)

    # Apply filters
    if body.filter:
        if body.filter.get("missing_tax_id"):
            query = query.where((Client.tax_id == None) | (Client.tax_id == ""))  # noqa: E711

    result = await db.execute(query)
    clients = result.scalars().all()

    if not clients:
        return {"documents": [], "count": 0}

    documents = []
    for c in clients:
        context_data: dict[str, Any] = dict(body.custom_data or {})
        context_data.setdefault("client_name", c.name)
        context_data.setdefault("email", c.email or "")
        context_data.setdefault("company", c.company or "")
        context_data.setdefault("tax_id", c.tax_id or "")
        context_data.setdefault("filing_type", c.filing_type or "")
        doc = await generate_document(body.doc_type, context_data, body.instructions)
        doc["client_id"] = c.id
        documents.append(doc)

    return {"documents": documents, "count": len(documents)}
