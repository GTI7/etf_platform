"""The `archive_manifest.json` contract's two identity constants, in one
place.

Both describe `docs/RESEARCH_ARCHIVE_MANIFEST.md`: the filename that
carries a research archive's identity, and the three archive directories
that predate the concept and therefore never carry one ("Applicability"
in that document).

**Why this module exists.** Each constant previously had more than one
definition, and each duplication was individually well-argued in a
comment at its own site:

- `LEGACY_ARCHIVE_PROJECT_IDS` was written out three times --
  `tools/archive_manifest.py`, `core.governance.archive_verifier`,
  `core.governance.archive_seal` -- each copy justified by the direction
  of some import it was avoiding (`core/` must not import `tools/`;
  `archive_seal` must not import its own caller `archive_verifier`).
  Every one of those justifications was correct about the edge it named
  and wrong about the conclusion: the fix for "the module that has it is
  the wrong one to depend on" is a module that is the right one to depend
  on, not a third copy.
- `ARCHIVE_MANIFEST_FILENAME` was hosted by
  `core.governance.decision_recorder` -- a module about hash-chained
  transition records that happened to be the first to need the name --
  and duplicated a fourth time as `MANIFEST_FILENAME` in
  `tools/archive_manifest.py`.

The failure mode a duplicated constant has here is not maintenance
tedium. `LEGACY_ARCHIVE_PROJECT_IDS` decides whether an archive is exempt
from the v1 layout check (`archive_verifier`) *and* whether it can ever
be sealed (`archive_seal`, AC-74-9). Two copies that disagreed would
produce an archive that is exempt from one control and subject to the
other, silently, with no test able to see the disagreement.

**Direction.** This module imports nothing -- not from `core`, not from
the standard library beyond what a `frozenset` literal needs. Everything
above it may therefore depend on it without inverting any edge:
`decision_recorder` -> here, `archive_seal` -> here, `archive_verifier` ->
here, and `tools/archive_manifest.py` -> here (tooling depends on `core`,
never the reverse).
"""

from __future__ import annotations

# The file whose presence, and whose `project_id` field, establish a
# research archive's identity (docs/RESEARCH_ARCHIVE_MANIFEST.md).
ARCHIVE_MANIFEST_FILENAME = "archive_manifest.json"

# The three archive directories that predate `archive_manifest.json`
# (docs/RESEARCH_ARCHIVE_MANIFEST.md "Applicability"). They are never
# written to by the manifest tooling, are exempt from the v1 archive
# layout check, and are never sealed (AC-74-9) -- their bytes are held by
# `tests/fixtures/protected_file_hashes.json` instead.
LEGACY_ARCHIVE_PROJECT_IDS = frozenset({"reference_v1", "reference_v2_h1", "reference_h3"})
