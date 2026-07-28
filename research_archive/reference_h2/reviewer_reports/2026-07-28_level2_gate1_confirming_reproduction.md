# `reference_h2` — Level 2 Gate 1 Confirming Review: Independent Reproduction

**Review event:** Gate 1 (signal independence) confirming review of
`reference_h2` Construction Attempt #1, per
[`prevalidation_plan.md`](../prevalidation_plan.md) §6, point 4
("independently reproduce — not merely inspect — both required
components").

**Date:** 2026-07-28.

**Reviewer identity:** Claude Opus 5, fresh session, acting as confirming
reviewer. Not the author of the H2 hypothesis, research proposal,
pre-validation plan, Attempt #1 specification, Attempt #1 addendum,
`experiments/validate_h2_gate1_independence.py`, or any prior
`reference_h2` reviewer report.

**Independence tier:** **Level 2 — AI-assisted adversarial review**, per
[`docs/RESEARCH_GOVERNANCE_STANDARD.md`](../../../docs/RESEARCH_GOVERNANCE_STANDARD.md)
§4, and no higher.

**Independence disclosure (mandatory, per `prevalidation_plan.md` §6).**
This is **procedural independence only**. It is **not organizational
independence** and must never be represented as such:

- Same model family and same vendor as the reviewed work; no incentive
  separation; no separate reporting line.
- Session separation is self-reported and not third-party verifiable
  from outside the session, exactly as Standard §4 states.
- **Level 3 review was not available for this gate.** No Level 3 review
  has ever been performed on this platform. This is disclosed here in
  advance, per `prevalidation_plan.md` §6's "Level 3 availability
  disclosure requirement", and is not an oversight to be silently
  corrected later.

**Scope limits of this report (binding).** This report does **not**:

- declare Gate 1 PASS, FAIL, or INCONCLUSIVE;
- interpret the measured correlation as "very high", "moderate", or
  "low" under `prevalidation_plan.md` §3 Gate 1's degenerate-case
  interpretation rules;
- authorize, recommend, or imply Methodology Freeze (Phase 4);
- make or imply any lifecycle transition. No `advance_phase()` call, no
  `DecisionRecorder.append()`, and no append to or edit of
  [`transition_records.jsonl`](../transition_records.jsonl) occurs as a
  result of this review.

Its findings are confined to (a) reproduction match/mismatch and (b)
`prevalidation_plan.md` §6 points 1–3 compliance.

---

## 1. Pre-computation confirmations

### 1.1 `reference_h2` remains PRE_VALIDATION

[`research_archive/reference_h2/transition_records.jsonl`](../transition_records.jsonl)
contains exactly **one** record (verified: 1 line, tracked, no
uncommitted modification at `HEAD`):

| Field | Value |
|---|---|
| `sequence_number` | 1 |
| `from_phase` → `to_phase` | `Research Proposal` → `Pre-validation` |
| `recorded_at` | 2026-07-28T11:09:00Z |
| `commit_hash` | `4030d86e2316a7fe3b0ec70c84a44bbf389fac2d` |
| `gate_outcomes` | `[]` (empty) |
| `predecessor_hash` | `null` |

**Confirmed.** The cycle is in PRE_VALIDATION. No Gate outcome has been
recorded in the transition record, and no Pre-validation → Methodology
Freeze transition exists.

### 1.2 Attempt #1 is the only logged attempt

`find research_archive/reference_h2 -name "attempt*"` returns exactly two
files, both belonging to Attempt #1:

- [`attempt_001_specification.md`](../attempt_001_specification.md)
  (2026-07-28 14:08 local) — the frozen construction;
- [`attempt_001_addendum_2026-07-28.md`](../attempt_001_addendum_2026-07-28.md)
  (2026-07-28 14:25 local) — the false-attestation correction, which
  supersedes the specification's status header and §3 points 2–3 only.

No `attempt_002*` or later artifact exists. **Confirmed: Attempt #1 is
the only logged attempt**, and per the addendum §7 it is the only
*validly* logged one — the original 14:08 logging was procedurally
invalidated by the false attestation and re-submitted, corrected, at
14:25 without consuming an extra slot against the plan's cap of 3.

This reviewer notes, without ruling on it, that the addendum's
disposition of the cap (invalid logging not counted as a consumed
attempt) is a governance ruling made by the same party that discovered
the defect; it is recorded here as reviewed and understood, not as
independently re-adjudicated, since adjudicating it is outside this
review's reproduction mandate.

---

## 2. Provenance captured

### 2.1 Repository

| Item | Value |
|---|---|
| `git rev-parse HEAD` | `f879d9e40a5ea5cd115b63b838786e9f87b3d743` |
| Branch | `master` |
| Working tree | **clean** (`git status --porcelain` empty) |
| Submitted report's commit | `a7d0938c66ab86e0bfb46b643698f67229b224a2` |

`a7d0938` is a verified ancestor of `f879d9e`. `git diff --name-only
a7d0938 f879d9e` touches nine files: `.gitignore`, the Gate 1 evidence
script, the two Attempt #1 artifacts, two reviewer reports, and three
test files. It touches **none** of
`experiments/daily_etf_universe_update.py`, `core/analytics/`,
`core/market_data/`, or the database, so the score-side inputs are
identical at both commits.

`experiments/validate_h2_gate1_independence.py`,
`attempt_001_specification.md`, and
`attempt_001_addendum_2026-07-28.md` are all **now tracked** — the
addendum §2's "neither has ever been committed" observation was correct
when written and has since been discharged by `41ce0fb`/`c771355`.

**However, the committed evidence script is not provably the script that
produced the submitted report** — see Finding O-5. Timeline:

| Time (local) | Event |
|---|---|
| 13:58:38 | script created on disk (per addendum §2) |
| 13:58:46 | report generated |
| 14:25 | addendum written, still recording script mtime 13:58:38 |
| **15:05:58** | **script mtime — modified after the report was generated** |
| 15:08:54 | script first committed, at `c771355` |

The reviewer's reproduction is unaffected: it reimplements the
specification rather than the script, so its match in §4 confirms the
report's *figures* independently of which script version produced them.

### 2.2 Database identity snapshot

| Item | Value |
|---|---|
| Path | `experiments_etf_universe.db` |
| Size | 85,446,656 bytes |
| SHA-256 | `cd4fd53d2032fbc87364adc578bcab4fc5ad1a1a779ce72c62697a037a148103` |
| mtime (UTC) | 2026-07-18T23:23:48Z |
| WAL / SHM sidecars | none present (fully checkpointed) |
| Tables | Calendar, DimensionScore, ETF, IndicatorDefinition, IndicatorValue, IngestionRun, PipelineState, PriceBar, Score, ScoringProfile, TradingSession, schema_migrations |
| Row counts | ETF 25 · PriceBar 61,850 · IndicatorValue 24,200 · Score 12,075 · DimensionScore 24,150 · TradingSession 2,725 |
| `PriceBar.source` composition | `yahoo_finance` — **single tag, 61,850/61,850 rows** |

The database mtime (2026-07-18T23:23:48Z) **precedes** both the
submitted report's `generated_at` (2026-07-28T11:58:46Z) and this
reproduction's run (2026-07-28T13:42:41Z), and no WAL sidecar exists.
The submitted run and this reproduction therefore read the same
unmodified database. This is mtime-and-sidecar evidence, not a hash
taken at the moment of the submitted run — no such hash was recorded by
the submitted artifact (see Finding O-2).

Governing definitions read from the database, not assumed:

- **SMA(20)**: `IndicatorDefinition` `38481ad9524e4922a9275fffacc39df6`,
  `name=SMA`, `version=1`, `parameters={"window": 20}`.
- **REFERENCE v1 profile**: `parameters` maps
  `MOMENTUM → {indicator_name: "SMA", indicator_version: 1}`.
- **Calendar**: `XNYS`, 2,725 trading days spanning 2016-09-13 to
  2027-07-19.

### 2.3 PriceBar coverage for the 25-ETF universe

All 25 tickers in `experiments/daily_etf_universe_update.py`'s
`ETF_UNIVERSE` are present, and coverage is **exactly uniform across all
25**:

| Item | Value |
|---|---|
| Tickers | ACWI, ARKK, BND, BOTZ, EEM, EFA, EWJ, GLD, HACK, ICLN, IWM, QQQ, SCHD, SKYY, SPY, TLT, USMV, VGK, VNQ, VT, VTI, XLE, XLF, XLK, XLV |
| Rows per ticker | 2,474 (identical for every ticker; 25 × 2,474 = 61,850) |
| First / last session | 2016-09-13 / 2026-07-17 (identical for every ticker) |

**Formation-window adequacy for Gate 1's own date panel.** The earliest
ranking date evaluated is 2024-08-13, whose formation window resolves to
2023-07-13 → 2024-07-15. Price history extends 2016-09-13, so the
252 + 21 trading-day lookback is available with a very large margin, and
**zero** ranking dates were dropped for insufficient calendar history.

This is a Gate 1 provenance capture only. It is **not** the fresh, dated
Gate 2 data-adequacy inventory that `prevalidation_plan.md` §3 Gate 2
requires; that gate remains open and is not addressed by this report.

### 2.4 Read-path validation for "`reference_v1`'s frozen SMA(20) score"

The submitted script reads MOMENTUM via
`generate_ranked_etf_report()` → `DimensionScore`. This reviewer instead
read the `IndicatorValue` rows for SMA v1 directly, then verified the two
read paths are equivalent rather than assuming it:

```
SELECT COUNT(*), SUM(CASE WHEN DimensionScore.value = IndicatorValue.value THEN 1 ELSE 0 END)
  → {tot: 12075, eq: 12075}
```

All **12,075** `(ETF, date)` MOMENTUM dimension scores are numerically
identical to their SMA(20) indicator values. The reproduction below
therefore reaches `reference_v1`'s frozen SMA(20) score by an
independent read path that provably resolves to the same values.

---

## 3. Independent reproduction

### 3.1 Independence of the implementation

The reproduction script was written from
[`prevalidation_plan.md`](../prevalidation_plan.md) §3 Gate 1 and
[`attempt_001_specification.md`](../attempt_001_specification.md) §2
alone. It:

- does **not** import `compute_h2_scores()`;
- does **not** import or invoke `validate_h2_gate1_independence.run()`
  or any other symbol from that module;
- does **not** import `validate_h3_gate1_independence.score_overlap()`
  or `compute_momentum_scores()` (the two overlap/momentum helpers the
  submitted script reuses) — both are reimplemented here;
- reimplements the H2 score construction, panel assembly, average-tie
  ranking, Spearman correlation, top/bottom-N overlap, and every
  distribution summary from scratch.

Approved shared infrastructure reused, and nothing else:

| Purpose | Symbol |
|---|---|
| SMA(20) read path | `core.analytics.persistence.repository.get_indicator_values` |
| Price read path | `core.market_data.persistence.repository.get_price_bars` |
| Calendar read path | `core.market_data.persistence.repository.get_trading_days` |
| Connection | `core.store.connection.connect` |
| Generic statistical helpers (**cross-check only**) | `experiments.validate_reference_v1_significance._rank_average_ties`, `._pearson` |

The platform helpers were used only to cross-check the reviewer's own
primitives, never to produce the reported figures. Over 29 sampled dates
the maximum absolute difference between the reviewer's Spearman and the
platform-helper Spearman was **0.0**, confirming the reviewer's
average-tie convention matches the frozen tie rule of
`attempt_001_specification.md` §2.6.

### 3.2 Frozen construction as transcribed

| Element | Value | Source |
|---|---|---|
| Formation window | 252 trading days | §2.4 |
| Skip period | 21 trading days | §2.4 |
| Score | `ln(close[trading_day k−21]) − ln(close[trading_day k−273])` | §2.4 |
| Return basis | close-to-close log, price return (no dividend adjustment) | §2.4 |
| Ranking | cross-sectional ordinal rank, descending | §2.5 |
| Tie handling | average rank | §2.6 |
| Missing data | both endpoint closes must resolve directly from `PriceBar`; no fill, no interpolation, no partial window | §2.7 |
| Minimum panel | 10 | §2.8 |
| Bucket size | 5 | §2.9 |
| Window | 2024-07-17 → 2026-07-17 | §2.10 |

**Date-set reading.** §2.10 fixes a *window*, not a date list. The
primary reading applied here is: every `XNYS` trading day inside that
window on which `reference_v1`'s frozen SMA(20) score exists. That
yields **502** trading days in the window, of which **19** (2024-07-17
through 2024-08-12, the SMA(20) warm-up interval) carry no SMA(20)
value, leaving **483** evaluated ranking dates. A sensitivity variant
restricted to the 463 dates `reference_v1`'s significance report
actually evaluated is reported in §3.5.

### 3.3 Component 1 — reviewer's own figures

Per-date cross-sectional Spearman rank correlation between the H2
trailing-return score and `reference_v1`'s frozen SMA(20) score, one
correlation per date, never pooled.

| Statistic | Reviewer's value |
|---|---|
| n (ranking dates) | 483 |
| mean | 0.3120003185220576 |
| median | 0.3376923076923077 |
| p05 | 0.065 |
| p25 | 0.15307692307692308 |
| p75 | 0.4473076923076923 |
| p95 | 0.5451538461538461 |
| min | −0.047692307692307694 |
| max | 0.6246153846153846 |
| stdev | 0.16271839627387008 |
| undefined (zero-variance) dates | 0 |

Panel size was **25 on every one of the 483 dates**. Dates dropped for
insufficient calendar history: **0**. Dates dropped below the
minimum-panel threshold of 10: **0**.

### 3.4 Component 2 — reviewer's own figures

Fraction of the top-5 (and bottom-5) ETFs under `reference_v1`'s frozen
SMA(20) score that also appear in the top-5 (bottom-5) under the H2
candidate score, computed per date and reported as a distribution.

| Statistic | Top-5 overlap | Bottom-5 overlap |
|---|---|---|
| n | 483 | 483 |
| mean | 0.2819875776397516 | 0.3337474120082816 |
| median | 0.2 | 0.4 |
| p05 | 0.2 | 0.0 |
| p25 | 0.2 | 0.2 |
| p75 | 0.4 | 0.4 |
| p95 | 0.6 | 0.6 |
| min | 0.0 | 0.0 |
| max | 0.8 | 0.8 |
| stdev | 0.13414313843094397 | 0.1637217378243783 |

### 3.5 Date-set sensitivity (reviewer-added, not part of the submitted evidence)

Restricting to the 463 ranking dates `reference_v1`'s own significance
report evaluated (the 483 less the trailing 20 its forward horizon
consumed — a restriction Gate 1 does not need, since Gate 1 uses no
forward horizon):

| Statistic | Component 1 | Top-5 overlap | Bottom-5 overlap |
|---|---|---|---|
| n | 463 | 463 | 463 |
| mean | 0.3187572686492773 | 0.28250539956803455 | 0.339524838012959 |
| median | 0.3476923076923077 | 0.2 | 0.4 |
| min / max | −0.047692… / 0.624615… | 0.0 / 0.8 | 0.0 / 0.8 |

The distributions are materially unchanged. **The 483-vs-463 date-set
ambiguity in §2.10 is not outcome-bearing for either component.** This
is reported so the ambiguity is on the record as tested rather than
assumed away; it does not alter the comparison in §4.

---

## 4. Comparison against the submitted report

Compared against
`h2_gate1_independence_analysis_report.json` (SHA-256
`b021ed4461e81f36c5947f3b04c9975aafff5f8c4eceed8f100638fe88996197`,
`generated_at` 2026-07-28T11:58:46Z, `repository_commit` `a7d0938c…`).
The report's figures were **not** read until after the reviewer's own
figures above were computed and written to disk; prior reviewer reports'
conclusions about the numbers were not read at any point.

**Tolerance used: exact bitwise equality of IEEE-754 doubles (absolute
tolerance 0).** A looser tolerance was prepared but proved unnecessary —
no quantity required it.

### 4.1 Panel construction

| Quantity | Submitted | Reviewer | Match |
|---|---|---|---|
| Universe size | 25 | 25 | ✅ |
| Ranking dates in window | 502 | 502 | ✅ |
| Dates excluded, missing MOMENTUM score | 19 | 19 | ✅ |
| Dates excluded, missing H2 history | 0 | 0 | ✅ |
| Dates excluded, below minimum panel | 0 | 0 | ✅ |
| Ranking dates evaluated | 483 | 483 | ✅ |
| Date set (as sets) | — | — | ✅ identical, no symmetric difference |
| First / last date | 2024-08-13 / 2026-07-17 | 2024-08-13 / 2026-07-17 | ✅ |

### 4.2 Distribution summaries

| Statistic | Submitted | Reviewer | Δ |
|---|---|---|---|
| C1 n | 483 | 483 | 0 |
| C1 mean | 0.3120003185220576 | 0.3120003185220576 | 0 |
| C1 median | 0.3376923076923077 | 0.3376923076923077 | 0 |
| C1 p25 | 0.15307692307692308 | 0.15307692307692308 | 0 |
| C1 p75 | 0.4473076923076923 | 0.4473076923076923 | 0 |
| C1 min | −0.047692307692307694 | −0.047692307692307694 | 0 |
| C1 max | 0.6246153846153846 | 0.6246153846153846 | 0 |
| C2 top mean | 0.2819875776397516 | 0.2819875776397516 | 0 |
| C2 top median | 0.2 | 0.2 | 0 |
| C2 top min / max | 0.0 / 0.8 | 0.0 / 0.8 | 0 |
| C2 bottom mean | 0.3337474120082816 | 0.3337474120082816 | 0 |
| C2 bottom median | 0.4 | 0.4 | 0 |
| C2 bottom min / max | 0.0 / 0.8 | 0.0 / 0.8 | 0 |

### 4.3 Per-date comparison (all 483 dates, not a sample)

| Quantity | Dates compared | Bitwise-identical | Max abs Δ |
|---|---|---|---|
| `spearman_correlation` | 483 | **483 / 483** | 0 |
| `top_overlap_fraction` | 483 | **483 / 483** | 0 |
| `bottom_overlap_fraction` | 483 | **483 / 483** | 0 |
| `n_etfs` (panel size) | 483 | **483 / 483** | 0 |

### 4.4 Reproduction verdict

**MATCH.** Both Gate 1 components reproduce exactly. Neither component's
reproduction was substituted for the other: Component 1 (rank
correlation) and Component 2 (ranking-extreme overlap) were each
independently implemented and each independently compared, per
`prevalidation_plan.md` §6 point 4.

**No data-provenance escalation is raised.** The reviewer found no
discrepancy in universe composition, price coverage, calendar
resolution, score availability, panel construction, or exclusion
accounting.

This is a statement about arithmetic reproducibility only. It is **not**
a Gate 1 determination and carries no interpretation of what the
reproduced figures mean.

---

## 5. `prevalidation_plan.md` §6 points 1–3 compliance

### 5.1 Point 1 — complete construction attempt log reviewed

**Confirmed.** The complete log is Attempt #1 and nothing else: the
specification and its addendum were both read in full, including the
addendum's invalidation ruling and its §10 residual risk. There is no
"final passing construction" selected from among several — only one
construction has ever been logged under this cycle. The three-attempt
cap has two slots remaining.

### 5.2 Point 2 — no outcome data read or computed

**Confirmed for the work being confirmed, and for this review's own
work.**

Evidence for the submitted work:

- `grep -c forward_return experiments/validate_h2_gate1_independence.py`
  → **0**. The script neither imports nor calls
  `validate_scoring_signal.forward_return()`, the platform's only
  forward-return implementation.
- The script's complete set of data reads is `get_price_bars`,
  `get_trading_days`, `get_scoring_profile`, and — via
  `compute_momentum_scores` → `generate_ranked_etf_report` —
  `Score`/`DimensionScore`. All four are score-side or price-side, all
  resolved at or before the ranking date.
- Its imported helpers are `_percentile` and `_spearman` (pure, no I/O)
  and `score_overlap` (pure, no I/O). `compute_momentum_scores` reads
  only the MOMENTUM dimension score, verified above to be the SMA(20)
  value.
- The report's `daily_results` records exactly four quantities per date
  — `n_etfs`, `spearman_correlation`, `top_overlap_fraction`,
  `bottom_overlap_fraction`. No forward return, IC, p-value, null
  distribution, permutation, or bootstrap quantity appears anywhere in
  the script or its output.

Evidence for this review's own work: the reproduction script reads
`PriceBar`, `TradingSession`, `IndicatorValue`, `ETF`, and
`IndicatorDefinition` only. Every price it reads is dated at or before
the ranking date's formation-end (`t − 21`). It computes no forward
return, IC, p-value, null distribution, or any other outcome variable.

**One qualification, stated rather than glossed:** this review's
cross-check imported `experiments.validate_reference_v1_significance`,
whose module-level imports include `forward_return`. Importing a symbol
is not reading or computing an outcome; `forward_return()` is never
called by either the submitted script or this reproduction, and no
forward-return value exists anywhere in either run's memory or output.

### 5.3 Point 3 — no already-tested cycle's observed results influenced construction selection

**Confirmed on the documentary record, with the residual risk the
addendum already disclosed left unresolved — as it must be.**

What the repository record supports:

- `docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md` (00:17 local)
  names the construction to test — "~252 trading days (~12 months), with
  a 1-month skip" (§ table, line 18) and "the cross-sectional
  correlation between `reference_v1`'s `SMA(20)` rank and a
  trailing-12-1-month-return rank" (§1 item 2) — roughly **13¾ hours
  before** `experiments/validate_h2_gate1_independence.py` existed. The
  construction was therefore named before any correlation figure for it
  could exist under this cycle. This reviewer verified the timestamps
  and the document text directly rather than accepting the addendum's
  account of them.
- `attempt_001_specification.md` §4 discloses six rejected alternatives,
  each with an economic or construction-logic rationale. None cites a
  numeric correlation, overlap figure, or any prior cycle's observed
  result. `reference_v2_h1` and `reference_h3` are cited only for
  *convention reuse* (log-return basis, bucket size 5, minimum panel
  10) and for *mechanism distinctness*, never for their outcomes.

What remains unresolved, and is carried forward rather than closed:

- Whether the pre-existing report's figures were consulted while
  drafting §2 or §4 of the specification is not establishable from
  repository evidence. `attempt_001_addendum_2026-07-28.md` §10 records
  this as a permanent, disclosed, unconfirmed-status residual risk on
  Attempt #1. **This review does not resolve it in either direction**,
  and the exact reproduction reported in §4 above does not bear on it —
  reproducing a number correctly says nothing about whether that number
  was known in advance. Per `prevalidation_plan.md` §3 Gate 1's
  "Resolving ambiguity" rule, the stricter reading is the default, and
  this reviewer applies it: the residual risk stands open and attaches
  to Attempt #1's evidentiary weight, a matter for whoever makes the
  Gate 1 determination.

---

## 6. Observations (not gate determinations)

**O-1 — The Gate 1 evidence artifact is not under version control and is
not in the evidence package.**
`h2_gate1_independence_analysis_report.json` lives at the repository
root and is explicitly excluded by `.gitignore:34`. It is therefore
neither committed nor located under
`research_archive/reference_h2/`, which
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §5 defines as the cycle's single
self-contained evidence package. `prevalidation_plan.md` §5 requires
every Gate 1–4 evidence artifact to state its source, producing commit,
and date, and to be reproducible by a second party from the written
record. Reproducibility is satisfied — this report demonstrates it — but
the artifact's *location and durability* are not: a regeneration or a
clean checkout silently replaces or loses it. This is an evidence-package
placement matter for whoever makes the Gate 1 determination, not a
reproduction defect.

**O-2 — The submitted report records no database identity.** Its
provenance block captures `generated_at` and `repository_commit` but no
database hash, size, or row counts. This review had to establish
database identity independently (§2.2), and can only bound the database
as unchanged between the two runs by mtime and the absence of WAL
sidecars, not by a hash contemporaneous with the submitted run. Future
evidence artifacts under this plan would satisfy §5's provenance rule
more strongly by recording the database hash inline.

**O-3 — Minor overstatement in the addendum's corrected attestation.**
`attempt_001_addendum_2026-07-28.md` §9 point 3 states that "the
construction parameters (252-day formation, 21-day skip, log return)
were named" in `docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md`.
Verified against that document: **252 trading days and a 1-month skip
are named**; the strings "21 trading", "21-trading", and "log return" do
**not** appear anywhere in it (case-insensitive count: 0). The skip's
exact integer (21) and the return basis (log vs. simple) were first
fixed in `attempt_001_specification.md` §2.4, after the report existed.
Both are justified there on disclosed convention-reuse grounds
(the platform's 21-trading-day-month convention; the log-return basis of
`REFERENCE_V2_H1` and `reference_h3`), which is a defensible provenance —
but it is a *different* provenance from the one §9 point 3 claims. The
addendum's core correction is sound; this specific supporting sentence
overstates its source and should be read as covering the formation
window and the existence of a skip only.

**O-4 — The evidence package is incomplete against §5's seven-item
structure** (no `methodology.md`, `dataset_manifest.json`,
`dataset_hashes/`, `experiment_results/`, or `decision_log.md`). Four of
those are Phase 4+ artifacts and their absence is expected at
PRE_VALIDATION; `decision_log.md`, which §5 describes as spanning
Phases 2 through 8, is not. Noted for the cycle's later Archive
requirement, not as a Gate 1 obstacle.

**O-5 — The producing code for the submitted report is not preserved,
and the report's `repository_commit` field does not pin it.**
`h2_gate1_independence_analysis_report.json` was written at 13:58:46
local. `experiments/validate_h2_gate1_independence.py` has an on-disk
mtime of **15:05:58** local — 67 minutes *after* the report — and was
first committed three minutes later, at `c771355` (15:08:54). The
addendum, written at 14:25, independently recorded the script's mtime as
13:58:38 at that time, so the modification occurred between 14:25 and
15:05:58. The script version that actually produced the submitted report
was never committed and no longer exists in the working tree or in git.

Compounding this, the report's `repository_commit` field records
`a7d0938c…`, which was HEAD at generation time — but the script was
untracked at `a7d0938`, so that field pins the *repository state around*
the run without pinning the *code that ran*. A reader following the
provenance chain from report to producing code lands on a script that
demonstrably post-dates the report.

`prevalidation_plan.md` §5 requires that an artifact be reproducible "by
a second party from the written record and the raw data alone". That
requirement is met — §4 of this report demonstrates it, from the
specification rather than from the script. The gap is narrower but real:
the report-to-script provenance link asserted by the artifact's own
metadata does not hold, and cannot be repaired retroactively. Noted as a
disclosure matter for whoever makes the Gate 1 determination.

This reviewer deliberately did **not** re-run the committed script to
test whether it reproduces the report: `DEFAULT_OUTPUT_PATH` writes to
the repository root, which would overwrite the submitted evidence
artifact under review.

---

## 7. Summary of what this report establishes

1. `reference_h2` remains in **PRE_VALIDATION**; the transition record
   holds one entry with empty `gate_outcomes`. ✅
2. **Attempt #1 is the only logged construction attempt.** ✅
3. Provenance captured: commit `f879d9e…` (clean tree), database
   SHA-256 `cd4fd53d…` unchanged since 2026-07-18, uniform PriceBar
   coverage of 2,474 rows per ETF across all 25 tickers from 2016-09-13
   to 2026-07-17, single `yahoo_finance` source tag. ✅
4. **Component 1 independently reproduced — exact match**, 483/483
   dates bitwise identical, tolerance 0. ✅
5. **Component 2 independently reproduced — exact match**, both top-5
   and bottom-5 overlap, 483/483 dates bitwise identical, tolerance 0. ✅
6. §6 point 1 (complete attempt log reviewed) — **confirmed**. ✅
7. §6 point 2 (no outcome data read or computed) — **confirmed**, with
   the import-vs-call qualification stated in §5.2. ✅
8. §6 point 3 (no already-tested cycle's results influenced selection) —
   **confirmed on the documentary record**, with Attempt #1's disclosed
   residual risk (addendum §10) left open, not resolved. ✅
9. Level 3 review was **not available** for this gate. ✅ (disclosed)
10. Five provenance/packaging observations (O-1 … O-5) are recorded for
    whoever makes the Gate 1 determination. The most consequential is
    **O-5**: the script that produced the submitted report was modified
    67 minutes after generating it and its pre-modification version was
    never committed, so the report's own `repository_commit` field does
    not pin the code that ran. This does not affect the reproduction
    verdict — §4's match derives from the frozen specification, not from
    the script — but the report-to-code provenance link asserted by the
    artifact's metadata does not hold and cannot be repaired
    retroactively.

**No Gate 1 PASS/FAIL/INCONCLUSIVE determination is made here. No
interpretation of the measured correlation as very high, moderate, or
low is made here. No Methodology Freeze is authorized here. No lifecycle
transition, `DecisionRecord`, or edit to `transition_records.jsonl`
occurs here.**

---

## 8. Reproduction instructions

The reviewer's reproduction script is retained outside the repository
(session scratchpad). It is fully specified by §3.1–3.2 above and can be
rewritten from that description alone. To re-derive the figures:

1. Check out `f879d9e40a5ea5cd115b63b838786e9f87b3d743`.
2. Confirm `experiments_etf_universe.db` hashes to
   `cd4fd53d2032fbc87364adc578bcab4fc5ad1a1a779ce72c62697a037a148103`.
3. Build the `XNYS` trading-day list from `TradingSession`
   (`is_trading_day = 1`).
4. For each trading day `t` in 2024-07-17 … 2026-07-17 with an SMA(20)
   `IndicatorValue`, at calendar index `k`: score each ETF as
   `ln(close[trading_days[k−21]]) − ln(close[trading_days[k−273]])`,
   requiring both closes to resolve directly from `PriceBar`.
5. Require ≥ 10 ETFs with both an H2 score and an SMA(20) value.
6. Component 1: Spearman (Pearson on average-tie ranks) of the two
   score vectors.
7. Component 2: `|top5(H2) ∩ top5(SMA)| / 5` and the same for the
   bottom 5, ranking descending in both cases.
8. Summarize each per-date series across dates.

---

*End of Level 2 Gate 1 confirming review. Procedural independence only —
not organizational independence.*
