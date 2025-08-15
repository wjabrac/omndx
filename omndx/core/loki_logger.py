"""Logging handler for Grafana Loki."""
from __future__ import annotations

import logging
import time
from typing import Dict, Optional

try:  # pragma: no cover - optional dependency
    import requests
except Exception:  # pragma: no cover - fallback when requests is missing
    requests = None  # type: ignore


class LokiHandler(logging.Handler):
    """A basic logging handler that ships logs to Loki."""

    def __init__(self, url: str = "http://localhost:3100/loki/api/v1/push", tags: Optional[Dict[str, str]] = None) -> None:
        super().__init__()
        self.url = url
        self.tags = tags or {}

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - network IO
        if not requests:
            return
        ts = str(int(time.time() * 1e9))
        payload = {
            "streams": [
                {
                    "stream": self.tags,
                    "values": [[ts, self.format(record)]],
                }
            ]
        }
        try:
            requests.post(self.url, json=payload, timeout=0.5)
        except Exception:
            pass


def get_loki_logger(name: str, url: str = "http://localhost:3100/loki/api/v1/push", tags: Optional[Dict[str, str]] = None) -> logging.Logger:
    """Create a logger that sends entries to Loki."""

    logger = logging.getLogger(name)
    handler = LokiHandler(url=url, tags=tags)
    logger.addHandler(handler)
    return logger


__all__ = ["LokiHandler", "get_loki_logger"]
