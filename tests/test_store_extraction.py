"""Invariants for the ``core.store`` storage substrate (AD-069).

Boundary-hardening step 2 moved ``connect()`` and ``run_migrations()`` out
of ``core/market_data/persistence/`` -- the Data domain -- into a neutral
``core.store`` package. Neither primitive has ever had any market-data
content; they lived there only because market_data was the first package
that needed a database.

The move could not be a clean delete. The old modules survive as
re-export shims, and they are **permanent** (AD-069). Their primary
reason is not hash protection but pinned-commit module resolution: a
pinned experiment script's legacy import resolves through HEAD's
``core.__path__`` and binds the shim, so the shims are live runtime
infrastructure for reproduction. Hash protection -- eight
``experiments/*.py`` scripts and
``maintenance/remediate_h3_invalid_pricebar_rows.py``, which may not have
their import lines edited -- is the secondary reason.

These tests hold the properties that make that survivable: the substrate
stays neutral, the shims stay dead to every non-frozen caller, and the
retirement condition stays mechanically enforced against **pinned
commits** rather than against the current working tree alone.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

import core.market_data.persistence.database as legacy_database
import core.market_data.persistence.migrations as legacy_migrations
from core.store.connection import connect
from core.store.migrations import run_migrations

REPO_ROOT = Path(__file__).resolve().parent.parent
STORE_ROOT = REPO_ROOT / "core" / "store"
PROTECTED_HASHES = REPO_ROOT / "tests" / "fixtures" / "protected_file_hashes.json"
RESEARCH_ARCHIVE = REPO_ROOT / "research_archive"

LEGACY_SHIM_MODULES = frozenset(
    {
        "core.market_data.persistence.database",
        "core.market_data.persistence.migrations",
    }
)
# Files whose import of a shim is not a *use* of it: the shims themselves
# (their re-export line) and this module (whose import is the identity
# assertion below). Everything else that imports a shim is a real caller.
NOT_A_CALLER = frozenset(
    {
        Path("core/market_data/persistence/database.py"),
        Path("core/market_data/persistence/migrations.py"),
        Path("tests/test_store_extraction.py"),
    }
)


def _python_files() -> list[Path]:
    skip_dirs = {"__pycache__", ".git", ".pytest_cache"}
    return [
        path
        for path in sorted(REPO_ROOT.rglob("*.py"))
        if not skip_dirs.intersection(path.parts)
    ]


def _imported_modules(path: Path) -> set[str]:
    """Every dotted module name an import statement in `path` names. AST,
    not text search: a module path quoted inside a test fixture string is
    not an import and must not count as one."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module)
    return modules


def _frozen_python_files() -> set[str]:
    hashes = json.loads(PROTECTED_HASHES.read_text(encoding="utf-8"))
    return {name for name in hashes if name.endswith(".py")}


def _archived_commit_pins() -> dict[str, str]:
    """Every archived cycle's pinned commit, keyed by cycle name. These
    are the commits ``core/governance/reproduction_runner.py`` checks out
    and executes, and they are immutable."""
    return {
        pin.parent.name: pin.read_text(encoding="utf-8").strip()
        for pin in sorted(RESEARCH_ARCHIVE.glob("*/COMMIT.txt"))
    }


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _pinned_commit_imports_a_legacy_path(commit: str) -> bool | None:
    """Whether `commit`'s own tree contains an import of either legacy
    storage path. Returns None if the commit cannot be resolved, so an
    unresolvable pin is reported as unknown rather than as "clean" --
    the safe direction for a test that gates a deletion."""
    listing = _git("ls-tree", "-r", "--name-only", commit)
    if listing.returncode != 0:
        return None
    for name in listing.stdout.splitlines():
        if not name.endswith(".py"):
            continue
        blob = _git("show", f"{commit}:{name}")
        if blob.returncode != 0:
            continue
        if any(module in blob.stdout for module in LEGACY_SHIM_MODULES):
            return True
    return False


# --- the substrate is neutral ------------------------------------------


def test_store_imports_nothing_from_core() -> None:
    """Stricter than the import-direction checker, which exempts the
    shared kernel as a target for every domain. ``core.store`` is the
    bottom of the stack: it depends on the stdlib and on nothing this
    repository defines, kernel included."""
    offenders = {
        path.relative_to(REPO_ROOT).as_posix(): sorted(
            module for module in _imported_modules(path) if module.split(".")[0] == "core"
        )
        for path in sorted(STORE_ROOT.rglob("*.py"))
    }
    assert {file: imports for file, imports in offenders.items() if imports} == {}


def test_store_holds_only_the_two_primitives() -> None:
    """"Storage primitives only" is the whole scope of AD-069. A third
    module appearing here means something with domain content -- a
    repository, a dataset abstraction -- is being smuggled into the
    substrate, and needs its own decision first."""
    modules = sorted(
        path.stem for path in STORE_ROOT.glob("*.py") if path.name != "__init__.py"
    )
    assert modules == ["connection", "migrations"]


# --- the shims are dead to everything but the frozen scripts -----------


def test_shims_re_export_the_moved_objects_themselves() -> None:
    """Identity, not equivalence: the frozen scripts must get the exact
    object the live code gets, so behavior cannot drift between the two
    import paths."""
    assert legacy_database.connect is connect
    assert legacy_migrations.run_migrations is run_migrations


def test_legacy_shim_importers_are_exactly_the_frozen_files() -> None:
    """No live code imports the old paths, and the shims are still needed
    by -- and only by -- files that cannot be edited."""
    importers = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in _python_files()
        if path.relative_to(REPO_ROOT) not in NOT_A_CALLER
        and LEGACY_SHIM_MODULES.intersection(_imported_modules(path))
    }

    frozen = _frozen_python_files()
    assert importers <= frozen, (
        "these files still import the pre-AD-069 storage paths and are not "
        f"hash-protected, so they can and must be repointed at core.store: "
        f"{sorted(importers - frozen)}"
    )
    assert importers, (
        "No file in the working tree imports the shims any more. That is "
        "retirement condition (a) of AD-069, and it is NOT sufficient. "
        "Condition (b) -- no reproducible commit imports either legacy "
        "path -- is the binding one, and "
        "test_pinned_commits_still_require_the_shims is what checks it. "
        "Deleting the shims on the strength of this assertion alone "
        "converts every archived cycle's reproduction into an uncaught "
        "runner crash, silently, with a green suite. See AD-069."
    )


def test_shim_public_surface_is_exactly_one_name() -> None:
    """T-8. Each shim re-exports one name and defines nothing else.

    ``__all__`` is declarative and enforces nothing -- a shim could
    regrow a helper, a constant, or a second re-export and no existing
    test would notice. The module-level surface is checked from the AST
    rather than from ``dir()`` so that the imported name itself is the
    only thing that can appear."""
    expected = {
        "core/market_data/persistence/database.py": "connect",
        "core/market_data/persistence/migrations.py": "run_migrations",
    }
    for relative_path, name in expected.items():
        tree = ast.parse(
            (REPO_ROOT / relative_path).read_text(encoding="utf-8"),
            filename=relative_path,
        )
        bound: set[str] = set()
        assignments: set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                bound.update(
                    alias.asname or alias.name
                    for alias in node.names
                    if node.module != "__future__"
                )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                bound.add(node.name)
            elif isinstance(node, ast.Assign):
                assignments.update(
                    target.id for target in node.targets if isinstance(target, ast.Name)
                )

        assert bound == {name}, (
            f"{relative_path} must re-export exactly '{name}' and define nothing "
            f"else; found {sorted(bound)}. A shim that regrows logic is no longer "
            "a shim, and the frozen scripts would silently get different behavior "
            "from the live code."
        )
        assert assignments <= {"__all__"}, (
            f"{relative_path} defines module-level names beyond __all__: "
            f"{sorted(assignments - {'__all__'})}"
        )


def test_legacy_import_from_a_foreign_worktree_still_binds_core_store(tmp_path: Path) -> None:
    """T-2. The reproduction path, made executable.

    ``reproduction_runner._load_module_from_worktree`` prepends a pinned
    worktree to ``sys.path`` and ``exec_module``'s the pinned script. But
    ``sys.modules['core']`` is already populated with HEAD's package, so
    ``core.market_data.persistence.database`` resolves through **HEAD's**
    ``core.__path__`` and binds HEAD's shim -- never the worktree's own
    copy, whatever ``sys.path`` says.

    This test reproduces that exactly: a synthetic worktree containing
    its own, differently-behaving copy of the legacy module is placed at
    ``sys.path[0]``, and a module performing the legacy import is loaded
    the same way the runner loads one. The bound ``connect`` must be
    ``core.store.connection.connect`` and the worktree's marker must be
    absent.

    The existing shim tests cover *static* importers. This covers the
    dynamic exec path, which is the one AD-069 calls the shims' primary
    reason for existing -- and the one whose failure mode is an uncaught
    runner crash rather than a governed status."""
    worktree = tmp_path / "pinned_worktree"
    shim_dir = worktree / "core" / "market_data" / "persistence"
    shim_dir.mkdir(parents=True)
    for package_dir in (
        worktree / "core",
        worktree / "core" / "market_data",
        shim_dir,
    ):
        (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (shim_dir / "database.py").write_text(
        "WORKTREE_MARKER = 'this is the worktree copy, not HEAD'\n"
        "def connect(db_path):\n"
        "    raise AssertionError('the worktree copy must never be bound')\n",
        encoding="utf-8",
    )

    pinned_script = worktree / "pinned_experiment.py"
    pinned_script.write_text(
        "from core.market_data.persistence.database import connect\n"
        "import core.market_data.persistence.database as bound_module\n",
        encoding="utf-8",
    )

    spec = importlib.util.spec_from_file_location(pinned_script.stem, pinned_script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(worktree))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(worktree))

    assert module.connect is connect, (
        "a pinned script's legacy import did not bind core.store.connection.connect. "
        "The shims are the mechanism that makes archived cycles reproducible "
        "against HEAD -- see AD-069."
    )
    assert not hasattr(module.bound_module, "WORKTREE_MARKER"), (
        "the worktree's own copy of the legacy module was bound, which "
        "contradicts the sys.modules resolution AD-069 records"
    )


def test_pinned_commits_still_require_the_shims() -> None:
    """T-3. Retirement condition (b) of AD-069, made mechanical.

    The shims may be deleted only when *no reproducible commit* imports a
    legacy storage path. ``reproduction_runner`` executes pinned code
    against HEAD's ``core`` package -- ``sys.modules['core']`` is already
    populated, so a pinned script's legacy import resolves through HEAD's
    ``core.__path__`` and binds HEAD's shim, whatever ``sys.path`` says.
    A pinned commit that imports a legacy path therefore depends on the
    shim existing *at HEAD*, and pinned history is immutable.

    This test refuses the deletion premise while any pin still does so.
    It is the executable half of a condition that would otherwise be
    prose in an ADR and a docstring."""
    pins = _archived_commit_pins()
    assert pins, "expected at least one archived cycle with a COMMIT.txt pin"

    if _git("rev-parse", "--git-dir").returncode != 0:
        pytest.skip("not a git worktree; pinned commits cannot be resolved")

    verdicts = {cycle: _pinned_commit_imports_a_legacy_path(commit) for cycle, commit in pins.items()}
    unresolvable = sorted(cycle for cycle, verdict in verdicts.items() if verdict is None)
    if unresolvable:
        pytest.skip(f"pinned commits not present in this clone: {unresolvable}")

    requiring = sorted(cycle for cycle, verdict in verdicts.items() if verdict)
    assert requiring, (
        "No archived cycle's pinned commit imports a legacy storage path "
        "any more. Retirement condition (b) of AD-069 may now be "
        "satisfiable -- but deletion is a governance act requiring a NEW "
        "ADR that records which archived cycles were re-verified after "
        "deletion and by whom. A green suite is necessary and not "
        "sufficient. Do not delete the shims on the strength of this test."
    )
