"""Generate Graphviz DOT representations of task graphs.

TODO:
- Telemetry: log visualization requests.
- Metrics: track graph sizes and generation time.
- Security: sanitize node labels to prevent injection.
- Resiliency: handle large graphs without crashing.
"""
from __future__ import annotations

from typing import Iterable, Tuple


def to_dot(edges: Iterable[Tuple[str, str]]) -> str:
    lines = ["digraph G {"]
    for src, dst in edges:
        lines.append(f"  {src} -> {dst};")
    lines.append("}")
    return "\n".join(lines)


__all__ = ["to_dot"]
