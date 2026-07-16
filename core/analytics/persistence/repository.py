"""Repository functions for the analytics persistence layer.

Same convention as core/market_data/persistence/repository.py: these
functions only execute SQL against the connection they are given -- none
of them commit. The caller owns the transaction boundary.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal

from core.analytics.domain.models import IndicatorDefinition, IndicatorValue


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def insert_indicator_definition(conn: sqlite3.Connection, definition: IndicatorDefinition) -> None:
    conn.execute(
        """
        INSERT INTO IndicatorDefinition (
            indicator_definition_id, name, version, parameters, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            definition.indicator_definition_id,
            definition.name,
            definition.version,
            definition.parameters,
            _iso(definition.created_at),
        ),
    )


def get_indicator_definition(
    conn: sqlite3.Connection, name: str, version: int
) -> IndicatorDefinition | None:
    row = conn.execute(
        """
        SELECT indicator_definition_id, name, version, parameters, created_at
        FROM IndicatorDefinition
        WHERE name = ? AND version = ?
        """,
        (name, version),
    ).fetchone()
    if row is None:
        return None
    return IndicatorDefinition(
        indicator_definition_id=row["indicator_definition_id"],
        name=row["name"],
        version=row["version"],
        parameters=row["parameters"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def insert_indicator_value(conn: sqlite3.Connection, value: IndicatorValue) -> None:
    """Idempotent insert: a rerun for the same (definition, etf, session)
    is a silent no-op, never a duplicate row and never an overwrite."""
    conn.execute(
        """
        INSERT INTO IndicatorValue (
            indicator_value_id, indicator_definition_id, etf_id,
            session_date, value, computed_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT (indicator_definition_id, etf_id, session_date) DO NOTHING
        """,
        (
            value.indicator_value_id,
            value.indicator_definition_id,
            value.etf_id,
            value.session_date.isoformat(),
            str(value.value),
            _iso(value.computed_at),
        ),
    )


def get_indicator_values(
    conn: sqlite3.Connection,
    indicator_definition_id: str,
    etf_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[IndicatorValue]:
    query = (
        "SELECT * FROM IndicatorValue WHERE indicator_definition_id = ? AND etf_id = ?"
    )
    params: list[object] = [indicator_definition_id, etf_id]
    if start_date is not None:
        query += " AND session_date >= ?"
        params.append(start_date.isoformat())
    if end_date is not None:
        query += " AND session_date <= ?"
        params.append(end_date.isoformat())
    query += " ORDER BY session_date"
    rows = conn.execute(query, params).fetchall()
    return [
        IndicatorValue(
            indicator_value_id=row["indicator_value_id"],
            indicator_definition_id=row["indicator_definition_id"],
            etf_id=row["etf_id"],
            session_date=date.fromisoformat(row["session_date"]),
            value=Decimal(row["value"]),
            computed_at=datetime.fromisoformat(row["computed_at"]),
        )
        for row in rows
    ]
