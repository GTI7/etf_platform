from __future__ import annotations

import json

from core.governance.reproduction_environment import observe_reproduction_environment


def test_returns_exactly_the_three_observational_keys() -> None:
    assert set(observe_reproduction_environment().keys()) == {
        "python_version",
        "python_implementation",
        "platform",
    }


def test_all_values_are_non_empty_strings() -> None:
    for value in observe_reproduction_environment().values():
        assert isinstance(value, str)
        assert value != ""


def test_output_is_json_serializable() -> None:
    serialized = json.dumps(observe_reproduction_environment())
    assert json.loads(serialized) == observe_reproduction_environment()


def test_two_calls_in_the_same_process_return_identical_values() -> None:
    assert observe_reproduction_environment() == observe_reproduction_environment()
