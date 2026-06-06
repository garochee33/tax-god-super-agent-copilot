"""Tax God API - Audit Trail & Compliance Endpoints"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Query, Request
from sqlalchemy import delete, func, select

from app.api.deps import AdminUser, CurrentUser, DBSession
from app.models.audit_event import AuditEvent
from app.services.audit_service import get_audit_trail, get_compliance_summary, log_event

router = APIRouter()


@router.get("/events")
async def list_audit_events(
    db: DBSession,
    current_user: AdminUser,
    limit: int = 50,
    offset: int = 0,
):
    events = await get_audit_trail(db, current_user.id, limit=limit, offset=offset)
    return [_serialize(e) for e in events]


@router.get("/events/{entity_type}/{entity_id}")
async def entity_history(
    entity_type: str,
    entity_id: str,
    db: DBSession,
    current_user: CurrentUser,
    limit: int = 50,
    offset: int = 0,
):
    events = await get_audit_trail(
        db, current_user.id, entity_type=entity_type, entity_id=entity_id, limit=limit, offset=offset
    )
    return [_serialize(e) for e in events]


@router.get("/compliance")
async def compliance_dashboard(db: DBSession, current_user: CurrentUser):
    return await get_compliance_summary(db, current_user.id)


@router.get("/export")
async def export_audit_log(db: DBSession, current_user: AdminUser, request: Request):
    events = await get_audit_trail(db, current_user.id, limit=10000, offset=0)
    await log_event(db, current_user.id, "export", "audit_log", request=request)
    return [_serialize(e) for e in events]


def _serialize(e) -> dict:
    return {
        "id": e.id,
        "user_id": e.user_id,
        "action": e.action,
        "entity_type": e.entity_type,
        "entity_id": e.entity_id,
        "changes": json.loads(e.changes) if e.changes else None,
        "ip_address": e.ip_address,
        "user_agent": e.user_agent,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


@router.delete("/purge")
async def purge_old_events(
    db: DBSession,
    current_user: AdminUser,
    request: Request,
    older_than_days: int = Query(default=90, ge=1),
):
    cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
    result = await db.execute(delete(AuditEvent).where(AuditEvent.created_at < cutoff))
    deleted_count = result.rowcount
    await db.commit()
    await log_event(
        db,
        current_user.id,
        "purge",
        "audit_trail",
        changes={"older_than_days": older_than_days, "deleted": deleted_count},
        request=request,
    )
    return {"deleted": deleted_count, "older_than_days": older_than_days}


@router.get("/stats")
async def audit_stats(db: DBSession, current_user: AdminUser):
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    events_today = (
        await db.execute(select(func.count(AuditEvent.id)).where(AuditEvent.created_at >= today_start))
    ).scalar() or 0
    events_this_week = (
        await db.execute(select(func.count(AuditEvent.id)).where(AuditEvent.created_at >= week_start))
    ).scalar() or 0
    events_this_month = (
        await db.execute(select(func.count(AuditEvent.id)).where(AuditEvent.created_at >= month_start))
    ).scalar() or 0

    top_actions_rows = (
        await db.execute(
            select(AuditEvent.action, func.count(AuditEvent.id).label("cnt"))
            .group_by(AuditEvent.action)
            .order_by(func.count(AuditEvent.id).desc())
            .limit(5)
        )
    ).all()

    top_entities_rows = (
        await db.execute(
            select(AuditEvent.entity_type, func.count(AuditEvent.id).label("cnt"))
            .group_by(AuditEvent.entity_type)
            .order_by(func.count(AuditEvent.id).desc())
            .limit(5)
        )
    ).all()

    return {
        "events_today": events_today,
        "events_this_week": events_this_week,
        "events_this_month": events_this_month,
        "top_actions": [{"action": r[0], "count": r[1]} for r in top_actions_rows],
        "top_entities": [{"entity_type": r[0], "count": r[1]} for r in top_entities_rows],
    }
