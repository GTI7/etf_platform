# v0.6.0 — Write-side Pipeline Composition

## Highlights

- Added an orchestration layer combining the existing write-side stages
  into one entry point: `run_write_pipeline()`.
- Full pipeline execution for one ETF and one trading session:
  `ingest → SMA → RSI → score`.
- Backfill-safe ingestion guard using a direct `PriceBar` existence check
  — correctly handles out-of-order/backfill sessions, unlike a
  watermark-comparison guard (rejected during design review specifically
  because it cannot distinguish an already-ingested session from an
  earlier, never-ingested backfill session).
- Failure isolation preserved through the existing transaction
  boundaries: each stage still commits independently via `run_pipeline`,
  so a later stage's failure never rolls back an earlier stage's already
  -committed work, and every stage remains safe to retry.

## Technical changes

- New `core/analytics/write_pipeline.py` — `run_write_pipeline()`.
- New `WritePipelineResult` dataclass (frozen, slotted) — surfaces the
  four run ids the composed stages already produce; nothing new is
  persisted.
- New end-to-end orchestration tests in `tests/test_write_pipeline.py`
  (9 tests): successful end-to-end execution, ingestion/SMA/RSI/scoring
  failure isolation, the `PriceBar` existence-check guard, repeated
  execution, idempotency across repeated calls, a backfill regression
  test, and partial-failure-then-retry recovery.

## Compatibility

- No migrations.
- No schema changes.
- No repository changes.
- No scoring changes.
- No public API changes except the new orchestration entry point
  (`run_write_pipeline()` / `WritePipelineResult`).

## Quality

- 154/154 tests passing.
- `write_pipeline.py` — 100% coverage (25/25 statements).

## Explicitly not in this release

- Dynamic indicator dispatch (SMA/RSI are still called explicitly, by
  name — two concrete indicators remain judged-insufficient evidence for
  a dispatch mechanism).
- `ProviderRegistry` activation (`run_write_pipeline()` takes a
  `DataProvider` directly, exactly as `ingest_daily_prices()` already did).
- API/CLI.
- Portfolio support.
- Universe support.

See `docs/V0_6_0_DESIGN_WRITE_PIPELINE_COMPOSITION.md` for the full
design record and `docs/BASELINE_STATUS.md` for the updated project-wide
baseline this release folds into.
