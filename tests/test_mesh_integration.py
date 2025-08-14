"""Integration tests for the in-memory mesh network components."""

from __future__ import annotations

import os
import sys

# Ensure the package root is on the import path for the tests executed from the
# repository root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from omndx.mesh.bandwidth_balancer import BandwidthBalancer
from omndx.mesh.mesh_peer import MeshPeer


def setup_function() -> None:
    """Clear the peer registry before each test."""

    MeshPeer.clear_registry()


def test_onion_routed_message() -> None:
    """Messages can be routed through intermediate peers without disclosure."""

    peer_a = MeshPeer("A", bandwidth_balancer=BandwidthBalancer(1024))
    peer_b = MeshPeer("B", bandwidth_balancer=BandwidthBalancer(1024))
    peer_c = MeshPeer("C", bandwidth_balancer=BandwidthBalancer(1024))

    peer_a.send_message("B", "secret", path=["C"])  # route through C

    # Only the final recipient should have the message.
    assert peer_b.inbox == [("A", "secret")]
    assert peer_c.inbox == []


def test_file_replication() -> None:
    peer_a = MeshPeer("A", bandwidth_balancer=BandwidthBalancer(1024))
    peer_b = MeshPeer("B", bandwidth_balancer=BandwidthBalancer(1024))
    peer_c = MeshPeer("C", bandwidth_balancer=BandwidthBalancer(1024))

    data = b"payload"
    peer_a.file_replicator.replicate("data.bin", data)

    assert peer_b.file_replicator.files["data.bin"] == data
    assert peer_c.file_replicator.files["data.bin"] == data


def test_bandwidth_throttling() -> None:
    peer_a = MeshPeer("A", bandwidth_balancer=BandwidthBalancer(5))
    MeshPeer("B")  # recipient

    with pytest.raises(RuntimeError):
        peer_a.send_message("B", "too long")

