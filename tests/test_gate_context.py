from __future__ import annotations

from decimal import Decimal
from types import MappingProxyType

import pytest

from core.validation.gate_context import FrozenCriterion, GateContext
from core.validation.gate_result import DecisionMetadata


def _decision() -> DecisionMetadata:
    return DecisionMetadata(reviewer="test-reviewer", review_level="Level 2", decided_at="2026-07-24")


def test_empty_freeze_covered_paths_is_rejected() -> None:
    """AD-052: a bracket over an empty covered-path set proves nothing --
    GateContext refuses to be constructed with one at all, rather than
    silently producing a vacuously VERIFIED bracket later."""
    with pytest.raises(ValueError):
        GateContext(
            measurements={},
            frozen_criteria={},
            freeze_commit_ref="deadbeef",
            freeze_covered_paths=[],
            evidence_refs=(),
            decision=_decision(),
        )


def test_non_empty_freeze_covered_paths_is_accepted() -> None:
    context = GateContext(
        measurements={"economic_rationale": Decimal("0.05")},
        frozen_criteria={"economic_rationale": FrozenCriterion(threshold=Decimal("0.03"), direction="at_least")},
        freeze_commit_ref="deadbeef",
        freeze_covered_paths=["acceptance_criteria.md"],
        evidence_refs=("ref-1",),
        decision=_decision(),
    )

    assert context.freeze_covered_paths == ("acceptance_criteria.md",)
    assert context.evidence_refs == ("ref-1",)


def test_measurements_and_frozen_criteria_are_effectively_immutable() -> None:
    """A mutable dict handed to a GateContext must not remain hidden
    mutable state -- §6.3: 'a mutable dict handed to a runner is hidden
    state by another name.'"""
    measurements = {"economic_rationale": Decimal("0.05")}
    context = GateContext(
        measurements=measurements,
        frozen_criteria={},
        freeze_commit_ref="deadbeef",
        freeze_covered_paths=["acceptance_criteria.md"],
        evidence_refs=(),
        decision=_decision(),
    )

    assert isinstance(context.measurements, MappingProxyType)
    measurements["economic_rationale"] = Decimal("999")
    assert context.measurements["economic_rationale"] == Decimal("0.05")

    with pytest.raises(TypeError):
        context.measurements["economic_rationale"] = Decimal("1")  # type: ignore[index]


def test_measurement_provenance_defaults_to_none() -> None:
    context = GateContext(
        measurements={},
        frozen_criteria={},
        freeze_commit_ref="deadbeef",
        freeze_covered_paths=["acceptance_criteria.md"],
        evidence_refs=(),
        decision=_decision(),
    )

    assert context.measurement_provenance is None
