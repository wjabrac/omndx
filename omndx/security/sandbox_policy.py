"""Simple sandbox policy helpers.

The :class:`SandboxPolicy` context manager replaces a handful of built-in
functions to prevent access to the local file system and network.  It is a
minimal safeguard designed for testing and demonstration purposes and should
not be considered a full security solution.
"""

from __future__ import annotations

import builtins
import os
import socket
from typing import Iterable, List


class SandboxPolicy:
    """Context manager enforcing basic sandboxing rules.

    Parameters
    ----------
    allowed_paths:
        Optional iterable of directory paths that remain accessible while the
        policy is active.  Any access outside these paths results in a
        :class:`PermissionError`.
    """

    def __init__(self, allowed_paths: Iterable[str] | None = None) -> None:
        self.allowed_paths: List[str] = []
        if allowed_paths:
            for path in allowed_paths:
                self.allowed_paths.append(os.path.abspath(path))

        self._orig_open = builtins.open
        self._orig_socket = socket.socket

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _is_allowed(self, path: str) -> bool:
        abspath = os.path.abspath(path)
        return any(abspath.startswith(p) for p in self.allowed_paths)

    def _sandboxed_open(self, file, *args, **kwargs):  # type: ignore[override]
        if not self._is_allowed(file):
            raise PermissionError("File system access denied")
        return self._orig_open(file, *args, **kwargs)

    def _sandboxed_socket(self, *args, **kwargs):  # pragma: no cover - trivial
        raise PermissionError("Network access disabled")

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------
    def __enter__(self) -> "SandboxPolicy":
        builtins.open = self._sandboxed_open
        socket.socket = self._sandboxed_socket  # type: ignore[assignment]
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401 - standard CM
        builtins.open = self._orig_open
        socket.socket = self._orig_socket  # type: ignore[assignment]


__all__ = ["SandboxPolicy"]

