"""Toy onion routing to obscure message paths.

TODO:
- Telemetry: trace hop traversal for diagnostics.
- Metrics: measure routing overhead per hop.
- Security: implement cryptographic layers, not just annotations.
- Resiliency: retry or reroute on hop failure.
"""
from __future__ import annotations

from typing import Iterable


def route(message: str, hops: Iterable[str]) -> str:
    """Wrap *message* in successive hop annotations."""
    for hop in hops:
        message = f"[{hop}]{message}[/hop]"
    return message


__all__ = ["route"]
