# Research Governance Standard v1.0

**Status: permanent governance framework, not a research document.** This
standard defines how any research cycle on the ETF Intelligence Platform
— hypothesis to archive — must be conducted, documented, and reviewed. It
does not evaluate, approve, or design any specific hypothesis, strategy,
or scoring construct. It introduces no code, no scoring logic, and no
methodology for any strategy, including H3.

This standard is written directly from what the H3 pre-validation program
actually did, and where it fell short of its own aspirations: see
[`docs/REFERENCE_H3_PREVALIDATION_PLAN.md`](REFERENCE_H3_PREVALIDATION_PLAN.md)
for the first per-hypothesis application of most of this standard's ideas,
and
[`docs/H3_GOVERNANCE_REMEDIATION_ADDENDUM.md`](H3_GOVERNANCE_REMEDIATION_ADDENDUM.md)
for the honest accounting of what that program could not yet deliver — no
organizationally independent reviewer, a methodology freeze introduced
after part of the process had already run, and data-provenance controls
that needed strengthening after the fact. This standard exists so the
next research cycle does not have to discover the same gaps by living
through them first.

---

## 1. Purpose

This framework exists to make a research cycle's *conclusion* trustworthy
independent of who ran it, when, or how the result happened to come out.
Four specific failure modes motivate it, each observed or narrowly
avoided somewhere in this platform's own research history:

**Preventing hindsight bias.** A hypothesis, a construction, or an
acceptance threshold chosen — or quietly adjusted — with knowledge of how
it or something similar performed is not evidence of anything except that
adjustment. REFERENCE v1 and REFERENCE v2 H1 both avoided this by frozen
specification; H3's construction attempt was disclosed, alternative-by-
alternative, for the same reason. This standard generalizes that
discipline so it is a platform-wide default, not a per-hypothesis
invention.

**Ensuring reproducibility.** A result that only the person who produced
it can explain or regenerate is not a result an institution can rely on.
Every frozen artifact, every calculation, and every conclusion this
standard requires must be reproducible by a second party from the written
record and the raw data alone — a principle this standard inherits
directly from the reproducibility language already added to
`REFERENCE_H3_PREVALIDATION_PLAN.md` Section 4, generalized here to apply
to every phase, not only Gate 1.

**Protecting research integrity.** Research integrity fails quietly, not
dramatically — a silently mutated dataset, an unlogged data source, a
review performed by the same party as the work, a threshold nudged after
a near-miss. Every control in this standard targets a specific quiet
failure mode of this kind, most of them ones this platform's own H3
program already encountered (see the remediation addendum, Sections 2–3).

**Separating research, review, and decision.** These are three distinct
functions with three distinct incentives, and conflating them is the
single most consequential governance gap this platform has identified in
its own work to date (remediation addendum, Section 2). A person or
process that proposes a hypothesis should not be the same person or
process that certifies its independence, and neither should be the same
party that makes the final PASS/FAIL/INCONCLUSIVE call. This standard
does not claim the platform currently has the organizational capacity to
fully separate these three functions (Section 4 states this directly);
it defines the standard to be met, and requires every gap from that
standard to be disclosed rather than assumed away.

---

## 2. Research Lifecycle

Every research cycle governed by this standard passes through eight
mandatory phases, in order. A phase may not be skipped; it may be
compressed under a documented exception (Section 8), but compression must
be disclosed, not silent.

| Phase | Objective (one line) |
|---|---|
| 1. Hypothesis | State a candidate economic mechanism in plain terms |
| 2. Research Proposal | Rank the hypothesis against rejected alternatives on pre-fixed criteria |
| 3. Pre-validation | Verify the candidate is a genuinely new signal and the data is adequate — no outcome data touched |
| 4. Methodology Freeze | Fix every design choice in writing, immutably, before implementation |
| 5. Implementation | Build exactly what was frozen — no design decisions made here |
| 6. Validation | Run the frozen methodology against frozen data — the only phase where outcome data is touched |
| 7. Decision | Render PASS, FAIL, or INCONCLUSIVE against pre-registered criteria only |
| 8. Archive | Preserve the full evidence trail permanently, regardless of outcome |

### Phase 1 — Hypothesis

- **Objective.** Articulate one candidate economic mechanism, in plain
  economic terms, distinct from every mechanism already tested or
  currently in flight on this platform.
- **Required artifacts.** A dated hypothesis statement (`hypothesis.md`,
  Section 5) — no formula, benchmark, or parameter, only the mechanism
  and why it should exist.
- **Allowed changes.** Freely revised until a Research Proposal is
  opened against it; no freeze applies yet. Every revision must remain
  dated, so a later reviewer can establish the hypothesis predated any
  subsequent phase's results.
- **Approval state.** No formal gate. Logging (author, date) is
  mandatory even though approval is not, because Phase 2's "not selected
  using hindsight" claim depends on this phase's timestamp being real.

### Phase 2 — Research Proposal

- **Objective.** Rank the hypothesis against every other candidate under
  live consideration, using criteria fixed *before* any candidate is
  scored — mirroring `docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md`'s role for
  H3.
- **Required artifacts.** A ranked-candidate memo documenting every
  rejected alternative and the specific reason for its rejection —
  generalizing the "Candidate selection and rejected alternatives"
  section added to `REFERENCE_H3_PREVALIDATION_PLAN.md`. A hypothesis
  with no documented rejected alternatives has not completed this phase,
  even if it is objectively the strongest candidate available.
- **Allowed changes.** Ranking criteria, once stated, may not be
  reweighted after candidates are scored against them. New candidates
  may be added later as dated additions to the memo; existing scores may
  not be revised in light of a later candidate's addition.
- **Approval state.** Level 1 (self-review, Section 4) minimum; Level 2
  required before the proposal may proceed to Pre-validation.

### Phase 3 — Pre-validation

- **Objective.** Establish, without touching any outcome data, that (a)
  the candidate construction is not a disguised duplicate of an already-
  tested signal, and (b) the available data is sufficient to test it —
  the exact two questions `REFERENCE_H3_PREVALIDATION_PLAN.md` Section 1
  poses for H3, generalized here as the standing purpose of this phase
  for every future hypothesis.
- **Required artifacts.** A pre-validation plan (per-hypothesis,
  following the gate structure H3's plan established: signal
  independence, data adequacy, economic rationale, no unresolved degrees
  of freedom); a construction attempt log with a hard cap on the number
  of attempts, stated in the plan before the first attempt is logged;
  a pre-log attestation for every attempt, disclosing every alternative
  informally considered and why it was set aside.
- **Allowed changes.** The candidate construction may be revised across
  logged attempts, up to the pre-stated cap. The methodology used to
  *evaluate* each attempt may not change once the first attempt is
  logged — a methodology change invalidates the cycle to date and
  requires the pre-validation plan to be revised and re-approved before
  any further attempt is logged, exactly as `REFERENCE_H3_PREVALIDATION_PLAN.md`
  Section 2 already requires for H3.
- **Approval state.** Level 2 minimum for each individual gate within
  this phase. Level 3, where available, is required before the platform
  treats a Pre-validation PASS as sufficient grounds to commit real
  implementation effort; where Level 3 is not available (Section 4), the
  gap must be disclosed in the gate record itself, not left implicit.

### Phase 4 — Methodology Freeze

- **Objective.** Fix, in writing and in an immutable form, every element
  listed in Section 3 of this standard — before a single line of
  implementation code is written.
- **Required artifacts.** A single frozen-methodology document
  (`methodology.md`, Section 5), committed to version control, together
  with a dataset manifest and hash set (`dataset_manifest.json`,
  `dataset_hashes/`) capturing the exact data the freeze applies to.
- **Allowed changes.** None. Any change to a frozen element, for any
  reason, including a reason discovered later, does not amend this
  freeze — it invalidates the cycle and requires restarting from Phase 3
  with a new, separately logged construction attempt (subject to Phase
  3's attempt cap) or, if the cap is already exhausted, a wholly new
  cycle from Phase 1.
- **Approval state.** Level 2 minimum, confirming the freeze document is
  complete against Section 3's checklist and that no element was
  selected or adjusted using outcome data. Freeze is not effective until
  this confirmation is recorded.

### Phase 5 — Implementation

- **Objective.** Build exactly what Phase 4 froze. This phase makes no
  design decisions; any decision made here that was not already frozen
  belongs to Phase 4, not Phase 5.
- **Required artifacts.** Implementation commit(s), each referencing the
  Phase 4 freeze commit hash; a conformance note stating, element by
  element against Section 3's checklist, that the implementation matches
  the frozen methodology exactly.
- **Allowed changes.** Ordinary software bug fixes are permitted and
  expected, but must be logged and must not silently alter any frozen
  element (a "bug fix" that changes a lookback window, a benchmark, or a
  scoring formula is a Phase 4 violation wearing a bug fix's name, not a
  bug fix). Any change touching a frozen element reopens Phase 4.
- **Approval state.** Standard code review (Level 1 minimum) plus an
  explicit conformance check (Level 2 recommended) confirming the built
  artifact matches the frozen specification.

### Phase 6 — Validation

- **Objective.** Run the frozen methodology, exactly as implemented,
  against the frozen dataset, and compute outcome statistics — IC,
  significance tests, robustness checks — for the first time in the
  cycle. This is the only phase in the entire lifecycle where outcome
  data may be read, computed, or referenced.
- **Required artifacts.** Raw, unmodified experiment output
  (`experiment_results/`, Section 5); the statistical test results and
  robustness checks specified by the frozen methodology; a record of
  exactly which commit and which dataset snapshot were used to produce
  them.
- **Allowed changes.** None to methodology. If a data defect,
  calculation bug, or other anomaly is discovered during this phase, it
  is handled as a documented incident (Section 6, "anomaly records") —
  never silently patched and rerun without a record of what changed and
  why.
- **Approval state.** Level 2 minimum. Level 3 required before any
  Validation output is used to inform a Decision that could lead to real
  capital allocation; where Level 3 is unavailable, the Decision record
  (Phase 7) must disclose that gap explicitly.

### Phase 7 — Decision

- **Objective.** Render exactly one of PASS, FAIL, or INCONCLUSIVE
  (Section 7), using the acceptance criteria fixed at Methodology Freeze
  — never criteria adjusted after seeing Validation's output.
- **Required artifacts.** A decision record (the final-determination
  template pattern established in `REFERENCE_H3_PREVALIDATION_PLAN.md`
  Section 7), stating the outcome, the date, the reviewer(s) and their
  independence tier (Section 4), the version/commit of the frozen
  methodology in effect, and a synthesis rationale connecting the
  evidence to the outcome.
- **Allowed changes.** None. A Decision may not be revised by re-running
  Validation with adjusted parameters; a different outcome requires a
  new cycle from Phase 1 (for FAIL, subject to the terminal discipline
  in Section 7) or, for INCONCLUSIVE, the specific re-entry path Section
  7 defines.
- **Approval state.** Level 3 at target maturity (Section 4). Level 2
  minimum is acceptable only where Level 3 is genuinely unavailable, and
  only if that unavailability is stated in the decision record itself —
  never silently substituted.

### Phase 8 — Archive

- **Objective.** Preserve the complete evidence trail permanently,
  regardless of outcome — a FAIL or INCONCLUSIVE cycle is archived with
  exactly the same rigor as a PASS.
- **Required artifacts.** The full evidence package (Section 5), with
  every phase's artifacts present and internally consistent.
- **Allowed changes.** None. Archive is append-only. A correction to any
  archived artifact is added as a new, separately dated artifact; no
  existing archived file is edited in place, mirroring the discipline
  `REFERENCE_H3_PREVALIDATION_PLAN.md` Section 6 already establishes for
  H3.
- **Approval state.** A completeness check against Section 5's manifest
  (Level 1 sufficient — this is a checklist, not a judgment call).

---

## 3. Research Freeze Standard

Before Implementation (Phase 5) may begin, the following eight elements
must be fixed in writing, with no degree of freedom left open:

1. **Universe.** The exact set of instruments under study, named
   explicitly (not "the current universe" by reference, but the actual
   list as of the freeze).
2. **Dataset version.** The exact data snapshot — source, date range,
   and content hash (Section 5, `dataset_hashes/`) — the methodology
   will run against.
3. **Evaluation period.** The exact date range (or, where the phase is
   outcome-free by design, the exact same-date comparison basis) the
   methodology operates over.
4. **Benchmark.** The exact comparison construct, named and versioned if
   it is itself a derived score (e.g., "REFERENCE v1's frozen MOMENTUM
   score, commit `e909959`").
5. **Metrics.** The exact statistics to be computed, and how they will
   be aggregated (e.g., "daily cross-sectional Spearman rank
   correlation, reported as a distribution across dates, not pooled").
6. **Scoring rules.** The exact formula, including every input, weight,
   lookback, and missing-data handling rule.
7. **Parameters.** Every numeric constant the scoring rules depend on,
   each with a stated justification that does not reference any outcome
   figure.
8. **Acceptance criteria.** The exact PASS/FAIL/INCONCLUSIVE decision
   rule (Section 7), fixed before Validation is run, including how
   near-threshold or statistically ambiguous results will be resolved —
   generalizing the ambiguity-resolution principle already established
   in `REFERENCE_H3_PREVALIDATION_PLAN.md` Section 2.

### How freeze is recorded

A freeze is not effective until all eight elements above exist in a
single `methodology.md` document, that document is committed to version
control, and the commit hash is recorded in the cycle's `decision_log.md`
(Section 5). A document's own prose claim to be "frozen" is not freeze
evidence; the commit hash is. This directly closes the gap the Gate 1
governance-readiness review flagged for H3's own construction: several
governing H3 documents existed only as uncommitted files at the point
Gate 1 was declared ready to begin.

### How changes are handled after freeze

Any change to any of the eight elements, after the freeze commit, for
any reason:

- is not a revision — it is a new methodology, requiring a new freeze
  commit and, unless still within Phase 3's attempt cap, a new cycle
  from Phase 1;
- invalidates every Validation result already produced under the prior
  freeze for the purpose of the current Decision (those results remain
  archived, per Phase 8, but may not be cited toward a PASS/FAIL/
  INCONCLUSIVE call made under the new methodology);
- must itself be logged in `decision_log.md`, stating which element
  changed, why, and which prior freeze commit it supersedes — silence
  about a methodology change is itself a governance violation under this
  standard, independent of whether the change was substantively
  justified.

---

## 4. Reviewer Independence Model

Three review levels exist. **AI session separation — a fresh working
session with no conversational memory of the work being reviewed — is
not, and must never be represented as, organizational independence.**
This is the single most important governance correction this standard
makes relative to the H3 program's earlier practice, which recorded
"independent" reviews on session-separation grounds alone. Every review
record produced under this standard must state its level explicitly
(1, 2, or 3), and no document may describe a Level 2 review using the
unqualified word "independent."

### Level 1 — Self-review

The work is reviewed by the same individual or session that performed
it.

- **Strengths.** Fast, low-cost, catches self-detectable errors (typos,
  arithmetic slips, obvious logic errors) before anyone else sees the
  work. A necessary minimum floor, not a governance control by itself.
- **Limitations.** Cannot detect a bias the author holds, cannot
  self-certify independence under any circumstance, carries the highest
  risk of confirmation bias and post-hoc rationalization of any level.
  H3's own first Gate 2 review (`gate2_independent_review_2026-07-19.md`)
  is a documented example: performed by the same session as the work,
  and explicitly disclosed as not satisfying the plan's independence
  requirement.
- **Acceptable usage.** Hypothesis-phase and Implementation-phase sanity
  checks only. Never sufficient, alone, to satisfy a Pre-validation
  gate, a Methodology Freeze confirmation, a Validation approval, or a
  Decision.

### Level 2 — AI-assisted adversarial review

The work is reviewed by a separate AI session with no conversational
continuity to the work, explicitly instructed to adopt an adversarial
posture and to independently reproduce calculations rather than inspect
reported figures.

- **Strengths.** Cheap, fast, and scalable relative to Level 3; forces
  explicit written reasoning that a purely verbal sign-off would not
  produce; demonstrably effective at catching structural and logical
  inconsistencies — H3's Gate 2 post-remediation review caught a
  one-directional (missing-only) verification gap that had already
  passed a prior self-review, and the discrepancy analysis that preceded
  it independently root-caused a data anomaly no earlier step had
  flagged.
- **Limitations, stated without qualification.** Not organizationally
  independent under any definition this standard recognizes: the same
  underlying model family and vendor perform both the work and its
  review; no incentive separation exists between "doing the work" and
  "reviewing the work," since both are directed toward the same
  operator's same goal; no accountable, persistent reviewer role exists
  across cycles; the claim of "no conversational memory" is
  self-reported and not verifiable by a third party from outside the
  session. A Level 2 review can be procedurally independent (a real,
  separate pass over the material) without being organizationally
  independent (a distinct party with separate incentives and
  accountability) — and this standard requires every Level 2 record to
  say exactly that, in those terms, rather than the unqualified word
  "independent."
- **Acceptable usage.** The default review tier for Pre-validation
  gates, Implementation conformance checks, and Methodology Freeze
  confirmation. Required as a mandatory supplement — never a
  replacement — for Validation and Decision wherever Level 3 is
  unavailable, with that unavailability disclosed in the record.

### Level 3 — Independent external review

The work is reviewed by a distinct, accountable human or team,
organizationally and financially separated from the work being reviewed
— a different reporting line, no shared performance incentive tied to
the research passing, and standing authority to block a Decision.

- **Strengths.** The only tier capable of genuine institutional-grade
  independence: able to catch systemic or organizational bias that a
  same-operator process (Level 1 or Level 2) structurally cannot detect
  in itself; provides real accountability across time, since the
  reviewing role persists as an identity rather than resetting with each
  session; the tier a professional quantitative research environment or
  a regulator would expect before capital is committed on the strength
  of a research conclusion.
- **Limitations.** Costly and slow relative to Levels 1–2; requires an
  organizational structure — a standing, differently-incentivized
  reviewer role — that this platform does **not** currently have. This
  standard states that gap directly rather than allowing it to be
  papered over: as of this document's writing, the platform operates
  with a single human operator directing all research and all review
  sessions, meaning **no Level 3 review has ever been performed on this
  platform**, including for H3.
- **Acceptable usage.** Required, at target maturity, for Decision-phase
  sign-off on any research proceeding toward real capital allocation.
  Until that capacity exists, every Decision record produced under this
  standard must state explicitly: "Level 3 review not available; this
  Decision was made at Level 2 only." A Decision record that omits this
  statement where Level 3 was in fact unavailable is itself a governance
  violation under this standard, independent of whether the underlying
  research conclusion was correct.

---

## 5. Evidence Package Standard

Every research cycle governed by this standard produces a single,
self-contained evidence package under `research_archive/<cycle_name>/`,
in the following fixed structure:

```
research_archive/<cycle_name>/
 |
 ├── hypothesis.md          — Phase 1 artifact: the mechanism, dated
 ├── methodology.md         — Phase 4 freeze document, immutable once committed
 ├── dataset_manifest.json  — every dataset used: source, version, date range, content hash
 ├── dataset_hashes/        — per-snapshot checksums, at freeze time and at Validation time
 ├── experiment_results/    — raw, unmodified Validation output (Phase 6), append-only
 ├── reviewer_reports/      — every review record from every phase, each labeled with its
 │                            independence tier (Level 1 / 2 / 3, Section 4) — never labeled
 │                            "independent" without that qualifier
 └── decision_log.md        — single, append-only, chronological record of every decision
                               point across the lifecycle: which candidate was ranked where
                               and why (Phase 2), which construction attempt was frozen and
                               when (Phase 3–4), which freeze commit is in effect, which
                               review occurred at which level, and the final Decision
```

**Naming and versioning conventions.**

- Every file is dated in its own content or filename; nothing in this
  package is ever silently overwritten. A correction is a new, dated
  file, cross-referenced from the file it supersedes — the superseded
  file is retained, unedited, as the historical record of what was
  believed true at the time, exactly as `REFERENCE_H3_DATABASE_REMEDIATION_PLAN.md`
  Section 7 already established for H3's own remediation artifacts.
- `dataset_manifest.json` and `dataset_hashes/` must be regenerated, as
  new dated artifacts, any time the underlying dataset changes for any
  reason (extension, remediation, correction) — never hand-edited to
  reflect an expected value.
- `reviewer_reports/` must contain one file per review event, not a
  single running document — each review is a discrete artifact with its
  own date, reviewer identity, and independence-level declaration.
- `decision_log.md` is the one file in this package that is genuinely
  append-only in the literal sense (new entries added, nothing removed
  or edited) rather than superseded-by-new-file; every other file
  follows the supersession convention above.
- A package missing any of the seven items above is incomplete and does
  not satisfy Phase 8's Archive requirement, regardless of the cycle's
  outcome.

---

## 6. Data Provenance Requirements

Five controls, each directly derived from a specific gap the H3 program's
own data-integrity incident exposed (see
`docs/H3_GOVERNANCE_REMEDIATION_ADDENDUM.md` Section 3):

1. **Immutable datasets.** Once a dataset snapshot has been used under a
   frozen methodology, it is never mutated in place. Corrections are
   applied as a new, superseding snapshot with its own manifest entry
   and hash — never an in-place `UPDATE` or silent backfill against data
   already in use. This generalizes the lesson of H3's own remediation:
   the fix that mattered was export-then-delete-then-reverify against a
   new snapshot, not a quiet in-place correction.
2. **Source tracking.** Every stored data point must carry a source tag
   that corresponds to a value the current, committed ingestion code can
   actually produce. Any source tag that does not match a known,
   code-producible value is itself an anomaly signal and must be
   investigated before further use — the exact property that let the
   `backfill-gap-fill` tag (produced by no committed code path) be
   identified as invalid rather than accepted at face value.
3. **Transformation logs.** Every derived value's computation must be
   logged through an accountable run-tracking mechanism (this platform's
   `IngestionRun` convention or its equivalent) at the time it is
   computed. No write path may bypass this logging — the absence of a
   corresponding log entry is precisely what distinguished the 50
   invalid H3-era rows from every legitimate row in the same table.
4. **Reproducible calculations.** Any reviewer, given only the archived
   dataset manifest, the frozen methodology, and the committed code,
   must be able to regenerate every reported figure exactly, without
   supplementary explanation from whoever produced it originally — this
   is the data-layer instance of the reproducibility standard already
   established in Section 1 and in
   `REFERENCE_H3_PREVALIDATION_PLAN.md` Section 4.
5. **Anomaly records.** Any discovered data anomaly — a surplus row, a
   missing date, an unexplained value — is logged as its own dated
   artifact stating its scope, its root-cause status (confirmed /
   reconstructed-with-high-confidence / unconfirmed), and any accepted
   residual risk, before it is corrected. An anomaly that is silently
   fixed without this record does not satisfy this standard even if the
   fix itself was correct — H3's own backfill-gap-fill incident was
   handled this way (a full discrepancy analysis and origin report
   precede the remediation) and is the template this control
   generalizes, including its honest admission that the origin was
   never conclusively closed.

---

## 7. Decision Framework

Every cycle resolves, at Phase 7, to exactly one of three outcomes.

**Relationship to legacy vocabulary.** `REFERENCE_H3_PREVALIDATION_PLAN.md`
Section 6 defines PASS, PARTIAL, and FAIL for H3 specifically, where
PARTIAL is an in-cycle redirection (a revised construction attempt or a
revised data-sufficiency decision) that keeps the same cycle open rather
than closing it. Under this standard, PARTIAL-style redirection remains a
legitimate Phase 3 event — it is not eliminated — but it is not itself
one of this section's three terminal outcomes. Every cycle, including one
that passes through one or more PARTIAL-style redirections, must still
resolve to PASS, FAIL, or INCONCLUSIVE before Phase 8.

### PASS

- **Meaning.** Every required phase completed, every gate satisfied at
  the required review level, and the pre-registered acceptance criteria
  (Section 3, item 8) were met by the Validation-phase result.
- **Required documentation.** The complete evidence package (Section 5)
  with no gaps; a decision record stating the outcome, date, reviewer(s)
  and their independence level, the freeze commit in effect, and a
  synthesis rationale.
- **Next allowed action.** Proceed to Archive (Phase 8). Any further use
  of the result — implementation into a live scoring pipeline, capital
  allocation, or promotion into production — is governed by whatever
  separate deployment process exists outside this standard's scope, and
  that process must independently confirm this standard's Decision
  record exists and is complete before relying on it.

### FAIL

- **Meaning.** The pre-registered acceptance criteria were not met, or a
  hard trigger was reached (e.g., a Phase 3 attempt cap exhausted with
  no attempt clearing its gate).
- **Required documentation.** The complete evidence package, plus an
  explicit statement of which specific criterion failed and why, and
  confirmation of the terminal-failure discipline below.
- **Terminal-failure discipline (mandatory for every FAIL, on every
  hypothesis this standard governs, not only H3).** The moment FAIL is
  recorded: (1) research under this hypothesis's exact form stops,
  immediately, other than the Phase 8 archive steps; (2) no parameter,
  benchmark, universe, or construction adjustment may be made to the
  failed attempt in order to force a different outcome — any such change
  is a new attempt or a new cycle, not a correction; (3) no alternative
  evaluation period, date range, or universe may be substituted after
  the fact in search of a window where the same construction would have
  passed; (4) no criterion may be relaxed or reinterpreted after seeing
  the result that triggered FAIL. These four points are a direct
  generalization of the terminal-failure rule already written into
  `REFERENCE_H3_PREVALIDATION_PLAN.md` Section 6 for H3 specifically;
  this standard makes them the default for every hypothesis.
- **Next allowed action.** Archive (Phase 8). A future proposal touching
  the same or a closely related mechanism is only legitimate as a wholly
  new Phase 1–2 cycle that explicitly engages with the failed cycle's
  archived evidence and states, in writing, why it is a genuinely
  different hypothesis rather than a renamed or restarted attempt at the
  failed one.

### INCONCLUSIVE

- **Meaning.** The cycle could not reach a clean PASS or FAIL: a
  Validation result fell into the ambiguous zone the frozen acceptance
  criteria's own ambiguity-resolution rule (Section 3, item 8) was
  meant to resolve but could not resolve cleanly; a statistical-power
  limitation was discovered only during Validation and could not have
  been anticipated at Methodology Freeze; or the cycle was deliberately
  closed, by documented decision rather than by neglect, before
  completing all phases.
- **Required documentation.** The complete evidence package, an explicit
  statement of why no clean PASS or FAIL was reached, and a stated
  choice between the cycle's two legitimate next steps (below), with
  reasoning.
- **Default treatment.** Absent a specific, documented, Level 2-or-above
  reviewed justification for treating an INCONCLUSIVE result more
  leniently, it is treated with FAIL's terminal discipline for the
  purpose of reopening — INCONCLUSIVE is not a mechanism for retrying
  the same construction with adjusted parameters under a friendlier
  label.
- **Next allowed action.** Either: (a) archive as closed, subject to the
  same re-engagement requirement FAIL imposes on any future proposal
  touching the same mechanism; or (b) where the ambiguity stems
  specifically from a data-sufficiency limitation rather than the
  construction itself, reopen at Phase 3 under a new, separately logged
  data-sufficiency decision — never by relaxing Section 3's acceptance
  criteria to make the existing result look cleaner than it is.

---

## 8. Governance Exceptions

No phase, gate, or control in this standard may be silently skipped.
Every exception requires all three of the following, recorded together
as a single exception record in the cycle's `decision_log.md`:

1. **Documented reason.** What is being skipped, expedited, or reduced,
   and why — stated in enough detail that a future reader can judge
   whether the reason still applies.
2. **Impact assessment.** Which specific governance protection is
   weakened by this exception, and the resulting residual risk — in the
   same explicit, unhedged style as the "accepted residual risks" record
   in `docs/H3_GOVERNANCE_REMEDIATION_ADDENDUM.md` Section 3. An impact
   assessment that describes no actual weakening has not identified a
   real exception and does not need one.
3. **Approval record.** Who approved the exception, and at what
   independence level (Section 4). An exception may never be
   self-approved by the same party requesting it — Level 2 minimum
   approval is required for any exception touching Phases 3–7; Level 3
   is required, where available, for any exception touching Methodology
   Freeze, Validation, or Decision specifically.

Every exception must also be time-boxed: either an explicit expiry (the
exception applies to this cycle only, or until a stated date), or a
documented remediation commitment (a specific future control that will
close the gap, in the style of Section 4 of the remediation addendum).
An exception with neither is not a valid exception under this standard.

### Worked examples

- **Urgent research** (e.g., a regime shift motivates an accelerated
  look at a hypothesis). *Permitted:* compressing phase timelines,
  running phases in closer succession than usual. *Not permitted:*
  skipping the Methodology Freeze, or reducing review below Level 2 for
  any gate. Urgency is a schedule pressure, not a license to remove a
  control.
- **Missing data.** *Permitted:* proceeding with a reduced universe or
  shortened history (an Option-C-style decision, per
  `REFERENCE_H3_PREVALIDATION_PLAN.md` Section 3), documented and
  reviewed as such. *Not permitted:* backfilling gaps with synthetic or
  inferred values without flagging every synthetic value explicitly in
  `dataset_manifest.json` — the exact failure mode the H3 program's own
  `backfill-gap-fill` incident produced when a gap was filled ad hoc,
  outside any accountable path, and without disclosure.
- **Incomplete provenance** (a data anomaly whose root cause cannot be
  conclusively established, as in H3's own case). *Permitted:*
  proceeding only with an explicit, reviewed recurrence-monitoring
  commitment and a disclosed "unconfirmed origin" status in the anomaly
  record (Section 6) — exactly the precedent
  `docs/REFERENCE_H3_BACKFILL_GAP_FILL_ORIGIN_REPORT.md` and
  `docs/REFERENCE_H3_DATABASE_REMEDIATION_PLAN.md` Section 5 already set.
  *Not permitted:* treating an unconfirmed origin as equivalent to a
  closed one, or omitting the recurrence check that provenance gap
  requires.

---

## 9. Applicability

This standard applies to:

- H3's own remaining phases (Gate 1 quantitative testing onward) and any
  future H3-related proposal, subject to the retrospective/prospective
  distinction already established in
  `docs/H3_GOVERNANCE_REMEDIATION_ADDENDUM.md` Section 1 — this standard
  does not retroactively invalidate any PASS already recorded for H3's
  Gate 2 or Gate 3, and does not require redoing work already completed
  under the standard in effect at the time it was done;
- future ETF strategies proposed on this platform;
- scoring model experiments, including any revision to an existing
  scoring dimension (MOMENTUM, VALUE, or any future indicator);
- factor research of any kind conducted on this platform's data;
- portfolio construction research, including any future work on
  portfolio formation, rebalancing, or bucket/weighting logic building
  on a validated factor.

This standard governs *process* — how a research conclusion is reached,
documented, and reviewed. It does not itself validate, approve, or
invalidate the substance of any specific hypothesis; that remains the
role of each hypothesis's own pre-validation and methodology documents,
produced under this standard's Phase 3 and Phase 4 requirements.

---

## 10. Standing Corrective-Action and Calibration-Leakage Rules

This section codifies two standing rules first adopted as cycle-level
decisions during the `positive_control_phase3` cycle and promoted here,
per that cycle's own governance plan, as platform-wide defaults rather
than one-cycle exceptions. Promoting them does not reopen, revise, or
reinterpret any decision already recorded for that cycle (Gate 2 and
Gate 3 remain FAIL, no target, tolerance, or attempt-cap value changes as
a result of this promotion) — it only makes the rule binding on future
cycles without requiring a second promotion.

### 10.1 GOV-1 — Correction discipline

No more than one theory-based target correction may be applied to a
validation gate without a fresh Level 2 review (Section 4) of that
specific correction. Any subsequent correction motivated by a residual
observed after a prior correction must pre-register its candidate
mechanism — before that mechanism is checked against the data it is
meant to explain — exactly as Section 3's freeze discipline already
requires for every other frozen element.

This rule applies identically to every gate of a generator-fidelity or
methodology-fidelity type, including but not limited to a Gate 2
(score-side or combined daily-IC autocorrelation fidelity) and a Gate 3
(independence-cutoff verification) of the kind first defined for the
`positive_control_phase3` cycle — it is a standing platform rule, not
scoped to that cycle alone. A correction that does not first clear a
fresh Level 2 review, or whose candidate mechanism was not pre-registered
before being checked against the residual it responds to, does not
satisfy this standard regardless of whether the correction later proves
numerically accurate.

*Origin:* first adopted as standing-rule "GOV-1" in
`docs/POSITIVE_CONTROL_PHASE3_REMEDIATION_DECISION.md` and
`research_archive/positive_control_phase3/decision_log.md` Entry 5;
promoted here per
`docs/POSITIVE_CONTROL_PHASE3_CONTROLLED_EXECUTION_PLAN.md` gate G4,
which additionally requires this rule to cover Gate 3 as well as Gate 2
so no second promotion is needed for that extension.

### 10.2 Calibration-leakage firewall

**(a) Effect-size, lookback, and promotion-criteria leakage.** No future
hypothesis cycle may cite another cycle's calibration parameters, power
curves, or minimum-detectable-effect (MDE) figures — including but not
limited to a positive-control or power-calibration cycle's output — to
select, size, or justify that future cycle's own effect-size expectation,
lookback window, or promotion criteria. Such outputs may describe what
the pipeline can detect in general; they may never inform what a
specific hypothesis should target.

**(b) Target-function-tuning leakage.** The same firewall applies to a
gate's own target function (for example, an autocorrelation or
generator-fidelity target checked against a theoretical curve): the
target function may not be corrected, adjusted, or re-derived using
knowledge of the specific residual pattern it is being checked against,
except through the pre-registration-before-checking discipline Section
10.1 (GOV-1) already requires. A correction whose only stated support is
post-hoc agreement with an observed residual shape, with no independently
disclosed theoretical grounding, is a calibration-leakage violation under
this section — not a valid correction — regardless of the review level
that approved it.

*Origin:* (a) first drafted as
`docs/POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md` Section 11.2,
itself carrying forward v1 Section 6.4 unchanged in substance; (b) is
the extension to target-function tuning required by
`docs/POSITIVE_CONTROL_PHASE3_CONTROLLED_EXECUTION_PLAN.md` gate G5 so
that a single promotion covers both leakage channels.

---

**Version:** 1.1. **Effective:** upon commit of this document. Future
revisions to this standard follow the same discipline it imposes on
research cycles: a revision is a new, dated version, not a silent edit —
this document's own version history is itself subject to the archive
discipline it defines in Section 5.

**Revision history.**

- **v1.0** — original standard (Phases 1–8, Sections 1–9).
- **v1.1** (2026-07-20) — added Section 10 (GOV-1 correction discipline
  and the calibration-leakage firewall, extended to target-function
  tuning), promoting standing rules already adopted at the cycle level
  for `positive_control_phase3`
  (`docs/POSITIVE_CONTROL_PHASE3_CONTROLLED_EXECUTION_PLAN.md` gates
  G4/G5). No change to Sections 1–9 or to any prior decision, freeze, or
  Decision-phase outcome recorded under v1.0.
