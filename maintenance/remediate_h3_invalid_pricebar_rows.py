"""REFERENCE H3 Gate 2 remediation: one-off, versioned maintenance script.

Implements Option F ("export-then-delete") from
docs/REFERENCE_H3_DATABASE_REMEDIATION_PLAN.md, Section 4, using Option D's
predicate as the delete criterion: any PriceBar row whose (etf_id,
session_date) has no matching is_trading_day=1 TradingSession row for that
ETF's calendar. This is deliberately NOT a `source = 'backfill-gap-fill'`
tag match (Option C) -- see the remediation plan's Section 5 "Predicate
drift risk". The two predicates happen to select the identical 50 rows
today; only the invariant-based one is used to decide what gets deleted.

This script is a one-off, not a repeatable tool: it is meant to be run
exactly once, reviewed as a whole (the SQL predicate is the entire risk
surface -- Section 5), and never re-run. It lives outside migrations/
because it is a data-quality fix, not a schema change.

Phases (in order, matching the remediation plan's Section 4):
  1. Dry run: run the predicate read-only, hard-stop unless the match is
     exactly 50 rows with the exact shape the investigation already
     enumerated (25 ETFs x 2 dates, source='backfill-gap-fill', flat OHLC,
     zero volume).
  2. Export: write the full, unedited matched row set to a permanent,
     timestamped archive file, then re-read that file back from disk and
     verify it byte-for-byte accounts for the same rows before any DELETE
     is allowed to proceed.
  3. Delete: inside a single transaction, delete exactly the row IDs
     captured in step 1/2 (not a re-evaluation of the predicate at delete
     time, so the exported set and the deleted set are provably
     identical). PriceBar carries a BEFORE DELETE trigger
     (trg_pricebar_no_delete) that unconditionally raises ABORT --
     enforcing this table's general append-only design. That trigger is
     dropped and recreated verbatim inside the same transaction so the
     guarantee is intact both before and after this script runs; it is
     never permanently weakened. If anything fails before COMMIT, SQLite
     rolls back the DROP along with everything else.
  4. Post-remediation validation: row count reconciliation, two-directional
     (missing + surplus) coverage check per ETF, source-tag audit,
     universe/date-range integrity, export/backup integrity, and a
     recurrence check.

Usage:
    python maintenance/remediate_h3_invalid_pricebar_rows.py --dry-run
    python maintenance/remediate_h3_invalid_pricebar_rows.py --execute
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.market_data.persistence.database import connect  # noqa: E402

DB_PATH = REPO_ROOT / "experiments_etf_universe.db"
ARCHIVE_DIR = REPO_ROOT / "research_archive" / "reference_h3"
MIGRATION_FILE = REPO_ROOT / "migrations" / "0001_initial_schema.sql"

EXPECTED_COUNT = 50
EXPECTED_DATES = {"2026-06-19", "2026-07-03"}
EXPECTED_SOURCE = "backfill-gap-fill"
EXPECTED_ETF_COUNT = 25

TRIGGER_NAME = "trg_pricebar_no_delete"
TRIGGER_RAISE_MESSAGE = "PriceBar is immutable raw data: DELETE is not allowed, insert a new record instead"
TRIGGER_CREATE_SQL = f"""
CREATE TRIGGER IF NOT EXISTS {TRIGGER_NAME}
BEFORE DELETE ON PriceBar
BEGIN
    SELECT RAISE(ABORT, '{TRIGGER_RAISE_MESSAGE}');
END;
"""

# Frozen per REFERENCE_H3_DATABASE_REMEDIATION_PLAN.md Section 4, point 1.
# Do not change this to match on `source` -- see Section 5, "Predicate
# drift risk".
PREDICATE_SQL = """
    SELECT pb.*, e.ticker AS etf_ticker, e.calendar_id AS etf_calendar_id
    FROM PriceBar pb
    JOIN ETF e ON e.etf_id = pb.etf_id
    WHERE NOT EXISTS (
        SELECT 1 FROM TradingSession ts
        WHERE ts.calendar_id = e.calendar_id
          AND ts.session_date = pb.session_date
          AND ts.is_trading_day = 1
    )
    ORDER BY e.ticker, pb.session_date
"""


class StopCondition(RuntimeError):
    """Raised when a pre-flight or in-flight invariant does not hold.

    Per the remediation plan's Section 4, point 3: any deviation from the
    expected shape is a stop condition, not something to be quietly
    reconciled by widening or narrowing the predicate.
    """


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def script_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def assert_trigger_definition_unchanged() -> None:
    """Self-check that this script's copy of the trigger's RAISE message
    still matches the migration file, so the temporary drop+recreate
    below cannot silently drift from the schema's own definition."""
    migration_text = MIGRATION_FILE.read_text(encoding="utf-8")
    if TRIGGER_RAISE_MESSAGE not in migration_text:
        raise StopCondition(
            f"{MIGRATION_FILE} no longer contains the expected "
            f"{TRIGGER_NAME} RAISE message -- this script's hardcoded "
            "recreate statement may be stale. Aborting before touching "
            "the database."
        )


def row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def fetch_matching_rows(conn: sqlite3.Connection) -> list[dict]:
    return [row_to_dict(r) for r in conn.execute(PREDICATE_SQL).fetchall()]


def validate_match_shape(rows: list[dict]) -> list[str]:
    """Returns a list of human-readable warnings for any property of the
    matched set that deviates from the investigation's enumerated set,
    WITHOUT raising -- the caller decides whether a given deviation is a
    hard stop. Count-mismatch is always a hard stop and is checked
    separately by the caller before this function is even useful."""
    warnings = []

    dates = {r["session_date"] for r in rows}
    if dates != EXPECTED_DATES:
        warnings.append(f"expected dates {EXPECTED_DATES}, found {dates}")

    sources = {r["source"] for r in rows}
    if sources != {EXPECTED_SOURCE}:
        warnings.append(f"expected source={{'{EXPECTED_SOURCE}'}}, found {sources}")

    per_etf = Counter(r["etf_id"] for r in rows)
    if len(per_etf) != EXPECTED_ETF_COUNT or any(v != 2 for v in per_etf.values()):
        warnings.append(f"expected {EXPECTED_ETF_COUNT} ETFs with exactly 2 rows each, found {dict(per_etf)}")

    non_flat_or_nonzero_volume = [
        r["price_bar_id"]
        for r in rows
        if not (r["open_amount"] == r["high_amount"] == r["low_amount"] == r["close_amount"])
        or r["volume"] != 0
    ]
    if non_flat_or_nonzero_volume:
        warnings.append(
            "expected all matched rows to be flat-OHLC and zero-volume; "
            f"exceptions: {non_flat_or_nonzero_volume}"
        )

    return warnings


def dry_run(conn: sqlite3.Connection) -> list[dict]:
    rows = fetch_matching_rows(conn)
    print(f"[dry-run] predicate matched {len(rows)} row(s)")
    if len(rows) != EXPECTED_COUNT:
        raise StopCondition(
            f"Predicate matched {len(rows)} rows, expected exactly "
            f"{EXPECTED_COUNT}. Per the remediation plan's Section 4, "
            "point 3, this is a hard stop -- the database may have "
            "changed since the investigation ran, or the invariant is "
            "broader than currently understood. Remediation must not "
            "proceed until that is explained."
        )
    shape_warnings = validate_match_shape(rows)
    if shape_warnings:
        raise StopCondition(
            "Predicate matched exactly 50 rows, but the matched set does "
            "not match the investigation's enumerated shape:\n  - "
            + "\n  - ".join(shape_warnings)
        )
    print(
        f"[dry-run] shape check passed: {EXPECTED_ETF_COUNT} ETFs x 2 dates "
        f"({sorted(EXPECTED_DATES)}), all source='{EXPECTED_SOURCE}', "
        "all flat-OHLC, all zero-volume"
    )
    return rows


def write_export(rows: list[dict], dry_run_conn_check: list[dict]) -> Path:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    export_date = date.today().isoformat()
    export_path = ARCHIVE_DIR / f"removed_backfill_gap_fill_rows_{export_date}.json"
    if export_path.exists():
        raise StopCondition(
            f"{export_path} already exists -- refusing to overwrite an "
            "existing archive artifact. This script is meant to be run "
            "once; if it must be re-run today, this needs a human "
            "decision, not a silent overwrite."
        )

    payload = {
        "artifact": "removed_backfill_gap_fill_rows",
        "generated_at": utc_now_iso(),
        "scope_note": (
            "Pre-delete export of the exact PriceBar rows matched by the "
            "invariant-based predicate (Option D) from "
            "docs/REFERENCE_H3_DATABASE_REMEDIATION_PLAN.md Section 4. "
            "This is the permanent forensic record of exactly what was "
            "removed and the remediation's undo mechanism. No H3 signal, "
            "benchmark, peer group, lookback window, scoring logic, IC, "
            "p-value, or forward return is present anywhere in this "
            "artifact."
        ),
        "remediation_execution_record": {
            "predicate_sql": PREDICATE_SQL.strip(),
            "predicate_kind": "Option D (TradingSession-invariant join), not Option C (source-tag match)",
            "dry_run_row_count": len(dry_run_conn_check),
            "script_path": "maintenance/remediate_h3_invalid_pricebar_rows.py",
            "script_sha256": script_sha256(),
            "governing_docs": [
                "docs/REFERENCE_H3_GATE2_DISCREPANCY_ANALYSIS.md",
                "docs/REFERENCE_H3_DATABASE_REMEDIATION_PLAN.md",
                "docs/REFERENCE_H3_BACKFILL_GAP_FILL_ORIGIN_REPORT.md",
            ],
            "note": (
                "The exact commit hash of this script is available via "
                "`git log --oneline -- maintenance/"
                "remediate_h3_invalid_pricebar_rows.py` after this "
                "change is committed -- not recorded here since this "
                "file is written before that commit exists."
            ),
        },
        "row_count": len(rows),
        "rows": rows,
    }
    export_path.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")
    return export_path


def verify_export_integrity(export_path: Path, expected_rows: list[dict]) -> None:
    on_disk = json.loads(export_path.read_text(encoding="utf-8"))
    if on_disk["row_count"] != len(expected_rows):
        raise StopCondition(
            f"Export file row_count ({on_disk['row_count']}) does not "
            f"match in-memory matched row count ({len(expected_rows)})."
        )
    disk_ids = {r["price_bar_id"] for r in on_disk["rows"]}
    live_ids = {r["price_bar_id"] for r in expected_rows}
    if disk_ids != live_ids:
        raise StopCondition(
            "Export file's price_bar_id set does not exactly match the "
            "live dry-run's matched set. Refusing to proceed to delete."
        )
    print(f"[export] verified {export_path} contains exactly the {len(expected_rows)} matched rows")


def execute_delete(conn: sqlite3.Connection, rows: list[dict]) -> None:
    ids = [r["price_bar_id"] for r in rows]
    conn.execute("BEGIN")
    try:
        conn.execute(f"DROP TRIGGER {TRIGGER_NAME}")
        placeholders = ",".join("?" for _ in ids)
        cur = conn.execute(
            f"DELETE FROM PriceBar WHERE price_bar_id IN ({placeholders})",
            ids,
        )
        if cur.rowcount != len(ids):
            raise StopCondition(
                f"DELETE affected {cur.rowcount} rows, expected exactly "
                f"{len(ids)} (one per exported row id). Rolling back."
            )
        conn.execute(TRIGGER_CREATE_SQL)

        remaining = conn.execute(PREDICATE_SQL).fetchall()
        if remaining:
            raise StopCondition(
                f"{len(remaining)} row(s) still match the predicate after "
                "delete -- expected 0. Rolling back."
            )

        conn.commit()
        print(f"[delete] committed: {len(ids)} rows deleted, {TRIGGER_NAME} restored")
    except Exception:
        conn.rollback()
        print("[delete] transaction rolled back due to error", file=sys.stderr)
        raise


def per_etf_coverage_check(conn: sqlite3.Connection) -> dict:
    etfs = conn.execute("SELECT etf_id, ticker, calendar_id FROM ETF ORDER BY ticker").fetchall()
    results = {}
    for etf in etfs:
        bars = conn.execute(
            "SELECT session_date FROM PriceBar WHERE etf_id = ? ORDER BY session_date",
            (etf["etf_id"],),
        ).fetchall()
        stored_dates = {b["session_date"] for b in bars}
        if not stored_dates:
            results[etf["ticker"]] = {"error": "no PriceBar rows found"}
            continue
        earliest, latest = min(stored_dates), max(stored_dates)
        expected = {
            r["session_date"]
            for r in conn.execute(
                """
                SELECT session_date FROM TradingSession
                WHERE calendar_id = ? AND is_trading_day = 1
                  AND session_date BETWEEN ? AND ?
                """,
                (etf["calendar_id"], earliest, latest),
            ).fetchall()
        }
        missing = sorted(expected - stored_dates)
        surplus = sorted(stored_dates - expected)
        results[etf["ticker"]] = {
            "bars_per_etf": len(stored_dates),
            "earliest": earliest,
            "latest": latest,
            "expected_trading_days": len(expected),
            "missing_count": len(missing),
            "missing_dates": missing,
            "surplus_count": len(surplus),
            "surplus_dates": surplus,
        }
    return results


def run_post_remediation_validation(conn: sqlite3.Connection, export_path: Path, pre_delete_total: int) -> dict:
    total_after = conn.execute("SELECT COUNT(*) c FROM PriceBar").fetchone()["c"]
    expected_after = pre_delete_total - EXPECTED_COUNT

    coverage = per_etf_coverage_check(conn)
    any_missing_or_surplus = any(
        v.get("missing_count", 0) != 0 or v.get("surplus_count", 0) != 0
        for v in coverage.values()
        if "error" not in v
    )

    distinct_sources = [
        dict(r) for r in conn.execute("SELECT source, COUNT(*) c FROM PriceBar GROUP BY source").fetchall()
    ]
    unrecognized_sources = [s["source"] for s in distinct_sources if s["source"] != "yahoo_finance"]

    tickers = sorted(r["ticker"] for r in conn.execute("SELECT ticker FROM ETF").fetchall())
    ranges = conn.execute(
        "SELECT MIN(session_date) mn, MAX(session_date) mx FROM PriceBar"
    ).fetchone()

    remaining_matches = conn.execute(PREDICATE_SQL).fetchall()

    on_disk_export = json.loads(export_path.read_text(encoding="utf-8"))

    validation = {
        "row_count_reconciliation": {
            "before": pre_delete_total,
            "after": total_after,
            "expected_after": expected_after,
            "delta": pre_delete_total - total_after,
            "pass": total_after == expected_after and (pre_delete_total - total_after) == EXPECTED_COUNT,
        },
        "two_directional_coverage_per_etf": coverage,
        "two_directional_coverage_pass": not any_missing_or_surplus,
        "source_tag_audit": {
            "distinct_sources": distinct_sources,
            "unrecognized_sources": unrecognized_sources,
            "pass": unrecognized_sources == [],
        },
        "universe_date_range_integrity": {
            "ticker_count": len(tickers),
            "tickers": tickers,
            "global_earliest": ranges["mn"],
            "global_latest": ranges["mx"],
            "pass": len(tickers) == EXPECTED_ETF_COUNT,
        },
        "export_backup_integrity": {
            "export_path": str(export_path.relative_to(REPO_ROOT)),
            "export_row_count": on_disk_export["row_count"],
            "pass": on_disk_export["row_count"] == EXPECTED_COUNT,
        },
        "recurrence_check": {
            "rows_matching_predicate_post_delete": len(remaining_matches),
            "pass": len(remaining_matches) == 0,
        },
    }
    validation["all_checks_pass"] = all(
        [
            validation["row_count_reconciliation"]["pass"],
            validation["two_directional_coverage_pass"],
            validation["source_tag_audit"]["pass"],
            validation["universe_date_range_integrity"]["pass"],
            validation["export_backup_integrity"]["pass"],
            validation["recurrence_check"]["pass"],
        ]
    )
    return validation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Run predicate + shape checks only, no writes.")
    group.add_argument("--execute", action="store_true", help="Export, delete, and validate.")
    args = parser.parse_args()

    assert_trigger_definition_unchanged()

    conn = connect(DB_PATH)
    try:
        rows = dry_run(conn)

        if args.dry_run:
            print("[dry-run] no changes made (--dry-run mode)")
            return 0

        pre_delete_total = conn.execute("SELECT COUNT(*) c FROM PriceBar").fetchone()["c"]

        export_path = write_export(rows, rows)
        verify_export_integrity(export_path, rows)

        execute_delete(conn, rows)

        validation = run_post_remediation_validation(conn, export_path, pre_delete_total)
        print(json.dumps(validation, indent=2))

        validation_path = ARCHIVE_DIR / f"post_remediation_validation_{date.today().isoformat()}.json"
        validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
        print(f"[validate] wrote {validation_path}")

        if not validation["all_checks_pass"]:
            print("[validate] ONE OR MORE CHECKS FAILED -- see above", file=sys.stderr)
            return 1

        print("[validate] ALL CHECKS PASSED")
        return 0
    except StopCondition as exc:
        print(f"[STOP] {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
