"""Observational environment metadata for one reproduction verification run.

This module observes the **current process's** interpreter and platform --
the machine state of *this* verification attempt, nothing more. It does
not write ``reproduction_record.json`` or any other archive artifact, and
recording its output into one is a separately authorized action: this
module has no file I/O, touches no archive, and creates no new
archive-writing authority.

The three fields returned are evidence about how a reproduction attempt
was run, never identity. They must never be folded into
``ReproductionStatus``, into a dataset or result content hash, or into
``IndicatorDefinition.version`` -- doing so would turn an observation
about the runner into part of what is being verified.
"""

from __future__ import annotations

import platform


def observe_reproduction_environment() -> dict[str, str]:
    """The current process's interpreter and platform, as plain strings.

    Exactly ``python_version``, ``python_implementation``, ``platform`` --
    no dependency discovery, no lockfile inspection, no hostname/username/
    environment-variable/CPU/container/filesystem information."""
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
    }
