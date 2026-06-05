"""
Tax God API - User Profile Endpoints
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.core.security import hash_password, verify_password
from app.models.user import User

router = APIRouter()


class ProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


@router.get("", response_model=ProfileResponse)
async def get_profile(current_user: CurrentUser):
    """Get current user profile."""
    return ProfileResponse.model_validate(current_user, from_attributes=True)


@router.patch("", response_model=ProfileResponse)
async def update_profile(body: ProfileUpdate, current_user: CurrentUser, db: DBSession):
    """Update current user's name or email."""
    updates = body.model_dump(exclude_unset=True)

    if "email" in updates and updates["email"] != current_user.email:
        existing = await db.execute(select(User).where(User.email == updates["email"]))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    for field, value in updates.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)
    return ProfileResponse.model_validate(current_user, from_attributes=True)


@router.post("/password", status_code=status.HTTP_200_OK)
async def change_password(body: ChangePasswordRequest, current_user: CurrentUser, db: DBSession):
    """Change password (requires current password)."""
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    current_user.hashed_password = hash_password(body.new_password)
    await db.commit()
    return {"message": "Password updated successfully"}
