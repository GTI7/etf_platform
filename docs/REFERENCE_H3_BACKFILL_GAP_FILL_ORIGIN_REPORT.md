# REFERENCE H3 — `backfill-gap-fill` Origin Report

**Status: historical forensic investigation only. No code, database
row, migration, or archive file has been modified as part of producing
this report.** This document answers the one open question the
[remediation plan](REFERENCE_H3_DATABASE_REMEDIATION_PLAN.md) (Section
5) left as a hard precondition on deletion: where did the 50
`source='backfill-gap-fill'` `PriceBar` rows come from, and can the
platform produce them again. It recommends nothing about the database
and performs no remediation.

## 1. Executive summary

The string `backfill-gap-fill` does not appear anywhere in this
repository's Git history — not in the current tree, not in any of the
38 commits ever made on any branch, not in any dangling or unreachable
object. It was not produced by a script, a migration, or an
experiment that was ever committed. No `IngestionRun` row — the
table every current pipeline component (`price_ingestion:*`,
`indicator:*`, `scoring:*`) uses to log its own execution — references
anything resembling a backfill or gap-fill run either. Whatever
process inserted these 50 rows did not go through the codebase's own
run-logging convention, which every legitimate pipeline component
does.

Direct inspection of the live database (`experiments_etf_universe.db`,
gitignored, not version-controlled) does, however, reconstruct the
**mechanism** with high confidence: all 50 rows carry an
`open = high = low = close` value that is byte-for-byte identical to
the prior trading day's real (`yahoo_finance`-sourced) close for that
same ETF — a 50/50 match, zero exceptions. Both anomalous dates
(2026-06-19 and 2026-07-03) are **Fridays** — ordinary business days on
a naive Monday–Friday calendar, but NYSE holidays absent from
`TradingSession`. The rows were inserted at 2026-07-17T21:32:29–30
UTC, in a ~17-second window sandwiched between a bulk historical
Yahoo Finance backfill batch (21:32:16 UTC) and the moment the
previously-failing `indicator:SMA:v1:*` pipeline runs began succeeding
again (21:32:33 UTC) for every one of the 25 ETFs in the universe.

**Conclusion: this is very likely the byte-for-byte signature of an
ad hoc, uncommitted, weekday-only (not trading-calendar-aware)
forward-fill action** — most plausibly a manual script or interactive
session run once by the repository's sole operator to silence the SMA
indicator's "Missing PriceBar" failures, using "every weekday has a
bar" as the (incorrect) invariant instead of "every `is_trading_day=1`
session has a bar." It was never committed to source control, so it
cannot be re-identified as a named script — only reconstructed from
its data fingerprint.

**Can it recur? UNKNOWN, leaning NO under current code, but not
provably closed** — see Section 6. No code path in the present
codebase produces this pattern, but because the origin was never
captured as a committed artifact, its absence from the codebase cannot
be distinguished with certainty from "the same manual action simply
hasn't been repeated."

## 2. Evidence reviewed

- Full commit history of `etf_platform` (38 commits, single branch
  `master`, single author, one remote `origin`), via `git log --all`,
  `git log --all -S<pattern>`, `git reflog show --all`, and
  `git fsck --full --unreachable --dangling`.
- Every blob ever committed to the repository (162 total, enumerated
  via `git rev-list --objects --all`), individually scanned for
  `backfill-gap-fill`, `backfill_gap_fill`, `gap-fill`, `gap_fill`, and
  `gapfill`.
- The current working tree, including untracked and gitignored paths.
- The live SQLite database `experiments_etf_universe.db` (gitignored,
  never tracked): `PriceBar`, `IngestionRun`, and `TradingSession`
  tables, specifically the 50 flagged rows, their `ingested_at`
  timestamps, and their relationship in time to every other
  `IngestionRun` row logged within the same minute.
- Current source of every code path capable of writing a `PriceBar`
  row: `core/market_data/ingestion/price_ingestion.py`,
  `experiments/backfill_price_history.py`,
  `core/market_data/persistence/repository.py`.
- `git log --follow` for both files above, to confirm whether either
  ever contained gap-filling logic that was later removed.
- Leftover `__pycache__/*.pyc` filenames across the whole checkout, as
  a check for a since-deleted script that was at least once executed
  from a `.py` file.
- `git stash list`, `git status --ignored`, and the `migrations/`
  directory, as a check for a stash, backup file, or schema migration
  that could account for the rows.

## 3. Git history

- **First appearance in Git: never.** `git log --all -S"backfill-gap-fill"`
  (and every underscore/hyphen variant) returns zero commits, on any
  ref, including `origin/master`.
- **Last appearance in Git: never** — same result; there is nothing to
  date a removal for, because it was never added.
- **Dangling/unreachable objects: none.** `git fsck --full
  --unreachable --dangling` returns nothing, so there is no orphaned
  commit or blob (e.g. from an amended or rebased-away commit) hiding
  the string outside of reachable history.
- **Blob-level scan: 162/162 clean.** Every blob ever created in this
  repository's history (not just the tip of each file's history, but
  every historical version of every file) was individually
  decompressed and grepped; none contain the string.
- **Only two files anywhere on disk currently reference the string**,
  and both are the analysis documents already produced by the prior
  investigation (`REFERENCE_H3_GATE2_DISCREPANCY_ANALYSIS.md`,
  `REFERENCE_H3_DATABASE_REMEDIATION_PLAN.md`) — both untracked at the
  time of this report, both written *about* the anomaly, not sources
  of it.

This rules out, with high confidence: an older ingestion script (would
have left a commit), a migration (`migrations/*.sql` contains no
reference and the schema itself has no default carrying this value),
a committed experiment (`experiments/` history was fully enumerated),
and a documented one-off maintenance script (no such script exists in
any commit). It cannot rule out a script that was written, run once,
and deleted before ever being `git add`ed — Git has no record of a
file that was never staged.

## 4. Code history

- `experiments/backfill_price_history.py` has exactly **one** commit
  in its entire history (`cae13e7`, "feat(experiments): add price
  backfill and scoring signal research tooling"). It has never been
  modified since. Its only write path is
  `insert_price_bar(..., source=provider.name, ...)`, where `provider`
  is `YahooFinanceProvider` — meaning it can only ever write
  `source='yahoo_finance'`. It contains no forward-fill, no flat-OHLC
  construction, and no weekday-only date iteration; it inserts exactly
  what `DataProvider.fetch_daily_bars()` returns for the requested
  range, and Yahoo Finance does not return bars for exchange holidays.
- `core/market_data/ingestion/price_ingestion.py` has two commits
  (`07c075e` initial add, `9c45ec6` CLI visibility). Its only write
  path is likewise `source=provider.name`, and it is further gated by
  `is_trading_day()` per the remediation plan's own finding — it
  will not even attempt to ingest a non-trading date.
- Two commits from the same evening are thematically adjacent but
  **not the source of the `PriceBar` rows**: `cebd5b0` ("fix(analytics):
  skip SMA/RSI computation on non-trading days") and `67d9e90` ("fix
  MAX_DRAWDOWN…") added an `is_trading_day()` guard to
  `core/analytics/indicator_calculation.py` so that `IndicatorValue`
  rows stop being computed for non-trading dates. This fixes a
  **downstream** duplication bug in the indicator layer (discovered
  independently, "running the real daily experiment runner on a
  Saturday") and touches no `PriceBar` write path at all. It is easy to
  conflate with this incident because it fixes the same *class* of
  defect (non-trading days not excluded) one layer up the pipeline,
  but it neither produced nor removed the 50 rows.
- No `.pyc` file in any `__pycache__/` directory across the checkout
  corresponds to a `.py` file that no longer exists — every compiled
  module name matches a file present today. This is not conclusive
  (caches can be cleared), but it found no trace of a deleted script.
- `git stash list` is empty; `git status --ignored` lists only
  expected build/cache artifacts and the live database file — nothing
  resembling a leftover one-off script.

**Conclusion: the current and all past committed code is exonerated.**
No version of any script this repository has ever tracked can produce
a flat-OHLC, zero-volume, `source='backfill-gap-fill'` row.

## 5. Origin timeline (reconstructed from database evidence, all times UTC)

| Time | Event | Source |
|---|---|---|
| 21:31:40.687–.887 | `price_ingestion:<TICKER>` runs succeed for each of the 25 ETFs, inserting only that day's (2026-07-17) bar | `IngestionRun` |
| 21:31:40.890 | `indicator:SMA:v1:VT` **fails**: `Missing PriceBar for etf_id=... on trading day(s): [2026-06-18, 2026-06-22 … 2026-07-16]` — a real, ~19-trading-day gap per ETF. Note this list correctly excludes 2026-06-19 and 2026-07-03 already — the failure's own missing-date logic already knows those two are not trading days | `IngestionRun.error_message` |
| 21:32:16.514 | A batch of `source='yahoo_finance'` `PriceBar` rows appears for every genuinely missing trading day across the affected range, for VT and (by the same pattern) presumably the other 24 ETFs — consistent with a manual run of `experiments/backfill_price_history.py`, which was not yet committed to Git at this point | `PriceBar.ingested_at` |
| **21:32:29.961 – 21:32:30.017** | **The 50 `source='backfill-gap-fill'` rows are inserted** — exactly 2 per ETF × 25 ETFs, for 2026-06-19 and 2026-07-03 only. Every row's OHLC is identical to that ETF's immediately preceding real trading-day close (50/50 verified, zero mismatches); volume is 0 in all 50 | `PriceBar.ingested_at`, `PriceBar.close_amount` cross-check |
| 21:32:33.919 onward | `indicator:SMA:v1:*`, `indicator:RSI:v1:*`, and `scoring:REFERENCE:v1:*` all begin succeeding, for all 25 ETFs, within the same second-scale window | `IngestionRun` |
| 22:11:06 (00:11:06+02:00 local) | Commit `cae13e7` adds `experiments/backfill_price_history.py` to Git — **~39 minutes after** the yahoo_finance batch it is presumed to have produced, and **~39 minutes after** the backfill-gap-fill rows appeared. The script was evidently written/run before this commit, consistent with a same-session workflow of "write script → run it → fix what's still broken → commit" | Git commit metadata |
| 22:20:19 / 22:22:55 | Commits `cebd5b0` / `67d9e90` add the `is_trading_day()` guard to the indicator layer — a related but distinct fix, addressing a different manifestation (duplicate `IndicatorValue` rows) discovered separately | Git commit metadata |

No `IngestionRun` row exists with a `started_at`/`completed_at` bracketing 21:32:29–30, and no `pipeline_name` in the entire table (101 distinct values, all prefixed `price_ingestion:`, `indicator:`, or `scoring:`) mentions backfill or gap-fill. Every legitimate pipeline component in this codebase logs an `IngestionRun` row; whatever inserted these 50 rows did not.

**Interpretation.** The evidence is most consistent with the operator
manually unblocking the SMA failure in real time: having just bulk-
backfilled real trading history (fixing the *listed* missing dates),
the SMA run was still failing (or was about to be re-tried) against a
naive "no gap in the business-day sequence" expectation. A short,
un-versioned action — plausibly a few lines typed into a Python REPL
or a throwaway script never staged in Git — iterated the two
Mon–Fri dates still lacking a row in each ETF's June–July date range
(2026-06-19 and 2026-07-03, both Fridays) and forward-filled a flat
bar from the prior close, without checking `TradingSession`. This
would explain every observed property at once: the exact timing
between the real backfill and the SMA runs turning green, the
weekday-not-trading-day selection of exactly these two dates, the
carried-forward close values, the zero volume (nothing traded), and
the complete absence of any `IngestionRun` log entry or Git trace.

This reconstruction is **inference from a strong, consistent data
fingerprint, not a recovered script**. No file, commit, stash, or log
line naming this action was found, and none can be produced after the
fact — the action, if manual and unstaged as reconstructed, left no
artifact capable of confirming its exact form.

## 6. Can it recur?

**UNKNOWN, leaning NO, not provably closed.**

Evidence for NO / low risk:
- No committed script, past or present, contains logic that produces
  this pattern (Section 4).
- Both current `PriceBar`-writing paths (`price_ingestion.py`,
  `backfill_price_history.py`) are gated to real provider data only
  and, in the ingestion case, an explicit `is_trading_day()` check.
- No `IngestionRun`-logged pipeline component in the current codebase
  has ever produced a `backfill-gap-fill`-tagged row, across the
  entire run history in the database.
- The related indicator-layer defect class (non-trading days not
  excluded) was independently found and fixed the same evening
  (`cebd5b0`, `67d9e90`), suggesting the operator's general awareness
  of this failure mode increased shortly after this incident.

Evidence against a confident NO:
- The likely mechanism (Section 5) is a manual, un-versioned action,
  not a code defect. Reviewing "the codebase" cannot exhaustively rule
  out a repeat of a manual action that, by construction, leaves no
  code to review. If the operator hits a similar SMA/RSI "missing
  bars" failure again in the future and reaches for the same kind of
  quick unblock, nothing in the current codebase would prevent it or
  detect it before the fact.
- There is no committed regression test asserting that a `PriceBar`
  row can never exist for a non-`is_trading_day=1` date — only that
  the *indicator layer* now skips non-trading dates for computation
  (`cebd5b0`/`67d9e90`), which is a downstream mitigation, not a
  constraint on `PriceBar` writes themselves. Nothing currently stops
  a future manual `INSERT` (or ad hoc script) from repeating exactly
  this pattern.
- The discrepancy analysis's own Section 9 / the remediation plan's
  Section 6, point 6 already flag this same gap and recommend a
  recurrence check as part of post-remediation validation — this
  report's finding is consistent with, and reinforces, that existing
  recommendation rather than closing it.

## 7. Residual risks

- **No structural guard exists against a repeat.** The invariant "a
  `PriceBar` row implies `is_trading_day=1` for that date" is enforced
  today only by the *shape* of the code paths that happen to write
  `PriceBar` rows (both gate on real provider data), not by any
  database constraint, trigger, or application-level assertion at
  write time. A future ad hoc write — through a REPL, a notebook, or a
  new one-off script — has nothing stopping it from reintroducing the
  same pattern.
- **The reconstructed mechanism is inference, not confirmation.** No
  script, stash, or log entry was recovered; Section 5's timeline is
  the strongest explanation the available evidence supports, not a
  proven one. If a different, currently-unconsidered process was
  responsible, this report would not detect it.
- **`IngestionRun` completeness is only as good as pipeline
  discipline.** The absence of a logged run for this incident is
  itself evidence of how easy it is to write directly to `PriceBar`
  without going through any accountable pipeline path — a structural
  gap independent of this specific incident.
- **The database is not version-controlled**, so no historical
  snapshot exists to compare against; all timeline reconstruction here
  relies on the single live copy of `experiments_etf_universe.db` and
  its own internal timestamps, which are self-reported by the writing
  process and not independently corroborated by an external log.

## 8. Recommendation

This report recommends no database action, consistent with its scope.
It surfaces one point relevant to the remediation plan's existing
precondition (Section 5 there): the origin cannot be conclusively
identified or ruled out as still-active, because the most likely
mechanism is a manual, un-versioned action rather than a discoverable
piece of code. Per the remediation plan's own Section 5 mitigation,
this means remediation may still proceed, but Gate 2's
re-verification **must** include the recurrence check already
specified in the remediation plan (Section 6, point 6) rather than
treating the origin question as closed. Consider, as a separate,
future-authorized change (not part of this report and not proposed
here as an action to take now): a lightweight write-time or
periodic-audit guard tying `PriceBar` inserts to `TradingSession`
directly, so that a future recurrence — manual or automated — is
caught immediately rather than requiring another ad hoc forensic
investigation like this one.

---

**STOP — this is a historical forensic investigation only. No
remediation, deletion, migration, or documentation update has been
performed. No fix is proposed or authorized by this report.**
