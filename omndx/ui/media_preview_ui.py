"""Stub for media preview functionality.

TODO:
- Telemetry: capture preview request statistics.
- Metrics: monitor preview rendering times.
- Security: validate media paths and handle untrusted formats.
- Resiliency: implement fallbacks for unsupported media.
"""
from __future__ import annotations

from pathlib import Path


def preview(path: Path) -> str:
    return f"Preview not available for {path.name}"


__all__ = ["preview"]
