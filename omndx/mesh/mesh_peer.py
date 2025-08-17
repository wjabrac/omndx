"""Peer representation for the experimental mesh network.

TODO:
- Telemetry: emit peer message counts.
- Metrics: record latency between peers.
- Security: authenticate peers and encrypt messages.
- Resiliency: handle offline peers gracefully.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MeshPeer:
    """Simple peer containing an identifier and message buffer."""

    peer_id: str
    inbox: list[str]

    def send(self, other: "MeshPeer", message: str) -> None:
        other.inbox.append(message)

    def receive(self) -> list[str]:
        messages = self.inbox[:]
        self.inbox.clear()
        return messages


__all__ = ["MeshPeer"]
