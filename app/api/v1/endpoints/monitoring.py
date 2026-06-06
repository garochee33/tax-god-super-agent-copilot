"""Tax God - Production Monitoring Endpoints (admin only)."""

from __future__ import annotations

import os
import shutil
import time

from fastapi import APIRouter, Request

from app.api.deps import AdminUser, DBSession
from app.core.config import get_settings
from app.core.database import check_database_health, engine

router = APIRouter()
settings = get_settings()
_start_time = time.time()


@router.get("/metrics")
async def metrics(request: Request, user: AdminUser):
    """Basic operational metrics."""
    from prometheus_client import REGISTRY

    requests_total = 0
    errors_total = 0
    for m in REGISTRY.collect():
        if m.name == "taxgod_http_requests_total":
            for sample in m.samples:
                requests_total += int(sample.value)
                if sample.labels.get("status_code", "").startswith("5"):
                    errors_total += int(sample.value)

    db_size = 0
    db_url = settings.DATABASE_URL
    if "sqlite" in db_url:
        db_path = db_url.split("///")[-1] if "///" in db_url else "db/taxgod.db"
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path)

    return {
        "requests_total": requests_total,
        "errors_total": errors_total,
        "active_users": 0,
        "db_size_bytes": db_size,
        "uptime_seconds": round(time.time() - _start_time, 1),
    }


@router.get("/status")
async def status(request: Request, user: AdminUser):
    """Detailed service status for production monitoring."""
    db_ok = await check_database_health(engine)
    disk = shutil.disk_usage("/")
    return {
        "database": {"ok": db_ok},
        "ai_keys_configured": bool(settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY),
        "stripe_configured": bool(settings.STRIPE_SECRET_KEY),
        "plaid_configured": bool(os.environ.get("PLAID_CLIENT_ID")),
        "disk": {
            "total_gb": round(disk.total / (1024**3), 1),
            "free_gb": round(disk.free / (1024**3), 1),
            "used_percent": round((disk.used / disk.total) * 100, 1),
        },
    }
