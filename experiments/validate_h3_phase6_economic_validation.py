#!/usr/bin/env python3
"""REFERENCE H3 Phase 6 -- Economic Validation.

Executes exactly the frozen acceptance criteria in
docs/H3_ACCEPTANCE_CRITERIA.md (freeze commit
a6439934882d5ad2c08ce8dba597810ac99e69f9) against the frozen H3
construction in
research_archive/reference_h3/attempt_001_specification.md (freeze
commit 07f0da379d8cccf06d17c34a51cbb557da047fef). This is Phase 6
(Validation) -- the first point in H3's lifecycle any forward return,
IC, p-value, or other outcome figure for H3 is read, computed, or
referenced anywhere on this platform.

**H3-A (primary, Acceptance Criteria Section 1.1).** Daily
cross-sectional Spearman correlation between H3_score_i(t) and
H3_score_i(t + horizon), one correlation per date, averaged across
dates, never pooled.

**H3-B (secondary, Acceptance Criteria Section 1.1).** Top-5 vs.
bottom-5 H3_score-ranked portfolio spread in forward raw return
(bucket_size = 5, reused unmodified from
docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md Part 6).

Both evaluated at two horizons (Acceptance Criteria Section 2.1):
60 trading days (primary, decision-relevant, governs Section 5's
decision table) and 20 trading days (secondary/diagnostic only,
reported for cross-hypothesis comparability, explicitly excluded from
the Holm-Bonferroni family and from the decision rule per Section 4.3).

Evaluation window (Acceptance Criteria Section 2.2): 2024-08-13 to
2026-07-17, reused unmodified from the window already established
through Gate 1 (docs/H3_GATE1_REPRODUCTION_REVIEW.md). At the 60-day
primary horizon, the last 60 trading days of this window cannot
produce a forward-shifted score/outcome and are mechanically excluded
-- a data-availability consequence of the frozen window, not a
discretionary trim.

Reuses existing code unchanged:
- experiments.validate_h3_gate1_independence.{compute_h3_scores,
  SEGMENTS, SEGMENT_OF} -- the frozen H3 score construction, the exact
  same formula and missing-data rule already reviewed at Gate 1.
- experiments.validate_reference_v1_significance.{_rank_average_ties,
  _pearson, _spearman, _percentile, mean_ic, top_bottom_spread,
  permutation_null, empirical_p_value, bootstrap_ci, holm_bonferroni,
  _statistic_verdict} -- the platform's existing statistical machinery
  (Acceptance Criteria Sections 4.1-4.4: within-date permutation,
  block bootstrap, Holm-Bonferroni, undefined-statistic handling),
  imported, not reimplemented, not modified.
- experiments.validate_reference_v2_h1_significance.build_statistic_view
  -- the existing generic per-statistic panel-narrowing adapter (min
  panel size, independent eligibility per statistic), imported
  unmodified.
- experiments.validate_scoring_signal.forward_return() -- the
  platform's existing simple-return convention, used for H3-B's
  outcome variable.

No parameter below is a free choice made by this script: the score
formula, the segment grouping, the two horizons, the bucket size, the
minimum panel size, the permutation/bootstrap iteration counts, the
block lengths, and the {H3-A, H3-B} Holm-Bonferroni family are each
fixed constants sourced directly from the two frozen documents cited
above, with an inline citation for each below.

Additive reporting-only construction, disclosed and NOT part of the
frozen acceptance criteria (Acceptance Criteria Sections 3.1/3.2 impose
no numeric threshold and require descriptive reporting only, with no
method specified): the H3-B drawdown/volatility series is built from
non-overlapping 60-trading-day periods (walking the primary horizon
forward by whole 60-day steps, never a rolling/overlapping window),
compounding each leg's realized period return into a cumulative NAV
series. This avoids double-counting the same days in an overlapping
60-day-forward series and produces roughly the same ~8 independent
periods Acceptance Criteria Section 2.2 already discloses as the
platform's effective sample size at this horizon. This choice affects
descriptive reporting only -- it does not enter H3-A, H3-B's point
estimate, any permutation p-value, any bootstrap CI, or the decision
table in any way.

Standalone principle: this script performs no tuning, no parameter
sweep, no alternative construction, and reports every result it
computes, including a FAIL or an "evidence against" (reversal) result,
in full, per this task's own instruction.

Usage:
    python -c "from experiments.validate_h3_phase6_economic_validation import run; raise SystemExit(run())"
"""

from __future__ import annotations

import json
import math
import random
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.market_data.persistence.database import connect  # noqa: E402
from core.market_data.persistence.migrations import run_migrations  # noqa: E402
from core.market_data.persistence.repository import (  # noqa: E402
    get_etf_by_ticker,
    get_price_bars,
    get_trading_days,
)

from experiments.daily_etf_universe_update import CALENDAR_ID, ETF_UNIVERSE  # noqa: E402
from experiments.validate_h3_gate1_independence import (  # noqa: E402
    SEGMENT_OF,
    SEGMENTS,
    compute_h3_scores,
)
from experiments.validate_reference_v1_significance import (  # noqa: E402
    _percentile,
    _statistic_verdict,
    bootstrap_ci,
    empirical_p_value,
    holm_bonferroni,
    mean_ic,
    permutation_null,
    top_bottom_spread,
)
from experiments.validate_reference_v2_h1_significance import build_statistic_view  # noqa: E402
from experiments.validate_scoring_signal import forward_return  # noqa: E402

DB_PATH = Path(__file__).resolve().parent.parent / "experiments_etf_universe.db"
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
DEFAULT_OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "research_archive"
    / "reference_h3"
    / "phase6_economic_validation_2026-07-19.json"
)

# Freeze commits this script executes against (Task instructions; verified
# against `git cat-file -t` / `git rev-parse` before this script was written).
METHODOLOGY_FREEZE_COMMIT = "07f0da379d8cccf06d17c34a51cbb557da047fef"
ACCEPTANCE_CRITERIA_FREEZE_COMMIT = "a6439934882d5ad2c08ce8dba597810ac99e69f9"

# Acceptance Criteria Section 2.2: reused unmodified from the window
# already established through Gate 1 (H3_GATE1_REPRODUCTION_REVIEW.md,
# "2024-08-13 to 2026-07-17, 483 of 502 nominal dates usable").
PERIOD_START = date(2024, 8, 13)
PERIOD_END = date(2026, 7, 17)

# Acceptance Criteria Section 2.1: dual-horizon design, 60d primary
# (governs the decision), 20d secondary/diagnostic only.
PRIMARY_HORIZON = 60
SECONDARY_HORIZON = 20

# Acceptance Criteria Section 1.1 / 3.3: bucket size and minimum panel
# size, both reused unmodified from
# docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md.
BUCKET_SIZE = 5
MIN_PANEL_SIZE = BUCKET_SIZE * 2  # 10

# Acceptance Criteria Section 4.1/4.2: permutation and bootstrap minimums.
PERMUTATIONS = 10_000
BOOTSTRAP_ITERATIONS = 2_000
BLOCK_LENGTHS = (20, 40, 60)

# Acceptance Criteria Section 4.4: single fixed, documented seed, chosen
# before any Phase 6 result was generated or examined. Distinct from
# REFERENCE v1's (20260718) and REFERENCE v2 H1's (2026071801) own seeds.
RANDOM_SEED = 2026071901

# Acceptance Criteria Section 3.3: disclosed structural weak point.
GLOBAL_EQUITY_SEGMENT = "Global equity"
GLOBAL_EQUITY_TICKERS = frozenset(SEGMENTS[GLOBAL_EQUITY_SEGMENT])

STATISTIC_LABELS = ("h3_a", "h3_b")  # Acceptance Criteria Section 4.3: exactly this 2-statistic family


# ---------------------------------------------------------------------------
# Panel construction
# ---------------------------------------------------------------------------


def _load_closes_by_ticker(conn, universe: list[tuple[str, str]]) -> dict[str, dict[date, float]]:
    closes_by_ticker: dict[str, dict[date, float]] = {}
    for ticker, _name in universe:
        etf = get_etf_by_ticker(conn, ticker)
        if etf is None:
            raise RuntimeError(f"ETF {ticker!r} not found in database.")
        bars = get_price_bars(conn, etf.etf_id)
        closes_by_ticker[ticker] = {bar.session_date: float(bar.close.amount) for bar in bars}
    return closes_by_ticker


def build_horizon_panel(
    all_trading_days: list[date],
    window_days: list[date],
    h3_scores_by_date: dict[date, dict[str, float]],
    closes_by_ticker: dict[str, dict[date, float]],
    horizon: int,
) -> list[dict]:
    """One base entry per window date with a forward-shifted score
    (H3-A's outcome) and forward raw return (H3-B's outcome) at the
    given horizon. A date is mechanically excluded if the forward date
    falls outside `all_trading_days` (Acceptance Criteria Section 2.2:
    "the last N trading days of this window cannot produce a
    forward-shifted score ... a data-availability consequence of the
    frozen window, not a discretionary trim"). No forward-fill, no
    interpolation -- missing per-ETF data at either end excludes that
    ETF from that date, per attempt_001_specification.md Section 3.9's
    convention, reused unmodified here at the outcome side."""
    index_by_date = {d: i for i, d in enumerate(all_trading_days)}
    panel: list[dict] = []
    for t in window_days:
        idx = index_by_date[t]
        forward_idx = idx + horizon
        if forward_idx >= len(all_trading_days):
            continue
        forward_date = all_trading_days[forward_idx]

        h3_now = h3_scores_by_date.get(t)
        if not h3_now:
            continue
        h3_forward = h3_scores_by_date.get(forward_date, {})

        forward_return_by_ticker: dict[str, float] = {}
        for ticker in h3_now:
            table = closes_by_ticker.get(ticker)
            if table is None:
                continue
            start_price = table.get(t)
            end_price = table.get(forward_date)
            if start_price is None or end_price is None or start_price <= 0:
                continue
            forward_return_by_ticker[ticker] = float(forward_return(start_price, end_price))

        panel.append(
            {
                "session_date": t,
                "forward_date": forward_date,
                "etf_ids": list(h3_now.keys()),
                "h3_score": h3_now,
                "h3_score_forward": h3_forward,
                "forward_return": forward_return_by_ticker,
            }
        )
    return panel


def _exclude_tickers(panel: list[dict], excluded: frozenset[str]) -> list[dict]:
    """Same panel with `excluded` tickers removed from every date's
    score/outcome dicts and etf_ids -- used for the Global-equity-segment
    sensitivity disclosure (Acceptance Criteria Section 3.3), never for
    the primary result."""
    filtered: list[dict] = []
    for day in panel:
        new_day = dict(day)
        new_day["etf_ids"] = [e for e in day["etf_ids"] if e not in excluded]
        new_day["h3_score"] = {k: v for k, v in day["h3_score"].items() if k not in excluded}
        new_day["h3_score_forward"] = {k: v for k, v in day["h3_score_forward"].items() if k not in excluded}
        new_day["forward_return"] = {k: v for k, v in day["forward_return"].items() if k not in excluded}
        filtered.append(new_day)
    return filtered


# ---------------------------------------------------------------------------
# Statistic wrappers (H3-A view uses the forward-shifted SCORE as the
# "forward_return" key mean_ic()/permutation_null()/bootstrap_ci() expect;
# H3-B view uses the actual forward RAW return -- build_statistic_view()
# is the same generic adapter REFERENCE v2 H1 already uses for exactly
# this "present a different outcome under the fixed key" purpose.)
# ---------------------------------------------------------------------------


def h3a_view(panel: list[dict], min_panel_size: int = MIN_PANEL_SIZE) -> list[dict]:
    return build_statistic_view(panel, outcome_key="h3_score_forward", score_key="h3_score", min_panel_size=min_panel_size)


def h3b_view(panel: list[dict], min_panel_size: int = MIN_PANEL_SIZE) -> list[dict]:
    return build_statistic_view(panel, outcome_key="forward_return", score_key="h3_score", min_panel_size=min_panel_size)


def _leg_returns(day: dict, score_key: str, bucket_size: int) -> tuple[float, float] | None:
    etf_ids = day["etf_ids"]
    if len(etf_ids) < bucket_size * 2:
        return None
    ordered = sorted(etf_ids, key=lambda etf_id: day[score_key][etf_id], reverse=True)
    top, bottom = ordered[:bucket_size], ordered[-bucket_size:]
    top_returns = [day["forward_return"][e] for e in top]
    bottom_returns = [day["forward_return"][e] for e in bottom]
    return sum(top_returns) / len(top_returns), sum(bottom_returns) / len(bottom_returns)


# ---------------------------------------------------------------------------
# Descriptive risk reporting (Acceptance Criteria Sections 3.1/3.2:
# required reporting, no numeric pass/fail threshold). Non-overlapping
# 60-day periods -- see module docstring's disclosed construction note.
# ---------------------------------------------------------------------------


def _non_overlapping_periods(view: list[dict], all_trading_days: list[date], horizon: int) -> list[dict]:
    index_by_date = {d: i for i, d in enumerate(all_trading_days)}
    ordered = sorted(view, key=lambda d: d["session_date"])
    periods: list[dict] = []
    next_allowed_idx = -1
    for day in ordered:
        idx = index_by_date[day["session_date"]]
        if idx < next_allowed_idx:
            continue
        periods.append(day)
        next_allowed_idx = idx + horizon
    return periods


def _drawdown_and_vol(period_returns: list[float], horizon: int) -> dict:
    if not period_returns:
        return {"n_periods": 0, "max_drawdown": None, "annualized_volatility": None, "cumulative_return": None}
    nav = [1.0]
    for r in period_returns:
        nav.append(nav[-1] * (1.0 + r))
    peak = nav[0]
    max_dd = 0.0
    for value in nav:
        peak = max(peak, value)
        dd = (peak - value) / peak if peak > 0 else 0.0
        max_dd = max(max_dd, dd)
    n = len(period_returns)
    mean_r = sum(period_returns) / n
    period_vol = math.sqrt(sum((r - mean_r) ** 2 for r in period_returns) / (n - 1)) if n >= 2 else 0.0
    periods_per_year = 252.0 / horizon
    annualized_vol = period_vol * math.sqrt(periods_per_year)
    return {
        "n_periods": n,
        "max_drawdown": max_dd,
        "annualized_volatility": annualized_vol,
        "cumulative_return": nav[-1] - 1.0,
    }


def h3b_risk_report(view60: list[dict], all_trading_days: list[date]) -> dict:
    periods = _non_overlapping_periods(view60, all_trading_days, PRIMARY_HORIZON)
    long_returns, short_returns, spread_returns = [], [], []
    for day in periods:
        legs = _leg_returns(day, "h3_score", BUCKET_SIZE)
        if legs is None:
            continue
        top_avg, bottom_avg = legs
        long_returns.append(top_avg)
        short_returns.append(bottom_avg)
        spread_returns.append(top_avg - bottom_avg)
    return {
        "construction": (
            f"Non-overlapping {PRIMARY_HORIZON}-trading-day periods walking the primary "
            "horizon forward in whole steps (reporting-only construction, not part of the "
            "frozen acceptance criteria -- see module docstring)."
        ),
        "long_leg": _drawdown_and_vol(long_returns, PRIMARY_HORIZON),
        "short_leg": _drawdown_and_vol(short_returns, PRIMARY_HORIZON),
        "spread": _drawdown_and_vol(spread_returns, PRIMARY_HORIZON),
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def _compute_statistic_block(
    view: list[dict],
    score_key: str,
    statistic_fn,
    permutations: int,
    rng: random.Random,
) -> dict:
    observed = statistic_fn(view, score_key)
    null = permutation_null(view, score_key, statistic_fn, permutations, rng)
    raw_p = empirical_p_value(observed, null) if observed is not None else None
    bootstrap = {
        block_length: bootstrap_ci(view, statistic_fn, score_key, block_length, BOOTSTRAP_ITERATIONS, rng)
        for block_length in BLOCK_LENGTHS
    }
    return {"observed": observed, "null": null, "raw_p_value": raw_p, "bootstrap": bootstrap, "n_dates": len(view)}


def run(
    db_path: Path = DB_PATH,
    universe: list[tuple[str, str]] | None = None,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    random_seed: int = RANDOM_SEED,
) -> int:
    universe = universe if universe is not None else ETF_UNIVERSE
    rng = random.Random(random_seed)

    conn = connect(db_path)
    try:
        run_migrations(conn, MIGRATIONS_DIR)

        all_trading_days = sorted(get_trading_days(conn, CALENDAR_ID))
        window_days = [d for d in all_trading_days if PERIOD_START <= d <= PERIOD_END]
        if not window_days:
            print("No trading days found in the frozen evaluation window.", file=sys.stderr)
            return 1

        closes_by_ticker = _load_closes_by_ticker(conn, universe)
        h3_scores_by_date = compute_h3_scores(all_trading_days, closes_by_ticker)

        base_panel_60 = build_horizon_panel(all_trading_days, window_days, h3_scores_by_date, closes_by_ticker, PRIMARY_HORIZON)
        base_panel_20 = build_horizon_panel(all_trading_days, window_days, h3_scores_by_date, closes_by_ticker, SECONDARY_HORIZON)

        view_h3a_60 = h3a_view(base_panel_60)
        view_h3b_60 = h3b_view(base_panel_60)
        view_h3a_20 = h3a_view(base_panel_20)
        view_h3b_20 = h3b_view(base_panel_20)

        block_h3a_60 = _compute_statistic_block(view_h3a_60, "h3_score", mean_ic, PERMUTATIONS, rng)
        block_h3b_60 = _compute_statistic_block(
            view_h3b_60, "h3_score", lambda p, k: top_bottom_spread(p, k, BUCKET_SIZE), PERMUTATIONS, rng
        )
        block_h3a_20 = _compute_statistic_block(view_h3a_20, "h3_score", mean_ic, PERMUTATIONS, rng)
        block_h3b_20 = _compute_statistic_block(
            view_h3b_20, "h3_score", lambda p, k: top_bottom_spread(p, k, BUCKET_SIZE), PERMUTATIONS, rng
        )

        # Holm-Bonferroni jointly across exactly {H3-A, H3-B} at the
        # primary 60d horizon only (Acceptance Criteria Section 4.3). The
        # 20d diagnostics are explicitly excluded from this family.
        raw_p_60 = [
            (label, block["raw_p_value"])
            for label, block in (("h3_a", block_h3a_60), ("h3_b", block_h3b_60))
            if block["raw_p_value"] is not None
        ]
        corrected_60 = holm_bonferroni(raw_p_60)

        verdict_h3a_60 = _statistic_verdict("h3_a", corrected_60, block_h3a_60["bootstrap"], BLOCK_LENGTHS)
        verdict_h3b_60 = _statistic_verdict("h3_b", corrected_60, block_h3b_60["bootstrap"], BLOCK_LENGTHS)

        h3a_correct_sign = block_h3a_60["observed"] is not None and block_h3a_60["observed"] > 0
        h3b_correct_sign = block_h3b_60["observed"] is not None and block_h3b_60["observed"] > 0
        h3a_passes_final = verdict_h3a_60["passes"] and h3a_correct_sign
        h3b_passes_final = verdict_h3b_60["passes"] and h3b_correct_sign

        h3a_significant_reversal = verdict_h3a_60["significant_after_correction"] and not h3a_correct_sign
        h3b_significant_reversal = verdict_h3b_60["significant_after_correction"] and not h3b_correct_sign

        undefined_statistic = (
            block_h3a_60["observed"] is None
            or block_h3b_60["observed"] is None
            or any(ci is None for ci in block_h3a_60["bootstrap"].values())
            or any(ci is None for ci in block_h3b_60["bootstrap"].values())
        )

        decision = _decide(
            h3a_passes_final, h3b_passes_final, h3a_significant_reversal, h3b_significant_reversal, undefined_statistic
        )

        # Global-equity-segment sensitivity (Acceptance Criteria Section
        # 3.3): observed point estimate + raw permutation p-value only,
        # disclosed, not a pass/fail gate.
        base_panel_60_ex_ge = _exclude_tickers(base_panel_60, GLOBAL_EQUITY_TICKERS)
        view_h3a_60_ex_ge = h3a_view(base_panel_60_ex_ge)
        view_h3b_60_ex_ge = h3b_view(base_panel_60_ex_ge)
        ex_ge_h3a = {
            "observed": mean_ic(view_h3a_60_ex_ge, "h3_score"),
            "n_dates": len(view_h3a_60_ex_ge),
        }
        ex_ge_h3b = {
            "observed": top_bottom_spread(view_h3b_60_ex_ge, "h3_score", BUCKET_SIZE),
            "n_dates": len(view_h3b_60_ex_ge),
        }

        risk_report = h3b_risk_report(view_h3b_60, all_trading_days)

        report = _build_report(
            window_days=window_days,
            base_panel_60=base_panel_60,
            block_h3a_60=block_h3a_60,
            block_h3b_60=block_h3b_60,
            block_h3a_20=block_h3a_20,
            block_h3b_20=block_h3b_20,
            corrected_60=corrected_60,
            verdict_h3a_60=verdict_h3a_60,
            verdict_h3b_60=verdict_h3b_60,
            h3a_correct_sign=h3a_correct_sign,
            h3b_correct_sign=h3b_correct_sign,
            h3a_passes_final=h3a_passes_final,
            h3b_passes_final=h3b_passes_final,
            h3a_significant_reversal=h3a_significant_reversal,
            h3b_significant_reversal=h3b_significant_reversal,
            undefined_statistic=undefined_statistic,
            decision=decision,
            ex_ge_h3a=ex_ge_h3a,
            ex_ge_h3b=ex_ge_h3b,
            risk_report=risk_report,
            universe_size=len(universe),
            random_seed=random_seed,
        )

        print(_format_report(report))
        output_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print()
        print(f"Machine-readable report written to {output_path}")
        return 0
    finally:
        conn.close()


def _decide(h3a_pass, h3b_pass, h3a_reversal, h3b_reversal, undefined) -> dict:
    if h3a_reversal or h3b_reversal:
        return {
            "outcome": "EVIDENCE_AGAINST",
            "reason": (
                "Significant reversal per Acceptance Criteria Section 5.2 item 2: at least one "
                "of H3-A/H3-B is Holm-Bonferroni significant in the direction opposite the "
                "hypothesis's stated prediction. Recorded as evidence against the mechanism, "
                "not a milder finding than FAIL."
            ),
        }
    if undefined:
        return {
            "outcome": "FAIL",
            "reason": (
                "Undefined statistic per Acceptance Criteria Section 4.4/5.2 item 3: an "
                "undefined permutation p-value or bootstrap CI at a required block length "
                "automatically fails that criterion, no manual interpretation."
            ),
        }
    if h3a_pass and h3b_pass:
        return {
            "outcome": "ECONOMICALLY_SUPPORTED_H3A_H3B",
            "reason": "Both H3-A (primary) and H3-B (secondary) passed with correct sign (Acceptance Criteria Section 5.1 row 1).",
        }
    if h3a_pass and not h3b_pass:
        return {
            "outcome": "ECONOMICALLY_SUPPORTED_H3A_ONLY",
            "reason": "H3-A (primary) passed alone; H3-B did not (Acceptance Criteria Section 5.1 row 2).",
        }
    if not h3a_pass and h3b_pass:
        return {
            "outcome": "NOT_ECONOMICALLY_SUPPORTED",
            "reason": (
                "H3-B passed alone; the primary persistence test (H3-A) did not clear the bar "
                "(Acceptance Criteria Section 5.1 row 3). Portfolio spread observed, primary "
                "persistence test not confirmed."
            ),
        }
    return {
        "outcome": "FAIL",
        "reason": "Neither H3-A nor H3-B passed (Acceptance Criteria Section 5.1 row 4).",
    }


def _build_report(
    *,
    window_days,
    base_panel_60,
    block_h3a_60,
    block_h3b_60,
    block_h3a_20,
    block_h3b_20,
    corrected_60,
    verdict_h3a_60,
    verdict_h3b_60,
    h3a_correct_sign,
    h3b_correct_sign,
    h3a_passes_final,
    h3b_passes_final,
    h3a_significant_reversal,
    h3b_significant_reversal,
    undefined_statistic,
    decision,
    ex_ge_h3a,
    ex_ge_h3b,
    risk_report,
    universe_size,
    random_seed,
) -> dict:
    def _stat_block(block, corrected_label, corrected, verdict, correct_sign, passes_final):
        correction = corrected.get(corrected_label, {"raw_p_value": None, "adjusted_p_value": None})
        return {
            "observed": block["observed"],
            "n_dates": block["n_dates"],
            "raw_p_value": block["raw_p_value"],
            "adjusted_p_value": correction["adjusted_p_value"],
            "bootstrap": {
                f"block_{bl}": (
                    {"ci_low": ci[0], "ci_high": ci[1], "excludes_zero": not (ci[0] <= 0.0 <= ci[1])}
                    if ci is not None
                    else None
                )
                for bl, ci in block["bootstrap"].items()
            },
            "significant_after_correction": verdict["significant_after_correction"],
            "bootstrap_robust_across_block_lengths": verdict["bootstrap_robust_across_block_lengths"],
            "correct_sign": correct_sign,
            "passes": passes_final,
        }

    def _diagnostic_block(block):
        return {
            "observed": block["observed"],
            "n_dates": block["n_dates"],
            "raw_p_value_uncorrected": block["raw_p_value"],
            "bootstrap": {
                f"block_{bl}": (
                    {"ci_low": ci[0], "ci_high": ci[1], "excludes_zero": not (ci[0] <= 0.0 <= ci[1])}
                    if ci is not None
                    else None
                )
                for bl, ci in block["bootstrap"].items()
            },
            "note": "Diagnostic only, per Acceptance Criteria Section 2.1/4.3 -- not in the Holm-Bonferroni family, not decision-relevant.",
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology_freeze_commit": METHODOLOGY_FREEZE_COMMIT,
        "acceptance_criteria_freeze_commit": ACCEPTANCE_CRITERIA_FREEZE_COMMIT,
        "config": {
            "period_start": PERIOD_START.isoformat(),
            "period_end": PERIOD_END.isoformat(),
            "primary_horizon_trading_days": PRIMARY_HORIZON,
            "secondary_horizon_trading_days": SECONDARY_HORIZON,
            "bucket_size": BUCKET_SIZE,
            "min_panel_size": MIN_PANEL_SIZE,
            "etf_universe_size": universe_size,
            "ranking_dates_in_window": len(window_days),
            "ranking_dates_base_panel_60d": len(base_panel_60),
            "permutations": PERMUTATIONS,
            "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
            "block_lengths": list(BLOCK_LENGTHS),
            "random_seed": random_seed,
        },
        "h3_a_60d_primary": _stat_block(block_h3a_60, "h3_a", corrected_60, verdict_h3a_60, h3a_correct_sign, h3a_passes_final),
        "h3_b_60d_primary": _stat_block(block_h3b_60, "h3_b", corrected_60, verdict_h3b_60, h3b_correct_sign, h3b_passes_final),
        "h3_a_20d_diagnostic": _diagnostic_block(block_h3a_20),
        "h3_b_20d_diagnostic": _diagnostic_block(block_h3b_20),
        "reversal_flags": {
            "h3_a_significant_reversal": h3a_significant_reversal,
            "h3_b_significant_reversal": h3b_significant_reversal,
        },
        "undefined_statistic_detected": undefined_statistic,
        "global_equity_segment_sensitivity": {
            "with_global_equity": {"h3_a_observed": block_h3a_60["observed"], "h3_b_observed": block_h3b_60["observed"]},
            "without_global_equity": {"h3_a_observed": ex_ge_h3a["observed"], "h3_b_observed": ex_ge_h3b["observed"]},
            "note": "Reporting requirement per Acceptance Criteria Section 3.3, not a pass/fail gate on its own.",
        },
        "h3_b_risk_report": risk_report,
        "decision": decision,
    }


def _format_report(report: dict) -> str:
    lines = ["REFERENCE H3 Phase 6 -- Economic Validation"]
    cfg = report["config"]
    lines.append(f"Methodology freeze: {report['methodology_freeze_commit']}")
    lines.append(f"Acceptance criteria freeze: {report['acceptance_criteria_freeze_commit']}")
    lines.append(f"Window: {cfg['period_start']} to {cfg['period_end']}")
    lines.append(f"Horizons: {cfg['primary_horizon_trading_days']}d primary / {cfg['secondary_horizon_trading_days']}d diagnostic")
    lines.append(f"Random seed: {cfg['random_seed']}")
    lines.append("")
    for label, key in (("H3-A (60d primary)", "h3_a_60d_primary"), ("H3-B (60d primary)", "h3_b_60d_primary")):
        s = report[key]
        lines.append(f"-- {label} --")
        lines.append(f"  n={s['n_dates']}  observed={s['observed']}")
        lines.append(f"  raw p={s['raw_p_value']}  adjusted p={s['adjusted_p_value']}")
        lines.append(f"  significant={s['significant_after_correction']}  bootstrap_robust={s['bootstrap_robust_across_block_lengths']}  correct_sign={s['correct_sign']}")
        lines.append(f"  PASSES: {s['passes']}")
        for bkey, ci in s["bootstrap"].items():
            lines.append(f"  {bkey}: {ci}")
        lines.append("")
    lines.append(f"Decision: {report['decision']['outcome']}")
    lines.append(f"Reason: {report['decision']['reason']}")
    return "\n".join(lines)


if __name__ == "__main__":
    # Guarded inline self-checks, no database access -- same discipline
    # as the other frozen-methodology scripts in this directory.

    # h3a_view()/h3b_view() reuse build_statistic_view() correctly: a
    # panel where one ETF is missing h3_score_forward must be excluded
    # from H3-A's view but still present in H3-B's view (independent
    # eligibility, per statistic).
    _synthetic_panel = [
        {
            "session_date": date(2025, 1, 2),
            "etf_ids": [f"E{i}" for i in range(12)],
            "h3_score": {f"E{i}": 0.01 * i for i in range(12)},
            "h3_score_forward": {f"E{i}": 0.02 * i for i in range(11)},  # E11 missing
            "forward_return": {f"E{i}": 0.001 * i for i in range(12)},
        }
    ]
    _a_view = h3a_view(_synthetic_panel, min_panel_size=5)
    _b_view = h3b_view(_synthetic_panel, min_panel_size=5)
    assert len(_a_view) == 1 and "E11" not in _a_view[0]["etf_ids"] and len(_a_view[0]["etf_ids"]) == 11
    assert len(_b_view) == 1 and len(_b_view[0]["etf_ids"]) == 12

    # _leg_returns(): top bucket must be the highest-h3_score ETFs.
    _legs = _leg_returns(_synthetic_panel[0], "h3_score", 5)
    assert _legs is not None
    _top_avg, _bottom_avg = _legs
    assert _top_avg > _bottom_avg  # scores and forward_return both monotonic increasing in E-index here

    # _exclude_tickers(): removes exactly the requested tickers from
    # every dict, leaves everything else untouched.
    _excluded = _exclude_tickers(_synthetic_panel, frozenset({"E0", "E1"}))
    assert "E0" not in _excluded[0]["etf_ids"] and "E1" not in _excluded[0]["etf_ids"]
    assert "E2" in _excluded[0]["etf_ids"]
    assert len(_excluded[0]["etf_ids"]) == 10

    # _drawdown_and_vol(): a monotonically increasing NAV path has zero
    # drawdown; an interim dip below a prior peak is captured correctly.
    _dd_flat = _drawdown_and_vol([0.01, 0.01, 0.01], 60)
    assert _dd_flat["max_drawdown"] == 0.0
    _dd_dip = _drawdown_and_vol([0.10, -0.20, 0.05], 60)
    # NAV: 1.0 -> 1.10 -> 0.88 -> 0.924 ; peak 1.10, trough 0.88 -> dd = 0.2
    assert abs(_dd_dip["max_drawdown"] - 0.2) < 1e-9

    # _non_overlapping_periods(): consecutive daily entries collapse to
    # periods spaced at least `horizon` trading-day-indices apart.
    _daily_days = [date(2025, 1, 1) + __import__("datetime").timedelta(days=i) for i in range(150)]
    _daily_view = [{"session_date": d} for d in _daily_days]
    _periods = _non_overlapping_periods(_daily_view, _daily_days, 60)
    assert len(_periods) == 3  # indices 0, 60, 120 out of 150 daily-indexed entries
    assert [p["session_date"] for p in _periods] == [_daily_days[0], _daily_days[60], _daily_days[120]]

    # _decide(): each of the five branches in Acceptance Criteria Section
    # 5.1/5.2, exhaustively.
    assert _decide(True, True, False, False, False)["outcome"] == "ECONOMICALLY_SUPPORTED_H3A_H3B"
    assert _decide(True, False, False, False, False)["outcome"] == "ECONOMICALLY_SUPPORTED_H3A_ONLY"
    assert _decide(False, True, False, False, False)["outcome"] == "NOT_ECONOMICALLY_SUPPORTED"
    assert _decide(False, False, False, False, False)["outcome"] == "FAIL"
    assert _decide(True, True, True, False, False)["outcome"] == "EVIDENCE_AGAINST"
    assert _decide(False, False, False, True, False)["outcome"] == "EVIDENCE_AGAINST"
    assert _decide(False, False, False, False, True)["outcome"] == "FAIL"

    print("All self-checks passed.")
