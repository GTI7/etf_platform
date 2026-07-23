"""Import-direction boundary checker for ``core/``.

Enforces the cross-domain dependency table in
docs/PLATFORM_ARCHITECTURE_V1.md Section 5, using stdlib ``ast`` only
(AD-005: no third-party dependency for this or anything else). This is
the "Import-direction lint" the architecture document itself specifies
as one of the two enforcement mechanisms for domain boundaries (Section
5, "Enforcement", item 1).

Domain mapping. Each top-level package directly under ``core/`` is
assigned to one of the six architecture domains, or to the special
``"kernel"`` domain for the cross-cutting shared kernel (``core.shared``,
``core.domain``). The kernel is exempt from the dependency table only as
an import *target* -- every domain is allowed to depend on it, per
docs/ARCHITECTURE_DECISIONS.md AD-003/AD-007's existing "inject the
primitive, no domain owns it" pattern -- never as an import *source*: the
kernel may depend on nothing under ``core/`` (AD-049 part 5).

A top-level package under ``core/`` that is *not* in ``DOMAIN_OF_TOPLEVEL``
is a hard error (``UnmappedPackageError``), not a silent exemption
(AD-049 part 5): a new package must be classified before this checker can
run, so it cannot fall through unnoticed in either import direction.

``core.market_data`` and ``core.analytics`` are both mapped to the
``data`` domain. Per docs/RESEARCH_PLATFORM_MVP_MIGRATION_PLAN.md
Section 1, only ``core.analytics.persistence`` is formally Data-domain
code today; the rest of ``core.analytics`` (scoring/ranking business
logic) is "not yet a domain; stays product logic". Since Data is the
strictest domain in the table (it may depend on nothing else), folding
all of ``core.analytics`` into it for this checker is the conservative
simplification: it can only make the check stricter for that package's
non-persistence modules, never looser.

Usage:
    python -m tools.check_import_boundaries [core_root]

Exits 0 with no output if the tree is clean, or 1 and a violation
listing (one line per illegal import) if not -- suitable as a CI gate
once one is wired up; run today via ``tests/test_import_boundaries.py``.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CORE_ROOT = REPO_ROOT / "core"

# Top-level package name under core/ -> domain name, or "kernel" for the
# shared kernel (exempt from the dependency table as an import target
# only -- see ALLOWED_DEPENDENCIES["kernel"] below).
DOMAIN_OF_TOPLEVEL: dict[str, str] = {
    "market_data": "data",
    "analytics": "data",
    "statistics": "statistics",
    "governance": "governance",
    "validation": "validation",
    "research": "research",
    "reporting": "reporting",
    "shared": "kernel",
    "domain": "kernel",
}

# docs/PLATFORM_ARCHITECTURE_V1.md Section 5's allowed-dependency table.
# Same-domain imports are always allowed and are not listed here. The
# kernel is exempt as an import *target* for every domain (checked
# directly in check_repository, not via this table) but may itself
# depend on nothing under core/ -- AD-049 part 5.
ALLOWED_DEPENDENCIES: dict[str, frozenset[str]] = {
    "data": frozenset(),
    "statistics": frozenset(),
    "governance": frozenset({"data"}),
    "validation": frozenset({"data", "statistics", "governance"}),
    "research": frozenset({"data", "statistics", "governance", "validation"}),
    "reporting": frozenset({"data", "statistics", "governance", "validation", "research"}),
    "kernel": frozenset(),
}


class UnmappedPackageError(Exception):
    """Raised when a top-level package under ``core/`` is not present in
    ``DOMAIN_OF_TOPLEVEL``. AD-049 part 5: an unrecognized package must
    fail the check loudly rather than being silently exempted -- silent
    exemption was the escape hatch this tightening closes."""


@dataclass(frozen=True)
class Violation:
    file: Path
    lineno: int
    imported_module: str
    from_domain: str
    to_domain: str

    def __str__(self) -> str:
        return (
            f"{self.file}:{self.lineno}: domain '{self.from_domain}' may not import "
            f"'{self.imported_module}' (domain '{self.to_domain}') -- forbidden per "
            "docs/PLATFORM_ARCHITECTURE_V1.md Section 5"
        )


def _iter_python_files(core_root: Path):
    for path in sorted(core_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def _domain_of_file(path: Path, core_root: Path) -> str | None:
    relative_parts = path.relative_to(core_root).parts
    if len(relative_parts) < 2:
        return None  # core/__init__.py itself -- not inside any subpackage
    toplevel = relative_parts[0]
    if toplevel not in DOMAIN_OF_TOPLEVEL:
        raise UnmappedPackageError(
            f"core/{toplevel} is not in DOMAIN_OF_TOPLEVEL -- add it to the "
            "mapping (as a domain or as \"kernel\" for shared-kernel) before "
            "this checker can run"
        )
    return DOMAIN_OF_TOPLEVEL[toplevel]


def _domain_of_imported_module(dotted_module: str) -> str | None:
    parts = dotted_module.split(".")
    if len(parts) < 2 or parts[0] != "core":
        return None
    toplevel = parts[1]
    if toplevel not in DOMAIN_OF_TOPLEVEL:
        raise UnmappedPackageError(
            f"import target core.{toplevel} is not in DOMAIN_OF_TOPLEVEL -- "
            "add it to the mapping (as a domain or as \"kernel\") before "
            "this checker can run"
        )
    return DOMAIN_OF_TOPLEVEL[toplevel]


def _resolve_relative_import(file: Path, core_root: Path, node: ast.ImportFrom) -> str | None:
    """Resolve a relative ``ImportFrom`` (``node.level > 0``) found in
    `file` to its absolute dotted module string, e.g. ``'core.validation.
    gate'``. Returns None if the import climbs above ``core/`` itself
    (not resolvable to a core module; treated as out of scope rather than
    silently ignored, per AD-049 part 5's "resolved or rejected")."""
    relative_parts = list(file.relative_to(core_root).parts)
    # A module's own package is its parent directory; for `__init__.py`
    # that parent directory is also the package's own dotted name, so
    # dropping the filename gives the correct level=1 base in both cases.
    package_parts = relative_parts[:-1]

    base = ["core", *package_parts]
    climb = node.level - 1
    if climb:
        if climb >= len(base):
            return None
        base = base[: len(base) - climb]
    if node.module:
        base = base + node.module.split(".")
    return ".".join(base)


def _imported_core_modules(tree: ast.AST, file: Path, core_root: Path) -> list[tuple[str, int]]:
    """Every dotted module string of the form 'core...' referenced by an
    import in `tree` (absolute or relative), paired with its line number.
    Relative imports are resolved to their absolute target rather than
    skipped -- AD-049 part 5: a relative import must not be invisible to
    the checker."""
    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "core" or alias.name.startswith("core."):
                    found.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                if node.module and (node.module == "core" or node.module.startswith("core.")):
                    found.append((node.module, node.lineno))
            else:
                resolved = _resolve_relative_import(file, core_root, node)
                if resolved and (resolved == "core" or resolved.startswith("core.")):
                    found.append((resolved, node.lineno))
    return found


def check_repository(core_root: Path = DEFAULT_CORE_ROOT) -> list[Violation]:
    """Scan every ``.py`` file under `core_root` and return every import
    that violates docs/PLATFORM_ARCHITECTURE_V1.md Section 5's
    dependency table. Empty list means the tree is clean."""
    violations: list[Violation] = []
    for file in _iter_python_files(core_root):
        from_domain = _domain_of_file(file, core_root)
        if from_domain is None:
            continue  # core/__init__.py itself -- not inside any subpackage
        tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
        for dotted_module, lineno in _imported_core_modules(tree, file, core_root):
            to_domain = _domain_of_imported_module(dotted_module)
            if to_domain is None or to_domain == from_domain:
                continue
            if to_domain == "kernel":
                continue  # kernel is exempt as an import target for every domain
            if to_domain not in ALLOWED_DEPENDENCIES.get(from_domain, frozenset()):
                violations.append(
                    Violation(
                        file=file.relative_to(REPO_ROOT) if file.is_relative_to(REPO_ROOT) else file,
                        lineno=lineno,
                        imported_module=dotted_module,
                        from_domain=from_domain,
                        to_domain=to_domain,
                    )
                )
    return violations


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    core_root = Path(argv[0]).resolve() if argv else DEFAULT_CORE_ROOT
    violations = check_repository(core_root)
    if not violations:
        print(f"Import boundary check passed: no violations found under {core_root}")
        return 0
    print(f"Import boundary check FAILED: {len(violations)} violation(s) found under {core_root}")
    for violation in violations:
        print(f"  {violation}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
