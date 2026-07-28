"""Orchestration script for the `reference_h2` Research Proposal ->
Pre-validation transition. Follows the exact call shape
`experiments/run_reference_h4_lifecycle.py` established: plain
`advance_phase()` + direct `DecisionRecorder.append()`, for a transition
with no automated gate (no measured statistic vs. frozen threshold exists
yet -- that only arrives at Methodology Freeze / Validation). Records an
honest, disclosed Level 2 authorization rather than inventing a checklist
gate, matching AD-072's unconditional Level 2 floor for
(Research Proposal, Pre-validation).

This is cycle-execution tooling, not a research artifact. The
authorization basis is the fresh Level 2 PASS review at
`research_archive/reference_h2/reviewer_reports/2026-07-28_level2_review_head_201b8ae.md`,
which reviewed the proposal at commit `201b8ae` and found no drift between
that commit and the commit cited below as `commit_hash`.
"""

from __future__ import annotations

from pathlib import Path

from core.governance.decision_recorder import (
    AuthorizationRecord,
    DecisionRecord,
    DecisionRecorder,
)
from core.research.lifecycle import Authorization, advance_phase
from core.shared.lifecycle_phase import LifecyclePhase
from core.validation.gate_result import GateStatus

ARCHIVE_ROOT = Path("research_archive")
PROJECT_ID = "reference_h2"

AUTHORIZER = "Claude Sonnet 5 (session, this repo)"
REVIEWER_LEVEL_2 = "Level 2 (AI-assisted adversarial review)"


def record_transition(
    *,
    from_phase: LifecyclePhase,
    to_phase: LifecyclePhase,
    recorded_at: str,
    commit_hash: str,
    freeze_covered_paths: tuple[str, ...],
    evidence_refs: tuple[str, ...],
) -> DecisionRecord:
    """One `advance_phase()` + direct `DecisionRecorder.append()` call --
    no `Gate`/`GateRunner`/`compose_transition()` involved, since no
    automated gate exists for this transition. `freeze_verification_status`
    is fixed at `"not_applicable"`: nothing has been frozen yet (Methodology
    Freeze is two phases away)."""
    authorization = Authorization(
        reviewer_level=REVIEWER_LEVEL_2,
        authorizer=AUTHORIZER,
        ambiguity_acknowledged=False,
        override_acknowledged=False,
    )
    decision = advance_phase(from_phase, to_phase, GateStatus.PASS, authorization)

    recorder = DecisionRecorder(ARCHIVE_ROOT)
    return recorder.append(
        project_id=PROJECT_ID,
        from_phase=decision.from_phase.value,
        to_phase=decision.to_phase.value,
        recorded_at=recorded_at,
        commit_hash=commit_hash,
        freeze_commit_ref=commit_hash,
        freeze_verification_status="not_applicable",
        freeze_covered_paths=freeze_covered_paths,
        gate_outcomes=(),
        authorization=AuthorizationRecord(
            authorizer=decision.authorization.authorizer,
            reviewer_level=decision.authorization.reviewer_level,
            ambiguity_acknowledged=decision.authorization.ambiguity_acknowledged,
            override_acknowledged=decision.authorization.override_acknowledged,
        ),
        evidence_refs=evidence_refs,
        reproduction_record_ref=None,
    )
