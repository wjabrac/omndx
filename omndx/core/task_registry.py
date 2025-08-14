"""Central registry for OMNDX task definitions.

The :class:`TaskRegistry` keeps track of available tasks and their associated
metadata.  The skeleton below documents the functionality required for a
robust registry service.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


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

    Completion steps:

    * Back the registry with a durable database or configuration store.
    * Provide thread-safe registration and retrieval operations.
    * Validate ``TaskMetadata`` against a schema before insertion.
    * Support task deprecation and versioned lookups.
    * Expose metrics for registry hits/misses and audit all modifications.
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, TaskMetadata] = {}

    def register(self, metadata: TaskMetadata) -> None:
        """Add or update a task definition.

        Implementation notes:

        * Ensure concurrent registrations are serialised and atomic.
        * Reject incompatible versions or malformed metadata.
        * Persist changes to durable storage and emit audit logs.
        """
        raise NotImplementedError("TaskRegistry.register is not yet implemented")

    def get(self, name: str, version: Optional[str] = None) -> TaskMetadata:
        """Retrieve metadata for ``name`` and optional ``version``.

        Implementation notes:

        * Support latest-version resolution when ``version`` is ``None``.
        * Handle cache population and eviction policies.
        * Raise descriptive errors when a task is missing or deprecated.
        """
        raise NotImplementedError("TaskRegistry.get is not yet implemented")
