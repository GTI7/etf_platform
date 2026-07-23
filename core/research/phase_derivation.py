"""Derivation of a research cycle's current phase from its governance
transition chain (Phase 4 / Step 9, increment E --
docs/ARCHITECTURE_DECISIONS.md AD-058; AD-050 part 3 and Resolution D-14:
current phase is **derived** from the transition-record chain, never
stored on ``Project`` -- ``Project`` is unmodified and no INV-12
exception is created).

**UNKNOWN is a derived-state sentinel, not a ninth ``LifecyclePhase``.**
``core/shared/lifecycle_phase.py`` stays exactly the eight phases
transcribed from ``RESEARCH_GOVERNANCE_STANDARD.md`` Section 2 and pinned
by test; adding ``UNKNOWN`` to that enum would corrupt the transcription
invariant. ``UNKNOWN`` therefore lives here, outside the phase
vocabulary, as a typed single-member sentinel -- distinct from every
``LifecyclePhase`` and from ``None`` so an UNKNOWN derivation can never
be mistaken for a phase or for a value someone forgot to pass.

**An empty chain derives UNKNOWN, never Hypothesis (AD-058).** For a
cycle with no recorded transition, ``UNKNOWN`` is the *true* answer:
registration asserts nothing about phase (AD-050 A6-C5), and defaulting
to ``Hypothesis`` (or any phase) would over-claim. The failure direction
is safe -- a damaged or truncated chain regresses toward ``UNKNOWN``,
which under-claims, rather than asserting a phase the chain cannot prove.

Read-only over an already-read chain: this module does no IO. The caller
reads the chain (``core.governance.decision_recorder.read_chain``) and
passes the records in.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum

from core.governance.decision_recorder import DecisionRecord
from core.shared.lifecycle_phase import LifecyclePhase


class DerivedPhaseUnknown(Enum):
    """Single-member typed sentinel meaning 'the chain does not determine
    a phase'. Its own type, so ``x is UNKNOWN_PHASE`` is unambiguous and
    it can never collide with a ``LifecyclePhase`` member or with
    ``None``."""

    UNKNOWN = "unknown"


UNKNOWN_PHASE = DerivedPhaseUnknown.UNKNOWN

# A derived current phase is either one of the eight real phases, or the
# explicit UNKNOWN sentinel -- never a silent default.
DerivedPhase = LifecyclePhase | DerivedPhaseUnknown


def derive_current_phase(chain: Sequence[DecisionRecord]) -> DerivedPhase:
    """Derive the current phase from ``chain``:

    - an **empty** chain derives ``UNKNOWN_PHASE`` (AD-058);
    - otherwise, the current phase is the ``to_phase`` of the **last**
      record, mapped back onto ``LifecyclePhase``.

    Raises ``ValueError`` (from ``LifecyclePhase``) if the last record's
    stored ``to_phase`` string is not one of the eight phases -- a
    corrupted record is surfaced, never normalized away.
    """
    if not chain:
        return UNKNOWN_PHASE
    return LifecyclePhase(chain[-1].to_phase)
