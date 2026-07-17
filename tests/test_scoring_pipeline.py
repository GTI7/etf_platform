from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

import core.market_data.ingestion.pipeline_run as pipeline_run
from core.analytics.domain.models import (
    Dimension,
    IndicatorDefinition,
    IndicatorValue,
    MissingIndicatorValueError,
    ScoringProfile,
    serialize_parameters,
)
from core.analytics.persistence.repository import (
    get_dimension_scores,
    get_score,
    insert_indicator_definition,
    insert_indicator_value,
    insert_scoring_profile,
)
from core.analytics.scoring_pipeline import calculate_score
from core.market_data.domain.models import ETF, Calendar, TradingSession
from core.market_data.persistence.repository import (
    get_last_successful_pipeline_date,
    insert_calendar,
    insert_etf,
    insert_trading_session,
)
from core.shared.clock import FixedClock

CALENDAR_ID = "XNYS"
SESSION_DATE = date(2026, 7, 14)


def _make_etf_with_trading_day(conn: sqlite3.Connection, trading_day: date) -> ETF:
    insert_calendar(
        conn,
        Calendar(
            calendar_id=CALENDAR_ID,
            name="New York Stock Exchange",
            exchange="NYSE",
            timezone="America/New_York",
        ),
    )
    insert_trading_session(
        conn,
        TradingSession(
            calendar_id=CALENDAR_ID, session_date=trading_day, is_trading_day=True, close_time_utc=None
        ),
    )
    etf = ETF(
        etf_id=uuid.uuid4().hex,
        ticker="SPY",
        name="SPDR S&P 500",
        currency="USD",
        calendar_id=CALENDAR_ID,
        created_at=datetime.now(timezone.utc),
    )
    insert_etf(conn, etf)
    return etf


def _make_second_etf(conn: sqlite3.Connection, ticker: str = "QQQ") -> ETF:
    """A second ETF on the already-populated CALENDAR_ID calendar (does not
    re-insert the Calendar row -- use only after _make_etf_with_trading_day
    has already been called once in the same test)."""
    etf = ETF(
        etf_id=uuid.uuid4().hex,
        ticker=ticker,
        name="Invesco QQQ",
        currency="USD",
        calendar_id=CALENDAR_ID,
        created_at=datetime.now(timezone.utc),
    )
    insert_etf(conn, etf)
    return etf


def _make_indicator_definition(name: str = "SMA", version: int = 1) -> IndicatorDefinition:
    return IndicatorDefinition(
        indicator_definition_id=uuid.uuid4().hex,
        name=name,
        version=version,
        parameters=serialize_parameters({"window": 20}),
        created_at=datetime.now(timezone.utc),
    )


def _make_rsi_indicator_definition(version: int = 1) -> IndicatorDefinition:
    return IndicatorDefinition(
        indicator_definition_id=uuid.uuid4().hex,
        name="RSI",
        version=version,
        parameters=serialize_parameters({"period": 14}),
        created_at=datetime.now(timezone.utc),
    )


def _make_profile(name: str = "REFERENCE", version: int = 1) -> ScoringProfile:
    return ScoringProfile(
        scoring_profile_id=uuid.uuid4().hex,
        name=name,
        version=version,
        parameters=serialize_parameters(
            {"dimensions": {"MOMENTUM": {"indicator_name": "SMA", "indicator_version": 1}}}
        ),
        created_at=datetime.now(timezone.utc),
    )


def _seed_indicator_value(
    conn: sqlite3.Connection, definition: IndicatorDefinition, etf_id: str, value: str
) -> None:
    insert_indicator_value(
        conn,
        IndicatorValue(
            indicator_value_id=uuid.uuid4().hex,
            indicator_definition_id=definition.indicator_definition_id,
            etf_id=etf_id,
            session_date=SESSION_DATE,
            value=Decimal(value),
            computed_at=datetime.now(timezone.utc),
        ),
    )


def test_calculate_score_writes_score_and_dimension_score(conn: sqlite3.Connection) -> None:
    etf = _make_etf_with_trading_day(conn, SESSION_DATE)
    definition = _make_indicator_definition()
    insert_indicator_definition(conn, definition)
    _seed_indicator_value(conn, definition, etf.etf_id, "70")
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    clock = FixedClock(datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc))

    calculate_score(conn, clock, etf, profile, SESSION_DATE)

    score = get_score(conn, etf.etf_id, profile.scoring_profile_id, SESSION_DATE)
    assert score is not None
    assert score.overall_score == Decimal("70")  # single dimension -> mean is itself

    [dimension_score] = get_dimension_scores(conn, score.score_id)
    assert dimension_score.dimension == Dimension.MOMENTUM
    assert dimension_score.value == Decimal("70")

    pipeline_name = f"scoring:{profile.name}:v{profile.version}:{etf.ticker}"
    assert get_last_successful_pipeline_date(conn, pipeline_name) == SESSION_DATE


def test_calculate_score_is_a_noop_on_non_trading_day(conn: sqlite3.Connection) -> None:
    non_trading_day = date(2026, 7, 12)  # Sunday
    etf = _make_etf_with_trading_day(conn, SESSION_DATE)
    insert_trading_session(
        conn,
        TradingSession(
            calendar_id=CALENDAR_ID, session_date=non_trading_day, is_trading_day=False, close_time_utc=None
        ),
    )
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    clock = FixedClock(datetime(2026, 7, 12, 21, 0, tzinfo=timezone.utc))

    calculate_score(conn, clock, etf, profile, non_trading_day)

    assert get_score(conn, etf.etf_id, profile.scoring_profile_id, non_trading_day) is None
    pipeline_name = f"scoring:{profile.name}:v{profile.version}:{etf.ticker}"
    assert get_last_successful_pipeline_date(conn, pipeline_name) == non_trading_day


def test_calculate_score_raises_when_indicator_value_missing(conn: sqlite3.Connection) -> None:
    etf = _make_etf_with_trading_day(conn, SESSION_DATE)
    definition = _make_indicator_definition()
    insert_indicator_definition(conn, definition)
    # No IndicatorValue seeded.
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    clock = FixedClock(datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc))

    with pytest.raises(MissingIndicatorValueError):
        calculate_score(conn, clock, etf, profile, SESSION_DATE)

    assert get_score(conn, etf.etf_id, profile.scoring_profile_id, SESSION_DATE) is None
    pipeline_name = f"scoring:{profile.name}:v{profile.version}:{etf.ticker}"
    assert get_last_successful_pipeline_date(conn, pipeline_name) is None


def test_calculate_score_raises_when_indicator_definition_missing(conn: sqlite3.Connection) -> None:
    etf = _make_etf_with_trading_day(conn, SESSION_DATE)
    # No IndicatorDefinition registered at all.
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    clock = FixedClock(datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc))

    with pytest.raises(MissingIndicatorValueError):
        calculate_score(conn, clock, etf, profile, SESSION_DATE)


def test_calculate_score_is_idempotent_on_rerun(conn: sqlite3.Connection) -> None:
    etf = _make_etf_with_trading_day(conn, SESSION_DATE)
    definition = _make_indicator_definition()
    insert_indicator_definition(conn, definition)
    _seed_indicator_value(conn, definition, etf.etf_id, "70")
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    clock = FixedClock(datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc))

    for _ in range(3):
        calculate_score(conn, clock, etf, profile, SESSION_DATE)

    row = conn.execute(
        "SELECT COUNT(*) AS n FROM Score WHERE etf_id = ? AND scoring_profile_id = ? AND session_date = ?",
        (etf.etf_id, profile.scoring_profile_id, SESSION_DATE.isoformat()),
    ).fetchone()
    assert row["n"] == 1

    score = get_score(conn, etf.etf_id, profile.scoring_profile_id, SESSION_DATE)
    dimension_scores = get_dimension_scores(conn, score.score_id)
    assert len(dimension_scores) == 1  # not duplicated across reruns either


def test_calculate_score_is_deterministic_across_recalculation(conn: sqlite3.Connection) -> None:
    """Same inputs, computed at two different times, produce the same
    Score and DimensionScore values -- the calculation itself must not
    depend on when it runs."""
    etf = _make_etf_with_trading_day(conn, SESSION_DATE)
    definition = _make_indicator_definition()
    insert_indicator_definition(conn, definition)
    _seed_indicator_value(conn, definition, etf.etf_id, "70")
    profile = _make_profile()
    insert_scoring_profile(conn, profile)

    early_clock = FixedClock(datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc))
    calculate_score(conn, early_clock, etf, profile, SESSION_DATE)
    first_score = get_score(conn, etf.etf_id, profile.scoring_profile_id, SESSION_DATE)

    # A second, independent ETF/profile pairing computed "later" must
    # produce an identical result given identical inputs.
    other_etf = _make_second_etf(conn)
    _seed_indicator_value(conn, definition, other_etf.etf_id, "70")
    later_clock = FixedClock(datetime(2026, 7, 20, 21, 0, tzinfo=timezone.utc))
    calculate_score(conn, later_clock, other_etf, profile, SESSION_DATE)
    second_score = get_score(conn, other_etf.etf_id, profile.scoring_profile_id, SESSION_DATE)

    assert first_score.overall_score == second_score.overall_score == Decimal("70")


def test_profile_versions_produce_independent_score_histories(conn: sqlite3.Connection) -> None:
    etf = _make_etf_with_trading_day(conn, SESSION_DATE)
    definition = _make_indicator_definition()
    insert_indicator_definition(conn, definition)
    _seed_indicator_value(conn, definition, etf.etf_id, "70")
    profile_v1 = _make_profile(version=1)
    profile_v2 = _make_profile(version=2)
    insert_scoring_profile(conn, profile_v1)
    insert_scoring_profile(conn, profile_v2)
    clock = FixedClock(datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc))

    calculate_score(conn, clock, etf, profile_v1, SESSION_DATE)
    calculate_score(conn, clock, etf, profile_v2, SESSION_DATE)

    score_v1 = get_score(conn, etf.etf_id, profile_v1.scoring_profile_id, SESSION_DATE)
    score_v2 = get_score(conn, etf.etf_id, profile_v2.scoring_profile_id, SESSION_DATE)
    assert score_v1 is not None
    assert score_v2 is not None
    assert score_v1.score_id != score_v2.score_id


def test_watermark_advance_failure_rolls_back_completion(
    conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Failure in run_pipeline's own completion step must roll back the
    Score/DimensionScore writes made just before it, exactly as proven for
    market data (Phase 1) and indicators (Phase 2)."""
    etf = _make_etf_with_trading_day(conn, SESSION_DATE)
    definition = _make_indicator_definition()
    insert_indicator_definition(conn, definition)
    _seed_indicator_value(conn, definition, etf.etf_id, "70")
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    clock = FixedClock(datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc))

    def _boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated failure advancing the watermark")

    monkeypatch.setattr(pipeline_run, "advance_pipeline_watermark", _boom)

    with pytest.raises(RuntimeError):
        calculate_score(conn, clock, etf, profile, SESSION_DATE)

    assert get_score(conn, etf.etf_id, profile.scoring_profile_id, SESSION_DATE) is None
    pipeline_name = f"scoring:{profile.name}:v{profile.version}:{etf.ticker}"
    assert get_last_successful_pipeline_date(conn, pipeline_name) is None
    status = conn.execute(
        "SELECT status FROM IngestionRun WHERE pipeline_name = ?", (pipeline_name,)
    ).fetchone()["status"]
    assert status == "running"


def test_calculation_failure_rolls_back_partial_write(
    conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression test for the AD-019-style rollback guarantee, checked
    for the scoring pipeline specifically: a Score insert that succeeds,
    followed by a failure inserting a DimensionScore, must not leave the
    Score behind."""
    import core.analytics.scoring_pipeline as scoring_pipeline

    etf = _make_etf_with_trading_day(conn, SESSION_DATE)
    definition = _make_indicator_definition()
    insert_indicator_definition(conn, definition)
    _seed_indicator_value(conn, definition, etf.etf_id, "70")
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    clock = FixedClock(datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc))

    real_insert_dimension_score = scoring_pipeline.insert_dimension_score

    def _insert_then_fail(conn_: sqlite3.Connection, dimension_score: object) -> None:
        real_insert_dimension_score(conn_, dimension_score)
        raise RuntimeError("simulated failure after a successful write")

    monkeypatch.setattr(scoring_pipeline, "insert_dimension_score", _insert_then_fail)

    with pytest.raises(RuntimeError):
        calculate_score(conn, clock, etf, profile, SESSION_DATE)

    assert get_score(conn, etf.etf_id, profile.scoring_profile_id, SESSION_DATE) is None
    row = conn.execute("SELECT COUNT(*) AS n FROM DimensionScore").fetchone()
    assert row["n"] == 0
    pipeline_name = f"scoring:{profile.name}:v{profile.version}:{etf.ticker}"
    status = conn.execute(
        "SELECT status FROM IngestionRun WHERE pipeline_name = ?", (pipeline_name,)
    ).fetchone()["status"]
    assert status == "failed"


def test_scoring_profile_using_sma_and_rsi_together_succeeds_unmodified(
    conn: sqlite3.Connection,
) -> None:
    """The whole point of Milestone A: calculate_score()/_resolve_dimension_values()
    are completely unmodified by adding a second indicator. Scoring already
    resolves indicators generically by name+version, so a profile mixing
    SMA (MOMENTUM) and RSI (VALUE) must "just work" with zero scoring code
    changes -- this is the strongest proof that the architecture
    generalizes, not just that a second calculation function exists."""
    etf = _make_etf_with_trading_day(conn, SESSION_DATE)
    sma_definition = _make_indicator_definition(name="SMA")
    rsi_definition = _make_rsi_indicator_definition()
    insert_indicator_definition(conn, sma_definition)
    insert_indicator_definition(conn, rsi_definition)
    _seed_indicator_value(conn, sma_definition, etf.etf_id, "70")
    _seed_indicator_value(conn, rsi_definition, etf.etf_id, "65")
    profile = ScoringProfile(
        scoring_profile_id=uuid.uuid4().hex,
        name="MIXED",
        version=1,
        parameters=serialize_parameters(
            {
                "dimensions": {
                    "MOMENTUM": {"indicator_name": "SMA", "indicator_version": 1},
                    "VALUE": {"indicator_name": "RSI", "indicator_version": 1},
                }
            }
        ),
        created_at=datetime.now(timezone.utc),
    )
    insert_scoring_profile(conn, profile)
    clock = FixedClock(datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc))

    calculate_score(conn, clock, etf, profile, SESSION_DATE)

    score = get_score(conn, etf.etf_id, profile.scoring_profile_id, SESSION_DATE)
    assert score is not None
    assert score.overall_score == Decimal("67.5")  # mean(70, 65)

    dimension_scores = {ds.dimension: ds.value for ds in get_dimension_scores(conn, score.score_id)}
    assert dimension_scores == {Dimension.MOMENTUM: Decimal("70"), Dimension.VALUE: Decimal("65")}
