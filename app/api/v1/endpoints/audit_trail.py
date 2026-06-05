"""Tax God API - Audit Trail & Compliance Endpoints"""

from __future__ import annotations

import json

from fastapi import APIRouter, Request

from app.api.deps import AdminUser, CurrentUser, DBSession
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
