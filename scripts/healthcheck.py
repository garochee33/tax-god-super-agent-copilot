"""Tax God — Production Health Check.

Checks: DB readable, DB writable, disk space > 100MB, uploads writable.
Exits 0 (healthy) or 1 (unhealthy). Prints JSON status.
"""

import json
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "taxgod.db"
UPLOADS_DIR = BASE_DIR / "uploads"


def check_db_readable() -> dict:
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("SELECT 1")
        conn.close()
        return {"check": "db_readable", "ok": True}
    except Exception as e:
        return {"check": "db_readable", "ok": False, "error": str(e)}


def check_db_writable() -> dict:
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("CREATE TABLE IF NOT EXISTS _healthcheck (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO _healthcheck (id) VALUES (1)")
        conn.execute("DELETE FROM _healthcheck WHERE id = 1")
        conn.commit()
        conn.close()
        return {"check": "db_writable", "ok": True}
    except Exception as e:
        return {"check": "db_writable", "ok": False, "error": str(e)}


def check_disk_space() -> dict:
    usage = shutil.disk_usage(BASE_DIR)
    free_mb = usage.free / (1024 * 1024)
    ok = free_mb > 100
    return {"check": "disk_space", "ok": ok, "free_mb": round(free_mb, 1)}


def check_uploads_writable() -> dict:
    try:
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        tf = tempfile.NamedTemporaryFile(dir=UPLOADS_DIR, delete=True)
        tf.close()
        return {"check": "uploads_writable", "ok": True}
    except Exception as e:
        return {"check": "uploads_writable", "ok": False, "error": str(e)}


def main():
    results = [
        check_db_readable(),
        check_db_writable(),
        check_disk_space(),
        check_uploads_writable(),
    ]
    healthy = all(r["ok"] for r in results)
    print(json.dumps({"healthy": healthy, "checks": results}, indent=2))
    sys.exit(0 if healthy else 1)


if __name__ == "__main__":
    main()
