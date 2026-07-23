from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from core.research.project import ProjectLifecycleState
from core.research.project_id import create_project_id
from core.research.project_registry import ProjectRegistry
from core.research.project_repository import InMemoryResearchProjectRepository
from core.research.reference_h4_registration import (
    REFERENCE_H4_PROJECT,
    register_reference_h4,
)


@pytest.fixture
def registry() -> ProjectRegistry:
    return ProjectRegistry(InMemoryResearchProjectRepository())


def test_reference_h4_project_id_matches_ad_050_a6_c4() -> None:
    assert REFERENCE_H4_PROJECT.project_id == create_project_id("reference_h4")


def test_reference_h4_project_is_active_with_no_recorded_outcome() -> None:
    assert REFERENCE_H4_PROJECT.lifecycle_state is ProjectLifecycleState.ACTIVE
    assert REFERENCE_H4_PROJECT.research_outcome is None


def test_reference_h4_repository_path_matches_project_id() -> None:
    assert REFERENCE_H4_PROJECT.repository_path == "research_archive/reference_h4"


def test_register_reference_h4_adds_it_to_the_registry(registry: ProjectRegistry) -> None:
    register_reference_h4(registry)

    assert registry.get_project(create_project_id("reference_h4")) == REFERENCE_H4_PROJECT


def test_register_reference_h4_twice_raises_value_error(registry: ProjectRegistry) -> None:
    register_reference_h4(registry)

    with pytest.raises(ValueError):
        register_reference_h4(registry)


def test_registering_reference_h4_does_not_disturb_historical_backfill(registry: ProjectRegistry) -> None:
    from core.research.historical_backfill import backfill_historical_projects

    backfill_historical_projects(registry)
    register_reference_h4(registry)

    listed = {p.project_id for p in registry.list_projects()}
    assert listed == {"reference_v1", "reference_v2_h1", "reference_h3", "reference_h4"}


def test_reference_h4_origin_date_matches_its_archive_manifest_created_at() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    manifest_path = repo_root / "research_archive" / "reference_h4" / "archive_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    created_at_date = date.fromisoformat(manifest["created_at"][:10])
    assert REFERENCE_H4_PROJECT.origin_date == created_at_date


def test_reference_h4_archive_manifest_matches_schema_v1() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    manifest_path = repo_root / "research_archive" / "reference_h4" / "archive_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == 1
    assert manifest["project_id"] == "reference_h4"
    assert manifest["lifecycle_version"] == "v1"


def test_reference_h4_archive_has_no_evidence_subdirectories_scaffolded() -> None:
    """Manifest creation was identity registration only, not evidence
    initialization -- no `scaffold_project_archive()` call was made for
    this cycle, so none of Standard Section 5's evidence subdirectories
    exist yet."""
    repo_root = Path(__file__).resolve().parent.parent
    archive_dir = repo_root / "research_archive" / "reference_h4"

    for subdirectory in ("dataset_hashes", "experiment_results", "reviewer_reports"):
        assert not (archive_dir / subdirectory).exists()
