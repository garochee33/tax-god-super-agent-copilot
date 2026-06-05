"""Tax God - Advanced Settings Endpoints (10 upgrades)

1. Key rotation
2. Connection test
3. Audit log (on PUT)
4. Role-based visibility
5. Keychain store/status
6. Auto-restart (SIGHUP)
7. Import/Export encrypted .env
8. Stripe webhook auto-register
9. Expiry alerts
10. Multi-environment profiles
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import signal
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from cryptography.fernet import Fernet
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import AdminUser, CurrentUser
from app.models.user import UserRole

router = APIRouter()

ENV_PATH = Path(__file__).resolve().parents[4] / ".env"
KEY_ROTATION_FILE = Path(__file__).resolve().parents[4] / ".key_rotations.json"
MANAGED_KEYS = {
    "ai": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"],
    "stripe": ["STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE_MONTHLY"],
    "database": ["DATABASE_URL", "REDIS_URL"],
    "integrations": [
        "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI",
        "QUICKBOOKS_CLIENT_ID", "QUICKBOOKS_CLIENT_SECRET", "QUICKBOOKS_REDIRECT_URI",
        "INTEGRATION_ENCRYPTION_KEY",
    ],
    "outreach": ["SENDGRID_API_KEY", "APOLLO_API_KEY"],
    "app": ["SECRET_KEY", "ENVIRONMENT", "DEBUG", "LOG_LEVEL"],
}


def _read_env() -> dict[str, str]:
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip()
    return env


def _write_env(env: dict[str, str]) -> None:
    lines = []
    if ENV_PATH.exists():
        written_keys: set[str] = set()
        for line in ENV_PATH.read_text().splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key = stripped.partition("=")[0].strip()
                if key in env:
                    lines.append(f"{key}={env[key]}")
                    written_keys.add(key)
                else:
                    lines.append(line)
            else:
                lines.append(line)
        for key, val in env.items():
            if key not in written_keys:
                lines.append(f"{key}={val}")
    else:
        for key, val in env.items():
            lines.append(f"{key}={val}")
    ENV_PATH.write_text("\n".join(lines) + "\n")


def _mask(value: str) -> str:
    if not value or len(value) <= 8:
        return "••••" if value else ""
    return f"••••••••{value[-4:]}"


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def _load_rotations() -> dict:
    if KEY_ROTATION_FILE.exists():
        return json.loads(KEY_ROTATION_FILE.read_text())
    return {}


def _save_rotations(data: dict) -> None:
    KEY_ROTATION_FILE.write_text(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# 1. KEY ROTATION
# ---------------------------------------------------------------------------

class RotateRequest(BaseModel):
    key: str = "SECRET_KEY"


@router.post("/rotate")
async def rotate_key(body: RotateRequest, user: AdminUser):
    """Auto-generate new value for SECRET_KEY or INTEGRATION_ENCRYPTION_KEY."""
    env = _read_env()
    if body.key == "SECRET_KEY":
        new_val = os.urandom(32).hex()
    elif body.key == "INTEGRATION_ENCRYPTION_KEY":
        new_val = Fernet.generate_key().decode()
    else:
        raise HTTPException(status_code=400, detail="Only SECRET_KEY and INTEGRATION_ENCRYPTION_KEY can be rotated")

    env[body.key] = new_val
    _write_env(env)
    os.environ[body.key] = new_val

    # Track rotation timestamp
    rotations = _load_rotations()
    rotations[body.key] = datetime.now(UTC).isoformat()
    _save_rotations(rotations)

    return {"key": body.key, "new_masked_value": _mask(new_val)}


# ---------------------------------------------------------------------------
# 2. CONNECTION TEST
# ---------------------------------------------------------------------------

class ConnectionTestRequest(BaseModel):
    key: str


@router.post("/test-connection")
async def test_connection(body: ConnectionTestRequest, user: AdminUser):
    """Test connectivity for a given key (OpenAI, Redis, Stripe, DB)."""
    key = body.key
    try:
        if key == "OPENAI_API_KEY":
            import openai
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
            client.models.list()
            return {"key": key, "status": "ok", "detail": "Listed models successfully"}

        elif key == "REDIS_URL":
            import redis
            r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
            r.ping()
            r.close()
            return {"key": key, "status": "ok", "detail": "PONG"}

        elif key == "STRIPE_SECRET_KEY":
            import stripe
            stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
            stripe.Customer.list(limit=1)
            return {"key": key, "status": "ok", "detail": "Listed customers"}

        elif key == "DATABASE_URL":
            from sqlalchemy import text
            from app.core.database import engine
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return {"key": key, "status": "ok", "detail": "SELECT 1 succeeded"}

        else:
            raise HTTPException(status_code=400, detail=f"No test available for key: {key}")
    except HTTPException:
        raise
    except Exception as e:
        return {"key": key, "status": "error", "detail": str(e)}


# ---------------------------------------------------------------------------
# 3. AUDIT LOG (helper — called from PUT override below)
# ---------------------------------------------------------------------------

async def _log_audit(user_id: str, key_name: str, action: str, old_val: str, new_val: str):
    """Log a settings change to the audit table."""
    from app.core.database import async_session_factory
    from app.models.settings_audit import SettingsAuditLog
    async with async_session_factory() as session:
        entry = SettingsAuditLog(
            user_id=user_id,
            key_name=key_name,
            action=action,
            old_value_hash=_hash_value(old_val) if old_val else None,
            new_value_hash=_hash_value(new_val) if new_val else None,
        )
        session.add(entry)
        await session.commit()


class SettingsUpdateRequest(BaseModel):
    updates: dict[str, str]


@router.put("")
async def update_settings_with_audit(body: SettingsUpdateRequest, user: AdminUser):
    """Update settings with audit logging."""
    all_allowed = {k for keys in MANAGED_KEYS.values() for k in keys}
    invalid = set(body.updates.keys()) - all_allowed
    if invalid:
        raise HTTPException(status_code=400, detail=f"Keys not allowed: {sorted(invalid)}")

    env = _read_env()
    changed = []
    for key, val in body.updates.items():
        if val and val != env.get(key, ""):
            old = env.get(key, "")
            env[key] = val
            changed.append(key)
            await _log_audit(user.id, key, "update", old, val)

    if changed:
        _write_env(env)
        for key in changed:
            os.environ[key] = env[key]

    return {"updated": changed, "message": f"{len(changed)} key(s) updated with audit trail."}


# ---------------------------------------------------------------------------
# 4. ROLE-BASED VISIBILITY
# ---------------------------------------------------------------------------

class SettingsResponse(BaseModel):
    sections: dict[str, dict[str, str]]


@router.get("", response_model=SettingsResponse)
async def get_settings_rbac(user: CurrentUser):
    """Get settings — preparers see only app+integrations; admins see all."""
    env = _read_env()
    sensitive_prefixes = ("sk_", "sk-", "pk_", "whsec_", "price_")
    sensitive_keys = {"SECRET_KEY", "INTEGRATION_ENCRYPTION_KEY", "DATABASE_URL", "REDIS_URL"}

    if user.role == UserRole.PREPARER.value:
        visible_sections = {"app", "integrations"}
    else:
        visible_sections = set(MANAGED_KEYS.keys())

    sections: dict[str, dict[str, str]] = {}
    for section, keys in MANAGED_KEYS.items():
        if section not in visible_sections:
            continue
        sections[section] = {}
        for key in keys:
            val = env.get(key, os.environ.get(key, ""))
            if key in sensitive_keys or any(val.startswith(p) for p in sensitive_prefixes):
                sections[section][key] = _mask(val)
            else:
                sections[section][key] = val
    return SettingsResponse(sections=sections)


# ---------------------------------------------------------------------------
# 5. ENCRYPTED AT REST — macOS Keychain
# ---------------------------------------------------------------------------

class KeychainStoreRequest(BaseModel):
    key: str
    value: str


@router.post("/keychain/store")
async def keychain_store(body: KeychainStoreRequest, user: AdminUser):
    """Store a secret in macOS Keychain using security CLI."""
    try:
        # Delete existing first (ignore errors)
        subprocess.run(
            ["security", "delete-generic-password", "-s", f"taxgod-{body.key}"],
            capture_output=True,
        )
        result = subprocess.run(
            ["security", "add-generic-password", "-s", f"taxgod-{body.key}",
             "-a", "taxgod", "-w", body.value],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Keychain error: {result.stderr}")
        return {"status": "stored", "key": body.key}
    except FileNotFoundError:
        raise HTTPException(status_code=501, detail="macOS security CLI not available")


@router.get("/keychain/status")
async def keychain_status(user: AdminUser):
    """Check which keys are stored in keychain."""
    keys_to_check = ["SECRET_KEY", "INTEGRATION_ENCRYPTION_KEY", "OPENAI_API_KEY", "STRIPE_SECRET_KEY"]
    results = {}
    for key in keys_to_check:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", f"taxgod-{key}", "-w"],
            capture_output=True, text=True,
        )
        results[key] = result.returncode == 0
    return {"keychain_keys": results}


# ---------------------------------------------------------------------------
# 6. AUTO-RESTART
# ---------------------------------------------------------------------------

@router.post("/restart")
async def restart_server(user: AdminUser):
    """Send SIGHUP to uvicorn parent to trigger reload."""
    ppid = os.getppid()
    try:
        os.kill(ppid, signal.SIGHUP)
        return {"status": "restart_signal_sent", "pid": ppid}
    except ProcessLookupError:
        raise HTTPException(status_code=500, detail="Parent process not found")
    except PermissionError:
        raise HTTPException(status_code=500, detail="Permission denied sending signal")


# ---------------------------------------------------------------------------
# 7. IMPORT / EXPORT
# ---------------------------------------------------------------------------

def _get_fernet() -> Fernet:
    secret = os.environ.get("SECRET_KEY", "CHANGE-ME-IN-PRODUCTION")
    # Derive 32-byte key from SECRET_KEY via sha256, then base64 for Fernet
    derived = hashlib.sha256(secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(derived))


@router.get("/export")
async def export_settings(user: AdminUser):
    """Export .env encrypted with SECRET_KEY as base64."""
    if not ENV_PATH.exists():
        raise HTTPException(status_code=404, detail=".env file not found")
    content = ENV_PATH.read_bytes()
    f = _get_fernet()
    encrypted = f.encrypt(content)
    return {"payload": base64.b64encode(encrypted).decode()}


class ImportRequest(BaseModel):
    payload: str


@router.post("/import")
async def import_settings(body: ImportRequest, user: AdminUser):
    """Import encrypted .env payload, decrypt and write."""
    try:
        encrypted = base64.b64decode(body.payload)
        f = _get_fernet()
        decrypted = f.decrypt(encrypted)
        ENV_PATH.write_bytes(decrypted)
        return {"status": "imported", "bytes_written": len(decrypted)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decryption failed: {e}")


# ---------------------------------------------------------------------------
# 8. STRIPE WEBHOOK AUTO-REGISTER
# ---------------------------------------------------------------------------

class StripeWebhookRequest(BaseModel):
    url: str | None = None


@router.post("/stripe/register-webhook")
async def stripe_register_webhook(body: StripeWebhookRequest, user: AdminUser):
    """Register a Stripe webhook endpoint for this app."""
    try:
        import stripe
        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
        if not stripe.api_key:
            raise HTTPException(status_code=400, detail="STRIPE_SECRET_KEY not configured")

        app_url = body.url or os.environ.get("APP_URL", "http://localhost:8000")
        webhook_url = f"{app_url}/api/v1/billing/webhook"

        endpoint = stripe.WebhookEndpoint.create(
            url=webhook_url,
            enabled_events=[
                "checkout.session.completed",
                "customer.subscription.updated",
                "customer.subscription.deleted",
                "invoice.payment_succeeded",
                "invoice.payment_failed",
            ],
        )
        return {"status": "created", "id": endpoint.id, "url": webhook_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# 9. EXPIRY ALERTS
# ---------------------------------------------------------------------------

@router.get("/alerts")
async def expiry_alerts(user: AdminUser):
    """Check key ages; warn if not rotated in 90+ days."""
    rotations = _load_rotations()
    now = datetime.now(UTC)
    alerts = []
    keys_to_check = ["SECRET_KEY", "INTEGRATION_ENCRYPTION_KEY", "OPENAI_API_KEY", "STRIPE_SECRET_KEY"]

    for key in keys_to_check:
        last_rotated = rotations.get(key)
        if not last_rotated:
            alerts.append({"key": key, "severity": "warning", "message": "Never rotated — rotation date unknown"})
        else:
            dt = datetime.fromisoformat(last_rotated)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            days_ago = (now - dt).days
            if days_ago >= 90:
                alerts.append({"key": key, "severity": "critical", "message": f"Last rotated {days_ago} days ago"})

    return {"alerts": alerts, "checked_keys": keys_to_check}


# ---------------------------------------------------------------------------
# 10. MULTI-ENVIRONMENT PROFILES
# ---------------------------------------------------------------------------

PROFILE_DIR = ENV_PATH.parent
VALID_PROFILES = ["development", "staging", "production"]


class ProfileSwitchRequest(BaseModel):
    profile: str


@router.get("/profiles")
async def get_profiles(user: AdminUser):
    """List available environment profiles."""
    profiles = {}
    for name in VALID_PROFILES:
        path = PROFILE_DIR / f".env.{name}"
        profiles[name] = {"exists": path.exists(), "path": str(path)}
    active = _read_env().get("ENVIRONMENT", "development")
    return {"profiles": profiles, "active": active}


@router.put("/profiles")
async def switch_profile(body: ProfileSwitchRequest, user: AdminUser):
    """Switch environment profile by copying .env.<profile> to .env."""
    if body.profile not in VALID_PROFILES:
        raise HTTPException(status_code=400, detail=f"Invalid profile. Choose from: {VALID_PROFILES}")

    source = PROFILE_DIR / f".env.{body.profile}"
    if not source.exists():
        # Create from current .env as template
        if ENV_PATH.exists():
            shutil.copy2(ENV_PATH, source)
        else:
            raise HTTPException(status_code=404, detail=f".env.{body.profile} not found")

    # Backup current
    backup = PROFILE_DIR / ".env.backup"
    if ENV_PATH.exists():
        shutil.copy2(ENV_PATH, backup)

    shutil.copy2(source, ENV_PATH)
    return {"status": "switched", "profile": body.profile, "backup": str(backup)}
