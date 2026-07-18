# REFERENCE H3 — Database Remediation Plan

**Status: planning and governance review only. No code, database row,
migration, archive file, or governance document has been modified as
part of this plan.** This document answers: given the confirmed root
cause in
[`docs/REFERENCE_H3_GATE2_DISCREPANCY_ANALYSIS.md`](REFERENCE_H3_GATE2_DISCREPANCY_ANALYSIS.md),
what is the safest way to remediate the database, what must be
re-verified afterward, and what does Gate 2 require before it can move
off HOLD. It does not perform any of that work.

## 1. Executive summary

The discrepancy analysis identified 50 invalid `PriceBar` rows (25
ETFs × 2 dates: 2026-06-19 Juneteenth, 2026-07-03 observed
Independence Day) tagged `source='backfill-gap-fill'` — a value no
current ingestion path produces. These rows are flat-OHLC,
zero-volume, sit on non-trading days per the `TradingSession`
calendar, and were inserted 2026-07-17, a full day before the H3
extension ran. **The H3 extension itself is exonerated**; it inserted
only valid Yahoo Finance bars into the pre-existing window.

This plan evaluates six candidate remediation strategies (Section 3),
recommends a **scoped, predicate-based, export-then-delete data
cleanup** carried out as a reviewed, versioned script — not an
in-session ad hoc `DELETE` — with mandatory pre-deletion evidence
export, a two-directional post-fix verification, and a genuinely
independent Gate 2 reviewer before Gate 2 can leave HOLD (Section 8).
It explicitly recommends **against** full re-ingestion, against
leaving the rows in place with query-time filtering as a permanent
fix, and against unbounded/unreviewed manual deletion.

No remediation has been executed. No database connection was opened
by this session.

## 2. Root cause recap

(Full detail in
[`REFERENCE_H3_GATE2_DISCREPANCY_ANALYSIS.md`](REFERENCE_H3_GATE2_DISCREPANCY_ANALYSIS.md);
summarized here for a self-contained remediation record.)

| Fact | Value |
|---|---|
| Invalid row count | 50 (25 ETFs × 2 dates) |
| Dates | 2026-06-19 (Juneteenth), 2026-07-03 (observed Independence Day) |
| `source` tag | `backfill-gap-fill` — absent from current codebase |
| Row shape | `open = high = low = close` (flat), `volume = 0` |
| Calendar status | Both dates correctly absent from `TradingSession` (`is_trading_day=1`) — genuine NYSE closures |
| Insertion time | 2026-07-17T21:32:29–30 UTC — **before** the H3 extension batch (2026-07-18T22:24:05–13 UTC) and before the pre-extension inventory baseline was even taken |
| Relationship to H3 extension | None. The extension's own batch (49,300 rows, `source='yahoo_finance'`) is clean |
| Origin of the 50 rows | **Unidentified.** Not produced by `ingest_daily_prices` (gates on `is_trading_day()`) or `backfill_price_history.run` (tags `source='yahoo_finance'`) as they exist in the current codebase |

The general invariant these rows violate is already enforced
elsewhere in the platform: a `PriceBar` row should exist for a given
`(etf_id, session_date)` if and only if that date has a matching
`is_trading_day=1` `TradingSession` row for the relevant calendar. The
investigation's own scope check (an unrestricted join across every
`PriceBar` row against every ticker) found **no other anomalous date**
anywhere in the table — the 50 rows are the complete set, not a
sample.

The unidentified origin is the one open factual question this plan
cannot close and treats as a hard precondition on remediation
(Section 5).

## 3. Remediation options

Eight approaches were considered. Each is evaluated against: does it
fix the data, is it reversible, is it auditable, is it reproducible by
a third party, and what risk does it carry.

### A. Do nothing — accept and document as a known limitation

Leave the 50 rows in place; add a caveat to the archive noting the
surplus. **Rejected.** The rows are not a benign approximation — they
are synthetic, zero-information data on dates that should have zero
rows. Every future BOTZ-anchored (or any-ETF-anchored) bar count
built on this universe inherits a silent +2 inflation. Doing nothing
does not "preserve" the evidence, it lets a known-wrong number keep
propagating into work that has not happened yet.

### B. Query-time filtering — exclude at read time, leave storage untouched

Add a filter (`source != 'backfill-gap-fill'`, or the general
`is_trading_day=1`-join predicate) to every read path instead of
touching the stored rows. **Rejected as the primary fix**, viable only
as a defense-in-depth supplement. It is non-destructive and fully
reversible (nothing to reverse), but it requires every current and
future query, script, and ad hoc analysis to remember to apply the
filter — a single omission (exactly the kind of omission that let the
original "0 missing dates" check pass silently) reintroduces the bug.
It also does not fix `data_inventory`-style raw count exports unless
those are filtered too, so the evidence discrepancy persists even
after the "fix."

### C. Targeted deletion — `DELETE ... WHERE source = 'backfill-gap-fill'`

The narrowest possible fix: delete exactly the 50 rows the
investigation already enumerated by their `source` tag. **Viable but
inferior to Option D.** It matches today's findings exactly, but it
hard-codes *this incident's* signature (`source='backfill-gap-fill'`)
as the correctness criterion rather than the durable invariant the
platform actually relies on. If the unidentified origin process
resurfaces under a different `source` string, this delete criterion
would not catch it, and a future re-run of Gate 2 verification would
have no reason to look for it unless the verification methodology
itself also changes (Section 8).

### D. Predicate-based deletion — general invariant, not a tag match

`DELETE` any `PriceBar` row whose `(etf_id, session_date)` has no
matching `is_trading_day=1` `TradingSession` row for that ETF's
calendar — regardless of `source`. **Preferred deletion criterion.**
This encodes the actual data-quality invariant (a price bar cannot
exist for a day the exchange was closed) rather than one incident's
symptom. It is provably a superset-safe match of Option C given the
investigation's own finding that the 50 `backfill-gap-fill` rows are
the *only* rows violating this invariant anywhere in the table — so in
practice it deletes the identical 50 rows today, while remaining
correct if a differently-tagged violation is ever introduced later.

### E. Soft-delete / quarantine — flag rows instead of removing them

Add an `is_invalid` column (or move rows to a quarantine table)
instead of deleting. Maximizes reversibility and keeps a live forensic
trail in the primary schema. **Rejected as disproportionate.** For a
closed, fully-enumerated, 50-row, already-understood defect, a schema
change is more invasive than the problem requires, and it leaves
invalid rows inside tables that every other query touches, recreating
Option B's "everyone must remember to filter" risk permanently. The
forensic-trail benefit is fully achievable via Option F's export step
without a schema change.

### F. Export-then-delete — Option D's predicate, preceded by a mandatory evidence export

Before deleting, dump the exact matched rows (full column contents,
not just row count) to a permanent, timestamped archive file under
`research_archive/reference_h3/`. Then execute the Option D delete
inside a transaction, as a reviewed, versioned, one-off script (not an
interactive/ad hoc statement typed into a session). **Recommended —
see Section 4.**

### G. Re-ingest/replace the affected dates from the live provider

Treat this as a "backfill gap" and re-fetch 2026-06-19 and 2026-07-03
from Yahoo Finance to replace the bad rows with "corrected" ones.
**Rejected — inapplicable, not merely inferior.** These are confirmed
non-trading days; the correct number of `PriceBar` rows for them is
**zero**, not a corrected one. Re-ingesting would fetch nothing (a
live provider has no bar for a closed exchange) or, worse, could
silently accept whatever a provider returns for a closed day without
the same scrutiny this incident already required. This option is
listed only to rule it out explicitly, since "backfill-gap-fill"
naming invites the assumption that replacement, not removal, is the
fix.

### H. Full database rebuild — drop and re-ingest all ~63,826 rows from scratch

**Rejected.** Disproportionate to a fully-diagnosed, 50-row, bounded
defect. Re-fetching the entire universe from a live external API
introduces new risk (provider drift between the original ingestion
date and a rebuild date, rate limits, a new opportunity for a
different silent defect) that the current evidence gives no reason to
accept. The 61,850 non-anomalous rows already have three independent
lines of evidence supporting their validity (the discrepancy
analysis's own timestamp/count reconciliation, the H3 extension's
clean batch, and the independent-review record's reproduced counts) —
discarding them gains nothing.

### Comparison summary

| Option | Fixes data | Reversible | Auditable | Reproducible | Risk |
|---|---|---|---|---|---|
| A. Do nothing | No | — | Low (relies on a caveat being read) | — | Silent propagation into future H3 work |
| B. Query-time filter | No (masks) | Full | Low (implicit in every query) | Low — depends on every caller | Recurrence via any unfiltered query |
| C. Targeted delete (tag match) | Yes, today | Only via re-insert from backup | Medium | Medium — criterion is incident-specific | Misses a future differently-tagged recurrence |
| D. Predicate delete (invariant) | Yes | Only via re-insert from backup | Medium | High — criterion is durable | Low, if origin unconfirmed (Section 5) |
| E. Soft-delete/quarantine | Yes (logically) | Full | High | Medium | Schema churn disproportionate to scope |
| **F. Export-then-delete (D + backup)** | **Yes** | **Full (export is the reversal path)** | **High** | **High** | **Lowest of the fix-the-data options** |
| G. Re-ingest affected dates | N/A — wrong model | — | — | — | Category error; do not use |
| H. Full rebuild | Yes, but overkill | Full | High effort cost | High effort cost | New defects from a fresh full ingest |

## 4. Recommended approach

**Option F: export-then-delete, using Option D's general invariant as
the delete predicate.**

Concretely (for whoever implements this outside the current session):

1. **Freeze scope.** The delete predicate is exactly: `PriceBar` rows
   whose `(etf_id, session_date)` has no matching `is_trading_day=1`
   `TradingSession` row in the relevant calendar. Do not broaden this
   to a time-boxed "delete everything from this ingestion run" or
   narrow it to "delete only these two literal dates" — both are less
   correct than the invariant itself.
2. **Export before delete.** Write the full matched row set (all
   columns, not a summary) to a new, dated, immutable archive file —
   see Section 7 for exact naming and location. This is the
   remediation's undo mechanism; without it, Option F degrades to
   Option D with none of its reversibility advantage.
3. **Dry run first.** Run the predicate as a `SELECT COUNT(*)` /
   `SELECT *` before any `DELETE`, and confirm the count is exactly 50
   and the rows exactly match the investigation's enumerated set
   (same 25 ETFs, same 2 dates, same `source` tag). Any deviation from
   50 is a stop condition — it means either the invariant is broader
   than currently understood, or the database has changed since the
   investigation ran, and remediation should not proceed until that
   is explained.
4. **Delete inside a transaction**, as a committed, reviewed,
   versioned script (e.g. a one-off maintenance script, distinct from
   the numbered schema migrations in `migrations/`, since this is a
   data-quality fix, not a schema change) — never as an interactive
   statement typed ad hoc into a shell or notebook. The script itself
   becomes part of the audit trail.
5. **Do not touch verification methodology in the same change.** The
   investigation separately recommends making the missing-vs-surplus
   check two-directional (Section 8 here, and Section 9 of the
   discrepancy analysis). Land that as its own reviewed change, before
   or after the delete, but not silently bundled into the same commit
   — mixing "fix the data" with "fix the tool that failed to catch the
   data problem" in one change makes either one harder to review or
   revert independently.

### Why this best preserves research integrity

- **It removes exactly the invalid data and nothing else.** The
  predicate is derived from the platform's own existing
  source-of-truth table (`TradingSession`), not from a
  pattern-matched guess, so it cannot be accused of being tuned to
  produce a convenient row count.
- **It leaves a complete forensic trail.** The export step means the
  exact bytes of every deleted row remain permanently inspectable —
  anyone auditing this later can confirm the deleted rows really were
  flat-OHLC, zero-volume, non-trading-day rows, without having to
  trust a summary.
- **It does not touch any H3-relevant number.** No forward return, IC,
  p-value, score, or benchmark is read, computed, or referenced by
  this remediation — consistent with the pre-validation plan's
  standing no-outcome-data principle
  ([`REFERENCE_H3_PREVALIDATION_PLAN.md`](REFERENCE_H3_PREVALIDATION_PLAN.md),
  Section 2). Remediation is a data-hygiene action on raw price bars,
  strictly upstream of any H3 construction work, which has not yet
  started.
- **It is independently reproducible.** A second person, given only
  the predicate and the pre-deletion export, can verify the delete was
  correct without re-running the original investigation's SQLite
  session — which is exactly what Gate 2's independent-confirmation
  requirement (Section 8) needs.

## 5. Risks

- **Unidentified origin may recur.** The investigation could not
  determine what process inserted the 50 `backfill-gap-fill` rows.
  Deleting them without first ruling out an active, still-running
  source (a scheduled job outside this repository, a manual script
  run by another operator, etc.) risks the same 50 rows silently
  reappearing after cleanup, which would let a future Gate 2 check
  pass falsely again. **Mitigation:** treat "search for and either
  identify or rule out an active recurring source" as a precondition
  investigation step before the delete script is authorized to run —
  not a follow-up that happens after. If the origin cannot be
  confidently ruled out, the delete can still proceed (the rows are
  unambiguously invalid regardless of origin), but Gate 2's
  re-verification (Section 8) must then explicitly check for
  recurrence, not assume a one-time fix is durable.
- **Predicate drift risk.** If the delete script's predicate is
  written even slightly differently from Section 4's frozen invariant
  (e.g., matching on `source` instead of the `TradingSession` join),
  it silently degrades to Option C and loses Option D's durability
  advantage. **Mitigation:** code review of the script against this
  document's exact predicate wording before execution.
  **Mitigation for the review pass itself:** review of a one-off,
  never-to-be-rerun deletion script is a thin, one-time gate compared
  to schema migrations reviewed as permanent code — the reviewer
  should treat the SQL predicate as the entire risk surface and
  scrutinize it accordingly.
- **Backup/export completeness.** If the export step captures a
  summary or partial column set instead of full rows, the "reversible"
  property of Option F is only nominal. **Mitigation:** export must be
  a full row dump (`SELECT * `), machine-readable, and verified (row
  count and a spot-check of column values) against the live table
  before the delete transaction commits.
- **Scope creep into verification-methodology changes.** Bundling the
  two-directional check fix into the same change as the delete makes
  it harder to attribute a future regression to one or the other.
  **Mitigation:** land as two separate, separately reviewed changes
  (Section 4, point 5).
- **False sense of completeness from the 50-row match.** The dry-run
  count check (Section 4, point 3) is a safety gate, not a formality —
  a different count than 50 must halt remediation, not be quietly
  reconciled by widening or narrowing the predicate until it matches
  expectations.
- **Reviewer conflict of interest.** As with Gate 2 itself, whoever
  authors and executes the delete script should not be the sole
  confirmer of its correctness — this is a restatement of Section 8's
  independence requirement, listed here because it is a risk to the
  remediation specifically, not only to Gate 2's paperwork.

## 6. Validation plan

After remediation is executed (outside this session), the following
must be verified, in order, before Gate 2 re-review begins:

1. **Row count reconciliation.** `PriceBar` row count for the full
   universe drops by exactly 50 (61,900 → 61,850, using the
   investigation's own reported batch counts: 12,550 + 49,300 = 61,850
   valid rows). Per-ETF, each of the 25 ETFs drops from 2476 to 2474
   bars.
2. **Two-directional coverage check**, re-run against the live
   database, not against the old archived JSON:
   - **Missing:** 0 missing dates of 2474 expected trading days per
     ETF (unchanged from the original, still-true claim).
   - **Surplus (new):** 0 stored `PriceBar` dates with no matching
     `is_trading_day=1` `TradingSession` row, per ETF. This is the
     check that was absent originally and must now report explicitly,
     not be inferred from the missing-only result.
3. **Source-tag audit.** Zero remaining `PriceBar` rows anywhere in
   the table with `source='backfill-gap-fill'` (or any other
   unrecognized source value — the audit should enumerate all distinct
   `source` values present and confirm each is one the current
   ingestion codebase actually produces).
4. **Universe/date-range integrity.** Confirm the 25-ticker universe
   and each ETF's `[earliest, latest]` range are otherwise unchanged
   from the H3 extension's own post-extension state (2016-09-13 to
   2026-07-17) — the delete must not have removed any legitimate
   boundary row.
5. **Export/backup integrity check.** Confirm the pre-delete export
   archive (Section 7) contains exactly the 50 rows that were removed,
   byte-for-byte matching what the dry run reported in Section 4,
   point 3.
6. **Recurrence check** (only if Section 5's origin question was not
   conclusively closed): confirm no new `PriceBar` row with a
   non-`is_trading_day=1` `session_date` has appeared between the
   delete's execution time and the validation pass — i.e., the
   defect has not already started recurring in the gap between fix
   and verification.

### Evidence that must be regenerated

Because the underlying stored data changes, the following evidence
artifacts are now stale and must be **regenerated from the live,
post-remediation database** — not hand-edited to reflect the expected
numbers:

- A corrected data inventory (successor to
  `data_inventory_2026-07-19.json` and
  `data_inventory_2026-07-19_post_extension.json`), reporting
  `bars_per_etf: 2474` for all 25 ETFs and the two-directional
  coverage result from Section 6, point 2.
- A regenerated `post_extension_verification` result string that
  states both missing and surplus counts explicitly (e.g. "0 missing,
  0 surplus, of 2474 expected trading days"), replacing the
  one-directional "0 missing dates... ALL CLEAN" phrasing that masked
  this incident originally.
- A new independent Gate 2 review record (Section 8) — the existing
  `gate2_independent_review_2026-07-19.md` must not be edited or
  reused, since it reviewed pre-remediation evidence and already
  discloses its own independence gap.
- No H3-specific evidence (Gate 1 construction, correlation figures,
  economic rationale) needs regeneration — none of it has been
  produced yet, and none of it is affected by this remediation.

## 7. Required archive updates

Per this project's existing archive discipline (see
[`REFERENCE_H3_PREVALIDATION_PLAN.md`](REFERENCE_H3_PREVALIDATION_PLAN.md),
Section 6, and the `COMMIT.txt`/`README.md` convention already used in
`research_archive/reference_v1/` and `research_archive/reference_v2_h1/`),
remediation must **add** new dated artifacts rather than edit existing
ones in place. Existing files are a historical record of what was
believed true at the time and should remain readable as such.

New artifacts required under `research_archive/reference_h3/`:

1. **`removed_backfill_gap_fill_rows_<date>.json`** — the full,
   unedited pre-delete export from Section 4, point 2 / Section 6,
   point 5. This is the permanent forensic record of exactly what was
   removed.
2. **`data_inventory_<date>_post_remediation.json`** — the regenerated
   inventory from Section 6's "Evidence that must be regenerated,"
   following the same schema/fields as the two existing
   `data_inventory_*.json` files so they remain comparable.
3. **`gate2_independent_review_<date>_post_remediation.md`** — the new
   independent review record from Section 8, produced by a reviewer
   who did not perform the remediation.
4. **A remediation execution record** (could be folded into item 1's
   file header or kept separate) stating: who executed the delete
   script, the exact predicate used, the dry-run count, the commit
   hash of the delete script, and the timestamp of execution — mirroring
   the `COMMIT.txt` pointer convention already used for v1 and v2 H1.

Existing files requiring **no edits, only superseding cross-references
added**:

- `docs/REFERENCE_H3_GATE2_DISCREPANCY_ANALYSIS.md` — remains the
  authoritative account of how the discrepancy was found. A follow-up
  note (e.g., a short new "Remediation record" doc, or a dated
  addendum section — decided at implementation time, not here) should
  point forward to the new archive artifacts above, rather than this
  file being rewritten to erase the discrepancy it documents.
- `research_archive/reference_h3/data_inventory_2026-07-19.json` and
  `..._post_extension.json` — left untouched as the historical
  pre-remediation record; the new inventory file (item 2 above) is the
  current source of truth going forward.
- `research_archive/reference_h3/gate2_independent_review_2026-07-19.md`
  — left untouched; it already discloses its own non-independence and
  remains an accurate record of that review's findings at the time.
- `research_archive/reference_h3/README.md` — this one **should** be
  updated (it is an index, not a point-in-time record) to add the new
  artifacts to its listing, once they exist.

No governance document (`REFERENCE_H3_PREVALIDATION_PLAN.md`,
`REFERENCE_RESEARCH_ROADMAP_NEXT.md`) requires content changes — the
prevalidation plan's Gate 2 definition already anticipates exactly
this kind of correction-then-reverify cycle; only its **status**
(HOLD → satisfied) changes, and only after Section 8 completes.

## 8. Required Gate 2 re-review process

Gate 2 remains **HOLD** until all of the following occur, in order:

1. Remediation (Section 4) is executed and the validation plan
   (Section 6) passes in full, including the recurrence check if
   applicable.
2. The evidence artifacts in Section 7 exist and are internally
   consistent (the new inventory's counts match the export file's row
   count arithmetic; 61,900 − 50 = 61,850).
3. A **genuinely independent** reviewer — per
   `REFERENCE_H3_PREVALIDATION_PLAN.md` Section 4's confirmation
   duties, meaning someone (or some separately-scoped process with no
   memory of having performed the remediation) who did not author or
   execute the delete script — performs a fresh review that:
   - independently re-queries the live database (not the archived
     JSON) and reproduces the post-remediation counts and the
     two-directional check, matching Section 6's independent-
     reproduction standard already established by the original
     (non-independent) `gate2_independent_review_2026-07-19.md`;
   - confirms the pre-delete export (Section 7, item 1) exactly
     accounts for the row-count delta;
   - confirms no `source` value remains in the table that the current
     ingestion codebase does not itself produce;
   - explicitly re-confirms the standing no-outcome-data and
     no-prior-result-influence duties from the prevalidation plan
     (Section 4, points 2–3), since remediation work is a natural
     place for scope to silently creep toward H3 construction
     decisions it must not touch;
   - records this confirmation — reviewer identity, date, reproduced
     figures — as its own archived document (Section 7, item 3), not
     an informal sign-off appended elsewhere.
4. Only after step 3's record exists does Gate 2's status change from
   HOLD to satisfied. The original discrepancy analysis's Section 9
   recommendation ("Gate 2 should remain in HOLD until (a) the
   correction... is made and re-verified, and (b) genuine
   independent-reviewer confirmation... occurs") is the binding
   requirement this section operationalizes; nothing in this
   remediation plan lowers that bar.

## 9. Go / No-Go recommendation

**Go on remediation, via Option F (Section 4), subject to the
precondition in Section 5** (best-effort origin check, or explicit
acknowledgment that origin could not be determined, before the delete
script is authorized to execute).

**No-Go on Gate 2 itself** until Section 8's full re-review sequence
completes with a genuinely independent confirmation record. This plan
does not itself move Gate 2 off HOLD, and no action taken in this
session does either.

No database was modified, no migration was written, no report was
regenerated, no archive file was edited, and nothing was committed or
pushed as part of producing this plan.

---

**STOP — this is a planning and governance document only. No
remediation has been executed. Implementation requires a separate,
explicitly authorized task.**
