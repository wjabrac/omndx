import pytest

from omndx.core.task_registry import TaskRegistry, TaskMetadata


def _make_registry(tmp_path):
    db_path = tmp_path / "tasks.sqlite"
    return TaskRegistry(db_path=str(db_path))


def test_register_and_get(tmp_path):
    registry = _make_registry(tmp_path)
    meta = TaskMetadata(
        name="test",
        version="1.0.0",
        description="desc",
        schema={"input": "str"},
        owner="owner",
    )
    registry.register(meta)

    fetched = registry.get("test", "1.0.0")
    assert fetched == meta


def test_latest_version_resolution(tmp_path):
    registry = _make_registry(tmp_path)
    v1 = TaskMetadata(
        name="task",
        version="1.0.0",
        description="v1",
        schema={},
        owner="me",
    )
    v2 = TaskMetadata(
        name="task",
        version="1.2.0",
        description="v2",
        schema={},
        owner="me",
    )
    registry.register(v1)
    registry.register(v2)

    latest = registry.get("task")
    assert latest.version == "1.2.0"


def test_missing_raises(tmp_path):
    registry = _make_registry(tmp_path)
    with pytest.raises(KeyError):
        registry.get("unknown")

    registry.register(
        TaskMetadata(
            name="task",
            version="1.0.0",
            description="v1",
            schema={},
            owner="me",
        )
    )
    with pytest.raises(KeyError):
        registry.get("task", "2.0.0")
