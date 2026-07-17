from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

import core.analytics.indicator_calculation as indicator_calculation
import core.analytics.write_pipeline as write_pipeline
from core.analytics.domain.models import (
    Dimension,
    IndicatorDefinition,
    InsufficientPriceHistoryError,
    ScoringProfile,
    serialize_parameters,
)
from core.analytics.persistence.repository import (
    get_dimension_scores,
    get_indicator_values,
    get_score,
    insert_indicator_definition,
    insert_scoring_profile,
)
from core.analytics.write_pipeline import WritePipelineResult, run_write_pipeline
from core.market_data.domain.models import ETF, Calendar, PriceBar, TradingSession
from core.market_data.persistence.repository import (
    get_last_successful_pipeline_date,
    get_price_bars,
    insert_calendar,
    insert_etf,
    insert_price_bar,
    insert_trading_session,
)
from core.market_data.providers.base import ProviderError, ProviderPriceBar
from core.shared.clock import FixedClock
from core.shared.money import Money

CALENDAR_ID = "XNYS"
PRIOR_DAY = date(2026, 7, 16)  # Thursday
SESSION_DATE = date(2026, 7, 17)  # Friday


def _make_etf(conn: sqlite3.Connection, trading_days: list[date]) -> ETF:
    insert_calendar(
        conn,
        Calendar(
            calendar_id=CALENDAR_ID,
            name="New York Stock Exchange",
            exchange="NYSE",
            timezone="America/New_York",
        ),
    )
    for day in trading_days:
        insert_trading_session(
            conn,
            TradingSession(
                calendar_id=CALENDAR_ID, session_date=day, is_trading_day=True, close_time_utc=None
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


def _insert_bar(conn: sqlite3.Connection, etf_id: str, session_date: date, close: str) -> None:
    """Seed a PriceBar directly, bypassing ingestion -- used for history a
    window calculation needs that predates the session under test, the
    same pattern test_indicator_calculation.py already uses."""
    price = Money(Decimal(close), "USD")
    insert_price_bar(
        conn,
        PriceBar(
            price_bar_id=uuid.uuid4().hex,
            etf_id=etf_id,
            session_date=session_date,
            open=price,
            high=price,
            low=price,
            close=price,
            volume=1,
            source="test",
            ingested_at=datetime.now(timezone.utc),
        ),
    )


def _make_sma_definition(window: int = 1) -> IndicatorDefinition:
    return IndicatorDefinition(
        indicator_definition_id=uuid.uuid4().hex,
        name="SMA",
        version=1,
        parameters=serialize_parameters({"window": window}),
        created_at=datetime.now(timezone.utc),
    )


def _make_rsi_definition(period: int = 1) -> IndicatorDefinition:
    return IndicatorDefinition(
        indicator_definition_id=uuid.uuid4().hex,
        name="RSI",
        version=1,
        parameters=serialize_parameters({"period": period}),
        created_at=datetime.now(timezone.utc),
    )


def _make_profile() -> ScoringProfile:
    return ScoringProfile(
        scoring_profile_id=uuid.uuid4().hex,
        name="REFERENCE",
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


def _provider_bar(session_date: date, close: str) -> ProviderPriceBar:
    price = Decimal(close)
    return ProviderPriceBar(
        session_date=session_date, open=price, high=price, low=price, close=price, volume=1000, currency="USD"
    )


class _FakeProvider:
    def __init__(self, name: str, bars: list[ProviderPriceBar]) -> None:
        self.name = name
        self._bars = bars
        self.calls: list[tuple[str, date, date]] = []

    def fetch_daily_bars(self, ticker: str, start_date: date, end_date: date) -> list[ProviderPriceBar]:
        self.calls.append((ticker, start_date, end_date))
        return self._bars


class _FailingProvider:
    name = "failing"

    def fetch_daily_bars(self, ticker: str, start_date: date, end_date: date) -> list[ProviderPriceBar]:
        raise ProviderError("upstream is down")


def _seed_standard_fixture(
    conn: sqlite3.Connection,
) -> tuple[ETF, IndicatorDefinition, IndicatorDefinition, ScoringProfile]:
    """Two consecutive trading days, PRIOR_DAY already priced -- everything
    calculate_sma(window=1)/calculate_rsi(period=1)/calculate_score need
    for SESSION_DATE once SESSION_DATE itself is ingested."""
    etf = _make_etf(conn, [PRIOR_DAY, SESSION_DATE])
    _insert_bar(conn, etf.etf_id, PRIOR_DAY, "100")
    sma_definition = _make_sma_definition(window=1)
    rsi_definition = _make_rsi_definition(period=1)
    insert_indicator_definition(conn, sma_definition)
    insert_indicator_definition(conn, rsi_definition)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    return etf, sma_definition, rsi_definition, profile


def test_run_write_pipeline_end_to_end_success(conn: sqlite3.Connection) -> None:
    etf, sma_definition, rsi_definition, profile = _seed_standard_fixture(conn)
    provider = _FakeProvider("fake", [_provider_bar(SESSION_DATE, "103")])
    clock = FixedClock(datetime(2026, 7, 17, 21, 0, tzinfo=timezone.utc))

    result = run_write_pipeline(
        conn, clock, provider, etf, SESSION_DATE, sma_definition, rsi_definition, profile
    )

    assert isinstance(result, WritePipelineResult)
    assert result.price_ingestion_run_id is not None
    assert result.sma_run_id is not None
    assert result.rsi_run_id is not None
    assert result.score_run_id is not None

    [stored_bar] = get_price_bars(conn, etf.etf_id, start_date=SESSION_DATE, end_date=SESSION_DATE)
    assert stored_bar.close.amount == Decimal("103")

    [sma_value] = get_indicator_values(conn, sma_definition.indicator_definition_id, etf.etf_id)
    assert sma_value.value == Decimal("103")  # window=1 -> just the session's own close

    [rsi_value] = get_indicator_values(conn, rsi_definition.indicator_definition_id, etf.etf_id)
    assert rsi_value.value == Decimal("100")  # 100 -> 103 is a pure gain

    score = get_score(conn, etf.etf_id, profile.scoring_profile_id, SESSION_DATE)
    assert score is not None
    assert score.overall_score == Decimal("101.5")  # mean(103, 100)
    dimension_scores = {ds.dimension: ds.value for ds in get_dimension_scores(conn, score.score_id)}
    assert dimension_scores == {Dimension.MOMENTUM: Decimal("103"), Dimension.VALUE: Decimal("100")}

    assert provider.calls == [("SPY", SESSION_DATE, SESSION_DATE)]


def test_run_write_pipeline_rolls_back_and_stops_before_indicators_when_ingestion_fails(
    conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    etf, sma_definition, rsi_definition, profile = _seed_standard_fixture(conn)
    clock = FixedClock(datetime(2026, 7, 17, 21, 0, tzinfo=timezone.utc))

    def _must_not_be_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("calculate_sma must not run when ingestion fails")

    monkeypatch.setattr(write_pipeline, "calculate_sma", _must_not_be_called)

    with pytest.raises(ProviderError):
        run_write_pipeline(
            conn, clock, _FailingProvider(), etf, SESSION_DATE, sma_definition, rsi_definition, profile
        )

    assert get_price_bars(conn, etf.etf_id, start_date=SESSION_DATE, end_date=SESSION_DATE) == []
    assert get_indicator_values(conn, sma_definition.indicator_definition_id, etf.etf_id) == []
    assert get_score(conn, etf.etf_id, profile.scoring_profile_id, SESSION_DATE) is None
    status = conn.execute(
        "SELECT status FROM IngestionRun WHERE pipeline_name = ?", (f"price_ingestion:{etf.ticker}",)
    ).fetchone()["status"]
    assert status == "failed"


def test_run_write_pipeline_stops_before_rsi_and_score_when_sma_fails(
    conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SMA fails on a legitimate InsufficientPriceHistoryError (window
    larger than available history) rather than an injected failure, then
    proves neither RSI nor scoring ran, while ingestion's own commit from
    stage 1 survives untouched."""
    etf = _make_etf(conn, [SESSION_DATE])  # only one trading day
    sma_definition = _make_sma_definition(window=5)  # impossible: only 1 day exists
    rsi_definition = _make_rsi_definition(period=1)
    insert_indicator_definition(conn, sma_definition)
    insert_indicator_definition(conn, rsi_definition)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)
    provider = _FakeProvider("fake", [_provider_bar(SESSION_DATE, "100")])
    clock = FixedClock(datetime(2026, 7, 17, 21, 0, tzinfo=timezone.utc))

    def _must_not_be_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("must not run when SMA fails")

    monkeypatch.setattr(write_pipeline, "calculate_rsi", _must_not_be_called)
    monkeypatch.setattr(write_pipeline, "calculate_score", _must_not_be_called)

    with pytest.raises(InsufficientPriceHistoryError):
        run_write_pipeline(
            conn, clock, provider, etf, SESSION_DATE, sma_definition, rsi_definition, profile
        )

    # Ingestion (stage 1) already committed in its own transaction -- SMA's
    # later failure must not roll it back.
    [stored_bar] = get_price_bars(conn, etf.etf_id, start_date=SESSION_DATE, end_date=SESSION_DATE)
    assert stored_bar.close.amount == Decimal("100")
    assert get_indicator_values(conn, sma_definition.indicator_definition_id, etf.etf_id) == []
    assert get_score(conn, etf.etf_id, profile.scoring_profile_id, SESSION_DATE) is None


def test_run_write_pipeline_skips_ingestion_when_pricebar_already_exists(
    conn: sqlite3.Connection,
) -> None:
    """The ingestion guard is a direct PriceBar existence check, not a
    watermark lookup: a bar present for this exact date is enough to skip
    re-ingestion even when no price_ingestion watermark exists at all."""
    etf, sma_definition, rsi_definition, profile = _seed_standard_fixture(conn)
    _insert_bar(conn, etf.etf_id, SESSION_DATE, "103")  # seeded directly, never ingested
    provider = _FakeProvider("fake", bars=[])
    clock = FixedClock(datetime(2026, 7, 17, 21, 0, tzinfo=timezone.utc))

    assert get_last_successful_pipeline_date(conn, f"price_ingestion:{etf.ticker}") is None

    result = run_write_pipeline(
        conn, clock, provider, etf, SESSION_DATE, sma_definition, rsi_definition, profile
    )

    assert result.price_ingestion_run_id is None
    assert provider.calls == []
    assert len(get_price_bars(conn, etf.etf_id, start_date=SESSION_DATE, end_date=SESSION_DATE)) == 1
    [sma_value] = get_indicator_values(conn, sma_definition.indicator_definition_id, etf.etf_id)
    assert sma_value.value == Decimal("103")


def test_run_write_pipeline_second_call_skips_ingestion_and_does_not_duplicate_pricebar(
    conn: sqlite3.Connection,
) -> None:
    etf, sma_definition, rsi_definition, profile = _seed_standard_fixture(conn)
    provider = _FakeProvider("fake", [_provider_bar(SESSION_DATE, "103")])
    clock = FixedClock(datetime(2026, 7, 17, 21, 0, tzinfo=timezone.utc))

    first = run_write_pipeline(
        conn, clock, provider, etf, SESSION_DATE, sma_definition, rsi_definition, profile
    )
    second = run_write_pipeline(
        conn, clock, provider, etf, SESSION_DATE, sma_definition, rsi_definition, profile
    )

    assert first.price_ingestion_run_id is not None
    assert second.price_ingestion_run_id is None
    assert provider.calls == [("SPY", SESSION_DATE, SESSION_DATE)]  # the provider was asked only once
    assert len(get_price_bars(conn, etf.etf_id, start_date=SESSION_DATE, end_date=SESSION_DATE)) == 1


def test_run_write_pipeline_is_idempotent_across_repeated_calls(conn: sqlite3.Connection) -> None:
    etf, sma_definition, rsi_definition, profile = _seed_standard_fixture(conn)
    provider = _FakeProvider("fake", [_provider_bar(SESSION_DATE, "103")])
    clock = FixedClock(datetime(2026, 7, 17, 21, 0, tzinfo=timezone.utc))

    for _ in range(3):
        run_write_pipeline(conn, clock, provider, etf, SESSION_DATE, sma_definition, rsi_definition, profile)

    assert len(get_price_bars(conn, etf.etf_id, start_date=SESSION_DATE, end_date=SESSION_DATE)) == 1
    assert len(get_indicator_values(conn, sma_definition.indicator_definition_id, etf.etf_id)) == 1
    assert len(get_indicator_values(conn, rsi_definition.indicator_definition_id, etf.etf_id)) == 1
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM Score WHERE etf_id = ? AND scoring_profile_id = ? AND session_date = ?",
        (etf.etf_id, profile.scoring_profile_id, SESSION_DATE.isoformat()),
    ).fetchone()
    assert row["n"] == 1
    assert provider.calls == [("SPY", SESSION_DATE, SESSION_DATE)]  # never re-asked across all 3 calls


def test_run_write_pipeline_backfill_ingests_earlier_never_ingested_session(
    conn: sqlite3.Connection,
) -> None:
    """Regression test for the corrected design: a watermark that has
    already advanced past a LATER date must not cause an EARLIER,
    never-ingested backfill session to be skipped. A watermark-comparison
    guard would wrongly skip this; the PriceBar existence check does not.
    """
    day0 = date(2026, 7, 14)  # pre-existing history, seeded directly
    early_day = date(2026, 7, 15)  # the backfill target -- never ingested
    mid_day = date(2026, 7, 16)  # pre-existing history, seeded directly
    later_day = date(2026, 7, 17)  # ingested first, establishing the watermark

    etf = _make_etf(conn, [day0, early_day, mid_day, later_day])
    _insert_bar(conn, etf.etf_id, day0, "48")
    _insert_bar(conn, etf.etf_id, mid_day, "50")
    sma_definition = _make_sma_definition(window=1)
    rsi_definition = _make_rsi_definition(period=1)
    insert_indicator_definition(conn, sma_definition)
    insert_indicator_definition(conn, rsi_definition)
    profile = _make_profile()
    insert_scoring_profile(conn, profile)

    later_provider = _FakeProvider("fake", [_provider_bar(later_day, "55")])
    clock = FixedClock(datetime(2026, 7, 17, 21, 0, tzinfo=timezone.utc))
    run_write_pipeline(
        conn, clock, later_provider, etf, later_day, sma_definition, rsi_definition, profile
    )

    # Watermark now sits at later_day, well past early_day -- exactly the
    # state a watermark-comparison guard would misread as "already handled".
    assert get_last_successful_pipeline_date(conn, f"price_ingestion:{etf.ticker}") == later_day
    assert get_price_bars(conn, etf.etf_id, start_date=early_day, end_date=early_day) == []

    early_provider = _FakeProvider("fake", [_provider_bar(early_day, "49")])
    backfill_clock = FixedClock(datetime(2026, 7, 15, 21, 0, tzinfo=timezone.utc))
    result = run_write_pipeline(
        conn, backfill_clock, early_provider, etf, early_day, sma_definition, rsi_definition, profile
    )

    assert result.price_ingestion_run_id is not None  # ingestion actually ran, not skipped
    assert early_provider.calls == [("SPY", early_day, early_day)]
    [stored_bar] = get_price_bars(conn, etf.etf_id, start_date=early_day, end_date=early_day)
    assert stored_bar.close.amount == Decimal("49")
    [sma_value] = get_indicator_values(conn, sma_definition.indicator_definition_id, etf.etf_id, start_date=early_day, end_date=early_day)
    assert sma_value.value == Decimal("49")
    score = get_score(conn, etf.etf_id, profile.scoring_profile_id, early_day)
    assert score is not None


def test_run_write_pipeline_partial_failure_then_retry_recovers(
    conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    etf, sma_definition, rsi_definition, profile = _seed_standard_fixture(conn)
    provider = _FakeProvider("fake", [_provider_bar(SESSION_DATE, "103")])
    clock = FixedClock(datetime(2026, 7, 17, 21, 0, tzinfo=timezone.utc))

    real_insert = indicator_calculation.insert_indicator_value
    call_count = {"n": 0}

    def _fail_on_second_insert(conn_: sqlite3.Connection, value: object) -> None:
        call_count["n"] += 1
        if call_count["n"] == 2:  # the first insert is SMA's; the second is RSI's
            raise RuntimeError("simulated failure computing RSI")
        real_insert(conn_, value)

    monkeypatch.setattr(indicator_calculation, "insert_indicator_value", _fail_on_second_insert)

    with pytest.raises(RuntimeError):
        run_write_pipeline(conn, clock, provider, etf, SESSION_DATE, sma_definition, rsi_definition, profile)

    # First call: ingestion + SMA committed, RSI and scoring never completed.
    assert len(get_price_bars(conn, etf.etf_id, start_date=SESSION_DATE, end_date=SESSION_DATE)) == 1
    assert len(get_indicator_values(conn, sma_definition.indicator_definition_id, etf.etf_id)) == 1
    assert get_indicator_values(conn, rsi_definition.indicator_definition_id, etf.etf_id) == []
    assert get_score(conn, etf.etf_id, profile.scoring_profile_id, SESSION_DATE) is None
    assert provider.calls == [("SPY", SESSION_DATE, SESSION_DATE)]

    monkeypatch.undo()  # restore the real insert for the retry

    result = run_write_pipeline(conn, clock, provider, etf, SESSION_DATE, sma_definition, rsi_definition, profile)

    assert result.price_ingestion_run_id is None  # ingestion skipped: PriceBar already existed
    assert provider.calls == [("SPY", SESSION_DATE, SESSION_DATE)]  # still only ever called once
    assert len(get_indicator_values(conn, sma_definition.indicator_definition_id, etf.etf_id)) == 1
    [rsi_value] = get_indicator_values(conn, rsi_definition.indicator_definition_id, etf.etf_id)
    assert rsi_value.value == Decimal("100")
    score = get_score(conn, etf.etf_id, profile.scoring_profile_id, SESSION_DATE)
    assert score is not None
    assert score.overall_score == Decimal("101.5")


def test_run_write_pipeline_rolls_back_scoring_only_when_scoring_fails(
    conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression test for the one gap independent verification flagged:
    a composed-level failure inside the scoring stage specifically. Forces
    the failure with the exact insert-then-fail pattern
    test_scoring_pipeline.py's test_calculation_failure_rolls_back_partial_write
    already uses -- a Score insert that succeeds, followed by a failure
    inserting its DimensionScore. Proves the scoring stage's rollback is
    isolated to its own transaction: ingestion, SMA, and RSI already
    committed in their own, separate, prior transactions and must survive
    untouched."""
    import core.analytics.scoring_pipeline as scoring_pipeline

    etf, sma_definition, rsi_definition, profile = _seed_standard_fixture(conn)
    provider = _FakeProvider("fake", [_provider_bar(SESSION_DATE, "103")])
    clock = FixedClock(datetime(2026, 7, 17, 21, 0, tzinfo=timezone.utc))

    real_insert_dimension_score = scoring_pipeline.insert_dimension_score

    def _insert_then_fail(conn_: sqlite3.Connection, dimension_score: object) -> None:
        real_insert_dimension_score(conn_, dimension_score)
        raise RuntimeError("simulated failure inside the scoring stage")

    monkeypatch.setattr(scoring_pipeline, "insert_dimension_score", _insert_then_fail)

    with pytest.raises(RuntimeError):
        run_write_pipeline(
            conn, clock, provider, etf, SESSION_DATE, sma_definition, rsi_definition, profile
        )

    # Earlier stages already committed in their own, separate transactions --
    # the scoring stage's failure must not touch any of them.
    [stored_bar] = get_price_bars(conn, etf.etf_id, start_date=SESSION_DATE, end_date=SESSION_DATE)
    assert stored_bar.close.amount == Decimal("103")
    [sma_value] = get_indicator_values(conn, sma_definition.indicator_definition_id, etf.etf_id)
    assert sma_value.value == Decimal("103")
    [rsi_value] = get_indicator_values(conn, rsi_definition.indicator_definition_id, etf.etf_id)
    assert rsi_value.value == Decimal("100")

    # The scoring stage's own transaction rolled back completely -- the
    # Score insert that succeeded before the injected failure did not survive.
    assert get_score(conn, etf.etf_id, profile.scoring_profile_id, SESSION_DATE) is None
    row = conn.execute("SELECT COUNT(*) AS n FROM DimensionScore").fetchone()
    assert row["n"] == 0
    pipeline_name = f"scoring:{profile.name}:v{profile.version}:{etf.ticker}"
    status = conn.execute(
        "SELECT status FROM IngestionRun WHERE pipeline_name = ?", (pipeline_name,)
    ).fetchone()["status"]
    assert status == "failed"
