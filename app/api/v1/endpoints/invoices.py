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


class SetRecurringBody(BaseModel):
    frequency: str = Field(..., max_length=20)
    next_date: datetime


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
    recurring: bool
    recurring_frequency: str | None
    recurring_next_date: datetime | None
    created_at: datetime
    updated_at: datetime


class InvoiceListResponse(BaseModel):
    invoices: list[InvoiceResponse]
    total: int
    page: int
    per_page: int


async def _get_invoice(invoice_id: str, user_id: str, db):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.owner_id == user_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return inv


@router.get("/recurring", response_model=InvoiceListResponse)
async def list_recurring_invoices(
    current_user: CurrentUser, db: DBSession, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)
):
    query = select(Invoice).where(Invoice.owner_id == current_user.id, Invoice.recurring.is_(True))
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    results = (
        (
            await db.execute(
                query.order_by(Invoice.recurring_next_date.asc()).offset((page - 1) * per_page).limit(per_page)
            )
        )
        .scalars()
        .all()
    )
    return InvoiceListResponse(
        invoices=[InvoiceResponse.model_validate(i, from_attributes=True) for i in results],
        total=total,
        page=page,
        per_page=per_page,
    )


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
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    results = (
        (await db.execute(query.order_by(Invoice.updated_at.desc()).offset((page - 1) * per_page).limit(per_page)))
        .scalars()
        .all()
    )
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
    invoice = await _get_invoice(invoice_id, current_user.id, db)
    return InvoiceResponse.model_validate(invoice, from_attributes=True)


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(invoice_id: str, body: InvoiceUpdate, current_user: CurrentUser, db: DBSession):
    invoice = await _get_invoice(invoice_id, current_user.id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(invoice, field, value)
    await db.commit()
    await db.refresh(invoice)
    return InvoiceResponse.model_validate(invoice, from_attributes=True)


@router.post("/{invoice_id}/mark-paid", response_model=InvoiceResponse)
async def mark_invoice_paid(invoice_id: str, current_user: CurrentUser, db: DBSession):
    invoice = await _get_invoice(invoice_id, current_user.id, db)
    invoice.status = "paid"
    invoice.paid_date = datetime.now(UTC)
    await db.commit()
    await db.refresh(invoice)
    return InvoiceResponse.model_validate(invoice, from_attributes=True)


@router.post("/{invoice_id}/set-recurring", response_model=InvoiceResponse)
async def set_invoice_recurring(invoice_id: str, body: SetRecurringBody, current_user: CurrentUser, db: DBSession):
    invoice = await _get_invoice(invoice_id, current_user.id, db)
    invoice.recurring = True
    invoice.recurring_frequency = body.frequency
    invoice.recurring_next_date = body.next_date
    await db.commit()
    await db.refresh(invoice)
    return InvoiceResponse.model_validate(invoice, from_attributes=True)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(invoice_id: str, current_user: CurrentUser, db: DBSession):
    invoice = await _get_invoice(invoice_id, current_user.id, db)
    await db.delete(invoice)
    await db.commit()
