"""Gate result record types (Validation domain, Step 7 minimal increment).

Formalizes the plain record shape docs/PLATFORM_ARCHITECTURE_V1.md
Section 4.2 sketches for ``GateResult`` -- "statistic values,
pass/fail/ambiguous against the frozen acceptance criteria, and
evidence references" -- as an actual contract, ahead of the full
``Gate``/``GateRunner``/``ValidationRegistry`` apparatus that section
also sketches. That apparatus (and ``LifecyclePhase``, workflow states,
and any historical ``GateResult`` backfill) is deliberately not built
here -- see docs/ARCHITECTURE_DECISIONS.md AD-040 and AD-044.

Three types only:

- ``GateStatus`` -- a three-way outcome, not a boolean. Same shape as
  ``core.governance.freeze_verifier.FreezeStatus`` and for the same
  reason: a gate can conclude PASS, conclude FAIL, or be unable to
  mechanically conclude either (``AMBIGUOUS``) -- categorically
  different outcomes, never collapsed into a boolean.
- ``DecisionMetadata`` -- attribution only: who is on record for this
  gate result, at what independence level
  (docs/RESEARCH_GOVERNANCE_STANDARD.md Section 4's Level 1/2/3), and
  when. It carries no explanation of *why* a status was reached --
  that belongs to ``GateResult.summary`` (AD-041), which a gate
  function generates mechanically from its own comparison, not a human
  judgment call being attributed to someone.
- ``GateResult`` -- the outcome itself: which gate, what status, why
  (``summary``), what evidence backs it (``evidence_refs``), and who
  is on record for it (``decision``).

See AD-042 for what ``evidence_refs`` does and does not mean.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GateStatus(str, Enum):
    """Three-way gate outcome -- deliberately not a boolean. AMBIGUOUS
    covers every case a gate cannot mechanically resolve to PASS or FAIL,
    including a missing frozen acceptance criterion or a freeze that
    failed verification (AD-043) -- not only a genuinely borderline
    statistic."""

    PASS = "pass"
    FAIL = "fail"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class DecisionMetadata:
    """Attribution for one gate result: who is on record for it, at what
    reviewer-independence level, and when. Plain fields, no validation
    beyond typing -- mirrors ``decision_log.md``'s own required fields
    (docs/RESEARCH_GOVERNANCE_STANDARD.md Section 5: "reviewer identity,
    and independence-level declaration")."""

    reviewer: str
    review_level: str
    decided_at: str


@dataclass(frozen=True, slots=True)
class GateResult:
    """Plain, serializable outcome of one gate evaluation.

    ``evidence_refs`` are references to immutable evidence locations
    only (AD-042) -- this record does not own, duplicate, or mutate
    what they point to."""

    gate_name: str
    status: GateStatus
    summary: str
    evidence_refs: tuple[str, ...]
    decision: DecisionMetadata

    @property
    def passed(self) -> bool:
        return self.status is GateStatus.PASS
