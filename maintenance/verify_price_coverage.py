"""Reusable, read-only PriceBar coverage verification tool.

Extracted (copied, not moved) from the two-directional per-ETF coverage
check inside ``maintenance/remediate_h3_invalid_pricebar_rows.py``
(``per_etf_coverage_check`` / ``run_post_remediation_validation``'s
``two_directional_coverage_per_etf`` section), formalized here as a
standalone tool per
``docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md`` Section 3, Step 3:
"Copy the two-directional missing/surplus check ... into a new
``maintenance/verify_price_coverage.py``, callable standalone or from a
test." The original remediation script is unchanged by this extraction
-- this module does not import from it, and nothing here writes to
``research_archive/`` or ``experiments/``.

**Read-only.** Every function here only executes ``SELECT`` statements
against the connection it is given. Nothing here writes, deletes, or
runs a migration -- this is a verification tool, not a remediation.

**Two-directional, per ETF, bounded by that ETF's own observed range.**
For each ETF, "expected" trading days are the calendar's
``is_trading_day = 1`` sessions between that ETF's own earliest and
latest stored ``PriceBar.session_date`` (not some global date range).
Two independent gaps are reported:

- **missing** -- an expected trading day with no ``PriceBar`` row.
- **invalid** -- a stored ``PriceBar`` row whose ``session_date`` is not
  a recognized trading day for that ETF's calendar within the observed
  range. This is the same invariant
  ``remediate_h3_invalid_pricebar_rows.py``'s ``PREDICATE_SQL`` checks
  (any row with no matching ``is_trading_day = 1`` ``TradingSession``
  row), restricted here to each ETF's own observed range rather than
  the whole table. Per ``docs/ARCHITECTURE_DECISIONS.md`` AD-023, a
  calendar gap and a genuinely non-trading date are deliberately not
  distinguished -- both mean the row does not belong.

Usage:
    python -m maintenance.verify_price_coverage
    python -m maintenance.verify_price_coverage --db path/to/other.db
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.market_data.persistence.database import connect  # noqa: E402

DB_PATH = REPO_ROOT / "experiments_etf_universe.db"


@dataclass(frozen=True, slots=True)
class CoverageReport:
    """Two-directional PriceBar coverage result for one ETF.

    Plain, serializable data -- suitable input for a future
    Governance-domain consumer (``DatasetIntegrityChecker`` /
    ``ArchiveVerifier`` per ``docs/PLATFORM_ARCHITECTURE_V1.md`` Section
    4.4), which does not exist yet. Nothing here depends on such a
    consumer existing.
    """

    ticker: str
    bar_count: int
    earliest: str | None
    latest: str | None
    expected_trading_days: int
    missing_dates: list[str]
    invalid_dates: list[str]

    @property
    def has_data(self) -> bool:
        return self.bar_count > 0

    @property
    def is_covered(self) -> bool:
        return self.has_data and not self.missing_dates and not self.invalid_dates


def check_etf_coverage(
    conn: sqlite3.Connection, etf_id: str, ticker: str, calendar_id: str
) -> CoverageReport:
    """Two-directional coverage check for a single ETF. Pure read: issues
    only SELECT statements, never mutates `conn`."""
    bars = conn.execute(
        "SELECT session_date FROM PriceBar WHERE etf_id = ? ORDER BY session_date",
        (etf_id,),
    ).fetchall()
    stored_dates = {b["session_date"] for b in bars}

    if not stored_dates:
        return CoverageReport(
            ticker=ticker,
            bar_count=0,
            earliest=None,
            latest=None,
            expected_trading_days=0,
            missing_dates=[],
            invalid_dates=[],
        )

    earliest, latest = min(stored_dates), max(stored_dates)
    expected = {
        row["session_date"]
        for row in conn.execute(
            """
            SELECT session_date FROM TradingSession
            WHERE calendar_id = ? AND is_trading_day = 1
              AND session_date BETWEEN ? AND ?
            """,
            (calendar_id, earliest, latest),
        ).fetchall()
    }
    missing = sorted(expected - stored_dates)
    invalid = sorted(stored_dates - expected)

    return CoverageReport(
        ticker=ticker,
        bar_count=len(stored_dates),
        earliest=earliest,
        latest=latest,
        expected_trading_days=len(expected),
        missing_dates=missing,
        invalid_dates=invalid,
    )


def verify_price_coverage(conn: sqlite3.Connection) -> dict[str, CoverageReport]:
    """Read-only, two-directional PriceBar coverage check across every ETF
    the database currently has. Returns one CoverageReport per ticker."""
    etfs = conn.execute("SELECT etf_id, ticker, calendar_id FROM ETF ORDER BY ticker").fetchall()
    return {
        etf["ticker"]: check_etf_coverage(conn, etf["etf_id"], etf["ticker"], etf["calendar_id"])
        for etf in etfs
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        type=Path,
        default=DB_PATH,
        help="Path to the sqlite database to check, read-only (default: %(default)s)",
    )
    args = parser.parse_args()

    conn = connect(args.db)
    try:
        reports = verify_price_coverage(conn)
    finally:
        conn.close()

    payload = {ticker: asdict(report) for ticker, report in reports.items()}
    print(json.dumps(payload, indent=2))

    any_uncovered = any(not report.is_covered for report in reports.values())
    return 1 if any_uncovered else 0


if __name__ == "__main__":
    raise SystemExit(main())
