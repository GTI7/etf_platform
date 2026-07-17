from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from adapters.cli.formatting import format_etf_analysis_report
from adapters.cli.main import main
from core.analytics.domain.models import (
    Dimension,
    DimensionScore,
    Score,
    ScoringProfile,
    serialize_parameters,
)
from core.analytics.persistence.repository import (
    insert_dimension_score,
    insert_score,
    insert_scoring_profile,
)
from core.analytics.ranked_report import ETFAnalysisReport
from core.market_data.domain.models import ETF, Calendar
from core.market_data.persistence.database import connect
from core.market_data.persistence.migrations import run_migrations
from core.market_data.persistence.repository import insert_calendar, insert_etf

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
        [TICKER, PROFILE_NAME, str(PROFILE_VERSION), SESSION_DATE.isoformat(), str(db_path)]
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
        ["DOES-NOT-EXIST", PROFILE_NAME, str(PROFILE_VERSION), SESSION_DATE.isoformat(), str(db_path)]
    )

    assert exit_code != 0
    err = capsys.readouterr().err
    assert err.strip() == "No ETF found for ticker DOES-NOT-EXIST"


def test_main_profile_not_found_returns_nonzero_and_prints_factual_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed(db_path)

    exit_code = main([TICKER, "NOT-A-PROFILE", "1", SESSION_DATE.isoformat(), str(db_path)])

    assert exit_code != 0
    err = capsys.readouterr().err
    assert "No scoring profile found" in err


def test_main_missing_score_returns_nonzero_and_prints_factual_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed(db_path, with_score=False)

    exit_code = main(
        [TICKER, PROFILE_NAME, str(PROFILE_VERSION), SESSION_DATE.isoformat(), str(db_path)]
    )

    assert exit_code != 0
    err = capsys.readouterr().err
    assert "No Score for" in err


def test_main_invalid_profile_version_exits_nonzero(tmp_path: Path) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed(db_path)

    with pytest.raises(SystemExit) as exc_info:
        main([TICKER, PROFILE_NAME, "not-an-int", SESSION_DATE.isoformat(), str(db_path)])

    assert exc_info.value.code != 0


def test_main_invalid_session_date_exits_nonzero(tmp_path: Path) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed(db_path)

    with pytest.raises(SystemExit) as exc_info:
        main([TICKER, PROFILE_NAME, str(PROFILE_VERSION), "not-a-date", str(db_path)])

    assert exc_info.value.code != 0


def test_main_missing_required_argument_exits_nonzero(tmp_path: Path) -> None:
    db_path = tmp_path / "etf_platform_test.db"
    _seed(db_path)

    with pytest.raises(SystemExit) as exc_info:
        main([TICKER, PROFILE_NAME, str(PROFILE_VERSION)])  # missing session_date and db_path

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
        [TICKER, PROFILE_NAME, str(PROFILE_VERSION), SESSION_DATE.isoformat(), str(db_path)]
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
