"""Restricted environment for torrent operations.

TODO:
- Telemetry: log sandboxed torrent activity.
- Metrics: measure data transfer and sandbox utilization.
- Security: enforce read/write restrictions and scan downloads.
- Resiliency: clean up partial downloads on failures.
"""
from __future__ import annotations

from pathlib import Path


class TorrentSandbox:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def is_within_sandbox(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.root.resolve())
            return True
        except ValueError:
            return False


__all__ = ["TorrentSandbox"]
