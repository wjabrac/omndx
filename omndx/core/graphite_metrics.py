"""Minimal Graphite metrics sender.

This module provides a tiny helper to send metrics to a Graphite server using
its plain-text TCP protocol.  Failures to contact the server are logged but do
not raise exceptions, allowing the caller to proceed regardless of metrics
availability.
"""
from __future__ import annotations

import logging
import socket
import time


logger = logging.getLogger(__name__)


class GraphiteClient:
    """Send metrics to a Graphite endpoint."""

    def __init__(self, host: str = "localhost", port: int = 2003) -> None:
        self.address = (host, port)

    def send(self, path: str, value: float, timestamp: int | None = None) -> None:
        ts = timestamp or int(time.time())
        message = f"{path} {value} {ts}\n".encode("ascii")
        try:  # pragma: no cover - best effort networking
            with socket.create_connection(self.address, timeout=0.5) as sock:
                sock.sendall(message)
        except Exception:  # pragma: no cover - external service
            logger.warning("Graphite metric send failed", exc_info=True)


__all__ = ["GraphiteClient"]
