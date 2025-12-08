from omndx.security.secure_config_store import SecureConfigStore


def test_secure_config_replication_and_rotation() -> None:
    replica = SecureConfigStore("key1")
    store = SecureConfigStore("key1", replicas=[replica])

    store.set("api_key", "secret")
    assert store.get("api_key") == "secret"
    assert replica.get("api_key") == "secret"

    store.rotate("new-key")
    assert store.get("api_key") == "secret"
    assert replica.get("api_key") == "secret"


def test_secure_config_missing_key_raises() -> None:
    store = SecureConfigStore("key1")
    store.set("token", "abc")
    try:
        store.get("missing")
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")
