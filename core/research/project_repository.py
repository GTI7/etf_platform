"""Storage boundary for `Project` records (Migration Plan Step 5, item 4).

`ResearchProjectRepository` is the seam between `ProjectRegistry`'s
domain logic (duplicate-id checking, lookup semantics) and how project
records are actually stored. Only one implementation exists today --
`InMemoryResearchProjectRepository`, a plain dict, sufficient for tests
and for the historical backfill (Migration Plan Step 5, item 5). A
future YAML- or SQLite-backed implementation can be added beside it
later without `ProjectRegistry` changing at all; nothing about that
future need is designed or reserved here beyond this one seam --
consistent with "no abstraction ahead of need," this module commits to
exactly one concrete storage mechanism today.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.research.project import Project
from core.shared.ids import ProjectId


class ResearchProjectRepository(ABC):
    """Pure storage -- no duplicate-id policy, no validation. That logic
    belongs to `ProjectRegistry`, which is the only caller this interface
    is written for."""

    @abstractmethod
    def save(self, project: Project) -> None: ...

    @abstractmethod
    def get(self, project_id: ProjectId) -> Project | None: ...

    @abstractmethod
    def list_all(self) -> list[Project]: ...


class InMemoryResearchProjectRepository(ResearchProjectRepository):
    def __init__(self) -> None:
        self._projects: dict[ProjectId, Project] = {}

    def save(self, project: Project) -> None:
        self._projects[project.project_id] = project

    def get(self, project_id: ProjectId) -> Project | None:
        return self._projects.get(project_id)

    def list_all(self) -> list[Project]:
        return list(self._projects.values())
