# `reference_h2` — Phase 3: Pre-validation Plan

**Date:** 2026-07-28.
**Author:** Claude Sonnet 5 (this session), self-review only (Level 1 — see
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4). No outcome data (forward
return, risk-adjusted return, Information Coefficient, p-value, or any
other outcome variable) is touched anywhere in this document, per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §2, Phase 3's objective.

**Precedent basis.** This plan follows the gate structure and governing
disciplines `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` established
(signal independence, data adequacy, economic rationale, no unresolved
degrees of freedom; construction attempt log with a pre-stated cap and
mandatory pre-log attestation; independent-confirmation duties per gate),
not `research_archive/reference_h4/prevalidation_plan.md`'s simpler
structure. H4 tested a distributional property of returns with no
construction step, so its Gate 1 was correctly recorded as **N/A**. H2 is
a **constructed scoring signal** with real construction degrees of
freedom (formation window, skip length, return basis, dividend treatment,
ranking methodology, tie handling), exactly the situation H3's plan was
written for. H4's N/A pattern is not copied here; it does not fit this
cycle.

This document plans what future evidence must be produced and how. It
contains no completed gate result, no correlation figure, no data
inventory finding, and no economic-rationale determination. Every gate
below is a specification of required future work, not a report of work
already done.

---

## 1. Scope and authority

**Hypothesis under validation.** `reference_h2` — a candidate cross-
sectional scoring signal constructed from trailing cumulative return,
formed over a recent formation period that excludes a short skip interval
immediately preceding the ranking date (the general underreaction /
slow-information-diffusion mechanism stated in
`research_archive/reference_h2/hypothesis.md`, "Economic Mechanism").

**Current lifecycle phase.** PRE_VALIDATION. Per
`research_archive/reference_h2/transition_records.jsonl`, sequence 1
recorded the `RESEARCH_PROPOSAL → PRE_VALIDATION` transition. This is the
only transition recorded for `reference_h2` as of this document.

**What this plan authorizes.** This document authorizes only the
*planning* of Phase 3 work: it defines the gate structure, the
construction-attempt policy, and the evidence rules that future
Pre-validation work under this cycle must follow. Nothing in this
document itself constitutes Gate 1, 2, 3, or 4 evidence, and nothing here
satisfies any gate.

**What this plan does NOT authorize.**

- It does not authorize any construction attempt to be logged — that is a
  future, separate act under Section 2 below.
- It does not authorize Methodology Freeze (Phase 4). A Methodology
  Freeze document (`methodology.md`) is a distinct future artifact,
  produced only after every gate in Section 3 is satisfied.
- It does not authorize Implementation (Phase 5) of any scoring logic.
- It does not authorize any lifecycle transition. No `advance_phase()`
  call, no `DecisionRecord`, and no append to
  `research_archive/reference_h2/transition_records.jsonl` is made or
  implied by this document.
- It does not resolve any of the construction or methodology choices
  listed in `research_archive/reference_h2/hypothesis.md`'s "Known Open
  Questions" or `research_archive/reference_h2/research_proposal.md`
  §5's "Deferred Decisions Boundary" — Section 4 below restates that
  boundary for this document specifically.
- It does not touch, compute, or reference any outcome data of any kind.

**Phase 3 evidence required before Methodology Freeze.** Per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §2, Phase 3's required artifacts
include this plan, a construction attempt log (Section 2, below), and a
pre-log attestation for every logged attempt. All four gates in Section 3
must be satisfied, each at Level 2 minimum (AD-072's floor for the
Pre-validation → Methodology Freeze transition; see Section 6), before a
`methodology.md` freeze document may be opened. A Methodology Freeze
document produced without first satisfying every Section 3 gate does not
meet the Standard, regardless of the freeze document's own internal
completeness.

---

## 2. Construction attempt policy

Defined here, before any attempt occurs, per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §2 Phase 3's requirement that the
cap be "stated in the plan before the first attempt is logged."

**Maximum attempt count: 3.**

**Rationale for the cap.** H2, unlike H4, has genuine construction
degrees of freedom (formation window, skip length, return basis, dividend
treatment, ranking methodology, tie handling — Section 3 Gate 4's
checklist). A cap of exactly one, as H4 adopted, would not fit a
construction with real researcher choice; an unbounded count would permit
an undisclosed search across constructions until one happens to clear
Gate 1, defeating the independence check's purpose. Three attempts
mirrors `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §2's cap, set there for
the same reason: it is a documented pressure-relief valve for a
construction whose first attempt turns out, after genuine economic
reconsideration, to be flawed — not a budget for iterating mechanically
toward whichever construction happens to look independent.

**Exact definition of an attempt.** A construction attempt is a fully
specified candidate construction — every element in the list below fixed
to a specific value — submitted for Gate 1 evaluation together with its
pre-log attestation. A change to any one of the following, relative to a
previously logged attempt, constitutes a new attempt against the cap
above; there is no category of "refinement" or "minor adjustment" that
avoids being logged as one:

- formation window (length, in trading days, of the return-formation
  period);
- skip length (length, in trading days, of the interval excluded between
  the end of the formation window and the ranking date);
- return basis (log return vs. simple return);
- dividend treatment (total-return vs. price-return basis, and any
  distribution-handling rule);
- ranking methodology (how the cross-sectional score is derived from the
  return measure — e.g., raw value, z-score, percentile rank);
- tie handling (the rule applied when two or more ETFs have an identical
  score on a given ranking date);
- minimum panel size (the minimum number of ETFs required to be present
  in the cross-sectional panel on a given ranking date for that date to
  be included — the same item Section 3 Gate 4's checklist tracks);
- any other construction logic affecting the signal (e.g., a minimum
  history requirement per ETF, a winsorization or outlier-handling rule,
  or any other design choice that changes what score a given ETF receives
  on a given date).

A construction cannot be relabeled as a continuation of a prior attempt
to sidestep this cap, consistent with
`docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §2's identical rule.

**Verification methodology is frozen, independent of construction
attempts.** Consistent with the Standard's §2 Phase 3 "Allowed changes"
clause: the methodology used to *evaluate* each attempt (Gate 1's
correlation methodology, Section 3 below) may not change once the first
attempt is logged. A change to the evaluation methodology itself, for any
reason, is not a new attempt — it invalidates the cycle to date and
requires this plan to be revised and re-approved before any further
attempt is logged.

**Mandatory pre-log attestation.** Before any construction enters the
attempt log, whoever submits it must attest, in writing, alongside the
log entry:

1. **Economic reasoning existed before evaluation.** The construction was
   derived from the economic mechanism already stated in
   `research_archive/reference_h2/hypothesis.md` — underreaction /
   slow-information-diffusion, with the skip interval separating this
   effect from short-horizon reversal — not reverse-engineered to produce
   a construction that happens to pass Gate 1.
2. **No forward/outcome data used for selection.** No forward return,
   risk-adjusted return, Information Coefficient, p-value, or any other
   outcome variable was read, computed, or referenced in selecting this
   construction, at any point before or during its submission.
3. **No selection based on correlation outcome.** No alternative
   construction was selected or discarded based on its cross-sectional
   correlation with `reference_v1`'s MOMENTUM score, or on any other
   already-tested cycle's observed results, before this attempt was
   submitted.
4. **Alternatives considered and why rejected.** Any alternative
   constructions informally considered — even without computing any
   number for them — are disclosed by name or brief description, together
   with why each was set aside, and confirmation that each rejection
   rested on economic reasoning only, never on an impression of how a
   construction might correlate with MOMENTUM or with any outcome
   variable.

This attestation requirement, and its rationale (converting "informal,
undisclosed exploration before logging" into an explicit, falsifiable
claim rather than an invisible gap), follows
`docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §2 directly.

No construction attempt is logged by this document. This section defines
the policy an attempt must follow once one is submitted; it does not
submit one.

---

## 3. Gate structure

Four gates, all of which must be satisfied, each at the review level
Section 6 specifies, before a `methodology.md` freeze document may be
opened. This section specifies required future evidence and its
methodology; it reports no result and decides no open methodology
question.

### Gate 1 — Signal independence

**Purpose.** Determine whether H2 is a disguised duplicate of
`reference_v1`'s SMA(20) momentum score — the same concern
`research_archive/reference_h2/hypothesis.md` "Novelty Boundary" and
`research_archive/reference_h2/research_proposal.md` §2 (data readiness
row: "needed a written overlap argument against `reference_v1`
MOMENTUM") both flag as unresolved and explicitly deferred to this gate.

**Required future evidence.** Consistent with the two-component Gate 1
evidence structure `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §2
established, this gate requires both a rank correlation analysis
(Component 1) and a ranking-extreme overlap analysis (Component 2).
Neither component is optional and neither substitutes for the other;
both remain future evidence — no figure for either is produced by this
document.

- **Component 1 — SMA(20)-rank vs. trailing-12-1-month-return-rank
  correlation check.**
  For each historical ranking date already covered by `reference_v1`'s
  own analysis, compute the cross-sectional Spearman rank correlation
  between `reference_v1`'s frozen SMA(20) score and the candidate
  trailing-return score, on that same date — one correlation per date,
  not pooled across dates, consistent with this platform's existing
  discipline (per `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §2) against
  pooling ETF-days into a single statistic. This produces a distribution
  (median, spread) of daily score-to-score correlations, not a single
  number.
- **Component 2 — ranking-extreme overlap analysis.** For the same set
  of historical ranking dates, compute what fraction of the top-ranked
  ETFs under `reference_v1`'s frozen SMA(20) score also appear
  top-ranked under the candidate trailing-return score, and the same
  comparison for the bottom-ranked ETFs — following
  `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §2's "Score overlap
  analysis." Reported as a distribution across dates, same as Component
  1. This remains a score-to-score, descriptive comparison; no forward
  return, null distribution, or p-value is computed at any point.
- **Why both components are required.** The rank correlation check
  (Component 1) tests broad signal similarity across the full
  cross-section; it can report a moderate or low figure even when the
  two rankings agree almost exactly at the extremes, which is where a
  disguised-duplicate concern would matter most in practice. The
  ranking-extreme overlap check (Component 2) tests specifically whether
  the strongest-ranked candidates under each score are effectively the
  same selection. Neither component substitutes for the other; both are
  required future evidence before Gate 1 can be considered satisfied.
- **Cross-sectional correlation methodology.** The correlation check
  compares scores to scores only, on matched dates, across the same
  25-ETF universe both scores are already computed over. No forward
  return, null distribution, or p-value is computed at any point — this
  is a descriptive comparison of two already-computed scores, not a
  hypothesis test.
- **Score-side only.** Both inputs to this check — `reference_v1`'s
  SMA(20) score and H2's candidate return score — are score-side
  quantities computed from price history up to and including the ranking
  date. Neither is a forward-looking or outcome quantity.
- **No forward returns.** At no point in this gate's evidence may a
  forward return, in any form, be read, computed, or referenced. A
  proposed check that would require touching a forward return does not
  belong to this gate.
- **Degenerate-case interpretation rules.** Because `reference_v1`'s
  SMA(20) is a price-*level* statistic (unnormalized, currency-
  denominated) and H2's candidate is a return (a dimensionless ratio),
  the specific mathematical degeneracy `docs/REFERENCE_H3_PREVALIDATION_PLAN.md`
  §2 identifies for a naive relative-strength construction (subtracting a
  common benchmark, producing an exact rank identity) does not apply
  here in the same closed form; H2's own "Novelty Boundary" section
  already states this is a difference in what statistic is measured, not
  a parameter adjustment to an unchanged statistic. Nonetheless, an
  empirical correlation between the two rankings is possible for reasons
  unrelated to either construct's economic story, and this gate exists
  precisely because construction and mechanism distinctness are
  necessary but not sufficient. The following interpretation rules apply
  to the measured correlation distribution, following
  `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §2's general structure:
  - A measured median daily correlation that is very high (near the
    upper end of the plausible range) should be treated as **not having
    escaped a disguised-duplicate reading** and requires the economic
    rationale (Gate 3) to be revisited before this gate can be considered
    satisfied — this plan does not fix a specific numeric threshold for
    "very high," since doing so here would pre-decide a gate outcome
    rather than specify how the gate is to be evaluated.
  - A moderate correlation is interpretive, not an automatic pass/fail:
    momentum and longer-horizon return-based signals are documented
    "sibling" factor families in the literature, and some positive
    correlation is plausible even for genuinely, separately motivated
    constructions. A moderate reading requires a written economic
    explanation for why the correlation exists before this gate can be
    considered satisfied — it cannot be waved through by the number
    alone, and it cannot be rejected by the number alone either.
  - A low or near-zero correlation is reassuring but not sufficient by
    itself — it is evidence for Gate 1, not a substitute for Gate 3's
    economic rationale.
  - **Resolving ambiguity.** Where a reviewer cannot confidently place a
    measured result on one side of a boundary rather than the other, the
    ambiguous case is treated as the stricter of the two possible
    readings by default — never resolved in the direction of less
    scrutiny — following the general ambiguity-resolution principle
    `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §2 states for the identical
    situation.
  - **Scope boundary.** This gate's interpretation rules resolve
    ambiguity only in the score-to-score correlation reading. They do
    not, and cannot, define how ambiguity in H2's eventual significance
    test (forward return, IC, p-value, or promotion criterion) is
    resolved — that belongs to Methodology Freeze and Validation, and is
    not decided by this gate.

**Ordering requirement.** Per
`docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §2's "Required ordering," Gate
3's economic rationale must be frozen for the specific construction under
test before this check is run against it. This check is a confirmatory
sanity check on an already-decided construction, not a tool for searching
across candidate constructions for whichever happens to correlate least
with MOMENTUM.

No result for this gate is reported here. This section specifies what
evidence must exist and how it must be produced; producing it is future
Pre-validation work.

### Gate 2 — Data adequacy

**Purpose.** Determine whether the available data is sufficient to
construct and later validate H2, without touching any outcome data.

**Required future evidence.**

- **Fresh dated data inventory check required.** A new, dated inventory
  check against the live database — verified directly, not assumed or
  cited from memory — establishing, for all 25 ETFs in the current
  universe: row counts, date range covered, and source-tag composition
  (per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §6 item 2, every source tag
  must correspond to a value the current, committed ingestion code can
  actually produce).
- **12-month formation window adequacy.** An explicit check of whether
  the available price history, from the earliest date at which all 25
  ETFs have usable data, is sufficient to support a formation window on
  the order of 12 months (the hypothesis's own "trailing, multi-month
  cumulative return measure," per `hypothesis.md`) plus whatever skip
  interval and forecast horizon Methodology Freeze eventually fixes,
  across a ranking-date panel wide enough to be useful. This plan does
  not fix the exact formation-window length, the exact skip length, or
  the exact forecast horizon — those remain Section 4 deferred items —
  but the adequacy check must be performed against a stated candidate
  range, not left unexamined.
- **Ranking-date panel span decision required.** A written decision on
  how much of the platform's available price history the ranking-date
  panel will use — analogous to the A/B/C data-sufficiency decision
  structure `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §3 establishes
  (continue with current history; extend historical data; or change
  universe composition) — together with the reasoning for whichever
  option is chosen. This decision is not made by this plan; it is future
  Gate 2 work.
- **Missing data handling requirements.** An explicit statement of how
  missing or gapped data, if any is found, would be handled — consistent
  with `docs/RESEARCH_GOVERNANCE_STANDARD.md` §6's provenance
  requirements (no silent backfill against data already in use; any
  synthetic or inferred value flagged explicitly in
  `dataset_manifest.json`) — produced as part of Gate 2's evidence, not
  assumed away.

**Existing snapshots from other cycles cannot satisfy this gate.**
`research_archive/reference_h2/research_proposal.md` §7 (Evidence
Chronology Addendum) already establishes that a prior, dated database
inspection (`docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md`)
found that the historical-depth extension `reference_h3`'s own Gate 2
executed is already present in the live database. That finding is
relevant background; it is explicitly **not** a substitute for this
gate. `docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md` §2 itself
states that a defensible Gate 2 requires "a fresh, dated data-inventory
re-check" of that finding, not a citation of the Gate 0 review, and not a
citation of another cycle's snapshot. A `reference_h3`-era or any other
prior cycle's data inventory, dataset manifest, or hash set — regardless
of how recent or how thoroughly it was verified at the time — does not
satisfy this gate for `reference_h2`. Gate 2 requires its own fresh,
dated inventory check, performed under this cycle's own name, against the
live database as it exists at the time the check is run.

No result for this gate is reported here.

### Gate 3 — Economic rationale

**Purpose.** Confirm the economic mechanism for H2 is documented, in
writing, before any implementation decision is made — not reverse-
engineered to justify a construction that happens to pass Gate 1.

**Required future evidence.**

- The mechanism already stated in `research_archive/reference_h2/hypothesis.md`
  ("Economic Mechanism": underreaction / slow-information-diffusion,
  with a skip interval separating this effect from short-horizon
  reversal) must be documented as governing the specific construction
  under Gate 1 test — i.e., that the frozen construction actually
  implements the mechanism described, not a different construction that
  happens to share the same name.
- **Distinctness from `reference_v1` momentum.** A written statement of
  why H2's mechanism is economically distinct from whatever mechanism, if
  any, underlies `reference_v1`'s MOMENTUM — noting, per `hypothesis.md`
  "Novelty Boundary," that `reference_v1`'s own documentation states no
  economic mechanism for MOMENTUM at all, so this distinctness statement
  is the first explicit mechanism comparison of its kind for this
  construct, not a comparison against an existing documented rationale.
- **Distinctness from `reference_v2_h1`.** A written statement of why
  H2's mechanism is economically distinct from `reference_v2_h1`'s
  leverage-constrained-arbitrage / benchmarking-behavior account for low
  volatility.
- **Distinctness from `reference_h3`.** A written statement of why H2's
  mechanism is economically distinct from `reference_h3`'s slower-
  cadence institutional-reallocation account for segment rotation.

This document does not claim validation has passed, has been attempted,
or is expected to pass. Gate 3 evidence is future work; no economic-
rationale determination is made here beyond restating what
`hypothesis.md` already states as the candidate mechanism.

### Gate 4 — Degrees-of-freedom audit

**Purpose.** Confirm no design choice a future Methodology Freeze
document would need to fix remains silently undecided or ambiguous at
the point Freeze is opened.

**Checklist.** Every item below must carry an explicit state of
**fixed**, **deferred**, or **unresolved** before this gate is considered
satisfied. As of this plan, every item is stated **deferred** — none is
fixed here, and none is flagged as an unaddressed unknown requiring
further investigation before it can even be deferred.

| Item | State (as of this plan) |
|---|---|
| Formation window | Deferred — Methodology Freeze |
| Skip period | Deferred — Methodology Freeze |
| Return basis (log vs. simple) | Deferred — Methodology Freeze |
| Dividend treatment | Deferred — Methodology Freeze |
| Ranking method | Deferred — Methodology Freeze |
| Tie handling | Deferred — Methodology Freeze |
| Minimum panel size | Deferred — Methodology Freeze (depends on Gate 2's ranking-date panel span decision) |
| Forecast horizon | Deferred — Methodology Freeze |
| Evaluation metrics | Deferred — Methodology Freeze |
| Rejection criteria | Deferred — Methodology Freeze |

This gate is satisfied only when every row above can honestly be marked
**fixed** (at Methodology Freeze, per `docs/RESEARCH_GOVERNANCE_STANDARD.md`
§3) or is otherwise resolved — not when the table is merely present. As
of this document, satisfying this gate is future work; the table above
records the current, entirely deferred state, not a completed audit.

---

## 4. Deferred decisions boundary

The following items are intentionally not fixed by this plan. Each is
already stated as open in
`research_archive/reference_h2/hypothesis.md`'s "Known Open Questions"
and `research_archive/reference_h2/research_proposal.md` §5's "Deferred
Decisions Boundary"; this plan changes none of them and resolves none of
them silently:

- Exact formation-window length, in trading days.
- Exact skip-period length, in trading days.
- Return calculation basis (log vs. simple return).
- Dividend/distribution treatment.
- Ranking methodology (how the cross-sectional score is derived from the
  return measure).
- Tie-handling rule.
- Minimum cross-sectional panel size.
- Forecast/holding horizon.
- Statistical test design, significance and robustness protocol.
- Promotion/rejection (acceptance) criteria.

None of these is decided in Section 2 (the construction attempt policy
defines what counts as a change to one of these items, not what its value
should be), Section 3 (the gate structure defines what evidence must be
produced about these items, not what the items' values are), or anywhere
else in this document. These remain Methodology Freeze (Phase 4) content
under `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2 and §3, and are not
decided here.

---

## 5. Evidence rules

- **Phase 3 evidence is descriptive only.** Every artifact produced under
  this plan — the data inventory, the Gate 1 correlation distribution,
  the economic-rationale statements, the degrees-of-freedom table —
  describes the data and the candidate construction as they currently
  stand. None of it evaluates, scores, or ranks the construction against
  any outcome.
- **No outcome optimization.** No Phase 3 evidence may be produced,
  revised, or selected with reference to how it would affect a later
  forward-return or IC result. The construction-attempt attestation
  (Section 2) exists specifically to make this rule falsifiable rather
  than aspirational.
- **No forward-return evaluation during pre-validation.** At no point in
  this phase — Gate 1, Gate 2, Gate 3, or Gate 4 — may a forward return,
  risk-adjusted return, Information Coefficient, p-value, or any other
  outcome variable be read, computed, or referenced. This is the same
  standalone principle `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §2
  states as "the one rule this entire document exists to enforce,"
  restated here as binding on every gate of this plan without exception.
- **Every future evidence artifact requires provenance.** Any dataset,
  inventory, or figure produced under Gates 1, 2, 3, or 4 must state its
  source, the exact commit or session that produced it, and the date it
  was produced — consistent with `docs/RESEARCH_GOVERNANCE_STANDARD.md`
  §6's data-provenance requirements (source tracking, transformation
  logs, reproducibility). An artifact that cannot be reproduced by a
  second party from the written record and the raw data alone does not
  satisfy this rule, regardless of whether its reported figures are
  correct.

---

## 6. Review requirements

- **Level 2 review requirement for gate acceptance.** Per AD-072's
  mechanical enforcement boundary (`docs/ARCHITECTURE_DECISIONS.md`,
  "3 — Pre-validation → Methodology Freeze: Level 2 minimum, per
  individual gate"), each of Gates 1 through 4 requires a Level 2 —
  AI-assisted adversarial review (`docs/RESEARCH_GOVERNANCE_STANDARD.md`
  §4) — before it is considered satisfied. A Level 1 self-review, however
  thorough, does not satisfy any of the four gates; it is acceptable only
  for the sanity-check role §4 assigns it.
- **Level 3 availability disclosure requirement.** Per
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §4, "no Level 3 review has ever
  been performed on this platform." AD-072's floor table records Level 3
  for Phase 3 as a conditional clause ("Level 3 where available, before
  platform implementation effort") that is a human governance
  obligation, not mechanically enforced. Any gate record produced under
  this plan must state explicitly that Level 3 review was not available
  for that gate, rather than omitting the point or implying Level 2 was
  sufficient at institutional-grade independence. This plan itself
  discloses that unavailability here, in advance, so no future gate
  record can treat it as an oversight to silently correct.
- **Independent confirmation expectations.** Following
  `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §4's independent-confirmation
  duties, applied identically to Gates 1 through 4 of this plan: the
  confirming reviewer must be a distinct reviewing party in substance —
  a fresh session initiated by the same individual or process that
  performed the work does not, by itself, establish independence beyond
  session separation, and that limitation must be disclosed alongside
  the confirmation record rather than left for a reader to assume
  otherwise (per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §4's core
  correction: "AI session separation... is not, and must never be
  represented as, organizational independence"). For each gate, the
  confirming reviewer must, before the gate counts as satisfied:
  1. review the complete construction attempt log (Section 2), not only
     the final passing construction if one exists;
  2. explicitly confirm no outcome data was read or computed at any
     point in the work being confirmed;
  3. explicitly confirm that no already-tested cycle's observed results
     influenced construction selection, at any attempt, including the
     pre-log attestations;
  4. for Gate 1 specifically, independently reproduce — not merely
     inspect — both required components against `reference_v1`'s frozen
     SMA(20) scores, arriving at the reviewer's own figures using the
     frozen Gate 1 methodology (Section 3) and confirming they match what
     was submitted: (a) the rank-correlation calculation (Component 1),
     and (b) the ranking-extreme overlap analysis (Component 2). Neither
     component's reproduction substitutes for the other, consistent with
     Section 3 Gate 1's statement that neither component substitutes for
     the other as evidence;
  5. record this confirmation — reviewer identity, date, independence-
     level qualification, and the points above, including the
     independently reproduced Gate 1 figures — as part of the archived
     evidence in `research_archive/reference_h2/reviewer_reports/`, not
     only as an informal sign-off.

No review under this section has been performed by this document. This
document is itself Level 1 self-review only, as stated in its header.

---

## 7. Approval state

- This document is authored at planning stage.
- It contains no completed gate results. Gates 1 through 4 (Section 3)
  each specify required future evidence and methodology; none has been
  produced, reviewed, or evaluated by this document.
- It does not authorize Methodology Freeze. Methodology Freeze (Phase 4)
  remains gated on all four Section 3 gates being satisfied at Level 2
  minimum (Section 6), which has not occurred.
- A later independent review — Level 2 minimum, per AD-072's floor for
  this plan's own gates, with Level 3's unavailability disclosed per
  Section 6 — is required before any transition relying on this plan's
  gates being satisfied.
- No lifecycle transition is made or implied by this document. No
  `advance_phase()` call, `DecisionRecord`, or append to
  `research_archive/reference_h2/transition_records.jsonl` occurs here.
