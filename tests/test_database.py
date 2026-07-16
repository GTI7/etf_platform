from __future__ import annotations

import sqlite3


def test_wal_mode_enabled(conn: sqlite3.Connection) -> None:
    mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
    assert mode.lower() == "wal"


def test_isolation_level_is_explicit_legacy_mode(conn: sqlite3.Connection) -> None:
    """The whole project's rollback/atomicity model depends on this legacy
    (non-autocommit) transaction mode -- see connect()'s docstring."""
    assert conn.isolation_level == ""


def test_uncommitted_write_rolls_back(conn: sqlite3.Connection) -> None:
    """Direct proof of the property every pipeline's atomicity guarantee
    depends on: a DML statement outside an explicit `with conn:` block is
    not committed, and conn.rollback() discards it."""
    conn.execute(
        "INSERT INTO Calendar (calendar_id, name, exchange, timezone) VALUES (?, ?, ?, ?)",
        ("TEST", "Test Calendar", "TEST", "UTC"),
    )
    conn.rollback()

    row = conn.execute(
        "SELECT COUNT(*) AS n FROM Calendar WHERE calendar_id = ?", ("TEST",)
    ).fetchone()
    assert row["n"] == 0
