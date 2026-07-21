from __future__ import annotations

import socket

import pytest

from core.governance.network_guard import (
    OfflineViolationError,
    install_offline_guard,
    offline_guard,
    uninstall_offline_guard,
)


def test_offline_guard_blocks_socket_connect() -> None:
    with offline_guard():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            with pytest.raises(OfflineViolationError):
                sock.connect(("example.invalid", 80))
        finally:
            sock.close()


def test_offline_guard_blocks_create_connection() -> None:
    with offline_guard():
        with pytest.raises(OfflineViolationError):
            socket.create_connection(("example.invalid", 80))


def test_offline_guard_restores_real_socket_after_exit() -> None:
    with offline_guard():
        pass

    # After the context exits, connecting to a closed local port raises
    # an ordinary OSError (connection refused, fast and deterministic --
    # no real network or DNS involved), never OfflineViolationError --
    # proof the guard was actually uninstalled.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(OSError) as exc_info:
            sock.connect(("127.0.0.1", 1))
        assert not isinstance(exc_info.value, OfflineViolationError)
    finally:
        sock.close()


def test_install_and_uninstall_are_directly_callable() -> None:
    install_offline_guard()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            with pytest.raises(OfflineViolationError):
                sock.connect(("example.invalid", 80))
        finally:
            sock.close()
    finally:
        uninstall_offline_guard()


def test_guard_raises_even_when_run_experiment_swallows_generic_exceptions() -> None:
    """A reproduction attempt that (incorrectly) tries to catch broad
    exceptions around its own logic must still see OfflineViolationError
    surface as itself, not get relabeled -- it is a RuntimeError subclass
    but a distinctly named one callers can match on specifically."""
    with offline_guard():
        try:
            socket.create_connection(("example.invalid", 80))
        except OfflineViolationError as exc:
            assert "blocked outbound socket connection" in str(exc)
        else:
            pytest.fail("expected OfflineViolationError")


def test_offline_guard_blocks_bare_dns_resolution() -> None:
    """socket.getaddrinfo can reach the network (a real DNS query) even
    when nothing ever calls connect() -- a distinct leak from the
    connect()/create_connection() paths above, and one that must be
    blocked too."""
    with offline_guard():
        with pytest.raises(OfflineViolationError):
            socket.getaddrinfo("example.invalid", 80)


def test_offline_guard_restores_getaddrinfo_after_exit() -> None:
    with offline_guard():
        pass

    # A real (fast, local) resolution must work again once the guard is
    # uninstalled -- proof getaddrinfo was actually restored, not left
    # blocked.
    socket.getaddrinfo("127.0.0.1", 80)


def test_nested_offline_guard_contexts_do_not_leak() -> None:
    """The inner context's exit must not tear down the outer context's
    guard -- a caller nesting offline_guard() (directly or via a nested
    run_reproduction-style call) must stay protected until the outermost
    context actually exits."""
    with offline_guard():
        with offline_guard():
            pass
        # Still inside the outer context: the guard must still be active.
        with pytest.raises(OfflineViolationError):
            socket.create_connection(("example.invalid", 80))

    # Fully exited: the guard must be inactive.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(OSError) as exc_info:
            sock.connect(("127.0.0.1", 1))
        assert not isinstance(exc_info.value, OfflineViolationError)
    finally:
        sock.close()


def test_unmatched_uninstall_raises_instead_of_silently_no_opping() -> None:
    with pytest.raises(RuntimeError, match="no matching install_offline_guard"):
        uninstall_offline_guard()
