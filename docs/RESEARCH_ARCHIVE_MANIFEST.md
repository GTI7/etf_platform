# Research Archive Manifest v1

**Status: additive concept, Phase 0 of `docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md`.**
This document defines the shape of `archive_manifest.json`, a small,
versioned index file that will accompany the evidence package
(`docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 5) for every *future*
research project archived under `research_archive/<project>/`.

**This is an early preservation/integrity guard, not the complete
future archive system.** It was introduced in Phase 0, ahead of any
`core/governance/` business logic, to answer one narrow question
safely and immediately: can the earliest platform tooling be made
structurally incapable of writing into or overwriting a closed,
historical archive. `tools/archive_manifest.py`'s `write_manifest()`
guarantees exactly that (see "Reference implementation" below) and
nothing more — it does not check archive completeness, does not read
or interpret an existing manifest, and does not implement
`ArchiveVerifier`. A future `ArchiveVerifier`
(`docs/PLATFORM_ARCHITECTURE_V1.md` Section 4.4) is expected to build
on this manifest as its input contract — reading `schema_version` and
`lifecycle_version` to decide what shape of completeness check to run
against the rest of Standard Section 5's evidence package — rather
than replacing it. See `docs/ARCHITECTURE_DECISIONS.md` AD-030.

It does not apply retroactively. `research_archive/reference_v1/`,
`research_archive/reference_v2_h1/`, and `research_archive/reference_h3/`
each predate this concept, each have their own shape (3 flat files / 3
flat files / 19 files respectively — see
`docs/RESEARCH_PLATFORM_RETROSPECTIVE.md` Section 5, item 4), and none
of them will be given an `archive_manifest.json` retroactively. Adding
one after the fact would itself be a silent edit to a closed archive,
which every governing document on this platform (Standard Section 5,
`decision_log.md`'s append-only discipline, AD-004's migration
discipline) treats as never acceptable. A manifest is only ever written
once, at the point a *new* project's archive directory is created.

## Schema (`schema_version: 1`)

```json
{
  "schema_version": 1,
  "project_id": "h4",
  "created_at": "2026-08-01T00:00:00+00:00",
  "lifecycle_version": "v1"
}
```

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | integer | Version of this manifest's own shape, not of the project it describes. Starts at `1`. A future change to this document's schema is a new integer, added as a new revision of this document (Section "Versioning" below) — never a silent reinterpretation of an existing field. |
| `project_id` | string | The project's identifier, matching its `research_archive/<project_id>/` directory name and (once `core/research/`'s `ProjectRegistry` exists) its `ProjectId`. |
| `created_at` | string | ISO 8601, UTC-offset timestamp of the moment this manifest was generated — not the project's Phase 1 hypothesis date, which belongs in `hypothesis.md`. |
| `lifecycle_version` | string | Either `"legacy"` or `"v1"` (see below). Never any other value in schema v1. |

### `lifecycle_version` values

- **`"legacy"`** — describes a project whose archive predates this
  manifest concept and does not follow
  `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 5's evidence-package
  structure (`reference_v1`, `reference_v2_h1`, `reference_h3`). A
  `"legacy"`-tagged manifest is descriptive metadata only — recording
  that a directory of this shape exists and predates the standard — and
  is never generated *into* one of those three directories (see
  "Applicability" above). It exists in this schema only so a future
  `ArchiveVerifier` (per `docs/PLATFORM_ARCHITECTURE_V1.md` Section
  4.4) can distinguish "this project is exempt from the v1 layout
  check" from "this project should have the v1 layout and doesn't."
- **`"v1"`** — describes a project whose archive is expected to follow
  the full evidence-package structure: `hypothesis.md`, `methodology.md`,
  `dataset_manifest.json`, `dataset_hashes/`, `experiment_results/`,
  `reviewer_reports/`, `decision_log.md` (Standard Section 5). Every
  *new* project's manifest uses this value.

## What this document does not do

- It does not implement `ArchiveVerifier` (`docs/PLATFORM_ARCHITECTURE_V1.md`
  Section 4.4) — that requires `core/governance/` business logic, out
  of scope for Phase 0.
- It does not generate a manifest for any hypothesis currently open on
  this platform — there is none as of this document's writing (H3 is
  closed; H4 has not opened).
- It does not require `dataset_hashes/`, `reviewer_reports/`, or any
  other Standard Section 5 evidence-package item to exist yet — this
  manifest is the index a future `ArchiveVerifier` will check *against*
  that structure, not the structure itself.

## Reference implementation

`tools/archive_manifest.py` provides a pure `build_manifest()` function
matching this schema exactly, and a `write_manifest()` function that
refuses to write into any of the three legacy archive directories named
above, and refuses to overwrite an existing manifest file. It is
tooling, not `core/governance/` business logic — see that module's
docstring.

### Archive scaffold generator

`scaffold_project_archive(project_id, archive_root, clock, *,
lifecycle_version="v1")` composes `build_manifest()` and
`write_manifest()` to set up a *new* project's archive directory in one
call: it writes `archive_manifest.json`, then creates the three empty
evidence subdirectories Standard Section 5 expects —
`dataset_hashes/`, `experiment_results/`, `reviewer_reports/` — each
with a `.gitkeep` file so git tracks the empty directory. Both of
`write_manifest()`'s refusals (legacy archive directory, existing
manifest) apply unchanged, since the scaffold generator calls it rather
than duplicating its checks.

**It creates evidence directories, not evidence files (AD-038).**
`hypothesis.md`, `methodology.md`, `dataset_manifest.json`, and
`decision_log.md` are authored content — a human writes them as the
project's actual hypothesis, methodology, and decisions take shape.
Scaffolding empty stubs for any of them would let a reader mistake an
empty file for recorded evidence, so the generator never creates them.

## Versioning

This document follows the same discipline
`docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 9 and
`docs/PLATFORM_ARCHITECTURE_V1.md` Section 9 already establish for
themselves: a future revision to this schema is a new, dated version of
this document with a new `schema_version` integer, never a silent edit
to what `schema_version: 1` means.

**Version:** 1. **Effective:** upon commit of this document.
