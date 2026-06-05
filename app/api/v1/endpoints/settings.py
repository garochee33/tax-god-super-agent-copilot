"""
Tax God API - User Settings Endpoints
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.core.crypto import get_fernet
from app.models.integration import IntegrationCredential
from app.models.user_settings import UserSettings

router = APIRouter()


class SettingsResponse(BaseModel):
    theme: str
    notifications_enabled: bool
    default_model: str
    timezone: str
    settings_json: dict | None = None


class SettingsUpdate(BaseModel):
    theme: str | None = Field(default=None, pattern=r"^(light|dark|system)$")
    notifications_enabled: bool | None = None
    default_model: str | None = Field(default=None, max_length=100)
    timezone: str | None = Field(default=None, max_length=50)
    settings_json: dict | None = None


class SecretSaveRequest(BaseModel):
    key_name: str = Field(..., min_length=1, max_length=100)
    key_value: str = Field(..., min_length=1)


class SecretNameResponse(BaseModel):
    key_names: list[str]


class IntegrationStatusResponse(BaseModel):
    provider: str
    connected: bool


async def _get_or_create_settings(user_id: str, db) -> UserSettings:
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


def _settings_to_response(s: UserSettings) -> SettingsResponse:
    extra = json.loads(s.settings_json) if s.settings_json else None
    return SettingsResponse(
        theme=s.theme,
        notifications_enabled=s.notifications_enabled,
        default_model=s.default_model,
        timezone=s.timezone,
        settings_json=extra,
    )


@router.get("", response_model=SettingsResponse)
async def get_settings(current_user: CurrentUser, db: DBSession):
    """Get user settings."""
    s = await _get_or_create_settings(current_user.id, db)
    return _settings_to_response(s)


@router.patch("", response_model=SettingsResponse)
async def update_settings(body: SettingsUpdate, current_user: CurrentUser, db: DBSession):
    """Update user settings."""
    s = await _get_or_create_settings(current_user.id, db)
    updates = body.model_dump(exclude_unset=True)

    if "settings_json" in updates:
        updates["settings_json"] = json.dumps(updates["settings_json"]) if updates["settings_json"] else None

    for field, value in updates.items():
        setattr(s, field, value)

    await db.commit()
    await db.refresh(s)
    return _settings_to_response(s)


@router.get("/integrations", response_model=list[IntegrationStatusResponse])
async def list_integrations(current_user: CurrentUser, db: DBSession, request: Request):
    """List connected integrations status."""
    integration_manager = request.app.state.integration_manager
    providers = integration_manager.list_provider_names()

    result = await db.execute(
        select(IntegrationCredential.provider).where(IntegrationCredential.user_id == current_user.id)
    )
    connected_providers = set(result.scalars().all())

    return [IntegrationStatusResponse(provider=p, connected=p in connected_providers) for p in providers]


@router.post("/secrets", status_code=status.HTTP_200_OK)
async def save_secret(body: SecretSaveRequest, current_user: CurrentUser, db: DBSession):
    """Save or update an encrypted API key."""
    fernet = get_fernet()
    encrypted = fernet.encrypt(body.key_value.encode()).decode()

    result = await db.execute(
        select(IntegrationCredential).where(
            IntegrationCredential.user_id == current_user.id,
            IntegrationCredential.provider == body.key_name,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.payload_encrypted = encrypted
    else:
        cred = IntegrationCredential(
            user_id=current_user.id,
            provider=body.key_name,
            payload_encrypted=encrypted,
        )
        db.add(cred)

    await db.commit()
    return {"message": f"Secret '{body.key_name}' saved"}


@router.get("/secrets", response_model=SecretNameResponse)
async def list_secrets(current_user: CurrentUser, db: DBSession):
    """List saved secret key names (not values)."""
    result = await db.execute(
        select(IntegrationCredential.provider).where(IntegrationCredential.user_id == current_user.id)
    )
    return SecretNameResponse(key_names=list(result.scalars().all()))
