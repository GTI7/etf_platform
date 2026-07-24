"""Behavior of the ``core.store`` primitives at their new home (AD-069).

Renamed from ``tests/test_database.py``, whose subject moved to
``core/store/connection.py``; the old name pointed at what is now a
re-export shim. The ``conn`` fixture already reaches ``core.store``, so
the rename records a coverage relationship that was already true.

The relocation was verbatim, which is exactly why the moved behavior is
pinned here directly rather than left to be exercised incidentally
through the fixture: a verbatim move deserves a direct assertion at its
destination.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from core.store.connection import connect
from core.store.migrations import run_migrations

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


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


def test_foreign_keys_pragma_is_on(conn: sqlite3.Connection) -> None:
    """T-4. ``connect()`` sets ``PRAGMA foreign_keys=ON`` and, until this
    test, nothing asserted it -- while
    ``core/governance/reconstruction_loader.py`` calls that pragma
    load-bearing ("the load-order bug v1.0 had and v1.1 corrects").
    sqlite3 defaults this pragma to OFF and it is per-connection, so a
    dropped line here would silently disable every FK constraint in the
    schema without failing anything else. The relocation is the moment to
    pin it."""
    assert conn.execute("PRAGMA foreign_keys;").fetchone()[0] == 1


def test_foreign_key_violation_is_actually_rejected(conn: sqlite3.Connection) -> None:
    """T-4, behavioral half. The pragma being reported ON is one thing;
    the constraint being enforced is the property that matters.

    Every NOT NULL column is supplied and only ``calendar_id`` dangles, so
    the rejection can only be the foreign key -- a partial row would raise
    ``IntegrityError`` for a NOT NULL violation instead and the test would
    pass with the pragma off."""
    try:
        with pytest.raises(sqlite3.IntegrityError) as excinfo:
            conn.execute(
                "INSERT INTO ETF "
                "(etf_id, ticker, name, currency, calendar_id, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("E1", "TEST", "Test ETF", "USD", "NO_SUCH_CALENDAR", "2026-07-24T00:00:00Z"),
            )
    finally:
        conn.rollback()

    assert "FOREIGN KEY" in str(excinfo.value).upper()


def test_run_migrations_creates_the_ledger_and_is_idempotent(db_path: Path) -> None:
    """T-7. ``run_migrations`` behavioral parity at its new home: it owns
    the ``schema_migrations`` ledger, returns the versions it newly
    applied, and applies each file exactly once. The idempotence is what
    migrations/README.md's "applied exactly once, tracked by filename"
    policy rests on, and a second run returning anything but an empty
    list would mean a migration is being re-executed."""
    connection = connect(db_path)
    try:
        first = run_migrations(connection, MIGRATIONS_DIR)

        assert first, "expected at least one migration to be applied"
        ledger = [
            row["version"]
            for row in connection.execute("SELECT version FROM schema_migrations")
        ]
        assert sorted(ledger) == sorted(first)

        second = run_migrations(connection, MIGRATIONS_DIR)

        assert second == []
        assert (
            connection.execute("SELECT COUNT(*) AS n FROM schema_migrations").fetchone()["n"]
            == len(first)
        )
    finally:
        connection.close()


def test_run_migrations_applies_files_in_sorted_order(db_path: Path) -> None:
    """T-7, ordering half. Ordering is ``sorted()`` over the directory
    glob, which is what makes the numeric filename prefixes meaningful --
    a later migration may depend on an earlier one having run."""
    connection = connect(db_path)
    try:
        applied = run_migrations(connection, MIGRATIONS_DIR)
    finally:
        connection.close()

    assert applied == sorted(applied)
    assert applied == sorted(path.name for path in MIGRATIONS_DIR.glob("*.sql"))
