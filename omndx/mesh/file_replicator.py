"""File replication helper.

TODO:
- Telemetry: log replication operations.
- Metrics: track replication latency and throughput.
- Security: verify file integrity and permissions.
- Resiliency: support retries on transient errors.
"""
from __future__ import annotations

import shutil
from pathlib import Path


def replicate(src: Path, dest: Path) -> None:
    """Copy *src* to *dest* creating parent directories as needed."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


__all__ = ["replicate"]
