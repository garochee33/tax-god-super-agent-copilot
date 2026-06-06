"""Tax God - Webhook Dispatch Service"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import Webhook, WebhookDelivery

logger = logging.getLogger(__name__)


async def dispatch_event(db: AsyncSession, user_id: str, event_type: str, payload: dict) -> None:
    """Find matching webhooks for user/event and POST with HMAC signature."""
    result = await db.execute(select(Webhook).where(Webhook.owner_id == user_id, Webhook.is_active.is_(True)))
    webhooks = result.scalars().all()

    body = json.dumps(payload)
    for wh in webhooks:
        if event_type not in wh.events.split(","):
            continue
        signature = hmac.new(wh.secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        code = None
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    wh.url,
                    content=body,
                    headers={"Content-Type": "application/json", "X-TaxGod-Signature": signature},
                )
                code = resp.status_code
        except Exception as exc:
            logger.warning("Webhook delivery failed for %s: %s", wh.id, exc)
        delivery = WebhookDelivery(webhook_id=wh.id, event_type=event_type, payload=body, response_code=code)
        db.add(delivery)
    await db.commit()
