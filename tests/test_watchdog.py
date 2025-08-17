"""Tests for the :mod:`omndx.runtime.watchdog` module."""

from __future__ import annotations

import asyncio
import os
import sys

# Ensure the package root is on the import path when tests are run directly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from omndx.runtime.watchdog import Watchdog


def test_watchdog_invokes_callback() -> None:
    """The watchdog should invoke the callback periodically."""

    async def run_test() -> None:
        count = 0

        async def callback() -> None:
            nonlocal count
            count += 1

        wd = Watchdog(0.05, callback)
        wd.start()
        await asyncio.sleep(0.16)  # allow several invocations
        await wd.stop()

        assert count >= 2

    asyncio.run(run_test())


def test_watchdog_stop_cancels_future_calls() -> None:
    """After ``stop`` is awaited the callback should no longer run."""

    async def run_test() -> None:
        count = 0

        async def callback() -> None:
            nonlocal count
            count += 1

        wd = Watchdog(0.05, callback)
        wd.start()
        await asyncio.sleep(0.11)  # at least one invocation
        await wd.stop()
        called = count
        await asyncio.sleep(0.1)
        assert count == called

    asyncio.run(run_test())

