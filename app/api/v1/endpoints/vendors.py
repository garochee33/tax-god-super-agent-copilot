"""Tax God API - Vendor Endpoints"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select

from app.api.deps import CurrentUser, DBSession
from app.models.vendor import Vendor

router = APIRouter()


class VendorCreate(BaseModel):
    name: str = Field(..., max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    company: str | None = Field(default=None, max_length=255)
    category: str = Field(..., max_length=100)
    tax_id: str | None = Field(default=None, max_length=50)
    is_1099: bool = False
    total_paid: float = 0
    notes: str | None = None


class VendorUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    company: str | None = Field(default=None, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    tax_id: str | None = Field(default=None, max_length=50)
    is_1099: bool | None = None
    total_paid: float | None = None
    notes: str | None = None


class VendorResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    email: str | None
    phone: str | None
    company: str | None
    category: str
    tax_id: str | None
    is_1099: bool
    total_paid: float
    notes: str | None
    created_at: datetime
    updated_at: datetime


@router.get("/1099")
async def list_1099_vendors(current_user: CurrentUser, db: DBSession):
    query = select(Vendor).where(Vendor.owner_id == current_user.id, Vendor.is_1099.is_(True), Vendor.total_paid >= 600)
    results = (await db.execute(query.order_by(Vendor.name))).scalars().all()
    return {"vendors": [VendorResponse.model_validate(v, from_attributes=True) for v in results]}


@router.get("")
async def list_vendors(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = None,
):
    query = select(Vendor).where(Vendor.owner_id == current_user.id)
    if search:
        query = query.where(or_(Vendor.name.ilike(f"%{search}%"), Vendor.company.ilike(f"%{search}%")))
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    results = (
        (await db.execute(query.order_by(Vendor.name).offset((page - 1) * per_page).limit(per_page))).scalars().all()
    )
    return {
        "vendors": [VendorResponse.model_validate(v, from_attributes=True) for v in results],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post("", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(body: VendorCreate, current_user: CurrentUser, db: DBSession):
    vendor = Vendor(owner_id=current_user.id, **body.model_dump())
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    return VendorResponse.model_validate(vendor, from_attributes=True)


@router.patch("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(vendor_id: str, body: VendorUpdate, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id, Vendor.owner_id == current_user.id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(vendor, field, value)
    await db.commit()
    await db.refresh(vendor)
    return VendorResponse.model_validate(vendor, from_attributes=True)


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor(vendor_id: str, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id, Vendor.owner_id == current_user.id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    await db.delete(vendor)
    await db.commit()
