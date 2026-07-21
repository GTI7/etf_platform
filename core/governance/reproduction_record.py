"""Reproduction contract binding and its outcome (Phase 4 Architecture
Amendment v1.1 SS G; base proposal SS 2.2): commit hash + N dataset
content hashes + a result-report hash, all bound in one small record,
and the 4-state outcome verifying that record produces.

``ReproductionStatus`` "extends" ``core.governance.freeze_verifier.FreezeStatus``
in the sense of reusing its three semantics (``VERIFIED``/``DRIFTED``/
``UNVERIFIABLE``) plus a fourth state ``FreezeStatus`` cannot express --
*inputs matched exactly, but the computed output did not* -- a real
non-determinism or environment bug, categorically different from
"someone edited a frozen file". ``FreezeStatus`` is a closed ``str``
``Enum`` with no subclassing hook, so this is a conceptual extension,
not a literal Python one.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReproductionStatus(str, Enum):
    VERIFIED = "verified"  # inputs matched, output matched
    DRIFTED = "drifted"  # an input (commit/dataset) doesn't match its claimed hash
    REPRODUCTION_FAILED = "reproduction_failed"  # all inputs matched; output did not (or the offline guard tripped)
    UNVERIFIABLE = "unverifiable"  # a referenced artifact is missing/unresolvable


@dataclass(frozen=True, slots=True)
class ReproductionRecord:
    """One cycle's reproduction_record.json content: the commit pinning
    code, the dataset content hashes it was run against (one per
    frozen-identity dataset: ETF, PriceBar, TradingSession), and the
    result report hash it must reproduce exactly."""

    commit_hash: str
    dataset_content_hashes: dict[str, str]
    result_report_hash: str
