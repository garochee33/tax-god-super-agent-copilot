"""Tax God — Database Backup Script.

Copies db/taxgod.db to db/backups/ with timestamp. Keeps last 7 backups.
"""

import shutil
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "taxgod.db"
BACKUP_DIR = BASE_DIR / "db" / "backups"
MAX_BACKUPS = 7


def run_backup() -> Path:
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"taxgod_{ts}.db"
    shutil.copy2(DB_PATH, dest)

    size = dest.stat().st_size
    print(f"Backup: {dest}")
    print(f"Size: {size:,} bytes")

    # Prune old backups
    backups = sorted(BACKUP_DIR.glob("taxgod_*.db"))
    while len(backups) > MAX_BACKUPS:
        old = backups.pop(0)
        old.unlink()
        print(f"Deleted old backup: {old.name}")

    return dest


if __name__ == "__main__":
    run_backup()
