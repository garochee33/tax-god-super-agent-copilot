"""Tax God — Activity Logs, Build Tracking, Knowledge Base API"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import desc, select

from app.api.deps import AdminUser, CurrentUser, DBSession
from app.models.activity import ActivityLog, BuildLog, KnowledgeEntry

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────────


class LogEntry(BaseModel):
    id: str
    category: str
    action: str
    detail: str | None
    metadata_json: dict | None
    created_at: datetime


class BuildLogEntry(BaseModel):
    id: str
    agent_name: str
    commit_sha: str | None
    action: str
    files_changed: dict | None
    detail: str | None
    created_at: datetime


class KBEntry(BaseModel):
    id: str
    category: str
    title: str
    content: str
    source: str | None
    tags: dict | None
    version: int
    created_at: datetime
    updated_at: datetime


class KBCreateRequest(BaseModel):
    category: str = "note"
    title: str
    content: str
    source: str | None = None
    tags: dict | None = None


class BuildLogCreateRequest(BaseModel):
    agent_name: str
    commit_sha: str | None = None
    action: str
    files_changed: dict | None = None
    detail: str | None = None


# ─── Activity Logs ────────────────────────────────────────────────────────────


@router.get("/activity", response_model=list[LogEntry])
async def get_activity_logs(
    user: CurrentUser,
    db: DBSession,
    category: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    """Get activity logs. Admins see all, users see their own."""
    q = select(ActivityLog).order_by(desc(ActivityLog.created_at))
    if user.role != "admin":
        q = q.where(ActivityLog.user_id == user.id)
    if category:
        q = q.where(ActivityLog.category == category)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return [
        LogEntry(
            id=r.id,
            category=r.category,
            action=r.action,
            detail=r.detail,
            metadata_json=r.metadata_json,
            created_at=r.created_at,
        )
        for r in result.scalars().all()
    ]


# ─── Build Logs ───────────────────────────────────────────────────────────────


@router.get("/builds", response_model=list[BuildLogEntry])
async def get_build_logs(
    user: AdminUser,
    db: DBSession,
    limit: int = Query(default=50, le=200),
):
    """Get build/agent contribution logs."""
    q = select(BuildLog).order_by(desc(BuildLog.created_at)).limit(limit)
    result = await db.execute(q)
    return [
        BuildLogEntry(
            id=r.id,
            agent_name=r.agent_name,
            commit_sha=r.commit_sha,
            action=r.action,
            files_changed=r.files_changed,
            detail=r.detail,
            created_at=r.created_at,
        )
        for r in result.scalars().all()
    ]


@router.post("/builds", response_model=BuildLogEntry)
async def create_build_log(body: BuildLogCreateRequest, user: AdminUser, db: DBSession):
    """Log an agent/build contribution."""
    entry = BuildLog(
        agent_name=body.agent_name,
        commit_sha=body.commit_sha,
        action=body.action,
        files_changed=body.files_changed,
        detail=body.detail,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return BuildLogEntry(
        id=entry.id,
        agent_name=entry.agent_name,
        commit_sha=entry.commit_sha,
        action=entry.action,
        files_changed=entry.files_changed,
        detail=entry.detail,
        created_at=entry.created_at,
    )


# ─── Knowledge Base ───────────────────────────────────────────────────────────


@router.get("/kb", response_model=list[KBEntry])
async def get_knowledge_entries(
    user: CurrentUser,
    db: DBSession,
    category: str | None = None,
    search: str | None = None,
    limit: int = Query(default=50, le=200),
):
    """Get knowledge base entries."""
    q = select(KnowledgeEntry).order_by(desc(KnowledgeEntry.updated_at))
    if category:
        q = q.where(KnowledgeEntry.category == category)
    if search:
        q = q.where(KnowledgeEntry.title.ilike(f"%{search}%"))
    q = q.limit(limit)
    result = await db.execute(q)
    return [
        KBEntry(
            id=r.id,
            category=r.category,
            title=r.title,
            content=r.content,
            source=r.source,
            tags=r.tags,
            version=r.version,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in result.scalars().all()
    ]


@router.post("/kb", response_model=KBEntry)
async def create_knowledge_entry(body: KBCreateRequest, user: CurrentUser, db: DBSession):
    """Create a knowledge base entry."""
    entry = KnowledgeEntry(
        user_id=user.id,
        category=body.category,
        title=body.title,
        content=body.content,
        source=body.source or f"user:{user.email}",
        tags=body.tags,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return KBEntry(
        id=entry.id,
        category=entry.category,
        title=entry.title,
        content=entry.content,
        source=entry.source,
        tags=entry.tags,
        version=entry.version,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


@router.get("/kb/{entry_id}", response_model=KBEntry)
async def get_knowledge_entry(entry_id: str, user: CurrentUser, db: DBSession):
    """Get a single KB entry."""
    result = await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Entry not found")
    return KBEntry(
        id=entry.id,
        category=entry.category,
        title=entry.title,
        content=entry.content,
        source=entry.source,
        tags=entry.tags,
        version=entry.version,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


# ─── Helper: Log Activity (importable by other modules) ──────────────────────


async def log_activity(
    db: Any,
    category: str,
    action: str,
    user_id: str | None = None,
    detail: str | None = None,
    metadata: dict | None = None,
    ip: str | None = None,
):
    """Helper to log activity from any endpoint."""
    entry = ActivityLog(
        user_id=user_id,
        category=category,
        action=action,
        detail=detail,
        metadata_json=metadata,
        ip_address=ip,
    )
    db.add(entry)
    await db.commit()
