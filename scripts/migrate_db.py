"""Tax God — Simple SQL Migration System.

Reads .sql files from db/migrations/ in sorted order.
Tracks applied migrations in a _migrations table.
Supports rollback via 001_name.down.sql naming.
"""

import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "taxgod.db"
MIGRATIONS_DIR = BASE_DIR / "db" / "migrations"


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS _migrations ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "name TEXT UNIQUE NOT NULL, "
        "applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.commit()
    return conn


def applied_migrations(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM _migrations").fetchall()
    return {r[0] for r in rows}


def migrate():
    conn = get_connection()
    applied = applied_migrations(conn)
    up_files = sorted(MIGRATIONS_DIR.glob("*.up.sql"))

    if not up_files:
        print("No migration files found.")
        return

    count = 0
    for f in up_files:
        if f.name in applied:
            continue
        print(f"Applying: {f.name}")
        sql = f.read_text()
        conn.executescript(sql)
        conn.execute("INSERT INTO _migrations (name) VALUES (?)", (f.name,))
        conn.commit()
        count += 1

    print(f"Done. Applied {count} migration(s).")
    conn.close()


def rollback(target: str | None = None):
    conn = get_connection()
    applied = applied_migrations(conn)

    if target:
        down_files = [MIGRATIONS_DIR / target]
    else:
        # Rollback last applied migration
        up_files = sorted(MIGRATIONS_DIR.glob("*.up.sql"))
        last_applied = [f for f in up_files if f.name in applied]
        if not last_applied:
            print("Nothing to rollback.")
            conn.close()
            return
        last = last_applied[-1]
        down_files = [last.with_suffix("").with_suffix(".down.sql")]

    for df in down_files:
        if not df.exists():
            print(f"ERROR: Down file not found: {df.name}", file=sys.stderr)
            conn.close()
            sys.exit(1)
        up_name = df.name.replace(".down.sql", ".up.sql")
        print(f"Rolling back: {up_name}")
        sql = df.read_text()
        conn.executescript(sql)
        conn.execute("DELETE FROM _migrations WHERE name = ?", (up_name,))
        conn.commit()

    print("Rollback complete.")
    conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        target = sys.argv[2] if len(sys.argv) > 2 else None
        rollback(target)
    else:
        migrate()
