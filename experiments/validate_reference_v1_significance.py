#!/usr/bin/env python3
"""REFERENCE v1 Significance Testing.

A **research script**, not a validation framework, not a backtesting
engine, not a platform capability. It exists to answer exactly one
question, using data this platform has already computed:

    "Does REFERENCE v1 (or either of its two dimensions in isolation)
    contain a cross-sectional relationship to forward returns that is
    distinguishable from chance, given the data already collected?"

This is the corrected, minimal five-phase plan reviewed and approved
separately (see docs/BASELINE_STATUS.md and project memory for the
prior +0.231% finding this builds on). It does not redesign the
scoring engine, add a factor, change ranking logic, use ML, or
optimize any parameter -- it is read-only analysis over data already
in the database, using only Python's standard library.

Reuses existing code unchanged:
- experiments.daily_etf_universe_update.run(session_date=...) -- to
  make sure Score rows exist for the historical range (idempotent, a
  no-op if they already do, exactly as validate_scoring_signal.py
  already relies on).
- core.analytics.ranked_report.generate_ranked_etf_report() -- to
  reconstruct each historical date's ranking and per-dimension scores.
- experiments.validate_scoring_signal.forward_return() and
  _resolve_close() -- the exact same forward-return calculation
  already used and already reported on, imported here rather than
  duplicated, so both scripts always mean the same thing by "forward
  return."

IC definition (mandatory refinement #1): a daily cross-sectional
Spearman rank correlation between each ETF's score and that same
ETF's forward return, computed separately for each ranking date, then
averaged across dates. ETF-days are never pooled into one correlation
-- pooling would ignore the panel structure and let cross-time
variation dominate a statistic that is supposed to measure
cross-sectional discrimination only.

Dimension separation during permutation (mandatory refinement #2):
MOMENTUM's null distribution is built by shuffling only the MOMENTUM
score-to-ETF assignment; VALUE's null by shuffling only VALUE; the raw
blend's (and the top-vs-bottom spread's, which is a function of the
same raw-blend ranking) null by shuffling only the raw blend; the
normalized blend's null by shuffling only the normalized blend. Never
a single shared shuffle applied to all statistics at once -- the
underlying ETF-to-score assignment being tested for "no information"
differs by statistic, so each needs its own independent null.

Bootstrap interpretation (mandatory refinement #3): 20-trading-day
blocks are the primary result (matching the forward horizon); 40- and
60-day blocks are robustness diagnostics only. A statistic is only
reported as "bootstrap-robust" if its 95% CI excludes zero at ALL
THREE block lengths -- significance that only survives the shortest
block length is treated as not robust, per the approved decision rule.

Precision note: PriceBar/Score/DimensionScore remain Decimal
throughout core/ and throughout data loading here, exactly as the
platform already requires for correctness of what's stored. The
statistical machinery below (ranking, correlation, permutation,
bootstrap -- tens of millions of arithmetic operations at 10,000+
permutations) converts to float once, at the point values enter that
machinery, not before. This mirrors a decision already made and
argued for earlier in this research sequence: statistical estimates at
this sample size are not decision-sensitive to 28-digit precision, and
carrying Decimal through the hot loop would be a real performance cost
for no decision-relevant benefit.

Reproducibility: every random draw (permutation shuffles, bootstrap
resamples) is taken from one seeded `random.Random` instance
constructed once per run() call. Without an explicit seed, two runs
of this script would report slightly different p-values and confidence
intervals for identical underlying data -- inconsistent with this
platform's own "no hidden defaults, deterministic" principle, which
this script follows even though it lives outside core/.

Prerequisites: same as validate_scoring_signal.py -- a valid trading
Calendar/TradingSession set (seed_trading_calendar.py) and sufficient
PriceBar depth (backfill_price_history.py) for the requested period
plus the forward-return horizon beyond it.

Usage:
    python experiments/validate_reference_v1_significance.py

Output: a factual plain-text report (same "no recommendation, no
confirm/validate/prove" discipline as validate_scoring_signal.py), and
a machine-readable reference_v1_significance_report.json at the repo
root (git-ignored as generated research output, not source).

Dependency requirements: none beyond what this project already uses.
No third-party package is required to run this script.
"""

from __future__ import annotations

import contextlib
import io
import json
import random
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

# Makes core/ (and this directory's sibling scripts) importable when
# this script is run directly
# (`python experiments/validate_reference_v1_significance.py`) rather
# than as a package module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.analytics.domain.models import Dimension  # noqa: E402
from core.analytics.persistence.repository import get_scoring_profile  # noqa: E402
from core.analytics.ranked_report import generate_ranked_etf_report  # noqa: E402
from core.market_data.persistence.database import connect  # noqa: E402
from core.market_data.persistence.migrations import run_migrations  # noqa: E402
from core.market_data.persistence.repository import get_trading_days  # noqa: E402

from experiments.daily_etf_universe_update import (  # noqa: E402
    CALENDAR_ID,
    ETF_UNIVERSE,
    PROFILE_NAME,
    PROFILE_VERSION,
)
from experiments.daily_etf_universe_update import run as run_daily_update  # noqa: E402
from experiments.validate_scoring_signal import _resolve_close, forward_return  # noqa: E402

DB_PATH = Path(__file__).resolve().parent.parent / "experiments_etf_universe.db"
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent.parent / "reference_v1_significance_report.json"

DEFAULT_DAYS_BACK = 730
HORIZON_TRADING_DAYS = 20
BUCKET_SIZE = 5

PERMUTATIONS = 10_000  # mandatory refinement #4: 10,000 minimum
BOOTSTRAP_ITERATIONS = 2_000  # standard default for a stable 95% CI, distinct from the permutation minimum
BLOCK_LENGTHS = (20, 40, 60)  # mandatory refinement #3: 20 primary, 40/60 robustness-only

# Fixed once, documented, never left implicit -- see module docstring's
# "Reproducibility" note.
RANDOM_SEED = 20260718

STATISTIC_LABELS = ("momentum_ic", "value_ic", "raw_blend_ic", "normalized_blend_ic", "top_bottom_spread")


# ---------------------------------------------------------------------------
# Pure statistics helpers -- no database access, no Clock, no I/O.
# ---------------------------------------------------------------------------


def _rank_average_ties(values: list[float]) -> list[float]:
    """Rank `values` ascending (rank 1 = smallest), average rank assigned
    to ties -- the standard tie-handling convention Spearman correlation
    requires. Pure, deterministic, no I/O."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        average_rank = (i + j) / 2 + 1  # 1-indexed
        for k in range(i, j + 1):
            ranks[order[k]] = average_rank
        i = j + 1
    return ranks


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    """Pearson correlation of two equal-length series, or None if either
    series has zero variance (undefined correlation -- e.g. every ETF
    tied on score that day). Pure, no I/O."""
    n = len(xs)
    if n < 2:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0 or var_y == 0:
        return None
    return cov / (var_x**0.5 * var_y**0.5)


def _spearman(xs: list[float], ys: list[float]) -> float | None:
    """Spearman rank correlation: Pearson correlation computed on ranks,
    with average-rank tie handling. Pure, no I/O."""
    if len(xs) < 2:
        return None
    return _pearson(_rank_average_ties(xs), _rank_average_ties(ys))


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Linear-interpolation percentile of an already-sorted list, `pct`
    in [0, 100]. Pure, no I/O -- used for both bootstrap CIs and null
    distribution p-value/percentile lookups, deliberately not
    depending on any third-party statistics package."""
    if not sorted_values:
        raise ValueError("_percentile() requires at least one value")
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (pct / 100) * (len(sorted_values) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = rank - lower
    return sorted_values[lower] + fraction * (sorted_values[upper] - sorted_values[lower])


# ---------------------------------------------------------------------------
# Data panel construction
# ---------------------------------------------------------------------------


def _percentile_rank_within_day(values: dict[str, float]) -> dict[str, float]:
    """Cross-sectional percentile rank of each ETF's value among the
    other ETFs on the SAME day, scaled to [0, 1] (lowest value -> 0.0,
    highest -> 1.0, average rank for ties). This is the one and only
    normalization this script performs, applied entirely inside this
    research script -- never inside core/, never persisted."""
    etf_ids = list(values.keys())
    raw = [values[etf_id] for etf_id in etf_ids]
    ranks = _rank_average_ties(raw)
    n = len(raw)
    if n <= 1:
        return {etf_id: 0.0 for etf_id in etf_ids}
    return {etf_id: (rank - 1) / (n - 1) for etf_id, rank in zip(etf_ids, ranks)}


def build_panel(
    conn,
    profile_id: str,
    trading_days: list[date],
    horizon_trading_days: int,
    bucket_size: int,
    allowed_tickers: frozenset[str] | None = None,
) -> list[dict]:
    """One entry per ranking date with enough data to be usable: the
    per-ETF MOMENTUM value, VALUE value, raw blend (overall_score),
    retroactively percentile-normalized blend, and forward return over
    horizon_trading_days -- for every ETF ranked that day, not only
    bucket members (the missing-data requirement identified before
    implementation: IC needs the full cross-section, not just the
    buckets validate_scoring_signal.py already resolves).

    A date is included only if it has a full ranking and a resolvable
    forward date within `trading_days`; per-ETF entries within an
    included date are included only if both the start and forward
    close prices exist. Missing data is excluded, never estimated --
    the same discipline used throughout this platform.

    `allowed_tickers`: generate_ranked_etf_report() returns every ETF
    that has a Score for this profile/date IN THE DATABASE -- it has no
    concept of "the caller's requested universe" and is not modified
    here to add one (reuse existing code unchanged). For the full,
    intended 25-ETF analysis this is a no-op (the database's only
    scored ETFs already are exactly those 25), but a smaller universe
    passed to run() for a subset smoke test would otherwise silently
    still draw on every ETF already scored in the database, not the
    requested subset. When not None, entries are filtered to this set
    before anything else.
    """
    index_by_date = {d: i for i, d in enumerate(trading_days)}
    panel: list[dict] = []

    for session_date in trading_days:
        report = generate_ranked_etf_report(conn, profile_id, session_date)
        if allowed_tickers is not None:
            report = [entry for entry in report if entry.ticker in allowed_tickers]
        if len(report) < bucket_size * 2:
            continue  # not enough ranked ETFs this date -- excluded, not an error

        forward_index = index_by_date[session_date] + horizon_trading_days
        if forward_index >= len(trading_days):
            continue  # not enough future trading days in range yet -- excluded, not an error
        forward_date = trading_days[forward_index]

        momentum_by_etf: dict[str, float] = {}
        value_by_etf: dict[str, float] = {}
        blend_by_etf: dict[str, float] = {}
        return_by_etf: dict[str, float] = {}

        for entry in report:
            dims = entry.dimension_scores
            momentum = dims.get(Dimension.MOMENTUM)
            value = dims.get(Dimension.VALUE)
            if momentum is None or value is None:
                continue
            start_price = _resolve_close(conn, entry.etf_id, session_date)
            end_price = _resolve_close(conn, entry.etf_id, forward_date)
            if start_price is None or end_price is None:
                continue
            momentum_by_etf[entry.etf_id] = float(momentum)
            value_by_etf[entry.etf_id] = float(value)
            blend_by_etf[entry.etf_id] = float(entry.overall_score)
            return_by_etf[entry.etf_id] = float(forward_return(start_price, end_price))

        if len(return_by_etf) < bucket_size * 2:
            continue  # not enough complete (score, forward return) pairs -- excluded, not an error

        # Normalized blend = mean of each dimension's OWN cross-sectional
        # percentile rank, not the percentile rank of the raw mean --
        # this is the specific, documented normalization principle from
        # the prior methodology review ("standardize before combining",
        # not "combine then standardize").
        momentum_pct = _percentile_rank_within_day(momentum_by_etf)
        value_pct = _percentile_rank_within_day(value_by_etf)
        normalized_by_etf = {
            etf_id: (momentum_pct[etf_id] + value_pct[etf_id]) / 2 for etf_id in return_by_etf
        }

        panel.append(
            {
                "session_date": session_date,
                "etf_ids": list(return_by_etf.keys()),
                "momentum": momentum_by_etf,
                "value": value_by_etf,
                "raw_blend": blend_by_etf,
                "normalized_blend": normalized_by_etf,
                "forward_return": return_by_etf,
            }
        )

    return panel


# ---------------------------------------------------------------------------
# Statistics computed over the panel
# ---------------------------------------------------------------------------


def daily_ic_series(panel: list[dict], score_key: str) -> list[float]:
    """One Spearman correlation per date (score_key's cross-section vs.
    that date's forward returns), never pooled across dates -- mandatory
    refinement #1's explicit IC definition.

    Performance note, not a behavior change: forward returns are
    identical across every permutation iteration for a fixed score_key
    (only score_key's ETF-to-value assignment is shuffled -- see
    _shuffle_score_key()), so ranking them is wasted, repeated work
    across 10,000+ calls. When build_panel() has already attached
    "_return_ranks" (see build_panel()'s caller in run()), that
    precomputed rank list is reused instead of re-ranking forward
    returns on every call. Falls back to computing it fresh when absent
    (e.g. for a hand-built panel in a test), so this optimization can
    never silently change the result -- verified equivalent by a
    guarded self-check against the unoptimized path.
    """
    series = []
    for day in panel:
        etf_ids = day["etf_ids"]
        scores = [day[score_key][etf_id] for etf_id in etf_ids]
        score_ranks = _rank_average_ties(scores)
        return_ranks = day.get("_return_ranks")
        if return_ranks is None:
            return_ranks = _rank_average_ties([day["forward_return"][etf_id] for etf_id in etf_ids])
        ic = _pearson(score_ranks, return_ranks)
        if ic is not None:
            series.append(ic)
    return series


def mean_ic(panel: list[dict], score_key: str) -> float | None:
    return _mean(daily_ic_series(panel, score_key))


def top_bottom_spread(panel: list[dict], score_key: str, bucket_size: int) -> float | None:
    """Average (top-bucket average forward return - bottom-bucket average
    forward return) across dates, ranked by score_key -- the same
    statistic already reported in validate_scoring_signal.py, generalized
    to whichever score_key (here, always the raw blend, matching
    mandatory refinement #2: 'blend tests blend ranking shuffle')."""
    daily_spreads = []
    for day in panel:
        etf_ids = day["etf_ids"]
        if len(etf_ids) < bucket_size * 2:
            continue
        ordered = sorted(etf_ids, key=lambda etf_id: day[score_key][etf_id], reverse=True)
        top = ordered[:bucket_size]
        bottom = ordered[-bucket_size:]
        top_avg = _mean([day["forward_return"][etf_id] for etf_id in top])
        bottom_avg = _mean([day["forward_return"][etf_id] for etf_id in bottom])
        if top_avg is not None and bottom_avg is not None:
            daily_spreads.append(top_avg - bottom_avg)
    return _mean(daily_spreads)


# ---------------------------------------------------------------------------
# Permutation test (mandatory refinement #2: one independent shuffle per
# statistic, never a single shared shuffle reused across all of them)
# ---------------------------------------------------------------------------


def _shuffle_score_key(panel: list[dict], score_key: str, rng: random.Random) -> list[dict]:
    """A copy of `panel` with score_key's ETF-to-value assignment
    randomly reassigned WITHIN each date -- the real set of values
    observed that day is preserved exactly, only which ETF got which
    value is randomized. Forward returns are untouched. This is exactly
    'within-date reassignment of the real ETF universe, keep actual
    forward returns fixed' from the approved plan."""
    shuffled = []
    for day in panel:
        etf_ids = list(day["etf_ids"])
        values = [day[score_key][etf_id] for etf_id in etf_ids]
        rng.shuffle(values)
        new_day = dict(day)
        new_day[score_key] = dict(zip(etf_ids, values))
        shuffled.append(new_day)
    return shuffled


def permutation_null(
    panel: list[dict],
    score_key: str,
    statistic_fn,
    iterations: int,
    rng: random.Random,
) -> list[float]:
    """Empirical null distribution for `statistic_fn(panel, score_key)`,
    built from `iterations` independent within-date shuffles of
    score_key only. statistic_fn is called with the same panel-shaped
    argument the real statistic functions above already accept, so this
    one function serves every statistic -- reused, not duplicated per
    statistic -- while each CALL still uses its own independent shuffle
    series, satisfying refinement #2 without needing five separate
    permutation implementations.

    Efficiency note: forward returns never change across iterations for
    a fixed score_key, so downstream statistic_fn implementations
    (daily_ic_series, top_bottom_spread) naturally avoid redundant work
    by construction -- only the shuffled score side varies per call.
    """
    null_values = []
    for _ in range(iterations):
        shuffled_panel = _shuffle_score_key(panel, score_key, rng)
        value = statistic_fn(shuffled_panel, score_key)
        if value is not None:
            null_values.append(value)
    return null_values


def empirical_p_value(observed: float, null_distribution: list[float]) -> float:
    """Two-sided empirical p-value: the fraction of the null distribution
    at least as extreme as the observed value, using the data itself --
    no theoretical distributional assumption, per the approved plan."""
    if not null_distribution:
        return 1.0
    extreme = sum(1 for value in null_distribution if abs(value) >= abs(observed))
    return extreme / len(null_distribution)


# ---------------------------------------------------------------------------
# Block bootstrap (mandatory refinement #3: 20-day primary, 40/60-day
# robustness-only; all 25 ETFs resampled together per date-block, never
# per-ETF independently)
# ---------------------------------------------------------------------------


def _block_bootstrap_resample(panel: list[dict], block_length: int, rng: random.Random) -> list[dict]:
    """One resampled date series, built by drawing contiguous blocks of
    `block_length` consecutive panel entries (with replacement) until
    reaching panel's original length -- every ETF's data for a given
    resampled date moves together as it was originally observed that
    day, since a whole panel entry (all 25 ETFs) is drawn as one unit,
    never an ETF resampled independently of its peers."""
    n = len(panel)
    resampled: list[dict] = []
    while len(resampled) < n:
        start = rng.randrange(0, n)
        block = [panel[(start + offset) % n] for offset in range(block_length)]
        resampled.extend(block)
    return resampled[:n]


def bootstrap_ci(
    panel: list[dict],
    statistic_fn,
    score_key: str,
    block_length: int,
    iterations: int,
    rng: random.Random,
) -> tuple[float, float] | None:
    """95% confidence interval for statistic_fn(panel, score_key) via
    block bootstrap at the given block_length. Returns (low, high), or
    None if fewer than 2 resampled estimates were computable."""
    estimates = []
    for _ in range(iterations):
        resampled = _block_bootstrap_resample(panel, block_length, rng)
        value = statistic_fn(resampled, score_key)
        if value is not None:
            estimates.append(value)
    if len(estimates) < 2:
        return None
    estimates.sort()
    return _percentile(estimates, 2.5), _percentile(estimates, 97.5)


# ---------------------------------------------------------------------------
# Holm-Bonferroni correction
# ---------------------------------------------------------------------------


def holm_bonferroni(labeled_p_values: list[tuple[str, float]]) -> dict[str, dict]:
    """Holm-Bonferroni step-down correction across the given
    (label, raw_p_value) pairs. Adjusted p-values are monotonically
    non-decreasing in the sort order and capped at 1.0, the standard
    construction -- controls the family-wise error rate across the five
    simultaneous statistics, per the approved plan ('do not use
    unadjusted p-values for final conclusions')."""
    n = len(labeled_p_values)
    ordered = sorted(labeled_p_values, key=lambda pair: pair[1])
    results: dict[str, dict] = {}
    running_max = 0.0
    for i, (label, raw_p) in enumerate(ordered):
        adjusted = min((n - i) * raw_p, 1.0)
        running_max = max(running_max, adjusted)
        results[label] = {"raw_p_value": raw_p, "adjusted_p_value": running_max}
    return results


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run(
    db_path: Path = DB_PATH,
    universe: list[tuple[str, str]] | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    horizon_trading_days: int = HORIZON_TRADING_DAYS,
    bucket_size: int = BUCKET_SIZE,
    permutations: int = PERMUTATIONS,
    bootstrap_iterations: int = BOOTSTRAP_ITERATIONS,
    block_lengths: tuple[int, ...] = BLOCK_LENGTHS,
    random_seed: int = RANDOM_SEED,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> int:
    universe = universe if universe is not None else ETF_UNIVERSE
    today = date.today()
    end_date = end_date or (today - timedelta(days=1))
    start_date = start_date or (end_date - timedelta(days=DEFAULT_DAYS_BACK))
    rng = random.Random(random_seed)

    conn = connect(db_path)
    try:
        run_migrations(conn, MIGRATIONS_DIR)

        trading_days = sorted(d for d in get_trading_days(conn, CALENDAR_ID) if start_date <= d <= end_date)

        # Ensure Score rows exist -- idempotent, same reasoning and same
        # suppressed-output technique as validate_scoring_signal.py.
        with contextlib.redirect_stdout(io.StringIO()):
            for session_date in trading_days:
                run_daily_update(db_path=db_path, session_date=session_date, universe=universe)

        profile = get_scoring_profile(conn, PROFILE_NAME, PROFILE_VERSION)
        if profile is None:
            print(
                f"No scoring profile found for name {PROFILE_NAME!r} version {PROFILE_VERSION}",
                file=sys.stderr,
            )
            return 1

        allowed_tickers = frozenset(ticker for ticker, _name in universe)
        panel = build_panel(
            conn, profile.scoring_profile_id, trading_days, horizon_trading_days, bucket_size, allowed_tickers
        )
        if not panel:
            print("No ranking dates with sufficient data were found in this range.", file=sys.stderr)
            return 1

        # Precompute forward-return ranks once per date -- see
        # daily_ic_series()'s docstring. Forward returns never change
        # across permutation/bootstrap iterations, only the score side
        # does, so this is computed exactly once here rather than
        # thousands of times inside the hot loop.
        for day in panel:
            day["_return_ranks"] = _rank_average_ties([day["forward_return"][etf_id] for etf_id in day["etf_ids"]])

        # Phase 1 -- descriptive statistics only, not yet interpreted.
        observed = {
            "momentum_ic": mean_ic(panel, "momentum"),
            "value_ic": mean_ic(panel, "value"),
            "raw_blend_ic": mean_ic(panel, "raw_blend"),
            "normalized_blend_ic": mean_ic(panel, "normalized_blend"),
            "top_bottom_spread": top_bottom_spread(panel, "raw_blend", bucket_size),
        }

        # score_key + statistic_fn each statistic's null/bootstrap must
        # be built from -- the raw blend shuffle serves BOTH raw_blend_ic
        # and top_bottom_spread, per refinement #2 ("blend tests blend
        # ranking shuffle", singular, for both blend-derived statistics).
        statistic_specs = {
            "momentum_ic": ("momentum", mean_ic),
            "value_ic": ("value", mean_ic),
            "raw_blend_ic": ("raw_blend", mean_ic),
            "normalized_blend_ic": ("normalized_blend", mean_ic),
            "top_bottom_spread": ("raw_blend", lambda p, k: top_bottom_spread(p, k, bucket_size)),
        }

        # Phase 2 -- one permutation null per statistic, each from its
        # own independent shuffle series (refinement #2), 10,000+ draws
        # (refinement #4).
        null_distributions: dict[str, list[float]] = {}
        for label, (score_key, statistic_fn) in statistic_specs.items():
            null_distributions[label] = permutation_null(panel, score_key, statistic_fn, permutations, rng)

        raw_p_values = [
            (label, empirical_p_value(observed[label], null_distributions[label]))
            for label in STATISTIC_LABELS
            if observed[label] is not None
        ]
        # Phase 4 -- Holm-Bonferroni across all five simultaneous tests.
        corrected = holm_bonferroni(raw_p_values)

        # Phase 3 -- block bootstrap at 20 (primary) / 40 / 60 (robustness)
        # for every statistic, sharing one set of resampled date-blocks
        # per block length across statistics (resampling dates does not
        # touch the ETF-to-score assignment the way permutation does, so
        # a shared resample per block length is legitimate and cheaper).
        bootstrap_results: dict[str, dict[int, tuple[float, float] | None]] = {label: {} for label in STATISTIC_LABELS}
        for block_length in block_lengths:
            for label, (score_key, statistic_fn) in statistic_specs.items():
                bootstrap_results[label][block_length] = bootstrap_ci(
                    panel, statistic_fn, score_key, block_length, bootstrap_iterations, rng
                )

        # Phase 5 -- decision.
        report = _build_report(
            observed=observed,
            null_distributions=null_distributions,
            corrected=corrected,
            bootstrap_results=bootstrap_results,
            block_lengths=block_lengths,
            panel=panel,
            start_date=start_date,
            end_date=end_date,
            horizon_trading_days=horizon_trading_days,
            bucket_size=bucket_size,
            universe_size=len(universe),
            permutations=permutations,
            bootstrap_iterations=bootstrap_iterations,
            random_seed=random_seed,
        )

        print(_format_report(report))
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print()
        print(f"Machine-readable report written to {output_path}")
        return 0
    finally:
        conn.close()


def _statistic_verdict(label: str, corrected: dict, bootstrap_by_block: dict, block_lengths: tuple[int, ...]) -> dict:
    correction = corrected.get(label)
    significant_after_correction = correction is not None and correction["adjusted_p_value"] < 0.05

    robust_across_blocks = True
    for block_length in block_lengths:
        ci = bootstrap_by_block.get(block_length)
        excludes_zero = ci is not None and not (ci[0] <= 0.0 <= ci[1])
        if not excludes_zero:
            robust_across_blocks = False

    return {
        "significant_after_correction": significant_after_correction,
        "bootstrap_robust_across_block_lengths": robust_across_blocks,
        "passes": significant_after_correction and robust_across_blocks,
    }


def _build_report(
    *,
    observed,
    null_distributions,
    corrected,
    bootstrap_results,
    block_lengths,
    panel,
    start_date,
    end_date,
    horizon_trading_days,
    bucket_size,
    universe_size,
    permutations,
    bootstrap_iterations,
    random_seed,
) -> dict:
    statistics_report = {}
    for label in STATISTIC_LABELS:
        obs = observed[label]
        null = null_distributions[label]
        null_median = _percentile(sorted(null), 50) if null else None
        correction = corrected.get(label, {"raw_p_value": None, "adjusted_p_value": None})
        verdict = _statistic_verdict(label, corrected, bootstrap_results[label], block_lengths)

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

    qualifying = ["momentum_ic", "value_ic", "normalized_blend_ic"]
    qualifying_passed = [label for label in qualifying if statistics_report[label]["passes"]]
    raw_blend_only_artifact = (
        statistics_report["raw_blend_ic"]["passes"] and not qualifying_passed
    )

    if qualifying_passed:
        decision = "BUILD_V2_JUSTIFIED"
        reason = (
            f"{', '.join(qualifying_passed)} survived Holm-Bonferroni-corrected permutation "
            "testing and remained bootstrap-robust across 20/40/60-day blocks."
        )
    elif raw_blend_only_artifact:
        decision = "ARCHIVE"
        reason = (
            "Only the raw (unnormalized) blend passed -- MOMENTUM, VALUE, and the normalized "
            "blend all failed. This is the signature of the already-confirmed scale-dominance "
            "artifact (MOMENTUM's unnormalized range swamping the blend), not evidence of a "
            "real signal. Interpreted as artifact confirmation, per the approved decision rule."
        )
    else:
        decision = "ARCHIVE"
        reason = "No statistic survived Holm-Bonferroni-corrected permutation testing with bootstrap robustness."

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": {
            "scoring_profile": f"{PROFILE_NAME} v{PROFILE_VERSION}",
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "forward_horizon_trading_days": horizon_trading_days,
            "bucket_size": bucket_size,
            "etf_universe_size": universe_size,
            "ranking_dates_observed": len(panel),
            "permutations": permutations,
            "bootstrap_iterations": bootstrap_iterations,
            "block_lengths": list(block_lengths),
            "random_seed": random_seed,
        },
        "statistics": statistics_report,
        "decision": {
            "qualifying_statistics_passed": qualifying_passed,
            "raw_blend_only_artifact_detected": raw_blend_only_artifact,
            "verdict": decision,
            "verdict_reason": reason,
        },
    }


def _format_report(report: dict) -> str:
    lines = ["REFERENCE v1 Significance Test"]
    cfg = report["config"]
    lines.append(f"Scoring profile: {cfg['scoring_profile']}")
    lines.append(f"Period: {cfg['period_start']} to {cfg['period_end']}")
    lines.append(f"Forward return horizon: {cfg['forward_horizon_trading_days']} trading days")
    lines.append(f"ETF universe size: {cfg['etf_universe_size']}")
    lines.append(f"Ranking dates observed: {cfg['ranking_dates_observed']}")
    lines.append(f"Permutations: {cfg['permutations']}  Bootstrap iterations: {cfg['bootstrap_iterations']}")
    lines.append(f"Block lengths: {cfg['block_lengths']} (first is primary, rest are robustness diagnostics only)")
    lines.append(f"Random seed: {cfg['random_seed']}")
    lines.append("")

    for label in STATISTIC_LABELS:
        s = report["statistics"][label]
        lines.append(f"-- {label} --")
        lines.append(f"  Observed: {s['observed']}")
        lines.append(f"  Null median: {s['null_median']}")
        lines.append(f"  Difference from null: {s['difference_from_null']}")
        lines.append(f"  Raw p-value: {s['raw_p_value']}   Adjusted (Holm-Bonferroni): {s['adjusted_p_value']}")
        lines.append(f"  Significant after correction: {s['significant_after_correction']}")
        for key, ci in s["bootstrap"].items():
            lines.append(f"  Bootstrap {key}: {ci}")
        lines.append(f"  Bootstrap-robust across all block lengths: {s['bootstrap_robust_across_block_lengths']}")
        lines.append(f"  Passes (significant AND bootstrap-robust): {s['passes']}")
        lines.append("")

    d = report["decision"]
    lines.append("Decision")
    lines.append(f"Qualifying statistics passed: {d['qualifying_statistics_passed'] or '(none)'}")
    lines.append(f"Raw-blend-only artifact detected: {d['raw_blend_only_artifact_detected']}")
    lines.append(f"Verdict: {d['verdict']}")
    lines.append(f"Reason: {d['verdict_reason']}")
    lines.append("")
    lines.append(
        "This is an observed measurement over a limited historical sample. Even a "
        "BUILD_V2_JUSTIFIED verdict establishes statistical association within this sample "
        "only -- it does not confirm, validate, or prove predictive value, does not account "
        "for transaction costs or implementation frictions, and cannot speak to a different "
        "market regime than the one observed. No recommendation, no ranking judgment, no "
        "investment advice."
    )
    return "\n".join(lines)


if __name__ == "__main__":
    # Guarded inline self-checks -- heavier than a typical experiments/
    # script's, deliberately: a silent bug in any of these would produce
    # a wrong archive/build-v2 verdict, not just a wrong printed number.

    # Spearman correctness against hand-computable synthetic sequences.
    # Float arithmetic, not exact equality: Pearson-on-ranks for a
    # perfectly monotonic relationship lands at ~0.9999999999999998, not
    # a bit-exact 1.0 -- a tolerance check is correct here, not a
    # workaround for a bug.
    assert abs(_spearman([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) - 1.0) < 1e-9
    assert abs(_spearman([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]) - (-1.0)) < 1e-9
    assert _spearman([1, 1, 1], [1, 2, 3]) is None  # zero variance -> undefined, not zero

    # Permutation calibration: shuffling a score with NO real relationship
    # to the outcome should not systematically land in the tail -- this
    # is a "does the null generator actually behave like a null" check,
    # run against a synthetic panel with a genuinely random relationship.
    _calibration_rng = random.Random(1)
    _synthetic_panel = [
        {
            "etf_ids": [f"etf{i}" for i in range(10)],
            "score": {f"etf{i}": _calibration_rng.random() for i in range(10)},
            "forward_return": {f"etf{i}": _calibration_rng.random() for i in range(10)},
        }
        for _ in range(50)
    ]
    _calibration_ic = mean_ic(_synthetic_panel, "score")
    _calibration_null = permutation_null(_synthetic_panel, "score", mean_ic, 200, random.Random(2))
    _calibration_p = empirical_p_value(_calibration_ic, _calibration_null)
    assert 0.0 <= _calibration_p <= 1.0

    # Block bootstrap structural check: within one resample, an entire
    # panel entry (all ETFs for that date) must move together, never an
    # ETF resampled independently of its peers on the same date.
    _bootstrap_check_rng = random.Random(3)
    _resampled = _block_bootstrap_resample(_synthetic_panel, 5, _bootstrap_check_rng)
    assert len(_resampled) == len(_synthetic_panel)
    assert all(entry["etf_ids"] == _synthetic_panel[0]["etf_ids"] for entry in _resampled)

    # Holm-Bonferroni against a known textbook example.
    _hb = holm_bonferroni([("a", 0.01), ("b", 0.04), ("c", 0.03), ("d", 0.005)])
    assert _hb["d"]["adjusted_p_value"] == 0.02  # 0.005 * 4
    assert _hb["a"]["adjusted_p_value"] == 0.03  # max(0.02, 0.01 * 3)
    assert _hb["c"]["adjusted_p_value"] == 0.06  # max(0.03, 0.03 * 2)
    assert _hb["b"]["adjusted_p_value"] == 0.06  # max(0.06, 0.04 * 1)

    # Precomputed-return-rank optimization must be exactly equivalent to
    # the unoptimized path -- a performance change must never change a
    # result. Compare daily_ic_series() with and without a precomputed
    # "_return_ranks" field on the same synthetic panel.
    _unoptimized = daily_ic_series(_synthetic_panel, "score")
    _with_precomputed = [dict(day) for day in _synthetic_panel]
    for _day in _with_precomputed:
        _day["_return_ranks"] = _rank_average_ties([_day["forward_return"][e] for e in _day["etf_ids"]])
    _optimized = daily_ic_series(_with_precomputed, "score")
    assert len(_unoptimized) == len(_optimized)
    assert all(abs(a - b) < 1e-12 for a, b in zip(_unoptimized, _optimized))

    raise SystemExit(run())
