"""Canonical JSONL snapshot format shared by every frozen dataset type
(``ETF``, ``PriceBar``, ``TradingSession`` -- Phase 4 Architecture
Amendment v1.1 Appendix C.1, reusing v1.0 SS A.6's rule set unchanged):
one canonicalization rule set for this design, not one per dataset.

Rules:
- UTF-8, no BOM.
- LF (``\\n``) line endings only.
- Exactly one trailing newline (no missing terminal newline, no blank
  final line).
- Keys in alphabetical (codepoint) order, applied independently to every
  JSON object in the file, including nested objects.
- One JSON object per line.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def write_canonical_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    """Write `rows` as canonical JSONL. An empty `rows` list writes an
    empty (zero-byte) file -- there is no "trailing newline" to speak of
    when there are no rows."""
    lines = [json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) for row in rows]
    content = "\n".join(lines)
    if lines:
        content += "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("utf-8"))


def read_canonical_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a canonical JSONL file back into a list of row dicts. Rejects
    anything that is not exactly this format (CRLF line endings, a
    missing trailing newline) rather than silently tolerating it -- a
    dataset-hash pipeline is exactly the kind of thing that breaks
    silently across platform line-ending differences if this isn't
    enforced on read, not just on write."""
    raw = path.read_bytes()
    if raw == b"":
        return []
    text = raw.decode("utf-8")
    if "\r" in text:
        raise ValueError(f"{path}: not canonical JSONL -- contains CR line endings, LF-only required")
    if not text.endswith("\n"):
        raise ValueError(f"{path}: not canonical JSONL -- missing the required single trailing newline")
    return [json.loads(line) for line in text[:-1].split("\n")]


def sha256_of_file(path: Path) -> str:
    """The exported snapshot file's own bytes, hashed directly -- not a
    hash computed over in-memory rows via some serialization that could
    differ from what's actually stored on disk (base proposal SS 1.4)."""
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
