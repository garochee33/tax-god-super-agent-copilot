"""Tax God - Email Service"""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

BRAND_GOLD = "#D4AF37"
BRAND_NAVY = "#1B2A4A"


def _wrap_html(title: str, body: str) -> str:
    return (
        f'<html><body style="font-family:Arial,sans-serif;background:#f9f9f9;padding:20px;">'
        f'<div style="max-width:600px;margin:auto;background:#fff;border-top:4px solid {BRAND_GOLD};padding:30px;">'
        f'<h1 style="color:{BRAND_NAVY};">{title}</h1>{body}'
        f'<hr style="border:none;border-top:1px solid #eee;margin-top:30px;">'
        f'<p style="color:#888;font-size:12px;">Tax God &mdash; Your AI Tax Co-Pilot</p>'
        f"</div></body></html>"
    )


class EmailService:
    def __init__(self):
        self.host = os.getenv("TAXGOD_SMTP_HOST", "")
        self.port = int(os.getenv("TAXGOD_SMTP_PORT", "587"))
        self.user = os.getenv("TAXGOD_SMTP_USER", "")
        self.password = os.getenv("TAXGOD_SMTP_PASS", "")

    @property
    def _configured(self) -> bool:
        return bool(self.host and self.user and self.password)

    def send_email(self, to: str, subject: str, body_html: str, body_text: str | None = None) -> dict:
        if not self._configured:
            logger.info("[DEV EMAIL] To: %s | Subject: %s\n%s", to, subject, body_text or body_html)
            return {"success": True, "mode": "dev", "to": to}

        msg = MIMEMultipart("alternative")
        msg["From"] = self.user
        msg["To"] = to
        msg["Subject"] = subject
        if body_text:
            msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(self.host, self.port) as server:
            server.starttls()
            server.login(self.user, self.password)
            server.sendmail(self.user, to, msg.as_string())

        return {"success": True, "mode": "smtp", "to": to}

    def send_invoice(self, invoice, client) -> dict:
        html = _wrap_html(
            "Invoice Ready",
            f"<p>Hi {client.name},</p>"
            f"<p>Invoice <strong>{invoice.invoice_number}</strong> for "
            f'<span style="color:{BRAND_GOLD};font-weight:bold;">{invoice.currency} {invoice.amount:.2f}</span> is ready.</p>'
            f"<p>Due date: {invoice.due_date or 'On receipt'}</p>",
        )
        return self.send_email(client.email, f"Invoice {invoice.invoice_number}", html)

    def send_reminder(self, invoice, client) -> dict:
        html = _wrap_html(
            "Payment Reminder",
            f"<p>Hi {client.name},</p>"
            f"<p>This is a reminder that invoice <strong>{invoice.invoice_number}</strong> "
            f"({invoice.currency} {invoice.amount:.2f}) is due.</p>",
        )
        return self.send_email(client.email, f"Reminder: Invoice {invoice.invoice_number}", html)

    def send_portal_invite(self, client, invite_code: str) -> dict:
        html = _wrap_html(
            "You're Invited to Tax God Portal",
            f"<p>Hi {client.name},</p>"
            f"<p>Use the code below to access your client portal:</p>"
            f'<p style="font-size:24px;color:{BRAND_GOLD};font-weight:bold;">{invite_code}</p>',
        )
        return self.send_email(client.email, "Your Tax God Portal Invite", html)

    def send_deadline_reminder(self, user, deadline) -> dict:
        html = _wrap_html(
            "Upcoming Tax Deadline",
            f"<p>Hi {user.full_name},</p><p>You have an upcoming deadline: <strong>{deadline}</strong></p>",
        )
        return self.send_email(user.email, f"Deadline Reminder: {deadline}", html)
