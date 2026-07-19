# H3 Gate 4 — Final Determination Record

**Scope of this record.** This is a governance decision record only. It
consolidates existing Gate 4 evidence into a single determination; it
performs no new research, modifies no H3 methodology, scoring logic,
parameter, or acceptance criterion, and introduces no metric or finding
not already present in the cited sources.

---

## 1. Decision

**Gate 4: PASS.**

The frozen H3 construction (Attempt 1) was audited for unresolved
researcher degrees of freedom per
[`docs/H3_GATE4_DEGREES_OF_FREEDOM_AUDIT.md`](../../docs/H3_GATE4_DEGREES_OF_FREEDOM_AUDIT.md).
Six of seven audited categories are CONTROLLED; the remaining two
(evaluation window, acceptance criteria) are PARTIALLY CONTROLLED with
disclosed, non-blocking limitations rather than concealed or
outcome-driven adjustments. No blocking issue was identified in that
audit.

---

## 2. Scope

Gate 4, as assessed by the cited audit, evaluated four things:

1. **Unresolved degrees of freedom** — whether every material design
   choice a specification would need to state exactly once (universe,
   peer-group/segment definition, lookback, scoring formula,
   missing-data handling, evaluation window, interpretation criteria)
   has exactly one, already-fixed answer.
2. **Researcher discretion** — whether any of those choices was left
   open to be decided informally, case-by-case, or "once the data is
   seen," rather than fixed in writing in advance.
3. **Hindsight bias risk** — whether any choice could have been
   selected, adjusted, or reverse-engineered using knowledge of an
   outcome, a correlation figure, or a prior research cycle's result.
4. **Methodology pre-commitment** — whether the construction and its
   evaluation criteria were committed to the record, in an immutable
   form, before the measurement they govern was performed.

Gate 4 does not evaluate investment performance, does not compute or
interpret any forward-return or significance statistic, and does not
itself authorize implementation — those remain separate, later
questions under this project's own research lifecycle
(`docs/RESEARCH_GOVERNANCE_STANDARD.md` §2).

---

## 3. Evidence Basis

- **Gate 4 audit report:**
  [`docs/H3_GATE4_DEGREES_OF_FREEDOM_AUDIT.md`](../../docs/H3_GATE4_DEGREES_OF_FREEDOM_AUDIT.md)
  — the primary evidence for this record; all findings below are drawn
  from it without modification.
- **Gate 1 final determination:**
  [`gate1_final_determination.md`](gate1_final_determination.md) (this
  archive directory — no `docs/H3_GATE1_FINAL_DETERMINATION.md` exists;
  the corresponding record lives here and is committed at `a2cafac`).
- **Frozen specification:**
  [`attempt_001_specification.md`](attempt_001_specification.md), as
  fixed at the freeze commit below.
- **Freeze provenance:**
  [`FREEZE_RECORD.md`](FREEZE_RECORD.md) — commit
  `07f0da379d8cccf06d17c34a51cbb557da047fef`.
- **Process record:** [`decision_log.md`](decision_log.md), Entries
  1–12.
- **Governance framework:**
  [`docs/RESEARCH_GOVERNANCE_STANDARD.md`](../../docs/RESEARCH_GOVERNANCE_STANDARD.md)
  v1.0.

**Summary of audited elements**, as documented in the Gate 4 audit
report:

- **Universe selection** — the 25-ETF universe was reused unchanged from
  `experiments/daily_etf_universe_update.py:89-120`, a file the Gate 4
  audit confirmed via git history (`git merge-base --is-ancestor`)
  predates H3's first construction attempt by two days and was authored
  for an unrelated purpose.
- **Segment definitions** — six segments partitioning all 25 ETFs with
  no overlap or residual, reused verbatim from the same pre-existing,
  pre-H3 file. The disclosed 2-member Global equity segment is recorded
  as a known structural limitation, not silently corrected.
- **Scoring methodology** — the peer-relative excess-return formula was
  frozen with two rejected alternatives (single common-benchmark
  subtraction; leave-one-out universe-mean subtraction) ruled out by
  algebraic proof of rank-identity to absolute-return ranking, derived
  before any Gate 1 correlation figure was computed.
- **Lookback choice** — the 60-trading-day window is justified on two
  non-outcome grounds (institutional review cadence; reuse of an
  already-frozen window from a prior, unrelated research cycle) and was
  explicitly not set to match MOMENTUM's own 20-day window.
- **Missing-data rules** — the exclusion rule (no forward-fill, no
  interpolation) was frozen before Gate 1 ran and independently verified
  to have produced a full 25-ETF cross-section on every evaluated date.
- **Evaluation window** — the nominal window was reused unchanged from
  REFERENCE v1's own frozen window; 19 of 502 nominal dates were
  mechanically dropped due to a database coverage gap discovered during
  validation, independently reconfirmed, and disclosed rather than
  concealed.
- **Acceptance criteria** — Gate 1's own PASS/FAIL interpretation rule
  was frozen before any Gate 1 figure existed. The acceptance criteria
  for H3's eventual significance test remain unwritten, explicitly
  deferred to the Methodology Freeze phase per this project's own phase
  sequencing, not concealed as already resolved.

---

## 4. Degrees-of-Freedom Summary

| Category | Status |
|---|---|
| Universe | CONTROLLED |
| Lookback | CONTROLLED |
| Segments | CONTROLLED |
| Scoring | CONTROLLED |
| Missing data | CONTROLLED |
| Evaluation window | PARTIALLY CONTROLLED |
| Acceptance criteria | PARTIALLY CONTROLLED |

---

## 5. Governance Classification

**Review level: Level 2 — AI-assisted adversarial review**, per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4, consistent with the tier
already recorded for every other gate review in this archive (Gates 1,
2, 3; `decision_log.md` Entries 7, 8, 11).

This review is **procedurally independent**: the Gate 4 audit was
performed in a session distinct from the sessions that produced the
frozen specification and the Gate 1 evidence, adopted an adversarial
posture toward the record rather than accepting it at face value, and
independently verified — via git history (`git log --follow`,
`git merge-base --is-ancestor`) and direct inspection of cited source
documents — claims that the underlying reports made about themselves,
rather than relying on those reports' own descriptions.

This review is **not organizationally independent**: the same AI model
vendor performed the work being audited and the audit itself, both were
directed by the same single operator, no incentive separation exists
between "doing the work" and "reviewing the work," no standing
accountable reviewer role persists across cycles, and no third party can
verify the claim of session-to-session discontinuity. Per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §4, this record does not use the
unqualified term "independent review" to describe any review in this
chain.

No Level 3 (organizationally independent, distinct-reporting-line)
review has ever been performed on this platform, for H3 or any prior
research cycle.

---

## 6. Remaining Limitations

Preserved from the Gate 4 audit and Gate 1 final determination records,
unmodified:

1. **No Level 3 (organizationally independent) review exists or is
   available** for H3 or any prior cycle on this platform. Every
   finding in this record rests on Level 2 evidence at most.
2. **Evaluation window is only partially controlled.** 19 of 502 nominal
   window dates could not be evaluated due to a database coverage gap on
   the MOMENTUM/`Score` side, disclosed and independently reconfirmed —
   not a discretionary window choice, but the realized evaluation set
   was only established during validation, not fully known at freeze
   time.
3. **Acceptance criteria for H3's eventual significance test remain
   deferred.** Gate 1's own interpretation rule is frozen and was
   applied without amendment; the acceptance criteria for the
   *eventual* significance test have not been written, appropriately
   sequenced to the Methodology Freeze phase, but still an open item.
4. **Bottom-tail rank-overlap asymmetry is measured but unexplained.**
   Bottom-5 overlap (median 40%) is roughly double top-5 overlap (median
   20%, at chance), confirmed identically by independent reproduction of
   the underlying Gate 1 figures; neither the Gate 1 evidence nor the
   Gate 4 audit resolves it.
5. **Provenance/archival gaps remain open**, carried forward from
   `gate1_final_determination.md` §5: the dataset-hash / provenance
   policy called for by `docs/RESEARCH_GOVERNANCE_STANDARD.md` §5
   (`dataset_manifest.json`, `dataset_hashes/`) has not been
   implemented; and `decision_log.md` (Entries 1–12, "Current status")
   has not yet been appended with an entry reflecting either Gate 1's
   PASS or this Gate 4 determination — it still reads, as of the
   evidence reviewed for this record, "Gate 4 (no unresolved degrees of
   freedom): not assessed."
6. **This record's own review tier applies to itself.** This
   determination is authored at Level 2 (procedurally, not
   organizationally, independent), consistent with Section 5 above —
   it does not upgrade the independence tier of any evidence it
   consolidates.

---

## 7. Next Allowed Action

**Gate 4, individually, is closed at PASS**, at the Level 2 review tier
this platform's governance standard treats as the default for Phase 3
gates.

**H3 as a whole may not yet proceed to a frozen specification (Phase
4).** Per `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §6 and
`docs/RESEARCH_GOVERNANCE_STANDARD.md` §2, that step requires all four
Phase 3 gates satisfied and the evidence package archived per §5. Gates
2 and 3 are already PASS; Gate 1 is PASS (`gate1_final_determination.md`);
this record closes Gate 4 at PASS. However, two archival items from
Section 6 above remain outstanding and are not resolved by this record:
appending Gate 1's and Gate 4's outcomes to `decision_log.md`, and
closing the dataset-hash/provenance policy gap. Whoever maintains
`research_archive/reference_h3/` should treat those as the next
bookkeeping steps — this record does not make those edits itself,
consistent with `decision_log.md`'s append-only discipline being a
decision for that document's own owner.

No new methodology is defined by this record. No H3 scoring logic,
parameter, benchmark, universe, or acceptance criterion was modified,
tuned, or reinterpreted to produce this determination.
