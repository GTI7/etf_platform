"""Economic-rationale gate (Validation domain, Step 7 minimal increment).

Evaluates an already-computed statistic (e.g. mean IC, top/bottom
spread -- whatever ``core.statistics`` produced) against a
caller-supplied frozen acceptance criterion. Computes nothing itself
(AD-041): unlike the H3 Phase 6 economic-validation script this gate
formalizes the contract for
(``experiments/validate_h3_phase6_economic_validation.py``, which both
computes its statistics via ``core.statistics``-equivalent helpers
*and* renders a verdict in one script), this function only does the
second half. Statistic computation stays entirely in
``core.statistics``; this module does not import it.

Calls ``core.governance.freeze_verifier.verify_freeze`` before any
comparison, same as ``signal_independence`` and for the same reason
(docs/PLATFORM_ARCHITECTURE_V1.md Section 4.2). A failed verification
or a missing frozen threshold both yield ``GateStatus.AMBIGUOUS`` per
AD-043 -- a governance-provenance failure, never a threshold this
function invents to force a PASS/FAIL.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path
from typing import Literal

from core.governance.freeze_verifier import FreezeStatus, verify_freeze
from core.validation.gate_result import DecisionMetadata, GateResult, GateStatus

GATE_NAME = "economic_rationale"


def evaluate_economic_rationale_gate(
    *,
    statistic_name: str,
    measured_value: Decimal,
    frozen_threshold: Decimal | None,
    threshold_direction: Literal["at_least", "at_most"] | None,
    freeze_commit_ref: str,
    freeze_covered_paths: Iterable[Path | str],
    evidence_refs: Iterable[str],
    decision: DecisionMetadata,
    repo_root: Path | None = None,
) -> GateResult:
    """Evaluate `measured_value` for `statistic_name` (already computed
    by Statistics) against `frozen_threshold`/`threshold_direction` (the
    frozen criterion, supplied by the caller -- never invented here),
    gated on `freeze_commit_ref`/`freeze_covered_paths` verifying clean.

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
        measured_value >= frozen_threshold
        if threshold_direction == "at_least"
        else measured_value <= frozen_threshold
    )
    comparator = ">=" if threshold_direction == "at_least" else "<="
    return GateResult(
        gate_name=GATE_NAME,
        status=GateStatus.PASS if meets_criterion else GateStatus.FAIL,
        summary=(
            f"{statistic_name}={measured_value} {comparator} frozen_threshold={frozen_threshold}: "
            f"{'meets' if meets_criterion else 'does not meet'} the frozen acceptance criterion."
        ),
        evidence_refs=tuple(evidence_refs),
        decision=decision,
    )
