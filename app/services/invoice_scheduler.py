"""Tax God - Recurring Invoice Scheduler Service"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.invoice import Invoice

logger = logging.getLogger(__name__)

FREQUENCY_DELTAS = {
    "weekly": timedelta(weeks=1),
    "biweekly": timedelta(weeks=2),
    "monthly": timedelta(days=30),
    "quarterly": timedelta(days=91),
    "yearly": timedelta(days=365),
}


async def process_recurring_invoices(db_session: AsyncSession) -> list[str]:
    """Find due recurring invoices, create copies, advance next_date."""
    now = datetime.now(UTC)
    result = await db_session.execute(
        select(Invoice).where(Invoice.recurring.is_(True), Invoice.recurring_next_date <= now)
    )
    due_invoices = result.scalars().all()
    created_ids: list[str] = []

    for inv in due_invoices:
        new_id = str(uuid4())
        new_invoice = Invoice(
            id=new_id,
            owner_id=inv.owner_id,
            client_id=inv.client_id,
            invoice_number=f"{inv.invoice_number}-R{now.strftime('%Y%m%d')}",
            status="sent",
            amount=inv.amount,
            tax_amount=inv.tax_amount,
            currency=inv.currency,
            due_date=now + timedelta(days=30),
            items=inv.items,
            notes=inv.notes,
            recurring=False,
        )
        db_session.add(new_invoice)

        # Advance recurring_next_date
        delta = FREQUENCY_DELTAS.get(inv.recurring_frequency or "monthly", timedelta(days=30))
        inv.recurring_next_date = inv.recurring_next_date + delta

        # Send email if client exists
        if inv.client_id:
            client_result = await db_session.execute(select(Client).where(Client.id == inv.client_id))
            client = client_result.scalar_one_or_none()
            if client and client.email:
                await send_invoice_email(new_invoice, client.email)

        created_ids.append(new_id)

    if created_ids:
        await db_session.commit()
        logger.info("Processed %d recurring invoices", len(created_ids))

    return created_ids


async def send_invoice_email(invoice: Invoice, client_email: str) -> None:
    """Send invoice notification email (logs for now)."""
    logger.info(
        "📧 Invoice %s ($%.2f) sent to %s",
        invoice.invoice_number,
        invoice.amount,
        client_email,
    )
