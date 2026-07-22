"""Reproduction runner (Phase 4 Architecture Amendment v1.1 SS D-F): the
one place that ties the offline guard, the pinned-worktree execution
model, the reconstruction loader, and the post-run frozen-identity check
together into a single reproduction attempt.

The offline guard installs before this function does anything else --
in particular, before the pinned commit's own experiment module is
imported -- so it is active for the entire attempt, not scoped to one
construction call (SS E).

Migrations, dataset snapshots, and the experiment script all come from
the pinned commit's own worktree, never from `repo_root`'s current HEAD
copy (SS F.2: "the dataset artifacts for a given cycle are committed
alongside methodology.md at freeze time... commit_hash pins code and
data together; nothing needs to reach outside the worktree").

Status mapping follows the base proposal's SS 2.2 semantics exactly:
a missing/unresolvable artifact (including an unresolvable commit_hash)
is ``UNVERIFIABLE``; an input that doesn't match its claimed hash/shape
is ``DRIFTED``; every input matching but the run itself failing
(including the offline guard tripping) is ``REPRODUCTION_FAILED``;
everything holding is ``VERIFIED``.

The reconstruction phase (offline guard already active, dataset/manifest
loading, pinned ETF_UNIVERSE coverage) is fully governed: no raw
exception from that phase -- including ``sqlite3.IntegrityError`` or
``ValueError`` from a malformed snapshot row a preflight check didn't
name -- ever escapes this function. Every specifically-named
reconstruction error maps to its own status below; anything else raised
during reconstruction still means an input didn't hold up against the
pinned commit's own reconstruction code, so it is governed as
``DRIFTED`` too, never left as a raw exception.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

from core.governance.identity_verification import (
    assert_frozen_identity_unchanged,
    snapshot_identity_state,
)
from core.governance.network_guard import offline_guard
from core.governance.pinned_worktree import REPO_ROOT, WorktreeError, pinned_worktree
from core.governance.reconstruction_loader import (
    DatasetHashMismatchError,
    DatasetRowCountMismatchError,
    DuplicateEtfIdError,
    DuplicateTickerError,
    DuplicateTradingSessionError,
    MalformedSnapshotRowError,
    MissingExpectedTickerError,
    MissingSnapshotArtifactError,
    OrphanPriceBarError,
    UnknownEtfCalendarError,
    UnknownTradingSessionCalendarError,
    reconstruct_database,
)
from core.governance.reproduction_record import ReproductionStatus
from core.market_data.persistence.database import connect

# The pinned commit's own copy of this file, never HEAD's -- the single
# source of truth for which tickers the ETF snapshot must cover (SS D.2).
UNIVERSE_MODULE_RELATIVE_PATH = "experiments/daily_etf_universe_update.py"

_DRIFT_ERRORS = (
    DatasetHashMismatchError,
    DatasetRowCountMismatchError,
    DuplicateEtfIdError,
    DuplicateTickerError,
    DuplicateTradingSessionError,
    MalformedSnapshotRowError,
    MissingExpectedTickerError,
    OrphanPriceBarError,
    UnknownEtfCalendarError,
    UnknownTradingSessionCalendarError,
)


class ReproductionRunnerError(RuntimeError):
    """Raised for an environmental failure of the runner itself (e.g. the
    experiment module cannot be loaded from the worktree at all) -- not
    for a failed reproduction attempt, which is a normal
    ``ReproductionOutcome`` result."""


class ReproductionOutcome:
    """Plain, serializable outcome of one reproduction attempt."""

    def __init__(self, status: ReproductionStatus, detail: str) -> None:
        self.status = status
        self.detail = detail

    def __repr__(self) -> str:
        return f"ReproductionOutcome(status={self.status!r}, detail={self.detail!r})"


def _load_module_from_worktree(worktree_path: Path, relative_module_path: str) -> ModuleType:
    """Import the pinned commit's own copy of an experiment script by
    file path, from the worktree -- never the repository's HEAD copy of
    the same file (SS D.2: the executing code's own universe literal
    must be the one the loaded ETF snapshot was checked against)."""
    module_file = worktree_path / relative_module_path
    spec = importlib.util.spec_from_file_location(module_file.stem, module_file)
    if spec is None or spec.loader is None:
        raise ReproductionRunnerError(f"cannot load an importable module from {module_file}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(worktree_path))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(worktree_path))
    return module


def _load_expected_tickers_from_worktree(worktree_path: Path) -> set[str]:
    """The pinned commit's own ``ETF_UNIVERSE``, loaded from its own
    worktree copy of ``experiments/daily_etf_universe_update.py`` -- never
    HEAD's, and never a caller-suppliable override. This makes the
    semantic coverage check mandatory: a reproduction attempt can no
    longer skip it by simply not passing an ``expected_tickers`` argument
    (SS D.2: "the executing code's own universe literal must be the one
    the loaded ETF snapshot was checked against")."""
    try:
        module = _load_module_from_worktree(worktree_path, UNIVERSE_MODULE_RELATIVE_PATH)
    except OSError as exc:
        # spec_from_file_location() does not itself fail for a path that
        # doesn't exist -- the failure only surfaces once exec_module()
        # tries to read it. A pinned commit that predates this file (or
        # never had it) is a missing/unresolvable artifact, not a runner
        # crash.
        raise ReproductionRunnerError(
            f"cannot load {UNIVERSE_MODULE_RELATIVE_PATH} from the pinned commit's worktree: {exc}"
        ) from exc
    try:
        universe = module.ETF_UNIVERSE
    except AttributeError as exc:
        raise ReproductionRunnerError(
            f"{UNIVERSE_MODULE_RELATIVE_PATH} at the pinned commit does not define ETF_UNIVERSE"
        ) from exc
    return {ticker for ticker, _name in universe}


def run_reproduction(
    *,
    repo_root: Path,
    cycle_dir: Path,
    dataset_manifest_path: Path,
    migrations_relative_path: str,
    experiment_module_relative_path: str,
    commit_hash: str,
    scratch_db_path: Path,
    run_experiment: Callable[[ModuleType, Path], Any],
) -> ReproductionOutcome:
    """Run one full reproduction attempt end-to-end.

    `run_experiment(module, scratch_db_path)` is the caller-supplied call
    into the pinned module's own `run()` entrypoint -- every existing
    `experiments/validate_*.py` script's signature differs slightly
    (universe, session_date, ...), so the exact call is the caller's
    responsibility; this function's job is guaranteeing the module and
    migrations come from the pinned worktree and every frozen input has
    already been verified, not knowing every script's own parameter shape.

    The ETF snapshot's semantic coverage (does it cover the pinned
    commit's own ETF_UNIVERSE, not just hash-match) is always checked --
    there is no way to opt out of it from this function's signature.
    """
    with offline_guard():
        try:
            with pinned_worktree(commit_hash, repo_root=repo_root) as worktree_path:
                expected_tickers = None

                # Only experiments that actually define ETF_UNIVERSE require the
                # semantic coverage check. Generic reproduction tests use simple
                # experiment.py modules that have no ETF universe.
                if experiment_module_relative_path == UNIVERSE_MODULE_RELATIVE_PATH:
                    try:
                        expected_tickers = _load_expected_tickers_from_worktree(worktree_path)
                    except ReproductionRunnerError as exc:
                        return ReproductionOutcome(
                            ReproductionStatus.UNVERIFIABLE,
                            str(exc),
                        )

                try:
                    reconstruct_database(
                        db_path=scratch_db_path,
                        migrations_dir=worktree_path / migrations_relative_path,
                        cycle_dir=cycle_dir,
                        manifest_path=dataset_manifest_path,
                        expected_tickers=expected_tickers,
                    )
                except MissingSnapshotArtifactError as exc:
                    return ReproductionOutcome(ReproductionStatus.UNVERIFIABLE, str(exc))
                except _DRIFT_ERRORS as exc:
                    return ReproductionOutcome(ReproductionStatus.DRIFTED, str(exc))
                except Exception as exc:  # noqa: BLE001 -- governed backstop: any other
                    # reconstruction-phase failure (a malformed dataset_manifest.json, a raw
                    # sqlite3.IntegrityError/ValueError a preflight check didn't name) still
                    # means an input didn't hold up -- DRIFTED, never a raw exception.
                    return ReproductionOutcome(ReproductionStatus.DRIFTED, str(exc))

                conn = connect(scratch_db_path)
                try:
                    before = snapshot_identity_state(conn)
                finally:
                    conn.close()

                try:
                    module = _load_module_from_worktree(worktree_path, experiment_module_relative_path)
                    run_experiment(module, scratch_db_path)
                except Exception as exc:  # noqa: BLE001 -- any failure during execution, including
                    # OfflineViolationError, means REPRODUCTION_FAILED: "the guard raising at all is
                    # itself an automatic REPRODUCTION_FAILED, not a silent pass" (amendment SS F.3).
                    return ReproductionOutcome(ReproductionStatus.REPRODUCTION_FAILED, str(exc))

                conn = connect(scratch_db_path)
                try:
                    after = snapshot_identity_state(conn)
                finally:
                    conn.close()

                try:
                    assert_frozen_identity_unchanged(before, after)
                except Exception as exc:  # noqa: BLE001
                    return ReproductionOutcome(ReproductionStatus.REPRODUCTION_FAILED, str(exc))
        except WorktreeError as exc:
            return ReproductionOutcome(ReproductionStatus.UNVERIFIABLE, str(exc))

    return ReproductionOutcome(
        ReproductionStatus.VERIFIED, "reproduction completed; frozen identities unchanged"
    )


def _run_experiment_entrypoint(module: ModuleType, db_path: Path) -> Any:
    """The one calling convention every pinned experiment script exposes
    (amendment SS F.2: "Run `run(db_path=<scratch path>, ...)` from the
    worktree's own copy of the experiment script")."""
    return module.run(db_path)


def _cli_main(argv: list[str] | None = None) -> int:
    """``python -m core.governance.reproduction_runner <cycle>``: run one
    reproduction attempt for a ``research_archive/<cycle>`` directory,
    resolving ``commit_hash`` from its own ``reproduction_record.json``
    and the dataset manifest from its own ``dataset_manifest.json`` --
    the two files Standard SS5 already places there. The experiment
    module's own path isn't part of either schema (and this fix does not
    add a field to invent one), so it is the one required flag."""
    parser = argparse.ArgumentParser(
        prog="python -m core.governance.reproduction_runner",
        description="Run one end-to-end reproduction attempt for a research_archive/<cycle> directory.",
    )
    parser.add_argument(
        "cycle",
        type=Path,
        help="path to the cycle directory (must contain reproduction_record.json and dataset_manifest.json)",
    )
    parser.add_argument(
        "--experiment-module",
        type=Path,
        required=True,
        help="path, relative to --repo-root, to the pinned commit's own experiment script (must expose run(db_path))",
    )
    parser.add_argument(
        "--migrations",
        type=Path,
        default=Path("migrations"),
        help="path, relative to --repo-root, to the migrations directory (default: migrations)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="repository root to resolve commit_hash against (default: this repository)",
    )
    parser.add_argument(
        "--scratch-db",
        type=Path,
        default=None,
        help="scratch database path (default: a fresh path under a new temp directory)",
    )
    args = parser.parse_args(argv)

    cycle_dir: Path = args.cycle
    record_path = cycle_dir / "reproduction_record.json"
    try:
        record_raw = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read {record_path}: {exc}", file=sys.stderr)
        return 2
    commit_hash = record_raw.get("commit_hash")
    if not commit_hash:
        print(f"error: {record_path} has no commit_hash", file=sys.stderr)
        return 2

    scratch_db_path = args.scratch_db
    if scratch_db_path is None:
        scratch_db_path = Path(tempfile.mkdtemp(prefix="reproduction_scratch_")) / "scratch.db"

    outcome = run_reproduction(
        repo_root=args.repo_root,
        cycle_dir=cycle_dir,
        dataset_manifest_path=cycle_dir / "dataset_manifest.json",
        migrations_relative_path=str(args.migrations),
        experiment_module_relative_path=str(args.experiment_module),
        commit_hash=commit_hash,
        scratch_db_path=scratch_db_path,
        run_experiment=_run_experiment_entrypoint,
    )

    print(f"{outcome.status.value}: {outcome.detail}")
    return 0 if outcome.status is ReproductionStatus.VERIFIED else 1


if __name__ == "__main__":
    raise SystemExit(_cli_main())
