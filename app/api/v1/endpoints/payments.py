"""Tax God API - Stripe Payments (Invoice checkout links + webhooks)"""

from __future__ import annotations

import os
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.models.invoice import Invoice

router = APIRouter()


class PaymentLinkResponse(BaseModel):
    invoice_id: str
    payment_link: str
    amount: float
    currency: str


class WebhookResult(BaseModel):
    status: str
    invoice_id: str | None = None


@router.post("/create-payment-link/{invoice_id}", response_model=PaymentLinkResponse)
async def create_payment_link(invoice_id: str, current_user: CurrentUser, db: DBSession):
    """Create a Stripe Checkout session for an invoice."""
    stripe_key = os.environ.get("STRIPE_SECRET_KEY")
    if not stripe_key:
        raise HTTPException(status_code=503, detail="Stripe not configured. Add STRIPE_SECRET_KEY to settings.")

    invoice = (
        await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.owner_id == current_user.id))
    ).scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == "paid":
        raise HTTPException(status_code=400, detail="Invoice already paid")

    import httpx

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://api.stripe.com/v1/checkout/sessions",
            headers={"Authorization": f"Bearer {stripe_key}"},
            data={
                "mode": "payment",
                "success_url": f"{_get_base_url()}/static/payment-success.html?invoice={invoice_id}",
                "cancel_url": f"{_get_base_url()}/static/payment-cancel.html?invoice={invoice_id}",
                "line_items[0][price_data][currency]": invoice.currency.lower(),
                "line_items[0][price_data][unit_amount]": str(int(invoice.amount * 100)),
                "line_items[0][price_data][product_data][name]": f"Invoice #{invoice.invoice_number}",
                "line_items[0][quantity]": "1",
                "metadata[invoice_id]": invoice_id,
            },
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Stripe API error")
        session = resp.json()

    invoice.payment_link = session["url"]
    invoice.stripe_payment_intent_id = session.get("payment_intent")
    await db.commit()

    return PaymentLinkResponse(
        invoice_id=invoice_id,
        payment_link=session["url"],
        amount=invoice.amount,
        currency=invoice.currency,
    )


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: DBSession):
    """Handle Stripe webhook events (payment completed)."""

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

    if webhook_secret:
        # Verify signature (simplified — production should use stripe lib)
        if not _verify_stripe_signature(payload, sig_header, webhook_secret):
            raise HTTPException(status_code=400, detail="Invalid signature")

    import json

    event = json.loads(payload)
    event_type = event.get("type")

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        invoice_id = session.get("metadata", {}).get("invoice_id")
        if invoice_id:
            invoice = (await db.execute(select(Invoice).where(Invoice.id == invoice_id))).scalar_one_or_none()
            if invoice:
                invoice.status = "paid"
                invoice.paid_date = datetime.now(UTC)
                invoice.stripe_payment_intent_id = session.get("payment_intent")
                await db.commit()
                return WebhookResult(status="paid", invoice_id=invoice_id)

    return WebhookResult(status="ignored")


def _get_base_url() -> str:
    return os.environ.get("APP_BASE_URL", "http://127.0.0.1:8000")


def _verify_stripe_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    """Basic Stripe signature verification."""
    import hashlib
    import hmac

    try:
        parts = dict(item.split("=", 1) for item in sig_header.split(","))
        timestamp = parts.get("t", "")
        signature = parts.get("v1", "")
        signed_payload = f"{timestamp}.".encode() + payload
        expected = hmac.HMAC(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False
