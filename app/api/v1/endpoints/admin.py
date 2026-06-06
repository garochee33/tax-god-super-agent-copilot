"""Tax God — Admin Endpoints (backup, db-stats)."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser, get_db

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[4]
DB_PATH = BASE_DIR / "db" / "taxgod.db"
BACKUP_DIR = BASE_DIR / "db" / "backups"
MAX_BACKUPS = 7


@router.post("/admin/backup")
async def trigger_backup(user: AdminUser):
    """Trigger a database backup (admin only)."""
    if not DB_PATH.exists():
        raise HTTPException(status_code=500, detail="Database file not found")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"taxgod_{ts}.db"
    shutil.copy2(DB_PATH, dest)

    # Prune old backups
    backups = sorted(BACKUP_DIR.glob("taxgod_*.db"))
    while len(backups) > MAX_BACKUPS:
        backups.pop(0).unlink()

    return {"filename": dest.name, "size_bytes": dest.stat().st_size}


@router.get("/admin/db-stats")
async def db_stats(user: AdminUser, db: AsyncSession = Depends(get_db)):
    """Return table row counts and DB file size."""
    result = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
    tables = [r[0] for r in result.fetchall()]

    counts = {}
    for t in tables:
        row = await db.execute(text(f"SELECT COUNT(*) FROM [{t}]"))  # noqa: S608
        counts[t] = row.scalar()

    db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
    return {"db_size_bytes": db_size, "tables": counts}
