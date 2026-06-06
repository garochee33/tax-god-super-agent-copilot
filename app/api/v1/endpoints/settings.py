"""Tax God - Admin Settings Endpoint (manage .env keys from UI)"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import AdminUser

router = APIRouter()

# Keys that can be managed from the UI (grouped by section)
MANAGED_KEYS = {
    "ai": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"],
    "stripe": ["STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE_MONTHLY"],
    "database": ["DATABASE_URL", "REDIS_URL"],
    "integrations": [
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REDIRECT_URI",
        "QUICKBOOKS_CLIENT_ID",
        "QUICKBOOKS_CLIENT_SECRET",
        "QUICKBOOKS_REDIRECT_URI",
        "INTEGRATION_ENCRYPTION_KEY",
    ],
    "outreach": ["SENDGRID_API_KEY", "APOLLO_API_KEY"],
    "app": ["SECRET_KEY", "ENVIRONMENT", "DEBUG", "LOG_LEVEL"],
}

ENV_PATH = Path(__file__).resolve().parents[4] / ".env"


def _mask(value: str) -> str:
    """Mask sensitive values, showing only last 4 chars."""
    if not value or len(value) <= 8:
        return "••••" if value else ""
    return f"••••••••{value[-4:]}"


def _read_env() -> dict[str, str]:
    """Read current .env file into dict."""
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip()
    return env


def _write_env(env: dict[str, str]) -> None:
    """Write dict back to .env preserving comments and order."""
    lines = []
    if ENV_PATH.exists():
        written_keys = set()
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
        # Append any new keys not in original file
        for key, val in env.items():
            if key not in written_keys:
                lines.append(f"{key}={val}")
    else:
        for key, val in env.items():
            lines.append(f"{key}={val}")
    ENV_PATH.write_text("\n".join(lines) + "\n")


class SettingsResponse(BaseModel):
    sections: dict[str, dict[str, str]]


class SettingsUpdateRequest(BaseModel):
    updates: dict[str, str]


@router.get("", response_model=SettingsResponse)
async def get_settings(user: AdminUser):
    """Get all manageable settings (masked)."""
    env = _read_env()
    sensitive_prefixes = ("sk_", "sk-", "pk_", "whsec_", "price_")
    sensitive_keys = {"SECRET_KEY", "INTEGRATION_ENCRYPTION_KEY", "DATABASE_URL", "REDIS_URL"}

    sections = {}
    for section, keys in MANAGED_KEYS.items():
        sections[section] = {}
        for key in keys:
            val = env.get(key, os.environ.get(key, ""))
            if key in sensitive_keys or any(val.startswith(p) for p in sensitive_prefixes):
                sections[section][key] = _mask(val)
            else:
                sections[section][key] = val
    return SettingsResponse(sections=sections)


@router.put("")
async def update_settings(body: SettingsUpdateRequest, user: AdminUser):
    """Update settings in .env file. Only allowed keys can be set."""
    all_allowed = {k for keys in MANAGED_KEYS.values() for k in keys}
    invalid = set(body.updates.keys()) - all_allowed
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Keys not allowed: {sorted(invalid)}",
        )

    env = _read_env()
    changed = []
    for key, val in body.updates.items():
        if val and val != env.get(key, ""):
            env[key] = val
            changed.append(key)

    if changed:
        _write_env(env)
        # Also update current process env so changes take effect without restart
        for key in changed:
            os.environ[key] = env[key]

    return {"updated": changed, "message": f"{len(changed)} key(s) updated. Restart server for full effect."}
