"""Governance domain (Layer 1).

Package for the platform's artifact/state auditing capability --
``FreezeVerifier``, ``IndependenceLabelLinter``, ``ArchiveVerifier``,
``DatasetIntegrityChecker``, ``ReproducibilityChecker`` -- per
docs/PLATFORM_ARCHITECTURE_V1.md Section 4.4.

As of Migration Plan Step 4 / Phase 1C, Tier 1 is implemented:
``freeze_verifier.verify_freeze`` and ``independence_linter.lint``
automate the two checks docs/RESEARCH_PLATFORM_RETROSPECTIVE.md Section
3 items 1-2 identified as manual, one-off audit passes (see
docs/H3_GOVERNANCE_COMPLIANCE_AUDIT.md for what those passes looked like
before automation). ``ArchiveVerifier``, ``DatasetIntegrityChecker``,
and ``ReproducibilityChecker`` remain unimplemented.

Decision logging is deliberately not part of this package's planned
surface. ``docs/PLATFORM_ARCHITECTURE_V1.md``'s own ``DecisionLogger``
sketch is superseded (docs/ARCHITECTURE_DECISIONS.md AD-045): every
research decision is recorded through the human-authored
``decision_log.md`` evidence pattern --
``docs/templates/decision_log_template.md``'s append-only entry shape,
already proven across ``research_archive/reference_h3/decision_log.md``'s
18 entries -- not through a Governance-owned logging call. AD-045
explains why: an automated log call would satisfy "an entry exists"
without the human judgment the template's fields actually require, and
its designed trigger (Research's ``advance_phase()``) does not exist in
this codebase.

Depends only on the Data domain (``core.market_data``,
``core.analytics.persistence``) -- not yet exercised by either Tier 1
module, both of which depend on nothing beyond git and the standard
library. Per the architecture document, Governance must never import
from Research, Validation, or Reporting -- it audits their output as
opaque artifacts, never their internals.
"""
