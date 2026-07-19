"""Import-direction boundary checker for ``core/``.

Enforces the cross-domain dependency table in
docs/PLATFORM_ARCHITECTURE_V1.md Section 5, using stdlib ``ast`` only
(AD-005: no third-party dependency for this or anything else). This is
the "Import-direction lint" the architecture document itself specifies
as one of the two enforcement mechanisms for domain boundaries (Section
5, "Enforcement", item 1).

Domain mapping. Each top-level package directly under ``core/`` is
assigned to one of the six architecture domains, or to ``None`` for the
cross-cutting shared kernel (``core.shared``, ``core.domain``), which
is exempt from the dependency table entirely -- every domain is allowed
to depend on it, per docs/ARCHITECTURE_DECISIONS.md AD-003/AD-007's
existing "inject the primitive, no domain owns it" pattern.

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

# Top-level package name under core/ -> domain name, or None for the
# shared kernel (exempt from the dependency table).
DOMAIN_OF_TOPLEVEL: dict[str, str | None] = {
    "market_data": "data",
    "analytics": "data",
    "statistics": "statistics",
    "governance": "governance",
    "validation": "validation",
    "research": "research",
    "reporting": "reporting",
    "shared": None,
    "domain": None,
}

# docs/PLATFORM_ARCHITECTURE_V1.md Section 5's allowed-dependency table.
# Same-domain imports are always allowed and are not listed here.
ALLOWED_DEPENDENCIES: dict[str, frozenset[str]] = {
    "data": frozenset(),
    "statistics": frozenset(),
    "governance": frozenset({"data"}),
    "validation": frozenset({"data", "statistics", "governance"}),
    "research": frozenset({"data", "statistics", "governance", "validation"}),
    "reporting": frozenset({"data", "statistics", "governance", "validation", "research"}),
}


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
    return DOMAIN_OF_TOPLEVEL.get(relative_parts[0])


def _domain_of_imported_module(dotted_module: str) -> str | None:
    parts = dotted_module.split(".")
    if len(parts) < 2 or parts[0] != "core":
        return None
    return DOMAIN_OF_TOPLEVEL.get(parts[1])


def _imported_core_modules(tree: ast.AST) -> list[tuple[str, int]]:
    """Every dotted module string of the form 'core...' referenced by an
    absolute import in `tree`, paired with its line number. Relative
    imports (``level > 0``) are not resolved -- none exist under core/
    today (verified by direct inspection), and a relative import can
    never cross a top-level package boundary in a way this checker
    would need to catch beyond what its own directory already implies.
    """
    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "core" or alias.name.startswith("core."):
                    found.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module and (node.module == "core" or node.module.startswith("core.")):
                found.append((node.module, node.lineno))
    return found


def check_repository(core_root: Path = DEFAULT_CORE_ROOT) -> list[Violation]:
    """Scan every ``.py`` file under `core_root` and return every import
    that violates docs/PLATFORM_ARCHITECTURE_V1.md Section 5's
    dependency table. Empty list means the tree is clean."""
    violations: list[Violation] = []
    for file in _iter_python_files(core_root):
        from_domain = _domain_of_file(file, core_root)
        if from_domain is None:
            continue  # shared kernel or unrecognized top-level package -- exempt
        tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
        for dotted_module, lineno in _imported_core_modules(tree):
            to_domain = _domain_of_imported_module(dotted_module)
            if to_domain is None or to_domain == from_domain:
                continue
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
