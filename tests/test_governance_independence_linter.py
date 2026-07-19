from __future__ import annotations

from pathlib import Path

from core.governance.independence_linter import lint


def _write(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_level_2_qualifier_on_previous_line_is_not_flagged(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "doc.md",
        "**Reviewer level:** **Level 2 — AI-assisted adversarial**\n"
        "(procedurally independent, single-session).\n",
    )

    assert lint([path]) == []


def test_level_3_qualifier_on_same_line_is_not_flagged(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "doc.md",
        "Reviewed at Level 3 (organizationally independent) review.\n",
    )

    assert lint([path]) == []


def test_bare_independent_with_no_nearby_qualifier_is_flagged(tmp_path: Path) -> None:
    path = _write(tmp_path, "doc.md", "This was an independent review of the result.\n")

    findings = lint([path])

    assert len(findings) == 1
    assert findings[0].line_number == 1
    assert findings[0].path == str(path)


def test_independently_validated_with_no_nearby_qualifier_is_flagged(tmp_path: Path) -> None:
    path = _write(tmp_path, "doc.md", "The reviewer independently validated the calculation.\n")

    findings = lint([path])

    assert len(findings) == 1
    assert "independently validated" in findings[0].line_text


def test_qualifier_two_lines_above_does_not_count(tmp_path: Path) -> None:
    """Only the same line or the immediately preceding line count -- a
    Level 2/3 mention further up the document does not retroactively
    qualify every later use of "independent" (that is the whole-file
    behavior this linter deliberately avoids -- see module docstring)."""
    path = _write(
        tmp_path,
        "doc.md",
        "Level 2 review performed here.\n"
        "Some unrelated line in between.\n"
        "This was an independent check.\n",
    )

    findings = lint([path])

    assert len(findings) == 1
    assert findings[0].line_number == 3


def test_bare_phrase_independent_variable_is_also_flagged(tmp_path: Path) -> None:
    """Known, accepted false positive: this linter is lexical, not
    semantic (module docstring), so a non-review use of "independent"
    (e.g. a statistics term like "independent variable") is flagged
    exactly like an unqualified review claim would be. Distinguishing
    the two would require sentence-level natural language understanding,
    which is explicitly out of scope -- findings are candidates for human
    triage, not an automatic gate."""
    path = _write(tmp_path, "doc.md", "Regress the outcome on the independent variable.\n")

    findings = lint([path])

    assert len(findings) == 1
    assert "independent variable" in findings[0].line_text


def test_multiple_files_and_multiple_findings_are_aggregated_in_order(tmp_path: Path) -> None:
    first = _write(tmp_path, "first.md", "An independent claim here.\nLevel 2 says independent right here.\n")
    second = _write(tmp_path, "second.md", "Another independent claim, unqualified.\n")

    findings = lint([first, second])

    assert [(f.path, f.line_number) for f in findings] == [
        (str(first), 1),
        (str(second), 1),
    ]


def test_no_occurrence_of_independent_produces_no_findings(tmp_path: Path) -> None:
    path = _write(tmp_path, "doc.md", "Nothing relevant in this document at all.\n")

    assert lint([path]) == []
