from __future__ import annotations

from datetime import date

import pytest

from core.research.historical_backfill import HISTORICAL_PROJECTS, backfill_historical_projects
from core.research.project import Project, ProjectLifecycleState
from core.research.project_id import create_project_id
from core.research.project_registry import ProjectRegistry
from core.research.project_repository import InMemoryResearchProjectRepository


def _make_project(project_id: str = "h4", **overrides: object) -> Project:
    defaults: dict[str, object] = dict(
        project_id=create_project_id(project_id),
        name="H4",
        description="A hypothetical fourth research cycle.",
        lifecycle_state=ProjectLifecycleState.ACTIVE,
        research_outcome=None,
        origin_date=date(2026, 7, 20),
        repository_path=f"research_archive/{project_id}",
        metadata={},
    )
    defaults.update(overrides)
    return Project(**defaults)  # type: ignore[arg-type]


@pytest.fixture
def registry() -> ProjectRegistry:
    return ProjectRegistry(InMemoryResearchProjectRepository())


def test_register_and_retrieve_a_project(registry: ProjectRegistry) -> None:
    project = _make_project()

    registry.register_project(project)

    assert registry.get_project(project.project_id) == project


def test_retrieving_an_unregistered_project_raises_key_error(registry: ProjectRegistry) -> None:
    with pytest.raises(KeyError):
        registry.get_project(create_project_id("nonexistent"))


def test_registering_a_duplicate_id_raises_value_error(registry: ProjectRegistry) -> None:
    registry.register_project(_make_project())

    with pytest.raises(ValueError):
        registry.register_project(_make_project())


def test_registering_a_duplicate_id_does_not_overwrite_the_original(registry: ProjectRegistry) -> None:
    original = _make_project(name="original")
    registry.register_project(original)

    with pytest.raises(ValueError):
        registry.register_project(_make_project(name="replacement"))

    assert registry.get_project(original.project_id).name == "original"


def test_list_projects_returns_every_registered_project(registry: ProjectRegistry) -> None:
    first = _make_project("h4")
    second = _make_project("h5")
    registry.register_project(first)
    registry.register_project(second)

    listed = registry.list_projects()

    assert {p.project_id for p in listed} == {first.project_id, second.project_id}


def test_list_projects_on_empty_registry_returns_empty_list(registry: ProjectRegistry) -> None:
    assert registry.list_projects() == []


def test_in_memory_repository_get_returns_none_for_unknown_id() -> None:
    repo = InMemoryResearchProjectRepository()

    assert repo.get(create_project_id("nonexistent")) is None


# --- Historical backfill -----------------------------------------------------


def test_historical_projects_constant_has_exactly_three_entries() -> None:
    assert len(HISTORICAL_PROJECTS) == 3
    assert {p.project_id for p in HISTORICAL_PROJECTS} == {
        "reference_v1",
        "reference_v2_h1",
        "reference_h3",
    }


def test_backfill_registers_all_three_historical_projects(registry: ProjectRegistry) -> None:
    backfill_historical_projects(registry)

    listed = registry.list_projects()
    assert len(listed) == 3
    assert {p.project_id for p in listed} == {
        "reference_v1",
        "reference_v2_h1",
        "reference_h3",
    }


def test_backfilled_projects_are_all_archived_with_a_recorded_outcome(registry: ProjectRegistry) -> None:
    backfill_historical_projects(registry)

    for project in registry.list_projects():
        assert project.lifecycle_state is ProjectLifecycleState.ARCHIVED
        assert project.research_outcome is not None


def test_backfilled_h3_metadata_records_both_freeze_commits(registry: ProjectRegistry) -> None:
    backfill_historical_projects(registry)

    h3 = registry.get_project(create_project_id("reference_h3"))

    freeze = h3.metadata["freeze"]
    assert freeze["construction_commit"] == "07f0da379d8cccf06d17c34a51cbb557da047fef"
    assert freeze["acceptance_commit"] == "a6439934882d5ad2c08ce8dba597810ac99e69f9"


def test_backfilled_v1_metadata_records_its_single_freeze_commit(registry: ProjectRegistry) -> None:
    backfill_historical_projects(registry)

    v1 = registry.get_project(create_project_id("reference_v1"))

    assert v1.metadata["freeze"]["commit"] == "19771d4fd93d95b223c6aff603fdaf8f31f28038"
    assert v1.metadata["closeout_doc"] == "docs/REFERENCE_V1_RESEARCH_CLOSEOUT.md"


def test_backfill_is_not_idempotent_a_second_call_raises(registry: ProjectRegistry) -> None:
    backfill_historical_projects(registry)

    with pytest.raises(ValueError):
        backfill_historical_projects(registry)
