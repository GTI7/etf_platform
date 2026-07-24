from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from adapters.cli.formatting import (
    format_etf_analysis_report,
    format_ranked_report,
    format_score_history,
    format_status,
    format_update_result,
)
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
    get_scoring_profile,
    insert_dimension_score,
    insert_indicator_definition,
    insert_score,
    insert_scoring_profile,
)
from core.analytics.ranked_report import (
    ETFAnalysisReport,
    RankedETFReportEntry,
    ScoreHistoryEntry,
    compare_etfs,
    generate_ranked_etf_report,
    get_score_history,
)
from core.analytics.write_pipeline import WritePipelineResult
from core.market_data.domain.models import ETF, Calendar, IngestionRun, IngestionStatus, PriceBar, TradingSession
from core.market_data.persistence.repository import (
    get_etf_by_ticker,
    insert_calendar,
    insert_etf,
    insert_price_bar,
    insert_trading_session,
)
from core.market_data.providers.base import ProviderError, ProviderPriceBar
from core.shared.clock import FixedClock
from core.shared.money import Money
from core.store.connection import connect
from core.store.migrations import run_migrations

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
CALENDAR_ID = "XNYS"
TICKER = "SPY"
PROFILE_NAME = "REFERENCE"
PROFILE_VERSION = 1
SESSION_DATE = date(2026, 7, 14)
FORBIDDEN_WORDS = [
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


# ---------------------------------------------------------------------------
# etf status
# ---------------------------------------------------------------------------


def _status_argv(db_path: Path) -> list[str]:
    return [
        "status",
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
        "--db-path",
        str(db_path),
    ]


def test_status_reports_no_run_recorded_before_any_update(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)

    exit_code = main(_status_argv(db_path))

    assert exit_code == 0
    out = capsys.readouterr().out
    assert out.count("No run recorded") == 4


def test_status_reports_success_after_a_successful_update(
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
    update_exit_code = main(_update_argv(db_path), clock=clock, provider=provider)
    assert update_exit_code == 0
    capsys.readouterr()  # discard update's own output

    exit_code = main(_status_argv(db_path))

    assert exit_code == 0
    out = capsys.readouterr().out
    assert out.count("Status: success") == 4
    assert "Pipeline date: 2026-07-14" in out
    assert "Error: none" in out


def test_status_reports_failure_after_a_failed_update(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)
    update_exit_code = main(
        _update_argv(db_path),
        clock=FixedClock(datetime(2026, 7, 14, tzinfo=timezone.utc)),
        provider=_FailingProvider(),
    )
    assert update_exit_code != 0
    capsys.readouterr()  # discard update's own output

    exit_code = main(_status_argv(db_path))

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Status: failed" in out
    assert "upstream is down" in out


def test_status_ticker_not_found_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)
    argv = _status_argv(db_path)
    argv[argv.index("--ticker") + 1] = "DOES-NOT-EXIST"

    exit_code = main(argv)

    assert exit_code != 0
    err = capsys.readouterr().err
    assert err.strip() == "No ETF found for ticker DOES-NOT-EXIST"


def test_status_sma_definition_not_found_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)
    argv = _status_argv(db_path)
    argv[argv.index("--sma-name") + 1] = "NOT-A-DEFINITION"

    exit_code = main(argv)

    assert exit_code != 0
    err = capsys.readouterr().err
    assert "No indicator definition found" in err


def test_status_rsi_definition_not_found_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)
    argv = _status_argv(db_path)
    argv[argv.index("--rsi-name") + 1] = "NOT-A-DEFINITION"

    exit_code = main(argv)

    assert exit_code != 0
    err = capsys.readouterr().err
    assert "No indicator definition found" in err


def test_status_profile_not_found_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)
    argv = _status_argv(db_path)
    argv[argv.index("--profile-name") + 1] = "NOT-A-PROFILE"

    exit_code = main(argv)

    assert exit_code != 0
    err = capsys.readouterr().err
    assert "No scoring profile found" in err


def test_status_invalid_sma_version_exits_nonzero(tmp_path: Path) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)
    argv = _status_argv(db_path)
    argv[argv.index("--sma-version") + 1] = "not-an-int"

    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code != 0


def test_status_missing_required_argument_exits_nonzero(tmp_path: Path) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["status", "--ticker", TICKER])  # missing every other required flag

    assert exc_info.value.code != 0


def test_status_output_contains_no_forbidden_wording(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_update_fixture(db_path)

    exit_code = main(_status_argv(db_path))
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


def test_format_status_contains_only_supplied_run_fields() -> None:
    run = IngestionRun(
        ingestion_run_id="run-1",
        pipeline_name="price_ingestion:SPY",
        pipeline_date=date(2026, 7, 14),
        status=IngestionStatus.SUCCESS,
        started_at=datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 7, 14, 21, 0, 5, tzinfo=timezone.utc),
        error_message=None,
    )

    output = format_status("SPY", run, run, run, run)

    assert "Ticker: SPY" in output
    assert "Price ingestion:" in output
    assert "SMA:" in output
    assert "RSI:" in output
    assert "Score:" in output
    assert output.count("Status: success") == 4
    assert "Error: none" in output


def test_format_status_reports_no_run_recorded_factually() -> None:
    output = format_status("SPY", None, None, None, None)

    assert output.count("No run recorded") == 4


def test_format_status_reports_failed_run_error_message() -> None:
    run = IngestionRun(
        ingestion_run_id="run-1",
        pipeline_name="price_ingestion:SPY",
        pipeline_date=date(2026, 7, 14),
        status=IngestionStatus.FAILED,
        started_at=datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 7, 14, 21, 0, 5, tzinfo=timezone.utc),
        error_message="upstream is down",
    )

    output = format_status("SPY", run, None, None, None)

    assert "Status: failed" in output
    assert "Error: upstream is down" in output


# ---------------------------------------------------------------------------
# etf rank / etf compare (shared fixture: three ETFs, one session date)
# ---------------------------------------------------------------------------

RANK_TICKER_A = "SPY"
RANK_TICKER_B = "QQQ"
RANK_TICKER_C = "VTI"
RANK_SESSION_DATE = date(2026, 7, 14)


def _seed_ranked_fixture(db_path: Path) -> None:
    """Three ETFs, each with a Score for the same scoring profile/session
    date, with distinct overall_score values so ranking order is
    unambiguous in assertions."""
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

        for ticker, name, score_value in [
            (RANK_TICKER_A, "SPDR S&P 500", Decimal("80")),
            (RANK_TICKER_B, "Invesco QQQ Trust", Decimal("95")),
            (RANK_TICKER_C, "Vanguard Total Stock Market", Decimal("60")),
        ]:
            etf = ETF(
                etf_id=uuid.uuid4().hex,
                ticker=ticker,
                name=name,
                currency="USD",
                calendar_id=CALENDAR_ID,
                created_at=datetime.now(timezone.utc),
            )
            insert_etf(conn, etf)
            score = Score(
                score_id=uuid.uuid4().hex,
                etf_id=etf.etf_id,
                scoring_profile_id=profile.scoring_profile_id,
                session_date=RANK_SESSION_DATE,
                overall_score=score_value,
                computed_at=datetime.now(timezone.utc),
            )
            insert_score(conn, score)
            insert_dimension_score(
                conn,
                DimensionScore(
                    score_id=score.score_id,
                    dimension=Dimension.MOMENTUM,
                    value=score_value,
                    computed_at=datetime.now(timezone.utc),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def test_rank_success_prints_ranked_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    exit_code = main(
        [
            "rank",
            "--date",
            RANK_SESSION_DATE.isoformat(),
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--db-path",
            str(db_path),
        ]
    )

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Rank 1: QQQ" in out
    assert "Rank 2: SPY" in out
    assert "Rank 3: VTI" in out
    assert "Overall score: 95" in out


def test_rank_profile_not_found_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    exit_code = main(
        [
            "rank",
            "--date",
            RANK_SESSION_DATE.isoformat(),
            "--profile-name",
            "NOT-A-PROFILE",
            "--profile-version",
            "1",
            "--db-path",
            str(db_path),
        ]
    )

    assert exit_code != 0
    err = capsys.readouterr().err
    assert "No scoring profile found" in err


def test_rank_no_scores_for_date_prints_factual_empty_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    exit_code = main(
        [
            "rank",
            "--date",
            "2099-01-01",
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--db-path",
            str(db_path),
        ]
    )

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "No ranked scores found for this profile and session date." in out


def test_rank_invalid_date_exits_nonzero(tmp_path: Path) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "rank",
                "--date",
                "not-a-date",
                "--profile-name",
                PROFILE_NAME,
                "--profile-version",
                str(PROFILE_VERSION),
                "--db-path",
                str(db_path),
            ]
        )

    assert exc_info.value.code != 0


def test_rank_invalid_profile_version_exits_nonzero(tmp_path: Path) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "rank",
                "--date",
                RANK_SESSION_DATE.isoformat(),
                "--profile-name",
                PROFILE_NAME,
                "--profile-version",
                "not-an-int",
                "--db-path",
                str(db_path),
            ]
        )

    assert exc_info.value.code != 0


def test_rank_missing_required_argument_exits_nonzero(tmp_path: Path) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["rank", "--date", RANK_SESSION_DATE.isoformat()])  # missing profile-name/version/db-path

    assert exc_info.value.code != 0


def test_rank_risk_name_without_risk_version_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    exit_code = main(
        [
            "rank",
            "--date",
            RANK_SESSION_DATE.isoformat(),
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--risk-name",
            "MAX_DRAWDOWN",
            "--db-path",
            str(db_path),
        ]
    )

    assert exit_code != 0
    err = capsys.readouterr().err
    assert "Both --risk-name and --risk-version are required together" in err


def test_rank_unknown_risk_definition_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    exit_code = main(
        [
            "rank",
            "--date",
            RANK_SESSION_DATE.isoformat(),
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--risk-name",
            "MAX_DRAWDOWN",
            "--risk-version",
            "1",
            "--db-path",
            str(db_path),
        ]
    )

    assert exit_code != 0
    err = capsys.readouterr().err
    assert "No indicator definition found" in err


def test_rank_output_contains_no_forbidden_wording(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    exit_code = main(
        [
            "rank",
            "--date",
            RANK_SESSION_DATE.isoformat(),
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--db-path",
            str(db_path),
        ]
    )
    assert exit_code == 0

    out = capsys.readouterr().out.lower()
    for word in FORBIDDEN_WORDS:
        assert word not in out


def test_rank_cli_output_matches_direct_core_function_call(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Wiring check only: the CLI must not reformat, reorder, or reinterpret
    what generate_ranked_etf_report() already produced."""
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    exit_code = main(
        [
            "rank",
            "--date",
            RANK_SESSION_DATE.isoformat(),
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--db-path",
            str(db_path),
        ]
    )
    assert exit_code == 0
    cli_out = capsys.readouterr().out

    conn = connect(db_path)
    try:
        profile = get_scoring_profile(conn, PROFILE_NAME, PROFILE_VERSION)
        direct_report = generate_ranked_etf_report(conn, profile.scoring_profile_id, RANK_SESSION_DATE)
    finally:
        conn.close()

    expected = format_ranked_report("Ranked ETF report", RANK_SESSION_DATE, direct_report)
    assert cli_out.strip() == expected.strip()


# ---------------------------------------------------------------------------
# etf compare
# ---------------------------------------------------------------------------


def test_compare_success_prints_comparison_result(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    exit_code = main(
        [
            "compare",
            RANK_TICKER_A,
            RANK_TICKER_B,
            "--date",
            RANK_SESSION_DATE.isoformat(),
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--db-path",
            str(db_path),
        ]
    )

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "ETF comparison: SPY, QQQ" in out
    assert "Rank 1: QQQ" in out
    assert "Rank 2: SPY" in out
    assert "VTI" not in out  # not requested -- compare_etfs() ranks only the requested set


def test_compare_accepts_zero_tickers(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """compare_etfs([]) is documented as a valid 'compare nothing' request
    -- the CLI must not reject it, per the design review."""
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    exit_code = main(
        [
            "compare",
            "--date",
            RANK_SESSION_DATE.isoformat(),
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--db-path",
            str(db_path),
        ]
    )

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "ETF comparison: (no tickers)" in out
    assert "No ranked scores found for this profile and session date." in out


def test_compare_accepts_one_ticker(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A single ticker is a valid comparison of one, per compare_etfs()'s
    own documented precedent -- the CLI must not reject it."""
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    exit_code = main(
        [
            "compare",
            RANK_TICKER_A,
            "--date",
            RANK_SESSION_DATE.isoformat(),
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--db-path",
            str(db_path),
        ]
    )

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Rank 1: SPY" in out


def test_compare_ticker_not_found_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    exit_code = main(
        [
            "compare",
            "DOES-NOT-EXIST",
            "--date",
            RANK_SESSION_DATE.isoformat(),
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--db-path",
            str(db_path),
        ]
    )

    assert exit_code != 0
    err = capsys.readouterr().err
    assert err.strip() == "No ETF found for ticker DOES-NOT-EXIST"


def test_compare_profile_not_found_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    exit_code = main(
        [
            "compare",
            RANK_TICKER_A,
            "--date",
            RANK_SESSION_DATE.isoformat(),
            "--profile-name",
            "NOT-A-PROFILE",
            "--profile-version",
            "1",
            "--db-path",
            str(db_path),
        ]
    )

    assert exit_code != 0
    err = capsys.readouterr().err
    assert "No scoring profile found" in err


def test_compare_missing_required_argument_exits_nonzero(tmp_path: Path) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["compare", RANK_TICKER_A])  # missing date/profile-name/profile-version/db-path

    assert exc_info.value.code != 0


def test_compare_invalid_date_exits_nonzero(tmp_path: Path) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "compare",
                RANK_TICKER_A,
                "--date",
                "not-a-date",
                "--profile-name",
                PROFILE_NAME,
                "--profile-version",
                str(PROFILE_VERSION),
                "--db-path",
                str(db_path),
            ]
        )

    assert exc_info.value.code != 0


def test_compare_output_contains_no_forbidden_wording(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    exit_code = main(
        [
            "compare",
            RANK_TICKER_A,
            RANK_TICKER_B,
            "--date",
            RANK_SESSION_DATE.isoformat(),
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--db-path",
            str(db_path),
        ]
    )
    assert exit_code == 0

    out = capsys.readouterr().out.lower()
    for word in FORBIDDEN_WORDS:
        assert word not in out


def test_compare_cli_output_matches_direct_core_function_call(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Wiring check only: the CLI must not reformat, reorder, or reinterpret
    what compare_etfs() already produced."""
    db_path = tmp_path / "etf_platform_test.db"
    _seed_ranked_fixture(db_path)

    exit_code = main(
        [
            "compare",
            RANK_TICKER_A,
            RANK_TICKER_B,
            "--date",
            RANK_SESSION_DATE.isoformat(),
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--db-path",
            str(db_path),
        ]
    )
    assert exit_code == 0
    cli_out = capsys.readouterr().out

    conn = connect(db_path)
    try:
        profile = get_scoring_profile(conn, PROFILE_NAME, PROFILE_VERSION)
        etf_a = get_etf_by_ticker(conn, RANK_TICKER_A)
        etf_b = get_etf_by_ticker(conn, RANK_TICKER_B)
        direct_report = compare_etfs(
            conn, profile.scoring_profile_id, RANK_SESSION_DATE, [etf_a.etf_id, etf_b.etf_id]
        )
    finally:
        conn.close()

    expected = format_ranked_report(
        f"ETF comparison: {RANK_TICKER_A}, {RANK_TICKER_B}", RANK_SESSION_DATE, direct_report
    )
    assert cli_out.strip() == expected.strip()


# ---------------------------------------------------------------------------
# etf history
# ---------------------------------------------------------------------------

HISTORY_DATE_1 = date(2026, 7, 10)
HISTORY_DATE_2 = date(2026, 7, 14)


def _seed_history_fixture(db_path: Path) -> None:
    """One ETF with two Scores on two different session dates, under the
    same scoring profile -- enough to exercise get_score_history()'s
    ordering and optional date-range parameters."""
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
        for session_date, score_value in [(HISTORY_DATE_1, Decimal("70")), (HISTORY_DATE_2, Decimal("80"))]:
            score = Score(
                score_id=uuid.uuid4().hex,
                etf_id=etf.etf_id,
                scoring_profile_id=profile.scoring_profile_id,
                session_date=session_date,
                overall_score=score_value,
                computed_at=datetime.now(timezone.utc),
            )
            insert_score(conn, score)
            insert_dimension_score(
                conn,
                DimensionScore(
                    score_id=score.score_id,
                    dimension=Dimension.MOMENTUM,
                    value=score_value,
                    computed_at=datetime.now(timezone.utc),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def test_history_success_prints_score_history(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_history_fixture(db_path)

    exit_code = main(
        [
            "history",
            "--ticker",
            TICKER,
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--db-path",
            str(db_path),
        ]
    )

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Ticker: SPY" in out
    assert "Session date: 2026-07-10" in out
    assert "Overall score: 70" in out
    assert "Session date: 2026-07-14" in out
    assert "Overall score: 80" in out


def test_history_date_range_restricts_results(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_history_fixture(db_path)

    exit_code = main(
        [
            "history",
            "--ticker",
            TICKER,
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--start-date",
            HISTORY_DATE_2.isoformat(),
            "--db-path",
            str(db_path),
        ]
    )

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "2026-07-10" not in out
    assert "Session date: 2026-07-14" in out


def test_history_ticker_not_found_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_history_fixture(db_path)

    exit_code = main(
        [
            "history",
            "--ticker",
            "DOES-NOT-EXIST",
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--db-path",
            str(db_path),
        ]
    )

    assert exit_code != 0
    err = capsys.readouterr().err
    assert err.strip() == "No ETF found for ticker DOES-NOT-EXIST"


def test_history_profile_not_found_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_history_fixture(db_path)

    exit_code = main(
        [
            "history",
            "--ticker",
            TICKER,
            "--profile-name",
            "NOT-A-PROFILE",
            "--profile-version",
            "1",
            "--db-path",
            str(db_path),
        ]
    )

    assert exit_code != 0
    err = capsys.readouterr().err
    assert "No scoring profile found" in err


def test_history_no_scores_prints_factual_empty_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_history_fixture(db_path)

    exit_code = main(
        [
            "history",
            "--ticker",
            TICKER,
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--start-date",
            "2099-01-01",
            "--db-path",
            str(db_path),
        ]
    )

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "No score history found for this ticker and profile." in out


def test_history_invalid_start_date_exits_nonzero(tmp_path: Path) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_history_fixture(db_path)

    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "history",
                "--ticker",
                TICKER,
                "--profile-name",
                PROFILE_NAME,
                "--profile-version",
                str(PROFILE_VERSION),
                "--start-date",
                "not-a-date",
                "--db-path",
                str(db_path),
            ]
        )

    assert exc_info.value.code != 0


def test_history_missing_required_argument_exits_nonzero(tmp_path: Path) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_history_fixture(db_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["history", "--ticker", TICKER])  # missing profile-name/version/db-path

    assert exc_info.value.code != 0


def test_history_output_contains_no_forbidden_wording(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed_history_fixture(db_path)

    exit_code = main(
        [
            "history",
            "--ticker",
            TICKER,
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--db-path",
            str(db_path),
        ]
    )
    assert exit_code == 0

    out = capsys.readouterr().out.lower()
    for word in FORBIDDEN_WORDS:
        assert word not in out


def test_history_cli_output_matches_direct_core_function_call(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Wiring check only: the CLI must not reformat, reorder, or reinterpret
    what get_score_history() already produced."""
    db_path = tmp_path / "etf_platform_test.db"
    _seed_history_fixture(db_path)

    exit_code = main(
        [
            "history",
            "--ticker",
            TICKER,
            "--profile-name",
            PROFILE_NAME,
            "--profile-version",
            str(PROFILE_VERSION),
            "--db-path",
            str(db_path),
        ]
    )
    assert exit_code == 0
    cli_out = capsys.readouterr().out

    conn = connect(db_path)
    try:
        etf = get_etf_by_ticker(conn, TICKER)
        profile = get_scoring_profile(conn, PROFILE_NAME, PROFILE_VERSION)
        direct_history = get_score_history(conn, etf.etf_id, profile.scoring_profile_id)
    finally:
        conn.close()

    expected = format_score_history(TICKER, direct_history)
    assert cli_out.strip() == expected.strip()


# ---------------------------------------------------------------------------
# format_ranked_report / format_score_history
# ---------------------------------------------------------------------------


def test_format_ranked_report_contains_only_entry_fields() -> None:
    entries = [
        RankedETFReportEntry(
            rank=1,
            etf_id="etf-1",
            ticker="QQQ",
            name="Invesco QQQ Trust",
            overall_score=Decimal("95"),
            dimension_scores={Dimension.MOMENTUM: Decimal("95"), Dimension.VALUE: Decimal("60")},
            max_drawdown=Decimal("-0.08"),
        ),
    ]

    output = format_ranked_report("Ranked ETF report", date(2026, 7, 14), entries)

    assert "Ranked ETF report" in output
    assert "Session date: 2026-07-14" in output
    assert "Rank 1: QQQ (Invesco QQQ Trust)" in output
    assert "Overall score: 95" in output
    assert "MOMENTUM: 95" in output
    assert "VALUE: 60" in output
    assert "Max drawdown: -0.08" in output


def test_format_ranked_report_handles_missing_dimension_scores_and_max_drawdown() -> None:
    entries = [
        RankedETFReportEntry(
            rank=1,
            etf_id="etf-1",
            ticker="SPY",
            name="SPDR S&P 500",
            overall_score=Decimal("80"),
            dimension_scores={},
            max_drawdown=None,
        ),
    ]

    output = format_ranked_report("Ranked ETF report", date(2026, 7, 14), entries)

    assert "Dimension scores: none" in output
    assert "Max drawdown: N/A" in output


def test_format_ranked_report_empty_entries_prints_factual_message() -> None:
    output = format_ranked_report("Ranked ETF report", date(2026, 7, 14), [])

    assert "No ranked scores found for this profile and session date." in output


def test_format_ranked_report_header_distinguishes_rank_from_compare() -> None:
    rank_output = format_ranked_report("Ranked ETF report", date(2026, 7, 14), [])
    compare_output = format_ranked_report("ETF comparison: SPY, QQQ", date(2026, 7, 14), [])

    assert "Ranked ETF report" in rank_output
    assert "ETF comparison: SPY, QQQ" in compare_output
    assert "ETF comparison" not in rank_output
    assert "Ranked ETF report" not in compare_output


def test_format_score_history_contains_only_entry_fields() -> None:
    entries = [
        ScoreHistoryEntry(
            session_date=date(2026, 7, 10),
            overall_score=Decimal("70"),
            dimension_scores={Dimension.MOMENTUM: Decimal("70")},
        ),
        ScoreHistoryEntry(
            session_date=date(2026, 7, 14),
            overall_score=Decimal("80"),
            dimension_scores={Dimension.MOMENTUM: Decimal("80")},
        ),
    ]

    output = format_score_history("SPY", entries)

    assert "Ticker: SPY" in output
    assert "Session date: 2026-07-10" in output
    assert "Overall score: 70" in output
    assert "Session date: 2026-07-14" in output
    assert "Overall score: 80" in output


def test_format_score_history_handles_missing_dimension_scores() -> None:
    entries = [
        ScoreHistoryEntry(session_date=date(2026, 7, 14), overall_score=Decimal("80"), dimension_scores={}),
    ]

    output = format_score_history("SPY", entries)

    assert "Dimension scores: none" in output


def test_format_score_history_empty_entries_prints_factual_message() -> None:
    output = format_score_history("SPY", [])

    assert "No score history found for this ticker and profile." in output
