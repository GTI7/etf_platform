# Positive Control Study — Phase 3 Controlled Execution Plan

**Author/role:** Phase 3 Research Program Manager.
**Implements:** [`docs/POSITIVE_CONTROL_PHASE3_REMEDIATION_DECISION.md`](POSITIVE_CONTROL_PHASE3_REMEDIATION_DECISION.md)
("the Decision") in full, together with the diagnostic plan it ratifies
in [`docs/POSITIVE_CONTROL_PHASE3_ANALYTICAL_CORRECTION_ADDENDUM.md`](POSITIVE_CONTROL_PHASE3_ANALYTICAL_CORRECTION_ADDENDUM.md)
§12 ("the Addendum"), and the frozen tolerance/seed procedures in
[`docs/POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md`](POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md)
§2a/§8 ("V2").

**No code is written or modified by this document. No methodology,
target function, tolerance formula, or acceptance criterion is
derived, altered, or selected here.** This document does exactly one
thing: it sequences, gates, and records-in-advance the diagnostics the
Decision already authorized, so that no step can be reordered,
skipped, or reinterpreted once results are observed. Every numeric
value this plan requires to exist "in writing before execution" is a
placeholder for content the Research role must author and a Level 2
reviewer must approve — this plan mandates that such content exist and
be committed at a specific point; it does not supply the content
itself, per the Decision's own instruction that this remains open
research work, not a settled parameter.

**Governing standard:** [`docs/RESEARCH_GOVERNANCE_STANDARD.md`](RESEARCH_GOVERNANCE_STANDARD.md)
("the Standard"). All phase names, review levels, and evidence-package
requirements below are the Standard's, not new inventions of this plan.

---

## 0. Roles, authority, and the two tracks

| Role | Authority | Cannot do |
|---|---|---|
| **Program Manager** (this document) | Sequences work; enforces gate order; may HALT any track for a process violation; maintains the commit checklist (§6) | Cannot approve a Level 2 review of work this same session produced; cannot waive a BLOCKER |
| **Executor** | Runs pre-registered diagnostics exactly as specified; reports raw output | Cannot alter a pre-registered parameter after RNG draw begins, for any reason |
| **Level 2 Reviewer** | Separate session, procedurally independent, adversarial posture, reproduces rather than inspects | Is not organizationally independent (Standard §4) — every sign-off below must say so explicitly |
| **Level 3 Reviewer** | N/A | Does not exist on this platform (standing, disclosed gap per Standard §4) — every gate below inherits this disclosure automatically |

**Two tracks, structurally separate from this point forward, per Decision §6:**

- **Track A — Gate 2** (score-side ACF target correction). Governed in
  full by this document.
- **Track B — Gate 3** (daily-IC-series lags 44–51 anomaly). Governed
  by this document only up to its single authorized diagnostic (§B1);
  any further Gate 3 work requires its own later, separately-scoped
  addendum and its own execution plan.

**Standing rule, stated once, binding throughout this entire document:**
no artifact, commit, decision-log entry, or review may reference both
tracks' results as jointly supporting a single conclusion. A document
that does so is non-compliant with this plan regardless of the
correctness of either track's individual finding.

---

## 1. Required governance steps before any experiment

Nothing in Track A or Track B may begin execution until **every** item
below is committed. This is the single governance gate (Gate G) that
precedes all diagnostic work.

| # | Step | Why (Decision ref.) | Type |
|---|---|---|---|
| G0 | **Phase 3 construction-attempt cap.** Fix, before G1, the counting convention and hard cap on theory-based target-correction attempts for Gate 2's `target_fn`, per `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2 Phase 3 ("a construction attempt log with a hard cap on the number of attempts, stated in the plan before the first attempt is logged"). **Counting convention:** **Attempt 1** = the original, already-executed naive `Bartlett(k)` construction (V2 §1.3's pre-correction claim, executed and recorded FAIL in `decision_log.md` Entry 3) — the baseline construction this Plan responds to; counted, but not itself a "correction." **Attempt 2** = `G(k)` (the Addendum's theory-based correction, §6 of the Addendum, exercised by Track A's A1) — already derived, gated for execution by this Plan, not yet gate-executed. **Cap: at most one further theory-based correction attempt (Attempt 3) beyond Attempt 2 may ever be pre-registered under this Plan.** This number is not chosen casually: it is the number the Decision and this Plan's own §5 decision tree already imply and this gate simply makes binding — §5 path (a) authorizes exactly "a new, wholly separate theory-derivation attempt" (singular) as the sole response to an OUTCOME 2 residual, and Decision §5 states an empirical reference curve is a last resort "only if repeated theory-based attempts fail to close a persistent, N-independent gap," with this Plan's own §5 path (c) further restricting it to "ONLY after path (a) has been attempted at least once and failed" — i.e., the Decision's own text already contemplates exactly one further theory attempt before the path forks to termination or last-resort, never an open-ended series of further corrections. Setting the cap any higher would license exactly the "iterative target patching without a terminal boundary" GOV-1 (G4) exists to prohibit; setting it at zero would foreclose the single legitimate refinement the Decision itself explicitly permits. **Terminal behavior:** if Attempt 3 is triggered (reachable only from A3 OUTCOME 2, per §5) and itself fails to close the residual (a further OUTCOME-2-style result) or is not attempted at all, no Attempt 4 may be pre-registered, executed, or checked against data under this Plan, for any reason, including a plausible-sounding new candidate mechanism. Track A must then resolve via §5 path (b) (FAIL/INCONCLUSIVE, `docs/RESEARCH_GOVERNANCE_STANDARD.md` §7's terminal-failure discipline applies in full — no further parameter nudging on this construction) or path (c) (the empirical reference curve, already gated as last-resort-only and separately firewalled). Any further theory-based work on Gate 2's target after the cap is exhausted is out of scope for this Plan and requires a wholly new Phase 1–2 hypothesis cycle under the Standard — not a further attempt logged against this cycle. **Correction-lineage tracking (cross-cycle):** the counting convention above is defined against a persistent, **platform-level correction-lineage record** — [`docs/RESEARCH_LINEAGE_REGISTER.md`](RESEARCH_LINEAGE_REGISTER.md), entry `gate2_score_acf_target_fn` — not against this Plan document in isolation. That record's attempt count carries forward into any later Phase 1–2 hypothesis cycle proposing a new construction for the same target_fn/mechanism space, regardless of how that cycle is named or scoped. A later cycle may open a fresh attempt count only if its Phase 2 proposal and Level 2 sign-off explicitly certify, on a stated mechanistic basis (not a restated name, scope, or framing), that the new construction is not a continuation, renaming, or reformulation of any attempt already in the lineage; that certification must be filed in `docs/RESEARCH_LINEAGE_REGISTER.md`'s `certifications[]` list for the `gate2_score_acf_target_fn` entry, cross-referenced to the archived prior cycle's evidence, before the new cycle's own Attempt 1 may be logged. Absent such a certification, any new cycle touching Gate 2's target_fn is treated as continuing this lineage and inherits its remaining attempt budget — if this Plan's cap is already exhausted, the new cycle has zero further theory-based attempts available under this clause. This does not change the counting convention, the cap value, or Attempt 3's availability under this Plan; it only prevents the same cap from being reset by opening a nominally new cycle. This Plan's own lineage entry is opened with `lineage_status: active`; per the register's schema, status moves to `exhausted` if the cap is reached with no attempt clearing Gate 2, to `superseded` if a later cycle's certified fresh count supersedes this lineage for the same mechanism space, or to `archived` once this cycle reaches Phase 8 regardless of terminal outcome — a status change is a register update recorded in that entry's `status_log`, not a re-opening of this Plan's own cap. **Mechanism provenance disclosure:** before Attempt 3's candidate mechanism is checked against any data, its pre-registration must include a provenance disclosure — self-attested, under the same non-verifiability caveat G8 already states for its blindness disclosure, since this platform cannot independently confirm what an author did or did not see — listing every prior-attempt output the author had access to before formulating the mechanism (at minimum: A1's per-lag pass/fail pattern, A3's N-sweep results, and any residual-shape description in the Addendum, the Decision, or an intervening decision-log entry), and stating explicitly whether the residual's shape (sign pattern, magnitude, lag concentration) was known to the author before derivation began. This is a disclosure obligation, not a blinding requirement, and does not itself block Attempt 3. **Reviewer obligation — residual-shape overfitting assessment:** the fresh Level 2 review of Attempt 3's derivation already required by GOV-1 must include a labeled subsection, separate from its mathematical-soundness verdict, assessing whether the proposed mechanism is independently motivated (grounded in theory or literature that predates, or does not depend on, the specific observed residual) or instead appears fit to the shape disclosed under the provenance requirement above. A candidate mechanism whose only stated support is post-hoc agreement with the observed residual shape, with no independently disclosed theoretical grounding, does not clear this pre-registration gate and may not proceed to execution as Attempt 3 in that form — this rejects that specific candidate on review and sends it back for revision or replacement, it does not consume the Attempt 3 slot (only an attempt actually checked against data counts against the cap, per this gate's counting convention above) and does not reduce, remove, or cap-below-one the number of theory-based attempts this cap otherwise allows. | `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2 Phase 3 attempt-cap requirement; GOV-1 (G4); Decision §8 items 1–2 (iterative target-patching risk; same-data motivation-and-validation overlap) | BLOCKER |
| G1 | Commit the currently uncommitted evidence set as one reviewed commit: the Addendum, both V2 drafts, `research_archive/positive_control_phase3/` in full, and the Decision document itself. | §7 — "this decision document itself has no governance effect until it is committed" | BLOCKER |
| G2 | In the same commit as G1, append `decision_log.md` **Entry 5**: diagnostic-only acceptance of the Addendum, the full §4/§5/§6 requirement list, explicit non-adoption of the §10 Gate 3 reframing. Reference this commit (G1) as the commit this entry itself lands in. | §7 | BLOCKER |
| G3 | File the Decision document under `research_archive/positive_control_phase3/reviewer_reports/` (currently an empty scaffold). | §7 | REQUIRED |
| G4 | Promote **standing rule GOV-1** into `docs/RESEARCH_GOVERNANCE_STANDARD.md`: *no more than one theory-based target correction may be applied to a gate without a fresh Level 2 review of that specific correction; any subsequent correction motivated by a residual observed after a prior correction must pre-register its candidate mechanism before being checked against data.* Extend its wording explicitly to cover Gate 3 as well as Gate 2, so Track B inherits the same discipline without a second promotion later. | §7 | REQUIRED — this is the concrete mechanism preventing repeated correction loops (§5 below) |
| G5 | Promote the calibration-leakage firewall extension from V2 §11.2, reworded to explicitly cover **target-function tuning**, not only effect-size tuning, into `docs/RESEARCH_GOVERNANCE_STANDARD.md` (or the roadmap memo's standing entry-requirements list, per V2's own siting). | §7, §5 | REQUIRED |
| G6 | Commit a one-paragraph **Track Separation Charter** (may live in this document's own §0, already satisfied above, or as a short standalone note) formally establishing Track A and Track B as separate document families, separate decision-log entries, and separate votes, per Decision §6. | §6 | REQUIRED |
| G7 | Commission the **second, independently-written implementation** of the fidelity-gate computation (Decision §4). **Independence requirement, binding on *how* the second implementation may be produced, not merely that a second one exists:** the second implementation must be written from frozen specification text only — V2 §1.2–§1.3 (generator model), §2/§2a (gate definitions and tolerance procedure), and, once committed, this Plan's own A1/A2/A3 pre-registrations (§3) — and from nothing else. Before its own result is generated, the implementer (human or AI session) building the second implementation must not: (a) inspect `experiments/positive_control_phase3_pilot.py`, or any other file containing the first implementation's source; (b) copy, port, or adapt any implementation detail (data structures, code shape, helper functions, variable naming that tracks the first implementation rather than the spec) from the first implementation; (c) review the first implementation's output (`generator_fidelity_results.json`, `pilot_results.md`, or any table derived from either) before its own run completes and its own raw output is recorded. Reconciliation between the two implementations' outputs happens only *after* both independently-produced results exist (§C5) — never before, and never as an input to either implementation's own construction. A second implementation produced by reading, translating, or lightly modifying the first implementation's code, or by checking its own intermediate results against the first's output before finishing, is **not** a G7-qualifying implementation under this Plan and does not satisfy this gate, regardless of how it is labeled. It must exist and be committed before Track A's Diagnostic 1 result (§A1) can be *accepted* — it need not block Diagnostic 1's *execution*, which may proceed in parallel while the second implementation is built, provided that parallelism does not become a channel for the second implementation's author to observe the first's in-progress output before its own result is generated. | §4 | REQUIRED (gates acceptance, not execution) |
| G8 | Independent **Level 2 blind re-derivation** of Addendum §3–§8: a reviewer re-derives the grade-correlation target from the model definition without first reading the Addendum's own derivation, then compares. **Blindness disclosure, stated explicitly and required in every record of this gate:** the reviewing session's claim to not have read the Addendum's derivation before re-deriving is **self-attested only** — there is no mechanism on this platform to verify, from outside the reviewing session, that claimed blindness was actually maintained during the re-derivation. This is not a defect specific to this gate; it is the same **platform-level limitation** `docs/RESEARCH_GOVERNANCE_STANDARD.md` §4 already names for every Level 2 review generally ("the claim of 'no conversational memory' is self-reported and not verifiable by a third party from outside the session"). **No Level 3 verification of this blindness, or of any other part of this re-derivation, exists or is available on this platform** — this gate's record must state that limitation in those terms every time it is cited, and must never describe the blindness as verified, confirmed, or independently established. This gate's outcome remains Level 2 evidence, procedurally independent but not organizationally independent, exactly as every other Level 2 review on this platform. May run in parallel with Track A's diagnostics; must complete before the **A-Adoption Gate** (§A-AG). | §4 | REQUIRED (gates adoption, not execution) |

G0–G6 must all be committed before either track's first diagnostic
executes. G7 and G8 may be in progress concurrently with execution but
must close before their respective downstream gates (§A1 acceptance,
§A-AG adoption).

---

## 2. Exact order of diagnostic experiments

**Cross-track rule:** Track A and Track B may proceed on independent
calendar timelines; neither track's start, sequencing, or outcome is
contingent on the other's. They are ordered separately below.

### Track A (Gate 2) — strict sequential order

1. **A1 — Gate 2 corrected-target rerun** (`target_fn = G(k)`, fresh
   seeds). BLOCKER. Must complete (execute + reconcile against G7's
   second implementation) before A2 or A3 begin.
2. **A2 — w-blend cross-term validation** (`w ∈ {0.3, 0.5, 0.7}`).
   REQUIRED. Runs after A1 completes, using the same fresh-seed family
   established in A1's pre-registration (§A0).
3. **A3 — Finite-N sensitivity sweep** (`N ∈ {25, 50, 100, 400}`).
   BLOCKER, **conditional**: only executes if A1 leaves an unresolved
   residual (the expected outcome per Addendum §9). If A1 passes
   outright, A3 is skipped and that skip is itself logged with
   reasoning (§6).
4. **A-Adoption Gate.** Not a diagnostic — the single decision point
   at which Gate 2's operative `target_fn` may change, gated on A1 +
   A2 + A3 (if run) + G7 + G8 all being complete and reconciled.

This order matches the Addendum's own §12 step numbering (1→2→3); this
plan adds the fresh-seed requirement, the explicit conditional-entry
rule for A3, and the separate Adoption Gate that the Addendum's §12
does not itself define.

### Track B (Gate 3) — single authorized diagnostic

1. **B1 — targeted R-increase across lags 40–60.** REQUIRED before
   treating the lags 44–51 excursion as Monte Carlo noise. This is the
   only diagnostic this plan authorizes for Gate 3. Any further Gate 3
   work (e.g. formalizing a corrected IC-series target, or adopting
   the Addendum §10 `2h`-cutoff reframing) is explicitly **out of
   scope** for this plan and requires a new, later, separately-scoped
   addendum and its own execution plan, per Decision §6.

---

## 3. Pre-registration requirements per experiment

Every item below must exist as a **committed, dated document**, with
its commit hash preceding the commit hash of the corresponding
execution's raw output. No field may be filled in, adjusted, or
clarified after RNG draw for that experiment begins.

### A0 — Track A entry (shared by A1–A3)

- A fresh `base_seed`, distinct from the original pilot's `20260720`
  seed, drawn and recorded before A1 begins. Same SHA-256 + two-stream
  (`panel`/`test`) scheme as V2 §8, unmodified.
- This `base_seed` is frozen for the entire Track A sequence (A1–A3)
  unless a specific diagnostic's own design requires a distinct,
  separately pre-registered seed rule (A3's N-sweep is the one case
  where this applies — see below).

### A1 pre-registration

- `target_fn = G(k)` exactly as Addendum §6, unmodified.
- `R = 25`, unchanged from V2 §2a's frozen procedure (an R-increase is
  optional per Decision §4 but must be separately pre-registered and
  elected before this run, not folded in silently).
- Seed: A0's fresh `base_seed`, new `stream_tag` distinct from the
  original pilot's.
- Tolerance procedure: V2 §2a, unmodified — 95% two-sided Monte Carlo
  band, `SE(k)` from the run's own 25 replications.
- Per-lag pass rule: `|deviation(k)| ≤ tolerance(k)` for `k = 1..20`,
  evaluated lag-by-lag — no aggregate "N of 20 pass" summary may
  substitute for the per-lag record.
- Overall verdict rule: Gate 2 PASSES only if all 20 lags pass
  (preserves the existing all-or-nothing convention **established in
  V2 §2 gate 1's pass condition, "every lag's empirical ACF falls
  within a frozen Monte Carlo tolerance band of the closed-form value"
  — explicitly applied to gate 2 (score-side) by V2 §2 item 2's
  "Identical procedure applied to `score` instead of `forward_return`"
  — and restated in full generality by V2 §2a, "Pass condition:
  `|deviation(k)| ≤ tolerance(k)` for every lag `k` in the gate's
  checked range." This is where the per-lag, all-or-nothing rule is
  defined; `decision_log.md` Entry 3 is where that already-defined rule
  was first applied to an executed result (16 of 20 lags outside
  tolerance under the naive target) and remains cited here only as
  historical evidence of that application, not as the rule's source**).
- Second-implementation requirement (G7): the independent
  implementation must reproduce this run's output within a documented
  floating-point tolerance, stated in the pre-registration doc before
  either implementation runs. Per G7's independence requirement, this
  second implementation is built from frozen specification text
  (V2 §1.2–§1.3/§2/§2a and this pre-registration) only — no inspection
  of the first implementation's source, no ported code, and no look at
  the first implementation's output before the second implementation's
  own result is generated.
- Explicit clause: no parameter above may be changed after this
  pre-registration is committed, regardless of outcome.

### A2 pre-registration

- `w` grid: `{0.3, 0.5, 0.7}`.
- Predicted curve: `ACF_score(k; w) = G(k) + w·√(1-w²)·Gx(k)`, per
  Addendum §8, unmodified.
- Seed: A0's fresh `base_seed` family — **not** `rho_calibration.csv`'s
  original seeds, for the same look-then-leap reason the Decision
  applies to A1 (§4, §8 item 2).
- `R` (or replication count) for this comparison, and its derivation,
  must be written and Level 2-reviewed before execution — not assumed
  equal to A1's `R=25` without a stated reason.
- The specific `(k, w)` checkpoints where the cross-term is checked
  (concentrated near `k ≈ h` per §8) must be listed explicitly before
  execution, not chosen after seeing the empirical curve.
- Pass rule: `|empirical ACF(k;w) − predicted ACF(k;w)| ≤ tolerance(k)`
  at every pre-registered checkpoint.

### A3 pre-registration (its own separate, sequential gate — "A3-entry")

This is the specific BLOCKER the Decision names: *"pre-register the
N-sweep's stopping/interpretation rule before running it."*

- Fixed parameters: `h=20`, `β=0.30`, `N ∈ {25, 50, 100, 400}`.
- Replication count `R` per `N`-point: stated and justified in writing
  (diagnostic, not a fidelity determination — need not match `R=25`)
  before execution.
- Seed rule for each `N`-point: derived from A0's `base_seed` family
  via a stated, deterministic per-`N` stream tag, fixed before
  execution.
- **The stopping/interpretation rule itself**: a named, quantitative,
  falsifiable test (e.g. a monotone-trend test on the residual across
  the four `N`-points, plus a numeric closeness threshold at `N=400`)
  that distinguishes "residual has shrunk to finite-N noise level"
  from "residual has plateaued at a nonzero value." Authoring the
  specific test is Research work requiring its own Level 2 sign-off —
  **this plan requires the rule to exist, in writing, committed,
  before A3 executes; it does not specify the rule's content**, per
  this document's own no-methodology-change constraint.
- Explicit clause: once committed, the stopping rule may not be
  loosened, supplemented, or reinterpreted after the four `N`-points'
  results are observed.

### B1 pre-registration (Track B, fully separate document)

- The increased `R` value and its derivation (a §2a-style
  precision-target calculation), written and Level 2-reviewed before
  execution.
- Scope: lags 40–60 specifically, or globally — stated explicitly,
  with reasoning, before execution (Decision §6 permits either but
  requires the choice be disclosed, not defaulted silently).
- A quantitative pass criterion for "the excursion disappears" (e.g.
  no lag in the checked range exceeds its recomputed tolerance band at
  the increased `R`), fixed before execution.

---

## 4. Acceptance / rejection criteria

### A1

| Result | Verdict |
|---|---|
| All 20 lags pass, both implementations agree within tolerance | **PASS** |
| Some lags fail (expected: 1–12), both implementations agree on which | **PARTIAL / EXPECTED-FAIL** — proceed per §5 |
| Implementations disagree beyond documented tolerance | **INVALID RUN** — discard, reconcile implementations, redo as a new dated attempt (not a silent rerun) |
| Failure pattern qualitatively contradicts the Addendum's own directional prediction (§4 property (b)) | **ANOMALY** — halt Track A, route to root-cause triage (§5) |

*Clarification:* an INVALID RUN redo re-executes the same candidate mechanism (`G(k)`, Attempt 2) to fix a reconciliation problem between implementations; it is not a new construction and does not consume an additional slot against G0's cap or `docs/RESEARCH_LINEAGE_REGISTER.md`'s `gate2_score_acf_target_fn` attempt count.

### A2

| Result | Verdict |
|---|---|
| Predicted curve within tolerance at every pre-registered checkpoint | **CONFIRMED** — cross-term licensed for use **only at the specific `w` values and `(k,w)` checkpoints actually tested** (§A2 pre-registration), pending A-Adoption Gate; not a license for any untested `w` value or for unrestricted interpolation across the `w`-domain |
| Any checkpoint outside tolerance | **NOT CONFIRMED** — any eventual G(k) adoption is restricted to `w=0` only; `Gx(k)` remains "derived, unvalidated"; no formula adjustment permitted in response (GOV-1 applies) |

### A3

| Result (per the pre-registered stopping rule) | Verdict |
|---|---|
| Residual shrinks per the committed criterion | **OUTCOME 1** — finite-N bias (Addendum §11 item 1) confirmed sufficient |
| Residual does not shrink / plateaus | **OUTCOME 2** — finite-N bias ruled out as sufficient; a structural term (§11 item 4) is implicated |

### B1

| Result (per the pre-registered pass criterion) | Verdict |
|---|---|
| Excursion disappears at increased R | Supports (does not prove) Monte Carlo noise; does **not** flip Gate 3 to PASS and does **not** validate Addendum §10's `2h=40` reframing |
| Excursion persists at increased R | MC noise ruled out; anomaly requires its own separately-scoped root-cause investigation — not an automatic trigger for a Gate 3 target correction |

### A-Adoption Gate — the only point Gate 2's operative target may change

All of the following required simultaneously:

- A1 = PASS, **or** A1 = PARTIAL with A3 resolved to OUTCOME 1.
  (A1 = ANOMALY/INVALID, or A3 unresolved/OUTCOME 2 with no chosen
  path from §5, blocks adoption entirely.)
- A2 = CONFIRMED **at every pre-registered `(k,w)` checkpoint actually
  validated**, or adoption is explicitly scoped to `w=0` only. A
  CONFIRMED verdict licenses adoption **strictly for the specific `w`
  values tested (`w ∈ {0.3, 0.5, 0.7}`, §A2 pre-registration) and the
  specific checkpoints validated at each** — it is not, and must never
  be recorded as, validation across the full continuous `w ∈ [0,1]`
  domain, and it does not by itself license use at any untested `w`
  value. Any adoption-record use of the formula at an untested `w`, or
  via interpolation between tested `w` values, must state its own
  interpolation assumption explicitly (what is being assumed about
  `ACF_score(k;w)`'s behavior between the tested points, and why that
  assumption is reasonable given §8's smooth closed form) — no adoption
  entry may imply the formula is validated at arbitrary `w` merely
  because it passed at three tested points.
- G8 (blind re-derivation) complete, clean or reconciled.
- G7 (second implementation) reconciled against A1 and A2.
- A decision-log entry drafted stating exactly which lags/`w`-values
  are covered and which are **not** — the "8 of 20 lags pass, 12 do
  not" honest framing (Decision §8 item 3) must persist verbatim into
  any adoption record, not be summarized away.
- The adoption decision-log entry itself receives Level 2 sign-off —
  adoption is a reviewed decision in its own right, not an automatic
  consequence of a passing diagnostic.

---

## 5. Decision tree after each possible outcome

```
A1 executed
├── PASS (all 20 lags)
│     → A2 required before adoption (scopes w>0 eligibility)
│     → A3 skipped, skip logged with reasoning
│     → proceed to A-Adoption Gate
│
├── PARTIAL / EXPECTED-FAIL (lags 1–12 fail, 13–20 pass)
│     → A2 proceeds independently
│     → A3 REQUIRED (its own separate A3-entry pre-registration gate)
│         ├── A3 OUTCOME 1 (residual shrinks)
│         │     → finite-N bias confirmed sufficient
│         │     → no further correction opened
│         │     → proceed to A-Adoption Gate (subject to A2, G7, G8)
│         │
│         └── A3 OUTCOME 2 (residual persists)
│               → GOV-1 engages: NO automatic second correction
│               → Program Manager selects exactly one of (a)/(b)/(c)
│                 below — **and this selection is itself a reviewed
│                 decision artifact, not an incidental note.** Before
│                 any of (a)/(b)/(c) is acted on (before its own
│                 pre-registration, if any, is committed), a
│                 decision-log entry must be drafted stating: (i) the
│                 rationale for the path selected; (ii) the rejected
│                 alternatives — the other one or two paths — and the
│                 specific reason each was rejected for this case, not
│                 a generic restatement of the option's own definition;
│                 (iii) an explicit governance justification citing
│                 which specific rule governs the choice (GOV-1 for why
│                 no automatic second correction occurs; this Plan's
│                 §5 path ordering — (a) before (b)/(c), (c) only after
│                 (a) has been tried and failed — for why the paths are
│                 not interchangeable; Standard §7 if (b) is selected).
│                 This entry requires **Level 2 review before** the
│                 selected path's own pre-registration may be
│                 committed — the choice of path is reviewed
│                 independently of, and prior to, whatever the chosen
│                 path itself goes on to require.
│                   (a) New, wholly separate theory-derivation attempt:
│                       pre-register the candidate mechanism BEFORE
│                       checking it against the residual; fresh
│                       base_seed distinct from A0's; fresh Level 2
│                       review of that specific new derivation
│                       (GOV-1's explicit requirement); subject to
│                       Phase 3's attempt-cap discipline (Standard §2
│                       Phase 3).
│                   (b) Declare the theory-based correction path
│                       exhausted for this cycle; render FAIL or
│                       INCONCLUSIVE per Standard §7. Terminal-failure
│                       discipline (Standard §7) then applies: no
│                       further parameter nudging on this construction.
│                   (c) Empirical-reference-curve last resort — ONLY
│                       after path (a) has been attempted at least
│                       once and failed (Decision §5's "last resort"
│                       framing forbids selecting (c) directly from
│                       OUTCOME 2). Requires its own separate
│                       pre-registration and a dedicated high-R/
│                       high-N reference run structurally firewalled
│                       from the runs it later validates.
│
└── ANOMALY / INVALID RUN
      → HALT Track A
      → log as anomaly record (Standard §6-style: scope, root-cause
        status, accepted residual risk)
      → route to Program Manager + Level 2 review for root-cause
        triage BEFORE any new diagnostic is designed
      → no new target correction may be proposed until root cause is
        established (this is exactly the iterative-target-patching
        risk Decision §8 item 1 names)

A2 executed (independently of A1's branch above)
├── CONFIRMED → use licensed only at the tested `w` values/checkpoints,
│     pending A-Adoption Gate — not an unrestricted `w>0` claim
└── NOT CONFIRMED → adoption scoped to w=0 only; Gx(k) formula is not
      adjusted in response (GOV-1 applies identically to a cross-term
      failure as to an own-term failure)

B1 executed (Track B, independent timeline)
├── Excursion disappears → logged as support for MC-noise explanation;
│     Gate 3 status remains FAIL; §10 reframing remains unadopted;
│     any future Gate 3 correction requires its own new addendum
└── Excursion persists → MC noise ruled out; new, separately-scoped
      root-cause diagnostic required (out of this plan's scope);
      Gate 3 status remains FAIL
```

---

## 6. Required artifacts and commit points

Strict order. Each commit's preconditions must be satisfied — and, for
execution commits, its pre-registration commit must already exist —
before that commit is made.

| # | Commit | Contents | Precondition |
|---|---|---|---|
| C1 | Governance batch | G0–G3: the construction-attempt-cap statement (G0), `docs/RESEARCH_LINEAGE_REGISTER.md` (new platform-level register, seeded with this cycle's Attempt 1/Attempt 2 entries for `gate2_score_acf_target_fn`), Addendum, both V2 drafts, `research_archive/positive_control_phase3/`, Decision doc, `decision_log.md` Entry 5, Decision doc filed to `reviewer_reports/` | None (first commit) |
| C2 | Standing-rule promotion | G4 (GOV-1, extended to Gate 3) + G5 (leakage firewall, extended to target-function tuning) into `RESEARCH_GOVERNANCE_STANDARD.md` | C1 |
| C3 | Track Separation Charter | G6 (may be satisfied by this document's §0, already committed with it) | C1 |
| C4 | A0 + A1 pre-registration | Fresh seed family, A1's full pre-registration (§3) | C2, C3 |
| C5 | A1 execution output | Dated JSON (e.g. `generator_fidelity_results_trackA1_<date>.json`), second-implementation output (G7), reconciliation note | C4; G7 implementation must exist |
| C6 | Decision-log entry — Track A1 result | PASS / PARTIAL / ANOMALY verdict, per §4 | C5 |
| C7 | G8 blind re-derivation report | Filed to `reviewer_reports/` | May start any time after C1; must close before A-Adoption Gate |
| C8 | A2 pre-registration | Full pre-registration (§3) | C6 (A1 complete) |
| C9 | A2 execution output + decision-log entry | Dated results file, CONFIRMED/NOT CONFIRMED verdict | C8 |
| C10 | A3-entry pre-registration (stopping rule) | Full pre-registration (§3), including the authored, Level 2-reviewed stopping/interpretation rule | C6 shows PARTIAL; skipped entirely if A1 = PASS (log the skip instead) |
| C11 | A3 execution output + decision-log entry | 4-point N-sweep results, OUTCOME 1/2 verdict and, if OUTCOME 2, the Level-2-reviewed path-selection entry (§5) recording which of paths (a)/(b)/(c) was selected, its rationale, its rejected alternatives, and its governance justification — committed *before* the selected path's own pre-registration | C10 |
| C12 | A-Adoption Gate decision-log entry | Full citation of C5/C6, C9, C11 (if run), C7, G7 reconciliation; explicit lag/`w` coverage statement preserving the honest-framing caveat; Level 2 sign-off | All of §4's A-Adoption Gate preconditions |
| C13 | (Only after C12) target_fn code change | The only commit in this entire plan that may modify `target_fn` in the fidelity-gate implementation | C12 |
| — | *(Track B, parallel timeline, never interleaved with C1–C13's numbering)* | | |
| D1 | Gate 3 Scope Charter | Confirms Track B separation (mirrors C3 but is its own commit, never combined with Track A commits) | C1 |
| D2 | B1 pre-registration | Full pre-registration (§3) | D1 |
| D3 | B1 execution output + decision-log entry (clearly labeled `[Gate 3 Track]`, never combined with a Track A entry) | Dated results, verdict per §4 | D2 |

---

## 7. Standing prohibitions (auditor checklist)

- [ ] No target function, tolerance, seed, `R`, `N`, or stopping rule
      is ever adjusted after its pre-registration commit, for any
      reason, including proximity to a decision boundary.
- [ ] No second Gate 2 correction proceeds without: an independently
      named mechanism, pre-registered before being checked against the
      residual, and a fresh Level 2 review of that specific correction
      (GOV-1, C2).
- [ ] No document, decision-log entry, commit, or review combines
      Track A and Track B findings, conclusions, or votes.
- [ ] No adoption of `G(k)` (or any future corrected target) occurs
      outside the A-Adoption Gate (§A-AG), and no adoption entry omits
      the honest-framing caveat on lag/`w` coverage.
- [ ] No empirical reference curve is used for Gate 2 unless at least
      one theory-based correction attempt (path (a)) has already been
      tried and failed, and the curve's own reference run is
      pre-registered and firewalled from the runs it validates
      (Decision §5).
- [ ] No Gate 3 status, cutoff, or target changes on the strength of
      Addendum §10 or B1 alone — only through a separate, later,
      independently-scoped addendum and its own adoption gate.
- [ ] Every review record states its independence level (1/2/3)
      explicitly; no Level 2 review is described as unqualified
      "independent" (Standard §4).
- [ ] No theory-based Gate 2 target-correction attempt beyond Attempt 3
      (G0's cap) is ever pre-registered, executed, or checked against
      data under this Plan; once the cap is exhausted, only §5 path (b)
      or (c) remain available, and any further theory-based work
      requires a wholly new Phase 1–2 hypothesis cycle, not a further
      attempt under this Plan (G0).
