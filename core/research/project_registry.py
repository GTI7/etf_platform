"""`ProjectRegistry` -- identity and metadata ownership only (Migration
Plan Step 5, item 3).

Gives every research project a single place other domains can resolve a
`ProjectId` against. Deliberately narrower than
`docs/PLATFORM_ARCHITECTURE_V1.md` Section 4.1's own `ProjectRegistry`
Protocol sketch -- see `docs/ARCHITECTURE_DECISIONS.md` AD-036 for the
divergence and why it is temporary, not final.

**Responsibilities, and only these:** register a project, retrieve one
by id, list all of them, and refuse a duplicate id. Same shape as
`ProviderRegistry` (`core/market_data`, AD-015): an explicit,
dict-backed registry, duplicate registration raises `ValueError`, an
unknown id raises `KeyError`, no auto-discovery.

**Explicitly not this module's job** (all deferred, none stubbed here):
git operations, freeze verification (Governance's `FreezeVerifier`),
experiment execution, dataset validation, and lifecycle *transitions*
(`advance_phase`-shaped behavior) -- a project's `lifecycle_state` is
set at construction by the caller, this registry never mutates it.
"""

from __future__ import annotations

from core.research.project import Project
from core.research.project_repository import ResearchProjectRepository
from core.shared.ids import ProjectId


class ProjectRegistry:
    def __init__(self, repository: ResearchProjectRepository) -> None:
        self._repository = repository

    def register_project(self, project: Project) -> None:
        if self._repository.get(project.project_id) is not None:
            raise ValueError(f"project {project.project_id!r} is already registered")
        self._repository.save(project)

    def get_project(self, project_id: ProjectId) -> Project:
        project = self._repository.get(project_id)
        if project is None:
            raise KeyError(project_id)
        return project

    def list_projects(self) -> list[Project]:
        return self._repository.list_all()
