"""Tax God API - Note Management Endpoints"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DBSession
from app.models.note import Note

router = APIRouter()


class NoteCreate(BaseModel):
    client_id: str | None = None
    project_id: str | None = None
    title: str = Field(..., min_length=1, max_length=255)
    content: str
    tags: str | None = Field(default=None, max_length=500)


class NoteUpdate(BaseModel):
    client_id: str | None = None
    project_id: str | None = None
    title: str | None = Field(default=None, max_length=255)
    content: str | None = None
    tags: str | None = Field(default=None, max_length=500)


class NoteResponse(BaseModel):
    id: str
    owner_id: str
    client_id: str | None
    project_id: str | None
    title: str
    content: str
    tags: str | None
    created_at: datetime
    updated_at: datetime


class NoteListResponse(BaseModel):
    notes: list[NoteResponse]
    total: int
    page: int
    per_page: int


@router.get("", response_model=NoteListResponse)
async def list_notes(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    client_id: str | None = Query(default=None),
    project_id: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=255),
):
    query = select(Note).where(Note.owner_id == current_user.id)
    if client_id:
        query = query.where(Note.client_id == client_id)
    if project_id:
        query = query.where(Note.project_id == project_id)
    if search:
        query = query.where(Note.title.ilike(f"%{search}%"))
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()
    query = query.order_by(Note.updated_at.desc()).offset((page - 1) * per_page).limit(per_page)
    results = (await db.execute(query)).scalars().all()
    return NoteListResponse(
        notes=[NoteResponse.model_validate(n, from_attributes=True) for n in results],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(body: NoteCreate, current_user: CurrentUser, db: DBSession):
    note = Note(owner_id=current_user.id, **body.model_dump())
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return NoteResponse.model_validate(note, from_attributes=True)


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: str, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(Note).where(Note.id == note_id, Note.owner_id == current_user.id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteResponse.model_validate(note, from_attributes=True)


@router.patch("/{note_id}", response_model=NoteResponse)
async def update_note(note_id: str, body: NoteUpdate, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(Note).where(Note.id == note_id, Note.owner_id == current_user.id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(note, field, value)
    await db.commit()
    await db.refresh(note)
    return NoteResponse.model_validate(note, from_attributes=True)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: str, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(Note).where(Note.id == note_id, Note.owner_id == current_user.id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    await db.delete(note)
    await db.commit()
