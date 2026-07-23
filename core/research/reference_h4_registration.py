"""Registration of the `reference_h4` open research cycle (Phase 4 / Step
9, increment B-3b -- see docs/PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md
Section 4.2's Phase B row, "H4 project registration", and
docs/ARCHITECTURE_DECISIONS.md's AD-050 A6-C4/A6-C5/A6-C6).

Registers `reference_h4` as an **open** `Project` --
`lifecycle_state=ACTIVE`, `research_outcome=None` -- under the
identifier AD-050 A6-C4 fixes: `reference_h4`, byte-identical across the
`research_archive/` directory name, the `cycle_name`, the `ProjectId`
string, and `archive_manifest.json`'s `project_id` field.

Per A6-C5, registering `reference_h4` **asserts nothing about hypothesis
content, data adequacy, or Phase 2 selection** -- no Phase 1 or Phase 2
artifact exists for this cycle yet, and the description below is
deliberately silent on hypothesis content. This module is identity
registration only, matching `research_archive/reference_h4/`'s own
scope: only `archive_manifest.json` was written there (via
`tools/archive_manifest.py`'s `build_manifest()`/`write_manifest()`, not
`scaffold_project_archive()`) -- no evidence subdirectories exist yet,
because manifest creation is identity registration, not evidence
initialization.

`origin_date` is `research_archive/reference_h4/archive_manifest.json`'s
own `created_at` date (AD-050 A6-C6: "`origin_date` would be taken from
`archive_manifest.json`'s `created_at`, an already-recorded evidence
date") -- this is the **archive registration date**, not a research
start date; no Phase 1 hypothesis date exists yet for this cycle.

This module contains no git operations, no freeze verification, no
archive scaffolding, and no lifecycle-transition logic -- it only
constructs one `Project` record and calls
`ProjectRegistry.register_project`, the same scope
`core/research/historical_backfill.py` keeps for the three historical
cycles. It introduces no generic registration abstraction: this is a
single, named function for a single, named cycle, not a reusable
registry framework.
"""

from __future__ import annotations

from datetime import date

from core.research.project import Project, ProjectLifecycleState
from core.research.project_id import create_project_id
from core.research.project_registry import ProjectRegistry

REFERENCE_H4_PROJECT = Project(
    project_id=create_project_id("reference_h4"),
    name="reference_h4",
    description=(
        "Open research cycle registered under the identifier fixed by "
        "AD-050 A6-C4. No Phase 1 hypothesis or Phase 2 selection has "
        "been recorded for it -- registration asserts nothing about "
        "hypothesis content, data adequacy, or Phase 2 selection "
        "(AD-050 A6-C5)."
    ),
    lifecycle_state=ProjectLifecycleState.ACTIVE,
    research_outcome=None,
    origin_date=date(2026, 7, 23),
    repository_path="research_archive/reference_h4",
    metadata={
        "manifest": "research_archive/reference_h4/archive_manifest.json",
    },
)


def register_reference_h4(registry: ProjectRegistry) -> None:
    """Register `REFERENCE_H4_PROJECT` into `registry`. Raises
    `ValueError` (via `ProjectRegistry.register_project`) if `reference_h4`
    is already registered -- not idempotent, matching
    `ProjectRegistry`'s own duplicate-id policy."""
    registry.register_project(REFERENCE_H4_PROJECT)
