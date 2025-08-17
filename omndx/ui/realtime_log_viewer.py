"""Follow a log file and yield new lines.

TODO:
- Telemetry: report viewer connection status.
- Metrics: track throughput of streamed lines.
- Security: enforce read permissions on log files.
- Resiliency: handle file rotations and truncation gracefully.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator


def follow(path: Path) -> Iterator[str]:
    with path.open() as fh:
        fh.seek(0, 2)
        while True:
            line = fh.readline()
            if not line:
                break
            yield line.rstrip("\n")


__all__ = ["follow"]
