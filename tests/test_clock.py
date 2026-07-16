from __future__ import annotations

from datetime import datetime, timezone

import pytest

from core.shared.clock import FixedClock, SystemClock


def test_fixed_clock_is_deterministic() -> None:
    fixed = datetime(2026, 1, 1, tzinfo=timezone.utc)
    clock = FixedClock(fixed)
    assert clock.now() == fixed
    assert clock.now() == clock.now()


def test_fixed_clock_requires_timezone_aware_datetime() -> None:
    with pytest.raises(ValueError):
        FixedClock(datetime(2026, 1, 1))


def test_system_clock_returns_timezone_aware_datetime() -> None:
    now = SystemClock().now()
    assert now.tzinfo is not None
