"""
Tax God API - Client Management Endpoints (Agora)
CRUD operations for tax clients.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DBSession
from app.models.client import Client, ClientStatus

router = APIRouter()


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    company: str | None = Field(default=None, max_length=255)
    status: ClientStatus = ClientStatus.ACTIVE
    notes: str | None = None
    tax_id: str | None = Field(default=None, max_length=50)
    filing_type: str | None = Field(default=None, max_length=50)


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    company: str | None = Field(default=None, max_length=255)
    status: ClientStatus | None = None
    notes: str | None = None
    tax_id: str | None = Field(default=None, max_length=50)
    filing_type: str | None = Field(default=None, max_length=50)


class ClientResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    email: str | None
    phone: str | None
    company: str | None
    status: str
    notes: str | None
    tax_id: str | None
    filing_type: str | None
    created_at: datetime
    updated_at: datetime


class ClientListResponse(BaseModel):
    clients: list[ClientResponse]
    total: int
    page: int
    per_page: int


@router.get("", response_model=ClientListResponse)
async def list_clients(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: ClientStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, max_length=255),
):
    """List clients owned by the current user (paginated)."""
    query = select(Client).where(Client.owner_id == current_user.id)

    if status_filter:
        query = query.where(Client.status == status_filter.value)
    if search:
        query = query.where(Client.name.ilike(f"%{search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(Client.updated_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    results = (await db.execute(query)).scalars().all()

    return ClientListResponse(
        clients=[ClientResponse.model_validate(c, from_attributes=True) for c in results],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(body: ClientCreate, current_user: CurrentUser, db: DBSession):
    """Create a new client."""
    client = Client(
        owner_id=current_user.id,
        name=body.name,
        email=body.email,
        phone=body.phone,
        company=body.company,
        status=body.status.value,
        notes=body.notes,
        tax_id=body.tax_id,
        filing_type=body.filing_type,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return ClientResponse.model_validate(client, from_attributes=True)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str, current_user: CurrentUser, db: DBSession):
    """Get a single client by ID."""
    result = await db.execute(select(Client).where(Client.id == client_id, Client.owner_id == current_user.id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientResponse.model_validate(client, from_attributes=True)


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(client_id: str, body: ClientUpdate, current_user: CurrentUser, db: DBSession):
    """Update an existing client."""
    result = await db.execute(select(Client).where(Client.id == client_id, Client.owner_id == current_user.id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    updates = body.model_dump(exclude_unset=True)
    if "status" in updates and updates["status"] is not None:
        updates["status"] = updates["status"].value
    for field, value in updates.items():
        setattr(client, field, value)

    await db.commit()
    await db.refresh(client)
    return ClientResponse.model_validate(client, from_attributes=True)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(client_id: str, current_user: CurrentUser, db: DBSession):
    """Delete a client."""
    result = await db.execute(select(Client).where(Client.id == client_id, Client.owner_id == current_user.id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    await db.delete(client)
    await db.commit()
