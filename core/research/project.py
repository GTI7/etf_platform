"""Canonical research-project identity and metadata (Migration Plan Step 5).

`Project` gives every research cycle -- past or future -- one stable
record other domains can reference by `ProjectId` instead of a
filesystem path or a document title. This module owns identity and
metadata only; it does not verify anything (Governance's job), run
anything (Validation's job), or narrate anything (Reporting's job) --
see `docs/PLATFORM_ARCHITECTURE_V1.md` Section 4.1's own "explicitly out
of scope" list, which this module deliberately does not cross.

**Two independent axes, not one.** `lifecycle_state` and
`research_outcome` answer different questions and must not be
collapsed into a single field:

- `lifecycle_state` -- where the project *is* in the governance process
  (`ACTIVE` / `FROZEN` / `ARCHIVED`). Structural, closed vocabulary,
  controlled by this registry.
- `research_outcome` -- what the project *found*, once it has one.
  Free text, deliberately not an enum: the real vocabulary across the
  three historical cycles is not a single closed set --
  `docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md` and
  `docs/REFERENCE_V2_H1_RESEARCH_CLOSEOUT.md` both record `"ARCHIVE"`,
  while `docs/REFERENCE_H3_RESEARCH_CLOSEOUT.md` records
  `"EVIDENCE AGAINST"` (a `docs/RESEARCH_GOVERNANCE_STANDARD.md` Section
  7 FAIL-discipline classification, not the same taxonomy as the other
  two's three-category archive framework). Forcing these into one enum
  now would mean guessing at a taxonomy broader research history hasn't
  actually settled on yet -- exactly the "abstraction ahead of a second
  concrete need" this repository's discipline avoids. `None` for a
  project with no concluded outcome yet (e.g. still `ACTIVE`).

`origin_date` intentionally does not claim to be "when the project
started" -- for the three historical backfill entries, no such date is
recorded anywhere in the repository, and inventing one would be a
governance violation of the same kind
`docs/RESEARCH_PLATFORM_RETROSPECTIVE.md` catalogs (facts recorded
retroactively, without disclosure, are exactly what this platform's
governance discipline exists to prevent). It instead names the earliest
*already-recorded* evidence date for that project -- see
`core/research/historical_backfill.py` for what each of the three uses
and why.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from core.shared.ids import ProjectId


class ProjectLifecycleState(str, Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class Project:
    """Plain, serializable research-project record."""

    project_id: ProjectId
    name: str
    description: str
    lifecycle_state: ProjectLifecycleState
    research_outcome: str | None
    origin_date: date
    repository_path: str
    metadata: dict[str, object] = field(default_factory=dict)
