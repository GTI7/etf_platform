"""Migration-runner primitive. Moved verbatim from
``core/market_data/persistence/migrations.py`` by AD-069; that module now
re-exports this one for the frozen Phase-0 scripts that may not be
edited. Behavior is unchanged -- this is a relocation, not a rewrite.

The runner is neutral about *what* the SQL creates: it takes the
migrations directory as an argument and knows only the
``schema_migrations`` ledger it owns.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# See migrations/README.md for the migration policy: once a real database
# has been created from a migration file, that file is frozen forever and
# all further schema changes ship as new, additive migration files.


def run_migrations(conn: sqlite3.Connection, migrations_dir: str | Path) -> list[str]:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )
    conn.commit()

    applied = {row["version"] for row in conn.execute("SELECT version FROM schema_migrations")}

    migrations_dir = Path(migrations_dir)
    migration_files = sorted(migrations_dir.glob("*.sql"))

    newly_applied: list[str] = []
    for migration_file in migration_files:
        version = migration_file.name
        if version in applied:
            continue
        sql = migration_file.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
            (version, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        newly_applied.append(version)

    return newly_applied
