"""Tax God API - Email Endpoints"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.models.client import Client
from app.models.invoice import Invoice
from app.services.email_service import EmailService

router = APIRouter()
email_service = EmailService()


@router.post("/send-invoice/{invoice_id}")
async def send_invoice_email(invoice_id: str, db: DBSession, user: CurrentUser):
    invoice = (await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.owner_id == user.id))).scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if not invoice.client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice has no client")
    client = (await db.execute(select(Client).where(Client.id == invoice.client_id))).scalar_one_or_none()
    if not client or not client.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client has no email")
    return email_service.send_invoice(invoice, client)


@router.post("/send-reminder/{invoice_id}")
async def send_reminder_email(invoice_id: str, db: DBSession, user: CurrentUser):
    invoice = (await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.owner_id == user.id))).scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if not invoice.client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice has no client")
    client = (await db.execute(select(Client).where(Client.id == invoice.client_id))).scalar_one_or_none()
    if not client or not client.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client has no email")
    return email_service.send_reminder(invoice, client)


@router.post("/send-portal-invite/{client_id}")
async def send_portal_invite(client_id: str, db: DBSession, user: CurrentUser):
    client = (await db.execute(select(Client).where(Client.id == client_id, Client.owner_id == user.id))).scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    if not client.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client has no email")
    invite_code = client.invite_code or "TAXGOD-INVITE"
    return email_service.send_portal_invite(client, invite_code)


@router.post("/test")
async def send_test_email(user: CurrentUser):
    from app.services.email_service import _wrap_html
    html = _wrap_html("Test Email", "<p>Your SMTP configuration is working correctly!</p>")
    return email_service.send_email(user.email, "Tax God - Test Email", html)
