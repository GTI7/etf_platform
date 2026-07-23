"""`LifecyclePhase` -- the eight research-lifecycle phases named in
`docs/RESEARCH_GOVERNANCE_STANDARD.md` Section 2, transcribed exactly
and pinned by `tests/test_lifecycle_phase.py`.

This is vocabulary, not behavior: a closed `str` enum with no methods
and no transition logic, the same profile as `ProjectId` in
`core/shared/ids.py`. It belongs in the shared kernel because Research,
Validation, and Governance all need to reference the same eight phases
without any of them owning the vocabulary (see
`docs/ARCHITECTURE_DECISIONS.md` AD-050).

`LifecyclePhase` is not `core.research.project.ProjectLifecycleState`.
ACTIVE / FROZEN / ARCHIVED is a storage posture; the eight phases below
are the research process itself -- two orthogonal axes, not one.
"""

from __future__ import annotations

from enum import Enum


class LifecyclePhase(str, Enum):
    HYPOTHESIS = "Hypothesis"
    RESEARCH_PROPOSAL = "Research Proposal"
    PRE_VALIDATION = "Pre-validation"
    METHODOLOGY_FREEZE = "Methodology Freeze"
    IMPLEMENTATION = "Implementation"
    VALIDATION = "Validation"
    DECISION = "Decision"
    ARCHIVE = "Archive"
