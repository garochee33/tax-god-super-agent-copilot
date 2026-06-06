"""Tax God - Audit Service"""

from __future__ import annotations

import json

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_event import AuditEvent


async def log_event(
    db: AsyncSession,
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    changes: dict | None = None,
    request: Request | None = None,
) -> AuditEvent:
    event = AuditEvent(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        changes=json.dumps(changes) if changes else None,
        ip_address=request.client.host if request and request.client else None,
        user_agent=(request.headers.get("user-agent", "")[:500]) if request else None,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def get_audit_trail(
    db: AsyncSession,
    user_id: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list:
    q = select(AuditEvent).where(AuditEvent.user_id == user_id)
    if entity_type:
        q = q.where(AuditEvent.entity_type == entity_type)
    if entity_id:
        q = q.where(AuditEvent.entity_id == entity_id)
    q = q.order_by(AuditEvent.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_compliance_summary(db: AsyncSession, user_id: str) -> dict:
    base = select(AuditEvent).where(AuditEvent.user_id == user_id)

    total = (await db.execute(select(func.count(AuditEvent.id)).where(AuditEvent.user_id == user_id))).scalar() or 0

    by_type_rows = (
        await db.execute(
            select(AuditEvent.action, func.count(AuditEvent.id))
            .where(AuditEvent.user_id == user_id)
            .group_by(AuditEvent.action)
        )
    ).all()
    events_by_type = {row[0]: row[1] for row in by_type_rows}

    sensitive = (
        (
            await db.execute(
                base.where(AuditEvent.action.in_(["delete", "export"])).order_by(AuditEvent.created_at.desc()).limit(10)
            )
        )
        .scalars()
        .all()
    )

    exports = (
        (await db.execute(base.where(AuditEvent.action == "export").order_by(AuditEvent.created_at.desc()).limit(10)))
        .scalars()
        .all()
    )

    return {
        "total_events": total,
        "events_by_type": events_by_type,
        "recent_sensitive_actions": [_event_dict(e) for e in sensitive],
        "data_exports": [_event_dict(e) for e in exports],
    }


def _event_dict(e: AuditEvent) -> dict:
    return {
        "id": e.id,
        "action": e.action,
        "entity_type": e.entity_type,
        "entity_id": e.entity_id,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }
