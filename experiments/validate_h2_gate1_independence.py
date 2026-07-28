#!/usr/bin/env python3
"""`reference_h2` Phase 3, Gate 1 -- Signal Independence Evidence-Generation Capability.

**What this script is, and is not.** This is the first Phase 3
evidence-generation capability for `reference_h2`'s Gate 1, per
`research_archive/reference_h2/prevalidation_plan.md` Section 3 ("Gate
1 -- Signal independence") and the empirical check named in
`docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md` Section 1 item
2 ("the cross-sectional correlation between `reference_v1`'s `SMA(20)`
rank and a trailing-12-1-month-return rank, computed across the same
25-ETF universe and a shared date range"). It is **not** a logged
construction attempt under the prevalidation plan's Section 2: no
pre-log attestation has been written, no attempt has been entered
against the plan's cap of three, and running this script does not, by
itself, satisfy Gate 1. A run of this script produces descriptive
evidence that a future, properly logged and attested construction
attempt may cite -- it does not substitute for logging one. This
script also does not perform, and is not part of, Methodology Freeze
(Phase 4): the formation window, skip length, and return basis below
are the specific trailing-12-1-month construction already named in the
Gate 0 review as the evidence item Gate 1 requires, not a Methodology
Freeze decision, and remain listed as "Deferred -- Methodology Freeze"
in the prevalidation plan's Section 3 Gate 4 checklist.

**Standalone principle, restated from
`docs/REFERENCE_H3_PREVALIDATION_PLAN.md` Section 2 and carried forward
by `research_archive/reference_h2/prevalidation_plan.md` Section 3 Gate
1 and Section 5:** no forward return, Information Coefficient, p-value,
or other outcome variable is read, computed, or referenced anywhere in
this script. This is a same-date, score-to-score comparison only.

Reuses existing code unchanged:
- `core.analytics.ranked_report.generate_ranked_etf_report()` -- to
  read `reference_v1`'s already-computed MOMENTUM (`SMA(20)`) dimension
  score per ETF per date, exactly as
  `experiments/validate_reference_v1_significance.py` and
  `experiments/validate_h3_gate1_independence.py` already do.
- `experiments.validate_h3_gate1_independence.compute_momentum_scores()`
  and `.score_overlap()` -- both are generic, score-to-score functions
  with no H3-specific assumption (they operate on arbitrary per-date
  score dictionaries), reused here rather than re-implemented.
- `experiments.validate_reference_v1_significance._pearson()`,
  `._spearman()`, `._rank_average_ties()`, `._percentile()` -- the
  platform's existing Spearman/tie-handling implementation.

H2's candidate score is computed fresh from `PriceBar` close-to-close
log returns, per the trailing-12-1-month construction named in the
Gate 0 review (Section 1): a ~252-trading-day (~12 calendar month)
formation window, ending ~21 trading days (~1 calendar month) before
the ranking date. **Disclosed, not silently assumed:** the exact
trading-day counts (252, 21) are this platform's own already-used
252-trading-day-year / 21-trading-day-month convention (the same
implicit convention `SMA(20)`'s own name already uses for "20 trading
days ~ 1 month"), not a value chosen for this check, and not a claim
that 252/21 is what a future Methodology Freeze will adopt -- Section 3
Gate 4's checklist item "Formation window" and "Skip period" remain
"Deferred -- Methodology Freeze" regardless of what this script uses to
produce descriptive Gate 1 evidence now. Return basis is close-to-close
log return, the same convention
`experiments/validate_h3_gate1_independence.py` and
`docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md` Part 3 already
use -- also a disclosed convention reuse, not a frozen decision.

Evaluation basis (matching `research_archive/reference_v1/reference_v1_significance_report_2026-07-18.json`
`config.period_start` / `config.period_end`, per the user's own
instruction and `docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md`
Section 1 item 2's "a shared date range"): 2024-07-17 to 2026-07-17.

Missing-data handling: an ETF is included in a date's cross-section
only if both required close prices (the formation-start date and the
skip-end date) are directly resolvable from `PriceBar` -- no
forward-fill, no interpolation, no synthetic value. A ranking date is
included in the reported distributions only if at least
`MINIMUM_PANEL_SIZE` ETFs have both a resolvable H2 candidate score and
a resolvable MOMENTUM score that date (the same
`bucket_size * 2 = 10`-ETF minimum-panel convention already used by
`experiments/validate_reference_v1_significance.py` and named in the
Gate 0 review's Section 3 checklist, "prior cycles used >=10 valid
ETFs").

Output: a factual plain-text report and a machine-readable JSON file,
written to the repository root (git-ignored generated research output,
the same convention `experiments/validate_reference_v1_significance.py`
already uses) rather than into `research_archive/reference_h2/` --
deliberately, since nothing in `research_archive/` should look like
logged Gate 1 evidence before a construction attempt has actually been
logged and attested per the prevalidation plan's Section 2. No
PASS/FAIL/INCONCLUSIVE determination, no interpretation against the
prevalidation plan's degenerate-case boundary, and no gate-satisfaction
claim is made anywhere in this script's output.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.analytics.persistence.repository import get_scoring_profile  # noqa: E402
from core.store.connection import connect  # noqa: E402
from core.store.migrations import run_migrations  # noqa: E402
from core.market_data.persistence.repository import (  # noqa: E402
    get_etf_by_ticker,
    get_price_bars,
    get_trading_days,
)

from experiments.daily_etf_universe_update import CALENDAR_ID, ETF_UNIVERSE, PROFILE_NAME, PROFILE_VERSION  # noqa: E402
from experiments.validate_h3_gate1_independence import compute_momentum_scores, score_overlap  # noqa: E402
from experiments.validate_reference_v1_significance import _percentile, _spearman  # noqa: E402

DB_PATH = Path(__file__).resolve().parent.parent / "experiments_etf_universe.db"
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent.parent / "h2_gate1_independence_analysis_report.json"

# Frozen evaluation window: REFERENCE v1's own analysis, unchanged.
# Source: research_archive/reference_v1/reference_v1_significance_report_2026-07-18.json
# config.period_start / config.period_end.
PERIOD_START = date(2024, 7, 17)
PERIOD_END = date(2026, 7, 17)

# H2 candidate construction (trailing-12-1-month return) -- see module
# docstring for why these two counts are a disclosed convention reuse,
# not a Methodology Freeze decision.
FORMATION_TRADING_DAYS = 252  # ~12 calendar months
SKIP_TRADING_DAYS = 21  # ~1 calendar month

# Score-overlap bucket size -- reused platform convention (same value
# used throughout validate_reference_v1_significance.py and
# validate_h3_gate1_independence.py).
BUCKET_SIZE = 5

# Minimum cross-sectional panel size for a ranking date to be included
# in the reported distributions -- same bucket_size * 2 = 10 convention
# used by validate_reference_v1_significance.py's build_panel().
MINIMUM_PANEL_SIZE = BUCKET_SIZE * 2


def _load_closes(conn, etf_id: str) -> dict[date, float]:
    """All resolvable close prices for one ETF, full history -- more
    than enough lookback for a 252+21-trading-day window starting at
    PERIOD_START, given the platform's 2016-09-13 coverage start."""
    bars = get_price_bars(conn, etf_id)
    return {bar.session_date: float(bar.close.amount) for bar in bars}


def compute_h2_scores(
    trading_days: list[date],
    closes_by_ticker: dict[str, dict[date, float]],
) -> dict[date, dict[str, float]]:
    """H2 candidate score per ticker per trading day with enough
    history: the close-to-close log return from
    (t - SKIP_TRADING_DAYS - FORMATION_TRADING_DAYS) to
    (t - SKIP_TRADING_DAYS), i.e. a ~252-trading-day formation window
    ending ~21 trading days before the ranking date. An ETF is included
    on a date only if both endpoint close prices are directly
    resolvable -- no forward-fill, no interpolation, no partial-window
    calculation."""
    needed = FORMATION_TRADING_DAYS + SKIP_TRADING_DAYS
    h2_by_date: dict[date, dict[str, float]] = {}
    for idx, t in enumerate(trading_days):
        if idx < needed:
            continue
        t_skip = trading_days[idx - SKIP_TRADING_DAYS]
        t_formation_start = trading_days[idx - needed]
        day_scores: dict[str, float] = {}
        for ticker, closes in closes_by_ticker.items():
            c_skip = closes.get(t_skip)
            c_start = closes.get(t_formation_start)
            if c_skip is None or c_start is None or c_skip <= 0 or c_start <= 0:
                continue  # missing endpoint -- excluded, no forward-fill/interpolation
            day_scores[ticker] = math.log(c_skip / c_start)
        if day_scores:
            h2_by_date[t] = day_scores
    return h2_by_date


def _repository_commit(repo_root: Path) -> str | None:
    """Current HEAD commit hash, or None if it cannot be determined
    (e.g. git unavailable) -- never fabricated."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def run(db_path: Path = DB_PATH, output_path: Path = DEFAULT_OUTPUT_PATH) -> int:
    conn = connect(db_path)
    try:
        run_migrations(conn, MIGRATIONS_DIR)

        profile = get_scoring_profile(conn, PROFILE_NAME, PROFILE_VERSION)
        if profile is None:
            print(f"No scoring profile found for name {PROFILE_NAME!r} version {PROFILE_VERSION}", file=sys.stderr)
            return 1

        all_trading_days = sorted(get_trading_days(conn, CALENDAR_ID))
        window_days = [d for d in all_trading_days if PERIOD_START <= d <= PERIOD_END]
        if not window_days:
            print("No trading days found in the evaluation window.", file=sys.stderr)
            return 1

        allowed_tickers = frozenset(ticker for ticker, _name in ETF_UNIVERSE)
        closes_by_ticker: dict[str, dict[date, float]] = {}
        for ticker, _name in ETF_UNIVERSE:
            etf = get_etf_by_ticker(conn, ticker)
            if etf is None:
                print(f"ETF {ticker!r} not found in database.", file=sys.stderr)
                return 1
            closes_by_ticker[ticker] = _load_closes(conn, etf.etf_id)

        # Need trailing (252 + 21)-day history relative to the FULL
        # trading-day index, not just window_days, so H2's lookback can
        # reach back before PERIOD_START correctly.
        h2_scores_by_date = compute_h2_scores(all_trading_days, closes_by_ticker)
        momentum_scores_by_date = compute_momentum_scores(conn, profile.scoring_profile_id, window_days, allowed_tickers)

        daily_results = []
        dates_missing_h2_history = 0
        dates_missing_momentum_score = 0
        dates_below_minimum_panel = 0
        for t in window_days:
            h2_day = h2_scores_by_date.get(t)
            mom_day = momentum_scores_by_date.get(t)
            if not h2_day:
                dates_missing_h2_history += 1
                continue
            if not mom_day:
                dates_missing_momentum_score += 1
                continue
            common = sorted(set(h2_day) & set(mom_day))
            if len(common) < MINIMUM_PANEL_SIZE:
                dates_below_minimum_panel += 1
                continue
            h2_values = [h2_day[tk] for tk in common]
            mom_values = [mom_day[tk] for tk in common]
            corr = _spearman(h2_values, mom_values)
            overlap = score_overlap(h2_day, mom_day, BUCKET_SIZE)
            daily_results.append(
                {
                    "date": t.isoformat(),
                    "n_etfs": len(common),
                    "spearman_correlation": corr,
                    "top_overlap_fraction": overlap["top_overlap_fraction"] if overlap else None,
                    "bottom_overlap_fraction": overlap["bottom_overlap_fraction"] if overlap else None,
                }
            )

        correlations = [r["spearman_correlation"] for r in daily_results if r["spearman_correlation"] is not None]
        top_overlaps = [r["top_overlap_fraction"] for r in daily_results if r["top_overlap_fraction"] is not None]
        bottom_overlaps = [r["bottom_overlap_fraction"] for r in daily_results if r["bottom_overlap_fraction"] is not None]

        repo_root = Path(__file__).resolve().parent.parent
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repository_commit": _repository_commit(repo_root),
            "disclosure": {
                "logged_construction_attempt": False,
                "pre_log_attestation_written": False,
                "gate_1_satisfied": False,
                "note": (
                    "This is Phase 3 evidence-generation-capability output for "
                    "reference_h2 Gate 1 (research_archive/reference_h2/prevalidation_plan.md "
                    "Section 3), not a logged construction attempt under that plan's Section 2. "
                    "No pre-log attestation has been written and this run is not counted against "
                    "the plan's attempt cap. This artifact does not, by itself, satisfy Gate 1: "
                    "Section 2's attempt log and pre-log attestation, and Section 6's Level 2 "
                    "independent confirmation (including independent reproduction of both "
                    "components below), remain outstanding. No PASS/FAIL/INCONCLUSIVE "
                    "determination, gate verdict, or recommendation is made anywhere in this "
                    "report."
                ),
            },
            "universe": {
                "tickers": [ticker for ticker, _name in ETF_UNIVERSE],
                "etf_universe_size": len(ETF_UNIVERSE),
            },
            "config": {
                "scoring_profile": f"{PROFILE_NAME} v{PROFILE_VERSION}",
                "period_start": PERIOD_START.isoformat(),
                "period_end": PERIOD_END.isoformat(),
                "h2_formation_trading_days": FORMATION_TRADING_DAYS,
                "h2_skip_trading_days": SKIP_TRADING_DAYS,
                "h2_return_basis": "close-to-close log return",
                "momentum_source": "reference_v1 frozen SMA(20), read via generate_ranked_etf_report()",
                "bucket_size": BUCKET_SIZE,
                "minimum_panel_size": MINIMUM_PANEL_SIZE,
                "ranking_dates_in_window": len(window_days),
                "ranking_dates_evaluated": len(daily_results),
            },
            "missing_data_handling": {
                "policy": (
                    "No forward-fill, no interpolation, no synthetic value. An ETF is excluded "
                    "from a date's cross-section if either required close price is not directly "
                    "resolvable. A ranking date is excluded from the reported distributions if "
                    "fewer than minimum_panel_size ETFs have both scores resolvable that date."
                ),
                "dates_excluded_missing_h2_history": dates_missing_h2_history,
                "dates_excluded_missing_momentum_score": dates_missing_momentum_score,
                "dates_excluded_below_minimum_panel": dates_below_minimum_panel,
            },
            "component_1_correlation_distribution": {
                "n": len(correlations),
                "mean": (sum(correlations) / len(correlations)) if correlations else None,
                "median": _percentile(sorted(correlations), 50) if correlations else None,
                "p25": _percentile(sorted(correlations), 25) if correlations else None,
                "p75": _percentile(sorted(correlations), 75) if correlations else None,
                "min": min(correlations) if correlations else None,
                "max": max(correlations) if correlations else None,
            },
            "component_2_top_overlap_distribution": {
                "n": len(top_overlaps),
                "mean": (sum(top_overlaps) / len(top_overlaps)) if top_overlaps else None,
                "median": _percentile(sorted(top_overlaps), 50) if top_overlaps else None,
                "min": min(top_overlaps) if top_overlaps else None,
                "max": max(top_overlaps) if top_overlaps else None,
            },
            "component_2_bottom_overlap_distribution": {
                "n": len(bottom_overlaps),
                "mean": (sum(bottom_overlaps) / len(bottom_overlaps)) if bottom_overlaps else None,
                "median": _percentile(sorted(bottom_overlaps), 50) if bottom_overlaps else None,
                "min": min(bottom_overlaps) if bottom_overlaps else None,
                "max": max(bottom_overlaps) if bottom_overlaps else None,
            },
            "daily_results": daily_results,
        }

        print(_format_report(report))
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print()
        print(f"Machine-readable report written to {output_path}")
        return 0
    finally:
        conn.close()


def _format_report(report: dict) -> str:
    lines = ["reference_h2 Phase 3 -- Gate 1 Signal Independence Evidence (Component 1 + Component 2)"]
    lines.append("")
    lines.append(report["disclosure"]["note"])
    lines.append("")
    cfg = report["config"]
    lines.append(f"Scoring profile (MOMENTUM/SMA(20) source): {cfg['scoring_profile']}")
    lines.append(f"Evaluation window: {cfg['period_start']} to {cfg['period_end']} (reference_v1's own analysis window)")
    lines.append(
        f"H2 candidate construction: {cfg['h2_formation_trading_days']}-trading-day trailing "
        f"{cfg['h2_return_basis']}, ending {cfg['h2_skip_trading_days']} trading days before "
        "the ranking date"
    )
    lines.append(f"Bucket size (overlap check): {cfg['bucket_size']}")
    lines.append(f"Minimum cross-sectional panel size: {cfg['minimum_panel_size']}")
    lines.append(f"ETF universe size: {report['universe']['etf_universe_size']}")
    lines.append(f"Ranking dates evaluated: {cfg['ranking_dates_evaluated']} of {cfg['ranking_dates_in_window']} in window")
    lines.append("")
    md = report["missing_data_handling"]
    lines.append("-- Missing-data handling --")
    lines.append(f"  Policy: {md['policy']}")
    lines.append(f"  Dates excluded (insufficient H2 trailing history): {md['dates_excluded_missing_h2_history']}")
    lines.append(f"  Dates excluded (no MOMENTUM/SMA(20) score that date): {md['dates_excluded_missing_momentum_score']}")
    lines.append(f"  Dates excluded (below minimum panel size): {md['dates_excluded_below_minimum_panel']}")
    lines.append("")
    cd = report["component_1_correlation_distribution"]
    lines.append("-- Component 1: Daily Spearman correlation (SMA(20)-rank vs. H2 trailing-return-rank) --")
    lines.append(f"  n={cd['n']}  mean={cd['mean']}  median={cd['median']}  p25={cd['p25']}  p75={cd['p75']}  min={cd['min']}  max={cd['max']}")
    lines.append("")
    to = report["component_2_top_overlap_distribution"]
    bo = report["component_2_bottom_overlap_distribution"]
    lines.append(f"-- Component 2: Top-{report['config']['bucket_size']} overlap fraction -- n={to['n']} mean={to['mean']} median={to['median']} min={to['min']} max={to['max']}")
    lines.append(f"-- Component 2: Bottom-{report['config']['bucket_size']} overlap fraction -- n={bo['n']} mean={bo['mean']} median={bo['median']} min={bo['min']} max={bo['max']}")
    lines.append("")
    lines.append(
        "This is a descriptive same-date score-to-score comparison only. No forward return, "
        "IC, p-value, or promotion decision is computed or implied. No PASS/FAIL/INCONCLUSIVE "
        "determination is made by this script -- interpretation against "
        "research_archive/reference_h2/prevalidation_plan.md Section 3's degenerate-case "
        "boundary, a logged construction attempt with pre-log attestation, and Level 2 "
        "independent confirmation (Section 6) are all required before Gate 1 counts as "
        "satisfied."
    )
    return "\n".join(lines)


if __name__ == "__main__":
    # Guarded inline self-checks, same discipline as
    # validate_h3_gate1_independence.py: a silent bug here would produce
    # a wrong Gate 1 evidence figure, not just a wrong printed number.
    assert abs(_spearman([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) - 1.0) < 1e-9
    assert abs(_spearman([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]) - (-1.0)) < 1e-9

    # compute_h2_scores(): missing-data exclusion -- an ETF absent at
    # either endpoint must be excluded from that date, not estimated.
    from datetime import timedelta as _timedelta

    _synthetic_days = [date(2020, 1, 1) + _timedelta(days=i) for i in range(300)]
    _synthetic_closes = {
        "AAA": {d: 100.0 + i * 0.1 for i, d in enumerate(_synthetic_days)},
        "BBB": {d: 100.0 + i * 0.2 for i, d in enumerate(_synthetic_days)},
        # CCC is missing its formation-start-date close entirely.
        "CCC": {d: 100.0 for i, d in enumerate(_synthetic_days) if i > 100},
    }
    _h2_check = compute_h2_scores(_synthetic_days, _synthetic_closes)
    _last_day = _synthetic_days[-1]
    assert _last_day in _h2_check
    assert "AAA" in _h2_check[_last_day] and "BBB" in _h2_check[_last_day]
    assert "CCC" not in _h2_check[_last_day]  # missing formation-start close -- excluded
    # BBB rose faster than AAA -> higher trailing return -> higher H2 score.
    assert _h2_check[_last_day]["BBB"] > _h2_check[_last_day]["AAA"]

    # No score at all before enough trailing history exists.
    assert _synthetic_days[0] not in _h2_check
    assert _synthetic_days[FORMATION_TRADING_DAYS + SKIP_TRADING_DAYS - 1] not in _h2_check

    raise SystemExit(run())
