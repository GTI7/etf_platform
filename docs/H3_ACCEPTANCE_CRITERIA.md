# H3 Acceptance Criteria — Pre-Registered Economic Evidence Standard

**Author role.** Institutional Quant Research Acceptance Criteria
Architect. This document defines decision rules only. It does not
develop, tune, run, or improve H3's construction; it does not compute,
read, or reference any forward return, Information Coefficient,
p-value, Sharpe ratio, drawdown, or any other outcome/performance
figure for H3. No such figure exists yet for H3 anywhere in this
platform's archive, per
[`docs/H3_ECONOMIC_EVIDENCE_VALIDATION_REPORT.md`](H3_ECONOMIC_EVIDENCE_VALIDATION_REPORT.md)
§1, and none was consulted, estimated, or informally previewed in
producing this document.

**Status: pre-registered, written before Phase 6 (Validation).** Under
this platform's eight-phase lifecycle
([`docs/RESEARCH_GOVERNANCE_STANDARD.md`](RESEARCH_GOVERNANCE_STANDARD.md)
§2), H3 has completed Phase 3 (Pre-validation: Gates 1–4, all PASS —
[`docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md`](H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md),
[`docs/H3_GATE4_DEGREES_OF_FREEDOM_AUDIT.md`](H3_GATE4_DEGREES_OF_FREEDOM_AUDIT.md))
and has not yet entered Phase 6, where outcome data may first be
touched. This document is the acceptance-criteria component of Phase 4
(Methodology Freeze) — specifically item 8 of the eight-element freeze
checklist (`RESEARCH_GOVERNANCE_STANDARD.md` §3) — and, because two
prerequisite design choices for stating a measurable criterion (the
forward holding horizon and the portfolio-formation logic) were
explicitly and deliberately left open by the frozen construction
(`research_archive/reference_h3/attempt_001_specification.md` §3.7–3.8,
"not computed or implemented by this document... a future,
separately-scoped validation phase"), this document also resolves
those two items, on the same non-outcome basis required of every
other frozen element.

**What this document is not.** It is not Gate 1's independence check
(already closed, PASS, not reopened here). It is not an implementation.
It is not a backtest. It selects no "best" construction — H3's
construction remains exactly as frozen in `attempt_001_specification.md`
§3, unmodified. Every design choice below is justified on economic,
procedural, or platform-consistency grounds stated *before* any result
exists — never on an expectation of what result would make H3 look
favorable.

---

## 0. How to read this document

Sections 1–5 answer the five questions this task requires, in the
order requested. Section 6 states the freeze and immutability rule
that makes these criteria binding once Phase 6 begins. Section 7 is a
single consolidated table of every criterion in this document marked
**UNRESOLVED** — items that cannot be honestly fixed without inventing
an arbitrary number, per this task's own instruction. Section 8 is a
fillable decision-record template, mirroring the pattern already
established in `REFERENCE_H3_PREVALIDATION_PLAN.md` §7.

---

## 1. Primary objective

### 1.1 Main hypothesis test

H3's frozen claim (`attempt_001_specification.md` §1) is that an ETF's
relative standing versus its own peer segment — not its absolute
return — persists in the near term. The most direct, minimal-new-
construction test of that specific claim is **autocorrelation of the
frozen H3 score itself**, evaluated forward in time, rather than
inventing a new outcome variable:

> **H3-A (primary statistic).** Daily cross-sectional Spearman rank
> correlation between `H3_score_i(t)` (as frozen,
> `attempt_001_specification.md` §3.5) and `H3_score_i(t + 60
> trading days)` — the identical score formula, computed on the same
> ETF, 60 trading days later — one correlation per date, averaged
> across ranking dates, never pooled (consistent with this platform's
> standing discipline against pooling ETF-days into a single
> statistic).

This is chosen over defining a new "forward peer-relative return"
outcome variable because, at the primary horizon (60 trading days,
Section 2.1), the score computed at `t + 60` is constructed from the
trailing-60-day window `[t, t+60]` — contiguous with, and
non-overlapping against, the window `[t-60, t]` underlying the score
at `t`. Testing `H3_score_i(t)` against `H3_score_i(t+60)` is therefore
already exactly a test of "does this quarter's relative standing
predict next quarter's relative standing," using zero new formulas,
zero new parameters, and reusing Gate 1's own already-reviewed
correlation methodology (`docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §2)
— only forward-shifted instead of same-date. This minimizes researcher
degrees of freedom relative to any alternative construction of the
outcome variable.

> **H3-B (secondary / diagnostic statistic).** Top-vs-bottom portfolio
> spread: rank the full 25-ETF universe by `H3_score_i(t)` on each
> date, form a long position in the top-`bucket_size` ranked ETFs and
> a short position in the bottom-`bucket_size` ranked ETFs
> (`bucket_size = 5`, inherited unmodified from
> `docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md` Part 6's
> minimum-panel convention — not a new bucket size chosen for H3, per
> `attempt_001_specification.md` §3.7), and measure the spread between
> the mean forward raw return of the long leg and the mean forward raw
> return of the short leg over the same 60-trading-day horizon.

H3-A answers the literal persistence-of-standing question the
hypothesis makes. H3-B answers the practical, investability-adjacent
question ("would acting on this rank have produced a return spread")
without yet asserting anything about implementation cost (Section 3.3).
This primary/secondary structure mirrors the H1-A/H1-B pattern already
established for REFERENCE v2 H1 — a primary statistic that directly
tests the stated mechanism, and a secondary statistic offering a
different, corroborating lens, with the promotion rule (Section 5)
stating explicitly which one governs the decision when they diverge.

### 1.2 Benchmark comparison

Three distinct comparisons apply, and must not be conflated:

1. **Statistical null.** Both H3-A and H3-B are tested against zero
   (no persistence / no spread) via permutation (Section 4.1) — the
   standard null for a correlation or a long-short spread.
2. **Economic benchmark for H3-B only.** The zero-skill capital
   benchmark for the long-short spread is an equal-weighted,
   buy-and-hold position in the full 25-ETF universe over the same
   holding horizon — not a cash return, not a risk-free rate, since
   the spread itself is already long-short and self-financing in
   direction (though not in transaction cost — see Section 3.3). This
   benchmark answers "does the spread exceed the noise floor implied
   by simply holding the universe," not "does H3 beat holding the
   universe outright" (a long-short spread and a long-only benchmark
   are not directly netted against each other; the comparison is
   reported, not differenced, per Section 3.2).
3. **Not a re-run of Gate 1.** Gate 1's MOMENTUM comparison
   (`docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md`) already closed
   the *independence* question (median Spearman correlation 0.108,
   PASS) and is not reopened, re-weighted, or re-litigated by this
   document. This document's benchmark comparisons test *economic
   value*, a question Gate 1 explicitly and repeatedly disclaimed
   addressing (`docs/H3_ECONOMIC_EVIDENCE_VALIDATION_REPORT.md` §2,
   "Gate 1 vs. economic validation — kept distinct").

---

## 2. Return criteria

### 2.1 Required measurement period (holding horizon)

**Dual-horizon design, primary horizon governs the decision:**

| Horizon | Role | Justification (non-outcome) |
|---|---|---|
| **60 trading days** | **Primary** — governs Section 5's decision | Matches the mechanism's own stated cadence: Gate 3's economic rationale (`docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md` §3) explicitly cites a "quarterly or annual committee cycle" as the source of the reallocation lag, and the frozen score's own 60-day lookback (`attempt_001_specification.md` §3.5) was independently justified on the identical cadence argument. Using the same 60-day period for the forward test that the mechanism itself names avoids introducing a horizon disconnected from the claimed economics. |
| **20 trading days** | **Secondary / diagnostic only** — reported, never decision-relevant | Reused, unmodified, from the platform-standard forecast horizon already fixed for REFERENCE v1 and REFERENCE v2 H1 (`docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md` Part 4). Included solely for cross-hypothesis comparability with prior cycles, not because any economic argument specific to H3 favors 20 days — the specification itself already rejected letting MOMENTUM's window shape H3's own parameters for exactly this reason (`attempt_001_specification.md` §3.5). |

Fixing two horizons rather than sweeping across several avoids the
"tested at multiple lengths, selected after seeing which produces a
more favorable result" failure mode this platform's own prior
specification explicitly disclaims
(`docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md` Part 3). Both
are fixed now, by this document, before Phase 6 begins; neither may be
added to, removed, or substituted once Validation starts (Section 6).

### 2.2 Evaluation period

The dataset window is reused, not re-selected: the same window already
established through Gate 1
(`docs/H3_GATE1_REPRODUCTION_REVIEW.md`, 2024-08-13 to 2026-07-17, 483
of 502 nominal dates usable after the disclosed `Score`-table gap,
`docs/H3_GATE4_DEGREES_OF_FREEDOM_AUDIT.md` Matrix row 6). At the
60-day primary horizon, the last 60 trading days of this window cannot
produce a forward-shifted score and are mechanically excluded from the
H3-A panel — a data-availability consequence of the frozen window, not
a discretionary trim.

**Effective sample size (disclosed, not a threshold).** At a 60-day
non-overlapping forward horizon, the ≈483 usable ranking dates imply
roughly 483 ÷ 60 ≈ 8 truly independent windows — consistent with, and
no larger than, the effective-sample-size problem already disclosed as
H3's motivating risk
(`docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §5, "Insufficient
independent observations, regardless of A/B/C"). This is reported here
as required context for interpreting Section 4's confidence intervals
— a small effective sample size does not itself fail a criterion, but
a reviewer must not read a narrow bootstrap interval at this sample
size as more conclusive than 8 independent windows can actually support.

### 2.3 Minimum acceptable excess return

This splits into a **statistical bar** (resolved below) and an
**economic materiality bar** (partially unresolved — see Section 7):

- **Statistical bar (resolved).** H3-A's IC and H3-B's spread must each
  be statistically distinguishable from zero per Section 4's
  significance and confidence-interval rules. This is necessary but,
  on its own, not sufficient to call H3 "economically supported" — a
  statistically significant but economically negligible spread is a
  real, distinct outcome this document must not collapse into "PASS."
- **Gross economic bar (resolved).** Conditional on clearing the
  statistical bar, H3-B's realized long-short spread over the primary
  60-day horizon must be **positive in the direction the hypothesis
  predicts** (long top-ranked, short bottom-ranked) at the point
  estimate, and its bootstrap confidence interval (Section 4.2) must
  exclude zero at all three required block lengths. A statistically
  significant spread of the *wrong* sign is not a milder form of
  support — see Section 5's terminal conditions.
- **Net-of-implementation-cost bar: UNRESOLVED.** See Section 3.3 and
  Section 7. No transaction-cost, turnover, borrowing-cost, or
  capacity model exists anywhere on this platform
  (`docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md`: "No transaction costs or
  implementation frictions modeled at any point in either script").
  Inventing a specific basis-point hurdle now, with no documented cost
  basis, would be exactly the kind of arbitrary threshold this task
  instructs against. A PASS under this document (Section 5) is
  therefore a research conclusion about gross, pre-cost economic
  evidence only — not an investability conclusion — until a
  separately-scoped cost/capacity study closes this gap.

### 2.4 Treatment of uncertainty

Every reported statistic is a point estimate plus a block-bootstrap
confidence interval (Section 4.2), never a point estimate alone. A
result whose interval includes zero at any one of the three required
block lengths is treated as **not clearing** the return criterion,
regardless of the point estimate's sign or magnitude, and regardless of
how narrowly it misses — this is the same "ambiguity resolves to the
stricter reading" default already established platform-wide
(`docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §2, "General
ambiguity-resolution principle").

---

## 3. Risk criteria

### 3.1 Drawdown considerations — UNRESOLVED (numeric threshold); resolved (reporting requirement)

With only ≈2 years of single-regime history behind any H3 return
series that Phase 6 would produce
(`docs/H3_ECONOMIC_EVIDENCE_VALIDATION_REPORT.md` §5, "Single ~2-year
historical regime"), no maximum-drawdown ceiling can be honestly
pre-registered as a numeric pass/fail threshold — any such number would
be calibrated against a distribution that has not been observed even
once at this horizon (≈8 independent 60-day windows, Section 2.2).
Setting one now would be exactly the kind of criterion "chosen based on
expected outcomes" this task prohibits. Consistent with this
platform's own treatment of regime coverage as qualitative, not a
precise figure
(`docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §3, "Regime coverage"):

- **Required (resolved):** Phase 6 must report the realized
  peak-to-trough drawdown of the H3-B long-short spread, and of each
  leg individually, over the full evaluation window, as descriptive
  output — with no associated pass/fail threshold in this document.
- **Not required:** a specific drawdown percentage as an acceptance
  criterion. See Section 7.

### 3.2 Volatility limits — UNRESOLVED (numeric ceiling); resolved (reporting requirement + non-applicability note)

For the same reason as 3.1, no volatility ceiling can be pre-registered
from non-outcome reasoning alone. Note explicitly: the cross-sectional
coefficient-of-variation GO/NO-GO check used for REFERENCE v2 H1
(`docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md` Part 5) is
**not transferable here** — that check tests dispersion of a
*volatility-based score variable* pre-Implementation; H3's score is a
*return-based* variable, and the analogous pre-registrable quantity
would be a dispersion check on H3-score cross-sectional spread, which
is a Gate-1-adjacent construction question, not a Phase 6 return-risk
criterion, and is out of this document's scope.

- **Required (resolved):** Phase 6 must report the realized annualized
  volatility of the H3-B spread and of each leg, descriptively.
- **Not required:** a numeric ceiling as a pass/fail gate. See Section 7.

### 3.3 Implementation risks (resolved — structural, known in advance)

Unlike 3.1–3.2, the following are knowable from the frozen construction
and this platform's own documented state, without touching any outcome
figure, and are therefore fixed now:

- **Minimum panel size.** A ranking date is included in either
  statistic's cross-sectional calculation only if at least **10 ETFs**
  have valid score data (`attempt_001_specification.md` §3.9) *and*
  valid forward-outcome data on that date — `bucket_size × 2 = 10`,
  reused unmodified from
  `docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md` §6. Dates
  below this are excluded entirely, not down-weighted or imputed.
- **Global-equity segment concentration (disclosed structural weak
  point).** The 2-member Global equity segment (`VT`, `ACWI`,
  `attempt_001_specification.md` §3.10) means any ETF in that segment's
  peer-relative score is driven by a single peer. Any Phase 6 report
  under this document must separately compute and disclose H3-A and
  H3-B **with and without** Global-equity-segment members, so a reader
  can see whether the result is disproportionately carried by this
  structurally weak segment. This is a reporting requirement, not a
  pass/fail gate on its own.
- **No transaction-cost, turnover, or capacity model exists on this
  platform** (Section 2.3). Any PASS recorded under this document
  (Section 5) must state explicitly, in the decision record, that it
  is a gross-of-cost, research-only conclusion — not an investability
  or capital-allocation conclusion — until a separate cost/capacity
  study exists. Omitting this statement in a decision record that
  reaches PASS is itself a governance gap under
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §7's documentation
  requirements.
- **No Level 3 (organizationally independent) review exists on this
  platform**, for H3 or any prior cycle
  (`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4). Any Decision reached
  under this document is a Level 2 (procedurally independent, not
  organizationally independent) decision at most, and the decision
  record must say so explicitly, in those terms — never the
  unqualified word "independent" — per the Standard's own requirement.

---

## 4. Statistical criteria

### 4.1 Significance requirements

Within-date permutation test: the score is shuffled within each date,
the outcome held fixed, **10,000 iterations minimum**, computed
separately for H3-A and H3-B, each with its own independent shuffle
series — reused unmodified from
`docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md` §6.

### 4.2 Confidence thresholds

"Passes," for either statistic, means, identically to the platform's
existing convention (REFERENCE v1, REFERENCE v2 H1):

> Holm-Bonferroni-adjusted **p < 0.05** **and** the block-bootstrap
> confidence interval excludes zero **at all three** block lengths
> (20, 40, and 60 trading days; 2,000 iterations minimum per block
> length), subject to the undefined-statistic handling rule below.

Block-bootstrap structure (contiguous whole-date blocks, identical to
REFERENCE v1's and REFERENCE v2 H1's construction) is reused
unmodified — no new resampling scheme is introduced for H3.

### 4.3 Multiple testing

Holm-Bonferroni correction is applied jointly across exactly the
2-statistic family **{H3-A, H3-B}**, at the primary 60-day horizon
only — sorted ascending by raw p-value, adjusted `p = min((n − rank) ×
raw p, 1.0)`, `n = 2`. This family is fixed by this document before
either statistic is computed and may not be reweighted, expanded, or
narrowed afterward. The secondary 20-day diagnostic statistics
(Section 2.1) are explicitly **excluded** from this correction family
and from any decision rule, precisely because they are reported for
comparability only, not tested for promotion — including a
non-decision-relevant statistic inside the correction family would
dilute the correction applied to the two that actually govern the
decision.

### 4.4 Reproducibility and undefined-statistic handling

- **Fixed seed.** A single, fixed, documented random seed for all
  permutation and bootstrap procedures, selected and recorded before
  any Phase 6 result is generated or examined. The literal seed value
  is an implementation detail, not fixed by this document.
- **Undefined statistics automatically fail.** An undefined permutation
  p-value, or a bootstrap confidence interval that cannot be computed
  at a given block length (e.g., due to an insufficient number of
  usable resampled estimates — plausible at this platform's small
  effective sample size, Section 2.2), automatically fails that
  criterion. No manual interpretation or case-by-case judgment is
  permitted — reused unmodified from the platform's existing
  convention.

---

## 5. Failure conditions

### 5.1 Decision table (primary 60-day horizon governs)

| H3-A (primary, 60d) | H3-B (secondary, 60d) | Outcome |
|---|---|---|
| Passes (correct sign, Section 4.2) | Passes (correct sign, Section 4.2) | **Economically supported (gross-of-cost).** Both the direct persistence test and the portfolio-spread diagnostic confirm the hypothesis's stated direction. Proceed per Section 6's next-step note; net-of-cost investability remains open (Section 2.3, 3.3). |
| Passes | Fails | **Economically supported on H3-A alone**, since H3-A is the pre-registered primary statistic testing the literal hypothesis. The H3-A/H3-B divergence must be explicitly explained in the decision record, not silently dropped — mirrors `docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md` Part 6's identical rule for H1-A/H1-B. |
| Fails | Passes | **Not economically supported.** H3-B passing alone is insufficient — the primary persistence test did not clear the bar. Recorded distinctly as "portfolio spread observed, primary persistence test not confirmed," a real, preserved finding, not a promotion trigger. |
| Fails | Fails | **FAIL.** Archive under `docs/RESEARCH_GOVERNANCE_STANDARD.md` §7's FAIL discipline. |

### 5.2 Terminal failure — when H3 is considered unsupported

H3 is terminally unsupported, requiring FAIL or an explicit
"evidence against" record (below), if **any** of the following:

1. The decision table above resolves to FAIL (both statistics fail).
2. **Significant reversal.** Either H3-A or H3-B is Holm-Bonferroni
   significant *in the direction opposite* the hypothesis's stated
   prediction (i.e., relative standing significantly reverses rather
   than persists). This is not a milder finding than a plain FAIL — it
   must be recorded as **evidence against** the mechanism, not
   neutral, because Gate 3's own falsification criteria already state
   that reversal, not mere non-continuation, is what would count
   against this mechanism (`attempt_001_specification.md` §2,
   "Expected persistence mechanism"; the same falsification logic
   Gate 3's rationale document establishes).
3. Either statistic is undefined at a required block length (Section
   4.4) and cannot be resolved by the fixed methodology — treated as a
   failure of that criterion, not an exception.

### 5.3 When further optimization is prohibited

The moment any of Section 5.2's conditions is reached, the same
terminal-failure discipline this platform already applies platform-wide
(`docs/RESEARCH_GOVERNANCE_STANDARD.md` §7) binds without exception:

1. **Research under H3's exact frozen construction stops immediately**,
   other than Phase 8 archive steps.
2. **No tuning to force a different outcome.** No lookback, segment
   boundary, benchmark, peer-averaging method, bucket size, holding
   horizon, or any other parameter — frozen either in
   `attempt_001_specification.md` §6 or in this document — may be
   adjusted on the failed result in an attempt to convert it into a
   PASS. Any such change is a new construction attempt or a new cycle,
   never a correction.
3. **No alternative evaluation period may be substituted after the
   fact.** The dataset window (Section 2.2) and both horizons (Section
   2.1) are fixed by this document before Phase 6; none may be swapped
   for a different window, date subset, or horizon in search of one
   where the same construction would have passed.
4. **No criterion in this document may be relaxed or reinterpreted**
   after seeing the Phase 6 result that triggered the failure —
   including Section 4.2's confidence-interval rule, Section 3.3's
   cost-disclosure requirement, or Section 5.1's decision table itself.
5. A future proposal touching relative-strength or rotation-style ideas
   again is only legitimate as a wholly new cycle from Phase 1 that
   explicitly engages with H3's archived evidence and states, in
   writing, why it is a genuinely different hypothesis — not a
   renamed or restarted H3 attempt (`docs/REFERENCE_H3_PREVALIDATION_PLAN.md`
   §6, "Terminal rule," generalized platform-wide by
   `docs/RESEARCH_GOVERNANCE_STANDARD.md` §7).

### 5.4 INCONCLUSIVE (narrow, not a relabeled retry)

Reserved for the two circumstances `docs/RESEARCH_GOVERNANCE_STANDARD.md`
§7 already defines platform-wide: a Validation result whose ambiguity
Section 4's own rules cannot cleanly resolve despite being applied
exactly as written, or a statistical-power limitation (e.g., the
minimum-panel-size rule, Section 3.3, eliminating enough dates to make
either statistic undefined project-wide) discovered only during
Validation and not knowable at this freeze. INCONCLUSIVE is not a
mechanism for retrying the same construction with adjusted parameters
under a friendlier label, and defaults to FAIL's terminal discipline
for reopening purposes unless a specific, Level-2-or-above-reviewed
justification for leniency is documented at the time.

---

## 6. Freeze and immutability

This document fixes, as of the version in effect when Phase 6
(Validation) first reads any H3 outcome figure: both holding horizons
(Section 2.1), the evaluation window (Section 2.2), the primary and
secondary statistics and their exact definitions (Section 1.1), the
benchmark comparisons (Section 1.2), the bucket size and minimum panel
size (Section 3.3), the full statistical machinery (Section 4), and the
decision table and terminal conditions (Section 5).

Per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §3, "How changes are handled
after freeze": any change to any element above, after this document's
freeze commit, for any reason — including a reason discovered while
reviewing a Phase 6 result — is not a revision. It is a new methodology,
requiring a new freeze commit and, unless still within the
pre-validation attempt cap, a new cycle from Phase 1. It must be
logged in `research_archive/reference_h3/decision_log.md`, stating
which element changed, why, and which prior freeze commit it
supersedes. Silence about such a change is itself a governance
violation under that standard, independent of whether the change was
substantively justified.

This document does not itself authorize Implementation or Validation
to begin. Per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2 (Phase 4), a
Level 2 confirmation that this freeze document is complete against
Section 3's eight-element checklist — and that no element here was
selected or adjusted using any outcome data — must be recorded before
the freeze is effective and before Phase 5 (Implementation) may begin.

---

## 7. Consolidated unresolved items

Everything in this document not listed below is fixed. These items
could not be justified from non-outcome reasoning alone and are left
open, per this task's own instruction, rather than filled with an
invented number:

| # | Item | Where discussed | Why unresolved | What would resolve it |
|---|---|---|---|---|
| 1 | Net-of-implementation-cost minimum excess return | §2.3, §3.3 | No transaction-cost, turnover, borrowing-cost, or capacity model exists anywhere on this platform (confirmed absent even for REFERENCE v1). Any specific basis-point hurdle set now would be an arbitrary number, not a justified one. | A separately-scoped cost/capacity study, producing a documented cost model this platform does not currently have — then a hurdle can be fixed non-arbitrarily. |
| 2 | Maximum-drawdown acceptance threshold | §3.1 | Only ≈8 independent 60-day windows of single-regime history exist; any numeric ceiling would be calibrated against a distribution never observed at this horizon. | Either a longer, multi-regime history (Option B/C-style extension, per the precedent in `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §3), or an explicit, separately-justified risk-tolerance policy set by whoever would allocate capital against this result — not a number this research-acceptance document can supply on its own. |
| 3 | Volatility ceiling on the H3-B spread | §3.2 | Same reasoning as #2; no pre-registrable numeric ceiling exists without assuming a return distribution not yet observed even once. | Same resolution path as #2. |

No other criterion in Sections 1–5 is left open. Where this document
made a design choice not previously frozen (the two holding horizons,
the bucket-size reuse, the H3-A/H3-B statistic definitions), the
justification given is procedural, economic-mechanism-based, or
platform-consistency-based — never an expectation of what result these
choices would produce.

---

## 8. Decision record template (fillable, not completed here)

Mirrors the pattern established in
`docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §7. Completed only once a
Phase 6 Validation result actually exists, by whoever is authorized to
close the cycle — not filled in speculatively, and not filled in by the
same party who ran Validation, per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4's independence disclosure
requirement.

---

**Determination:** ☐ Economically supported (H3-A+H3-B) ☐ Economically
supported (H3-A only) ☐ Not economically supported ☐ FAIL ☐ Evidence
against (reversal) ☐ INCONCLUSIVE

**Determination date:** _______________

**Reviewer(s) and independence level (Section 4 of
`RESEARCH_GOVERNANCE_STANDARD.md`):** _______________
*(state explicitly if Level 3 was unavailable, per that standard's
mandatory disclosure requirement)*

**Freeze commit of this document in effect:** _______________

**H3-A result (60d primary):** point estimate _____, Holm-Bonferroni
adjusted p _____, bootstrap CI (20/40/60d) _____

**H3-B result (60d primary):** point estimate _____, Holm-Bonferroni
adjusted p _____, bootstrap CI (20/40/60d) _____

**Diagnostic-only 20d results (not decision-relevant):** _______________

**Global-equity-segment sensitivity (Section 3.3):** _______________

**Gross-vs-net-of-cost disclosure (Section 2.3, 3.3):** _______________

**Synthesis rationale:** _______________
*(a short, written account of how the evidence led to the
determination — not left to be inferred from the individual statistic
results alone)*

---

## Sources reviewed

- `research_archive/reference_h3/attempt_001_specification.md`
- `docs/REFERENCE_H3_PREVALIDATION_PLAN.md`
- `docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md`
- `docs/RESEARCH_GOVERNANCE_STANDARD.md`
- `docs/H3_ECONOMIC_EVIDENCE_VALIDATION_REPORT.md`
- `docs/H3_GATE4_DEGREES_OF_FREEDOM_AUDIT.md`
- `docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md`
- `docs/H3_GATE1_REPRODUCTION_REVIEW.md`
- `docs/REFERENCE_V2_H1_LOW_VOLATILITY_SPECIFICATION.md` (Parts 3–8, statistical-machinery precedent)
- `docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md` (confirms no transaction-cost model exists on this platform)

No H3 methodology, scoring formula, parameter, universe, or segment
definition was modified, tuned, tested against an alternative, or
newly introduced by this document. No forward return, IC, p-value,
Sharpe ratio, drawdown, or other outcome figure was read, computed, or
referenced anywhere above; every threshold and rule is justified by
economic mechanism, procedural consistency, or platform precedent
stated before any such figure exists.
