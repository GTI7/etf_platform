"""Orchestration script for the `reference_h4` governed research cycle
(research_archive/reference_h4/decision_log.md documents each call's
result). This is cycle-execution tooling, not the frozen research
implementation itself -- `validate_h4_kurtosis.py` is the Phase 5
implementation artifact this script's Implementation->Validation call
freezes against.

Two call shapes, matching the plan approved for this cycle:

- `record_transition(...)` -- plain `advance_phase()` + direct
  `DecisionRecorder.append()`, for every transition with no automated
  gate. Records an honest, disclosed Level 1 self-review authorization
  and an empty `gate_outcomes` tuple rather than inventing a checklist
  gate.
- `record_gated_transition(...)` -- `compose_transition()`, used for
  exactly one transition (Validation -> Decision) where a real gate
  (measured statistic vs. frozen threshold) exists.

Each call in this file is run once, interactively, and its printed
`DecisionRecord` is what gets cited in `decision_log.md`'s anchor for the
next call (`expected_anchor=(sequence_number, hash_record(...))`). This
module intentionally has no `main()` / CLI -- it is imported and driven
one call at a time so each transition's evidence can be committed to git
before the next one runs.
"""

from __future__ import annotations

from pathlib import Path

from core.governance.decision_recorder import (
    AuthorizationRecord,
    DecisionRecord,
    DecisionRecorder,
    GateOutcome,
    hash_record,
)
from core.governance.freeze_verifier import VerificationResult, verify_freeze
from core.research.lifecycle import Authorization, advance_phase, compose_transition
from core.shared.lifecycle_phase import LifecyclePhase
from core.validation.gate_context import GateContext
from core.validation.gate_result import GateStatus
from core.validation.gate_run_record import GateRunRecord

ARCHIVE_ROOT = Path("research_archive")
PROJECT_ID = "reference_h4"

AUTHORIZER = "Claude Sonnet 5 (session, this repo)"
REVIEWER_LEVEL_1 = "Level 1 (self-review)"


def record_transition(
    *,
    from_phase: LifecyclePhase,
    to_phase: LifecyclePhase,
    recorded_at: str,
    commit_hash: str,
    freeze_verification_status: str,
    freeze_commit_ref: str,
    freeze_covered_paths: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    reproduction_record_ref: str | None = None,
) -> DecisionRecord:
    """One `advance_phase()` + direct `DecisionRecorder.append()` call --
    no `Gate`/`GateRunner` involved. `freeze_verification_status` is
    either `"not_applicable"` (phases 1-3, nothing frozen yet) or the
    `.status.value` of a *real* `verify_freeze()` call the caller already
    ran (phases 4 onward) -- this function never fabricates that value."""
    authorization = Authorization(
        reviewer_level=REVIEWER_LEVEL_1,
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
        freeze_commit_ref=freeze_commit_ref,
        freeze_verification_status=freeze_verification_status,
        freeze_covered_paths=freeze_covered_paths,
        gate_outcomes=(),
        authorization=AuthorizationRecord(
            authorizer=decision.authorization.authorizer,
            reviewer_level=decision.authorization.reviewer_level,
            ambiguity_acknowledged=decision.authorization.ambiguity_acknowledged,
            override_acknowledged=decision.authorization.override_acknowledged,
        ),
        evidence_refs=evidence_refs,
        reproduction_record_ref=reproduction_record_ref,
    )


def real_freeze_status(commit_ref: str, covered_paths: tuple[str, ...], repo_root: Path | None = None) -> VerificationResult:
    """Thin, honest wrapper: calls the real `verify_freeze()` and returns
    its result unmodified, so callers record `.status.value` -- never a
    string this script invents."""
    return verify_freeze(commit_ref, covered_paths, repo_root=repo_root)


def record_gated_transition(
    *,
    from_phase: LifecyclePhase,
    to_phase: LifecyclePhase,
    run_record: GateRunRecord,
    context: GateContext,
    recorded_at: str,
    commit_hash: str,
    expected_anchor: tuple[int, str] | None,
) -> DecisionRecord:
    """The single `compose_transition()` call this cycle uses (Validation
    -> Decision) -- the one transition with a real gate (a measured
    statistic vs. a frozen threshold), run through a real `GateRunner`
    against `run_record`/`context` built by the caller. Reviewer level is
    Level 1 for the run itself; a separate Level 2 adversarial pass is
    recorded as its own `reviewer_reports/*.md` file, not inside this
    call."""
    authorization = Authorization(
        reviewer_level=REVIEWER_LEVEL_1,
        authorizer=AUTHORIZER,
        ambiguity_acknowledged=False,
        override_acknowledged=False,
    )
    recorder = DecisionRecorder(ARCHIVE_ROOT)
    return compose_transition(
        recorder=recorder,
        project_id=PROJECT_ID,
        from_phase=from_phase,
        to_phase=to_phase,
        required_gate_names=("economic_rationale",),
        run_record=run_record,
        context=context,
        authorization=authorization,
        recorded_at=recorded_at,
        commit_hash=commit_hash,
        expected_anchor=expected_anchor,
    )


def anchor_for(record: DecisionRecord) -> tuple[int, str]:
    """The `(sequence_number, head_hash)` anchor the *next* transition
    must cite, computed from the row `hash_record()` actually hashes --
    matches what a human would read out of `decision_log.md` by hand."""
    import dataclasses

    row = dataclasses.asdict(record)
    return record.sequence_number, hash_record(row)
