"""Sandbox policy declaration.

TODO:
- Telemetry: audit denied syscall attempts.
- Metrics: monitor frequency of sandbox violations.
- Security: expand policy to cover filesystem and network access.
- Resiliency: provide dynamic policy updates without restarts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set


@dataclass
class SandboxPolicy:
    allowed_syscalls: Set[str] = field(default_factory=set)

    def is_allowed(self, syscall: str) -> bool:
        return syscall in self.allowed_syscalls


__all__ = ["SandboxPolicy"]
