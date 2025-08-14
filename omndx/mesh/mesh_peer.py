"""Peer management and communication utilities.

This module provides the :class:`MeshPeer` class which acts as a very small
in-memory simulation of a peer in a mesh network.  The class is intentionally
minimal – it is not intended to be a production ready implementation of mesh
networking.  Instead it offers enough behaviour for the unit tests in this
repository to model peer discovery and message exchange.

The design favours clarity over performance.  Peers register themselves in a
class level registry allowing other peers to discover them.  Messages are sent
using the accompanying :class:`~omndx.mesh.onion_router.OnionRouter` which can
optionally forward messages through intermediate peers to provide a form of
onion style routing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Dict, Iterable, List, Optional, Tuple

from .bandwidth_balancer import BandwidthBalancer
from .file_replicator import FileReplicator
from .onion_router import OnionRouter


@dataclass
class MeshPeer:
    """Represents a single peer in the mesh network.

    Parameters
    ----------
    peer_id:
        Unique identifier for the peer.
    onion_router:
        Optional :class:`OnionRouter` instance.  If not provided a default one
        will be created.
    file_replicator:
        Optional :class:`FileReplicator` instance.  If not provided a default
        one will be created.
    bandwidth_balancer:
        Optional :class:`BandwidthBalancer` instance used to throttle outgoing
        traffic.  By default a balancer with a generous limit is used.
    """

    peer_id: str
    onion_router: OnionRouter | None = None
    file_replicator: FileReplicator | None = None
    bandwidth_balancer: BandwidthBalancer | None = None
    inbox: List[Tuple[str, str]] = field(default_factory=list)

    # Class level registry of peers.  It allows very small scale peer discovery
    # for the purposes of our tests.
    registry: ClassVar[Dict[str, "MeshPeer"]] = {}

    def __post_init__(self) -> None:
        if self.onion_router is None:
            self.onion_router = OnionRouter(self)
        if self.file_replicator is None:
            self.file_replicator = FileReplicator(self)
        if self.bandwidth_balancer is None:
            # 1MB default budget which is ample for the tests.
            self.bandwidth_balancer = BandwidthBalancer(max_bandwidth=1_000_000)

        # Register this peer for discovery.
        MeshPeer.registry[self.peer_id] = self

    # ------------------------------------------------------------------
    # class helpers
    # ------------------------------------------------------------------
    @classmethod
    def get_peer(cls, peer_id: str) -> Optional["MeshPeer"]:
        """Return a peer by identifier if it exists."""

        return cls.registry.get(peer_id)

    @classmethod
    def clear_registry(cls) -> None:
        """Remove all registered peers.

        Useful for tests to ensure isolation between scenarios.
        """

        cls.registry.clear()

    # ------------------------------------------------------------------
    # discovery & communication API
    # ------------------------------------------------------------------
    def discover_peers(self) -> Dict[str, "MeshPeer"]:
        """Return all known peers except for ``self``."""

        return {pid: p for pid, p in MeshPeer.registry.items() if pid != self.peer_id}

    def send_message(self, target_id: str, message: str, path: Optional[List[str]] = None) -> None:
        """Send a message to ``target_id``.

        Parameters
        ----------
        target_id:
            Identifier of the receiving peer.
        message:
            The string message to send.
        path:
            Optional list of intermediate peer identifiers that the message
            should traverse.  When provided the message will be routed through
            these peers using onion-style routing; otherwise the message is sent
            directly to the target.
        """

        size = len(message.encode())
        if not self.bandwidth_balancer.can_send(size):
            raise RuntimeError("bandwidth exceeded")
        assert self.onion_router is not None  # for type checkers
        self.onion_router.send_onion(target_id, message, path or [])

    # ------------------------------------------------------------------
    # inbound handlers
    # ------------------------------------------------------------------
    def receive_message(self, source_id: str, message: str) -> None:
        """Store an incoming message for inspection by tests."""

        self.inbox.append((source_id, message))


__all__ = ["MeshPeer"]

