"""Reproduction runner (Phase 4 Architecture Amendment v1.1 SS D-F): the
one place that ties the offline guard, the pinned-worktree execution
model, the reconstruction loader, and the post-run frozen-identity check
together into a single reproduction attempt.

The offline guard installs before this function does anything else --
in particular, before the pinned commit's own experiment module is
imported -- so it is active for the entire attempt, not scoped to one
construction call (SS E).

Migrations, dataset snapshots, and the experiment *script* all come from
the pinned commit's own worktree, never from `repo_root`'s current HEAD
copy (SS F.2: "the dataset artifacts for a given cycle are committed
alongside methodology.md at freeze time... commit_hash pins code and
data together; nothing needs to reach outside the worktree").

That isolation covers the script's own source and nothing more. The
``core.*`` modules the pinned script *imports* resolve through **HEAD's**
package, not the worktree's: this module is itself
``core.governance.reproduction_runner``, so ``sys.modules['core']`` is
already populated by the time the pinned script runs, and Python
resolves ``core.…`` through HEAD's ``core.__path__`` regardless of the
``sys.path`` insertion in ``_load_module_from_worktree``. There is no
``sys.modules`` isolation anywhere in ``core/``. AD-069 records this as
a pre-existing property that the legacy re-export shims now depend on;
``test_legacy_import_from_a_foreign_worktree_still_binds_core_store``
(T-2) pins the real behaviour.

Status mapping follows the base proposal's SS 2.2 semantics exactly:
a missing/unresolvable artifact (including an unresolvable commit_hash,
and a pinned import that no longer resolves) is ``UNVERIFIABLE``; an
input that doesn't match its claimed hash/shape is ``DRIFTED``; every
input matching but the run itself failing (including the offline guard
tripping) is ``REPRODUCTION_FAILED``; everything holding is ``VERIFIED``.

Both pre-run phases are fully governed -- no raw exception from either
escapes this function:

* the **pinned-universe preload** (``_load_expected_tickers_from_worktree``)
  maps a worktree file that cannot be read *or imported* to
  ``UNVERIFIABLE``. ``ImportError``/``ModuleNotFoundError`` is not an
  ``OSError`` subclass, so it needs its own clause; without it, deleting
  a module a pinned script imports would crash the runner with no
  governed status at all (AD-069's disclosed open item);
* the **reconstruction phase** (dataset/manifest loading, pinned
  ETF_UNIVERSE coverage) maps every specifically-named reconstruction
  error to its own status below. ``ImportError``/``ModuleNotFoundError``
  there means the pinned commit's own reconstruction code cannot be
  loaded -- an unresolvable artifact, so ``UNVERIFIABLE``, not the
  archived data's fault. Anything else -- ``sqlite3.IntegrityError``, a
  ``ValueError`` from a malformed snapshot row a preflight check didn't
  name -- still means an input didn't hold up, so it is governed as
  ``DRIFTED``, never left as a raw exception.

The **execution phase** is deliberately not part of that carve-out: once
reconstruction has succeeded, any exception out of the pinned module's
own load-and-run -- ``ImportError`` included -- is
``REPRODUCTION_FAILED``. Remapping a load-time ``ImportError`` there
would change what ``REPRODUCTION_FAILED`` means and is a separate
decision (Phase F gate review SS 3.3).

**This module is a library, not an entry point** (Engine Boundary
cleanup item C4, 2026-07-27). Its ``python -m
core.governance.reproduction_runner`` CLI moved to
``tools/reproduce_cycle.py`` and the invocation is now ``python -m
tools.reproduce_cycle``. Behaviour is unchanged; the reason is that a CLI
must *choose* the ``parse_row``/``load_rows`` implementations
``reconstruct_database`` now requires, and choosing the ETF workload's
implementations inside Governance would reinstate the ``governance ->
etf`` edge (AD-068 decision 2) that C4 exists to remove.
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

from core.governance.identity_verification import (
    assert_frozen_identity_unchanged,
    snapshot_identity_state,
)
from core.governance.network_guard import offline_guard
from core.governance.pinned_worktree import WorktreeError, pinned_worktree
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
    RowParser,
    SnapshotRowLoader,
    UnknownEtfCalendarError,
    UnknownTradingSessionCalendarError,
    reconstruct_database,
)
from core.governance.reproduction_record import ReproductionStatus
from core.store.connection import connect

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
    except (OSError, ImportError) as exc:
        # spec_from_file_location() does not itself fail for a path that
        # doesn't exist -- the failure only surfaces once exec_module()
        # tries to read it. A pinned commit that predates this file (or
        # never had it) is a missing/unresolvable artifact, not a runner
        # crash. ImportError/ModuleNotFoundError -- raised when the pinned
        # script imports a module HEAD no longer provides -- is the same
        # kind of unresolvable artifact, and is *not* an OSError subclass,
        # so it needs naming here rather than riding along.
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
    parse_row: RowParser,
    load_rows: SnapshotRowLoader,
) -> ReproductionOutcome:
    """Run one full reproduction attempt end-to-end.

    `run_experiment(module, scratch_db_path)` is the caller-supplied call
    into the pinned module's own `run()` entrypoint -- every existing
    `experiments/validate_*.py` script's signature differs slightly
    (universe, session_date, ...), so the exact call is the caller's
    responsibility; this function's job is guaranteeing the module and
    migrations come from the pinned worktree and every frozen input has
    already been verified, not knowing every script's own parameter shape.

    `parse_row` and `load_rows` are the same kind of parameter for the
    same kind of reason, added by Engine Boundary cleanup item C4: this
    function verifies frozen inputs and never constructs the workload's
    objects. They are passed straight through to `reconstruct_database`
    -- see `core.governance.reconstruction_loader` for their contracts.

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
                        parse_row=parse_row,
                        load_rows=load_rows,
                        expected_tickers=expected_tickers,
                    )
                except MissingSnapshotArtifactError as exc:
                    return ReproductionOutcome(ReproductionStatus.UNVERIFIABLE, str(exc))
                except ImportError as exc:
                    # A module the reconstruction path needs no longer resolves
                    # (ModuleNotFoundError included). The archived inputs are not
                    # at fault, so this is an unresolvable artifact, not DRIFTED
                    # -- it must not fall through to the backstop below.
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
