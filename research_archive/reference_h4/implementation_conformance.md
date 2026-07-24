# `reference_h4` — Phase 5: Implementation Conformance Note

**Date:** 2026-07-25
**Author:** Claude Sonnet 5 (this session), self-review only (Level 1).
**Implementation artifact:** `experiments/validate_h4_kurtosis.py`.

Per `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 2, Phase 5: this
confirms, element by element against `methodology.md`, that the
implementation matches the frozen specification exactly and makes no
design decision of its own.

| `methodology.md` element | Implementation |
|---|---|
| §1 Universe (25 named tickers) | `UNIVERSE` tuple, verbatim, same order |
| §2 Dataset (frozen snapshot) | Reads `PriceBar`/`ETF` via `core.market_data.persistence.repository`, the live tables the frozen `dataset_hashes/` snapshot was itself exported from — no other data source touched |
| §3 Return definition (`ln(close_t/close_{t-1})`, session_date order) | `_log_returns` — `get_price_bars` already returns rows ordered by `session_date`; no reordering, filtering, or adjustment applied |
| §4 Statistic (uncorrected sample excess kurtosis) | `_sample_excess_kurtosis` — plain `m4/m2^2 - 3`, no bias correction, matches the exact formula frozen in §4 |
| §5 Cross-sectional aggregation (median) | `_median` over the 25 per-ETF point estimates |
| §6 Significance procedure (i.i.d. bootstrap, resample-with-replacement across the 25 ETFs, 10,000 iterations, seed 20260725, 2.5/97.5 percentile CI) | `_bootstrap_median_ci` — `random.Random(20260725)`, `BOOTSTRAP_ITERATIONS = 10_000`, resamples the 25 point estimates (not the underlying return series) |
| §7 Acceptance criterion | Not evaluated in this script — deliberately left for the Validation→Decision gate (Phase 6), so no PASS/FAIL judgment is embedded in the implementation itself |

No parameter, threshold, or design choice appears in
`experiments/validate_h4_kurtosis.py` that is not already named in
`methodology.md`. The script exposes `run(db_path)` per
`core.governance.reproduction_runner`'s calling convention (SS F.2), is
read-only against its database argument, and was smoke-tested against
`experiments_etf_universe.db` in this session (not yet the official
Validation-phase run — that happens in Phase 6 against the frozen
snapshot, per Standard §2 Phase 6: "the only phase... where outcome data
may be read").

## Approval state

Level 1 (self-review) for this conformance note, per Standard §2 Phase 5's
stated minimum ("Standard code review (Level 1 minimum)").
