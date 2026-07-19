"""Independence-label linting (Governance Tier 1, item 2).

Automates ``docs/RESEARCH_PLATFORM_RETROSPECTIVE.md`` Section 3 item 2:
"a single regex/CI check for the literal word 'independent' appearing
without an adjacent Level 2/3 qualifier" -- the cheapest automation on
the retrospective's own list, which "would have caught every one of the
three mislabeled H3 review documents before they were written, not
after." ``docs/RESEARCH_GOVERNANCE_STANDARD.md`` requires every review
described as "independent" to carry an explicit Level 1/2/3 qualifier
(Level 2 = procedurally independent, same-operator session; Level 3 =
organizationally independent, a distinct party) -- an unqualified
"independent" is the specific defect this lints for.

**Local, line-adjacent matching -- not whole-document, not NLU.** A
whole-file check ("does this document mention Level 2/3 anywhere") would
flag almost nothing, since most H3 documents mention a Level qualifier
somewhere while still containing individual unqualified sentences (the
actual historical defect). This linter instead flags each line
containing "independent"/"independently" unless a Level 2/3 qualifier
appears on that same line or the immediately preceding line -- matching
the two real patterns already in use (`"**Level 2** ... independent"` on
one line; `"**Reviewer level:** **Level 2**"` followed by an
"independent"-using line next).

This is deliberately a lexical check, not a natural-language one. It
does not attempt to determine whether "independent" is being used in
this document's review-independence sense at all -- a phrase like
"independent variable" is flagged exactly the same as an unqualified
review claim, because distinguishing the two would require actual
sentence understanding, which is out of scope. Findings are candidates
for a human reviewer to triage, not an automatic pass/fail gate (see
`docs/PLATFORM_ARCHITECTURE_V1.md` Section 4.4: Governance "flags", it
does not fix or auto-reject).

**Calibration finding (Phase 1C smoke test).** Run read-only against
every `.md` file under `docs/` and `research_archive/` (50 files), this
linter produced 403 findings -- far more than the "three mislabeled H3
review documents" the retrospective named. Inspection of the output
shows why: real documents typically state a Level 2/3 qualifier once
per section, then use bare "independent"/"independently" several more
times in the same section still referring to that one already-qualified
claim. The one-line lookback (by design, see above) does not reach
those later, section-scoped repeats, so they surface as findings too.
This is a **candidate-discovery tool, not a semantic validator**: it
finds every unqualified occurrence of the word, not every occurrence
that is actually unqualified *in context*. High findings volume on this
corpus is a calibration signal about that gap between lexical and
section-level meaning, not a defect in what the tool was built to do --
consistent with its role as something a human triages (see above), not
an automatic gate. No change to the matching rule was made in response
to this finding; widening the window (e.g. to a paragraph/section scope)
remains a deliberate, separate decision for later, once Governance has
a real consumer to evaluate precision against.

Read-only: only reads the given file paths, never writes.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

_INDEPENDENT_RE = re.compile(r"\bindependent(ly)?\b", re.IGNORECASE)
_LEVEL_QUALIFIER_RE = re.compile(r"\blevel\s*[23]\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class LintFinding:
    """One unqualified "independent" occurrence, plain enough to render
    directly or feed to a future Reporting-domain consumer."""

    path: str
    line_number: int
    line_text: str


def lint(paths: Iterable[Path | str]) -> list[LintFinding]:
    """Scan each file in `paths` for "independent"/"independently"
    occurrences not accompanied by a Level 2/3 qualifier on the same or
    immediately preceding line. Returns one `LintFinding` per offending
    line, in file-then-line order."""
    findings: list[LintFinding] = []
    for path in paths:
        file_path = Path(path)
        lines = file_path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            if not _INDEPENDENT_RE.search(line):
                continue
            qualified_here = _LEVEL_QUALIFIER_RE.search(line) is not None
            qualified_previous = index > 0 and _LEVEL_QUALIFIER_RE.search(lines[index - 1]) is not None
            if qualified_here or qualified_previous:
                continue
            findings.append(LintFinding(path=str(path), line_number=index + 1, line_text=line.strip()))
    return findings
