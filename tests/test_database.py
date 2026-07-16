from __future__ import annotations

import sqlite3


def test_wal_mode_enabled(conn: sqlite3.Connection) -> None:
    mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
    assert mode.lower() == "wal"
