"""Tax God API - Client Portal Endpoints"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.core.security import create_access_token
from app.models.client import Client
from app.models.invoice import Invoice
from app.models.portal_message import PortalMessage
from app.models.project import Project

router = APIRouter()

UPLOAD_DIR = Path("uploads/portal")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class PortalLoginRequest(BaseModel):
    email: str
    invite_code: str


class MessageCreate(BaseModel):
    content: str


@router.post("/login")
async def portal_login(body: PortalLoginRequest, db: DBSession):
    """Client logs in with email + invite code."""
    result = await db.execute(
        select(Client).where(Client.email == body.email, Client.invite_code == body.invite_code)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=401, detail="Invalid email or invite code")
    token = create_access_token(client.owner_id, extra={"client_id": client.id, "portal": True})
    return {"access_token": token, "client_id": client.id, "name": client.name}


@router.get("/invoices")
async def portal_invoices(current_user: CurrentUser, db: DBSession):
    """Client sees their invoices."""
    result = await db.execute(
        select(Invoice).where(Invoice.owner_id == current_user.id).order_by(Invoice.created_at.desc())
    )
    invoices = result.scalars().all()
    return [
        {"id": i.id, "invoice_number": i.invoice_number, "amount": i.amount, "status": i.status, "due_date": str(i.due_date) if i.due_date else None}
        for i in invoices
    ]


@router.get("/projects")
async def portal_projects(current_user: CurrentUser, db: DBSession):
    """Client sees their project status."""
    result = await db.execute(
        select(Project).where(Project.owner_id == current_user.id).order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return [
        {"id": p.id, "name": p.name, "status": p.status, "start_date": str(p.start_date) if p.start_date else None, "end_date": str(p.end_date) if p.end_date else None}
        for p in projects
    ]


@router.post("/documents/upload")
async def portal_upload_document(current_user: CurrentUser, file: UploadFile = File(...)):
    """Client uploads documents."""
    dest = UPLOAD_DIR / f"{current_user.id}_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{file.filename}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"filename": file.filename, "path": str(dest)}


@router.get("/messages")
async def portal_get_messages(current_user: CurrentUser, db: DBSession):
    """Client sees messages from preparer."""
    # Find client record for this user (as owner)
    client_result = await db.execute(select(Client).where(Client.owner_id == current_user.id).limit(1))
    client = client_result.scalar_one_or_none()
    if not client:
        return []
    result = await db.execute(
        select(PortalMessage).where(PortalMessage.client_id == client.id).order_by(PortalMessage.created_at.asc())
    )
    messages = result.scalars().all()
    return [{"id": m.id, "sender": m.sender, "content": m.content, "created_at": str(m.created_at)} for m in messages]


@router.post("/messages")
async def portal_send_message(body: MessageCreate, current_user: CurrentUser, db: DBSession):
    """Client sends message."""
    client_result = await db.execute(select(Client).where(Client.owner_id == current_user.id).limit(1))
    client = client_result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client record not found")
    msg = PortalMessage(client_id=client.id, sender="client", content=body.content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return {"id": msg.id, "sender": msg.sender, "content": msg.content, "created_at": str(msg.created_at)}
