# Phase 4 — Reproducibility Hardening / Evidence Preservation Layer

> ## 📄 BASE PROPOSAL — AMENDED TWICE, RETAINED — as of 2026-07-21
>
> This is the **base proposal** for the Phase 4 governance subsystem. It has
> been amended by [v1.0](PHASE_4_ARCHITECTURE_AMENDMENT_V1.md) (now
> superseded) and then by
> [v1.1](PHASE_4_ARCHITECTURE_AMENDMENT_V1_1.md), which is the **current
> design of record**.
>
> **Reading rule.** Where this document and v1.1 conflict, **v1.1 controls**.
> Where v1.1 is silent, this document's text stands. It is retained, not
> replaced, because parts of it remain load-bearing — notably **§2.3
> (exact-match policy)**, which
> [PHASE_4_ARB_DETERMINATION_2026-07-21.md](PHASE_4_ARB_DETERMINATION_2026-07-21.md)
> relies on for its ruling A1(b).
>
> **Status correction (2026-07-21).** The line below previously read
> *"proposal, not implemented"* without qualification. A partial,
> uncommitted, non-conformant implementation now exists — see the v1.1
> banner for the exact figures. Nothing below this banner is edited.

**Status: base proposal — amended by v1.0 then v1.1; retained as source for §2.3. Not a description of the code.**

This document is the architecture
design requested after the Independent Reproducibility and Verification
Audit. It commits to no code. Every schema, interface, and recommendation
below is a design decision awaiting review, not a description of anything
that currently exists in this repository.

**Audit finding this document responds to:** research methodology and
governance are strong; statistical calculations are deterministic; the
critical weakness is evidence preservation — no frozen dataset artifacts,
no dataset manifests/hashes, no environment lock, no deterministic replay
test, live dependency on Yahoo Finance historical data.

**Method.** Every claim below about the current repository state was
verified by reading the actual files, not assumed. Where the audit's
framing turns out to rest on a shaky premise, that is called out
explicitly rather than quietly designed around.

---

## 0. What already exists (do not re-invent this)

The audit is correct that no dataset artifact, manifest, or environment
lock exists. It is *not* the case that this is greenfield design. Three
pieces of forward-looking infrastructure are already committed, and Phase
4 is substantially the job of finishing what they started rather than
starting from zero:

| Piece | Where | What it already does |
|---|---|---|
| `FreezeVerifier` | [core/governance/freeze_verifier.py](../core/governance/freeze_verifier.py) | Given a commit ref and a list of covered paths, proves byte-identical, no-drift reproduction of **code/document** artifacts via `git diff`/`git status`. Returns a 3-way `FreezeStatus` (`VERIFIED` / `DRIFTED` / `UNVERIFIABLE`). |
| `archive_manifest.json` schema v1 | [docs/RESEARCH_ARCHIVE_MANIFEST.md](RESEARCH_ARCHIVE_MANIFEST.md), [tools/archive_manifest.py](../tools/archive_manifest.py) | A versioned index file (`schema_version`, `project_id`, `created_at`, `lifecycle_version`) written once per *new* project archive. Refuses to write into the three legacy directories or overwrite an existing manifest. |
| Forward interface sketches | [docs/PLATFORM_ARCHITECTURE_V1.md](PLATFORM_ARCHITECTURE_V1.md) §4.4 | `DatasetVersioner`, `DatasetIntegrityChecker`, `ArchiveVerifier`, `ReproducibilityChecker` are already named as `Protocol`s with sketched signatures, explicitly deferred pending a "concrete consumer." |
| Evidence-package contract | [docs/RESEARCH_GOVERNANCE_STANDARD.md](RESEARCH_GOVERNANCE_STANDARD.md) §3 element 2, §5, §6 | Already *requires* "dataset version — source, date range, content hash," already names `dataset_manifest.json` and `dataset_hashes/` in the fixed archive layout, already states five data-provenance controls (immutable datasets, source tracking, transformation logs, reproducible calculations, anomaly records). None of this is implemented; all of it is specified. |
| Roadmap placement | [docs/RESEARCH_PLATFORM_RETROSPECTIVE.md](RESEARCH_PLATFORM_RETROSPECTIVE.md) §5 item 1, §6 Tier 3 | Already identifies "no dataset-hashing infrastructure exists anywhere in the codebase" as **the single most consequential gap**, already schedules it as Tier 3 ("needed before the next cycle's Phase 4 freeze can honestly claim 'dataset version'"). |

Phase 4, as designed here, is the implementation of `DatasetVersioner` and
`DatasetIntegrityChecker`, the closing of the Tier 3 roadmap item, and the
extension of the `FreezeVerifier` pattern from code artifacts to dataset
artifacts. It is not a new initiative competing with existing plans — it
is the next scheduled one, arriving on time.

**A fact that reshapes the "environment lock" question before Section 4
even starts:** [AD-005](ARCHITECTURE_DECISIONS.md) commits this codebase
to Python-standard-library-only — no numpy, no pandas, no scipy, no
`yfinance` (the Yahoo provider is a raw `urllib` client, see
[core/market_data/providers/yahoo_finance.py](../core/market_data/providers/yahoo_finance.py)).
AD-005's own stated rationale is partly reproducibility: "removes an
entire class of reproducibility risk: there are no third-party numerical
library versions that could silently change calculation behavior between
releases." Any environment-lock design that reaches for Docker, Poetry,
or Nix without first weighing this fact is solving a problem the codebase
has already mostly engineered away. See §4.

---

## 1. Dataset Preservation Architecture

### 1.1 Current state (verified, not assumed)

- Market data lives in `experiments_etf_universe.db`, a single 82 MB
  SQLite file at the repo root. Gitignored (`.gitignore` line 27, `*.db`)
  — by design, per the comment above it ("never commit real or ephemeral
  data").
- `PriceBar` (61,850 rows) is the raw input table. `IngestionRun`
  (182,612 rows) logs every ingestion attempt against it — a ~3:1
  churn-to-data ratio, meaning the live table has been backfilled,
  corrected, and re-ingested many times since any given historical result
  was produced. `Score` and `DimensionScore` are *derived* tables, not
  raw input.
- [research_archive/reference_h3/FREEZE_RECORD.md](../research_archive/reference_h3/FREEZE_RECORD.md)
  states this outright: *"The live `experiments_etf_universe.db` database
  is not part of this freeze... its own provenance is tracked separately"*
  — separately meaning, on inspection, nowhere durable. This is the exact
  hole the audit found, confirmed at the file level.
- `dataset_hashes/` already exists as an empty, `.gitkeep`-only directory
  under `research_archive/positive_control_phase3/` (created by
  `scaffold_project_archive()`), per the Standard §5 layout — structure
  only, no content, no hashing code anywhere (grep for `hashlib`/`sha256`
  across the repo returns zero hits outside two unrelated files that
  don't hash datasets).
- Every historical significance report already records its PRNG seed as
  a plain field (`"random_seed": 20260718` in
  `research_archive/reference_v1/reference_v1_significance_report_2026-07-18.json`)
  — a good existing habit, but it lives only in the *output*, not in any
  frozen *input* artifact. There is currently nothing that would stop a
  seed from being chosen after seeing early results; nothing in this
  Phase 4 design fixes that (it's a Phase 3/4 pre-registration question,
  not a dataset-preservation one) but it should not be quietly assumed
  away either.

### 1.2 What must be answered before any schema is designed

**"What is the minimum artifact set required to prove a historical
research result?"**

Four items, cryptographically chained, nothing more:

1. **Code commit** — already solved (`FreezeVerifier`, git).
2. **Dataset snapshot** — a content-addressed, immutable extract of
   exactly the rows the experiment read. **Not** the live 82 MB database.
3. **Experiment configuration** — the frozen parameters (`methodology.md`
   already carries this in prose; it needs a machine-hashable
   companion) including the PRNG seed.
4. **Result report** — already produced (`experiment_results/`), just
   never hash-bound to the other three.

The proof is not any one of these files — it is a single small record
binding all four hashes together. Everything else (dataset_hashes/
directory conventions, storage format, CI tests) exists to make that one
binding statement checkable. Section 2 formalizes it as
`reproduction_record.json`.

**Reject, explicitly:** snapshotting the whole `experiments_etf_universe.db`
file as "the" artifact. Three reasons: (a) it mixes raw input (`PriceBar`)
with derived, re-computable state (`Score`, `DimensionScore`,
`IndicatorValue`) that has no business being "frozen" — freezing derived
output alongside its own input conflates the thing being proven with the
proof; (b) SQLite binary snapshots are not diffable, not human-reviewable
in a PR, and not the medium this repository uses anywhere else for
evidence (every existing archive artifact is text — JSON, Markdown); (c)
at 82 MB and growing, committing full snapshots per cycle does not scale
and invites exactly the kind of "just don't look at it" avoidance that
left this gap open in the first place. A scoped extract of a few thousand
rows for one universe over one evaluation window is a fundamentally
different, and tractable, problem.

### 1.3 `dataset_manifest.json` schema

Lives at `research_archive/<cycle>/dataset_manifest.json`, exactly where
Standard §5 already names it. Its own `schema_version` is independent of
`archive_manifest.json`'s — they are sibling files with different
schemas, not the same document; do not conflate the two counters.

```json
{
  "schema_version": 1,
  "project_id": "h4",
  "generated_at": "2026-08-01T00:00:00+00:00",
  "datasets": [
    {
      "dataset_id": "pricebar_h4_universe_v1",
      "source": "yahoo_finance",
      "source_table": "PriceBar",
      "universe": ["SPY", "QQQ", "..."],
      "date_range": {"start": "2015-01-01", "end": "2026-07-01"},
      "extraction_query": "sql/h4_pricebar_extract.sql",
      "extraction_query_hash": "sha256:...",
      "row_count": 14832,
      "snapshot_path": "dataset_hashes/pricebar_h4_universe_v1_2026-08-01.jsonl",
      "content_hash": "sha256:...",
      "ingestion_run_ids": ["...", "..."],
      "source_tags_observed": ["yahoo_finance_daily"]
    }
  ]
}
```

Field notes, because every field is a decision:

- `extraction_query` + `extraction_query_hash` — the SQL (or equivalent)
  that produced the snapshot from the live database is itself committed
  and hashed. Without this, a reviewer can verify the snapshot is
  internally consistent but not that it was drawn honestly (no
  cherry-picked date range, no silently excluded tickers).
- `ingestion_run_ids` — ties the snapshot back to Standard §6 control 3
  (transformation logs / `IngestionRun`), so a reviewer can trace *how*
  each row entered the system, not just that it exists.
- `source_tags_observed` — direct implementation of Standard §6 control
  2: any tag here that the current, committed ingestion code cannot
  produce is an anomaly, exactly the property that caught the
  `backfill-gap-fill` defect in H3.
- No `checksum_algorithm` field with a default — always explicit
  (`sha256:` prefix on every hash value), because a manifest that is
  silently reinterpreted if the default ever changes is worse than one
  that states its algorithm every time.

### 1.4 Hashing strategy

Hash the **exported snapshot file bytes directly** — not a hash computed
over live database rows via some in-memory serialization that differs
from what's actually stored on disk. This matters because it means
`sha256sum dataset_hashes/pricebar_h4_universe_v1_2026-08-01.jsonl` *is*
the verification command; no bespoke hashing code needs to be trusted at
verification time, only at generation time.

Canonicalization rules (all currently unenforced anywhere — must be
specified once, here, and never varied):

- **Row order:** `ORDER BY etf_id, session_date` — the same order
  `idx_pricebar_etf_session` already indexes by, so extraction is cheap
  and order is unambiguous.
- **Format:** JSONL, one row per line, keys in a fixed order. `PriceBar`
  already stores `open_amount`/`high_amount`/`low_amount`/`close_amount`
  as `TEXT` (`Decimal`-compatible strings, not floats) — the snapshot
  format must preserve that, never round-tripping through `float`. This
  is a case where the schema already does the hard part; the snapshot
  format just has to not undo it.
- **Line endings:** `\n` only, UTF-8, no BOM, trailing newline — stated
  explicitly because this repository already has a known,
  documented CRLF test-fragility issue (per
  [project memory: positive-control-study]); a dataset-hash pipeline is
  exactly the kind of thing that silently breaks across Windows/Linux
  line-ending differences if this isn't pinned in writing.

### 1.5 Artifact storage: reject new infrastructure, use what's already here

The audit's framing implies "artifact storage" is a missing capability.
Given the scale actually observed (universes of dozens of tickers,
evaluation windows of years, snapshots landing in the low single-digit
megabytes — `PriceBar` in full is 61,850 rows before any per-cycle
scoping), the correct storage mechanism is **git**, the same mechanism
already used for every other evidence artifact in this repository. There
is no case yet for introducing DVC, S3, or any content-addressed blob
store — that would be new infrastructure solving a scale problem this
repository does not currently have, in a codebase whose own AD-005
explicitly rejects speculative infrastructure ahead of need.

**MUST HAVE:** snapshots under `dataset_hashes/` are plain, git-tracked
text files, following exactly the pattern `research_archive/`'s own
README already documents for everything else in the directory
("snapshot, never regenerate in place").

**SHOULD HAVE:** a stated size ceiling (proposed: 20 MB per snapshot
file) past which a cycle must either scope its universe/date-range
tighter or explicitly flag the exception in `decision_log.md`. No
external storage is provisioned for the overflow case yet — that stays a
documented, escalate-to-a-human situation, not a new subsystem.

**FUTURE ENHANCEMENT:** if a hypothesis cycle ever needs a genuinely
large snapshot (full-market universes, minute-bar data), revisit
external content-addressed storage then, against that concrete need —
not now, against a hypothetical one.

### 1.6 Versioning model

```
code commit (git, verified by FreezeVerifier)
      │  pins
      ▼
experiment config  ──hash──▶  config_hash
      │  (methodology.md's 8 frozen elements, machine-readable subset)
      ▼
dataset snapshot   ──hash──▶  content_hash  (dataset_manifest.json)
      │
      ▼
result report      ──hash──▶  report_hash   (experiment_results/)
      │
      ▼
reproduction_record.json  — binds all four hashes + the commit ref
                             in one place (Section 2)
```

Each arrow is a **hash reference**, not a copy — nothing above duplicates
another artifact's content, it only cites it. This mirrors the existing
`FREEZE_RECORD.md` convention (cites a commit hash, doesn't re-embed the
frozen files) and Standard §5's supersession rule (new dated file,
cross-referenced, nothing edited in place).

---

## 2. Reproduction Contract

### 2.1 Formal definition

**Input** (four items, all resolvable from the archive alone — no
tribal knowledge required):

| Element | Source | Must match |
|---|---|---|
| Repository commit | `reproduction_record.json.commit_hash` | Exactly (git SHA) |
| Dataset artifact | `dataset_manifest.json.datasets[].content_hash` | Exactly (sha256) |
| Environment | `.python-version` at that commit (§4) | Python major.minor exactly; patch version tracked but not gating |
| Experiment configuration | `methodology.md`'s 8 frozen elements + a `config_hash` over their machine-readable form | Exactly (sha256) |

**Output:**

| Element | Form |
|---|---|
| Deterministic result report | JSON, same shape as existing `*_significance_report*.json` |
| Verification status | One of `VERIFIED`, `DRIFTED`, `REPRODUCTION_FAILED`, `UNVERIFIABLE` (extends `FreezeStatus`, see below) |

### 2.2 Verification status — extending, not replacing, `FreezeStatus`

`core/governance/freeze_verifier.py` already defines a 3-way
`FreezeStatus` for code/document drift. Dataset reproduction needs a
4th, semantically distinct state that `FreezeStatus` cannot express:
*inputs matched exactly, but the computed output didn't* — a real
non-determinism or environment bug, categorically different from
"someone edited a frozen file."

```python
class ReproductionStatus(str, Enum):
    VERIFIED = "verified"                    # inputs matched, output matched
    DRIFTED = "drifted"                       # an input (commit/dataset/config) doesn't match its claimed hash
    REPRODUCTION_FAILED = "reproduction_failed"  # all inputs matched; output did not
    UNVERIFIABLE = "unverifiable"             # a referenced artifact is missing/unresolvable
```

`REPRODUCTION_FAILED` is the state that would have caught a silent
non-determinism bug (unseeded randomness, float-precision drift across
Python versions) that `DRIFTED` structurally cannot catch, because
`DRIFTED` only inspects inputs.

### 2.3 What must match exactly vs. what may vary

**Must match exactly:**
- Commit hash, dataset content hash, config hash (all sha256/SHA-1 —
  binary yes/no, no tolerance concept applies).
- Statistical results computed from `Decimal`-typed inputs (prices,
  returns derived from them) — this codebase already stores money as
  `Decimal`-compatible `TEXT` specifically to avoid float
  non-determinism; the reproduction contract should hold that guarantee
  to its word: **zero tolerance** on any figure that never passed through
  `float`.

**Acceptable numerical tolerance — and where it is actually needed:**
`core/statistics/significance.py` is `float`-based by its own docstring
("same numeric precision (float, converted once at the boundary"), and
its permutation/bootstrap functions consume an injected
`random.Random` instance. Given an identical seed, identical input
ordering, and identical Python version, CPython's `random.Random` and
IEEE-754 float arithmetic are deterministic — but that determinism is an
*implementation* guarantee of CPython on a given version, not a language
guarantee across Python releases or interpreters (PyPy). Tolerance
policy:
- `mean_ic`, `pearson_correlation`, `top_bottom_spread`, and other direct
  arithmetic: **exact match** (same Python minor version → same result,
  no epsilon needed; this is a testable claim, see §5).
- `permutation_null`, `bootstrap_ci` (resampling-dependent): **exact
  match**, contingent on same seed + same Python version — if this ever
  fails on an environment with the same commit/dataset/config hashes, that
  is itself evidence the environment lock (§4) is under-specified, not
  grounds to loosen the tolerance.
- No blanket epsilon (e.g. "1e-6") should ever be adopted as a
  substitute for pinning the environment precisely enough to not need
  one. A tolerance band is a admission that the environment lock failed,
  not a design feature.

**Failure conditions:**
- Any input hash mismatch → `DRIFTED`, reproduction refused before any
  computation runs (fail fast, matching `FreezeVerifier`'s existing
  pattern of never running "review" logic against unverified state).
- Referenced commit/dataset/config artifact does not resolve →
  `UNVERIFIABLE`.
- All inputs match, output differs → `REPRODUCTION_FAILED`, and this is
  the loudest possible signal — it means either the environment lock is
  incomplete or a real non-determinism bug exists. It must never be
  silently retried or averaged away.

---

## 3. Archive Evolution

### 3.1 What already exists

`research_archive/` has three legacy directories (`reference_v1`,
`reference_v2_h1`, `reference_h3`), each a different ad hoc shape (3
flat files / 3 flat files / 19 files — already documented as technical
debt in the retrospective §5 item 4). [AD-030](ARCHITECTURE_DECISIONS.md)
has *already decided* these will never receive a retroactive
`archive_manifest.json`, on the grounds that doing so "would itself be a
silent edit to a closed archive." `tools/archive_manifest.py` enforces
this in code (`LEGACY_ARCHIVE_PROJECT_IDS`, a hardcoded frozenset of
three names, checked in `write_manifest()`).

### 3.2 Independent evaluation of A / B / C

**A — Migrate.** Reject outright. Rewriting three already-closed,
already-cited archives into a new shape is precisely the action Standard
§5's append-only/supersession discipline and AD-004's migration
discipline both exist to prevent. It would also be the single most
damaging thing this proposal could recommend for institutional trust:
the audit exists to prove *these specific historical results* are what
they claim to be, and touching them to make that easier to check is
self-defeating.

**B — Frozen as historical (the status quo, per AD-030).** Correct in
spirit, but has a real, currently-unaddressed weakness: the exemption
lives *only* inside `tools/archive_manifest.py`'s `write_manifest()`
function, as a hardcoded name list nothing else references. When
`ArchiveVerifier` or the `ReproductionStatus` checker from §2 is
eventually built, it will need to know these three directories are
exempt from the reproduction contract *by design*, not silently missing
evidence — and today, nothing tells it that except a constant buried in
a different module's write path, which a reproduction-checking tool has
no structural reason to import. Left as-is, the first person to run a
future `ReproducibilityChecker` against `reference_v1/` gets an
indistinguishable `UNVERIFIABLE`, whether the archive is legitimately
exempt or actually broken.

**C — Wrap with new metadata, as originally proposed in
`RESEARCH_ARCHIVE_MANIFEST.md`.** That document's specific objection —
*"adding one after the fact would itself be a silent edit to a closed
archive"* — conflates two different actions. Editing or backfilling a
file to make an old archive **look like it always had the new
structure** is deceptive and correctly rejected. Adding a **new,
separately-dated, clearly-external file** that describes the archive
from outside — stating what it is, what it does not have, and why — is
exactly what Standard §5 already blesses for every other kind of
correction ("a correction is a new, dated file, cross-referenced from
the file it supersedes — the superseded file is retained, unedited").
`FREEZE_RECORD.md` for H3 is itself an example of this pattern already
in use: a new file added after the fact, describing provenance, without
editing anything it describes.

**Recommendation: a narrow, additive exemption record — not full "C," not
bare "B."**

- `MUST HAVE`: one new file per legacy directory,
  `research_archive/<legacy>/LEGACY_PROVENANCE_NOTE.md`, added once,
  stating: this archive predates the reproducibility system; no dataset
  snapshot, `dataset_manifest.json`, or `config_hash` exists or ever
  will for it; any reproduction check against it should report
  `UNVERIFIABLE (legacy — exempt by design, see AD-030)`, not a bare
  `UNVERIFIABLE`. Deliberately **not** named `archive_manifest.json` or
  `dataset_manifest.json`, so it can never collide with, or be mistaken
  for, either real schema, and so `write_manifest()`'s existing refusal
  needs no code change.
- `MUST HAVE`: `LEGACY_ARCHIVE_PROJECT_IDS` moves to a single shared
  location (e.g. `core/shared/legacy_archives.py`) that both
  `tools/archive_manifest.py` and the future `ReproducibilityChecker`
  import, instead of the constant being re-declared (and potentially
  drifting) wherever it's next needed.
- `SHOULD HAVE`: the future `ArchiveVerifier`/`ReproducibilityChecker`
  (§5) treats "legacy + provenance note present" as its own reportable
  state, not a silent pass or a scary-looking failure.

### 3.3 Tradeoff summary

| Option | Institutional trust | Engineering cost | Leaves a trap for future tooling? |
|---|---|---|---|
| A — Migrate | Destroyed | High | N/A (rejected) |
| B — Frozen, untouched (status quo) | Preserved | Zero | Yes — hardcoded exemption only in one write path |
| C — Full metadata wrap | Preserved, if done additively | Low | No, but oversteps what's needed |
| **Recommended: narrow provenance note + shared constant** | Preserved | Low | No |

---

## 4. Environment Reproducibility

### 4.1 The question the audit's framing skips

"Evaluate requirements.txt / uv.lock / poetry.lock / Docker / Nix" already
presupposes a dependency-management problem exists. Verified fact: there
is no `requirements.txt`, no lock file, no `Dockerfile`, and `pyproject.toml`
is four lines — pytest config only, no `[project]` table, no dependency
list, because **AD-005 means there is nothing to list.** The one runtime
import outside the standard library across `core/`, `adapters/`, and
`experiments/` is `pytest` itself, and it is dev-only. Recommending
Docker or Nix for a zero-runtime-dependency, stdlib-only codebase would
add a new maintenance surface (a base image with its *own* reproducibility
story, its own patch cadence, its own multi-year support question) to
solve a problem that mostly doesn't exist here. That would fail this
proposal's own "prefer simple robust solutions" constraint.

What genuinely is unpinned today, and matters:

1. **Python interpreter version.** Nothing pins it anywhere. Locally:
   3.12.10. `random.Random` + `float` determinism (§2.3) is only as
   strong as this pin.
2. **`pytest` version.** Unpinned, dev-only, but test *behavior*
   (collection, fixture semantics) can change across major pytest
   releases in ways that affect whether the reproduction test in §5 even
   runs the same way twice.
3. **OS-level determinism.** SQLite's own file format and `sqlite3`
   stdlib module behavior are stable across the officially supported OS
   set; nothing here relies on OS-specific float behavior since money
   values are `Decimal`-via-`TEXT`. The known live risk is line-ending
   handling in snapshot files (§1.4) and in the CRLF test fragility
   already on record from Phase 3 — a platform difference, not a
   dependency one.

### 4.2 Recommendation

**MUST HAVE:**
- `.python-version` file at repo root, pinning the minor version (e.g.
  `3.12`) that the reproduction contract's "must match" column (§2.3)
  actually requires. This alone is the entire "environment lock" this
  codebase needs for its production code path.
- A minimal `[project]` table added to `pyproject.toml` declaring
  `requires-python = ">=3.12,<3.13"` — turns today's implicit,
  undocumented assumption into an enforced one (`pip install` already
  refuses to proceed outside a declared `requires-python` range).
- `requirements-dev.txt` — one pinned line, `pytest==<version>`. Not a
  lock file in the uv/poetry sense (there is nothing transitively to
  lock; pytest's own dependency tree is the only thing that could drift,
  and pinning pytest itself is sufficient at this dependency count).

**SHOULD HAVE:**
- CI (§5) asserts the running interpreter's `sys.version_info[:2]`
  matches `.python-version` before running the reproduction test, so a
  silent CI-runner upgrade is caught immediately rather than showing up
  as a mysterious `REPRODUCTION_FAILED`.

**Explicitly rejected for now (FUTURE ENHANCEMENT at most):**
- **Docker.** No runtime dependency isolation problem exists to solve;
  the cost (image maintenance, base-image CVE churn, contributor friction
  of "now you need Docker installed to touch a stdlib-only Python repo")
  outweighs a benefit this codebase doesn't currently need. Revisit only
  if AD-005 is ever revisited and a real third-party numerical dependency
  enters the picture — Docker earns its cost pinning *that*, not pinning
  Python-plus-stdlib.
- **uv.lock / poetry.lock.** Same reasoning, smaller version — these
  tools solve transitive dependency resolution, and there are no
  transitive dependencies. Adopting one now is process theater; it
  performs rigor without adding any.
- **Nix.** Full system-level reproducibility (compiler, libc, and
  beyond) is disproportionate to a workload that is "run this stdlib
  Python script against this SQLite file." If this platform ever needs
  bit-identical results across heterogeneous OSes at the C-library level
  (which today it explicitly does not — no numeric C extensions are in
  the dependency graph, because there is no dependency graph), Nix
  becomes worth its steep contributor learning curve. Not before.

**5–10 year framing.** A `.python-version` pin plus a one-line
`requirements-dev.txt` is the artifact most likely to still be
meaningful in a decade — it says exactly what it needs to say and
nothing else. A Dockerfile written today would almost certainly need
active maintenance (base image EOL, e.g.) well before then; an unpinned,
undocumented assumption (today's actual state) would be actively
misleading by then. The recommendation optimizes for "still correct and
still legible in 2036," not for looking rigorous today.

---

## 5. Automated Verification

### 5.1 Precondition the audit's framing skips

**There is no CI in this repository.** No `.github/workflows/`, no other
CI config of any kind, anywhere. "Design `tests/test_reproduction_contract.py`
and explain how CI should behave" presupposes a CI system that does not
exist yet. This is listed as a MUST HAVE precisely because everything
else in this section is inert without it — a reproduction test that only
ever runs when a human remembers to type `pytest` locally provides none
of the "can't merge a silent break" guarantee the audit is actually
asking for.

### 5.2 `tests/test_reproduction_contract.py` design

Structure, following this repository's existing pure/IO-split discipline
(`core/analytics/domain/calculations.py`'s pattern, `AD-007`'s injectable
`Clock`):

```python
"""Reproduction-contract verification (Phase 4).

For each cycle with a reproduction_record.json under research_archive/,
proves: dataset hash matches, config hash matches, and re-running the
frozen experiment against the frozen (not live) dataset snapshot
reproduces the archived result report exactly.

Never touches experiments_etf_universe.db or the network. Every input is
read from committed, git-tracked files only -- the same "fully offline,
canned data" pattern tests/test_yahoo_finance_provider.py already
established for the market-data provider (AD-007's injectable fetch).
"""

def test_dataset_hash_matches_manifest(cycle_dir: Path) -> None:
    """Re-hash every dataset_hashes/*.jsonl file; compare to
    dataset_manifest.json's declared content_hash. Pure sha256, no
    network, no live DB."""

def test_config_hash_matches_manifest(cycle_dir: Path) -> None:
    """Re-hash the machine-readable config extracted from methodology.md
    (or its dedicated companion file); compare to reproduction_record.json's
    config_hash."""

def test_experiment_reproduces_archived_result(cycle_dir: Path) -> None:
    """Load the frozen dataset snapshot (not the live DB), run the
    cycle's actual experiment/statistics functions against it with the
    archived seed, and assert byte-equality (or the declared, near-zero
    tolerance per Section 2.3) against the archived result report."""

def test_environment_matches_lock(cycle_dir: Path) -> None:
    """Assert sys.version_info[:2] matches .python-version. A future
    reproduction attempt on the wrong interpreter should fail loudly
    here, not produce a silently-wrong REPRODUCTION_FAILED downstream."""
```

The third test is the one doing real work, and it has a real
prerequisite that does not exist yet: **experiment scripts must accept
an injected data source**, the same way `YahooFinanceProvider` already
accepts an injected `fetch` callable
(`core/market_data/providers/yahoo_finance.py`) so its own tests run
fully offline. Today's `experiments/validate_*.py` scripts read from
`experiments_etf_universe.db` directly; without an injection point, a
reproduction test cannot substitute the frozen snapshot for the live
database without either mutating the live DB (forbidden, Standard §6
control 1) or maintaining a parallel, second implementation (drift risk).
This is a real, non-trivial piece of implementation work this design
depends on — flagged here rather than glossed over, per this proposal's
"attack weak assumptions" instruction to itself.

### 5.3 How CI should behave

**MUST HAVE:**
- A CI workflow (any runner — GitHub Actions is the obvious default
  given a GitHub-shaped repo, but nothing here is vendor-specific) that
  runs `pytest` on every push and PR, full stop. This does not exist
  today and is a prerequisite independent of Phase 4.
- `test_reproduction_contract.py` runs in that same workflow, fully
  offline (network access should be blocked or simply unnecessary — the
  test suite never needs `urllib` once snapshots exist), and is
  merge-blocking for any PR touching `core/statistics/`,
  `core/market_data/`, or any `research_archive/**` path.
- A `REPRODUCTION_FAILED` result blocks merge unconditionally — no
  override, no "acknowledge and merge anyway" path. A `DRIFTED` or
  `UNVERIFIABLE` result on an *existing* cycle blocks merge too, since it
  means the PR broke a previously-working reproduction; a `DRIFTED`
  result is the whole point of the check.

**SHOULD HAVE:**
- A scheduled (weekly) CI run of the full reproduction suite even absent
  any PR, catching silent environment drift (e.g. the CI runner's own
  Python image gets bumped) that no code change would otherwise trigger.

**Explicitly out of scope for CI:** re-fetching from Yahoo Finance live
in CI. The entire point of the frozen snapshot is that CI, and any future
external reviewer, never needs live network access to verify a historical
result. If the live provider's data ever needs re-validating against the
new API surface, that is a separate, deliberate `experiments/` script
run by a human, producing a *new* dated snapshot — never something CI
does automatically or silently.

---

## 6. Institutional Benchmark

| Practice | Academic computational research | Quant hedge funds | Regulated investment research | This proposal |
|---|---|---|---|---|
| Data snapshot | Often absent or informal (a `data/` folder, no hash) — this repo's *current* state is roughly here | Point-in-time database (bitemporal), full commercial-grade lineage | Point-in-time database, often vendor-audited | Content-addressed, git-tracked scoped extracts — stronger than typical academic practice, weaker than institutional bitemporal PIT storage |
| Environment lock | Increasingly `environment.yml`/Docker (post-2020 replication crisis pressure) | Internal package repos, pinned to the commit | Vendor-controlled compute environments, often literally frozen hardware images | `.python-version` + one pinned dev dependency — proportionate to a stdlib-only codebase; would be *under*-specified for a numpy/pandas-heavy one |
| Reproduction test | Rare; "replication package" is usually a zip file, not a CI-verified claim | Standard — nightly reproduction of live strategies against historical state is table stakes | Required by SR 11-7 (model risk management) style regimes — independent reproduction is a compliance artifact, not a nice-to-have | `test_reproduction_contract.py`, merge-blocking — closer to institutional practice than most academic replication packages, once CI exists (§5.1) |
| Review independence | Peer review (genuinely external, but rarely re-runs the code) | Independent model validation function, org-separated from the desk that built the model | Mandated independent validation (model risk management) | Already explicitly modeled and honestly disclosed: this platform has Level 1/2 review only, **no Level 3**, and says so in writing ([Standard §4](RESEARCH_GOVERNANCE_STANDARD.md#4-reviewer-independence-model)) rather than papering over it |
| Immutable archive | Sometimes a Zenodo DOI per paper | Regulatory retention requirements (often 7 years), WORM storage | Regulatory retention, often longer | git history + append-only `decision_log.md` convention — durable, but **not WORM**; a force-push or history rewrite is not structurally prevented, only socially prohibited |

**Remaining gaps after Phase 4, stated plainly:**

1. **No point-in-time database.** This design snapshots the rows an
   experiment actually reads, after the fact. A true institutional
   setup maintains bitemporal storage (as-of-date *and* as-reported-date)
   so *any* historical query, not just ones anticipated by a snapshot,
   can be answered exactly. Out of scope here — real infrastructure
   investment, correctly deferred (matches this repo's own Tier
   discipline: don't build ahead of a second concrete need).
2. **No WORM guarantee on the git history itself.** `git push --force`
   to `main` is a social prohibition (per this platform's own operating
   discipline) not a technical one. An institutional archive typically
   has this enforced at the infrastructure layer (branch protection,
   immutable object storage). Not addressed by this proposal — flagged
   as a real, currently-open gap, not swept under "governance is
   strong."
3. **No Level 3 review capacity.** Already honestly disclosed elsewhere
   in this platform's own documents; repeating it here because "compare
   against regulated investment research" cannot honestly avoid it —
   regulated research requires exactly the org-separated validation
   function this platform states it does not have.
4. **Single-operator risk.** Every control in this document — freeze
   verification, dataset hashing, reproduction tests — is designed to
   be checkable by a machine, which is good, but every *decision* about
   what to freeze, what tolerance to accept, what counts as an anomaly,
   is still made by the same single operator directing both research and
   review. Tooling closes the mechanical-error gap; it does not, and
   cannot, close the independence gap. Section 3's Level 3 discussion
   already says this; it is repeated here so the benchmark section
   doesn't imply otherwise.

---

## Summary: MUST HAVE / SHOULD HAVE / FUTURE ENHANCEMENT

| Tier | Item |
|---|---|
| **MUST HAVE** | `dataset_manifest.json` schema v1 + canonicalization rules (§1.3–1.4) |
| **MUST HAVE** | Scoped, JSONL, git-tracked dataset snapshots under `dataset_hashes/`, hashed as stored bytes (§1.4–1.5) |
| **MUST HAVE** | `reproduction_record.json` binding commit + dataset + config + report hashes (§1.6, §2.1) |
| **MUST HAVE** | `ReproductionStatus` enum extending `FreezeStatus` with `REPRODUCTION_FAILED` (§2.2) |
| **MUST HAVE** | `LEGACY_PROVENANCE_NOTE.md` per legacy archive + shared `LEGACY_ARCHIVE_PROJECT_IDS` constant (§3.2) |
| **MUST HAVE** | `.python-version` + `requires-python` in `pyproject.toml` + pinned `requirements-dev.txt` (§4.2) |
| **MUST HAVE** | CI workflow running `pytest` on every push/PR — does not exist today, blocks everything in §5 (§5.1, §5.3) |
| **MUST HAVE** | Injectable data-source seam on `experiments/validate_*.py` scripts, mirroring `YahooFinanceProvider`'s injectable `fetch` (§5.2) |
| **MUST HAVE** | `tests/test_reproduction_contract.py`, merge-blocking in CI (§5.2–5.3) |
| **SHOULD HAVE** | Documented snapshot size ceiling (20 MB) with an explicit escalation path past it (§1.5) |
| **SHOULD HAVE** | CI asserts running interpreter matches `.python-version` before reproduction tests run (§4.2) |
| **SHOULD HAVE** | Weekly scheduled CI run of the full reproduction suite, independent of PR activity (§5.3) |
| **SHOULD HAVE** | `ArchiveVerifier`/`ReproducibilityChecker` treats "legacy + provenance note" as its own reportable state (§3.2) |
| **FUTURE ENHANCEMENT** | External content-addressed storage, if a cycle ever genuinely exceeds the snapshot size ceiling (§1.5) |
| **FUTURE ENHANCEMENT** | Docker/Nix, only if AD-005 is ever revisited and a real third-party numerical dependency enters the codebase (§4.2) |
| **FUTURE ENHANCEMENT** | Point-in-time (bitemporal) market data storage (§6, gap 1) |
| **FUTURE ENHANCEMENT** | WORM/branch-protection enforcement on archive history (§6, gap 2) |

---

## Phase 4 Readiness Assessment

**Current maturity level:** Governance-designed, evidence-absent. Every
schema and interface this document proposes already has a named forward
reference in `docs/PLATFORM_ARCHITECTURE_V1.md` §4.4 and a scheduled slot
in the retrospective's Tier 3 roadmap — the *design* maturity is
genuinely high. The *implementation* maturity for dataset preservation
specifically is zero: no hashing code, no snapshot convention, no CI at
all, no environment pin. This is not a contradiction; it is a platform
that has consistently written down what it intends to build before
building it (visible in AD-030, AD-036, AD-038, AD-039 all explicitly
deferring implementation pending "a concrete consumer") — Phase 4 is that
concrete consumer arriving.

**Required changes (implementation, not further design):**
1. `core/shared/dataset_hash.py` (or equivalent) — pure hashing/manifest
   functions, mirroring `tools/archive_manifest.py`'s pure/IO split.
2. A dataset-extraction script (or `experiments/` helper) that queries
   `PriceBar` for a stated universe/date-range and writes canonical
   JSONL.
3. `core/governance/reproduction_checker.py` — extends
   `freeze_verifier.py`'s pattern with dataset-hash and config-hash
   checks, returns `ReproductionStatus`.
4. Injectable data-source seam on the four existing
   `experiments/validate_*.py` scripts.
5. `.python-version`, `pyproject.toml` `[project]` table,
   `requirements-dev.txt`.
6. A CI workflow file — the one item on this list with no existing
   partial implementation anywhere in the repository to extend.
7. `tests/test_reproduction_contract.py`.
8. Three `LEGACY_PROVENANCE_NOTE.md` files (small, additive, no code).
9. A first real `reproduction_record.json` + dataset manifest, generated
   for the next hypothesis cycle to open (H4, per project memory) —
   applying this design to the retroactive legacy archives is explicitly
   out of scope (§3).

**Estimated complexity:** Moderate, not large, precisely because AD-005
already removed the hardest part (no dependency graph to lock) and
`FreezeVerifier`/`archive_manifest.py` already establish the exact
code patterns (pure/IO split, refuse-don't-silently-skip, 3-way status
enums) items 1–3 above extend rather than invent. The single largest
unknown is item 4 (the injection seam) — it touches four already-shipped
scripts that were not written with this seam in mind, and doing it
without changing any script's frozen numerical behavior (the same
"behavior-preserving" bar `core/statistics/significance.py`'s own
extraction held itself to) is real, careful work, not a rubber stamp. Item
6 (CI) is mechanically simple but organizationally is the one item that
was not on any prior roadmap at all — worth flagging to whoever approves
this proposal as a scope addition beyond what the audit named.

**Does this close the reproducibility objection from the audit?**
Yes, for every research cycle opened *after* Phase 4 ships — a future
reviewer, given only a commit hash and a `research_archive/<cycle>/`
directory, can mechanically verify the dataset, the configuration, and
the result, offline, without trusting any human's account of what
happened. **No**, for the three cycles already closed
(`reference_v1`, `reference_v2_h1`, `reference_h3`) — those remain, and
under this proposal's own §3 recommendation, will always remain,
evidenced only to the standard that existed when they were produced, with
an honest, explicit note saying so. That is not a shortcoming of this
design; treating a closed historical record as reproducible-after-the-fact
would be the actual audit failure. The correct claim for this platform to
make, once Phase 4 ships, is: *"every result from H4 onward is
independently reproducible from the archive alone; every result before it
is exactly as trustworthy as it always was, honestly labeled as
predating this guarantee."* That is a narrower claim than "we fixed
reproducibility," and it is the true one.
