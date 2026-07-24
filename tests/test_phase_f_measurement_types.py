"""Phase F F-1 -- measurement types (docs/ARCHITECTURE_DECISIONS.md
AD-061, AD-064; condition F-C2). Pins the closed field sets of
`ExperimentSpec` and `MeasurementBundle`, that both are frozen, the
closed serialized-payload key set `ExperimentSpec` + `MeasurementBundle`
-> `dict` produces and its key *order*, and that the new
`core/research/execution/` modules import nothing from outside their own
package -- the Proposal's F-1 exit criterion is "no domain import"
(docs/PHASE_4_PHASE_F_RESEARCH_EXECUTION_ENGINE_PROPOSAL.md:1058), and
these modules import each other by type the same way
`core.validation.gate` imports `GateContext`/`GateResult` and
`core.reporting.json_renderer` imports `ReportModel`.

B1 only: no `ResearchRunner`, no `GateContext` assembly, no
`ArchiveWriter`, no reproduction integration, no dataset manifest logic,
no CLI, no ETF experiment. Those are later Phase F increments."""

from __future__ import annotations

import ast
import dataclasses
import typing
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from core.research.execution.experiment import Experiment, ExperimentSpec
from core.research.execution.measurement_bundle import MeasurementBundle
from core.research.execution.measurement_serialization import serialize_measurement_artifact

EXECUTION_PACKAGE_DIR = Path(__file__).resolve().parent.parent / "core" / "research" / "execution"

FORBIDDEN_MEASUREMENT_BUNDLE_FIELDS = {
    "status",
    "verdict",
    "threshold",
    "criterion",
    "direction",
    "summary",
    "notes",
    "rationale",
    "code_revision",
    "code_commit_hash",
}


def _make_spec(**overrides: object) -> ExperimentSpec:
    defaults: dict[str, object] = {
        "project_id": "golden_run_001",
        "as_of": datetime(2026, 7, 24, 12, 0, 0, tzinfo=timezone.utc),
        "parameters": {"universe": "sp500", "scoring_profile": "default"},
        "code_revision": "c" * 40,
    }
    defaults.update(overrides)
    return ExperimentSpec(**defaults)  # type: ignore[arg-type]


def _make_bundle(**overrides: object) -> MeasurementBundle:
    defaults: dict[str, object] = {
        "experiment_name": "golden_run_001_ranking",
        "measurements": {"sharpe": Decimal("1.50")},
        "evidence_refs": ("experiment_results/measurements_20260724T120000Z.jsonl",),
        "dataset_refs": ("dataset_hashes/etf_20260724T120000Z.jsonl",),
        "provenance_ref": None,
    }
    defaults.update(overrides)
    return MeasurementBundle(**defaults)  # type: ignore[arg-type]


# --- 1. MeasurementBundle exact field set ---------------------------------


def test_measurement_bundle_has_exactly_five_fields() -> None:
    """Closed field set (AD-064): adding a field must fail this test and
    force a new AD, never land as a quiet addition."""
    field_names = {f.name for f in dataclasses.fields(MeasurementBundle)}
    assert field_names == {
        "experiment_name",
        "measurements",
        "evidence_refs",
        "dataset_refs",
        "provenance_ref",
    }


# --- 2. ExperimentSpec exact field set -------------------------------------


def test_experiment_spec_has_exactly_four_fields() -> None:
    """Closed field set (AD-061, AD-064): the code revision reference
    lives here, never on `MeasurementBundle`."""
    field_names = {f.name for f in dataclasses.fields(ExperimentSpec)}
    assert field_names == {"project_id", "as_of", "parameters", "code_revision"}


# --- 3. Forbidden fields cannot appear --------------------------------------


def test_measurement_bundle_forbidden_fields_absent() -> None:
    field_names = {f.name for f in dataclasses.fields(MeasurementBundle)}
    assert field_names.isdisjoint(FORBIDDEN_MEASUREMENT_BUNDLE_FIELDS)


# --- 3b. Both records are frozen --------------------------------------------


def test_measurement_bundle_is_frozen() -> None:
    bundle = _make_bundle()
    with pytest.raises(dataclasses.FrozenInstanceError):
        bundle.experiment_name = "rewritten"  # type: ignore[misc]


def test_experiment_spec_is_frozen() -> None:
    spec = _make_spec()
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.code_revision = "d" * 40  # type: ignore[misc]


# --- Experiment is a Protocol only, no implementation -----------------------


def test_experiment_is_a_structural_protocol() -> None:
    assert typing.Protocol in Experiment.__mro__
    assert getattr(Experiment, "_is_protocol", False) is True


# --- 4. Serialized payload exact key set ------------------------------------


def test_serialized_payload_has_exactly_the_ad_061_key_set() -> None:
    payload = serialize_measurement_artifact(_make_spec(), _make_bundle())
    assert set(payload) == {
        "experiment_name",
        "as_of",
        "parameters",
        "measurements",
        "evidence_refs",
        "dataset_refs",
        "provenance_ref",
        "code_revision",
    }


def test_serialized_payload_has_no_project_id_key() -> None:
    """AD-061 lists the artifact's minimum field set without `project_id`
    -- the project is already named by the archive path (AD-062), not
    duplicated in the payload."""
    payload = serialize_measurement_artifact(_make_spec(), _make_bundle())
    assert "project_id" not in payload


# --- 5. Decimal serialization -----------------------------------------------


def test_measurement_decimals_serialize_as_strings_not_floats() -> None:
    bundle = _make_bundle(measurements={"sharpe": Decimal("1.50"), "sortino": Decimal("2")})
    payload = serialize_measurement_artifact(_make_spec(), bundle)
    assert payload["measurements"] == {"sharpe": "1.50", "sortino": "2"}
    assert all(isinstance(v, str) for v in payload["measurements"].values())


# --- 6. Datetime serialization ----------------------------------------------


def test_as_of_serializes_to_a_deterministic_isoformat_string() -> None:
    spec = _make_spec(as_of=datetime(2026, 7, 24, 12, 0, 0, tzinfo=timezone.utc))
    payload_a = serialize_measurement_artifact(spec, _make_bundle())
    payload_b = serialize_measurement_artifact(spec, _make_bundle())
    assert payload_a["as_of"] == "2026-07-24T12:00:00+00:00"
    assert payload_a["as_of"] == payload_b["as_of"]


def test_as_of_is_serialized_verbatim_with_no_utc_normalization() -> None:
    """B1 normalizes no timezone and refuses no naive instant -- it has
    no clock to normalize against. AD-061 (R-7) places the naive-instant
    refusal at the injected clock (`core/shared/clock.py:19`), which
    `ResearchRunner` reads at F-2. This pins the non-claim so a later
    reader cannot mistake the UTC fixtures above for normalization."""
    offset_spec = _make_spec(
        as_of=datetime(2026, 7, 24, 14, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    )
    naive_spec = _make_spec(as_of=datetime(2026, 7, 24, 12, 0, 0))
    offset_payload = serialize_measurement_artifact(offset_spec, _make_bundle())
    naive_payload = serialize_measurement_artifact(naive_spec, _make_bundle())

    assert offset_payload["as_of"] == "2026-07-24T14:00:00+02:00"
    assert naive_payload["as_of"] == "2026-07-24T12:00:00"


# --- 7. Explicit None/null preservation -------------------------------------


def test_none_provenance_and_code_revision_are_preserved_not_omitted() -> None:
    spec = _make_spec(code_revision=None)
    bundle = _make_bundle(provenance_ref=None)
    payload = serialize_measurement_artifact(spec, bundle)
    assert "provenance_ref" in payload
    assert payload["provenance_ref"] is None
    assert "code_revision" in payload
    assert payload["code_revision"] is None


# --- 8. Parameters preserved unchanged --------------------------------------


def test_parameters_are_preserved_unchanged() -> None:
    parameters = {"universe": "sp500", "scoring_profile": "default", "session_date": "2026-07-20"}
    spec = _make_spec(parameters=parameters)
    payload = serialize_measurement_artifact(spec, _make_bundle())
    assert payload["parameters"] == parameters


def test_parameter_serialization_is_independent_of_input_mapping_order() -> None:
    """Key *order*, not just key/value equality: `dict.__eq__` ignores
    insertion order, so an equality assertion alone would pass on an
    unsorted serializer and prove nothing about determinism."""
    spec_a = _make_spec(parameters={"b": "2", "a": "1"})
    spec_b = _make_spec(parameters={"a": "1", "b": "2"})
    bundle_a = _make_bundle(measurements={"sortino": Decimal("2"), "sharpe": Decimal("1.50")})
    bundle_b = _make_bundle(measurements={"sharpe": Decimal("1.50"), "sortino": Decimal("2")})
    payload_a = serialize_measurement_artifact(spec_a, bundle_a)
    payload_b = serialize_measurement_artifact(spec_b, bundle_b)

    assert list(payload_a["parameters"].items()) == [("a", "1"), ("b", "2")]
    assert list(payload_a["parameters"].items()) == list(payload_b["parameters"].items())
    assert list(payload_a["measurements"].items()) == [("sharpe", "1.50"), ("sortino", "2")]
    assert list(payload_a["measurements"].items()) == list(payload_b["measurements"].items())


def test_evidence_and_dataset_refs_preserve_order_not_sorted() -> None:
    bundle = _make_bundle(
        evidence_refs=("z_ref.jsonl", "a_ref.jsonl"),
        dataset_refs=("z_dataset.jsonl", "a_dataset.jsonl"),
    )
    payload = serialize_measurement_artifact(_make_spec(), bundle)
    assert payload["evidence_refs"] == ["z_ref.jsonl", "a_ref.jsonl"]
    assert payload["dataset_refs"] == ["z_dataset.jsonl", "a_dataset.jsonl"]


# --- 9. New execution modules import nothing outside their own package ------

EXECUTION_PACKAGE = "core.research.execution"


def _execution_py_files() -> list[Path]:
    """Every `.py` file in the package, **recursively** -- a plain
    `glob("*.py")` would leave a nested subpackage entirely unscanned,
    and this test is the only thing standing behind the import claim.
    `__pycache__` is skipped the same way
    `tools/check_import_boundaries.py:_iter_python_files` skips it."""
    return sorted(
        path
        for path in EXECUTION_PACKAGE_DIR.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def _resolve_import_from(module_file: Path, node: ast.ImportFrom) -> str:
    """Absolute dotted target of an `ImportFrom`, resolving relative
    imports (`node.level > 0`) against `module_file`'s own package.
    A relative import must not be invisible to this check -- reading only
    `node.module` would score `from .measurement_bundle import X` as the
    non-core name `"measurement_bundle"`, and `from . import X` (whose
    `node.module` is `None`) as nothing at all. Same resolution rule as
    `tools/check_import_boundaries.py:_resolve_relative_import`."""
    if not node.level:
        return node.module or ""
    base = list(module_file.parent.relative_to(EXECUTION_PACKAGE_DIR).parts)
    base = [*EXECUTION_PACKAGE.split("."), *base]
    climb = node.level - 1
    if climb:
        base = base[: max(len(base) - climb, 0)]
    return ".".join([*base, *(node.module.split(".") if node.module else [])])


def _imported_module_names(module_file: Path) -> set[str]:
    tree = ast.parse(module_file.read_text(encoding="utf-8"))
    names = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    names |= {
        _resolve_import_from(module_file, node)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    return {name for name in names if name}


def test_execution_modules_import_nothing_outside_their_own_package() -> None:
    """The claim is exactly this: no import of any `core` module outside
    `core.research.execution`. Intra-package imports by type are the
    repository's existing shape for a Protocol and a renderer
    (`core/validation/gate.py:23-24`, `core/reporting/json_renderer.py:14`)
    and are not violations; a cross-domain import is."""
    py_files = _execution_py_files()
    assert {str(p.relative_to(EXECUTION_PACKAGE_DIR).as_posix()) for p in py_files} == {
        "__init__.py",
        "experiment.py",
        "measurement_bundle.py",
        "measurement_serialization.py",
    }
    for py_file in py_files:
        imported = _imported_module_names(py_file)
        outside_package = {
            name
            for name in imported
            if (name == "core" or name.startswith("core."))
            and not (name == EXECUTION_PACKAGE or name.startswith(EXECUTION_PACKAGE + "."))
        }
        assert not outside_package, (
            f"{py_file.name} imports outside {EXECUTION_PACKAGE}: {outside_package}"
        )
