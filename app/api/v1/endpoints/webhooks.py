"""Tax God API - Webhook Management Endpoints"""

from __future__ import annotations

import secrets
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.models.webhook import Webhook, WebhookDelivery
from app.services.webhook_service import dispatch_event

router = APIRouter()


class WebhookCreate(BaseModel):
    url: str = Field(..., min_length=1)
    events: list[str] = Field(..., min_length=1)


class WebhookResponse(BaseModel):
    id: str
    url: str
    events: str
    is_active: bool
    created_at: datetime


class DeliveryResponse(BaseModel):
    id: str
    event_type: str
    payload: str
    response_code: int | None
    delivered_at: datetime


@router.post("/webhooks", status_code=status.HTTP_201_CREATED)
async def create_webhook(body: WebhookCreate, user: CurrentUser, db: DBSession):
    wh = Webhook(
        owner_id=user.id,
        url=body.url,
        events=",".join(body.events),
        secret=secrets.token_hex(32),
    )
    db.add(wh)
    await db.commit()
    await db.refresh(wh)
    return {"id": wh.id, "url": wh.url, "events": wh.events, "secret": wh.secret, "is_active": wh.is_active}


@router.get("/webhooks")
async def list_webhooks(user: CurrentUser, db: DBSession):
    result = await db.execute(select(Webhook).where(Webhook.owner_id == user.id))
    hooks = result.scalars().all()
    return [
        WebhookResponse(id=h.id, url=h.url, events=h.events, is_active=h.is_active, created_at=h.created_at)
        for h in hooks
    ]


@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(webhook_id: str, user: CurrentUser, db: DBSession):
    result = await db.execute(select(Webhook).where(Webhook.id == webhook_id, Webhook.owner_id == user.id))
    wh = result.scalar_one_or_none()
    if not wh:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.delete(wh)
    await db.commit()


@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(webhook_id: str, user: CurrentUser, db: DBSession):
    result = await db.execute(select(Webhook).where(Webhook.id == webhook_id, Webhook.owner_id == user.id))
    wh = result.scalar_one_or_none()
    if not wh:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await dispatch_event(db, user.id, "test", {"message": "Test webhook delivery"})
    return {"status": "sent"}


@router.get("/webhooks/{webhook_id}/deliveries")
async def list_deliveries(webhook_id: str, user: CurrentUser, db: DBSession):
    result = await db.execute(select(Webhook).where(Webhook.id == webhook_id, Webhook.owner_id == user.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Webhook not found")
    deliveries = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.delivered_at.desc())
        .limit(50)
    )
    rows = deliveries.scalars().all()
    return [
        DeliveryResponse(
            id=d.id,
            event_type=d.event_type,
            payload=d.payload,
            response_code=d.response_code,
            delivered_at=d.delivered_at,
        )
        for d in rows
    ]
