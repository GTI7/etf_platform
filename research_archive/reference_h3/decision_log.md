# REFERENCE H3 — Decision Log

**Status: append-only.** Per `docs/RESEARCH_GOVERNANCE_STANDARD.md`
Section 5, this is the single, chronological record of every decision
point in the H3 pre-validation cycle. New entries are appended; existing
entries are never edited or removed. A correction to an entry is added as
a new, separately dated entry cross-referencing the one it corrects. This
log was created retroactively on 2026-07-19 to consolidate decision points
that were, until now, scattered across nine documents — closing the gap
`docs/H3_GOVERNANCE_COMPLIANCE_AUDIT.md` Section 7, item 4 identified. It
does not restate those documents in full; each entry references the
primary source rather than duplicating it.

This log records process decisions only. It does not itself evaluate,
redesign, or change any H3 methodology, scoring logic, or prior gate
determination.

---

## Entry 1 — Candidate selection: H3 ranked first

- **Date:** 2026-07-18 23:37
- **Decision:** H3 (ETF-segment relative-strength rotation) ranked #1 of
  7 remaining candidate hypotheses, against four fixed criteria (economic
  justification, independence from REFERENCE v1/v2 H1, data availability,
  overfitting risk).
- **Evidence references:** `docs/REFERENCE_RESEARCH_ROADMAP_NEXT.md`
  (commit `1091a01`); rejected-alternatives detail in
  `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §1 "Candidate selection and
  rejected alternatives".
- **Governance status:** Phase 2 (Research Proposal) — substantially
  complete.
- **Reviewer level:** Level 1 (self-review) only; no distinct Phase 2
  approval record exists.
- **Known limitations:** The original 8-hypothesis document that first
  ranked H3 is not present in this repository as a primary source (known
  only secondhand); the rejected-alternatives disclosure was added to the
  governing plan *after* Gates 2 and 3 had already passed, making that
  specific control retrospective rather than prospective for this cycle.

## Entry 2 — Pre-validation plan frozen

- **Date:** 2026-07-19 00:16
- **Decision:** `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` frozen as the
  governance document this cycle operates under.
- **Evidence references:** commit `e909959`.
- **Governance status:** Phase 3 (Pre-validation) opened.
- **Reviewer level:** Level 1 (self-review; authoring commit).
- **Known limitations:** Superseded in substance by the hardened version
  committed under Entry 9 below; `e909959` no longer matches the file
  gate reviews after that point actually relied on (see Entry 9).

## Entry 3 — Gate 2 data sufficiency: Option B (extend history) selected

- **Date:** 2026-07-19 00:21–00:25 (report), extension executed same
  session
- **Decision:** Extend historical price data (Option B) rather than
  accept the existing window (Option A) or reduce the universe (Option
  C).
- **Evidence references:**
  `research_archive/reference_h3/data_inventory_2026-07-19.json`;
  `docs/REFERENCE_H3_DATA_SUFFICIENCY_REPORT.md`.
- **Governance status:** Phase 3, Gate 2 — in progress.
- **Reviewer level:** Level 1 (self-review).
- **Known limitations:** None specific to this decision; the data
  extension itself later revealed a discrepancy (Entry 4).

## Entry 4 — Gate 2 discrepancy discovered and root-caused

- **Date:** 2026-07-19 00:44 (discovery), 00:48 (remediation plan
  drafted), 00:56 (origin forensic report)
- **Decision:** A +2-bar-per-ETF surplus (50 rows total,
  `source='backfill-gap-fill'`, on two non-trading NYSE dates) was
  identified, root-caused as far as the evidence allowed, and a
  remediation plan (Option F: export-then-delete) selected over seven
  rejected alternatives. Origin of the anomaly was **not** conclusively
  established ("UNKNOWN, leaning NO, not provably closed").
- **Evidence references:**
  `docs/REFERENCE_H3_GATE2_DISCREPANCY_ANALYSIS.md`;
  `docs/REFERENCE_H3_BACKFILL_GAP_FILL_ORIGIN_REPORT.md`;
  `docs/REFERENCE_H3_DATABASE_REMEDIATION_PLAN.md`.
- **Governance status:** Phase 3, Gate 2 — anomaly under remediation, per
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §6 control 5 (anomaly records).
- **Reviewer level:** Level 1 (self-review).
- **Known limitations:** Root cause unconfirmed; proceeding relies on the
  remediation plan's own accepted-residual-risk mitigation (a
  two-directional recurrence check), not a closed origin. No structural
  write-time guard against recurrence exists (still open as of this log).

## Entry 5 — Gate 2 remediation executed

- **Date:** 2026-07-19 01:27 (executed), 01:28 (committed)
- **Decision:** 50 invalid `PriceBar` rows removed via export-then-delete
  (`maintenance/remediate_h3_invalid_pricebar_rows.py`), full pre-delete
  row set preserved.
- **Evidence references:** commit `af239c2`;
  `research_archive/reference_h3/removed_backfill_gap_fill_rows_2026-07-19.json`;
  `research_archive/reference_h3/post_remediation_validation_2026-07-19.json`;
  `docs/REFERENCE_H3_REMEDIATION_RECORD.md`.
- **Governance status:** Phase 3, Gate 2 — remediation complete, pending
  independent re-review.
- **Reviewer level:** Level 1 (self-review; the executing session).
- **Known limitations:** No pre-delete byte-level database snapshot
  exists; the "no unrelated rows removed" conclusion rests on export-file
  arithmetic and consistency checks, not a direct diff.

## Entry 6 — Gate 2 self-review (disclosed non-independent)

- **Date:** 2026-07-19 (prior to 01:27, pre-remediation)
- **Decision:** First Gate 2 review record produced by the same session
  that performed the underlying work.
- **Evidence references:**
  `research_archive/reference_h3/gate2_independent_review_2026-07-19.md`.
- **Governance status:** Phase 3, Gate 2 — does not satisfy the plan's
  independence requirement by its own admission.
- **Reviewer level:** **Level 1 — self-review.** Explicitly and correctly
  disclosed as such in the document's own opening line; this is the one
  review in the program whose label already matched its actual tier
  before this remediation, and it is left unedited as the historical
  record per archive discipline.
- **Known limitations:** Self-review only; superseded in substance by
  Entry 7.

## Entry 7 — Gate 2 post-remediation review: PASS

- **Date:** 2026-07-19 01:43
- **Decision:** Gate 2 (historical data adequacy, including the Section 8
  remediation re-review) moves from HOLD to **PASS**.
- **Evidence references:**
  `research_archive/reference_h3/gate2_independent_review_2026-07-19_post_remediation.md`.
- **Governance status:** Phase 3, Gate 2 — **satisfied**.
- **Reviewer level:** **Level 2 — AI-assisted adversarial** (procedurally
  independent: fresh session, no conversational continuity to the
  remediation, independently re-derived verification queries; **not
  organizationally independent** — see the review's Section 0 for the
  full limitations statement).
- **Known limitations:** Same-model-family/same-operator limitations
  common to every Level 2 review in this program (see
  `docs/H3_GOVERNANCE_REMEDIATION_ADDENDUM.md` §2); runtime trigger
  behavior was not independently tested (schema-text inspection only);
  no durable two-directional coverage check exists outside the one-off
  remediation script.

## Entry 8 — Gate 3 economic rationale drafted and reviewed: PASS

- **Date:** 2026-07-19 01:48 (drafted), 02:00 (reviewed)
- **Decision:** Gate 3 (economic rationale) assessed **PASS** — mechanism
  distinct from REFERENCE v1 MOMENTUM on actor, causal-mechanism,
  information-flow, and unit-of-analysis grounds; falsification criteria
  adequate; no data-mining risk or prior-result leakage found.
- **Evidence references:**
  `docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md`;
  `research_archive/reference_h3/gate3_independent_review_2026-07-19.md`.
- **Governance status:** Phase 3, Gate 3 — **satisfied**.
- **Reviewer level:** **Level 2 — AI-assisted adversarial** (procedurally
  independent; **not organizationally independent** — see the review's
  Section 0).
- **Known limitations:** Same Level 2 limitations as Entry 7. Literature
  citations were checked for existence and correct characterization only,
  not re-read in full.

## Entry 9 — Pre-validation plan hardened; governance addendum and Standard authored

- **Date:** 2026-07-19 (later in the day, prior to this remediation)
- **Decision:** `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` hardened with
  six governance additions (rejected-candidates disclosure, frozen-
  methodology summary, reviewer-independence definition, reproducibility
  standard, terminal-failure restatement, final-determination template);
  `docs/H3_GOVERNANCE_REMEDIATION_ADDENDUM.md` written to classify every
  prior review's actual independence tier and disclose data-provenance
  gaps; `docs/RESEARCH_GOVERNANCE_STANDARD.md` v1.0 authored as the
  platform-wide governance framework generalizing these lessons.
- **Evidence references:** the three documents named above.
- **Governance status:** Governance infrastructure — applies
  retrospectively (as disclosure) to Gates 2–3 and prospectively to Gate 1
  onward, per the addendum's own retrospective/prospective distinction
  (§1).
- **Reviewer level:** Level 1 (self-directed governance authoring, not a
  review of prior research work — self-classified as such in the
  addendum §2).
- **Known limitations:** A retrospective control cannot certify that
  already-completed work met a standard that did not yet exist when that
  work was done; none of Entries 6–8's underlying documents were
  relabeled, only cross-referenced.

## Entry 10 — H3 Construction Attempt 1 frozen

- **Date:** 2026-07-19 10:51
- **Decision:** Attempt 1 construction fixed: 25-ticker universe
  (unchanged from REFERENCE v1), six-segment peer grouping, relative-
  strength score formula, 60-day lookback, ranking convention,
  missing-data handling. A later same-day edit (Section 4, "within-group
  algebraic structure") added a pure algebraic derivation, introducing no
  new construction element.
- **Evidence references:**
  `research_archive/reference_h3/attempt_001_specification.md`.
- **Governance status:** Phase 4 (Methodology Freeze) — construction
  fixed in writing, but **not yet effective** under
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §3 at the time of freezing (no
  commit existed until Entry 12 below).
- **Reviewer level:** Level 1 at time of drafting; confirmed by Level 2
  review at Entry 11.
- **Known limitations:** Acceptance criteria for H3's eventual
  significance test (Standard §3, item 8) are not yet set — explicitly
  deferred to a document not yet written.

## Entry 11 — Gate 1 governance readiness review: PASS

- **Date:** 2026-07-19 12:03
- **Decision:** Confirmed all Gate-1-relevant construction degrees of
  freedom are frozen, the Section 4 algebraic clarification alters
  nothing, no outcome data was used, and Attempt 1 remains Attempt 1.
  Gate 1's quantitative independence testing declared eligible to begin.
  **This is not a Gate 1 result** — no rank-correlation or score-overlap
  figure has been computed.
- **Evidence references:**
  `research_archive/reference_h3/gate1_governance_readiness_review_2026-07-19.md`.
- **Governance status:** Phase 3, Gate 1 — readiness confirmed; Gate 1
  itself **not started**.
- **Reviewer level:** **Level 2 — AI-assisted adversarial** (procedurally
  independent; **not organizationally independent** — see the review's
  tier statement).
- **Known limitations:** Flagged, in the same review, that the frozen
  construction had no commit hash at the time (closed by Entry 12
  below). Same Level 2 limitations as Entries 7–8.

## Entry 12 — Freeze provenance established; terminology corrected; this log created

- **Date:** 2026-07-19
- **Decision:** Committed the previously-untracked H3 construction
  specification, economic rationale, governance standard, remediation
  addendum, compliance audit, and all three Level 2 gate review records,
  together with the hardened pre-validation plan and updated archive
  README, giving the frozen construction a real, verifiable commit hash.
  Corrected unqualified "independent" labeling in the Gate 1, Gate 2
  (post-remediation), and Gate 3 review documents and the archive README
  to state "Level 2 — AI-assisted adversarial (procedurally independent,
  not organizationally independent)", per
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §4. Created this decision log
  and `FREEZE_RECORD.md`. **No H3 methodology, scoring logic, or any
  prior gate's PASS/HOLD/FAIL conclusion was changed.**
- **Evidence references:** commit `07f0da3` (see
  `research_archive/reference_h3/FREEZE_RECORD.md` for full detail);
  `docs/H3_GOVERNANCE_COMPLIANCE_AUDIT.md` (the audit this entry
  remediates).
- **Governance status:** Closes three of the audit's Section 7 material
  gaps (no commit hash for the frozen construction; unqualified
  "independent" labeling; missing `decision_log.md`). Does not close: the
  data-layer structural-guard gap, the missing durable dataset-hash
  policy, or the absence of any Level 3 review capacity on this platform
  — all explicitly out of scope for this remediation.
- **Reviewer level:** Level 1 (self-directed remediation, performed at
  the direction of a governance-remediation task; not a review of H3's
  research substance and not itself a Gate confirmation).
- **Known limitations:** This entry is itself only Level 1. Per
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §4, a governance-remediation
  action does not require Level 2 review to be valid (it changes no
  research conclusion), but any future document citing this remediation
  as having been "independently verified" would repeat the exact error
  this remediation corrects. The reconciliation of
  `docs/REFERENCE_H3_PREVALIDATION_PLAN.md`'s prior uncommitted-diff gap
  is folded into this same freeze commit rather than logged as a separate
  entry, since both artifacts were committed together.

---

## Current status (as of Entry 12)

- **Gate 2:** PASS (Entry 7).
- **Gate 3:** PASS (Entry 8).
- **Gate 1 governance readiness:** PASS (Entry 11). **Gate 1 itself (the
  quantitative rank-correlation / score-overlap test) has not been run.**
- **Gate 4** (no unresolved degrees of freedom): not assessed.
- **Phase 7 Decision:** Not reached. No PASS, FAIL, or INCONCLUSIVE
  determination exists for H3 as a whole. This log records process
  decisions only and does not itself render one.
- **No outcome data** (forward return, IC, p-value, Sharpe, or any other
  performance figure) has been read, computed, or referenced at any point
  reflected in this log.

## Entry 13 — Gate 1 final determination consolidated: PASS

- **Date:** 2026-07-19 14:56
- **Decision:** Gate 1 (candidate signal independence) closed at
  **PASS**, consolidating the quantitative validation report and its
  independent reproduction review into a single governance decision
  record. The degenerate-case boundary was not triggered; observed
  median Spearman correlation 0.1085 against REFERENCE v1's MOMENTUM
  score, treated as the stricter "moderate correlation" case per the
  pre-validation plan's ambiguity-resolution principle; a pre-existing
  economic explanation for the correlation was found in
  `attempt_001_specification.md` §4 (pre-dating the measurement); the
  figures were independently reproduced to full floating-point
  precision via two independently written code paths. This entry
  consolidates already-recorded evidence; no new analysis was performed
  and no H3 methodology or scoring logic was modified.
- **Evidence references:**
  `research_archive/reference_h3/gate1_final_determination.md` (commit
  `a2cafac`); `docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md`;
  `docs/H3_GATE1_REPRODUCTION_REVIEW.md`;
  `experiments/validate_h3_gate1_independence.py`;
  `research_archive/reference_h3/gate1_independence_analysis_2026-07-19.json`.
- **Governance status:** Phase 3, Gate 1 — **satisfied**. Does not, by
  itself, authorize proceeding to a frozen H3 specification — see Entry
  14 and the status section below for the full four-gate picture.
- **Reviewer level:** Level 2 — AI-assisted adversarial (procedurally
  independent: fresh session, no conversational continuity to the
  validation session, independently recomputed — not merely inspected —
  the rank-correlation and score-overlap figures via a second,
  independently written implementation; **not organizationally
  independent** — same disclosed limitations as Entries 7, 8, and 11).
- **Known limitations:** No Level 3 (organizationally independent)
  review exists or is available on this platform. The dataset-hash /
  provenance policy called for by
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` §5 remains open. The
  bottom-tail rank-overlap asymmetry (median 40% vs. the 20% chance
  baseline for top-5) is independently confirmed as a measured fact but
  remains unexplained. Independent-confirmation duties 1–3 (construction
  log review; no-outcome-data confirmation; no-prior-result-influence
  confirmation) were read but not subjected to a full adversarial audit
  by the reproduction review, by its own account. 19 of 502 nominal
  window dates could not be evaluated due to a `Score`-table coverage
  gap on the MOMENTUM side. Full detail:
  `gate1_final_determination.md` §5.

## Entry 14 — Gate 4 final determination consolidated: PASS

- **Date:** 2026-07-19 14:58
- **Decision:** Gate 4 (no unresolved specification degrees of freedom)
  closed at **PASS**, consolidating the degrees-of-freedom audit into a
  single governance decision record. Five of seven audited categories
  (universe, segments, scoring, lookback, missing-data) are CONTROLLED;
  evaluation window and acceptance criteria are PARTIALLY CONTROLLED
  with disclosed, non-blocking limitations rather than concealed or
  outcome-driven adjustments. No blocking issue was identified in the
  audit. This entry consolidates already-recorded evidence; no new
  analysis was performed and no H3 methodology, scoring logic,
  parameter, benchmark, universe, or acceptance criterion was modified,
  tuned, or reinterpreted.
- **Evidence references:**
  `research_archive/reference_h3/gate4_final_determination.md`;
  `docs/H3_GATE4_DEGREES_OF_FREEDOM_AUDIT.md`; `gate1_final_determination.md`;
  `attempt_001_specification.md`; `FREEZE_RECORD.md` (commit `07f0da3`).
- **Governance status:** Phase 3, Gate 4 — **satisfied**. All four
  Phase 3 gates (2, 3, 1, 4) now PASS; per
  `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` §6 this closes Phase 3 as a
  whole, though the archival items noted under Known limitations remain
  outstanding and are not resolved by this entry.
- **Reviewer level:** Level 2 — AI-assisted adversarial (procedurally
  independent: a session distinct from the sessions that produced the
  frozen specification and the Gate 1 evidence, independently verifying
  claims via git history (`git log --follow`,
  `git merge-base --is-ancestor`) rather than relying on the underlying
  reports' own self-descriptions; **not organizationally independent** —
  same disclosed limitations as Entries 7, 8, 11, and 13).
- **Known limitations:** No Level 3 review exists or is available on
  this platform. Evaluation window and acceptance criteria remain only
  partially controlled, per the audit. The bottom-tail rank-overlap
  asymmetry remains unexplained. The dataset-hash / provenance policy
  gap remains open. **`gate4_final_determination.md` and its supporting
  evidence files (`docs/H3_GATE4_DEGREES_OF_FREEDOM_AUDIT.md`,
  `docs/H3_GATE1_QUANTITATIVE_VALIDATION_REPORT.md`,
  `docs/H3_GATE1_REPRODUCTION_REVIEW.md`,
  `experiments/validate_h3_gate1_independence.py`,
  `gate1_independence_analysis_2026-07-19.json`) are untracked as of
  this entry — no commit hash exists for them, and per
  `FREEZE_RECORD.md`'s own standard ("a document's own claim to be
  frozen is not freeze evidence"), this entry's citation of them should
  not be read as claiming committed provenance until they are
  committed.** Full detail: `gate4_final_determination.md` §6.

---

## Current status (as of Entry 14)

- **Gate 2:** PASS (Entry 7).
- **Gate 3:** PASS (Entry 8).
- **Gate 1:** PASS (Entry 13) — supersedes the "governance readiness
  only, quantitative test not run" status recorded in Entry 11 and in
  the "Current status (as of Entry 12)" section above, which are left
  unedited as the historical record per this log's append-only
  discipline.
- **Gate 4:** PASS (Entry 14) — supersedes the "not assessed" status
  recorded in the "Current status (as of Entry 12)" section above,
  likewise left unedited.
- **Phase 3:** All four gates now satisfied.
- **Phase 7 Decision:** Not reached. No PASS, FAIL, or INCONCLUSIVE
  determination exists for H3 as a whole. This log records process
  decisions only and does not itself render one. Per both final
  determination records' own "Next allowed action" sections, all four
  Phase 3 gates being satisfied does not, by itself, authorize
  proceeding to a frozen H3 specification (Phase 4) beyond what those
  records state; that remains a separate governance step outside the
  scope of this log.
- **Outstanding archival items (not resolved by Entries 13–14):** the
  dataset-hash / provenance policy gap
  (`docs/RESEARCH_GOVERNANCE_STANDARD.md` §5); committing
  `gate4_final_determination.md` and its supporting evidence files,
  which remain untracked as of this entry.
- **No outcome data** beyond what is already cited in Entries 7, 8, 13,
  and 14 has been read, computed, or referenced in producing this
  update.
