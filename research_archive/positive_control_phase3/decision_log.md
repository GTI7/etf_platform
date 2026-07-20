# Positive Control Study — Phase 3 Decision Log

**Status: append-only**, per `docs/RESEARCH_GOVERNANCE_STANDARD.md`
§5. New entries are appended; existing entries are never edited or
removed. A correction to an entry is added as a new, separately dated
entry cross-referencing the one it corrects. This log records process
decisions for the Positive Control study's Phase 3 (Pre-validation)
work only; it does not itself evaluate, redesign, or freeze any element
of the study's methodology.

---

## Entry 1 — v2 proposal reviewed at Governance Level 2: NOT READY FOR FREEZE

- **Date:** 2026-07-20
- **Decision:** `docs/POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md`
  reviewed and found **NOT READY FOR FREEZE**, notwithstanding its own
  §16 Recommendation declaring READY FOR FREEZE. Three specific defects
  identified: (1) unsupported "Independent Validation Committee /
  APPROVE WITH CONDITIONS" language implying organizational independence
  that does not exist on this platform, contradicting
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §4's explicit prohibition on
  describing a Level 2 review as unqualified "independent"; (2) §1.3
  conflated a mathematically proven property (forward_return/SMA
  independence via disjoint time support; finite-memory cutoff; zero
  correlation after horizon `h`) with an unproven empirical claim
  (exact intermediate-lag score ACF shape after rank transformation)
  presented with the same certainty; (3) the document's own §1.6 names
  the Phase 3 pilot run (fidelity gate execution + calibration table)
  as "the one genuinely outstanding pre-Freeze action" — and that pilot
  had never been run. Declaring Freeze-ready while disclosing an
  unexecuted required Pre-validation step violates
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2's phase ordering directly.
- **Governance status:** Phase 3 (Pre-validation) — reopened / continued.
  Phase 4 (Methodology Freeze) — **not** entered; this document's prior
  self-declared readiness is superseded by this entry, not by editing
  v2's own text in place (the corrections are applied as a tracked,
  reviewable diff to v2, per the same document-family supersession
  discipline `docs/RESEARCH_GOVERNANCE_STANDARD.md` §5 requires for
  every other artifact on this platform).
- **Reviewer level:** Level 2 — AI-assisted adversarial (procedurally
  independent: a review pass with no participation in authoring v2;
  **not organizationally independent** — same disclosed limitation as
  every other Level 2 review on this platform, per
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §4). No Level 3 review exists
  or is available on this platform.
- **Known limitations:** This entry records the review's verdict and
  its stated reasons; it does not itself execute any remediation — see
  Entries 2–4 for the remediation this verdict required.

## Entry 2 — Fidelity tolerance procedure frozen before execution

- **Date:** 2026-07-20
- **Decision:** The generator-fidelity gate's tolerance procedure
  (confidence level, estimator, deviation metric, and pilot-size
  derivation) was specified in writing — new §2a of
  `docs/POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md` — **before**
  any pilot replication was generated or any fidelity result observed,
  closing the gap Entry 1's review implicitly required (V2 §2 promised
  a tolerance band that is "a statistically principled band, not an
  eyeballed one" but never specified the method). Method: 95% two-sided
  Monte Carlo tolerance band around the mean pooled ACF estimate across
  `R` independent replications; `R` (and the calibration pilot's `P`)
  derived from a closed-form Fisher correlation-estimator variance
  bound targeting `SE ≤ 0.01` (half the frozen `0.02` effect-size grid
  spacing), in the same style as V2 §6's existing `M` derivation.
  Result: `R = 25` (fidelity), `P = 500` (full calibration, not fully
  executed — see Entry 4).
- **Evidence references:** `docs/POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md`
  §2a (this same change); `pilot_results.md` §5a (this directory).
- **Governance status:** Phase 3 — tolerance procedure specified,
  deterministic, and not subject to post-hoc adjustment per its own
  terms.
- **Reviewer level:** Level 1 (self-authored, at the direction of Entry
  1's review verdict). No Level 2 confirmation of this specific
  procedure's completeness has been obtained as of this entry — a real,
  disclosed gap, not resolved here.
- **Known limitations:** The derivation's own conservative constants
  (Fisher's asymptotic bound, worst-case `ρ ≈ 0`) are standard,
  closed-form, and not fit to any observed data from this study, but
  they are themselves a modeling choice; a materially different
  variance structure in the actual generator (discovered by Entry 3's
  execution) would not invalidate the procedure but could mean `R`/`P`
  under- or over-shoot their own stated precision target in practice.

## Entry 3 — Phase 3 pilot executed: generator-fidelity gate FAILS at the anchor point

- **Date:** 2026-07-20
- **Decision:** `experiments/positive_control_phase3_pilot.py` executed
  the generator-fidelity gate (V2 §2, tolerance procedure per Entry 2)
  at the frozen anchor dimension point (25 instruments, 463 days, h=20,
  β=0.30), R=25 replications, SHA-256-derived seeds (V2 §8, base seed
  `20260720`). Result: **Gate 1 (return-side ACF) PASS**; **Gate 2
  (score-side ACF) FAIL** (16 of 20 lags outside tolerance, score's
  empirical ACF decaying measurably faster than the closed-form
  Bartlett(h) target V2 §1.3 claimed it would inherit); **Gate 3
  (combined daily-IC-series ACF decay by lag h) FAIL** (lags 44–51 of
  the checked 20–60 range fall outside tolerance, a mild, unexplained
  negative excursion). This is the first point in this study's
  lifecycle any fidelity measurement has been computed — no such
  measurement existed anywhere on this platform before this entry.
- **Evidence references:**
  `research_archive/positive_control_phase3/generator_fidelity_results.json`
  (full per-lag output, all 25 seeds); `pilot_results.md` §5b (this
  directory); `experiments/positive_control_phase3_pilot.py`.
- **Governance status:** Phase 3 — generator-fidelity gate executed,
  **not passed** at the anchor point. Per
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §2 Phase 3, "the methodology
  used to evaluate each attempt may not change once the first attempt
  is logged" — no element of V2's frozen tolerance procedure (Entry 2)
  or generator model (V2 §1.2) was altered in response to this result;
  this entry reports the result as measured. Any future change to the
  generator construction in response to Gate 2/3's failure is a new,
  separately logged construction attempt under Phase 3's normal
  discipline, not a silent patch.
- **Reviewer level:** Level 1 (self-review) only. No Level 2 or above
  confirmation of this specific execution's code correctness or
  numerical output has been obtained.
- **Known limitations:** Horizon-sweep spot checks (h=10/20/40) not
  run — anchor point only. Gate 3's lags 44–51 dip is measured but not
  root-caused (real generator property vs. Monte Carlo noise at R=25 in
  that lag range — undetermined). No independent reproduction of these
  figures via a second, independently written implementation exists
  (contrast with H3 Gate 1's practice, `research_archive/reference_h3/decision_log.md`
  Entry 13) — a real gap relative to this platform's own established
  practice for reporting a first quantitative result.

## Entry 4 — Phase 3 pilot executed: reduced-scale `w ↔ ρ_true` calibration pass

- **Date:** 2026-07-20
- **Decision:** The same runner executed a **deliberately reduced,
  explicitly preliminary** pass of the V2 §1.6 calibration procedure:
  11 of the frozen 41 `w` grid points (`w = 0.0, 0.1, ..., 1.0`), at
  `P_pilot = 50` of the `P = 500` replications per point Entry 2's
  derivation requires for full precision. Results (mean measured
  `ρ_true` per `w`, with SE) recorded in `rho_calibration.csv`.
  Sanity checks pass (`w=0 → ρ̂≈0`, `w=1 → ρ̂=1.0` exactly, monotone,
  visibly nonlinear curve). **No isotonic fit or `w↔ρ_true` lookup-table
  inversion was performed** — computing one from an 11-point, P=50 pass
  and presenting it as V2 §1.6's frozen lookup table would misrepresent
  its precision against the procedure's own stated `SE ≤ 0.01` target
  (this pilot's SEs range from 0.0042 to 0.0052 at the weakest points,
  already close to target by chance at n=50, but the point count itself
  — 11 of 41 — is the binding shortfall, not just replication count).
- **Evidence references:**
  `research_archive/positive_control_phase3/rho_calibration.csv`;
  `pilot_results.md` §5c (this directory);
  `experiments/positive_control_phase3_pilot.py`.
- **Governance status:** Phase 3 — calibration procedure demonstrated
  end-to-end and executed at reduced scale; **not** complete against
  its own frozen precision requirement (Entry 2). Remains a required,
  not-yet-satisfied element before `docs/POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md`
  §1.6 can be considered fulfilled or Methodology Freeze opened.
- **Reviewer level:** Level 1 (self-review) only.
- **Known limitations:** Full-scale execution (41 points × 500
  replications ≈ 100x this pass's compute) was not attempted in this
  pass; wall-clock cost at full scale has not been measured and may
  require either a longer-running job or a design change (e.g. a
  faster implementation) before it is practical to run routinely. No
  Level 2 review of this pass's code or output exists.

## Entry 5 — Phase 3 Remediation Decision reviewed and filed: diagnostic-only acceptance, Gate 2/3 status unchanged

- **Date:** 2026-07-20
- **Decision:** `docs/POSITIVE_CONTROL_PHASE3_REMEDIATION_DECISION.md`
  (the "Remediation Decision"), reviewing
  `docs/POSITIVE_CONTROL_PHASE3_ANALYTICAL_CORRECTION_ADDENDUM.md` (the
  "Addendum") together with Entries 1–4 of this log and
  `pilot_results.md`, is filed and adopted at Governance Level 2.
  Verdicts: (a) the Addendum is **ACCEPTED as diagnostic/theoretical
  research only** — its closed-form derivation (Lemma 1, Sheppard's
  grade-correlation identity, the Bartlett(k) kernel, the cross-lag
  triangle function) contains no error found on spot-check, but is
  **NOT accepted as a completed Gate 2 correction** and **NOT** grounds
  to change any operative gate behavior, target function, or governance
  status by itself; (b) the Remediation Decision §4/§5/§6 requirement
  list is adopted in full as conditions precedent to any operative Gate
  2 change — in particular: §12 step 1 must be executed as an actual
  gate rerun (not the existing post-hoc §9 arithmetic comparison
  against already-recorded data) using a **fresh, independently-drawn
  seed set**, distinct from the original R=25/seed-25 run the
  correction was derived in response to; §12 step 3's N-sensitivity
  diagnostic must be run to a **pre-registered stopping/interpretation
  rule**, written before execution, before G(k) may be adopted as Gate
  2's operative target anywhere; an independent Level 2 blind
  re-derivation of Addendum §3–§8 and a second, independently-written
  implementation of the fidelity-gate computation are both required
  before adoption; §12 step 2 (w-blend cross-term test) must be
  executed before G(k) plus the cross term is used anywhere w>0
  matters; an R-increase for the rerun is optional; (c) Gate 3
  **remains FAIL, unresolved** — the Addendum's §10 finding (true
  independence cutoff `2h=40`, not `h=20`) is accepted only as a
  correct, out-of-scope structural observation and is explicitly
  **NOT** accepted as an explanation for the lags 44–51 failure; any
  future Gate 3 correction requires its own separate, later,
  independently-scoped addendum, never bundled with Gate 2 remediation.
- **New standing-rule recommendation (not yet promoted):** no more than
  one theory-based target correction may be applied to a gate without a
  fresh Level 2 review of that specific correction; any subsequent
  correction motivated by a residual observed after a prior correction
  must pre-register its candidate mechanism before being checked
  against data ("GOV-1"). Promotion into
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` is tracked as
  `docs/POSITIVE_CONTROL_PHASE3_CONTROLLED_EXECUTION_PLAN.md` G4, not
  yet executed as of this entry.
- **Governance status:** Phase 3 (Pre-validation) — unchanged from
  Entry 4's status. Gate 2: FAIL, operative target remains Bartlett(k)
  pending the conditions in (b) above. Gate 3: FAIL, unresolved. Phase
  4 (Methodology Freeze): **not open**, unaffected by this entry.
- **Evidence references:**
  `docs/POSITIVE_CONTROL_PHASE3_REMEDIATION_DECISION.md` (filed to
  `reviewer_reports/2026-07-20_phase3_remediation_decision.md` in this
  same commit); `docs/POSITIVE_CONTROL_PHASE3_ANALYTICAL_CORRECTION_ADDENDUM.md`;
  `docs/POSITIVE_CONTROL_PHASE3_CONTROLLED_EXECUTION_PLAN.md` (the
  execution sequencing this decision's conditions must follow);
  `docs/RESEARCH_LINEAGE_REGISTER.md` entry `gate2_score_acf_target_fn`
  (cross-cycle attempt tracking for the Gate 2 target correction
  referenced in (b)).
- **Reviewer level:** Level 2 — AI-assisted adversarial, procedurally
  independent (no participation in authoring the Addendum or V2);
  **not organizationally independent** — same disclosed limitation as
  every other Level 2 review on this platform, per
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §4. No Level 3 review exists
  or is available on this platform.
- **Known limitations:** This entry records the Remediation Decision's
  verdicts and makes them operative as of this commit; it does not
  itself execute any of the conditions in (b) — those remain open per
  `docs/POSITIVE_CONTROL_PHASE3_CONTROLLED_EXECUTION_PLAN.md` §1
  (G0–G8) and §2–§6 (Track A/B diagnostics), none of which have been
  executed as of this entry.

---

## Current status (as of Entry 5)

- **Committee-language and §1.3 proven/empirical corrections
  (Entry 1's items 1–2):** applied to
  `docs/POSITIVE_CONTROL_VALIDATION_STUDY_PROPOSAL_V2.md` in this same
  change.
- **Fidelity tolerance procedure (Entry 1's item 3, partial):**
  specified (Entry 2) and executed (Entry 3) — **FAILS** at 2 of 3
  gates at the anchor point. This is a real, open methodological
  problem, not a documentation gap.
- **Calibration procedure:** demonstrated but not executed at required
  precision (Entry 4).
- **Gate 2 remediation (Entry 5):** the Addendum's theory-based
  correction is accepted as diagnostic research only; Gate 2's
  operative target has **not** changed and remains gated on
  `docs/POSITIVE_CONTROL_PHASE3_CONTROLLED_EXECUTION_PLAN.md`'s G0–G8
  and Track A diagnostics (A1–A3), none executed yet.
- **Gate 3 (Entry 5):** remains FAIL, unresolved; the Addendum's §10
  reframing is not adopted; any correction requires a separate,
  later-scoped addendum (Track B, single authorized diagnostic B1, not
  yet executed).
- **Phase 4 (Methodology Freeze):** **not open.** No `methodology.md`
  exists. Per this log, Freeze cannot be responsibly opened while the
  fidelity gate fails at the anchor point the freeze would apply to.
- **No real market outcome data** has been read, computed, or
  referenced at any point reflected in this log.
- **This directory, `experiments/positive_control_phase3_pilot.py`,
  the Addendum, both V2 drafts, the Remediation Decision, and
  `docs/RESEARCH_LINEAGE_REGISTER.md` are committed together in the
  same commit as this Entry 5** (C1 per the Controlled Execution
  Plan) — the first commit hash for any of this evidence. Per
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §3's own standard, nothing
  here should be treated as having committed provenance until that
  commit exists.
