"""Tax God API - Two-Factor Authentication Endpoints"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import CurrentUser, DBSession
from app.services.totp_service import generate_provisioning_uri, generate_secret, verify_totp

router = APIRouter()


class TOTPVerifyRequest(BaseModel):
    code: str


class TOTPSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


@router.post("/2fa/setup", response_model=TOTPSetupResponse)
async def setup_2fa(db: DBSession, current_user: CurrentUser):
    """Generate TOTP secret and provisioning URI."""
    if current_user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA already enabled")
    secret = generate_secret()
    current_user.totp_secret = secret
    await db.commit()
    uri = generate_provisioning_uri(secret, current_user.email)
    return TOTPSetupResponse(secret=secret, provisioning_uri=uri)


@router.post("/2fa/verify")
async def verify_2fa(body: TOTPVerifyRequest, db: DBSession, current_user: CurrentUser):
    """Verify TOTP code to enable 2FA."""
    if not current_user.totp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Run /2fa/setup first")
    if not verify_totp(current_user.totp_secret, body.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")
    current_user.totp_enabled = True
    await db.commit()
    return {"message": "2FA enabled successfully"}


@router.post("/2fa/disable")
async def disable_2fa(body: TOTPVerifyRequest, db: DBSession, current_user: CurrentUser):
    """Disable 2FA (requires current TOTP code)."""
    if not current_user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA not enabled")
    if not verify_totp(current_user.totp_secret, body.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")
    current_user.totp_enabled = False
    current_user.totp_secret = None
    await db.commit()
    return {"message": "2FA disabled"}
