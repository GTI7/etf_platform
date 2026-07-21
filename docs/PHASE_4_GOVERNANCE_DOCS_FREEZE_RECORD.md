# Phase 4 Governance Documentation — Freeze Provenance Record

**Date:** 2026-07-21
**Tag:** `phase4-governance-docs-frozen-v1`

This record supplies the commit hash that makes the Phase 4 governance
documentation set frozen.
[RESEARCH_GOVERNANCE_STANDARD.md](RESEARCH_GOVERNANCE_STANDARD.md) §3 is
explicit that a prose claim is not freeze evidence: **a commit hash is
freeze evidence; a document's own claim to be "frozen" is not.** The same
discipline applied to the H3 construction in
`research_archive/reference_h3/FREEZE_RECORD.md` is applied here.

---

## ⚠️ What this freeze is NOT

Read this section before citing this tag anywhere.

**This is not the Phase 4 Methodology Freeze.** Standard §2 Phase 4
("Methodology Freeze") is a *research lifecycle gate*. It is **not open**,
and this record does not open it. The Positive Control Phase 3 study — the
cycle that would enter Phase 4 — currently has **Gate 2 FAIL and Gate 3
FAIL**, and
[POSITIVE_CONTROL_PHASE3_REMEDIATION_DECISION.md](POSITIVE_CONTROL_PHASE3_REMEDIATION_DECISION.md)
§9 records "Phase 4 (Methodology Freeze): **Not open**."

The tag name contains "phase4" because this documentation set concerns the
*Phase 4 governance subsystem* — the reproducibility and evidence-
preservation infrastructure being built ahead of that gate. **Anyone
reading `phase4-governance-docs-frozen-v1` as evidence that a methodology
freeze has occurred has misread it.**

**This is not an approval.** No document in the frozen set approves the
Phase 4 implementation. Two of them are adversarial review records finding
20 defects; a third adjudicates those findings and concludes the platform
is **not certifiable**.

**This does not freeze the implementation.** `core/governance/*` and its
tests remain **uncommitted** and are outside this freeze entirely.

**This does not make any research result reproducible.** No archive in this
repository contains a `dataset_manifest.json` or a
`reproduction_record.json`. The reproducibility subsystem has never
executed against a real research cycle.

---

## Freeze commit

| Field | Value |
|---|---|
| Commit hash (full) | `91acb2cd4af77872b912b9fa42673e84d1e2e093` |
| Commit hash (short) | `91acb2c` |
| Subject | *Close Phase 4 governance documentation chain* |
| Author date | 2026-07-21T19:42:46+02:00 |
| Branch | `arb/phase4-determination` |
| Parent commit | `bc1fde1` (*Record ARB determination on Phase 4 governance review*) |
| Repository | `D:\Claude\etf_platform` |

Every file below is reproducible byte-for-byte via
`git show 91acb2c:<path>`.

## Frozen files

**Brought under version control for the first time by `91acb2c`:**

- `docs/reviewer_reports/2026-07-21_RR-001_phase4_governance_architecture_review.md`
  — Level 2 adversarial architecture review of `core/governance/*`;
  20 findings across four bands, seven subsystems named sound.
- `docs/reviewer_reports/2026-07-21_RR-002_phase4_governance_peer_review.md`
  — Level 2 peer review of RR-001; five claims independently re-executed.
- `docs/PHASE_4_REPRODUCIBILITY_HARDENING_PROPOSAL.md` — base proposal;
  §2.3 load-bearing for the ARB's A1(b) ruling.
- `docs/PHASE_4_ARCHITECTURE_AMENDMENT_V1.md` — **superseded** by v1.1;
  retained as historical record.
- `docs/PHASE_4_ARCHITECTURE_AMENDMENT_V1_1.md` — **current design of
  record.**
- `docs/PHASE_4_IMPLEMENTATION_ROADMAP.md` — seven-PR sequencing for the
  ARB MUST list.
- `docs/README.md` — lifecycle index and open-defect register.

**Already committed, and part of the frozen chain by reference** (parent
`bc1fde1`):

- `docs/PHASE_4_ARB_DETERMINATION_2026-07-21.md` — binding determination.
- `docs/PHASE_4_RESULT_REPORT_CANONICALIZATION_CHARTER.md` — chartered,
  open.

## Provenance chain, as frozen

```
PHASE_4_REPRODUCIBILITY_HARDENING_PROPOSAL.md   (base)
  └─amended─> PHASE_4_ARCHITECTURE_AMENDMENT_V1.md      [SUPERSEDED]
       └─corrected─> PHASE_4_ARCHITECTURE_AMENDMENT_V1_1.md  [DESIGN OF RECORD]
                          │
                          ├── reviewed by ─> RR-001  (16:49:31Z–16:56:23Z, Level 2)
                          │                     └─ peer-reviewed by ─> RR-002
                          │                            (16:58:21Z–17:05:11Z, Level 2)
                          │
                          └── adjudicated by ─> PHASE_4_ARB_DETERMINATION_2026-07-21.md
                                                  (17:21:39Z)
                                                    ├─ chartered ─> CANONICALIZATION_CHARTER
                                                    └─ sequenced ─> IMPLEMENTATION_ROADMAP
```

Every link in this chain now exists as a repository artifact. Before
`91acb2c`, three of the eight nodes — including the design of record — were
untracked, and the determination cited two review events that had no file
at all.

## What the freeze certifies

1. **Ordering is fixed and verifiable.** Each review event's window
   precedes the determination that rules on it. No reviewer report cites a
   ruling made after its review closed.
2. **The chain is complete.** No document in the frozen set references a
   Phase 4 governance document absent from the repository.
3. **Supersession is explicit.** Every superseded document carries a
   forward-pointing banner; no reader can open v1.0 and mistake it for
   current.
4. **Status lines match reality.** No document claims "not implemented"
   while an implementation exists in the working tree.

## What the freeze does not certify

1. **Not that the implementation is correct.** It is uncommitted and, per
   RR-001/RR-002 and the ARB determination §6, non-conformant with the
   design of record on at least findings A1, A2 and A3.
2. **Not that any review was independent.** Both reviews are **Level 2**.
   Standard §4: no Level 3 review has ever been performed on this
   platform. The two reviews were conducted by the same model family, same
   vendor, same operator, nine minutes apart — the agreement between them
   is procedural corroboration, not independent confirmation, except for
   the five claims RR-002 re-executed.
3. **Not that the documentation is defect-free.** Seven known open
   governance defects are listed in
   [README.md](README.md#known-open-governance-defects), including two
   that this freeze deliberately did **not** resolve because resolving
   them would require editing committed history:
   - the "Level-3" independence-tier collision, inherited into the
     committed ARB determination (`bc1fde1`);
   - Standard §5's self-contradiction on supersession.

## Post-freeze change discipline

Per Standard §5, any correction to a document in this frozen set is a
**new, dated file** cross-referenced from the document it supersedes —
never a silent edit. A correction to the ARB determination or to either
reviewer report specifically requires a new dated document; neither may be
edited in place, because both are now committed historical record.

**This record is itself subject to that rule.** If the freeze is later
found to have been premature, that is recorded as a new dated document
citing this one — not by amending this file or moving the tag.
