# `reference_h4` — Decision Log

Per `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 5: a single, append-only,
chronological record of every decision point across this cycle's lifecycle.

**Honesty note on how this file was authored:** entries below are compiled
from `transition_records.jsonl`'s own real, hash-chained timestamps and
commit hashes, each of which was genuinely written at the time stated —
but this narrative file itself was composed in one pass at Phase 7, after
the chain already existed, rather than literally hand-edited after each
individual transition as Section 5's ideal describes. The underlying
record (the chain, the commits, the git history) is real and was not
reconstructed after the fact; only this prose summary's own authorship
timing departs from the ideal, and that departure is disclosed here rather
than presented as something it wasn't.

---

## Phase 2 — Research Proposal (candidate ranking)

Excess kurtosis of ETF daily log returns selected over three rejected
alternatives (ARCH-style volatility clustering, calendar effects, mean
reversion) on four criteria fixed before scoring: parameter count,
self-containedness, prior replication strength, no cycle overlap. See
`research_proposal.md`. Level 1 self-review only.

## Phase 3–4 — Construction attempt and freeze

One construction attempt (cap = 1), logged in `prevalidation_plan.md`,
carried through to freeze without revision. Methodology Freeze commit:
**`7b0e816dc4a8e8321f556d2b52b1ce3818a0f479`** — `methodology.md` +
`dataset_manifest.json` + `dataset_hashes/{ETF,TradingSession,PriceBar}.jsonl`,
real `core.governance.freeze_verifier.verify_freeze()` result: `VERIFIED`.
This is the freeze commit every subsequent transition through Decision
brackets against. Level 1 self-review confirms completeness (see the
Level 2 adversarial checklist re-confirmation below).

## Phase 6 — Validation and the one real gate

Validation run against a scratch database reconstructed from the frozen
`dataset_hashes/` snapshot (not the live mutable database) —
`experiment_results/kurtosis_results_2026-07-25.json`. Cross-sectional
median excess kurtosis = **9.995185801839456**; 95% bootstrap CI =
**[7.611023804796089, 15.26846242545566]**.

The Validation→Decision transition (sequence 6, the only transition in
this cycle using `compose_transition()`) ran one real gate —
`economic_rationale` via `EconomicRationaleGateAdapter` — comparing the CI
lower bound (7.611) against the frozen threshold (0, direction
`at_least`, `methodology.md` §7). **Gate result: PASS.** Freeze bracket
re-verified `VERIFIED` around the gate run, unchanged since the Phase 4
freeze commit.

## Reproduction verification (before Decision)

`core.governance.reproduction_runner.run_reproduction()` executed for
real: pinned detached worktree at commit
`3d586ded4aad31201cc4e3a349ff7e5d766ba8f5`, offline guard active, scratch
database reconstructed from the frozen dataset manifest, re-ran
`validate_h4_kurtosis.run()`. **Outcome: `VERIFIED`** (frozen identities
unchanged, no exception). See `reproduction_record.json`.

## Level 2 adversarial review

A separate session (no conversational continuity with the work being
reviewed) independently re-derived the kurtosis/median/bootstrap-CI
calculation from raw `sqlite3` access — **exact bit-for-bit match** to
every reported figure. Re-checked `methodology.md` against all 8 Standard
§3 Research Freeze Standard items — all fixed in substance, no hidden
degree of freedom, no drift against `validate_h4_kurtosis.py`. Refined the
disclosed close-price caveat: the specific split-jump risk named in
`prevalidation_plan.md`/`methodology.md` was not observed empirically in
this dataset (checked QQQ's 2024-03-18 and VTI's ~2021-10-12 splits
directly); the dividend-adjustment component remains genuinely
unconfirmed. **No blocking issue found.** Full report:
`reviewer_reports/2026-07-25_level2_adversarial_review.md`. This review is
explicitly labeled Level 2 — procedurally independent, **not**
organizationally independent (Standard §4) — never described as
unqualified "independent."

## Level 3 review — unavailable (disclosed)

No external, organizationally independent human reviewer exists on this
platform. Per Standard §7's PASS-path requirement, this is disclosed here
and repeated in `decision_record.md`, rather than silently substituted or
omitted.

## Chain anchors (for `verify_chain_anchored`)

| seq | transition | commit | freeze status | record hash |
|---|---|---|---|---|
| 1 | Hypothesis → Research Proposal | `985227e` | not_applicable | `sha256:6f782519...39aed` |
| 2 | Research Proposal → Pre-validation | `bedc34b` | not_applicable | `sha256:b033b4d2...551dd` |
| 3 | Pre-validation → Methodology Freeze | `febfa60` | not_applicable | `sha256:df5e36d9...b51653` |
| 4 | Methodology Freeze → Implementation | `7b0e816` | verified | `sha256:b4e742f1...a51c6` |
| 5 | Implementation → Validation | `6ebbd41` | verified | `sha256:07fcd6f3...cca8b2` |
| 6 | Validation → Decision | `3d586de` | verified | `sha256:cb1a04c7...bab7d59` |

(Full hashes in `transition_records.jsonl`; truncated here for
readability, matching how a human would cite them by hand per
`core.governance.decision_recorder`'s own anchor convention.)
