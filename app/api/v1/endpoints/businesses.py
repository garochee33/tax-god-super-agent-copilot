"""
Tax God API - Business Management Endpoints
CRUD operations for businesses.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.models.business import Business, BusinessType

router = APIRouter()


class BusinessCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    business_type: BusinessType
    ein: str | None = Field(default=None, max_length=20)
    address: str | None = None
    currency: str = Field(default="USD", max_length=10)
    fiscal_year_start: str = Field(default="01-01", max_length=10)
    is_default: bool = False


class BusinessUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    business_type: BusinessType | None = None
    ein: str | None = Field(default=None, max_length=20)
    address: str | None = None
    currency: str | None = Field(default=None, max_length=10)
    fiscal_year_start: str | None = Field(default=None, max_length=10)
    is_default: bool | None = None


class BusinessResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    business_type: str
    ein: str | None
    address: str | None
    currency: str
    fiscal_year_start: str
    is_default: bool
    created_at: datetime
    updated_at: datetime


class BusinessListResponse(BaseModel):
    businesses: list[BusinessResponse]
    total: int


@router.get("", response_model=BusinessListResponse)
async def list_businesses(current_user: CurrentUser, db: DBSession):
    """List businesses owned by the current user."""
    query = select(Business).where(Business.owner_id == current_user.id).order_by(Business.created_at.desc())
    results = (await db.execute(query)).scalars().all()
    return BusinessListResponse(
        businesses=[BusinessResponse.model_validate(b, from_attributes=True) for b in results],
        total=len(results),
    )


@router.post("", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
async def create_business(body: BusinessCreate, current_user: CurrentUser, db: DBSession):
    """Create a new business."""
    business = Business(
        owner_id=current_user.id,
        name=body.name,
        business_type=body.business_type.value,
        ein=body.ein,
        address=body.address,
        currency=body.currency,
        fiscal_year_start=body.fiscal_year_start,
        is_default=body.is_default,
    )
    db.add(business)
    await db.commit()
    await db.refresh(business)
    return BusinessResponse.model_validate(business, from_attributes=True)


@router.patch("/{business_id}", response_model=BusinessResponse)
async def update_business(business_id: str, body: BusinessUpdate, current_user: CurrentUser, db: DBSession):
    """Update an existing business."""
    result = await db.execute(select(Business).where(Business.id == business_id, Business.owner_id == current_user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    updates = body.model_dump(exclude_unset=True)
    if "business_type" in updates and updates["business_type"] is not None:
        updates["business_type"] = updates["business_type"].value
    for field, value in updates.items():
        setattr(business, field, value)

    await db.commit()
    await db.refresh(business)
    return BusinessResponse.model_validate(business, from_attributes=True)


@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(business_id: str, current_user: CurrentUser, db: DBSession):
    """Delete a business."""
    result = await db.execute(select(Business).where(Business.id == business_id, Business.owner_id == current_user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    await db.delete(business)
    await db.commit()


@router.post("/{business_id}/set-default", response_model=BusinessResponse)
async def set_default_business(business_id: str, current_user: CurrentUser, db: DBSession):
    """Set a business as the default."""
    result = await db.execute(select(Business).where(Business.id == business_id, Business.owner_id == current_user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # Unset all other defaults
    all_result = await db.execute(select(Business).where(Business.owner_id == current_user.id))
    for b in all_result.scalars().all():
        b.is_default = b.id == business_id

    await db.commit()
    await db.refresh(business)
    return BusinessResponse.model_validate(business, from_attributes=True)
