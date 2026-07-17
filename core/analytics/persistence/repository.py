"""Repository functions for the analytics persistence layer.

Same convention as core/market_data/persistence/repository.py: these
functions only execute SQL against the connection they are given -- none
of them commit. The caller owns the transaction boundary.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal

from core.analytics.domain.models import (
    Dimension,
    DimensionScore,
    IndicatorDefinition,
    IndicatorValue,
    Score,
    ScoringProfile,
)


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


def insert_scoring_profile(conn: sqlite3.Connection, profile: ScoringProfile) -> None:
    conn.execute(
        """
        INSERT INTO ScoringProfile (
            scoring_profile_id, name, version, parameters, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            profile.scoring_profile_id,
            profile.name,
            profile.version,
            profile.parameters,
            _iso(profile.created_at),
        ),
    )


def get_scoring_profile(conn: sqlite3.Connection, name: str, version: int) -> ScoringProfile | None:
    row = conn.execute(
        """
        SELECT scoring_profile_id, name, version, parameters, created_at
        FROM ScoringProfile
        WHERE name = ? AND version = ?
        """,
        (name, version),
    ).fetchone()
    if row is None:
        return None
    return ScoringProfile(
        scoring_profile_id=row["scoring_profile_id"],
        name=row["name"],
        version=row["version"],
        parameters=row["parameters"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def get_score(
    conn: sqlite3.Connection, etf_id: str, scoring_profile_id: str, session_date: date
) -> Score | None:
    row = conn.execute(
        """
        SELECT score_id, etf_id, scoring_profile_id, session_date, overall_score, computed_at
        FROM Score
        WHERE etf_id = ? AND scoring_profile_id = ? AND session_date = ?
        """,
        (etf_id, scoring_profile_id, session_date.isoformat()),
    ).fetchone()
    if row is None:
        return None
    return Score(
        score_id=row["score_id"],
        etf_id=row["etf_id"],
        scoring_profile_id=row["scoring_profile_id"],
        session_date=date.fromisoformat(row["session_date"]),
        overall_score=Decimal(row["overall_score"]),
        computed_at=datetime.fromisoformat(row["computed_at"]),
    )


def insert_score(conn: sqlite3.Connection, score: Score) -> None:
    """Idempotent insert, as a defense-in-depth backstop: the primary
    idempotency mechanism is the orchestration layer calling get_score()
    before computing anything (see core/analytics/scoring_pipeline.py),
    so this ON CONFLICT should only ever matter for a genuine race."""
    conn.execute(
        """
        INSERT INTO Score (
            score_id, etf_id, scoring_profile_id, session_date, overall_score, computed_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT (etf_id, scoring_profile_id, session_date) DO NOTHING
        """,
        (
            score.score_id,
            score.etf_id,
            score.scoring_profile_id,
            score.session_date.isoformat(),
            str(score.overall_score),
            _iso(score.computed_at),
        ),
    )


def insert_dimension_score(conn: sqlite3.Connection, dimension_score: DimensionScore) -> None:
    conn.execute(
        """
        INSERT INTO DimensionScore (score_id, dimension, value, computed_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            dimension_score.score_id,
            dimension_score.dimension.value,
            str(dimension_score.value),
            _iso(dimension_score.computed_at),
        ),
    )


def get_scores_for_session(
    conn: sqlite3.Connection, scoring_profile_id: str, session_date: date
) -> list[Score]:
    """Every Score for the given profile and session, across all ETFs.

    Fetch only -- no ORDER BY expressing rank. Ranking is a business rule
    and belongs in core/analytics/domain/ranking.py, not in this query."""
    rows = conn.execute(
        """
        SELECT score_id, etf_id, scoring_profile_id, session_date, overall_score, computed_at
        FROM Score
        WHERE scoring_profile_id = ? AND session_date = ?
        """,
        (scoring_profile_id, session_date.isoformat()),
    ).fetchall()
    return [
        Score(
            score_id=row["score_id"],
            etf_id=row["etf_id"],
            scoring_profile_id=row["scoring_profile_id"],
            session_date=date.fromisoformat(row["session_date"]),
            overall_score=Decimal(row["overall_score"]),
            computed_at=datetime.fromisoformat(row["computed_at"]),
        )
        for row in rows
    ]


def get_scores_for_etf(
    conn: sqlite3.Connection,
    etf_id: str,
    scoring_profile_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[Score]:
    """Every Score for one ETF/profile, optionally restricted to a
    session_date range -- the historical counterpart to
    get_scores_for_session()'s single-session/all-ETFs view.

    Ordered by session_date: unlike get_scores_for_session() (a single
    session has no inherent order across ETFs), a history is only
    meaningful in date order.
    """
    query = "SELECT score_id, etf_id, scoring_profile_id, session_date, overall_score, computed_at FROM Score WHERE etf_id = ? AND scoring_profile_id = ?"
    params: list[object] = [etf_id, scoring_profile_id]
    if start_date is not None:
        query += " AND session_date >= ?"
        params.append(start_date.isoformat())
    if end_date is not None:
        query += " AND session_date <= ?"
        params.append(end_date.isoformat())
    query += " ORDER BY session_date"
    rows = conn.execute(query, params).fetchall()
    return [
        Score(
            score_id=row["score_id"],
            etf_id=row["etf_id"],
            scoring_profile_id=row["scoring_profile_id"],
            session_date=date.fromisoformat(row["session_date"]),
            overall_score=Decimal(row["overall_score"]),
            computed_at=datetime.fromisoformat(row["computed_at"]),
        )
        for row in rows
    ]


def get_dimension_scores(conn: sqlite3.Connection, score_id: str) -> list[DimensionScore]:
    rows = conn.execute(
        "SELECT score_id, dimension, value, computed_at FROM DimensionScore WHERE score_id = ?",
        (score_id,),
    ).fetchall()
    return [
        DimensionScore(
            score_id=row["score_id"],
            dimension=Dimension(row["dimension"]),
            value=Decimal(row["value"]),
            computed_at=datetime.fromisoformat(row["computed_at"]),
        )
        for row in rows
    ]
