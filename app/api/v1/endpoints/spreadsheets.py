"""Tax God API - Spreadsheet Management Endpoints"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.models.spreadsheet import Spreadsheet

router = APIRouter()


class SpreadsheetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sheet_type: str = Field(..., max_length=50)
    data: str | None = None
    notes: str | None = None


class SpreadsheetUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    sheet_type: str | None = Field(default=None, max_length=50)
    data: str | None = None
    notes: str | None = None


class SpreadsheetResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    sheet_type: str
    data: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class SpreadsheetListResponse(BaseModel):
    spreadsheets: list[SpreadsheetResponse]
    total: int


@router.get("", response_model=SpreadsheetListResponse)
async def list_spreadsheets(current_user: CurrentUser, db: DBSession):
    query = select(Spreadsheet).where(Spreadsheet.owner_id == current_user.id).order_by(Spreadsheet.updated_at.desc())
    results = (await db.execute(query)).scalars().all()
    return SpreadsheetListResponse(
        spreadsheets=[SpreadsheetResponse.model_validate(s, from_attributes=True) for s in results],
        total=len(results),
    )


@router.post("", response_model=SpreadsheetResponse, status_code=status.HTTP_201_CREATED)
async def create_spreadsheet(body: SpreadsheetCreate, current_user: CurrentUser, db: DBSession):
    spreadsheet = Spreadsheet(owner_id=current_user.id, **body.model_dump())
    db.add(spreadsheet)
    await db.commit()
    await db.refresh(spreadsheet)
    return SpreadsheetResponse.model_validate(spreadsheet, from_attributes=True)


@router.get("/{spreadsheet_id}", response_model=SpreadsheetResponse)
async def get_spreadsheet(spreadsheet_id: str, current_user: CurrentUser, db: DBSession):
    result = await db.execute(
        select(Spreadsheet).where(Spreadsheet.id == spreadsheet_id, Spreadsheet.owner_id == current_user.id)
    )
    spreadsheet = result.scalar_one_or_none()
    if not spreadsheet:
        raise HTTPException(status_code=404, detail="Spreadsheet not found")
    return SpreadsheetResponse.model_validate(spreadsheet, from_attributes=True)


@router.patch("/{spreadsheet_id}", response_model=SpreadsheetResponse)
async def update_spreadsheet(spreadsheet_id: str, body: SpreadsheetUpdate, current_user: CurrentUser, db: DBSession):
    result = await db.execute(
        select(Spreadsheet).where(Spreadsheet.id == spreadsheet_id, Spreadsheet.owner_id == current_user.id)
    )
    spreadsheet = result.scalar_one_or_none()
    if not spreadsheet:
        raise HTTPException(status_code=404, detail="Spreadsheet not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(spreadsheet, field, value)
    await db.commit()
    await db.refresh(spreadsheet)
    return SpreadsheetResponse.model_validate(spreadsheet, from_attributes=True)


@router.delete("/{spreadsheet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_spreadsheet(spreadsheet_id: str, current_user: CurrentUser, db: DBSession):
    result = await db.execute(
        select(Spreadsheet).where(Spreadsheet.id == spreadsheet_id, Spreadsheet.owner_id == current_user.id)
    )
    spreadsheet = result.scalar_one_or_none()
    if not spreadsheet:
        raise HTTPException(status_code=404, detail="Spreadsheet not found")
    await db.delete(spreadsheet)
    await db.commit()
