#!/usr/bin/env python3
"""REFERENCE H3 Gate 1 -- Candidate Signal Independence Verification.

Executes exactly the frozen methodology in
docs/REFERENCE_H3_PREVALIDATION_PLAN.md Section 2 against the frozen
construction in
research_archive/reference_h3/attempt_001_specification.md Section 3.5,
as of freeze commit 07f0da379d8cccf06d17c34a51cbb557da047fef. Does not
define, adjust, or interpret methodology beyond what those two frozen
documents already state -- see this module's inline citations back to
specific sections for every design choice below that is not itself a
mechanical implementation detail.

**Standalone principle, restated from the Plan Section 2:** no forward
return, IC, p-value, or other outcome variable is read, computed, or
referenced anywhere in this script. This is a same-date score-to-score
comparison only.

Reuses existing code unchanged:
- core.analytics.ranked_report.generate_ranked_etf_report() -- to read
  REFERENCE v1's already-computed MOMENTUM (SMA(20)) dimension score
  per ETF per date, exactly as validate_reference_v1_significance.py
  already does.
- experiments.validate_reference_v1_significance._rank_average_ties(),
  _pearson(), _spearman(), _percentile() -- the platform's existing
  Spearman/tie-handling implementation (Prevalidation Plan Section 2:
  "existing average-rank convention already used for this platform's
  Spearman calculations"), imported rather than re-implemented.

H3 score computed fresh from PriceBar close-to-close log returns per
attempt_001_specification.md Section 3.5 (60-trading-day trailing
cumulative log return, peer-segment-relative), Section 3.2 (frozen
six-segment grouping), and Section 3.9 (missing-data exclusion rule).
No indicator or Score row is written for H3 -- this is score
comparison only, not a platform feature.

Evaluation basis (frozen methodology table, Prevalidation Plan Section
2 "Frozen methodology summary"): restricted to the exact ranking-date
window REFERENCE v1's own analysis already covered --
research_archive/reference_v1/reference_v1_significance_report_2026-07-18.json
config.period_start / period_end (2024-07-17 to 2026-07-17).

Interpretive choice disclosed, not silently assumed: Section 2's
"score overlap analysis" specifies comparing top/bottom rank extremes
but does not itself state a bucket size. This script reuses
BUCKET_SIZE = 5, the platform's own already-frozen convention (used
throughout validate_reference_v1_significance.py, and the same value
attempt_001_specification.md Section 3.7 names as the convention a
future top-vs-bottom comparison would reuse rather than invent) --
this is a reuse of an existing frozen convention, not a new parameter
chosen for this check. See the Gate 1 report's "Interpretive choices"
section for this disclosure restated alongside the results.

Output: a factual plain-text report and a machine-readable JSON file,
same discipline as validate_reference_v1_significance.py. No PASS/FAIL
determination is written by this script -- Section 2's own
interpretation boundaries are not a mechanical threshold (see the
frozen plan's "Acceptable interpretation boundaries"), and Section 4
requires independent reviewer confirmation before Gate 1 counts as
satisfied. This script reports the measured distributions only.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.analytics.domain.models import Dimension  # noqa: E402
from core.analytics.persistence.repository import get_scoring_profile  # noqa: E402
from core.analytics.ranked_report import generate_ranked_etf_report  # noqa: E402
from core.market_data.persistence.database import connect  # noqa: E402
from core.market_data.persistence.migrations import run_migrations  # noqa: E402
from core.market_data.persistence.repository import get_price_bars, get_trading_days  # noqa: E402

from experiments.daily_etf_universe_update import CALENDAR_ID, ETF_UNIVERSE, PROFILE_NAME, PROFILE_VERSION  # noqa: E402
from experiments.validate_reference_v1_significance import (  # noqa: E402
    _pearson,
    _percentile,
    _rank_average_ties,
    _spearman,
)

DB_PATH = Path(__file__).resolve().parent.parent / "experiments_etf_universe.db"
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
DEFAULT_OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "research_archive"
    / "reference_h3"
    / "gate1_independence_analysis_2026-07-19.json"
)

# Frozen evaluation window: REFERENCE v1's own analysis, unchanged.
# Source: research_archive/reference_v1/reference_v1_significance_report_2026-07-18.json
# config.period_start / config.period_end.
PERIOD_START = date(2024, 7, 17)
PERIOD_END = date(2026, 7, 17)

# H3 construction, frozen per attempt_001_specification.md Section 3.5.
H3_LOOKBACK_TRADING_DAYS = 60

# Score-overlap bucket size -- reused platform convention, see module
# docstring "Interpretive choice disclosed".
BUCKET_SIZE = 5

# Six-segment peer grouping, frozen per attempt_001_specification.md
# Section 3.2 -- reusing, not re-authoring, the inline category comments
# in experiments/daily_etf_universe_update.py:89-120.
SEGMENTS: dict[str, list[str]] = {
    "Global equity": ["VT", "ACWI"],
    "US equity": ["SPY", "VTI", "QQQ", "IWM"],
    "Regional equity": ["EFA", "VGK", "EWJ", "EEM"],
    "Sectors": ["XLK", "XLF", "XLE", "XLV"],
    "Themes": ["ARKK", "ICLN", "SKYY", "HACK", "BOTZ"],
    "Defensive / alternative assets": ["GLD", "TLT", "BND", "VNQ", "USMV", "SCHD"],
}
SEGMENT_OF: dict[str, str] = {ticker: segment for segment, tickers in SEGMENTS.items() for ticker in tickers}


def _load_closes(conn, etf_id: str) -> dict[date, float]:
    """All resolvable close prices for one ETF, full history -- more than
    enough lookback for a 60-trading-day window starting at PERIOD_START,
    given Gate 2's confirmed 2016-09-13 coverage start."""
    bars = get_price_bars(conn, etf_id)
    return {bar.session_date: float(bar.close.amount) for bar in bars}


def compute_h3_scores(
    trading_days: list[date],
    closes_by_ticker: dict[str, dict[date, float]],
) -> dict[date, dict[str, float]]:
    """H3_score_i(t) for every ticker on every trading day with enough
    history, per attempt_001_specification.md Section 3.5 (score formula)
    and Section 3.9 (missing-data handling): an ETF is included in a
    date's cross-section only if (a) its own 60-trailing-day close-to-
    close log return is resolvable and (b) at least one other member of
    its segment also satisfies (a) on that date. own_return uses the
    trailing-60-trading-day cumulative log return convention reused from
    docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md Part 3
    ("daily close-to-close log returns", cumulative = log(close_t /
    close_(t-60)))."""
    own_return_by_date: dict[date, dict[str, float]] = {}
    for idx, t in enumerate(trading_days):
        if idx < H3_LOOKBACK_TRADING_DAYS:
            continue
        t_minus_60 = trading_days[idx - H3_LOOKBACK_TRADING_DAYS]
        day_returns: dict[str, float] = {}
        for ticker, closes in closes_by_ticker.items():
            c_t = closes.get(t)
            c_prior = closes.get(t_minus_60)
            if c_t is None or c_prior is None or c_t <= 0 or c_prior <= 0:
                continue  # (a) not satisfied -- excluded, no forward-fill/interpolation
            day_returns[ticker] = math.log(c_t / c_prior)
        own_return_by_date[t] = day_returns

    h3_by_date: dict[date, dict[str, float]] = {}
    for t, own_returns in own_return_by_date.items():
        day_scores: dict[str, float] = {}
        for ticker, own_return in own_returns.items():
            segment = SEGMENT_OF[ticker]
            peers = [p for p in SEGMENTS[segment] if p != ticker and p in own_returns]
            if not peers:
                continue  # (b) not satisfied -- excluded, no partial-window calculation
            peer_return = sum(own_returns[p] for p in peers) / len(peers)
            day_scores[ticker] = own_return - peer_return
        if day_scores:
            h3_by_date[t] = day_scores
    return h3_by_date


def compute_momentum_scores(
    conn, profile_id: str, trading_days: list[date], allowed_tickers: frozenset[str]
) -> dict[date, dict[str, float]]:
    """REFERENCE v1's already-computed MOMENTUM (SMA(20), unnormalized
    price level) dimension score per ETF per date, read via the existing
    generate_ranked_etf_report() -- no MOMENTUM computation logic is
    reimplemented here."""
    momentum_by_date: dict[date, dict[str, float]] = {}
    for t in trading_days:
        report = generate_ranked_etf_report(conn, profile_id, t)
        day_scores = {
            entry.ticker: float(entry.dimension_scores[Dimension.MOMENTUM])
            for entry in report
            if entry.ticker in allowed_tickers and Dimension.MOMENTUM in entry.dimension_scores
        }
        if day_scores:
            momentum_by_date[t] = day_scores
    return momentum_by_date


def score_overlap(
    h3_scores: dict[str, float], momentum_scores: dict[str, float], bucket_size: int
) -> dict[str, float] | None:
    """Fraction overlap between the top-`bucket_size` and bottom-
    `bucket_size` tickers under each score, per Prevalidation Plan
    Section 2 "Score overlap analysis". None if the cross-section is
    smaller than bucket_size * 2 (same minimum-panel convention as
    validate_reference_v1_significance.py's build_panel())."""
    tickers = sorted(set(h3_scores) & set(momentum_scores))
    if len(tickers) < bucket_size * 2:
        return None
    h3_ordered = sorted(tickers, key=lambda tk: h3_scores[tk], reverse=True)
    mom_ordered = sorted(tickers, key=lambda tk: momentum_scores[tk], reverse=True)
    h3_top, h3_bottom = set(h3_ordered[:bucket_size]), set(h3_ordered[-bucket_size:])
    mom_top, mom_bottom = set(mom_ordered[:bucket_size]), set(mom_ordered[-bucket_size:])
    return {
        "top_overlap_fraction": len(h3_top & mom_top) / bucket_size,
        "bottom_overlap_fraction": len(h3_bottom & mom_bottom) / bucket_size,
        "n_etfs": len(tickers),
    }


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
            print("No trading days found in the frozen REFERENCE v1 evaluation window.", file=sys.stderr)
            return 1

        allowed_tickers = frozenset(ticker for ticker, _name in ETF_UNIVERSE)
        ticker_to_etf_id = {}
        from core.market_data.persistence.repository import get_etf_by_ticker  # local import, mirrors existing style

        closes_by_ticker: dict[str, dict[date, float]] = {}
        for ticker, _name in ETF_UNIVERSE:
            etf = get_etf_by_ticker(conn, ticker)
            if etf is None:
                print(f"ETF {ticker!r} not found in database.", file=sys.stderr)
                return 1
            ticker_to_etf_id[ticker] = etf.etf_id
            closes_by_ticker[ticker] = _load_closes(conn, etf.etf_id)

        # Need trailing-60-day history relative to the FULL trading-day
        # index, not just window_days, so H3's lookback can reach back
        # before PERIOD_START correctly.
        h3_scores_by_date = compute_h3_scores(all_trading_days, closes_by_ticker)
        momentum_scores_by_date = compute_momentum_scores(conn, profile.scoring_profile_id, window_days, allowed_tickers)

        daily_results = []
        for t in window_days:
            h3_day = h3_scores_by_date.get(t)
            mom_day = momentum_scores_by_date.get(t)
            if not h3_day or not mom_day:
                continue
            common = sorted(set(h3_day) & set(mom_day))
            if len(common) < 2:
                continue
            h3_values = [h3_day[tk] for tk in common]
            mom_values = [mom_day[tk] for tk in common]
            corr = _spearman(h3_values, mom_values)
            overlap = score_overlap(h3_day, mom_day, BUCKET_SIZE)
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

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "freeze_commit": "07f0da379d8cccf06d17c34a51cbb557da047fef",
            "config": {
                "scoring_profile": f"{PROFILE_NAME} v{PROFILE_VERSION}",
                "period_start": PERIOD_START.isoformat(),
                "period_end": PERIOD_END.isoformat(),
                "h3_lookback_trading_days": H3_LOOKBACK_TRADING_DAYS,
                "bucket_size": BUCKET_SIZE,
                "etf_universe_size": len(ETF_UNIVERSE),
                "ranking_dates_evaluated": len(daily_results),
                "ranking_dates_in_window": len(window_days),
            },
            "correlation_distribution": {
                "n": len(correlations),
                "mean": (sum(correlations) / len(correlations)) if correlations else None,
                "median": _percentile(sorted(correlations), 50) if correlations else None,
                "p25": _percentile(sorted(correlations), 25) if correlations else None,
                "p75": _percentile(sorted(correlations), 75) if correlations else None,
                "min": min(correlations) if correlations else None,
                "max": max(correlations) if correlations else None,
            },
            "top_overlap_distribution": {
                "n": len(top_overlaps),
                "mean": (sum(top_overlaps) / len(top_overlaps)) if top_overlaps else None,
                "median": _percentile(sorted(top_overlaps), 50) if top_overlaps else None,
            },
            "bottom_overlap_distribution": {
                "n": len(bottom_overlaps),
                "mean": (sum(bottom_overlaps) / len(bottom_overlaps)) if bottom_overlaps else None,
                "median": _percentile(sorted(bottom_overlaps), 50) if bottom_overlaps else None,
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
    lines = ["REFERENCE H3 Gate 1 -- Candidate Signal Independence"]
    cfg = report["config"]
    lines.append(f"Scoring profile (MOMENTUM source): {cfg['scoring_profile']}")
    lines.append(f"Evaluation window: {cfg['period_start']} to {cfg['period_end']} (REFERENCE v1's own analysis window)")
    lines.append(f"H3 lookback: {cfg['h3_lookback_trading_days']} trading days")
    lines.append(f"Bucket size (overlap check): {cfg['bucket_size']}")
    lines.append(f"ETF universe size: {cfg['etf_universe_size']}")
    lines.append(f"Ranking dates evaluated: {cfg['ranking_dates_evaluated']} of {cfg['ranking_dates_in_window']} in window")
    lines.append("")
    cd = report["correlation_distribution"]
    lines.append("-- Daily Spearman correlation (H3 score vs. MOMENTUM score) --")
    lines.append(f"  n={cd['n']}  mean={cd['mean']}  median={cd['median']}  p25={cd['p25']}  p75={cd['p75']}  min={cd['min']}  max={cd['max']}")
    lines.append("")
    to = report["top_overlap_distribution"]
    bo = report["bottom_overlap_distribution"]
    lines.append(f"-- Top-{report['config']['bucket_size']} overlap fraction -- n={to['n']} mean={to['mean']} median={to['median']}")
    lines.append(f"-- Bottom-{report['config']['bucket_size']} overlap fraction -- n={bo['n']} mean={bo['mean']} median={bo['median']}")
    lines.append("")
    lines.append(
        "This is a descriptive same-date score-to-score comparison only. No forward "
        "return, IC, p-value, or promotion decision is computed or implied. No PASS/FAIL "
        "determination is made by this script -- interpretation against the frozen "
        "boundaries in docs/REFERENCE_H3_PREVALIDATION_PLAN.md Section 2 and independent "
        "reviewer confirmation per Section 4 are required before Gate 1 counts as satisfied."
    )
    return "\n".join(lines)


if __name__ == "__main__":
    # Guarded inline self-checks, same discipline as
    # validate_reference_v1_significance.py: a silent bug here would
    # produce a wrong Gate 1 figure, not just a wrong printed number.
    assert abs(_spearman([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) - 1.0) < 1e-9
    assert abs(_spearman([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]) - (-1.0)) < 1e-9

    # score_overlap(): identical rankings under both scores must overlap
    # 100% at both extremes.
    _identical = {f"e{i}": float(i) for i in range(10)}
    _overlap = score_overlap(_identical, _identical, 5)
    assert _overlap is not None
    assert _overlap["top_overlap_fraction"] == 1.0
    assert _overlap["bottom_overlap_fraction"] == 1.0

    # Reversed ranking under one score should overlap 0% at each extreme
    # with the un-reversed score, since top-5 of one is bottom-5 of the
    # other for two perfectly anti-correlated series over 10 items with
    # no tie overlap between the two halves.
    _reversed = {f"e{i}": float(9 - i) for i in range(10)}
    _overlap_rev = score_overlap(_identical, _reversed, 5)
    assert _overlap_rev is not None
    assert _overlap_rev["top_overlap_fraction"] == 0.0
    assert _overlap_rev["bottom_overlap_fraction"] == 0.0

    # compute_h3_scores(): within-group affine-transform identity from
    # attempt_001_specification.md Section 4 -- ranking two members of
    # the SAME segment by H3_score must exactly match ranking them by
    # own_return alone (algebraic property, checked numerically here on
    # synthetic data as a regression guard on this implementation).
    from datetime import timedelta as _timedelta

    _synthetic_days = [date(2020, 1, 1) + _timedelta(days=i) for i in range(65)]
    _synthetic_closes = {
        "VT": {d: 100.0 + i for i, d in enumerate(_synthetic_days)},
        "ACWI": {d: 100.0 + 2 * i for i, d in enumerate(_synthetic_days)},
    }
    _orig_segments = dict(SEGMENTS)
    _orig_segment_of = dict(SEGMENT_OF)
    SEGMENTS.clear()
    SEGMENTS["Global equity"] = ["VT", "ACWI"]
    SEGMENT_OF.clear()
    SEGMENT_OF.update({"VT": "Global equity", "ACWI": "Global equity"})
    _h3_check = compute_h3_scores(_synthetic_days, _synthetic_closes)
    _last_day = _synthetic_days[-1]
    _own_vt = math.log(_synthetic_closes["VT"][_last_day] / _synthetic_closes["VT"][_synthetic_days[4]])
    _own_acwi = math.log(_synthetic_closes["ACWI"][_last_day] / _synthetic_closes["ACWI"][_synthetic_days[4]])
    assert (_h3_check[_last_day]["ACWI"] > _h3_check[_last_day]["VT"]) == (_own_acwi > _own_vt)
    SEGMENTS.clear()
    SEGMENTS.update(_orig_segments)
    SEGMENT_OF.clear()
    SEGMENT_OF.update(_orig_segment_of)

    raise SystemExit(run())
