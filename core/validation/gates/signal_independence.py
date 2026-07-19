"""Signal-independence gate (Validation domain, Step 7 minimal increment).

Evaluates an already-computed overlap/correlation statistic against a
caller-supplied frozen acceptance criterion. Computes nothing itself
(AD-041): ``measured_overlap`` must already be produced by
``core.statistics`` (or, today, one of the ``experiments/validate_*.py``
scripts computing it the same way) before this function is called.

**The missing-criterion case this gate exists to handle correctly.**
``experiments/validate_h3_gate1_independence.py`` -- the platform's one
real signal-independence check to date -- documents that no mechanical
PASS/FAIL threshold was ever frozen for this check: "No PASS/FAIL
determination is written by this script... Section 4 requires
independent reviewer confirmation before Gate 1 counts as satisfied."
Per AD-043, this function treats that as a governance-provenance
failure, not a statistical judgment call: ``frozen_threshold=None``
yields ``GateStatus.AMBIGUOUS`` with the fixed rationale "Acceptance
criterion was not frozen before validation." -- never a threshold this
function invents on the spot.

Calls ``core.governance.freeze_verifier.verify_freeze`` before any
comparison, per docs/PLATFORM_ARCHITECTURE_V1.md Section 4.2: "a gate
can never execute against an unverified or drifted freeze." A failed
verification is likewise ``AMBIGUOUS``, not ``FAIL`` -- the freeze
being untrustworthy says nothing about whether the underlying signals
are independent; it only means this gate cannot mechanically decide.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path
from typing import Literal

from core.governance.freeze_verifier import FreezeStatus, verify_freeze
from core.validation.gate_result import DecisionMetadata, GateResult, GateStatus

GATE_NAME = "signal_independence"


def evaluate_signal_independence_gate(
    *,
    measured_overlap: Decimal,
    frozen_threshold: Decimal | None,
    threshold_direction: Literal["at_least", "at_most"] | None,
    freeze_commit_ref: str,
    freeze_covered_paths: Iterable[Path | str],
    evidence_refs: Iterable[str],
    decision: DecisionMetadata,
    repo_root: Path | None = None,
) -> GateResult:
    """Evaluate `measured_overlap` (already computed by Statistics)
    against `frozen_threshold`/`threshold_direction` (the frozen
    criterion, supplied by the caller -- never invented here), gated on
    `freeze_commit_ref`/`freeze_covered_paths` verifying clean.

    `evidence_refs` are passed straight through, unmodified, into the
    returned `GateResult` -- see AD-042."""
    verification = verify_freeze(freeze_commit_ref, freeze_covered_paths, repo_root=repo_root)
    if verification.status is not FreezeStatus.VERIFIED:
        return GateResult(
            gate_name=GATE_NAME,
            status=GateStatus.AMBIGUOUS,
            summary=(
                f"Freeze verification did not succeed (status={verification.status.value}); "
                "gate cannot evaluate against an unverified or drifted basis."
            ),
            evidence_refs=tuple(evidence_refs),
            decision=decision,
        )

    if frozen_threshold is None or threshold_direction is None:
        return GateResult(
            gate_name=GATE_NAME,
            status=GateStatus.AMBIGUOUS,
            summary="Acceptance criterion was not frozen before validation.",
            evidence_refs=tuple(evidence_refs),
            decision=decision,
        )

    meets_criterion = (
        measured_overlap >= frozen_threshold
        if threshold_direction == "at_least"
        else measured_overlap <= frozen_threshold
    )
    comparator = ">=" if threshold_direction == "at_least" else "<="
    return GateResult(
        gate_name=GATE_NAME,
        status=GateStatus.PASS if meets_criterion else GateStatus.FAIL,
        summary=(
            f"measured_overlap={measured_overlap} {comparator} frozen_threshold={frozen_threshold}: "
            f"{'meets' if meets_criterion else 'does not meet'} the frozen acceptance criterion."
        ),
        evidence_refs=tuple(evidence_refs),
        decision=decision,
    )
