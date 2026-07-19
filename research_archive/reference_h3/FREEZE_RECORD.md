# REFERENCE H3 — Freeze Provenance Record

This record exists to close the gap identified in
`docs/H3_GOVERNANCE_COMPLIANCE_AUDIT.md` Section 3 and Section 7, item 1:
the frozen H3 construction previously existed only as an uncommitted file
with a prose "frozen" claim, which
[`docs/RESEARCH_GOVERNANCE_STANDARD.md`](../../docs/RESEARCH_GOVERNANCE_STANDARD.md)
Section 3 ("How freeze is recorded") explicitly states is not freeze
evidence. **A commit hash is freeze evidence; a document's own claim to be
"frozen" is not.** This record supplies that commit hash.

## Freeze commit

| Field | Value |
|---|---|
| Commit hash (full) | `07f0da379d8cccf06d17c34a51cbb557da047fef` |
| Commit hash (short, as cited elsewhere in this archive) | `07f0da3` |
| Author date | 2026-07-19T14:15:07+02:00 |
| Branch | `master` |
| Parent commit | `af239c2` ("fix(data): remediate 50 invalid PriceBar rows for REFERENCE H3 Gate 2") |
| Repository | `D:\Claude\etf_platform` |

## Frozen files

The commit above brought the following files under version control for
the first time, or updated them for the last time before this record was
written. Each is now reproducible byte-for-byte via `git show
07f0da3:<path>`:

**Newly committed (previously untracked):**
- `research_archive/reference_h3/attempt_001_specification.md` — the H3
  Attempt 1 construction: universe, peer-segment grouping, score formula,
  60-day lookback, ranking convention, missing-data handling (Section 3),
  and the within-group algebraic clarification (Section 4).
- `docs/REFERENCE_H3_GATE3_ECONOMIC_RATIONALE.md` — the frozen economic
  mechanism and falsification criteria Gate 3 was reviewed against.
- `docs/RESEARCH_GOVERNANCE_STANDARD.md` — the governance standard this
  record and the rest of this remediation comply with.
- `docs/H3_GOVERNANCE_REMEDIATION_ADDENDUM.md` — the governance
  transparency record documenting review-independence and data-provenance
  limitations.
- `docs/H3_GOVERNANCE_COMPLIANCE_AUDIT.md` — the audit that identified the
  gaps this record and its companion `decision_log.md` close.
- `research_archive/reference_h3/gate1_governance_readiness_review_2026-07-19.md`
- `research_archive/reference_h3/gate2_independent_review_2026-07-19_post_remediation.md`
- `research_archive/reference_h3/gate3_independent_review_2026-07-19.md`

**Updated in the same commit (previously modified, uncommitted):**
- `docs/REFERENCE_H3_PREVALIDATION_PLAN.md` — reconciles the governance
  gap the audit identified in Section 3 (the plan's cited freeze commit,
  `e909959`, no longer matched the file on disk that later gate reviews
  actually relied on). This commit is now the authoritative version.
- `research_archive/reference_h3/README.md` — the archive index, updated
  for corrected review terminology (see below).

## Freeze date

**2026-07-19** (commit author date `2026-07-19T14:15:07+02:00`).

## Repository state at freeze

Working tree clean (`git status --short` empty) immediately after the
commit above. No file relevant to H3's construction, governance, or gate
review record is modified or untracked as of this freeze. The live
`experiments_etf_universe.db` database is not part of this freeze (it is
gitignored and out of scope for a code/document freeze); its own
provenance is tracked separately per
`docs/H3_GOVERNANCE_REMEDIATION_ADDENDUM.md` Section 3.

## Immutability

**This freeze reference is immutable.** `07f0da379d8cccf06d17c34a51cbb557da047fef`
is a Git commit hash: any change to the content of any file listed above,
for any reason, produces a different hash and is therefore not this
freeze — it is a new, separately dated freeze that must be recorded as
its own entry in `decision_log.md`, per
`docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 3 ("How changes are
handled after freeze"). This record itself is never edited in place after
being committed; a correction is added as a new, dated freeze record
cross-referencing this one, following the same supersession convention
`docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 5 requires for every other
archive artifact.

Reproduce this exact state with:

```
git show 07f0da3:research_archive/reference_h3/attempt_001_specification.md
git checkout 07f0da3 -- research_archive/reference_h3/attempt_001_specification.md
```

## What this record does not do

This record does not evaluate, approve, or modify H3's methodology,
scoring logic, or any gate's PASS/HOLD/FAIL determination. It does not
run or authorize Gate 1's quantitative testing. It solely establishes
tamper-evident provenance for work already reviewed and recorded
elsewhere in this archive.
