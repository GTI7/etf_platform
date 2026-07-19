from __future__ import annotations

import pytest

from core.research.project_id import create_project_id
from core.shared.ids import ProjectId


@pytest.mark.parametrize(
    "raw",
    [
        "reference_v1",
        "reference_v2_h1",
        "reference_h3",
        "h4",
        "h3_reference_validation",
        "a",
    ],
)
def test_valid_ids_are_accepted(raw: str) -> None:
    project_id = create_project_id(raw)

    assert project_id == raw
    assert isinstance(project_id, str)


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "H3",
        "Reference_V1",
        "3h",
        "reference-v1",
        "reference v1",
        "reference.v1",
        "_reference_v1",
        "référence",
    ],
)
def test_invalid_ids_are_rejected(raw: str) -> None:
    with pytest.raises(ValueError):
        create_project_id(raw)


def test_equal_ids_compare_equal_and_hash_equal() -> None:
    first = create_project_id("reference_h3")
    second = create_project_id("reference_h3")

    assert first == second
    assert hash(first) == hash(second)


def test_different_ids_compare_unequal() -> None:
    first = create_project_id("reference_v1")
    second = create_project_id("reference_v2_h1")

    assert first != second


def test_project_id_usable_as_a_dict_key() -> None:
    mapping = {create_project_id("reference_h3"): "value"}

    assert mapping[ProjectId("reference_h3")] == "value"
