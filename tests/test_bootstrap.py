"""Tests for runtime bootstrap utilities."""

from __future__ import annotations

import os
import sys

# Ensure package root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from omndx.runtime.bootstrap import bootstrap


def test_bootstrap_creates_event_loop() -> None:
    config, logger, loop = bootstrap()
    try:
        assert isinstance(config, dict)
        assert logger.name == "omndx.runtime"
        assert not loop.is_closed()
    finally:
        loop.close()
