"""REFERENCE v2 H1 (low volatility) statistical significance test.

A **research analysis script**, following the same discipline as
`validate_reference_v1_significance.py`: it does not redesign the
scoring engine, add a factor to `core/`, change ranking logic, or use
ML. It is read-only analysis over price data already in the database,
using only Python's standard library. It implements exactly the frozen
specification and approved implementation plan, and nothing beyond
them:

- docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md
- docs/REFERENCE_V2_H1_GO_CHECKPOINT_REPORT.md

Architecture note (implementation plan, Part 1): unlike REFERENCE v1,
this script never touches `IndicatorDefinition`, `ScoringProfile`,
`Score`, or `DimensionScore`. H1's score (realized volatility) and both
of its outcome variables are computed directly from `PriceBar.close`
history, entirely in-memory, exactly once per script run. No new
indicator or scoring profile is registered; no production-facing table
is written to. This keeps H1 a pure experiments-only research artifact
until (and unless) the frozen promotion criteria (spec Part 6) are met.

Two pre-registered hypotheses (spec Part 1), tested independently:

- H1-A (primary): LowVol score vs. future RAW return.
- H1-B (secondary diagnostic): LowVol score vs. future RISK-ADJUSTED
  return (raw return / forward realized volatility). Cannot drive
  promotion on its own (spec Part 6) -- see _promotion_decision().

Score (spec Part 3, frozen -- not configurable, not swept): 60 trading
day trailing lookback, close-to-close log returns, sample standard
deviation (N-1), not annualized, score = -1 x realized_volatility.

Forward volatility for H1-B (spec Part 1, resolved): calculated by the
exact same realized_volatility() function as the trailing score, so
the two calculations cannot silently diverge -- but over a *different*
window. The trailing score uses 61 prices (the ranking date plus the
60 days before it) to form 60 returns. The forward window uses the 20
trading days strictly *after* the ranking date (excluding the ranking
date itself) -- 20 prices, 19 returns. This asymmetry is deliberate,
not an oversight: the trailing window's own anchor point (the ranking
date) is the last point of the lookback; the forward window's anchor
point (the ranking date) is the first point *excluded* from it, since
it belongs to the trailing side.

Reuses REFERENCE v1's statistical machinery unmodified, by import (see
implementation plan, Part 3): _percentile, mean_ic, permutation_null,
empirical_p_value, bootstrap_ci, holm_bonferroni, _statistic_verdict.
None of these functions are redefined here. mean_ic()/daily_ic_series()
read a hardcoded "forward_return" panel key; build_statistic_view()
below is the thin adapter that lets H1-A and H1-B reuse them unmodified
by presenting each statistic's own outcome under that one fixed key,
rather than modifying the imported function's signature.

Minimum panel size (spec Part 6): a ranking date is usable for a given
statistic only if at least 10 ETFs have both a valid score and a valid
outcome for that statistic on that date -- inherited unmodified from
REFERENCE v1's own bucket_size * 2 convention. Dates below this
threshold are excluded entirely, never down-weighted.

Reproducibility (spec Part 6): one seeded random.Random instance per
run() call. RANDOM_SEED below is H1's own fixed, pre-chosen seed --
distinct from, not a reuse of, REFERENCE v1's own seed value.

Undefined-statistic handling (spec Part 6): reused unmodified from
REFERENCE v1's _statistic_verdict() -- an undefined bootstrap CI at any
block length is treated as "does not exclude zero," i.e. a failure of
robustness. No manual interpretation.

Deviation from REFERENCE v1's script, deliberate: this script's
`if __name__ == "__main__":` guard runs synthetic self-checks only. It
does not automatically call run() against the real database afterward.
Running the real, full-scale significance study is a separate,
deliberate research action -- not an automatic consequence of
verifying this implementation. To run it: import run() and call it
explicitly (see Usage below).

Prerequisites: a valid trading Calendar/TradingSession set
(seed_trading_calendar.py) and sufficient PriceBar depth
(backfill_price_history.py) for the requested period plus 20 trading
days beyond it. Unlike REFERENCE v1's script, this one does NOT require
daily_etf_universe_update.py to have been run -- H1 never reads
Score/DimensionScore, so no scoring-pipeline prerequisite applies.

Usage:
    python experiments/validate_reference_v2_h1_significance.py   # self-checks only
    python -c "from experiments.validate_reference_v2_h1_significance import run; raise SystemExit(run())"

Output (when run() is called): a factual plain-text report and a
machine-readable reference_v2_h1_significance_report.json at the repo
root (git-ignored as generated research output, not source, same
convention as REFERENCE v1's own report).

Dependency requirements: none beyond what this project already uses.
No third-party package is required to run this script.
"""
import json
import math
import random
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.market_data.persistence.database import connect
from core.market_data.persistence.migrations import run_migrations
from core.market_data.persistence.repository import (
    get_etf_by_ticker,
    get_price_bars,
    get_trading_days,
)

from experiments.daily_etf_universe_update import CALENDAR_ID, ETF_UNIVERSE
from experiments.validate_reference_v1_significance import (
    _percentile,
    _statistic_verdict,
    bootstrap_ci,
    empirical_p_value,
    holm_bonferroni,
    mean_ic,
    permutation_null,
)
from experiments.validate_scoring_signal import forward_return

DB_PATH = Path(__file__).resolve().parent.parent / "experiments_etf_universe.db"
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent.parent / "reference_v2_h1_significance_report.json"

DEFAULT_DAYS_BACK = 730

# Frozen per spec Part 3/Part 1 -- not configurable, not swept, no
# alternative window is added anywhere in this script.
LOOKBACK_DAYS = 60      # trailing score window: 61 prices -> 60 returns
FORWARD_DAYS = 20       # forward H1-B window: 20 prices -> 19 returns

MIN_PANEL_SIZE = 10     # spec Part 6, inherited unmodified from REFERENCE v1's bucket_size * 2

PERMUTATIONS = 10_000        # spec Part 6: 10,000 minimum
BOOTSTRAP_ITERATIONS = 2_000  # spec Part 6: 2,000 minimum per block length
BLOCK_LENGTHS = (20, 40, 60)  # spec Part 6: 20 primary, 40/60 robustness-only

# H1's own fixed seed, chosen once for this study -- not a reuse of
# REFERENCE v1's RANDOM_SEED (20260718).
RANDOM_SEED = 2026071801

STATISTIC_LABELS = ("h1_a", "h1_b")


# ---------------------------------------------------------------------------
# Score: realized volatility (spec Part 3, shared by trailing score and
# H1-B's forward denominator -- one function, two windows, never two
# separately maintained implementations)
# ---------------------------------------------------------------------------


def realized_volatility(prices: list[float]) -> float:
    """Sample standard deviation (N-1) of close-to-close log returns,
    not annualized. Accepts any price window of 2 or more prices.

    With exactly 2 prices there is exactly 1 log return -- sample
    variance (N-1 denominator) is mathematically undefined for a single
    observation. Rather than raising, this is treated as a defined,
    degenerate case: zero variance information available from one
    observation, so realized_volatility returns 0.0. This is a defined
    convention for a genuine mathematical boundary, not a floor or clip
    on real multi-return volatility estimates (see spec Part 8 -- no
    floor/clip is applied to any real H1-A/H1-B calculation)."""
    if len(prices) < 2:
        raise ValueError("realized_volatility() requires at least 2 prices")
    log_returns = [math.log(prices[i] / prices[i - 1]) for i in range(1, len(prices))]
    n = len(log_returns)
    if n < 2:
        return 0.0
    mean_r = sum(log_returns) / n
    variance = sum((r - mean_r) ** 2 for r in log_returns) / (n - 1)
    return math.sqrt(variance)


# ---------------------------------------------------------------------------
# Panel construction
# ---------------------------------------------------------------------------


def build_panel(
    conn,
    universe: list[tuple[str, str]],
    trading_days: list[date],
    lookback_days: int = LOOKBACK_DAYS,
    forward_days: int = FORWARD_DAYS,
    min_panel_size: int = MIN_PANEL_SIZE,
) -> list[dict]:
    """One entry per ranking date with a usable LowVol score for at
    least `min_panel_size` ETFs. Each ETF's own price history is
    fetched once (not once per date) and indexed by session_date --
    this is the natural, correct data-access shape for a 61-price
    lookback per ETF per date, not a REFERENCE-v1-specific pattern
    being copied for its own sake.

    H1-A's outcome (raw_return) requires only the ranking date's own
    close and the close 20 trading days later -- the same two points
    forward_return() already needs. H1-B's outcome
    (risk_adjusted_return) additionally requires the full 20-day
    forward window to be resolvable for its own realized-volatility
    denominator. An ETF can therefore be present in one outcome and
    absent from the other, on the same date -- this is expected, not a
    bug, and is exactly why build_statistic_view() below computes each
    statistic's own eligible ETF set independently (spec Part 6)."""
    tickers = [ticker for ticker, _name in universe]
    closes_by_ticker: dict[str, dict[date, Decimal]] = {}
    for ticker in tickers:
        etf = get_etf_by_ticker(conn, ticker)
        if etf is None:
            continue
        bars = get_price_bars(conn, etf.etf_id)
        closes_by_ticker[ticker] = {bar.session_date: bar.close.amount for bar in bars}

    panel: list[dict] = []
    for i, session_date in enumerate(trading_days):
        if i < lookback_days or i + forward_days >= len(trading_days):
            continue
        trailing_dates = trading_days[i - lookback_days: i + 1]      # 61 dates
        forward_dates = trading_days[i + 1: i + 1 + forward_days]    # 20 dates
        forward_end_date = trading_days[i + forward_days]

        lowvol_score: dict[str, float] = {}
        raw_return: dict[str, float] = {}
        risk_adjusted_return: dict[str, float] = {}

        for ticker in tickers:
            table = closes_by_ticker.get(ticker)
            if table is None or not all(d in table for d in trailing_dates):
                continue  # missing data rule (spec Part 3): no fill, no interpolation, no partial window
            trailing_prices = [float(table[d]) for d in trailing_dates]
            lowvol_score[ticker] = -1.0 * realized_volatility(trailing_prices)

            start_price = table.get(session_date)
            end_price = table.get(forward_end_date)
            if start_price is not None and end_price is not None:
                raw_return[ticker] = float(forward_return(start_price, end_price))

            if all(d in table for d in forward_dates):
                forward_prices = [float(table[d]) for d in forward_dates]
                forward_vol = realized_volatility(forward_prices)
                if forward_vol > 0.0 and ticker in raw_return:
                    risk_adjusted_return[ticker] = raw_return[ticker] / forward_vol
                # forward_vol == 0.0 (no price movement across the whole
                # forward window) is a genuine mathematical boundary, not
                # a tiny-but-nonzero value -- the ratio does not exist.
                # Excluded here, not floored/clipped (spec Part 8).

        if len(lowvol_score) < min_panel_size:
            continue

        panel.append({
            "session_date": session_date,
            "etf_ids": list(lowvol_score.keys()),
            "lowvol_score": lowvol_score,
            "raw_return": raw_return,
            "risk_adjusted_return": risk_adjusted_return,
        })
    return panel


def build_statistic_view(
    panel: list[dict],
    outcome_key: str,
    score_key: str = "lowvol_score",
    min_panel_size: int = MIN_PANEL_SIZE,
) -> list[dict]:
    """Adapter that lets REFERENCE v1's mean_ic()/permutation_null()/
    bootstrap_ci() (all of which read a hardcoded "forward_return" key)
    be reused unmodified for either H1-A or H1-B: for each date, narrow
    etf_ids to the intersection of score-valid and outcome-valid ETFs,
    drop the date entirely if that intersection is below
    min_panel_size (spec Part 6), and present the chosen outcome under
    the "forward_return" key the imported functions expect. No
    modification to any imported REFERENCE v1 function."""
    view: list[dict] = []
    for day in panel:
        score = day[score_key]
        outcome = day[outcome_key]
        etf_ids = [etf_id for etf_id in day["etf_ids"] if etf_id in score and etf_id in outcome]
        if len(etf_ids) < min_panel_size:
            continue
        view.append({
            "session_date": day["session_date"],
            "etf_ids": etf_ids,
            score_key: score,
            "forward_return": outcome,
        })
    return view


# ---------------------------------------------------------------------------
# Promotion decision (spec Part 6, frozen 4-row table -- implemented
# exactly, no additional branch, no threshold changed here)
# ---------------------------------------------------------------------------


def _promotion_decision(verdicts: dict) -> dict:
    h1a_passes = verdicts["h1_a"]["passes"]
    h1b_passes = verdicts["h1_b"]["passes"]

    if h1a_passes and h1b_passes:
        decision = "PROMOTE_TO_REFERENCE_V2"
        reason = (
            "H1-A (primary) and H1-B (secondary diagnostic) both passed: classical "
            "anomaly confirmed and corroborated by risk-adjusted performance."
        )
    elif h1a_passes and not h1b_passes:
        decision = "PROMOTE_TO_REFERENCE_V2"
        reason = (
            "H1-A (primary) passed on its own; H1-B did not. H1-A is the pre-registered "
            "primary driver of promotion (spec Part 6). The H1-A/H1-B divergence must be "
            "explained at the audit stage, not silently dropped."
        )
    elif not h1a_passes and h1b_passes:
        decision = "ARCHIVE"
        reason = (
            "H1-B passed but H1-A (primary) did not. Per spec Part 6, H1-B passing alone "
            "is insufficient for promotion. Recorded as: risk-adjusted characteristic "
            "observed, classical anomaly not confirmed."
        )
    else:
        decision = "ARCHIVE"
        reason = "Neither H1-A nor H1-B survived Holm-Bonferroni-corrected permutation testing with bootstrap robustness."

    return {
        "h1_a_passed": h1a_passes,
        "h1_b_passed": h1b_passes,
        "verdict": decision,
        "verdict_reason": reason,
    }


# ---------------------------------------------------------------------------
# Report construction
# ---------------------------------------------------------------------------


def _build_report(
    *,
    observed,
    null_distributions,
    corrected,
    bootstrap_results,
    block_lengths,
    panel,
    h1a_view,
    h1b_view,
    start_date,
    end_date,
    lookback_days,
    forward_days,
    min_panel_size,
    universe_size,
    permutations,
    bootstrap_iterations,
    random_seed,
) -> dict:
    statistics_report = {}
    verdicts = {}
    for label in STATISTIC_LABELS:
        obs = observed[label]
        null = null_distributions[label]
        null_median = _percentile(sorted(null), 50) if null else None
        correction = corrected.get(label, {"raw_p_value": None, "adjusted_p_value": None})
        verdict = _statistic_verdict(label, corrected, bootstrap_results[label], block_lengths)
        verdicts[label] = verdict

        statistics_report[label] = {
            "observed": obs,
            "null_median": null_median,
            "difference_from_null": (obs - null_median) if (obs is not None and null_median is not None) else None,
            "raw_p_value": correction["raw_p_value"],
            "adjusted_p_value": correction["adjusted_p_value"],
            "significant_after_correction": verdict["significant_after_correction"],
            "bootstrap": {
                f"block_{block_length}": (
                    {"ci_low": ci[0], "ci_high": ci[1], "excludes_zero": not (ci[0] <= 0.0 <= ci[1])}
                    if (ci := bootstrap_results[label].get(block_length)) is not None
                    else None
                )
                for block_length in block_lengths
            },
            "bootstrap_robust_across_block_lengths": verdict["bootstrap_robust_across_block_lengths"],
            "passes": verdict["passes"],
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": {
            "hypothesis": "REFERENCE v2 H1 -- low volatility",
            "specification": "docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md",
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "lookback_trading_days": lookback_days,
            "forward_trading_days": forward_days,
            "min_panel_size": min_panel_size,
            "etf_universe_size": universe_size,
            "ranking_dates_in_base_panel": len(panel),
            "ranking_dates_h1_a": len(h1a_view),
            "ranking_dates_h1_b": len(h1b_view),
            "permutations": permutations,
            "bootstrap_iterations": bootstrap_iterations,
            "block_lengths": list(block_lengths),
            "random_seed": random_seed,
        },
        "statistics": statistics_report,
        "decision": _promotion_decision(verdicts),
    }


def _format_report(report: dict) -> str:
    lines = ["REFERENCE v2 H1 (low volatility) Significance Test"]
    cfg = report["config"]
    lines.append(f"Period: {cfg['period_start']} to {cfg['period_end']}")
    lines.append(f"Lookback: {cfg['lookback_trading_days']}d  Forward: {cfg['forward_trading_days']}d")
    lines.append(f"ETF universe size: {cfg['etf_universe_size']}")
    lines.append(
        f"Ranking dates -- base panel: {cfg['ranking_dates_in_base_panel']}  "
        f"H1-A: {cfg['ranking_dates_h1_a']}  H1-B: {cfg['ranking_dates_h1_b']}"
    )
    lines.append(f"Permutations: {cfg['permutations']}  Bootstrap iterations: {cfg['bootstrap_iterations']}")
    lines.append(f"Block lengths: {cfg['block_lengths']} (first is primary, rest are robustness diagnostics only)")
    lines.append(f"Random seed: {cfg['random_seed']}")
    lines.append("")

    for label in STATISTIC_LABELS:
        stat = report["statistics"][label]
        lines.append(f"-- {label} --")
        lines.append(f"  Observed: {stat['observed']}")
        lines.append(f"  Null median: {stat['null_median']}")
        lines.append(f"  Difference from null: {stat['difference_from_null']}")
        lines.append(f"  Raw p-value: {stat['raw_p_value']}   Adjusted (Holm-Bonferroni): {stat['adjusted_p_value']}")
        lines.append(f"  Significant after correction: {stat['significant_after_correction']}")
        for key, ci in stat["bootstrap"].items():
            lines.append(f"  Bootstrap {key}: {ci}")
        lines.append(f"  Bootstrap-robust across all block lengths: {stat['bootstrap_robust_across_block_lengths']}")
        lines.append(f"  Passes (significant AND bootstrap-robust): {stat['passes']}")
        lines.append("")

    dec = report["decision"]
    lines.append("Decision")
    lines.append(f"H1-A passed: {dec['h1_a_passed']}   H1-B passed: {dec['h1_b_passed']}")
    lines.append(f"Verdict: {dec['verdict']}")
    lines.append(f"Reason: {dec['verdict_reason']}")
    lines.append("")
    lines.append(
        "This is an observed measurement over a limited historical sample. Even a "
        "PROMOTE_TO_REFERENCE_V2 verdict establishes statistical association within this "
        "sample only -- it does not confirm, validate, or prove predictive value, does not "
        "account for transaction costs or implementation frictions, and cannot speak to a "
        "different market regime than the one observed. No recommendation, no ranking "
        "judgment, no investment advice."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run(
    db_path: Path = DB_PATH,
    universe: list[tuple[str, str]] | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    lookback_days: int = LOOKBACK_DAYS,
    forward_days: int = FORWARD_DAYS,
    min_panel_size: int = MIN_PANEL_SIZE,
    permutations: int = PERMUTATIONS,
    bootstrap_iterations: int = BOOTSTRAP_ITERATIONS,
    block_lengths: tuple[int, ...] = BLOCK_LENGTHS,
    random_seed: int = RANDOM_SEED,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> int:
    universe = universe if universe is not None else ETF_UNIVERSE
    end_date = end_date or date.today()
    start_date = start_date or (end_date - timedelta(days=DEFAULT_DAYS_BACK))

    rng = random.Random(random_seed)
    conn = connect(db_path)
    try:
        run_migrations(conn, MIGRATIONS_DIR)
        trading_days = sorted(d for d in get_trading_days(conn, CALENDAR_ID) if start_date <= d <= end_date)

        panel = build_panel(conn, universe, trading_days, lookback_days, forward_days, min_panel_size)
        h1a_view = build_statistic_view(panel, "raw_return", "lowvol_score", min_panel_size)
        h1b_view = build_statistic_view(panel, "risk_adjusted_return", "lowvol_score", min_panel_size)
        views = {"h1_a": h1a_view, "h1_b": h1b_view}

        observed = {label: mean_ic(views[label], "lowvol_score") for label in STATISTIC_LABELS}

        null_distributions = {
            label: permutation_null(views[label], "lowvol_score", mean_ic, permutations, rng)
            for label in STATISTIC_LABELS
        }
        raw_p_values = [
            (label, empirical_p_value(observed[label], null_distributions[label]))
            for label in STATISTIC_LABELS
            if observed[label] is not None
        ]
        corrected = holm_bonferroni(raw_p_values)

        bootstrap_results = {label: {} for label in STATISTIC_LABELS}
        for block_length in block_lengths:
            for label in STATISTIC_LABELS:
                bootstrap_results[label][block_length] = bootstrap_ci(
                    views[label], mean_ic, "lowvol_score", block_length, bootstrap_iterations, rng
                )

        report = _build_report(
            observed=observed,
            null_distributions=null_distributions,
            corrected=corrected,
            bootstrap_results=bootstrap_results,
            block_lengths=block_lengths,
            panel=panel,
            h1a_view=h1a_view,
            h1b_view=h1b_view,
            start_date=start_date,
            end_date=end_date,
            lookback_days=lookback_days,
            forward_days=forward_days,
            min_panel_size=min_panel_size,
            universe_size=len(universe),
            permutations=permutations,
            bootstrap_iterations=bootstrap_iterations,
            random_seed=random_seed,
        )
        print(_format_report(report))
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nMachine-readable report written to {output_path}")
        return 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Synthetic self-checks. No database access. Run automatically when this
# script is executed directly; run() (the real, database-backed analysis)
# is not invoked here -- see module docstring.
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    # -- realized_volatility(): boundary and correctness checks --------
    try:
        realized_volatility([100.0])
        raise AssertionError("expected ValueError for a single price")
    except ValueError:
        pass

    assert realized_volatility([100.0, 105.0]) == 0.0  # 2 prices -> 1 return -> defined as 0.0

    _constant = [100.0] * 61
    assert realized_volatility(_constant) == 0.0

    _prices = [100.0, 105.0, 98.0, 102.0, 101.5, 99.0]
    _expected_returns = [math.log(_prices[i] / _prices[i - 1]) for i in range(1, len(_prices))]
    _expected_mean = sum(_expected_returns) / len(_expected_returns)
    _expected_vol = math.sqrt(
        sum((r - _expected_mean) ** 2 for r in _expected_returns) / (len(_expected_returns) - 1)
    )
    assert abs(realized_volatility(_prices) - _expected_vol) < 1e-12

    # -- ranking direction: lower volatility -> higher score -----------
    _low_vol_prices = [100.0, 100.5, 100.2, 100.7, 100.4, 100.9]
    _high_vol_prices = [100.0, 115.0, 90.0, 120.0, 85.0, 125.0]
    _low_vol_score = -1.0 * realized_volatility(_low_vol_prices)
    _high_vol_score = -1.0 * realized_volatility(_high_vol_prices)
    assert _low_vol_score > _high_vol_score

    # -- build_statistic_view(): missing data + minimum panel size -----
    _tickers12 = [f"E{i}" for i in range(12)]
    _synthetic_score = {t: -0.01 * (i + 1) for i, t in enumerate(_tickers12)}
    # H1-A outcome present for all 12; H1-B outcome present for only 9
    # (below the min_panel_size=10 threshold) to prove H1-A and H1-B are
    # filtered independently, not by a single shared eligibility set.
    _synthetic_raw = {t: 0.001 * (i + 1) for i, t in enumerate(_tickers12)}
    _synthetic_risk_adj = {t: 0.02 * (i + 1) for i, t in enumerate(_tickers12[:9])}
    _synthetic_panel = [{
        "session_date": date(2025, 1, 2),
        "etf_ids": _tickers12,
        "lowvol_score": _synthetic_score,
        "raw_return": _synthetic_raw,
        "risk_adjusted_return": _synthetic_risk_adj,
    }]
    _h1a_check_view = build_statistic_view(_synthetic_panel, "raw_return", "lowvol_score", MIN_PANEL_SIZE)
    _h1b_check_view = build_statistic_view(_synthetic_panel, "risk_adjusted_return", "lowvol_score", MIN_PANEL_SIZE)
    assert len(_h1a_check_view) == 1 and len(_h1a_check_view[0]["etf_ids"]) == 12
    assert len(_h1b_check_view) == 0  # 9 < MIN_PANEL_SIZE -- date excluded entirely for H1-B only

    # A date with a genuine per-ETF gap in the outcome dict (not just an
    # undersized universe): 11 of 12 ETFs have a raw_return; 1 is missing.
    _partial_raw = dict(_synthetic_raw)
    del _partial_raw[_tickers12[0]]
    _synthetic_panel_partial = [{
        "session_date": date(2025, 1, 3),
        "etf_ids": _tickers12,
        "lowvol_score": _synthetic_score,
        "raw_return": _partial_raw,
        "risk_adjusted_return": {},
    }]
    _partial_view = build_statistic_view(_synthetic_panel_partial, "raw_return", "lowvol_score", MIN_PANEL_SIZE)
    assert len(_partial_view) == 1
    assert _tickers12[0] not in _partial_view[0]["etf_ids"]
    assert len(_partial_view[0]["etf_ids"]) == 11

    # -- H1-A/H1-B outcome separation -----------------------------------
    # Changing H1-B's outcome values must not change H1-A's statistic on
    # the same base panel.
    _ic_before = mean_ic(_h1a_check_view, "lowvol_score")
    _mutated_risk_adj = {t: -999.0 for t in _tickers12[:9]}
    _synthetic_panel[0]["risk_adjusted_return"] = _mutated_risk_adj
    _h1a_check_view_after = build_statistic_view(_synthetic_panel, "raw_return", "lowvol_score", MIN_PANEL_SIZE)
    _ic_after = mean_ic(_h1a_check_view_after, "lowvol_score")
    assert _ic_before == _ic_after

    # -- deterministic reproducibility -----------------------------------
    # Small synthetic panel, run the real statistical machinery (mean_ic,
    # permutation_null, holm_bonferroni, bootstrap_ci, _statistic_verdict,
    # _promotion_decision) twice with an identical seed and confirm the
    # decision and every statistic's numbers match exactly.
    def _make_repro_panel(local_rng: random.Random) -> list[dict]:
        panel = []
        etf_ids = [f"R{i}" for i in range(15)]
        for day_index in range(30):
            score = {e: local_rng.uniform(-0.05, -0.01) for e in etf_ids}
            raw = {e: local_rng.uniform(-0.02, 0.02) for e in etf_ids}
            risk_adj = {e: local_rng.uniform(-1.0, 1.0) for e in etf_ids}
            panel.append({
                "session_date": date(2025, 1, 1),
                "etf_ids": etf_ids,
                "lowvol_score": score,
                "raw_return": raw,
                "risk_adjusted_return": risk_adj,
            })
        return panel

    def _run_repro_pipeline(seed: int) -> dict:
        data_rng = random.Random(999)  # fixed data generator, independent of the pipeline's own rng
        panel = _make_repro_panel(data_rng)
        stat_rng = random.Random(seed)
        h1a_v = build_statistic_view(panel, "raw_return", "lowvol_score", min_panel_size=5)
        h1b_v = build_statistic_view(panel, "risk_adjusted_return", "lowvol_score", min_panel_size=5)
        views = {"h1_a": h1a_v, "h1_b": h1b_v}
        observed = {label: mean_ic(views[label], "lowvol_score") for label in STATISTIC_LABELS}
        nulls = {
            label: permutation_null(views[label], "lowvol_score", mean_ic, 50, stat_rng)
            for label in STATISTIC_LABELS
        }
        raw_p = [(label, empirical_p_value(observed[label], nulls[label])) for label in STATISTIC_LABELS]
        corrected = holm_bonferroni(raw_p)
        bootstrap_results = {label: {} for label in STATISTIC_LABELS}
        for block_length in (5, 10):
            for label in STATISTIC_LABELS:
                bootstrap_results[label][block_length] = bootstrap_ci(
                    views[label], mean_ic, "lowvol_score", block_length, 20, stat_rng
                )
        verdicts = {
            label: _statistic_verdict(label, corrected, bootstrap_results[label], (5, 10))
            for label in STATISTIC_LABELS
        }
        return {"observed": observed, "corrected": corrected, "decision": _promotion_decision(verdicts)}

    _run_a = _run_repro_pipeline(4242)
    _run_b = _run_repro_pipeline(4242)
    assert _run_a == _run_b

    print("All self-checks passed.")
