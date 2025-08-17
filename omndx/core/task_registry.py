"""Central registry for OMNDX task definitions.

The :class:`TaskRegistry` keeps track of available tasks and their associated
metadata.  The skeleton below documents the functionality required for a
robust registry service.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
import threading
from typing import Any, Dict, Optional

from packaging import version as pkg_version


@dataclass
class TaskMetadata:
    """Describes a registered task.

    Fields to implement:

    * ``name`` - human-readable identifier.
    * ``version`` - semantic version of the task contract.
    * ``description`` - short summary for documentation.
    * ``schema`` - machine-readable specification of expected inputs/outputs.
    * ``owner`` - contact or team responsible for the task.
    """

    name: str
    version: str
    description: str
    schema: Dict[str, Any]
    owner: str


class TaskRegistry:
    """Stores and retrieves task metadata.

    The registry is backed by a simple SQLite database and guarded by a
    :class:`threading.Lock` to provide basic concurrency safety.  All task
    definitions are also cached in-memory for quick lookups.
    """

    def __init__(self, db_path: str = "task_registry.sqlite") -> None:
        self._lock = threading.Lock()
        self._db_path = db_path
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                description TEXT NOT NULL,
                schema TEXT NOT NULL,
                owner TEXT NOT NULL,
                PRIMARY KEY (name, version)
            )
            """
        )
        self._conn.commit()

        # Cache: {name: {version: TaskMetadata}}
        self._tasks: Dict[str, Dict[str, TaskMetadata]] = {}
        self._load_from_db()

    def _load_from_db(self) -> None:
        cur = self._conn.execute("SELECT name, version, description, schema, owner FROM tasks")
        for name, ver, desc, schema_json, owner in cur.fetchall():
            schema = json.loads(schema_json)
            metadata = TaskMetadata(name=name, version=ver, description=desc, schema=schema, owner=owner)
            self._tasks.setdefault(name, {})[ver] = metadata
        cur.close()

    @staticmethod
    def _validate(metadata: TaskMetadata) -> None:
        if not metadata.name:
            raise ValueError("Task name must be non-empty")
        if not metadata.version:
            raise ValueError("Task version must be non-empty")
        if not isinstance(metadata.schema, dict):
            raise ValueError("Task schema must be a dictionary")

    def register(self, metadata: TaskMetadata) -> None:
        """Add or update a task definition.

        Registration is thread-safe and persisted to the underlying SQLite
        database.  Metadata is validated prior to insertion.
        """

        self._validate(metadata)
        with self._lock:
            self._conn.execute(
                "REPLACE INTO tasks (name, version, description, schema, owner) VALUES (?, ?, ?, ?, ?)",
                (
                    metadata.name,
                    metadata.version,
                    metadata.description,
                    json.dumps(metadata.schema),
                    metadata.owner,
                ),
            )
            self._conn.commit()

            self._tasks.setdefault(metadata.name, {})[metadata.version] = metadata

    def get(self, name: str, version: Optional[str] = None) -> TaskMetadata:
        """Retrieve metadata for ``name`` and optional ``version``.

        When ``version`` is ``None`` the latest semantic version is returned.
        A ``KeyError`` is raised if the task or version cannot be found.
        """

        with self._lock:
            versions = self._tasks.get(name)
            if not versions:
                raise KeyError(f"Task '{name}' is not registered")

            if version is None:
                latest = max(versions, key=lambda v: pkg_version.parse(v))
                return versions[latest]

            if version not in versions:
                raise KeyError(f"Task '{name}' has no version '{version}'")

            return versions[version]
