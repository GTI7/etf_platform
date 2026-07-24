from __future__ import annotations

from pathlib import Path

import pytest

from core.store.connection import connect
from core.store.migrations import run_migrations

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "etf_platform_test.db"


@pytest.fixture
def conn(db_path: Path):
    connection = connect(db_path)
    run_migrations(connection, MIGRATIONS_DIR)
    yield connection
    connection.close()
