from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from adapters.cli.formatting import format_etf_analysis_report, format_update_result
from adapters.cli.main import main
from core.analytics.domain.models import (
    Dimension,
    DimensionScore,
    IndicatorDefinition,
    Score,
    ScoringProfile,
    serialize_parameters,
)
from core.analytics.persistence.repository import (
    insert_dimension_score,
    insert_indicator_definition,
    insert_score,
    insert_scoring_profile,
)
from core.analytics.ranked_report import ETFAnalysisReport
from core.analytics.write_pipeline import WritePipelineResult
from core.market_data.domain.models import ETF, Calendar, PriceBar, TradingSession
from core.market_data.persistence.database import connect
from core.market_data.persistence.migrations import run_migrations
from core.market_data.persistence.repository import (
    insert_calendar,
    insert_etf,
    insert_price_bar,
    insert_trading_session,
)
from core.market_data.providers.base import ProviderError, ProviderPriceBar
from core.shared.clock import FixedClock
from core.shared.money import Money

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
CALENDAR_ID = "XNYS"
TICKER = "SPY"
PROFILE_NAME = "REFERENCE"
PROFILE_VERSION = 1
SESSION_DATE = date(2026, 7, 14)


def _seed(db_path: Path, *, with_score: bool = True) -> None:
    """Seed a fresh sqlite file at db_path via its own connection, committed
    and closed before the CLI opens its own connection to the same file --
    this mirrors how the CLI is actually used (a separate process/call
    opening the database independently), unlike every other test in this
    project that shares one connection for both setup and the call under
    test."""
    conn = connect(db_path)
    try:
        run_migrations(conn, MIGRATIONS_DIR)
        insert_calendar(
            conn,
            Calendar(
                calendar_id=CALENDAR_ID,
                name="New York Stock Exchange",
                exchange="NYSE",
                timezone="America/New_York",
            ),
        )
        etf = ETF(
            etf_id=uuid.uuid4().hex,
            ticker=TICKER,
            name="SPDR S&P 500",
            currency="USD",
            calendar_id=CALENDAR_ID,
            created_at=datetime.now(timezone.utc),
        )
        insert_etf(conn, etf)
        profile = ScoringProfile(
            scoring_profile_id=uuid.uuid4().hex,
            name=PROFILE_NAME,
            version=PROFILE_VERSION,
            parameters=serialize_parameters(
                {"dimensions": {"MOMENTUM": {"indicator_name": "SMA", "indicator_version": 1}}}
            ),
            created_at=datetime.now(timezone.utc),
        )
        insert_scoring_profile(conn, profile)
        if with_score:
            score = Score(
                score_id=uuid.uuid4().hex,
                etf_id=etf.etf_id,
                scoring_profile_id=profile.scoring_profile_id,
                session_date=SESSION_DATE,
                overall_score=Decimal("80"),
                computed_at=datetime.now(timezone.utc),
            )
            insert_score(conn, score)
            insert_dimension_score(
                conn,
                DimensionScore(
                    score_id=score.score_id,
                    dimension=Dimension.MOMENTUM,
                    value=Decimal("90"),
                    computed_at=datetime.now(timezone.utc),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def test_main_successful_execution_prints_report_and_returns_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed(db_path)

    exit_code = main(
        ["analyze", TICKER, PROFILE_NAME, str(PROFILE_VERSION), SESSION_DATE.isoformat(), str(db_path)]
    )

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Ticker: SPY" in out
    assert "Overall score: 80" in out
    assert "MOMENTUM: 90" in out


def test_main_ticker_not_found_returns_nonzero_and_prints_factual_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed(db_path)

    exit_code = main(
        [
            "analyze",
            "DOES-NOT-EXIST",
            PROFILE_NAME,
            str(PROFILE_VERSION),
            SESSION_DATE.isoformat(),
            str(db_path),
        ]
    )

    assert exit_code != 0
    err = capsys.readouterr().err
    assert err.strip() == "No ETF found for ticker DOES-NOT-EXIST"


def test_main_profile_not_found_returns_nonzero_and_prints_factual_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed(db_path)

    exit_code = main(
        ["analyze", TICKER, "NOT-A-PROFILE", "1", SESSION_DATE.isoformat(), str(db_path)]
    )

    assert exit_code != 0
    err = capsys.readouterr().err
    assert "No scoring profile found" in err


def test_main_missing_score_returns_nonzero_and_prints_factual_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed(db_path, with_score=False)

    exit_code = main(
        ["analyze", TICKER, PROFILE_NAME, str(PROFILE_VERSION), SESSION_DATE.isoformat(), str(db_path)]
    )

    assert exit_code != 0
    err = capsys.readouterr().err
    assert "No Score for" in err


def test_main_invalid_profile_version_exits_nonzero(tmp_path: Path) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed(db_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["analyze", TICKER, PROFILE_NAME, "not-an-int", SESSION_DATE.isoformat(), str(db_path)])

    assert exc_info.value.code != 0


def test_main_invalid_session_date_exits_nonzero(tmp_path: Path) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed(db_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["analyze", TICKER, PROFILE_NAME, str(PROFILE_VERSION), "not-a-date", str(db_path)])

    assert exc_info.value.code != 0


def test_main_missing_required_argument_exits_nonzero(tmp_path: Path) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed(db_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["analyze", TICKER, PROFILE_NAME, str(PROFILE_VERSION)])  # missing session_date and db_path

    assert exc_info.value.code != 0


def test_main_missing_command_exits_nonzero(tmp_path: Path) -> None:
    """No subcommand at all -- argparse's required=True on the subparsers
    group must reject this, same clean SystemExit(2) as any other missing
    required argument."""
    with pytest.raises(SystemExit) as exc_info:
        main([])

    assert exc_info.value.code != 0


def test_format_etf_analysis_report_contains_only_report_fields() -> None:
    report = ETFAnalysisReport(
        etf_id="etf-1",
        ticker="SPY",
        name="SPDR S&P 500",
        analysis_date=date(2026, 7, 14),
        scoring_profile_id="profile-1",
        overall_score=Decimal("80"),
        dimension_scores={Dimension.MOMENTUM: Decimal("90"), Dimension.VALUE: Decimal("70")},
        max_drawdown=Decimal("-0.12"),
        rank=1,
        peer_count=2,
    )

    output = format_etf_analysis_report(report)

    assert "Ticker: SPY" in output
    assert "Rank: 1 of 2" in output
    assert "MOMENTUM: 90" in output
    assert "VALUE: 70" in output
    assert "Max drawdown: -0.12" in output


def test_format_etf_analysis_report_handles_no_dimension_scores_and_no_max_drawdown() -> None:
    report = ETFAnalysisReport(
        etf_id="etf-1",
        ticker="SPY",
        name="SPDR S&P 500",
        analysis_date=date(2026, 7, 14),
        scoring_profile_id="profile-1",
        overall_score=Decimal("80"),
        dimension_scores={},
        max_drawdown=None,
        rank=1,
        peer_count=1,
    )

    output = format_etf_analysis_report(report)

    assert "Dimension scores: none" in output
    assert "Max drawdown: N/A" in output


def test_cli_output_contains_no_forbidden_wording(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Regression guard for the 'candidates, not recommendations' boundary:
    the formatted output must never contain evaluative/recommendation
    language."""
    db_path = tmp_path / "etf_platform_test.db"
    _seed(db_path)

    exit_code = main(
        ["analyze", TICKER, PROFILE_NAME, str(PROFILE_VERSION), SESSION_DATE.isoformat(), str(db_path)]
    )
    assert exit_code == 0

    out = capsys.readouterr().out.lower()
    forbidden = [
        "recommend",
        "buy",
        "sell",
        "best",
        "worst",
        "should",
        "good",
        "bad",
        "strong",
        "weak",
    ]
    for word in forbidden:
        assert word not in out


# ---------------------------------------------------------------------------
# etf update
# ---------------------------------------------------------------------------

UPDATE_PRIOR_DAY = date(2026, 7, 13)
UPDATE_SESSION_DATE = date(2026, 7, 14)
SMA_NAME = "SMA"
SMA_VERSION = 1
RSI_NAME = "RSI"
RSI_VERSION = 1


class _FakeProvider:
    """A minimal DataProvider stand-in returning canned bars -- no network
    access, no third-party mocking library, the same pattern
    tests/test_write_pipeline.py already establishes for this project."""

    name = "fake"

    def __init__(self, bars: list[ProviderPriceBar]) -> None:
        self._bars = bars

    def fetch_daily_bars(
        self, ticker: str, start_date: date, end_date: date
    ) -> list[ProviderPriceBar]:
        return self._bars


class _FailingProvider:
    """A DataProvider stand-in that always fails -- exercises the
    'pipeline failure' error path without needing a real upstream outage."""

    name = "failing"

    def fetch_daily_bars(
        self, ticker: str, start_date: date, end_date: date
    ) -> list[ProviderPriceBar]:
        raise ProviderError("upstream is down")


def _seed_update_fixture(db_path: Path) -> None:
    """Two consecutive trading days with PRIOR_DAY already priced --
    everything a window=1 SMA / period=1 RSI / score computation needs for
    UPDATE_SESSION_DATE, once UPDATE_SESSION_DATE itself is ingested by the
    update command under test."""
    conn = connect(db_path)
    try:
        run_migrations(conn, MIGRATIONS_DIR)
        insert_calendar(
            conn,
            Calendar(
                calendar_id=CALENDAR_ID,
                name="New York Stock Exchange",
                exchange="NYSE",
                timezone="America/New_York",
            ),
        )
        for day in (UPDATE_PRIOR_DAY, UPDATE_SESSION_DATE):
            insert_trading_session(
                conn,
                TradingSession(
                    calendar_id=CALENDAR_ID,
                    session_date=day,
                    is_trading_day=True,
                    close_time_utc=None,
                ),
            )
        etf = ETF(
            etf_id=uuid.uuid4().hex,
            ticker=TICKER,
            name="SPDR S&P 500",
            currency="USD",
            calendar_id=CALENDAR_ID,
            created_at=datetime.now(timezone.utc),
        )
        insert_etf(conn, etf)
        price = Money(Decimal("100"), "USD")
        insert_price_bar(
            conn,
            PriceBar(
                price_bar_id=uuid.uuid4().hex,
                etf_id=etf.etf_id,
                session_date=UPDATE_PRIOR_DAY,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=1,
                source="test",
                ingested_at=datetime.now(timezone.utc),
            ),
        )
        insert_indicator_definition(
            conn,
            IndicatorDefinition(
                indicator_definition_id=uuid.uuid4().hex,
                name=SMA_NAME,
                version=SMA_VERSION,
                parameters=serialize_parameters({"window": 1}),
                created_at=datetime.now(timezone.utc),
            ),
        )
        insert_indicator_definition(
            conn,
            IndicatorDefinition(
                indicator_definition_id=uuid.uuid4().hex,
                name=RSI_NAME,
                version=RSI_VERSION,
                parameters=serialize_parameters({"period": 1}),
                created_at=datetime.now(timezone.utc),
            ),
        )
        insert_scoring_profile(
            conn,
            ScoringProfile(
                scoring_profile_id=uuid.uuid4().hex,
                name=PROFILE_NAME,
                version=PROFILE_VERSION,
                parameters=serialize_parameters(
                    {
                        "dimensions": {
                            "MOMENTUM": {"indicator_name": SMA_NAME, "indicator_version": SMA_VERSION},
                            "VALUE": {"indicator_name": RSI_NAME, "indicator_version": RSI_VERSION},
                        }
                    }
                ),
                created_at=datetime.now(timezone.utc),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _update_argv(db_path: Path) -> list[str]:
    return [
        "update",
        "--ticker",
        TICKER,
        "--sma-name",
        SMA_NAME,
        "--sma-version",
        str(SMA_VERSION),
        "--rsi-name",
        RSI_NAME,
        "--rsi-version",
        str(RSI_VERSION),
        "--profile-name",
        PROFILE_NAME,
        "--profile-version",
        str(PROFILE_VERSION),
        "--session-date",
        UPDATE_SESSION_DATE.isoformat(),
        "--db-path",
        str(db_path),
    ]


def test_update_success_runs_existing_pipeline_and_prints_result(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)
    clock = FixedClock(datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc))
    provider = _FakeProvider(
        [
            ProviderPriceBar(
                session_date=UPDATE_SESSION_DATE,
                open=Decimal("103"),
                high=Decimal("103"),
                low=Decimal("103"),
                close=Decimal("103"),
                volume=1000,
                currency="USD",
            )
        ]
    )

    exit_code = main(_update_argv(db_path), clock=clock, provider=provider)

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "ETF update completed" in out
    assert "Ticker: SPY" in out
    assert "Session date: 2026-07-14" in out
    assert "Price ingestion run:" in out
    assert "SMA run:" in out
    assert "RSI run:" in out
    assert "Score run:" in out


def test_update_ticker_not_found_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)
    argv = _update_argv(db_path)
    argv[argv.index("--ticker") + 1] = "DOES-NOT-EXIST"

    exit_code = main(argv, clock=FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc)), provider=_FakeProvider([]))

    assert exit_code != 0
    err = capsys.readouterr().err
    assert err.strip() == "No ETF found for ticker DOES-NOT-EXIST"


def test_update_sma_definition_not_found_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)
    argv = _update_argv(db_path)
    argv[argv.index("--sma-name") + 1] = "NOT-A-DEFINITION"

    exit_code = main(argv, clock=FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc)), provider=_FakeProvider([]))

    assert exit_code != 0
    err = capsys.readouterr().err
    assert "No indicator definition found" in err


def test_update_rsi_definition_not_found_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)
    argv = _update_argv(db_path)
    argv[argv.index("--rsi-name") + 1] = "NOT-A-DEFINITION"

    exit_code = main(argv, clock=FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc)), provider=_FakeProvider([]))

    assert exit_code != 0
    err = capsys.readouterr().err
    assert "No indicator definition found" in err


def test_update_profile_not_found_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)
    argv = _update_argv(db_path)
    argv[argv.index("--profile-name") + 1] = "NOT-A-PROFILE"

    exit_code = main(argv, clock=FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc)), provider=_FakeProvider([]))

    assert exit_code != 0
    err = capsys.readouterr().err
    assert "No scoring profile found" in err


def test_update_pipeline_failure_returns_nonzero_with_factual_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)

    exit_code = main(
        _update_argv(db_path),
        clock=FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc)),
        provider=_FailingProvider(),
    )

    assert exit_code != 0
    err = capsys.readouterr().err
    assert err.strip() == "upstream is down"


def test_update_invalid_sma_version_exits_nonzero(tmp_path: Path) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)
    argv = _update_argv(db_path)
    argv[argv.index("--sma-version") + 1] = "not-an-int"

    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code != 0


def test_update_missing_required_argument_exits_nonzero(tmp_path: Path) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["update", "--ticker", TICKER])  # missing every other required flag

    assert exc_info.value.code != 0


def test_update_output_contains_no_forbidden_wording(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)
    clock = FixedClock(datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc))
    provider = _FakeProvider(
        [
            ProviderPriceBar(
                session_date=UPDATE_SESSION_DATE,
                open=Decimal("103"),
                high=Decimal("103"),
                low=Decimal("103"),
                close=Decimal("103"),
                volume=1000,
                currency="USD",
            )
        ]
    )

    exit_code = main(_update_argv(db_path), clock=clock, provider=provider)
    assert exit_code == 0

    out = capsys.readouterr().out.lower()
    forbidden = [
        "recommend",
        "buy",
        "sell",
        "best",
        "worst",
        "should",
        "good",
        "bad",
        "strong",
        "weak",
    ]
    for word in forbidden:
        assert word not in out


def test_format_update_result_contains_only_result_fields() -> None:
    result = WritePipelineResult(
        price_ingestion_run_id="ingest-run-1",
        sma_run_id="sma-run-1",
        rsi_run_id="rsi-run-1",
        score_run_id="score-run-1",
    )

    output = format_update_result("SPY", UPDATE_SESSION_DATE, result)

    assert "Ticker: SPY" in output
    assert "Session date: 2026-07-14" in output
    assert "Price ingestion run: ingest-run-1" in output
    assert "SMA run: sma-run-1" in output
    assert "RSI run: rsi-run-1" in output
    assert "Score run: score-run-1" in output


def test_format_update_result_reports_skipped_ingestion_factually() -> None:
    result = WritePipelineResult(
        price_ingestion_run_id=None,
        sma_run_id="sma-run-1",
        rsi_run_id="rsi-run-1",
        score_run_id="score-run-1",
    )

    output = format_update_result("SPY", UPDATE_SESSION_DATE, result)

    assert "Price ingestion run: skipped (price data already present)" in output
