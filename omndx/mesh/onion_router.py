"""Simple onion routing simulation.

The real world concept of onion routing involves wrapping a message in layers
of encryption and forwarding it through a number of intermediate peers.  Each
peer peels away a single layer thereby revealing the address of the next hop
until the final recipient is reached.  Implementing the cryptographic aspects
is far beyond the scope of this repository, however a tiny subset of the
behaviour is useful for unit tests.

The :class:`OnionRouter` class provided here performs purely logical routing –
no encryption is attempted.  A message is forwarded through a list of peer
identifiers, and only the final peer receives the delivered message.  The
intermediate hops do not retain the message which mirrors the anonymity aspect
of onion routing.
"""

from __future__ import annotations

from typing import List


class OnionRouter:
    """Light-weight onion routing helper."""

    def __init__(self, peer: "MeshPeer") -> None:
        self.peer = peer

    # ------------------------------------------------------------------
    def send_onion(self, target_id: str, message: str, path: List[str]) -> None:
        """Send ``message`` to ``target_id`` via the supplied ``path``.

        The ``path`` parameter lists the intermediate peers that should receive
        the message before it reaches ``target_id``.  It does **not** include the
        target itself; the router appends it automatically.  The source peer is
        inferred from ``self.peer``.
        """

        full_path = list(path) + [target_id]
        self._forward(full_path, message, self.peer.peer_id)

    # ------------------------------------------------------------------
    def _forward(self, remaining_path: List[str], message: str, origin: str) -> None:
        """Forward a message to the next hop.

        ``origin`` identifies the peer that originally sent the message.  This
        value is ultimately delivered to the final recipient.
        """

        next_hop = remaining_path[0]
        rest = remaining_path[1:]

        # Import is done lazily to avoid circular import at module level.
        from .mesh_peer import MeshPeer

        peer = MeshPeer.get_peer(next_hop)
        if peer is None:
            raise ValueError(f"unknown peer: {next_hop}")

        if rest:
            peer.onion_router._forward(rest, message, origin)
        else:
            peer.receive_message(origin, message)


__all__ = ["OnionRouter"]

