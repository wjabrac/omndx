"""Utilities for replicating files across peers.

The :class:`FileReplicator` class is a deliberately small abstraction which
allows a :class:`~omndx.mesh.mesh_peer.MeshPeer` to share byte content with other
peers in the network.  Each peer maintains a mapping of file name to bytes in
memory – persistence and conflict resolution are outside the scope of these
tests.

Replication is bandwidth aware; the owning peer's
:class:`~omndx.mesh.bandwidth_balancer.BandwidthBalancer` is consulted before
each transfer and a :class:`RuntimeError` is raised if the peer exceeds its
budget.  For the simple scenarios in the tests this provides sufficient
behaviour to reason about redundancy and throttling.
"""

from __future__ import annotations

from typing import Iterable, Optional


class FileReplicator:
    """Replicates files to other peers."""

    def __init__(self, peer: "MeshPeer") -> None:
        self.peer = peer
        self.files: dict[str, bytes] = {}

    # ------------------------------------------------------------------
    def store_file(self, name: str, content: bytes) -> None:
        """Store ``content`` locally under ``name``."""

        self.files[name] = content

    # ------------------------------------------------------------------
    def replicate(self, name: str, content: bytes, peers: Optional[Iterable["MeshPeer"]] = None) -> None:
        """Replicate ``content`` to ``peers``.

        If ``peers`` is ``None`` the file is replicated to all discovered peers
        except the owner itself.  The file is stored locally as well.
        """

        # Store locally first.
        self.store_file(name, content)

        from .mesh_peer import MeshPeer

        targets: Iterable[MeshPeer]
        if peers is None:
            targets = self.peer.discover_peers().values()
        else:
            targets = peers

        size = len(content)
        for target in targets:
            if not self.peer.bandwidth_balancer.can_send(size):
                raise RuntimeError("bandwidth exceeded")
            target.file_replicator.store_file(name, content)


__all__ = ["FileReplicator"]

