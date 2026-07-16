from __future__ import annotations

import sqlite3
from pathlib import Path


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a connection configured for this project's transaction model.

    isolation_level="" is passed explicitly -- it is also sqlite3's
    default, so this preserves existing behavior exactly. It is made
    explicit here because it is load-bearing: every rollback guarantee in
    this project (run_pipeline's atomic commit/rollback, every repository
    function's "never commit internally" contract) depends on this
    specific legacy/implicit transaction mode, where a transaction opens
    before the first DML statement and stays open until an explicit
    .commit()/.rollback(). Changing this value (e.g. to autocommit mode)
    would silently break those guarantees without any single test
    necessarily catching it, since every test connects the same way.
    """
    conn = sqlite3.connect(db_path, isolation_level="")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn
