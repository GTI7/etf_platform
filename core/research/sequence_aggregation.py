"""Pure aggregation of a gate sequence's per-gate ``GateStatus`` values
into one ``sequence_status`` (Phase 4 / Step 9, increment E --
docs/ARCHITECTURE_DECISIONS.md AD-059 step 5; AD-049 part 3 assigns
cycle-level aggregation to Research **by name**, never to Validation, so
this lives in ``core/research/`` and nowhere else).

Pure function, by construction: it takes ``GateStatus`` values only and
does no IO, no git, no clock read, no mutation. Same inputs, same output,
every time.

**A crash never reaches here (AD-056).** A crashed
``GateExecutionOutcome`` carries an ``error`` string, not a
``GateStatus``; it is refused one layer up in
``core.research.lifecycle.compose_transition`` *before* aggregation, so
this function only ever sees admitted, mechanically-concluded statuses.
It cannot coerce a crash into a verdict because a crash is not a value it
accepts.

**No vacuous PASS (AD-047 / AD-051 discipline).** An empty sequence has
no aggregate and is **refused**, not silently returned as ``PASS`` -- a
vacuous PASS over zero gates would record a claim stronger than the
(absent) evidence, exactly the empty-set hole the freeze verifier refuses
for zero covered paths. Completeness is enforced upstream (AD-059 step
1), so an empty sequence never legitimately reaches this function either.
"""

from __future__ import annotations

from collections.abc import Sequence

from core.validation.gate_result import GateStatus


class EmptyGateSequence(ValueError):
    """Raised when there are no statuses to aggregate. An empty sequence
    has no aggregate; returning a vacuous ``PASS`` is refused."""


def aggregate_sequence_status(statuses: Sequence[GateStatus]) -> GateStatus:
    """Aggregate ``statuses`` into one ``GateStatus``:

    - ``PASS`` iff **every** gate passed;
    - ``FAIL`` if **any** gate failed -- **FAIL dominates AMBIGUOUS**;
    - ``AMBIGUOUS`` otherwise (at least one AMBIGUOUS, no FAIL).

    Refuses an empty input (``EmptyGateSequence``) and any non-``GateStatus``
    element (``TypeError``) rather than guessing an aggregate.
    """
    if not statuses:
        raise EmptyGateSequence(
            "cannot aggregate an empty gate sequence -- an empty sequence has no "
            "aggregate status, and a vacuous PASS over zero gates would record a "
            "claim stronger than the evidence (refused, mirroring the empty "
            "covered-path refusal of AD-047/AD-051)"
        )
    for status in statuses:
        if not isinstance(status, GateStatus):
            raise TypeError(
                f"aggregate_sequence_status accepts GateStatus values only; got "
                f"{type(status).__name__} -- a crashed outcome is refused before "
                "aggregation (AD-056), never coerced into a status here"
            )

    if any(status is GateStatus.FAIL for status in statuses):
        return GateStatus.FAIL
    if all(status is GateStatus.PASS for status in statuses):
        return GateStatus.PASS
    return GateStatus.AMBIGUOUS
