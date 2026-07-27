"""Research artifacts: per-cycle registration data, not engine capability.

Every module here is a **record of specific research cycles that
happened** -- their identifiers, origin dates, outcomes, and pointers to
the committed evidence that substantiates each field. `historical_backfill`
holds the three closed cycles (`reference_v1`, `reference_v2_h1`,
`reference_h3`); `reference_h4_registration` holds the one open cycle
registered under AD-050 A6-C4. Both are data with a thin function around
them, and both would be *wrong* to carry into a fresh deployment of this
platform, which is the test that distinguishes an artifact from a
capability.

**Why they are not under `core/`.** They lived in `core/research/` from
Migration Plan Step 5 (2026-07-19) until 2026-07-27. That placement made
the Research *engine* -- the package that owns `Project`,
`ProjectRegistry`, and the lifecycle machinery -- name `reference_h4` and
the three REFERENCE cycles in its own source tree, so reading
`core/research/` could not tell you which parts are the platform and
which are one operator's history with it. `core.analytics` under AD-068
is the precedent in the opposite direction: a workload that reaches down
into the engine, never something the engine names.

**The dependency runs one way.** These modules import
`core.research.project`, `core.research.project_id`, and
`core.research.project_registry`; nothing under `core/` imports anything
here, and nothing here may be imported by `core/` in the future. That is
the entire structural claim, and it is enforced by the direction of the
import graph rather than by a check: `tools/check_import_boundaries.py`
scans `core/` only, so a `core -> research_artifacts` import would be
invisible to it. Reviewers, not tooling, hold this edge today.

**What did not move.** `Project`, `ProjectRegistry`,
`create_project_id`, `ResearchProjectRepository`, and the lifecycle
machinery are engine capability and stay in `core/research/`. A future
cycle registers itself by adding a module here, never by editing one
there.
"""
