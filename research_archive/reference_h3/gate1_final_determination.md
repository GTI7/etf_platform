# H3 Gate 1 — Final Determination Record

**Scope.** This record renders the final determination for **Gate 1
only** — "Candidate signal independence verified," as defined by
`docs/REFERENCE_H3_PREVALIDATION_PLAN.md` Section 4 — consolidating the
existing quantitative validation and its independent reproduction into
a single governance decision record. It does not perform new analysis,
does not modify H3's methodology or scoring logic, and does not
reinterpret any reported figure. It is not a Phase 7 Decision for H3 as
a whole (Gate 4 remains unassessed; see Section 6 below).

---

## 1. Decision

**Gate 1: PASS.**

The frozen H3 construction (Attempt 1) was checked against REFERENCE
v1's frozen MOMENTUM score per the pre-validation plan's Section 2
methodology. The degenerate-case boundary was not triggered, the
resulting moderate correlation has a documented economic explanation
that pre-dates the measurement, and the calculation was independently
reproduced — not merely inspected — per Section 4's duty 4. This PASS
is recorded at **Level 2 (AI-assisted adversarial) review**, the tier
this platform's governance standard treats as sufficient for a
Phase 3 gate (see Section 4 below); it is not, and is not represented
as, an organizationally independent determination.

This PASS applies to **Gate 1 alone**. It does not, by itself,
authorize proceeding to a frozen H3 specification — that requires all
four gates satisfied (Section 6), and Gate 4 has not yet been assessed.

---

## 2. Evidence basis

| Element | Value |
|---|---|
| Frozen commit | `07f0da379d8cccf06d17c34a51cbb557da047fef` |
| Methodology | `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` Section 2 ("Research independence verification") and Section 4 ("Research decision gates" / "Independent confirmation duties"), as committed at the frozen commit above |
| Validation report | `docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md` (2026-07-19) |
| Reproduction review | `docs/H3_GATE1_REPRODUCTION_REVIEW.md` (2026-07-19, Level 2, procedurally independent session) |
| Supporting evidence artifacts | `experiments/validate_h3_gate1_independence.py`; `research_archive/reference_h3/gate1_independence_analysis_2026-07-19.json` |
| Governance framework in effect | `docs/RESEARCH_GOVERNANCE_STANDARD.md` v1.0 |
| Prior gate context | `research_archive/reference_h3/decision_log.md` Entries 7, 8, 11 (Gates 2, 3, and Gate 1 readiness, respectively) |

Both the validation report and the reproduction review confirm the
repository state matched the cited freeze commit exactly, with no
drift on any frozen file (`attempt_001_specification.md`,
`docs/REFERENCE_H3_PREVALIDATION_PLAN.md`,
`docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md`,
`docs/RESEARCH_GOVERNANCE_STANDARD.md`).

---

## 3. Validation summary

**Independence result.** Measured against the plan's one hard,
mathematically provable rejection trigger (near-1.0 median correlation
to the degenerate single-benchmark-subtraction case), the construction
is unambiguously clear: observed median correlation 0.108, far from
1.0. Per the plan's ambiguity-resolution principle, this result is
treated as the stricter "moderate correlation" case, which requires a
written economic explanation before Gate 1 is satisfied. That
explanation already existed, pre-dating this measurement, in
`attempt_001_specification.md` Section 4 (the pre-registered
expectation that H3 and MOMENTUM would show some positive correlation
as "sibling" factors derived from the same underlying price history).

**Spearman findings.** Daily cross-sectional Spearman rank correlation
between the H3 score and REFERENCE v1's MOMENTUM score, across 483
evaluated trading dates (2024-08-13 through 2026-07-17): mean 0.1008,
median 0.1085, interquartile range -0.0362 to 0.2292, full range
-0.3223 to 0.4515. The interquartile range straddles zero — the sign
of the day-to-day relationship is not stable, only its central
tendency is mildly positive. These figures were independently
recomputed by the reproduction review, both by re-running the
committed script against the live database and via an independently
written second implementation sharing no code with the original, and
matched to full floating-point precision.

**Rank overlap findings.** Top-5 overlap fraction: mean 0.2017, median
0.20 — at the 0.20 chance baseline (5-of-25 random rankings). Bottom-5
overlap fraction: mean 0.3379, median 0.40 — roughly double the chance
baseline. This bottom-tail asymmetry was independently reproduced
exactly and is flagged as a specific, unresolved observation requiring
attention; neither the original report nor the reproduction review
explains it (Section 5 below).

**Data limitations.** 19 of the nominal 502 window dates
(2024-07-17 through 2024-08-12) could not be evaluated because no
`Score` row exists in the database for any ETF in that range — a gap
on the MOMENTUM/`Score` side, not the H3 side, independently confirmed
against the live database by direct query in the reproduction review.
Gate 1 therefore evaluates 483 of 502 window dates (96.2%). Separately,
the evaluated window spans a single ~2-year historical period, not
multiple independent market regimes.

---

## 4. Governance status

**Reviewer level: Level 2 — AI-assisted adversarial review**, per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 4.

This review is **procedurally independent**: a fresh session with no
conversational continuity to the session that produced the validation
report, which independently recomputed — not merely inspected — the
rank-correlation and score-overlap figures, both by re-running the
committed script and via a second, independently written
implementation sharing no code with the original.

This review is **not organizationally independent**: the same AI model
vendor performed both the original work and its review, both were
directed by the same single operator, no incentive separation exists
between "doing the work" and "reviewing the work," no standing
accountable reviewer role persists across cycles, and the claim of "no
conversational memory" is self-reported and not third-party-verifiable.
This is the same tier already used, and disclosed in the same terms,
for Gates 2 and 3 in this archive (`decision_log.md` Entries 7 and 8).

Per `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` Section 4, the
independent-confirmation duties for Gate 1 are: (1) review the
complete construction attempt log; (2) confirm no outcome data was
used; (3) confirm REFERENCE v1/H1 results did not influence
construction selection; (4) independently reproduce the rank-
correlation and score-overlap calculations; (5) record the
confirmation. The reproduction review performed duty 4 with full
rigor (byte-for-byte figure match via two independent code paths).
Duties 1–3 were read and no contradiction was found, but the
reproduction review's own text states a full adversarial audit of
those attestations was not the task it was scoped to perform — this is
recorded here as a disclosed gap, not resolved by this determination.

---

## 5. Remaining limitations

1. **No Level 3 (organizationally independent) review exists or is
   available.** Per `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 4,
   this platform has never performed a Level 3 review for any gate,
   including this one, because it operates with a single human
   operator directing all research and all review sessions. This gate
   is satisfied at Level 2 only.
2. **Dataset hash / provenance controls are incomplete.** Per
   `decision_log.md` Entry 12's own disclosure, the missing durable
   dataset-hash policy called for by
   `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 5
   (`dataset_manifest.json`, `dataset_hashes/`) remains open and was
   not closed by any artifact cited in this record.
3. **The bottom-tail overlap asymmetry is unexplained.** Bottom-5
   overlap (median 40%) is roughly double top-5 overlap (median 20%,
   at chance) — independently confirmed as a measured fact, but not
   explained, by either the validation report or the reproduction
   review. Both flag it for further attention rather than resolving
   it.
4. **Duties 1–3 of the independent-confirmation requirement** were
   read but not subjected to a full adversarial audit by the
   reproduction review, by its own account (Section 4 above).
5. **19 of 502 nominal window dates could not be evaluated**, due to a
   `Score`-table coverage gap disclosed in Section 3 above.
6. **Gate 4** (no unresolved specification degrees of freedom) has not
   been assessed by any evidence source cited in this record.

---

## 6. Next allowed action

**Gate 1, individually, is satisfied and requires no further action of
its own** at the Level 2 tier this platform's governance standard
treats as the default for Phase 3 gates.

**H3 as a whole may not yet proceed to a frozen specification
(Phase 4).** Per `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` Section 6,
a PASS enabling H3 specification work requires all four gates
satisfied: Gates 2 and 3 already PASS (`decision_log.md` Entries 7–8);
Gate 1 PASSes per this record; **Gate 4 (no unresolved degrees of
freedom) has not been assessed** by any cited evidence source and
remains the outstanding blocker before Phase 3 as a whole can close.

Consistent with `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 5
(`decision_log.md` is append-only), the appropriate bookkeeping step —
outside the scope of this record — is for whoever maintains
`research_archive/reference_h3/` to append a new dated entry to
`decision_log.md` reflecting this Gate 1 PASS, consistent with how
Entries 7, 8, and 11 recorded Gates 2, 3, and Gate 1 readiness. This
record does not make that edit itself, since `decision_log.md`'s
append-only discipline and its maintenance are a decision for that
document's own owner, not this consolidation task.

No H3 methodology, scoring logic, parameter, benchmark, universe, or
acceptance criterion was modified, tuned, or reinterpreted to produce
this determination.
