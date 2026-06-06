"""Tax God API - Recurring Invoice Endpoints"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DBSession
from app.models.invoice import Invoice
from app.services.invoice_scheduler import process_recurring_invoices

router = APIRouter()


@router.post("/process")
async def trigger_recurring_processing(user: AdminUser, db: DBSession):
    """Manually trigger recurring invoice processing (admin only)."""
    created_ids = await process_recurring_invoices(db)
    return {"processed": len(created_ids), "created_invoice_ids": created_ids}


@router.get("/upcoming")
async def list_upcoming_recurring(user: CurrentUser, db: DBSession):
    """List invoices due for generation in next 30 days."""
    cutoff = datetime.now(UTC) + timedelta(days=30)
    result = await db.execute(
        select(Invoice)
        .where(
            Invoice.owner_id == user.id,
            Invoice.recurring.is_(True),
            Invoice.recurring_next_date <= cutoff,
        )
        .order_by(Invoice.recurring_next_date.asc())
    )
    invoices = result.scalars().all()
    return {
        "upcoming": [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "amount": inv.amount,
                "recurring_frequency": inv.recurring_frequency,
                "recurring_next_date": inv.recurring_next_date.isoformat() if inv.recurring_next_date else None,
            }
            for inv in invoices
        ]
    }


@router.patch("/{invoice_id}/pause")
async def pause_recurring(invoice_id: str, user: CurrentUser, db: DBSession):
    """Pause recurring on an invoice."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.owner_id == user.id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    inv.recurring = False
    await db.commit()
    return {"id": inv.id, "recurring": False}


@router.patch("/{invoice_id}/resume")
async def resume_recurring(invoice_id: str, user: CurrentUser, db: DBSession):
    """Resume recurring on an invoice."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.owner_id == user.id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if not inv.recurring_frequency:
        raise HTTPException(status_code=400, detail="No recurring frequency set")
    inv.recurring = True
    if not inv.recurring_next_date:
        inv.recurring_next_date = datetime.now(UTC)
    await db.commit()
    return {"id": inv.id, "recurring": True, "recurring_next_date": inv.recurring_next_date.isoformat()}
