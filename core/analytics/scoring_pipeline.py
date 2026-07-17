from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import date
from decimal import Decimal

from core.analytics.domain import score_calculation
from core.analytics.domain.models import (
    Dimension,
    DimensionScore,
    MissingIndicatorValueError,
    Score,
    ScoringProfile,
)
from core.analytics.persistence.repository import (
    get_indicator_definition,
    get_indicator_values,
    get_score,
    insert_dimension_score,
    insert_score,
)
from core.market_data.domain.models import ETF
from core.market_data.ingestion.pipeline_run import run_pipeline
from core.market_data.persistence.repository import is_trading_day
from core.shared.clock import Clock
from core.shared.pipeline_names import scoring_pipeline_name


def _resolve_dimension_values(
    conn: sqlite3.Connection, profile: ScoringProfile, etf_id: str, session_date: date
) -> dict[Dimension, Decimal]:
    """Resolve one IndicatorValue per dimension named in profile.parameters.

    profile.parameters is expected to contain:
        {"dimensions": {"MOMENTUM": {"indicator_name": "SMA", "indicator_version": 1}, ...}}

    Raises MissingIndicatorValueError if the referenced IndicatorDefinition
    doesn't exist, or if it exists but has no IndicatorValue for this ETF
    and session_date yet.
    """
    config = json.loads(profile.parameters)["dimensions"]
    dimension_values: dict[Dimension, Decimal] = {}
    for dimension_name, indicator_ref in config.items():
        dimension = Dimension(dimension_name)
        indicator_name = indicator_ref["indicator_name"]
        indicator_version = indicator_ref["indicator_version"]

        definition = get_indicator_definition(conn, indicator_name, indicator_version)
        if definition is None:
            raise MissingIndicatorValueError(
                f"No IndicatorDefinition for name={indicator_name!r} version={indicator_version}"
            )

        values = get_indicator_values(
            conn,
            definition.indicator_definition_id,
            etf_id,
            start_date=session_date,
            end_date=session_date,
        )
        if not values:
            raise MissingIndicatorValueError(
                f"No IndicatorValue for etf_id={etf_id!r}, indicator={indicator_name!r} "
                f"v{indicator_version}, session_date={session_date}"
            )
        dimension_values[dimension] = values[0].value
    return dimension_values


def calculate_score(
    conn: sqlite3.Connection,
    clock: Clock,
    etf: ETF,
    profile: ScoringProfile,
    session_date: date,
) -> str:
    """Compute and store one Score (and its DimensionScores) for one ETF,
    one ScoringProfile, and one session.

    TradingCalendar-aware: a non-trading session_date is a no-op success,
    same as Phase 1's price ingestion. Idempotent: if a Score already
    exists for this (etf, profile, session), the run is a no-op success --
    checked explicitly with get_score() before any computation happens, so
    a rerun never attempts to insert a Score or DimensionScore rows a
    second time (unlike a single-row ON CONFLICT DO NOTHING, this has to
    be checked up front here because Score and DimensionScore form a
    parent-child pair: skipping only the Score insert on conflict would
    leave freshly-generated DimensionScore rows pointing at a score_id that
    was never actually written). One call is one atomic pipeline run: the
    Score insert, every DimensionScore insert, run completion, and
    watermark advance commit or roll back together, per run_pipeline's
    transaction boundary.
    """
    pipeline_name = scoring_pipeline_name(profile.name, profile.version, etf.ticker)
    with run_pipeline(conn, clock, pipeline_name, session_date) as ingestion_run_id:
        if not is_trading_day(conn, etf.calendar_id, session_date):
            return ingestion_run_id

        if get_score(conn, etf.etf_id, profile.scoring_profile_id, session_date) is not None:
            return ingestion_run_id

        dimension_values = _resolve_dimension_values(conn, profile, etf.etf_id, session_date)
        dimension_scores, overall_score = score_calculation.calculate_score(dimension_values)

        computed_at = clock.now()
        score = Score(
            score_id=uuid.uuid4().hex,
            etf_id=etf.etf_id,
            scoring_profile_id=profile.scoring_profile_id,
            session_date=session_date,
            overall_score=overall_score,
            computed_at=computed_at,
        )
        insert_score(conn, score)
        for dimension, value in dimension_scores.items():
            insert_dimension_score(
                conn,
                DimensionScore(
                    score_id=score.score_id,
                    dimension=dimension,
                    value=value,
                    computed_at=computed_at,
                ),
            )
    return ingestion_run_id
