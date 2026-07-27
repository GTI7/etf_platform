"""Registration of the `reference_h2` open research cycle (long-term
momentum, 12-1 month formation with a 1-month skip -- see
docs/PHASE5_HYPOTHESIS_SELECTION_REVIEW_2026-07-27.md,
docs/PHASE5_GATE0_PREPARATION_REVIEW_H2_2026-07-28.md, and
docs/ARCHITECTURE_DECISIONS.md's AD-050 A6-C4/A6-C5/A6-C6).

Registers `reference_h2` as an **open** `Project` --
`lifecycle_state=ACTIVE`, `research_outcome=None` -- under the
identifier AD-050 A6-C4 fixes: `reference_h2`, byte-identical across the
`research_archive/` directory name, the `cycle_name`, the `ProjectId`
string, and `archive_manifest.json`'s `project_id` field.

Per A6-C5, registering `reference_h2` **asserts nothing about hypothesis
content, data adequacy, or Phase 2 selection** -- this module is
identity registration only, matching `research_archive/reference_h4/`'s
own precedent: only `archive_manifest.json` is written by this
registration step (via `tools/archive_manifest.py`'s `build_manifest()`/
`write_manifest()`, not `scaffold_project_archive()`) -- no evidence
subdirectories (`dataset_hashes/`, `experiment_results/`,
`reviewer_reports/`) exist yet, because manifest creation is identity
registration, not evidence initialization.

`origin_date` is `research_archive/reference_h2/archive_manifest.json`'s
own `created_at` date, following the same convention AD-050 A6-C6
records for `reference_h4` -- this is the **archive registration
date**, not a research start date. A dated Phase 1 hypothesis artifact
(`research_archive/reference_h2/hypothesis.md`) is committed alongside
this module, but that artifact's own date governs Phase 1 timing
questions, not this module's `origin_date`.

This module contains no git operations, no freeze verification, no
archive scaffolding beyond the manifest itself, and no lifecycle-
transition logic -- it only constructs one `Project` record and calls
`ProjectRegistry.register_project`, the same scope
`research_artifacts/reference_h4_registration.py` keeps. It introduces
no generic registration abstraction: this is a single, named function
for a single, named cycle, not a reusable registry framework.

Registering this identifier does not open Phase 1, does not select or
approve H2 as a research direction, and does not constitute a lifecycle
transition under `core/research/lifecycle.py` -- registering a cycle
does not imply `Hypothesis` or any other phase (AD-058).
"""

from __future__ import annotations

from datetime import date

from core.research.project import Project, ProjectLifecycleState
from core.research.project_id import create_project_id
from core.research.project_registry import ProjectRegistry

REFERENCE_H2_PROJECT = Project(
    project_id=create_project_id("reference_h2"),
    name="reference_h2",
    description=(
        "Open research cycle registered under the identifier fixed by "
        "AD-050 A6-C4. No Phase 2 selection has been recorded for it -- "
        "registration asserts nothing about hypothesis content, data "
        "adequacy, or Phase 2 selection (AD-050 A6-C5)."
    ),
    lifecycle_state=ProjectLifecycleState.ACTIVE,
    research_outcome=None,
    origin_date=date(2026, 7, 27),
    repository_path="research_archive/reference_h2",
    metadata={
        "manifest": "research_archive/reference_h2/archive_manifest.json",
    },
)


def register_reference_h2(registry: ProjectRegistry) -> None:
    """Register `REFERENCE_H2_PROJECT` into `registry`. Raises
    `ValueError` (via `ProjectRegistry.register_project`) if
    `reference_h2` is already registered -- not idempotent, matching
    `ProjectRegistry`'s own duplicate-id policy."""
    registry.register_project(REFERENCE_H2_PROJECT)
