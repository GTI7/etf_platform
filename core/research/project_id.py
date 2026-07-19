"""Validated construction for `core.shared.ids.ProjectId`.

`ProjectId` itself is not redefined here -- it remains the plain
``NewType("ProjectId", str)`` reserved in ``core/shared/ids.py`` (AD-031),
per AD-003's cross-cutting rule against wrapper classes for typed IDs.
This module supplies the one thing a bare `NewType` cannot: a
construction-time format gate, so a `ProjectId` is never built from an
arbitrary, unvalidated string by convention alone -- the same role
`serialize_parameters()` plays for `IndicatorDefinition.parameters`
(AD-020).

Callers should construct every `ProjectId` through `create_project_id`,
never `ProjectId("...")` directly.
"""

from __future__ import annotations

import re

from core.shared.ids import ProjectId

_PROJECT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def create_project_id(raw: str) -> ProjectId:
    """Validate and wrap `raw` as a `ProjectId`.

    Format: lowercase ASCII letters, digits, and underscores only, must
    start with a letter (`^[a-z][a-z0-9_]*$`) -- matches every existing
    `research_archive/` directory name (`reference_v1`, `reference_v2_h1`,
    `reference_h3`) with no exceptions carved out for any of them.
    Raises `ValueError` on anything else.
    """
    if not _PROJECT_ID_PATTERN.match(raw):
        raise ValueError(
            f"invalid project id {raw!r}: must match {_PROJECT_ID_PATTERN.pattern!r} "
            "(lowercase letters, digits, underscores; must start with a letter)"
        )
    return ProjectId(raw)
