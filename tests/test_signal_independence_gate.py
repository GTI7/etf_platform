from __future__ import annotations

import subprocess
from decimal import Decimal
from pathlib import Path

import pytest

from core.validation.gate_result import DecisionMetadata, GateStatus
from core.validation.gates.signal_independence import evaluate_signal_independence_gate


def _git(args: list[str], *, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(["init", "-q"], cwd=tmp_path)
    _git(["config", "user.email", "test@example.com"], cwd=tmp_path)
    _git(["config", "user.name", "Test"], cwd=tmp_path)
    return tmp_path


def _commit(repo: Path, filename: str, content: str, message: str) -> str:
    (repo / filename).write_text(content, encoding="utf-8")
    _git(["add", filename], cwd=repo)
    _git(["commit", "-q", "-m", message], cwd=repo)
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _decision() -> DecisionMetadata:
    return DecisionMetadata(reviewer="test-reviewer", review_level="Level 2", decided_at="2026-07-19")


def test_missing_frozen_threshold_is_ambiguous_governance_failure(repo: Path) -> None:
    freeze_hash = _commit(repo, "gate1_plan.md", "frozen plan\n", "freeze")

    result = evaluate_signal_independence_gate(
        measured_overlap=Decimal("0.42"),
        frozen_threshold=None,
        threshold_direction=None,
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=["gate1_plan.md"],
        evidence_refs=("gate1_independence_analysis.json",),
        decision=_decision(),
        repo_root=repo,
    )

    assert result.status is GateStatus.AMBIGUOUS
    assert result.summary == "Acceptance criterion was not frozen before validation."


def test_missing_threshold_direction_alone_is_also_ambiguous(repo: Path) -> None:
    freeze_hash = _commit(repo, "gate1_plan.md", "frozen plan\n", "freeze")

    result = evaluate_signal_independence_gate(
        measured_overlap=Decimal("0.42"),
        frozen_threshold=Decimal("0.5"),
        threshold_direction=None,
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=["gate1_plan.md"],
        evidence_refs=(),
        decision=_decision(),
        repo_root=repo,
    )

    assert result.status is GateStatus.AMBIGUOUS
    assert result.summary == "Acceptance criterion was not frozen before validation."


def test_drifted_freeze_is_ambiguous_not_fail(repo: Path) -> None:
    freeze_hash = _commit(repo, "gate1_plan.md", "frozen plan\n", "freeze")
    _commit(repo, "gate1_plan.md", "edited after freeze\n", "oops")

    result = evaluate_signal_independence_gate(
        measured_overlap=Decimal("0.9"),
        frozen_threshold=Decimal("0.5"),
        threshold_direction="at_most",
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=["gate1_plan.md"],
        evidence_refs=(),
        decision=_decision(),
        repo_root=repo,
    )

    assert result.status is GateStatus.AMBIGUOUS
    assert "Freeze verification did not succeed" in result.summary
    assert result.summary != "Acceptance criterion was not frozen before validation."


def test_meets_frozen_threshold_passes(repo: Path) -> None:
    freeze_hash = _commit(repo, "gate1_plan.md", "frozen plan\n", "freeze")

    result = evaluate_signal_independence_gate(
        measured_overlap=Decimal("0.10"),
        frozen_threshold=Decimal("0.30"),
        threshold_direction="at_most",
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=["gate1_plan.md"],
        evidence_refs=(),
        decision=_decision(),
        repo_root=repo,
    )

    assert result.status is GateStatus.PASS


def test_misses_frozen_threshold_fails(repo: Path) -> None:
    freeze_hash = _commit(repo, "gate1_plan.md", "frozen plan\n", "freeze")

    result = evaluate_signal_independence_gate(
        measured_overlap=Decimal("0.90"),
        frozen_threshold=Decimal("0.30"),
        threshold_direction="at_most",
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=["gate1_plan.md"],
        evidence_refs=(),
        decision=_decision(),
        repo_root=repo,
    )

    assert result.status is GateStatus.FAIL


def test_evidence_refs_pass_through_unmodified(repo: Path) -> None:
    freeze_hash = _commit(repo, "gate1_plan.md", "frozen plan\n", "freeze")
    refs = ("research_archive/reference_h3/gate1_independence_analysis_2026-07-19.json", "docs/H3_GATE1_REPRODUCTION_REVIEW.md")

    result = evaluate_signal_independence_gate(
        measured_overlap=Decimal("0.10"),
        frozen_threshold=Decimal("0.30"),
        threshold_direction="at_most",
        freeze_commit_ref=freeze_hash,
        freeze_covered_paths=["gate1_plan.md"],
        evidence_refs=refs,
        decision=_decision(),
        repo_root=repo,
    )

    assert result.evidence_refs == refs


def test_gate_never_imports_core_statistics() -> None:
    """core.statistics is never imported by this gate module -- AD-041.
    Parses actual import statements (not the docstring, which mentions
    core.statistics in prose) via ast, same technique
    tools/check_import_boundaries.py uses for the same reason."""
    import ast

    import core.validation.gates.signal_independence as gate_module

    tree = ast.parse(Path(gate_module.__file__).read_text(encoding="utf-8"))
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }

    assert not any(module == "core.statistics" or module.startswith("core.statistics.") for module in imported_modules)
