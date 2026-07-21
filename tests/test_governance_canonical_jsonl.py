from __future__ import annotations

from pathlib import Path

import pytest

from core.governance.canonical_jsonl import (
    read_canonical_jsonl,
    sha256_of_file,
    write_canonical_jsonl,
)


def test_write_produces_utf8_lf_sorted_keys_with_one_trailing_newline(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.jsonl"
    write_canonical_jsonl([{"b": 1, "a": 2}, {"z": "x", "y": "w"}], path)

    raw = path.read_bytes()
    assert b"\r" not in raw
    assert raw.endswith(b"\n")
    assert raw.count(b"\n") == 2  # exactly one trailing newline, no blank final line
    text = raw.decode("utf-8")
    assert text.splitlines() == ['{"a":2,"b":1}', '{"y":"w","z":"x"}']


def test_write_sorts_nested_object_keys_too(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.jsonl"
    write_canonical_jsonl([{"outer_b": 1, "outer_a": {"inner_z": 1, "inner_a": 2}}], path)

    text = path.read_text(encoding="utf-8")
    assert text == '{"outer_a":{"inner_a":2,"inner_z":1},"outer_b":1}\n'


def test_write_empty_rows_produces_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.jsonl"
    write_canonical_jsonl([], path)

    assert path.read_bytes() == b""


def test_round_trip_preserves_rows(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.jsonl"
    rows = [{"ticker": "SPY", "etf_id": "abc"}, {"ticker": "QQQ", "etf_id": "def"}]

    write_canonical_jsonl(rows, path)

    assert read_canonical_jsonl(path) == rows


def test_read_empty_file_returns_empty_list(tmp_path: Path) -> None:
    path = tmp_path / "empty.jsonl"
    path.write_bytes(b"")

    assert read_canonical_jsonl(path) == []


def test_read_rejects_crlf_line_endings(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_bytes(b'{"a":1}\r\n')

    with pytest.raises(ValueError, match="CR line endings"):
        read_canonical_jsonl(path)


def test_read_rejects_missing_trailing_newline(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_bytes(b'{"a":1}')

    with pytest.raises(ValueError, match="trailing newline"):
        read_canonical_jsonl(path)


def test_sha256_of_file_matches_known_content_hash(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.jsonl"
    path.write_bytes(b"hello world")

    assert sha256_of_file(path) == "sha256:b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"


def test_sha256_of_file_changes_when_bytes_change(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.jsonl"
    path.write_bytes(b"content-a")
    hash_a = sha256_of_file(path)

    path.write_bytes(b"content-b")
    hash_b = sha256_of_file(path)

    assert hash_a != hash_b
    assert hash_a.startswith("sha256:")
