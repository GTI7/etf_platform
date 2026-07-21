"""``dataset_manifest.json`` schema v3 (Phase 4 Architecture Amendment
v1.1 SS C). Exactly three dataset entries -- ``ETF``, ``PriceBar``,
``TradingSession``, identified by their ``source_table`` field.
``Calendar`` is deliberately excluded (SS A.4): it is a code-defined
literal, not a frozen dataset -- see ``core.governance.calendar_definitions``.

Every entry's own ``schema_version`` is independent of the manifest's
top-level ``schema_version`` -- the same non-conflation discipline
already established for ``archive_manifest.json`` vs.
``dataset_manifest.json`` (``tools/archive_manifest.py``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MANIFEST_SCHEMA_VERSION = 3

REQUIRED_SOURCE_TABLES = frozenset({"ETF", "PriceBar", "TradingSession"})

_REQUIRED_ENTRY_FIELDS = (
    "dataset_id",
    "type",
    "source_table",
    "row_count",
    "snapshot_path",
    "content_hash",
    "schema_version",
)


class DatasetManifestError(RuntimeError):
    """A governance-quality error for a structurally invalid
    dataset_manifest.json -- never a raw KeyError/TypeError surfacing
    from partial parsing."""


@dataclass(frozen=True, slots=True)
class DatasetEntry:
    dataset_id: str
    type: str
    source_table: str
    row_count: int
    snapshot_path: str
    content_hash: str
    schema_version: int


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    schema_version: int
    project_id: str
    generated_at: str
    datasets: tuple[DatasetEntry, ...]


def _parse_entry(raw: dict[str, Any], index: int) -> DatasetEntry:
    missing = [field for field in _REQUIRED_ENTRY_FIELDS if field not in raw]
    if missing:
        raise DatasetManifestError(f"datasets[{index}] is missing required field(s): {missing}")
    content_hash = str(raw["content_hash"])
    if not content_hash.startswith("sha256:"):
        raise DatasetManifestError(
            f"datasets[{index}] ({raw['dataset_id']!r}).content_hash must be prefixed 'sha256:', "
            f"got {content_hash!r} -- the algorithm is always explicit, never a silent default"
        )
    return DatasetEntry(
        dataset_id=raw["dataset_id"],
        type=raw["type"],
        source_table=raw["source_table"],
        row_count=raw["row_count"],
        snapshot_path=raw["snapshot_path"],
        content_hash=content_hash,
        schema_version=raw["schema_version"],
    )


def parse_dataset_manifest(path: Path) -> DatasetManifest:
    """Parse and structurally validate a dataset_manifest.json file.
    Raises DatasetManifestError -- never a bare json/KeyError -- for any
    shape this schema does not allow, including a manifest that omits
    one of the three required source tables or that (incorrectly)
    includes a Calendar entry."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DatasetManifestError(f"{path} is not valid JSON: {exc}") from exc

    schema_version = raw.get("schema_version")
    if schema_version != MANIFEST_SCHEMA_VERSION:
        raise DatasetManifestError(
            f"{path}: schema_version must be {MANIFEST_SCHEMA_VERSION}, got {schema_version!r}"
        )

    entries = tuple(_parse_entry(entry, i) for i, entry in enumerate(raw.get("datasets", [])))

    source_tables = [entry.source_table for entry in entries]
    if len(set(source_tables)) != len(source_tables):
        raise DatasetManifestError(f"{path}: duplicate source_table entries: {source_tables}")

    actual_tables = frozenset(source_tables)
    if actual_tables != REQUIRED_SOURCE_TABLES:
        missing = REQUIRED_SOURCE_TABLES - actual_tables
        unexpected = actual_tables - REQUIRED_SOURCE_TABLES
        detail = []
        if missing:
            detail.append(f"missing: {sorted(missing)}")
        if unexpected:
            detail.append(
                f"unexpected (Calendar is deliberately excluded from datasets, see amendment "
                f"SS A.4): {sorted(unexpected)}"
            )
        raise DatasetManifestError(
            f"{path}: datasets must cover exactly {sorted(REQUIRED_SOURCE_TABLES)}. {'; '.join(detail)}"
        )

    return DatasetManifest(
        schema_version=schema_version,
        project_id=raw.get("project_id", ""),
        generated_at=raw.get("generated_at", ""),
        datasets=entries,
    )
