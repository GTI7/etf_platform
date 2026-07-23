"""Tests for core/research/lifecycle.py compose_transition() -- the sole
Validation + Governance composition boundary (Phase 4 / Step 9, increment
E; AD-056/AD-057/AD-058/AD-059).

These tests build GateRunRecords two ways:

- **hand-built**, with explicit VerificationResult/GateExecutionOutcome
  values, for the refusal paths (crash, bracket, freeze projection) --
  including deliberately *inconsistent* records that a real GateRunner
  would never emit, precisely to prove the composition's own independent
  guards fire rather than trusting an upstream flag; and
- **runner-built**, from a real GateRunner over a real git repo, for the
  H4 end-to-end path, so the full Validation -> Governance pipeline is
  exercised genuinely.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.governance.decision_recorder import (
    DecisionRecorder,
    TRANSITION_RECORDS_FILENAME,
    hash_record,
    read_chain,
)
from core.governance.canonical_jsonl import read_canonical_jsonl
from core.governance.freeze_verifier import FreezeStatus, VerificationResult
from core.research.lifecycle import (
    Authorization,
    BracketInvalidated,
    ChainNotAnchored,
    ContextRunRecordMismatch,
    CrashedGateInSequence,
    FreezeNotVerified,
    IncompleteGateSequence,
    PhaseChainMismatch,
    UnanchoredTransition,
    compose_transition,
)
from core.shared.clock import FixedClock
from core.shared.lifecycle_phase import LifecyclePhase
from core.validation.gate_context import GateContext
from core.validation.gate_result import DecisionMetadata, GateResult, GateStatus
from core.validation.gate_run_record import GateExecutionOutcome, GateRunRecord
from core.validation.gate_runner import GateRunner

FREEZE_REF = "f" * 40
RESOLVED = "a" * 40
COVERED = ("docs/acceptance_criteria.md",)


# --- fixtures / builders -------------------------------------------------


def _decision() -> DecisionMetadata:
    return DecisionMetadata(reviewer="r.reviewer", review_level="2", decided_at="2026-07-24")


def _authorization(**overrides: object) -> Authorization:
    kwargs: dict[str, object] = dict(
        reviewer_level="Level 2",
        authorizer="a.reviewer",
        ambiguity_acknowledged=False,
        override_acknowledged=False,
    )
    kwargs.update(overrides)
    return Authorization(**kwargs)  # type: ignore[arg-type]


def _verification(
    *,
    commit_ref: str = FREEZE_REF,
    resolved: str | None = RESOLVED,
    status: FreezeStatus = FreezeStatus.VERIFIED,
    covered: tuple[str, ...] = COVERED,
) -> VerificationResult:
    return VerificationResult(
        commit_ref=commit_ref,
        resolved_hash=resolved,
        status=status,
        drifted_files=(),
        errors=(),
        covered_paths=covered,
    )


def _result(name: str, status: GateStatus = GateStatus.PASS, evidence_refs: tuple[str, ...] = ()) -> GateResult:
    return GateResult(
        gate_name=name, status=status, summary=f"{name} ran", evidence_refs=evidence_refs, decision=_decision()
    )


def _outcome(
    name: str,
    status: GateStatus = GateStatus.PASS,
    evidence_refs: tuple[str, ...] = (),
    *,
    error: str | None = None,
) -> GateExecutionOutcome:
    if error is not None:
        return GateExecutionOutcome(gate_name=name, result=None, error=error)
    return GateExecutionOutcome(gate_name=name, result=_result(name, status, evidence_refs), error=None)


def _run_record(
    outcomes: list[GateExecutionOutcome],
    *,
    pre: VerificationResult | None = None,
    post: VerificationResult | None = None,
    bracket_invalidated: bool = False,
    provenance: str | None = "research_archive/reference_h4/reproduction_record.json",
) -> GateRunRecord:
    return GateRunRecord(
        requested_gate_names=tuple(o.gate_name for o in outcomes),
        outcomes=tuple(outcomes),
        pre_freeze_verification=pre if pre is not None else _verification(),
        post_freeze_verification=post if post is not None else _verification(),
        bracket_invalidated=bracket_invalidated,
        context_digest="sha256:" + "0" * 64,
        measurement_provenance=provenance,
        code_commit_hash="c" * 40,
        recorded_at=datetime(2026, 7, 24, 12, 0, 0, tzinfo=timezone.utc),
    )


def _context(*, commit_ref: str = FREEZE_REF, covered: tuple[str, ...] = COVERED) -> GateContext:
    return GateContext(
        measurements={},
        frozen_criteria={},
        freeze_commit_ref=commit_ref,
        freeze_covered_paths=list(covered),
        evidence_refs=(),
        decision=_decision(),
    )


@pytest.fixture
def archive(tmp_path: Path) -> tuple[Path, Path]:
    """A cycle archive dir with a valid manifest -- the precondition
    DecisionRecorder.append requires. Returns (archive_root, archive_dir)."""
    archive_root = tmp_path / "research_archive"
    archive_dir = archive_root / "reference_h4"
    archive_dir.mkdir(parents=True)
    manifest = {
        "schema_version": 1,
        "project_id": "reference_h4",
        "created_at": "2026-07-22T00:00:00+00:00",
        "lifecycle_version": "v1",
    }
    (archive_dir / "archive_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return archive_root, archive_dir


def _compose_genesis(archive_root: Path, run_record: GateRunRecord, context: GateContext, **overrides: object):
    kwargs: dict[str, object] = dict(
        recorder=DecisionRecorder(archive_root),
        project_id="reference_h4",
        from_phase=LifecyclePhase.IMPLEMENTATION,
        to_phase=LifecyclePhase.VALIDATION,
        required_gate_names=("economic_rationale",),
        run_record=run_record,
        context=context,
        authorization=_authorization(),
        recorded_at="2026-07-24T12:00:00+00:00",
        commit_hash="d" * 40,
        expected_anchor=None,
    )
    kwargs.update(overrides)
    return compose_transition(**kwargs)  # type: ignore[arg-type]


# --- happy path: genesis transition -------------------------------------


def test_genesis_transition_writes_one_record(archive: tuple[Path, Path]) -> None:
    archive_root, archive_dir = archive
    run_record = _run_record([_outcome("economic_rationale", GateStatus.PASS)])

    record = _compose_genesis(archive_root, run_record, _context())

    assert record.sequence_number == 1
    assert record.from_phase == "Implementation"
    assert record.to_phase == "Validation"
    assert record.freeze_verification_status == "verified"
    assert record.freeze_covered_paths == COVERED
    assert record.gate_outcomes[0].status == "pass"
    chain_path = archive_dir / TRANSITION_RECORDS_FILENAME
    assert len(read_canonical_jsonl(chain_path)) == 1


def test_genesis_predecessor_hash_is_none(archive: tuple[Path, Path]) -> None:
    archive_root, _ = archive
    run_record = _run_record([_outcome("economic_rationale", GateStatus.PASS)])

    record = _compose_genesis(archive_root, run_record, _context())

    assert record.predecessor_hash is None


def test_genesis_records_the_explicit_from_phase_never_a_default(archive: tuple[Path, Path]) -> None:
    """Genesis from_phase is an explicit human assertion (AD-058): the
    composition records exactly what was supplied, never a forced
    Hypothesis. Pre-validation -> Methodology Freeze proves no default."""
    archive_root, _ = archive
    run_record = _run_record([_outcome("economic_rationale", GateStatus.PASS)])

    record = _compose_genesis(
        archive_root,
        run_record,
        _context(),
        from_phase=LifecyclePhase.PRE_VALIDATION,
        to_phase=LifecyclePhase.METHODOLOGY_FREEZE,
    )

    assert record.from_phase == "Pre-validation"
    assert record.to_phase == "Methodology Freeze"


def test_compose_transition_requires_explicit_from_phase_argument() -> None:
    """from_phase is a required keyword-only argument -- there is no
    signature path that lets it default (AD-058)."""
    with pytest.raises(TypeError):
        compose_transition(  # type: ignore[call-arg]
            recorder=DecisionRecorder(Path(".")),
            project_id="reference_h4",
            to_phase=LifecyclePhase.VALIDATION,
            required_gate_names=("economic_rationale",),
            run_record=_run_record([_outcome("economic_rationale")]),
            context=_context(),
            authorization=_authorization(),
            recorded_at="2026-07-24T12:00:00+00:00",
            commit_hash="d" * 40,
        )


# --- crash refusal (AD-056) ---------------------------------------------


def test_crashed_outcome_refuses_transition(archive: tuple[Path, Path]) -> None:
    archive_root, _ = archive
    run_record = _run_record([_outcome("economic_rationale", error="RuntimeError: boom")])

    with pytest.raises(CrashedGateInSequence):
        _compose_genesis(archive_root, run_record, _context())


def test_crash_writes_no_decision_record(archive: tuple[Path, Path]) -> None:
    """A crash blocks the transition and no DecisionRecord is written --
    the chain file is never created, even though the archive manifest is
    present and an append would otherwise succeed (AD-056)."""
    archive_root, archive_dir = archive
    run_record = _run_record([_outcome("economic_rationale", error="RuntimeError: boom")])

    with pytest.raises(CrashedGateInSequence):
        _compose_genesis(archive_root, run_record, _context())

    chain_path = archive_dir / TRANSITION_RECORDS_FILENAME
    assert not chain_path.exists()
    assert read_chain(chain_path) == ()


def test_crash_is_refused_even_when_a_valid_gate_also_ran(archive: tuple[Path, Path]) -> None:
    archive_root, archive_dir = archive
    run_record = _run_record(
        [
            _outcome("economic_rationale", GateStatus.PASS),
            _outcome("signal_independence", error="ValueError: nope"),
        ]
    )

    with pytest.raises(CrashedGateInSequence):
        _compose_genesis(
            archive_root,
            run_record,
            _context(),
            required_gate_names=("economic_rationale", "signal_independence"),
        )
    assert not (archive_dir / TRANSITION_RECORDS_FILENAME).exists()


# --- completeness (AD-059 step 1) ---------------------------------------


def test_missing_required_gate_refuses_transition(archive: tuple[Path, Path]) -> None:
    archive_root, _ = archive
    run_record = _run_record([_outcome("economic_rationale", GateStatus.PASS)])

    with pytest.raises(IncompleteGateSequence):
        _compose_genesis(
            archive_root,
            run_record,
            _context(),
            required_gate_names=("economic_rationale", "signal_independence"),
        )


# --- bracket refusal (AD-059 step 3) ------------------------------------


def test_invalidated_bracket_refuses_transition(archive: tuple[Path, Path]) -> None:
    archive_root, archive_dir = archive
    run_record = _run_record(
        [_outcome("economic_rationale", GateStatus.PASS)],
        bracket_invalidated=True,
    )

    with pytest.raises(BracketInvalidated):
        _compose_genesis(archive_root, run_record, _context())
    assert not (archive_dir / TRANSITION_RECORDS_FILENAME).exists()


# --- freeze projection: verified-only (AD-059 step 4) -------------------


def test_non_verified_freeze_end_refuses_transition(archive: tuple[Path, Path]) -> None:
    """A DRIFTED post-verification refuses the transition with no
    AMBIGUOUS conversion. bracket_invalidated is left False deliberately
    so the freeze projection's own independent guard is what fires."""
    archive_root, _ = archive
    run_record = _run_record(
        [_outcome("economic_rationale", GateStatus.PASS)],
        pre=_verification(status=FreezeStatus.VERIFIED),
        post=_verification(status=FreezeStatus.DRIFTED),
        bracket_invalidated=False,
    )

    with pytest.raises(FreezeNotVerified):
        _compose_genesis(archive_root, run_record, _context())


def test_freeze_hash_mismatch_refuses_transition(archive: tuple[Path, Path]) -> None:
    """Both ends VERIFIED but at different resolved commits -- the bracket
    straddled a freeze change. Refused, again with bracket_invalidated
    left False to prove the composition's own hash-equality guard fires."""
    archive_root, _ = archive
    run_record = _run_record(
        [_outcome("economic_rationale", GateStatus.PASS)],
        pre=_verification(resolved="a" * 40),
        post=_verification(resolved="b" * 40),
        bracket_invalidated=False,
    )

    with pytest.raises(FreezeNotVerified):
        _compose_genesis(archive_root, run_record, _context())


# --- context <-> run record binding -------------------------------------


def test_context_freeze_ref_must_match_run_record(archive: tuple[Path, Path]) -> None:
    archive_root, _ = archive
    run_record = _run_record([_outcome("economic_rationale", GateStatus.PASS)])
    mismatched_context = _context(commit_ref="e" * 40)

    with pytest.raises(ContextRunRecordMismatch):
        _compose_genesis(archive_root, run_record, mismatched_context)


# --- covered-path binding (AD-060) --------------------------------------


def test_context_covered_paths_must_match_run_record(archive: tuple[Path, Path]) -> None:
    """A context claiming different covered paths than the run record's
    own verified evidence refuses the transition -- the same commit ref
    is not enough to smuggle in unverified coverage."""
    archive_root, _ = archive
    run_record = _run_record([_outcome("economic_rationale", GateStatus.PASS)])
    mismatched_context = _context(covered=("docs/a_different_file.md",))

    with pytest.raises(ContextRunRecordMismatch):
        _compose_genesis(archive_root, run_record, mismatched_context)


def test_context_covered_paths_superset_of_verified_refuses(archive: tuple[Path, Path]) -> None:
    """A context that claims *more* coverage than was actually verified
    (same commit ref, an extra path added) is refused, not silently
    trimmed or widened."""
    archive_root, _ = archive
    run_record = _run_record([_outcome("economic_rationale", GateStatus.PASS)])
    wider_context = _context(covered=(*COVERED, "docs/extra_unverified.md"))

    with pytest.raises(ContextRunRecordMismatch):
        _compose_genesis(archive_root, run_record, wider_context)


def test_pre_post_covered_path_disagreement_refuses(archive: tuple[Path, Path]) -> None:
    """A hand-built run record whose pre/post verifications covered
    different paths -- something a real GateRunner never produces, since
    it always runs both ends against the same context -- is refused
    rather than trusted on the pre end alone."""
    archive_root, _ = archive
    run_record = _run_record(
        [_outcome("economic_rationale", GateStatus.PASS)],
        pre=_verification(covered=COVERED),
        post=_verification(covered=("docs/other_file.md",)),
    )

    with pytest.raises(ContextRunRecordMismatch):
        _compose_genesis(archive_root, run_record, _context(covered=COVERED))


def test_matching_covered_paths_pass_and_bind_from_run_record(archive: tuple[Path, Path]) -> None:
    """When context and the run record's verified paths agree (as sets,
    regardless of order), the transition succeeds and the persisted
    `freeze_covered_paths` is bound to the run record's own verified
    value -- not merely copied from context -- proving the mechanical
    binding rather than a coincidental match."""
    archive_root, _ = archive
    verified_order = ("docs/b.md", "docs/a.md")
    run_record = _run_record(
        [_outcome("economic_rationale", GateStatus.PASS)],
        pre=_verification(covered=verified_order),
        post=_verification(covered=verified_order),
    )
    # context supplies the same set in a different order
    context = _context(covered=("docs/a.md", "docs/b.md"))

    record = _compose_genesis(archive_root, run_record, context)

    assert record.freeze_covered_paths == verified_order


# --- provenance pass-through (AD-059 step 7) ----------------------------


def test_evidence_refs_are_passed_through_ordered_and_deduped(archive: tuple[Path, Path]) -> None:
    archive_root, _ = archive
    run_record = _run_record(
        [
            _outcome("economic_rationale", GateStatus.PASS, evidence_refs=("r/a.json", "r/b.json")),
            _outcome("signal_independence", GateStatus.PASS, evidence_refs=("r/b.json", "r/c.json")),
        ]
    )

    record = _compose_genesis(
        archive_root,
        run_record,
        _context(),
        required_gate_names=("economic_rationale", "signal_independence"),
    )

    # first-appearance order preserved; r/b.json de-duplicated; nothing generated
    assert record.evidence_refs == ("r/a.json", "r/b.json", "r/c.json")


def test_reproduction_record_ref_is_exactly_the_run_records(archive: tuple[Path, Path]) -> None:
    archive_root, _ = archive
    provenance = "research_archive/reference_h4/reproduction_record.json"
    run_record = _run_record([_outcome("economic_rationale", GateStatus.PASS)], provenance=provenance)

    record = _compose_genesis(archive_root, run_record, _context())

    assert record.reproduction_record_ref == provenance


def test_absent_provenance_passes_through_as_none(archive: tuple[Path, Path]) -> None:
    """measurement_provenance=None is recorded as-is (an audit finding
    per AD-050), never invented into a string."""
    archive_root, _ = archive
    run_record = _run_record([_outcome("economic_rationale", GateStatus.PASS)], provenance=None)

    record = _compose_genesis(archive_root, run_record, _context())

    assert record.reproduction_record_ref is None


# --- non-genesis: derived-phase consistency + anchoring -----------------


def _append_genesis(archive_root: Path) -> tuple[int, str]:
    """Write a real genesis record and return its (sequence_number,
    head_hash) anchor, read back from the persisted chain."""
    run_record = _run_record([_outcome("economic_rationale", GateStatus.PASS)])
    _compose_genesis(
        archive_root,
        run_record,
        _context(),
        from_phase=LifecyclePhase.HYPOTHESIS,
        to_phase=LifecyclePhase.RESEARCH_PROPOSAL,
    )
    chain_path = DecisionRecorder(archive_root).chain_path("reference_h4")
    rows = read_canonical_jsonl(chain_path)
    return 1, hash_record(rows[0])


def test_non_genesis_transition_with_valid_anchor(archive: tuple[Path, Path]) -> None:
    archive_root, _ = archive
    anchor = _append_genesis(archive_root)
    run_record = _run_record([_outcome("economic_rationale", GateStatus.PASS)])

    record = compose_transition(
        recorder=DecisionRecorder(archive_root),
        project_id="reference_h4",
        from_phase=LifecyclePhase.RESEARCH_PROPOSAL,
        to_phase=LifecyclePhase.PRE_VALIDATION,
        required_gate_names=("economic_rationale",),
        run_record=run_record,
        context=_context(),
        authorization=_authorization(),
        recorded_at="2026-07-24T13:00:00+00:00",
        commit_hash="d" * 40,
        expected_anchor=anchor,
    )

    assert record.sequence_number == 2
    assert record.predecessor_hash is not None


def test_non_genesis_from_phase_must_match_derived_phase(archive: tuple[Path, Path]) -> None:
    archive_root, _ = archive
    anchor = _append_genesis(archive_root)  # chain now at Research Proposal
    run_record = _run_record([_outcome("economic_rationale", GateStatus.PASS)])

    with pytest.raises(PhaseChainMismatch):
        compose_transition(
            recorder=DecisionRecorder(archive_root),
            project_id="reference_h4",
            from_phase=LifecyclePhase.IMPLEMENTATION,  # wrong -- chain says Research Proposal
            to_phase=LifecyclePhase.VALIDATION,
            required_gate_names=("economic_rationale",),
            run_record=run_record,
            context=_context(),
            authorization=_authorization(),
            recorded_at="2026-07-24T13:00:00+00:00",
            commit_hash="d" * 40,
            expected_anchor=anchor,
        )


def test_non_genesis_without_anchor_is_refused(archive: tuple[Path, Path]) -> None:
    archive_root, _ = archive
    _append_genesis(archive_root)
    run_record = _run_record([_outcome("economic_rationale", GateStatus.PASS)])

    with pytest.raises(UnanchoredTransition):
        compose_transition(
            recorder=DecisionRecorder(archive_root),
            project_id="reference_h4",
            from_phase=LifecyclePhase.RESEARCH_PROPOSAL,
            to_phase=LifecyclePhase.PRE_VALIDATION,
            required_gate_names=("economic_rationale",),
            run_record=run_record,
            context=_context(),
            authorization=_authorization(),
            recorded_at="2026-07-24T13:00:00+00:00",
            commit_hash="d" * 40,
            expected_anchor=None,
        )


def test_non_genesis_with_bad_anchor_is_refused(archive: tuple[Path, Path]) -> None:
    archive_root, _ = archive
    _append_genesis(archive_root)
    run_record = _run_record([_outcome("economic_rationale", GateStatus.PASS)])

    with pytest.raises(ChainNotAnchored):
        compose_transition(
            recorder=DecisionRecorder(archive_root),
            project_id="reference_h4",
            from_phase=LifecyclePhase.RESEARCH_PROPOSAL,
            to_phase=LifecyclePhase.PRE_VALIDATION,
            required_gate_names=("economic_rationale",),
            run_record=run_record,
            context=_context(),
            authorization=_authorization(),
            recorded_at="2026-07-24T13:00:00+00:00",
            commit_hash="d" * 40,
            expected_anchor=(1, "sha256:" + "9" * 64),  # wrong hash
        )


# --- H4 end-to-end: real GateRunner -> real DecisionRecorder ------------


def _git(args: list[str], *, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


class _PassingGate:
    def __init__(self, name: str) -> None:
        self.name = name
        self.required_review_level = "Level 1"

    def run(self, context: GateContext) -> GateResult:
        return GateResult(
            gate_name=self.name,
            status=GateStatus.PASS,
            summary=f"{self.name} passed",
            evidence_refs=(f"research_archive/reference_h4/experiment_results/{self.name}.json",),
            decision=context.decision,
        )


def test_h4_end_to_end_transition(tmp_path: Path) -> None:
    """Full pipeline: a real GateRunner brackets a real freeze over a real
    git repo, and compose_transition binds the resulting GateRunRecord to
    a genesis DecisionRecord in a real archive."""
    repo = tmp_path
    _git(["init", "-q"], cwd=repo)
    _git(["config", "user.email", "test@example.com"], cwd=repo)
    _git(["config", "user.name", "Test"], cwd=repo)
    (repo / "acceptance_criteria.md").write_text("frozen\n", encoding="utf-8")
    _git(["add", "acceptance_criteria.md"], cwd=repo)
    _git(["commit", "-q", "-m", "freeze"], cwd=repo)
    freeze_hash = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    # real archive under the same repo
    archive_root = repo / "research_archive"
    archive_dir = archive_root / "reference_h4"
    archive_dir.mkdir(parents=True)
    (archive_dir / "archive_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "project_id": "reference_h4",
                "created_at": "2026-07-22T00:00:00+00:00",
                "lifecycle_version": "v1",
            }
        ),
        encoding="utf-8",
    )

    context = GateContext(
        measurements={},
        frozen_criteria={},
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=["acceptance_criteria.md"],
        evidence_refs=(),
        decision=_decision(),
        measurement_provenance="research_archive/reference_h4/reproduction_record.json",
    )
    runner = GateRunner()
    runner.register_gate(_PassingGate("economic_rationale"))
    run_record = runner.run_sequence(
        ["economic_rationale"],
        context,
        clock=FixedClock(datetime(2026, 7, 24, 12, 0, 0, tzinfo=timezone.utc)),
        code_commit_hash=freeze_hash,
        repo_root=repo,
    )
    assert run_record.bracket_invalidated is False

    record = compose_transition(
        recorder=DecisionRecorder(archive_root),
        project_id="reference_h4",
        from_phase=LifecyclePhase.IMPLEMENTATION,
        to_phase=LifecyclePhase.VALIDATION,
        required_gate_names=("economic_rationale",),
        run_record=run_record,
        context=context,
        authorization=_authorization(),
        recorded_at="2026-07-24T12:00:00+00:00",
        commit_hash=freeze_hash,
        expected_anchor=None,
    )

    assert record.sequence_number == 1
    assert record.predecessor_hash is None
    assert record.from_phase == "Implementation"
    assert record.to_phase == "Validation"
    assert record.freeze_verification_status == "verified"
    assert record.freeze_commit_ref == freeze_hash
    assert record.freeze_covered_paths == ("acceptance_criteria.md",)
    assert record.gate_outcomes == tuple(record.gate_outcomes)  # ordered, concrete
    assert record.gate_outcomes[0].gate_name == "economic_rationale"
    assert record.gate_outcomes[0].status == "pass"
    assert record.evidence_refs == (
        "research_archive/reference_h4/experiment_results/economic_rationale.json",
    )
    assert record.reproduction_record_ref == "research_archive/reference_h4/reproduction_record.json"

    # persisted and chain-intact
    chain_path = archive_dir / TRANSITION_RECORDS_FILENAME
    assert len(read_canonical_jsonl(chain_path)) == 1
