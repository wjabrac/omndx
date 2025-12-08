from omndx.mesh.mesh_peer import MeshPeer


def test_mesh_peer_encrypted_flow() -> None:
    sender = MeshPeer("a", shared_key="k")
    receiver = MeshPeer("b", shared_key="k")

    assert sender.send(receiver, "hello") is True
    assert receiver.receive() == ["hello"]


def test_mesh_peer_offline_and_error_handling() -> None:
    sender = MeshPeer("a")
    receiver = MeshPeer("b", online=False)

    assert sender.send(receiver, "test") is False
    # receiving empty list when nothing delivered
    assert receiver.receive() == []
