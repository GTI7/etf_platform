"""Historical project backfill (Migration Plan Step 5, item 5).

Registers the three existing, closed research cycles --
`research_archive/reference_v1/`, `research_archive/reference_v2_h1/`,
`research_archive/reference_h3/` -- the complete set; no fourth
candidate exists in `research_archive/`. Every field below traces to a
specific, already-committed file (cited in each project's own
`metadata`); nothing is invented. This module **points to** that
existing evidence -- it does not duplicate, summarize, or re-derive any
of it, per Migration Plan Step 5's own framing ("the registry should
point to existing evidence, not duplicate it").

`origin_date` per project (see `core/research/project.py` for why this
is not called "created_at"):
- `reference_v1` / `reference_v2_h1`: the date embedded in each
  project's own frozen significance-report filename
  (`reference_v1_significance_report_2026-07-18.json`,
  `reference_v2_h1_significance_report_2026-07-18.json`) -- the
  earliest dated artifact either project's archive directory contains.
- `reference_h3`: the author date of its construction freeze commit
  (`research_archive/reference_h3/FREEZE_RECORD.md`,
  `2026-07-19T14:15:07+02:00`) -- H3's archive directory has no single
  dated snapshot file the way the other two do, so its freeze record is
  the earliest dated evidence available.

This module contains no git operations, no freeze verification, and no
lifecycle-transition logic -- it only constructs `Project` records and
calls `ProjectRegistry.register_project`.
"""

from __future__ import annotations

from datetime import date

from core.research.project import Project, ProjectLifecycleState
from core.research.project_id import create_project_id
from core.research.project_registry import ProjectRegistry


def _historical_projects() -> tuple[Project, ...]:
    return (
        Project(
            project_id=create_project_id("reference_v1"),
            name="REFERENCE v1",
            description=(
                "Cross-sectional MOMENTUM/VALUE/blend score IC significance test "
                "across 25 ETFs, 2024-07-17 to 2026-07-17 (463 ranking dates)."
            ),
            lifecycle_state=ProjectLifecycleState.ARCHIVED,
            research_outcome="ARCHIVE",
            origin_date=date(2026, 7, 18),
            repository_path="research_archive/reference_v1",
            metadata={
                "closeout_doc": "docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md",
                "freeze": {"commit": "19771d4fd93d95b223c6aff603fdaf8f31f28038"},
            },
        ),
        Project(
            project_id=create_project_id("reference_v2_h1"),
            name="REFERENCE v2 H1 (Low Volatility)",
            description=(
                "Low-volatility factor (H1) hypothesis test: LowVol score vs. "
                "subsequent raw and risk-adjusted return, 25 ETFs, 2024-10-11 to "
                "2026-06-17 (421 ranking dates)."
            ),
            lifecycle_state=ProjectLifecycleState.ARCHIVED,
            research_outcome="ARCHIVE",
            origin_date=date(2026, 7, 18),
            repository_path="research_archive/reference_v2_h1",
            metadata={
                "closeout_doc": "docs/REFERENCE_V2_H1_RESEARCH_CLOSEOUT.md",
                "freeze": {"commit": "8831d54b51b67dbbbcab1e2008d1f06600afc064"},
            },
        ),
        Project(
            project_id=create_project_id("reference_h3"),
            name="REFERENCE H3 (Relative Strength / Segment Rotation)",
            description=(
                "Relative strength / segment rotation (H3) hypothesis test: score "
                "autocorrelation (H3-A, primary) and reversal (H3-B, secondary) "
                "over 60-trading-day forward windows, 25 ETFs."
            ),
            lifecycle_state=ProjectLifecycleState.ARCHIVED,
            research_outcome="EVIDENCE AGAINST",
            origin_date=date(2026, 7, 19),
            repository_path="research_archive/reference_h3",
            metadata={
                "closeout_doc": "docs/REFERENCE_H3_RESEARCH_CLOSEOUT.md",
                "freeze": {
                    "construction_commit": "07f0da379d8cccf06d17c34a51cbb557da047fef",
                    "acceptance_commit": "a6439934882d5ad2c08ce8dba597810ac99e69f9",
                },
            },
        ),
    )


HISTORICAL_PROJECTS: tuple[Project, ...] = _historical_projects()


def backfill_historical_projects(registry: ProjectRegistry) -> None:
    """Register all three historical projects into `registry`. Raises
    `ValueError` (via `ProjectRegistry.register_project`) if any of them
    is already registered -- this function is not idempotent by design,
    matching `ProjectRegistry`'s own duplicate-id policy."""
    for project in HISTORICAL_PROJECTS:
        registry.register_project(project)
