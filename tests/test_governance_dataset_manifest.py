from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.governance.dataset_manifest import (
    MANIFEST_SCHEMA_VERSION,
    REQUIRED_SOURCE_TABLES,
    DatasetManifestError,
    parse_dataset_manifest,
)


def _entry(source_table: str, dataset_id: str | None = None) -> dict:
    return {
        "dataset_id": dataset_id or f"{source_table.lower()}_v1",
        "type": "primary_market_data",
        "source_table": source_table,
        "row_count": 3,
        "snapshot_path": f"dataset_hashes/{source_table.lower()}_v1.jsonl",
        "content_hash": "sha256:" + "a" * 64,
        "schema_version": 1,
    }


def _valid_manifest_dict() -> dict:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "project_id": "h4",
        "generated_at": "2026-08-01T00:00:00+00:00",
        "datasets": [_entry("ETF"), _entry("PriceBar"), _entry("TradingSession")],
    }


def _write(tmp_path: Path, manifest: dict) -> Path:
    path = tmp_path / "dataset_manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_parses_a_valid_v3_manifest(tmp_path: Path) -> None:
    path = _write(tmp_path, _valid_manifest_dict())

    manifest = parse_dataset_manifest(path)

    assert manifest.schema_version == 3
    assert {e.source_table for e in manifest.datasets} == REQUIRED_SOURCE_TABLES
    assert REQUIRED_SOURCE_TABLES == {"ETF", "PriceBar", "TradingSession"}


def test_rejects_wrong_manifest_schema_version(tmp_path: Path) -> None:
    manifest = _valid_manifest_dict()
    manifest["schema_version"] = 2
    path = _write(tmp_path, manifest)

    with pytest.raises(DatasetManifestError, match="schema_version"):
        parse_dataset_manifest(path)


def test_rejects_calendar_dataset_entry(tmp_path: Path) -> None:
    manifest = _valid_manifest_dict()
    manifest["datasets"].append(_entry("Calendar"))
    path = _write(tmp_path, manifest)

    with pytest.raises(DatasetManifestError, match="deliberately excluded"):
        parse_dataset_manifest(path)


def test_rejects_missing_required_dataset(tmp_path: Path) -> None:
    manifest = _valid_manifest_dict()
    manifest["datasets"] = [_entry("ETF"), _entry("PriceBar")]  # TradingSession missing
    path = _write(tmp_path, manifest)

    with pytest.raises(DatasetManifestError, match="missing"):
        parse_dataset_manifest(path)


def test_rejects_duplicate_source_table_entries(tmp_path: Path) -> None:
    manifest = _valid_manifest_dict()
    manifest["datasets"].append(_entry("ETF", dataset_id="etf_v2"))
    path = _write(tmp_path, manifest)

    with pytest.raises(DatasetManifestError, match="duplicate"):
        parse_dataset_manifest(path)


def test_rejects_entry_missing_required_field(tmp_path: Path) -> None:
    manifest = _valid_manifest_dict()
    del manifest["datasets"][0]["content_hash"]
    path = _write(tmp_path, manifest)

    with pytest.raises(DatasetManifestError, match="missing required field"):
        parse_dataset_manifest(path)


def test_rejects_content_hash_without_sha256_prefix(tmp_path: Path) -> None:
    manifest = _valid_manifest_dict()
    manifest["datasets"][0]["content_hash"] = "a" * 64
    path = _write(tmp_path, manifest)

    with pytest.raises(DatasetManifestError, match="sha256:"):
        parse_dataset_manifest(path)


def test_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "dataset_manifest.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(DatasetManifestError):
        parse_dataset_manifest(path)


def test_per_entry_schema_version_is_independent_of_manifest_schema_version(tmp_path: Path) -> None:
    manifest = _valid_manifest_dict()
    manifest["datasets"][0]["schema_version"] = 7
    path = _write(tmp_path, manifest)

    parsed = parse_dataset_manifest(path)

    assert parsed.schema_version == 3
    etf_entry = next(e for e in parsed.datasets if e.source_table == "ETF")
    assert etf_entry.schema_version == 7
