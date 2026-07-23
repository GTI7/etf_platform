"""``GateContext`` -- the explicit input bundle a ``Gate`` is evaluated
against (Phase 4 / Step 9, increment D --
docs/PHASE_4_STEP9_ARCHITECTURE_RESOLUTION.md Section 4.2 row D;
docs/ARCHITECTURE_DECISIONS.md AD-049, AD-051, AD-052).

Defining constraint, inherited from ``docs/PLATFORM_ARCHITECTURE_V1.md``
Section 4.2: "a gate cannot reach outside what it was explicitly given."
``measurements`` and ``frozen_criteria`` are values only -- no callables,
no lazy handles, no database connection, no path to recompute. This is
what keeps AD-041 structurally true rather than merely conventional.

Both mappings are copied into a ``MappingProxyType`` in ``__post_init__``
so a mutable dict handed in by the caller is not hidden mutable state
reachable through this otherwise-frozen record (Step 9 Validation
Orchestration Proposal Section 6.3).

**AD-052: empty ``freeze_covered_paths`` is refused at construction.**
``core.governance.freeze_verifier.verify_freeze`` already treats zero
covered paths as ``UNVERIFIABLE``, but only after a caller has bothered
to call it. Refusing here means a ``GateRunner`` sequence can never even
be assembled against a vacuously "verified" bracket -- the empty-set hole
is closed one layer earlier than the freeze verifier itself closes it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Literal

from core.validation.gate_result import DecisionMetadata


@dataclass(frozen=True, slots=True)
class FrozenCriterion:
    """One gate's frozen acceptance criterion -- threshold plus
    direction, supplied by the caller and never invented here (same
    convention as both existing gate functions' own parameters)."""

    threshold: Decimal | None
    direction: Literal["at_least", "at_most"] | None


@dataclass(frozen=True, slots=True)
class GateContext:
    """Frozen, values-only input bundle for one gate or gate sequence.

    ``measurements`` and ``frozen_criteria`` are keyed by gate name --
    consuming adapters look up their own gate's entry, never another
    gate's."""

    measurements: Mapping[str, Decimal]
    frozen_criteria: Mapping[str, FrozenCriterion]
    freeze_commit_ref: str
    freeze_covered_paths: Sequence[Path | str]
    evidence_refs: Sequence[str]
    decision: DecisionMetadata
    measurement_provenance: str | None = None

    def __post_init__(self) -> None:
        covered_paths = tuple(str(p) for p in self.freeze_covered_paths)
        if not covered_paths:
            raise ValueError(
                "GateContext.freeze_covered_paths must not be empty -- a bracket over "
                "an empty covered-path set proves nothing and is refused at construction "
                "(AD-052), rather than left to be discovered only once verify_freeze runs."
            )
        object.__setattr__(self, "freeze_covered_paths", covered_paths)
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))
        object.__setattr__(self, "measurements", MappingProxyType(dict(self.measurements)))
        object.__setattr__(self, "frozen_criteria", MappingProxyType(dict(self.frozen_criteria)))
