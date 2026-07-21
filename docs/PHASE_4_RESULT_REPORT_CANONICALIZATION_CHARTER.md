# Charter — Result Report Canonicalization Spec (`result_report_hash`)

**Date:** 2026-07-21
**Status: charter — defines a design task. Specifies no algorithm and commits no code.**
**Chartered by:** [PHASE_4_ARB_DETERMINATION_2026-07-21.md](PHASE_4_ARB_DETERMINATION_2026-07-21.md) §1, ruling A1(b).

`result_report_hash` is a MUST HAVE in
[PHASE_4_ARCHITECTURE_AMENDMENT_V1_1.md](PHASE_4_ARCHITECTURE_AMENDMENT_V1_1.md) §G
("`reproduction_record.json` binding commit + 3 dataset hashes + report
hash") and §F.3 ("Result report hash / tolerance check"). It is not
implemented. The Level-3 review proposed implementing it as
`sha256_of_file` over the report; the peer review disproved that
empirically; the ARB accepted the disproof and split the work into
A1(a) — cheap, MUST, already scheduled — and A1(b), this charter.

**This charter exists because A1(b) is the one item on the ARB's list
that cannot be sized until a design decision is made.** Everything else
in the MUST list is between one line and one small module.

---

## 1. Why the obvious implementation cannot work

Verified directly against the archived artifacts, not asserted:

```
research_archive/reference_v1/reference_v1_significance_report_2026-07-18.json
  { "generated_at": "2026-07-18T16:32:12.075020+00:00", "config": {...}, "statistics": {...} }

research_archive/reference_v2_h1/reference_v2_h1_significance_report_2026-07-18.json
  { "generated_at": "2026-07-18T21:10:58.740443+00:00", "config": {...}, "statistics": {...} }
```

A wall-clock timestamp is the first key of the object. Any hash computed
over the file's bytes changes on every run **by construction**, so it can
never equal a value recorded at freeze time. A reproduction that compared
them would emit `REPRODUCTION_FAILED` — the most damaging verdict the
system can issue — on every correct run.

The field that must be hashed is therefore not the file. It is a
*derived, canonical projection* of the file, and defining that projection
is the whole of this task.

---

## 2. What is already decided and must not be re-opened

This is the primary risk to the task and the reason the charter leads
with it.

**Numeric tolerance is settled.**
[PHASE_4_REPRODUCIBILITY_HARDENING_PROPOSAL.md](PHASE_4_REPRODUCIBILITY_HARDENING_PROPOSAL.md) §2.3
already ruled: zero tolerance on any figure that never passed through
`float`; **exact match** for `float`-based statistics including
`permutation_null` and `bootstrap_ci` given the same seed and Python
version; and explicitly — *"No blanket epsilon (e.g. `1e-6`) should ever
be adopted as a substitute for pinning the environment precisely enough
to not need one. A tolerance band is an admission that the environment
lock failed, not a design feature."*

**The problem this charter solves is scope and serialization, not
tolerance.** A spec that arrives proposing an epsilon has misread its own
mandate. If two correct runs on a locked environment produce different
floats, §2.3 has already declared that evidence of an under-specified
environment lock (§4), to be fixed there — not absorbed here.

**Serialization discipline already exists.** `canonical_jsonl`'s write
path is named as architecturally sound by both reviews:
`sort_keys=True` recursing into nested objects, `separators` eliminating
whitespace ambiguity, explicit encoding before `write_bytes` to avoid
platform newline translation, and hashing the bytes actually written
rather than a re-serialization. **Reuse that discipline.** The reports
are single JSON objects rather than JSONL, so the module may not apply
directly; the *rules* do. Inventing a second, divergent canonical form in
the same codebase is an explicit non-goal.

---

## 3. Verified input: the archives are not uniform

The `result_report_hash` field is singular. The artifacts are not. This
is the finding that most affects the spec's shape, and it is verified:

| Cycle | Result artifact(s) | Has `generated_at`? |
|---|---|---|
| `reference_v1` | `reference_v1_significance_report_2026-07-18.json` | Yes |
| `reference_v2_h1` | `reference_v2_h1_significance_report_2026-07-18.json` | Yes |
| `reference_h3` | `phase6_economic_validation_2026-07-19.json`, `post_remediation_validation_2026-07-19.json` — **no `*_significance_report_*.json` exists** | Yes / No respectively |
| `positive_control_phase3` | `generator_fidelity_results.json` | No |

Two further shape differences matter:

- **Statistic keys differ per study.** `reference_v1` reports
  `statistics.momentum_ic`; `reference_v2_h1` reports `statistics.h1_a`
  and `statistics.h1_b`. A canonicalization keyed to a fixed schema will
  not survive the next hypothesis.
- **`reference_h3` carries extra top-level provenance** —
  `methodology_freeze_commit` and `acceptance_criteria_freeze_commit` —
  which the other cycles do not.

So the spec cannot assume one report per cycle, one schema across
cycles, or a uniform volatile-field set.

---

## 4. Decisions the spec must make

Each is a decision, not an implementation detail. Where the existing
evidence supports one option, the charter records a recommendation and
its reasoning; the spec may overturn it with argument.

**D1 — Which artifact is "the result report" for a cycle.**
Options: (a) the record declares an explicit path per cycle; (b) the
field becomes a map of `{artifact_path: hash}`; (c) a naming convention
the runner discovers.
*Recommendation:* (a) or (b) — never (c). Discovery-by-convention fails
silently on `reference_h3`, which has no file matching the convention,
and would hash nothing while reporting success. The record already
declares `commit_hash` and `dataset_content_hashes`; declaring the
report path is consistent with that design.

**D2 — Exclusion (denylist) or inclusion (allowlist) of fields.**
*Recommendation: exclusion, and the reasoning is asymmetric-failure, not
convenience.* An allowlist that misses a newly added statistic produces a
hash that **matches while the number changed** — a silent false
`VERIFIED`, which is the exact failure class this entire subsystem
exists to prevent. A denylist that misses a newly added volatile field
produces a hash that **never matches** — a loud, investigable false
`REPRODUCTION_FAILED`. Prefer the loud failure. The spec must state this
trade-off explicitly so a future maintainer does not "simplify" it in the
wrong direction.

**D3 — The exclusion set itself.** `generated_at` is the only confirmed
member. The spec must enumerate the rest by inspection of all four
archived artifacts, and must state a rule for classifying future fields
(a field is excluded iff its value is a function of *when the run
happened* rather than *what the run computed*).

**D4 — Float serialization.** *Recommendation: exact round-trip
(`repr`, or `float.hex()` if a bit-level guarantee is wanted) — never
fixed-precision formatting.* Rounding to N decimal places in the
serializer is a tolerance band wearing a serializer's clothes, and §2.3
forbids it. The archived reports carry values such as
`-0.11722455691576832` and `3.6543029417138544e-05`; any formatting rule
that does not round-trip those exactly is silently discarding evidence.

**D5 — Scope: whole document minus exclusions, or a declared subtree.**
Amendment v1.1 §G separately requires the report to echo every effective
experiment parameter, which argues for including `config` so a
parameter change is caught. The spec must decide whether `config`,
`statistics`, or both are in scope, and say why.

**D6 — Producer/consumer symmetry.** The hash is written at freeze time
and checked at reproduction time. The spec must name one implementation
used by both paths, and forbid the verification path from re-deriving
the canonical form independently.

**D7 — Versioning the canonicalization itself.** The algorithm must
carry a version identifier in the record. Changing the canonical form
after any hash is published invalidates that published hash; without a
version field the invalidation is silent and indistinguishable from a
genuine reproduction failure.

---

## 5. Non-goals

- Numeric tolerance in any form (§2 — already decided).
- Redesigning the result report schema. The spec canonicalizes what
  exists; it does not get to make the reports uniform first. If it
  concludes uniformity is required, that is a separate proposal.
- A1(a) — the manifest ↔ record dataset-hash binding, which is already
  MUST and does not depend on this work.
- Environment locking (base §4). If exact match proves unattainable, the
  defect is there, not here.
- Backfilling `result_report_hash` into the four existing archives. Those
  cycles were frozen without it; per Standard §5 the record of what was
  believed true at the time is retained, not retroactively improved.

---

## 6. Deliverables

1. A dated spec document under `docs/`, cross-referenced from this
   charter, resolving D1–D7 with reasoning.
2. A single canonicalization function with a stated version, used by both
   the producer and the verification path (D6).
3. A determinism test: canonicalize the same report twice in one process
   and across two processes; assert byte-identical output. This is the
   test that would have caught the `generated_at` defect before it
   reached a review.
4. A negative test per exclusion-set member: mutate the excluded field,
   assert the hash is unchanged; mutate one statistic, assert it changes.
5. A worked application to at least `reference_v1` and
   `reference_v2_h1` — the two cycles that have a report of the expected
   shape — demonstrating a stable hash across two runs.

---

## 7. Sequencing constraint

**The spec must land before the first `reproduction_record.json` is
written.**

Once a `result_report_hash` exists in a committed archive, the
canonicalization algorithm is load-bearing for published evidence and any
change to it becomes a migration affecting a frozen artifact — which
Standard §6 control 1 (immutable datasets, corrections as new superseding
artifacts, never in-place) makes deliberately expensive.

This is the same constraint the ARB determination flags conditionally for
C3: hash formats are cheap to change before the first write and costly
after. There is no reason to pay that cost, because nothing in the ARB's
MUST list requires `result_report_hash` to exist for the first
reproduction to be *sound* — only for it to be *complete*. The first
production reproduction can legitimately run with A1(a) closing the input
side and this field deferred, provided the attempt record (B5) states
plainly that output verification was not performed.

**Recommended order:** ship the MUST list, run the first reproduction
with output-hashing declared absent, then land this spec and re-run. A
first reproduction that is honestly incomplete is worth more than a
delayed one that is silently incomplete.

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| The spec re-opens tolerance and proposes an epsilon. | §2 is stated first and the reviewer should reject on sight. |
| Exact match proves unattainable across two runs on the locked environment. | Per §2.3 that is evidence the environment lock is under-specified; route to base §4, do not loosen here. Deliverable 5 surfaces it early and cheaply. |
| The spec is written against `reference_v1`'s shape only and breaks on the next hypothesis. | §3's non-uniformity table is verified input; deliverable 5 requires two cycles; D1 forbids convention-discovery. |
| An allowlist is chosen for tidiness and silently under-covers. | D2 records the asymmetric-failure reasoning explicitly so the trade-off cannot be re-decided by accident. |
| The work expands into report schema redesign. | Named non-goal (§5). |

---

## 9. Open questions requiring an operator decision

These are not for the spec author to resolve unilaterally — they are
research-governance questions:

1. **Which artifact is the citable result for `reference_h3`?** It has no
   significance report. Is `phase6_economic_validation_2026-07-19.json`
   the reproducible output, or is H3 simply outside the scope of
   automated reproduction?
2. **Is `positive_control_phase3` in scope at all?** Its
   `generator_fidelity_results.json` has no `generated_at`, so it may be
   hashable as-is — which would make it the cheapest first target for a
   real end-to-end reproduction.
3. **Does `config` participate in the hash (D5), or is parameter drift
   caught separately** by the amendment's "report echoes every effective
   parameter" requirement plus the commit binding?

Question 2 bears directly on the ARB determination's certification
finding 2: the flagship `daily_etf_universe_update.py` cannot run under
`offline_guard` because it fetches through `YahooFinanceProvider`. If a
positive-control or `validate_*` path is already offline-clean **and**
already hashable, it is the shortest route to the platform's first real
reproduction — and that route should be evaluated before any code in the
MUST list is written.
