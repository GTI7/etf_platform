"""Process-level offline guarantee (Phase 4 Architecture Amendment v1.1
SS E). Installed by the reproduction runner's own entrypoint, before
importing or invoking any experiment code -- not a pytest fixture, and
not scoped to one construction call the way the existing
``yahoo_finance._http_get`` patch test is (that test is retained as
secondary defense-in-depth, see ``tests/test_yahoo_finance_provider.py``).

This blocks the primitives every network call in this stdlib-only
codebase (AD-005) must ultimately go through: ``socket.socket.connect``,
``socket.create_connection``, and ``socket.getaddrinfo``. The last of
these closes a distinct leak the first two do not: code that resolves a
hostname (DNS) without ever opening a socket -- e.g. calling
``socket.getaddrinfo``/``gethostbyname``-style resolution directly --
still reaches the network even though ``connect`` is never invoked.
Nothing in ``core/``, ``adapters/``, or ``experiments/`` imports
``asyncio`` (verified directly), and asyncio's own default event loop
opens connections through ``socket.socket`` internally, so there is no
separate asyncio path left to patch here.

Known narrower gap, named rather than silently assumed away (matching
this platform's own risk-disclosure discipline, amendment SS H):
``socket.socket.connect_ex`` and ``socket.gethostbyname``/
``socket.gethostbyname_ex`` are distinct entry points this guard does
not patch. Nothing in this codebase currently uses them.
"""

from __future__ import annotations

import socket
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any


class OfflineViolationError(RuntimeError):
    """Raised when reproduction code attempts any network connection. A
    reproduction run that raises this must be treated as failed -- the
    guard raising at all is itself an automatic REPRODUCTION_FAILED, not
    a silent pass (amendment SS F.3)."""


_ORIGINAL_SOCKET_CONNECT = socket.socket.connect
_ORIGINAL_CREATE_CONNECTION = socket.create_connection
_ORIGINAL_GETADDRINFO = socket.getaddrinfo

# Depth counter, not a bool: makes install/uninstall safe to nest. Two
# overlapping `with offline_guard():` blocks (or a caller that installs
# the guard itself around a `run_reproduction` call that also installs
# it) must not let the inner block's exit tear down the outer block's
# guard -- only the outermost uninstall actually restores the real
# primitives.
_install_depth = 0


def _blocked_connect(self: socket.socket, address: Any, *args: Any, **kwargs: Any) -> None:
    raise OfflineViolationError(f"blocked outbound socket connection to {address!r} during reproduction")


def _blocked_create_connection(address: Any, *args: Any, **kwargs: Any) -> None:
    raise OfflineViolationError(f"blocked outbound socket connection to {address!r} during reproduction")


def _blocked_getaddrinfo(host: Any, port: Any, *args: Any, **kwargs: Any) -> None:
    raise OfflineViolationError(f"blocked outbound DNS resolution for {(host, port)!r} during reproduction")


def install_offline_guard() -> None:
    """Patch socket.socket.connect, socket.create_connection, and
    socket.getaddrinfo to raise OfflineViolationError unconditionally,
    for the lifetime of the process (or until every matching
    uninstall_offline_guard() call has run). Safe to call while already
    installed -- nesting increments a depth counter rather than
    re-patching or losing track of the outermost caller."""
    global _install_depth
    if _install_depth == 0:
        socket.socket.connect = _blocked_connect  # type: ignore[method-assign]
        socket.create_connection = _blocked_create_connection  # type: ignore[assignment]
        socket.getaddrinfo = _blocked_getaddrinfo  # type: ignore[assignment]
    _install_depth += 1


def uninstall_offline_guard() -> None:
    """Undo one install_offline_guard() call. Only restores the real
    socket primitives once every matching install has been undone (depth
    reaches zero) -- the reproduction run itself must never call this
    before it finishes (amendment SS H.4: the guard is unconditional for
    the life of the reproduction run, by design). Raises RuntimeError on
    an unmatched call rather than silently restoring an already-bare
    guard."""
    global _install_depth
    if _install_depth == 0:
        raise RuntimeError("uninstall_offline_guard() called with no matching install_offline_guard()")
    _install_depth -= 1
    if _install_depth == 0:
        socket.socket.connect = _ORIGINAL_SOCKET_CONNECT  # type: ignore[method-assign]
        socket.create_connection = _ORIGINAL_CREATE_CONNECTION  # type: ignore[assignment]
        socket.getaddrinfo = _ORIGINAL_GETADDRINFO  # type: ignore[assignment]


@contextmanager
def offline_guard() -> Iterator[None]:
    install_offline_guard()
    try:
        yield
    finally:
        uninstall_offline_guard()
