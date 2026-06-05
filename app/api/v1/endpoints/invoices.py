"""Tax God API - Invoice Management Endpoints"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DBSession
from app.models.invoice import Invoice

router = APIRouter()


class InvoiceCreate(BaseModel):
    client_id: str | None = None
    invoice_number: str = Field(..., max_length=50)
    status: str = Field(default="draft", max_length=50)
    amount: float
    tax_amount: float = 0
    currency: str = Field(default="USD", max_length=10)
    due_date: datetime | None = None
    items: str | None = None
    notes: str | None = None


class InvoiceUpdate(BaseModel):
    client_id: str | None = None
    invoice_number: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, max_length=50)
    amount: float | None = None
    tax_amount: float | None = None
    currency: str | None = Field(default=None, max_length=10)
    due_date: datetime | None = None
    items: str | None = None
    notes: str | None = None


class InvoiceResponse(BaseModel):
    id: str
    owner_id: str
    client_id: str | None
    invoice_number: str
    status: str
    amount: float
    tax_amount: float
    currency: str
    due_date: datetime | None
    paid_date: datetime | None
    items: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class InvoiceListResponse(BaseModel):
    invoices: list[InvoiceResponse]
    total: int
    page: int
    per_page: int


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
):
    query = select(Invoice).where(Invoice.owner_id == current_user.id)
    if status_filter:
        query = query.where(Invoice.status == status_filter)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()
    query = query.order_by(Invoice.updated_at.desc()).offset((page - 1) * per_page).limit(per_page)
    results = (await db.execute(query)).scalars().all()
    return InvoiceListResponse(
        invoices=[InvoiceResponse.model_validate(i, from_attributes=True) for i in results],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(body: InvoiceCreate, current_user: CurrentUser, db: DBSession):
    invoice = Invoice(owner_id=current_user.id, **body.model_dump())
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return InvoiceResponse.model_validate(invoice, from_attributes=True)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.owner_id == current_user.id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceResponse.model_validate(invoice, from_attributes=True)


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(invoice_id: str, body: InvoiceUpdate, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.owner_id == current_user.id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(invoice, field, value)
    await db.commit()
    await db.refresh(invoice)
    return InvoiceResponse.model_validate(invoice, from_attributes=True)


@router.post("/{invoice_id}/mark-paid", response_model=InvoiceResponse)
async def mark_invoice_paid(invoice_id: str, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.owner_id == current_user.id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice.status = "paid"
    invoice.paid_date = datetime.now(UTC)
    await db.commit()
    await db.refresh(invoice)
    return InvoiceResponse.model_validate(invoice, from_attributes=True)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(invoice_id: str, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.owner_id == current_user.id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    await db.delete(invoice)
    await db.commit()
