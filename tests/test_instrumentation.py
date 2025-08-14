"""Tests for tag-based instrumentation."""

from __future__ import annotations

import os
import sys

# Ensure the package root is on the import path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from omndx.core.instrumentation import TagLogger


def test_tag_logging_counts() -> None:
    logger = TagLogger("tester")
    logger.info("hello", tag="greeting")
    logger.info("world", tag="greeting")
    assert logger.get_metrics()["greeting"] == 2

