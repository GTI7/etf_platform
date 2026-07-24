"""`reference_h4` Phase 5 implementation: the frozen methodology
(research_archive/reference_h4/methodology.md), built exactly as frozen --
no design decision is made in this file that wasn't already fixed there.

Computes, per ETF in the frozen 25-ETF universe, the sample excess
kurtosis (Fisher, uncorrected) of daily log returns; aggregates via the
cross-sectional median; and reports its 95% confidence interval via i.i.d.
bootstrap resampling across the 25 ETF-level point estimates (methodology.md
Section 6 -- fixed seed 20260725, 10,000 iterations). This is deliberately
not a reuse of `core.statistics.significance.bootstrap_ci`: that function's
block-bootstrap-over-a-panel shape resamples consecutive time periods
within one series, a different sampling unit than this cycle's
cross-sectional resample across independent ETFs (methodology.md Section
6). Kurtosis and the bootstrap routine stay local to this experiment
script rather than being added to `core/statistics` (not yet justified as
a reusable primitive by a second use).

Exposes `run(db_path)`, the one calling convention every pinned experiment
script exposes for `core.governance.reproduction_runner` (SS F.2:
"Run `run(db_path=<scratch path>, ...)` from the worktree's own copy of
the experiment script"). Read-only: never writes to `db_path`'s database,
so `assert_frozen_identity_unchanged` (identity_verification.py) holds
trivially.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any

from core.market_data.persistence.repository import get_etf_by_ticker, get_price_bars
from core.store.connection import connect

# Methodology Freeze Section 1 -- the exact 25-ticker universe, fixed.
UNIVERSE: tuple[str, ...] = (
    "ACWI", "ARKK", "BND", "BOTZ", "EEM", "EFA", "EWJ", "GLD", "HACK",
    "ICLN", "IWM", "QQQ", "SCHD", "SKYY", "SPY", "TLT", "USMV", "VGK",
    "VNQ", "VT", "VTI", "XLE", "XLF", "XLK", "XLV",
)

# Methodology Freeze Section 6 -- fixed seed and iteration count.
BOOTSTRAP_SEED = 20260725
BOOTSTRAP_ITERATIONS = 10_000


def _log_returns(closes: list[float]) -> list[float]:
    """Methodology Section 3: r_t = ln(close_t / close_{t-1}), taken in
    session_date order (the order `get_price_bars` already returns)."""
    return [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]


def _sample_excess_kurtosis(values: list[float]) -> float:
    """Methodology Section 4: plain (uncorrected) sample excess kurtosis,
    Fisher definition. No small-sample bias correction (methodology.md
    states why: negligible effect at this cycle's n, and an added degree
    of freedom this methodology does not need)."""
    n = len(values)
    mean = sum(values) / n
    m2 = sum((v - mean) ** 2 for v in values) / n
    m4 = sum((v - mean) ** 4 for v in values) / n
    return m4 / (m2 ** 2) - 3.0


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 1:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Linear-interpolation percentile, matching
    `core.statistics.significance.percentile`'s convention."""
    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]
    rank = (pct / 100.0) * (n - 1)
    lower = int(math.floor(rank))
    upper = int(math.ceil(rank))
    if lower == upper:
        return sorted_values[lower]
    fraction = rank - lower
    return sorted_values[lower] + fraction * (sorted_values[upper] - sorted_values[lower])


def _bootstrap_median_ci(
    point_estimates: list[float], iterations: int, seed: int
) -> tuple[float, float]:
    """Methodology Section 6: i.i.d. resample-with-replacement across the
    per-ETF point estimates (not a time-series block bootstrap), median
    each draw, percentile CI."""
    rng = random.Random(seed)
    n = len(point_estimates)
    draws: list[float] = []
    for _ in range(iterations):
        resample = [point_estimates[rng.randrange(0, n)] for _ in range(n)]
        draws.append(_median(resample))
    draws.sort()
    return _percentile(draws, 2.5), _percentile(draws, 97.5)


def run(db_path: Path | str) -> dict[str, Any]:
    """Compute per-ETF excess kurtosis over the frozen universe, the
    cross-sectional median, and its bootstrap CI. Read-only against
    `db_path`; raises if any universe ticker or its PriceBar history is
    missing (an unresolvable input, per Standard Section 6 item 4 --
    never silently skipped)."""
    conn = connect(db_path)
    try:
        per_etf_kurtosis: dict[str, float] = {}
        per_etf_n: dict[str, int] = {}
        for ticker in UNIVERSE:
            etf = get_etf_by_ticker(conn, ticker)
            if etf is None:
                raise ValueError(f"universe ticker {ticker!r} has no ETF row in {db_path}")
            bars = get_price_bars(conn, etf.etf_id)
            if len(bars) < 2:
                raise ValueError(f"{ticker!r} has fewer than 2 PriceBar rows in {db_path}")
            closes = [float(bar.close.amount) for bar in bars]
            returns = _log_returns(closes)
            per_etf_kurtosis[ticker] = _sample_excess_kurtosis(returns)
            per_etf_n[ticker] = len(returns)
    finally:
        conn.close()

    point_estimates = [per_etf_kurtosis[ticker] for ticker in UNIVERSE]
    cross_sectional_median = _median(point_estimates)
    ci_low, ci_high = _bootstrap_median_ci(point_estimates, BOOTSTRAP_ITERATIONS, BOOTSTRAP_SEED)

    return {
        "universe": list(UNIVERSE),
        "per_etf_excess_kurtosis": per_etf_kurtosis,
        "per_etf_n_returns": per_etf_n,
        "cross_sectional_median_excess_kurtosis": cross_sectional_median,
        "bootstrap_ci_95": {"low": ci_low, "high": ci_high},
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "bootstrap_seed": BOOTSTRAP_SEED,
    }


if __name__ == "__main__":
    import sys

    db_path_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("experiments_etf_universe.db")
    result = run(db_path_arg)
    print(json.dumps(result, indent=2))
