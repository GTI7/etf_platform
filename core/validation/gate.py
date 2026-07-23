"""``Gate`` -- the pluggable-validation-stage protocol (Phase 4 / Step 9,
increment D -- docs/PLATFORM_ARCHITECTURE_V1.md Section 4.2's sketch,
formalized per docs/ARCHITECTURE_DECISIONS.md AD-049/AD-055).

Structural typing only (``typing.Protocol``); nothing here is a base
class, and nothing about ``GateRunner`` or the two existing gate
functions changes to satisfy it -- adapters implement it (see
``core.validation.gates.economic_rationale_adapter`` and
``core.validation.gates.signal_independence_adapter``).

``required_review_level`` is a plain ``str``, matching
``DecisionMetadata.review_level`` -- AD-055 rules out introducing a
``ReviewLevel`` enum. Its value is supplied by whoever constructs a
concrete ``Gate`` (see the adapters); this module does not assign or
default it, the same way neither existing gate function invents a
frozen threshold.
"""

from __future__ import annotations

from typing import Protocol

from core.validation.gate_context import GateContext
from core.validation.gate_result import GateResult


class Gate(Protocol):
    name: str
    required_review_level: str

    def run(self, context: GateContext) -> GateResult: ...
