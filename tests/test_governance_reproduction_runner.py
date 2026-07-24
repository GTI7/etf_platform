"""End-to-end test of core.governance.reproduction_runner: a throwaway
git repo standing in for the real etf_platform repo, with its own
committed migrations/ and a tiny experiment.py, pinned to a commit and
executed through the full guard -> worktree -> reconstruction ->
identity-check pipeline.
"""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from types import ModuleType

import pytest

from core.governance.canonical_jsonl import sha256_of_file, write_canonical_jsonl
from core.governance.dataset_manifest import MANIFEST_SCHEMA_VERSION
from core.governance.dataset_snapshots import etf_to_row
from core.governance import reproduction_runner as runner_module
from core.governance.reproduction_record import ReproductionStatus
from core.governance.reproduction_runner import UNIVERSE_MODULE_RELATIVE_PATH, run_reproduction
from core.market_data.domain.models import ETF

REAL_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"

_EXPERIMENT_SOURCE = '''\
import sqlite3

RAN_WITH_NETWORK_ATTEMPT = False


def run(db_path):
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO IndicatorDefinition (indicator_definition_id, name, version, parameters, created_at) "
            "VALUES ('def-1', 'SMA', 1, '{}', '2026-07-20T00:00:00+00:00')"
        )
        conn.commit()
    finally:
        conn.close()
    return "ok"
'''

_NETWORK_EXPERIMENT_SOURCE = '''\
import socket


def run(db_path):
    socket.create_connection(("example.invalid", 80))
'''

_FAILING_EXPERIMENT_SOURCE = '''\
def run(db_path):
    raise RuntimeError("the experiment itself blew up")
'''

# A pinned universe script importing a module HEAD no longer provides --
# the AD-069 shim-deletion scenario, reduced to a name that can never exist.
_UNIVERSE_SOURCE_WITH_MISSING_DEPENDENCY = '''\
import core.market_data.persistence.module_that_head_does_not_provide  # noqa: F401

ETF_UNIVERSE = [("SPY", "SPDR S&P 500")]
'''


def _git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo_with_migrations_and_experiment(repo: Path, experiment_source: str) -> str:
    _git(["init", "-q"], cwd=repo)
    _git(["config", "user.email", "test@example.com"], cwd=repo)
    _git(["config", "user.name", "Test"], cwd=repo)

    migrations_dir = repo / "migrations"
    migrations_dir.mkdir()
    for migration_file in REAL_MIGRATIONS_DIR.glob("*.sql"):
        shutil.copy(migration_file, migrations_dir / migration_file.name)

    (repo / "experiment.py").write_text(experiment_source, encoding="utf-8")

    _git(["add", "-A"], cwd=repo)
    _git(["commit", "-q", "-m", "pin this commit"], cwd=repo)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


def _init_repo_with_universe_module(repo: Path, universe_source: str) -> str:
    """Same throwaway repo, but the pinned experiment is the one path that
    triggers the mandatory ETF_UNIVERSE preload (runner :181-186)."""
    _init_repo_with_migrations_and_experiment(repo, _EXPERIMENT_SOURCE)
    universe_path = repo / UNIVERSE_MODULE_RELATIVE_PATH
    universe_path.parent.mkdir(parents=True, exist_ok=True)
    universe_path.write_text(universe_source, encoding="utf-8")
    _git(["add", "-A"], cwd=repo)
    _git(["commit", "-q", "-m", "pin the universe module"], cwd=repo)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def _etf(ticker: str, etf_id: str) -> ETF:
    return ETF(
        etf_id=etf_id,
        ticker=ticker,
        name=f"{ticker} Fund",
        currency="USD",
        calendar_id="XNYS",
        created_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
    )


def _build_cycle(tmp_path: Path) -> tuple[Path, Path]:
    cycle_dir = tmp_path / "cycle"
    (cycle_dir / "dataset_hashes").mkdir(parents=True)

    def _entry(source_table: str, filename: str, rows: list[dict]) -> dict:
        path = cycle_dir / "dataset_hashes" / filename
        write_canonical_jsonl(rows, path)
        return {
            "dataset_id": f"{source_table.lower()}_v1",
            "type": "test_fixture_data",
            "source_table": source_table,
            "row_count": len(rows),
            "snapshot_path": f"dataset_hashes/{filename}",
            "content_hash": sha256_of_file(path),
            "schema_version": 1,
        }

    entries = [
        _entry("ETF", "etf.jsonl", [etf_to_row(_etf("SPY", "etf-spy"))]),
        _entry("TradingSession", "trading_session.jsonl", []),
        _entry("PriceBar", "pricebar.jsonl", []),
    ]
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "project_id": "test_cycle",
        "generated_at": "2026-08-01T00:00:00+00:00",
        "datasets": entries,
    }
    manifest_path = cycle_dir / "dataset_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return cycle_dir, manifest_path


def _run_module(module: ModuleType, db_path: Path) -> None:
    module.run(db_path)


def test_full_reproduction_verifies(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    commit_hash = _init_repo_with_migrations_and_experiment(repo, _EXPERIMENT_SOURCE)
    cycle_dir, manifest_path = _build_cycle(tmp_path)

    outcome = run_reproduction(
        repo_root=repo,
        cycle_dir=cycle_dir,
        dataset_manifest_path=manifest_path,
        migrations_relative_path="migrations",
        experiment_module_relative_path="experiment.py",
        commit_hash=commit_hash,
        scratch_db_path=tmp_path / "scratch.db",
        run_experiment=_run_module,
    )

    assert outcome.status is ReproductionStatus.VERIFIED


def test_experiment_code_runs_from_the_pinned_commit_not_head(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    commit_hash = _init_repo_with_migrations_and_experiment(repo, _EXPERIMENT_SOURCE)

    # HEAD moves on to a version that would fail (bad table name) --
    # reproduction must still use the pinned commit's own version.
    (repo / "experiment.py").write_text(
        "def run(db_path):\n    raise RuntimeError('HEAD code must never run during reproduction')\n",
        encoding="utf-8",
    )
    _git(["add", "-A"], cwd=repo)
    _git(["commit", "-q", "-m", "HEAD moved on"], cwd=repo)

    cycle_dir, manifest_path = _build_cycle(tmp_path)

    outcome = run_reproduction(
        repo_root=repo,
        cycle_dir=cycle_dir,
        dataset_manifest_path=manifest_path,
        migrations_relative_path="migrations",
        experiment_module_relative_path="experiment.py",
        commit_hash=commit_hash,
        scratch_db_path=tmp_path / "scratch.db",
        run_experiment=_run_module,
    )

    assert outcome.status is ReproductionStatus.VERIFIED


def test_network_attempt_during_run_produces_reproduction_failed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    commit_hash = _init_repo_with_migrations_and_experiment(repo, _NETWORK_EXPERIMENT_SOURCE)
    cycle_dir, manifest_path = _build_cycle(tmp_path)

    outcome = run_reproduction(
        repo_root=repo,
        cycle_dir=cycle_dir,
        dataset_manifest_path=manifest_path,
        migrations_relative_path="migrations",
        experiment_module_relative_path="experiment.py",
        commit_hash=commit_hash,
        scratch_db_path=tmp_path / "scratch.db",
        run_experiment=_run_module,
    )

    assert outcome.status is ReproductionStatus.REPRODUCTION_FAILED
    assert "blocked outbound socket connection" in outcome.detail


def test_missing_dependency_on_the_universe_preload_is_unverifiable(tmp_path: Path) -> None:
    """Taxonomy, arm 1 of 3 -- a pinned artifact that cannot be *loaded*.

    ImportError/ModuleNotFoundError is not an OSError subclass, so before
    the failure taxonomy was normalized this escaped run_reproduction
    entirely: no governed status, no evidence record (AD-069's disclosed
    open item). It is a missing/unresolvable artifact, so: UNVERIFIABLE.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    commit_hash = _init_repo_with_universe_module(repo, _UNIVERSE_SOURCE_WITH_MISSING_DEPENDENCY)
    cycle_dir, manifest_path = _build_cycle(tmp_path)

    outcome = run_reproduction(
        repo_root=repo,
        cycle_dir=cycle_dir,
        dataset_manifest_path=manifest_path,
        migrations_relative_path="migrations",
        experiment_module_relative_path=UNIVERSE_MODULE_RELATIVE_PATH,
        commit_hash=commit_hash,
        scratch_db_path=tmp_path / "scratch.db",
        run_experiment=_run_module,
    )

    assert outcome.status is ReproductionStatus.UNVERIFIABLE
    assert "module_that_head_does_not_provide" in outcome.detail


def test_missing_dependency_during_reconstruction_is_unverifiable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Taxonomy, arm 1 of 3, second path -- the same fault raised from
    inside the reconstruction phase must not be absorbed by that phase's
    DRIFTED backstop. The archived inputs are not what broke."""
    repo = tmp_path / "repo"
    repo.mkdir()
    commit_hash = _init_repo_with_migrations_and_experiment(repo, _EXPERIMENT_SOURCE)
    cycle_dir, manifest_path = _build_cycle(tmp_path)

    def _raise_module_not_found(**_kwargs: object) -> None:
        raise ModuleNotFoundError("No module named 'core.market_data.persistence.database'")

    monkeypatch.setattr(runner_module, "reconstruct_database", _raise_module_not_found)

    outcome = run_reproduction(
        repo_root=repo,
        cycle_dir=cycle_dir,
        dataset_manifest_path=manifest_path,
        migrations_relative_path="migrations",
        experiment_module_relative_path="experiment.py",
        commit_hash=commit_hash,
        scratch_db_path=tmp_path / "scratch.db",
        run_experiment=_run_module,
    )

    assert outcome.status is ReproductionStatus.UNVERIFIABLE
    assert "core.market_data.persistence.database" in outcome.detail


def test_operational_failure_during_the_run_is_reproduction_failed(tmp_path: Path) -> None:
    """Taxonomy, arm 2 of 3 -- every input reconstructed cleanly and the
    run itself failed. Unchanged by the taxonomy normalization; asserted
    here so a future widening of the ImportError carve-out cannot quietly
    pull the execution phase in with it."""
    repo = tmp_path / "repo"
    repo.mkdir()
    commit_hash = _init_repo_with_migrations_and_experiment(repo, _FAILING_EXPERIMENT_SOURCE)
    cycle_dir, manifest_path = _build_cycle(tmp_path)

    outcome = run_reproduction(
        repo_root=repo,
        cycle_dir=cycle_dir,
        dataset_manifest_path=manifest_path,
        migrations_relative_path="migrations",
        experiment_module_relative_path="experiment.py",
        commit_hash=commit_hash,
        scratch_db_path=tmp_path / "scratch.db",
        run_experiment=_run_module,
    )

    assert outcome.status is ReproductionStatus.REPRODUCTION_FAILED
    assert "the experiment itself blew up" in outcome.detail


def test_artifact_hash_mismatch_is_drifted(tmp_path: Path) -> None:
    """Taxonomy, arm 3 of 3 -- a frozen input that no longer matches the
    hash the manifest claims for it. Still DRIFTED: carving ImportError
    out of the reconstruction backstop must not narrow real drift."""
    repo = tmp_path / "repo"
    repo.mkdir()
    commit_hash = _init_repo_with_migrations_and_experiment(repo, _EXPERIMENT_SOURCE)
    cycle_dir, manifest_path = _build_cycle(tmp_path)

    # The ETF snapshot is edited after freeze; its declared content_hash
    # no longer describes the bytes on disk.
    snapshot_path = cycle_dir / "dataset_hashes" / "etf.jsonl"
    snapshot_path.write_text(
        snapshot_path.read_text(encoding="utf-8").replace("SPY", "QQQ"), encoding="utf-8"
    )

    outcome = run_reproduction(
        repo_root=repo,
        cycle_dir=cycle_dir,
        dataset_manifest_path=manifest_path,
        migrations_relative_path="migrations",
        experiment_module_relative_path="experiment.py",
        commit_hash=commit_hash,
        scratch_db_path=tmp_path / "scratch.db",
        run_experiment=_run_module,
    )

    assert outcome.status is ReproductionStatus.DRIFTED
    assert "content_hash mismatch" in outcome.detail


def test_guard_is_uninstalled_after_the_attempt_completes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    commit_hash = _init_repo_with_migrations_and_experiment(repo, _EXPERIMENT_SOURCE)
    cycle_dir, manifest_path = _build_cycle(tmp_path)

    run_reproduction(
        repo_root=repo,
        cycle_dir=cycle_dir,
        dataset_manifest_path=manifest_path,
        migrations_relative_path="migrations",
        experiment_module_relative_path="experiment.py",
        commit_hash=commit_hash,
        scratch_db_path=tmp_path / "scratch.db",
        run_experiment=_run_module,
    )

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(OSError):
            sock.connect(("127.0.0.1", 1))
    finally:
        sock.close()
