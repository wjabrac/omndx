"""In-memory task metadata registry."""

from __future__ import annotations

from typing import Any, Dict


class TaskRegistry:
    """Simple registry exposing CRUD operations for task metadata."""

    def __init__(self) -> None:
        self._tasks: Dict[int, Dict[str, Any]] = {}
        self._counter = 0

    # ------------------------------------------------------------------
    def create(self, metadata: Dict[str, Any]) -> int:
        """Store *metadata* and return a new task identifier."""

        self._counter += 1
        self._tasks[self._counter] = dict(metadata)
        return self._counter

    # ------------------------------------------------------------------
    def read(self, task_id: int) -> Dict[str, Any]:
        """Return metadata for *task_id*."""

        return dict(self._tasks[task_id])

    # ------------------------------------------------------------------
    def update(self, task_id: int, metadata: Dict[str, Any]) -> None:
        """Update *task_id* with new *metadata*."""

        self._tasks[task_id].update(metadata)

    # ------------------------------------------------------------------
    def delete(self, task_id: int) -> None:
        """Remove *task_id* from the registry."""

        del self._tasks[task_id]

    # ------------------------------------------------------------------
    def all(self) -> Dict[int, Dict[str, Any]]:
        """Return a mapping of all registered tasks."""

        return dict(self._tasks)


__all__ = ["TaskRegistry"]
