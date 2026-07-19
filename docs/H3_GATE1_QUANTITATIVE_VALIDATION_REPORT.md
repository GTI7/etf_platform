# H3 Gate 1 Quantitative Validation Report

**Report date:** 2026-07-19
**Prepared by:** AI research assistant (Claude), single session, no
conversational continuity with any prior REFERENCE H3 session.
**Scope:** execution of `docs/REFERENCE_H3_PREVALIDATION_PLAN.md`
Section 2 ("Research independence verification") against the frozen
construction in
`research_archive/reference_h3/attempt_001_specification.md`. This is
**Gate 1 as this project's own governance defines it** — a same-date,
score-to-score independence check between the candidate H3 score and
REFERENCE v1's MOMENTUM score. It is **not** a forward-return backtest,
an IC/p-value significance test, or a risk-adjusted-performance
comparison; the frozen methodology explicitly prohibits touching any
of those in this phase (Prevalidation Plan Section 2, "Standalone
principle").

---

## 0. Terminology reconciliation (mandatory disclosure)

The task instructions requesting this report use a generic
institutional-validation template (benchmark comparison, performance
metrics, risk-adjusted return, statistical significance) that does
**not** match what "H3 Gate 1" actually is inside this repository's
frozen governance framework. Per the mandatory rule to document
ambiguity rather than resolve it by changing methodology, this
mismatch is recorded here rather than silently reconciled:

| Generic template term | What was actually executed |
|---|---|
| "Benchmark comparison" | REFERENCE v1's frozen MOMENTUM score — the literal "Benchmark" row in the Prevalidation Plan's own frozen methodology table (Section 2, "Frozen methodology summary") — **not** a market index, and **not** a forward-return comparison. |
| "Performance metrics" | Daily cross-sectional Spearman rank correlation and rank-overlap-at-the-extremes between two **scores**, not returns. |
| "Statistical significance" | No p-value, no hypothesis test, no permutation test was computed. The Plan explicitly forbids this at this phase ("No forward return, no null distribution, no p-value is computed at any point — this is a descriptive comparison of two already-computed scores against each other, not a hypothesis test.") |
| "Risk-adjusted performance / overfitting of returns" | Not applicable — no return series of any kind was touched. |

No frozen input, acceptance criterion, or evaluation methodology was
changed to resolve this mismatch. The frozen Section 2 methodology was
executed as written; the generic template's structure is followed only
for section *headings*, with content substituted accordingly.

---

## 1. Executive Summary

**Validation status: PASS on the measured quantitative evidence —
NOT YET a governance-final Gate 1 PASS.**

The frozen H3 construction (Attempt 1) was measured against REFERENCE
v1's frozen MOMENTUM score across 483 trading dates (2024-08-13 through
2026-07-17, within REFERENCE v1's own 2024-07-17–2026-07-17 evaluation
window). The daily Spearman rank correlation between the two scores has
a median of **0.108** and a mean of **0.101**, with an interquartile
range of **-0.036 to 0.229** and a full range of **-0.322 to 0.452**.
This is unambiguously and by a wide margin **not** the mathematically
provable near-1.0 degenerate case the Plan identifies as an automatic
rejection trigger — the construction has clearly escaped that failure
mode. Under the Plan's ambiguity-resolution principle (default to more
scrutiny when a reading is not unambiguous), this result is treated
here as the stricter "moderate correlation" case rather than "low,"
which requires a written economic explanation before Gate 1 can be
considered satisfied — an explanation that was already written and
frozen, before this measurement was made, in
`attempt_001_specification.md` Section 4. A secondary, more decision
-relevant finding — bottom-rank overlap (median 40%, roughly double the
~20% chance baseline) markedly exceeding top-rank overlap (median 20%,
at chance) — is disclosed as a specific, unresolved observation
requiring independent reviewer attention, not adjudicated here.

This report does **not** constitute a governance-final Gate 1 PASS.
`docs/REFERENCE_H3_PREVALIDATION_PLAN.md` Section 4 requires the
rank-correlation and score-overlap calculation to be **independently
reproduced** — not merely inspected — by a reviewer with no role in
performing it, before the gate counts as satisfied. This report and the
calculation it documents were produced in a single session with no such
independent reproduction. The next allowed action is that independent
confirmation, in the same Level 2 (AI-assisted adversarial,
procedurally-but-not-organizationally independent) format already used
for Gates 2 and 3 in this archive.

---

## 2. Freeze Verification

| Field | Value | Verified |
|---|---|---|
| Freeze commit (full) | `07f0da379d8cccf06d17c34a51cbb557da047fef` | `git cat-file -t` confirms object exists; `git rev-parse 07f0da3` resolves to this exact hash |
| Current repository HEAD | `149ae44` (one commit ahead) | `git log --oneline -3` |
| Drift check: HEAD vs. freeze commit, for every file the freeze covers | **None** | `git diff 07f0da3 HEAD -- <frozen files>` returns empty for `attempt_001_specification.md`, `docs/REFERENCE_H3_PREVALIDATION_PLAN.md`, `docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md`, `docs/RESEARCH_GOVERNANCE_STANDARD.md` |
| Working tree vs. freeze commit | Clean; `git status --short` shows only the two new artifacts this validation produced (analysis script and its JSON output) — no frozen file is modified or untracked | `git status --short` |
| Methodology version in effect | `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` as committed at `07f0da3` (Section 2's "Frozen methodology summary" table) | Read directly |

**Frozen artifacts used, exactly as committed at `07f0da3`:**
- `research_archive/reference_h3/attempt_001_specification.md` — construction (universe, Section 3.1; six-segment peer grouping, Section 3.2; score formula and 60-day lookback, Section 3.5; missing-data rule, Section 3.9).
- `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` — Gate 1 methodology (Section 2) and evaluation-window/benchmark definition (Section 2's "Frozen methodology summary" table).
- `research_archive/reference_v1/reference_v1_significance_report_2026-07-18.json` — the source of the frozen evaluation window (`period_start`/`period_end`) and of REFERENCE v1's identity (`"REFERENCE" v1`, MOMENTUM = `SMA(20)`, unnormalized).

**No mismatch found.** Repository state matches the cited freeze
reference exactly.

---

## 3. Data Validation

**Source.** `experiments_etf_universe.db` (SQLite), the same live
research database Gate 2 already certified.

**Price coverage (`PriceBar`).** 2016-09-13 to 2026-07-17, 61,850 rows
= 25 ETFs × 2,474 trading days, 0 missing / 0 surplus per
`gate2_independent_review_2026-07-19_post_remediation.md` (re-verified
here only by row-count spot check, not re-run in full — Gate 2's
certification is reused, not redone, consistent with "reuse existing
evidence, don't silently re-litigate a passed gate").

**Score/MOMENTUM coverage (`Score`, `DimensionScore`).** A material,
previously undocumented gap was found and is disclosed here rather
than silently worked around:

- REFERENCE v1's own evaluation window is nominally 2024-07-17 to
  2026-07-17 — **502 XNYS trading days**.
- No `Score` row exists in the database for any of the **19 XNYS
  trading days from 2024-07-17 through 2024-08-12 inclusive** (verified
  directly: `SELECT session_date, COUNT(*) FROM Score WHERE
  session_date BETWEEN '2024-07-17' AND '2024-08-13' GROUP BY
  session_date` returns zero rows before `2024-08-13`, where all 25
  ETFs first appear together).
- This is **not** an H3-side limitation: H3's own 60-trading-day
  lookback is satisfied for every date in the window many times over,
  since price history begins in 2016. The gap is entirely on the
  MOMENTUM/`Score` side of the database.
- **Consequence:** Gate 1 evaluates **483 of the nominal 502 window
  dates (96.2%)**. This is disclosed as a genuine reproducibility
  limitation of the underlying dataset, not repaired by backfilling
  Score rows for those 19 dates as part of this validation (doing so
  would mean this report silently changed the data the frozen
  methodology runs against, mid-execution — out of scope for a
  validation run, and a decision for whoever maintains the Score
  backfill pipeline, not this report).

**Reproducibility.** The script that produced every figure in this
report — `experiments/validate_h3_gate1_independence.py` — is
committed alongside this report's evidence file
(`research_archive/reference_h3/gate1_independence_analysis_2026-07-19.json`)
so a reviewer can re-run it byte-for-byte against the same database
state and obtain identical output (deterministic: no random sampling,
seed, or permutation is used anywhere in this calculation).

**No anomaly found** in the evaluated 483 dates beyond the coverage gap
above (checked: `n_etfs` per evaluated date is 25 for every date in the
output, i.e. no partial cross-sections occurred once a date qualified).

---

## 4. Methodology Execution

**Exact calculation performed**, per `REFERENCE_H3_PREVALIDATION_PLAN.md`
Section 2 and `attempt_001_specification.md` Section 3.5:

1. **H3 score.** For each ETF *i* in segment *S(i)*, on each trading
   date *t*: `own_return_i(t)` = cumulative close-to-close log return
   over the trailing 60 trading days ending at *t*
   (`ln(close_i(t) / close_i(t-60))`, 60-trading-day index offset, not
   calendar days). `peer_return_i(t)` = equal-weighted mean of
   `own_return_j(t)` over other members *j* of *S(i)*.
   `H3_score_i(t) = own_return_i(t) - peer_return_i(t)`. Missing-data
   rule (Section 3.9) enforced exactly: an ETF is excluded from a
   date's cross-section unless both its own 60-day return and at least
   one peer's are resolvable — no forward-fill, no interpolation.
2. **MOMENTUM score.** Read directly from the existing, already
   -computed `DimensionScore` rows for REFERENCE v1 (`SMA(20)`,
   unnormalized price level) via the platform's existing
   `generate_ranked_etf_report()` — not recomputed, not reimplemented.
3. **Daily Spearman rank correlation** between the two scores' 25 (or
   fewer, per the missing-data rule) ETF values on each date, using the
   platform's existing average-rank-tie-handling implementation
   (`experiments/validate_reference_v1_significance.py`'s
   `_rank_average_ties`/`_pearson`/`_spearman`, imported unchanged).
4. **Score overlap at the extremes.** Top-5 and bottom-5 ETFs by each
   score, on each date; overlap fraction = shared members ÷ 5.

**Parameters (all frozen, none chosen for this run):**
- Evaluation window: 2024-07-17 to 2026-07-17 (REFERENCE v1's own
  analysis window — Section 2's frozen "Benchmark"/"Evaluation basis"
  rows).
- H3 lookback: 60 trading days (`attempt_001_specification.md`
  Section 3.5).
- Bucket size for overlap: **5** — an interpretive choice, disclosed
  per the mandatory-ambiguity-documentation rule: Section 2's "score
  overlap analysis" specifies comparing rank extremes but states no
  numeric bucket size itself. `5` is not invented for this report; it
  is this platform's own already-frozen convention, used throughout
  `validate_reference_v1_significance.py` and named directly in
  `attempt_001_specification.md` Section 3.7 as the convention "a
  future... top-vs-bottom comparison... would reuse... rather than a
  new bucket size chosen for H3." This is reuse of an existing frozen
  parameter, not a new one selected for this validation — but it is
  still flagged here as an interpretive gap in Section 2 itself for a
  future methodology revision to consider closing explicitly.

**Assumptions:** none beyond the frozen documents. No parameter was
tuned, no alternative window was tried, no date range was substituted
after seeing results.

---

## 5. Results

### 5.1 Daily Spearman correlation (H3 score vs. MOMENTUM score)

| Statistic | Value |
|---|---|
| n (dates) | 483 |
| Mean | 0.1008 |
| Median | 0.1085 |
| P25 | -0.0362 |
| P75 | 0.2292 |
| Min | -0.3223 |
| Max | 0.4515 |

### 5.2 Score overlap at the extremes (bucket size 5 of 25)

| Statistic | Top-5 overlap fraction | Bottom-5 overlap fraction |
|---|---|---|
| n (dates) | 483 | 483 |
| Mean | 0.2017 | 0.3379 |
| Median | 0.20 | 0.40 |
| Chance baseline (5/25, independent random rankings) | 0.20 | 0.20 |

### 5.3 "Benchmark comparison" (per Section 0's terminology reconciliation)

The frozen "Benchmark" for Gate 1 is REFERENCE v1's MOMENTUM score
itself — Sections 5.1–5.2 above **are** the complete benchmark
comparison the frozen methodology defines. No market index or
buy-and-hold comparison exists in, or is authorized by, this phase.

---

## 6. Risk Assessment

- **Overfitting / researcher-degrees-of-freedom risk: low, by
  construction.** This is Attempt 1 of the Plan's maximum of 3; the
  construction was frozen (commit `07f0da3`) before any Gate 1 figure —
  including the ones in this report — was computed, and the pre-log
  attestation in `attempt_001_specification.md` Section 5 discloses the
  four alternative constructions considered and rejected on economic
  grounds alone, before any correlation was measured. This report
  changed nothing about the construction to produce a more favorable
  number.
- **Data limitation: single historical regime, ~2-year window.** The
  483 evaluated dates span roughly two years (2024-08 to 2026-07) — one
  historical period, not multiple independent regimes. This mirrors the
  same effective-sample-size caveat already recorded for REFERENCE v1
  and REFERENCE v2 H1 in this archive; Gate 1's own correlation
  read-out does not, by itself, say anything about how stable this
  relationship would be in a different regime.
- **Statistical uncertainty is material, not a footnote.** The
  interquartile range of the daily correlation (-0.036 to +0.229)
  straddles zero — the *sign* of the relationship is not stable
  day-to-day, only its central tendency is mildly positive. Reporting
  only the median without this spread would overstate how settled this
  reading is.
- **Unresolved, specific finding: bottom-tail overlap asymmetry.**
  Bottom-5 overlap (median 40%) is roughly double top-5 overlap (median
  20%, at chance). This is exactly the failure mode the Plan itself
  warns a bare correlation coefficient can hide ("a moderate overall
  correlation can still hide near-total overlap... at the tails,"
  Section 2). This report does not explain this asymmetry — doing so
  would require either new analysis (out of this report's scope, which
  is measurement, not interpretation-that-resolves-ambiguity) or
  drawing on `attempt_001_specification.md` Section 3.10's disclosed
  2-member Global equity segment as a partial structural candidate
  explanation, which is speculative and not confirmed here. Flagged
  for the required independent reviewer.
- **Implementation risk: low.** `Decimal` values are converted to
  `float` only at the point they enter the correlation/overlap
  arithmetic (same precision-boundary convention already used in
  `validate_reference_v1_significance.py`), and every date in the
  evaluated set has a full 25-ETF cross-section (verified, not
  assumed) — no silent partial-cross-section distortion is present in
  the reported distributions.
- **Independent-confirmation gap (the primary outstanding risk to this
  report's own status).** Per Section 4 of the Plan, this gate requires
  a procedurally distinct reviewer to *independently reproduce* — not
  inspect — these figures before Gate 1 counts as satisfied. That has
  not occurred. This report and its underlying calculation were
  produced in one session with no organizational or procedural
  separation from itself, which is a disclosure this project's own
  governance standard (`docs/RESEARCH_GOVERNANCE_STANDARD.md` Section
  4) requires to be stated explicitly rather than left for a reader to
  assume.

---

## 7. Final Determination

**PASS on the measured quantitative evidence; NOT a governance-final
Gate 1 PASS.**

**Evidence supporting this determination:**
- The construction is unambiguously and by a wide margin clear of the
  Plan's one hard, mathematically provable rejection trigger (near-1.0
  median correlation to the degenerate single-benchmark-subtraction
  case): observed median 0.108, mean 0.101, max 0.452 — nowhere near
  1.0.
- The observed low-to-moderate positive correlation was
  literature-anticipated and pre-registered *before* this measurement:
  `attempt_001_specification.md` Section 4 states, in advance, "some
  resulting positive correlation between the two scores is expected and
  literature-anticipated," because both scores are ultimately derived
  from the same underlying price history. The measured result is
  consistent with that pre-registered expectation, not a surprise
  requiring a new, after-the-fact rationalization.
- Applying the Plan's own ambiguity-resolution principle (default to
  the stricter reading when a boundary is not unambiguous), this result
  is treated as the "moderate correlation" case, which requires a
  written economic explanation before Gate 1 is satisfied — and that
  explanation already exists, pre-dating this measurement, in the same
  Section 4 cited above.

**Remaining limitations (not resolved by this report, by design):**
1. **Independent reproduction has not occurred.** This is the binding
   gap. Per Section 4 of the Plan, Gate 1 does not count as satisfied
   until a procedurally distinct reviewer independently recomputes
   these figures from the written record — this report, the committed
   analysis script, and the frozen documents — and confirms they match.
2. **The bottom-tail overlap asymmetry (Section 6) is unexplained**,
   not merely undocumented — it is a specific, disclosed open question
   for that independent reviewer, not resolved here.
3. **19 of 502 nominal window dates could not be evaluated** due to a
   `Score`-table coverage gap at the start of REFERENCE v1's own
   window (Section 3) — disclosed, not repaired, as part of this
   validation.
4. Gate 4 (no unresolved specification degrees of freedom) was not
   assessed by this report — out of this report's scope, which is Gate
   1 only.

**Next allowed action.** Per this project's own governance
(`docs/REFERENCE_H3_PREVALIDATION_PLAN.md` Section 4), the correct next
step is an independent (Level 2: AI-assisted adversarial, procedurally
distinct from this session) review that: (a) reviews the full
construction attempt log; (b) confirms no outcome data was read or
computed anywhere in this work (true here — no forward return, IC, or
p-value appears anywhere in this report or its underlying script); (c)
confirms REFERENCE v1/H1 results did not influence H3's construction
(already attested in `attempt_001_specification.md` Section 5, prior to
this report); (d) **independently reproduces** Sections 5.1–5.2 above
from `experiments/validate_h3_gate1_independence.py` and the frozen
inputs, arriving at its own matching figures; and (e) records that
confirmation in the archive, in the same format as
`gate2_independent_review_2026-07-19_post_remediation.md` and
`gate3_independent_review_2026-07-19.md`. Only after that confirmation
should `research_archive/reference_h3/decision_log.md` and
`research_archive/reference_h3/README.md` be updated to record Gate 1
as formally satisfied — neither was modified by this report, per the
"do not resolve ambiguity by changing the methodology or the record"
rule and per this report's own PASS being explicitly non-final.

**No H3 methodology, scoring logic, parameter, benchmark, universe, or
acceptance criterion was modified, tuned, or reinterpreted to produce
this determination.**

---

## Evidence artifacts produced by this report

- `experiments/validate_h3_gate1_independence.py` — the analysis
  script (new file; does not modify any existing code).
- `research_archive/reference_h3/gate1_independence_analysis_2026-07-19.json`
  — full machine-readable output, including per-date results for all
  483 evaluated dates.
- This report.

No existing frozen file was modified to produce this report.
