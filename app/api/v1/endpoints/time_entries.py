"""Tax God API - Time Entry Endpoints"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DBSession
from app.models.time_entry import TimeEntry

router = APIRouter()


class TimeEntryCreate(BaseModel):
    project_id: str | None = None
    client_id: str | None = None
    description: str = Field(..., max_length=500)
    hours: float
    date: datetime
    billable: bool = True
    rate: float | None = None


class TimeEntryUpdate(BaseModel):
    project_id: str | None = None
    client_id: str | None = None
    description: str | None = Field(default=None, max_length=500)
    hours: float | None = None
    date: datetime | None = None
    billable: bool | None = None
    rate: float | None = None
    invoiced: bool | None = None


class TimeEntryResponse(BaseModel):
    id: str
    owner_id: str
    project_id: str | None
    client_id: str | None
    description: str
    hours: float
    date: datetime
    billable: bool
    rate: float | None
    invoiced: bool
    created_at: datetime
    updated_at: datetime


@router.get("/summary")
async def time_entries_summary(current_user: CurrentUser, db: DBSession):
    query = (
        select(TimeEntry.project_id, func.sum(TimeEntry.hours), func.sum(TimeEntry.hours * TimeEntry.rate))
        .where(TimeEntry.owner_id == current_user.id, TimeEntry.billable.is_(True))
        .group_by(TimeEntry.project_id)
    )
    rows = (await db.execute(query)).all()
    return {"items": [{"project_id": r[0], "total_hours": r[1] or 0, "billable_amount": r[2] or 0} for r in rows]}


@router.get("")
async def list_time_entries(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    project_id: str | None = None,
    client_id: str | None = None,
    billable: bool | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    query = select(TimeEntry).where(TimeEntry.owner_id == current_user.id)
    if project_id:
        query = query.where(TimeEntry.project_id == project_id)
    if client_id:
        query = query.where(TimeEntry.client_id == client_id)
    if billable is not None:
        query = query.where(TimeEntry.billable == billable)
    if date_from:
        query = query.where(TimeEntry.date >= date_from)
    if date_to:
        query = query.where(TimeEntry.date <= date_to)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    results = (
        (await db.execute(query.order_by(TimeEntry.date.desc()).offset((page - 1) * per_page).limit(per_page)))
        .scalars()
        .all()
    )
    return {
        "time_entries": [TimeEntryResponse.model_validate(t, from_attributes=True) for t in results],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post("", response_model=TimeEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_time_entry(body: TimeEntryCreate, current_user: CurrentUser, db: DBSession):
    entry = TimeEntry(owner_id=current_user.id, **body.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return TimeEntryResponse.model_validate(entry, from_attributes=True)


@router.patch("/{entry_id}", response_model=TimeEntryResponse)
async def update_time_entry(entry_id: str, body: TimeEntryUpdate, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(TimeEntry).where(TimeEntry.id == entry_id, TimeEntry.owner_id == current_user.id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    await db.commit()
    await db.refresh(entry)
    return TimeEntryResponse.model_validate(entry, from_attributes=True)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_time_entry(entry_id: str, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(TimeEntry).where(TimeEntry.id == entry_id, TimeEntry.owner_id == current_user.id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    await db.delete(entry)
    await db.commit()
