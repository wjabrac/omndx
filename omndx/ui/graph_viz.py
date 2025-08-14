"""Render simple task graphs using Graphviz."""

from __future__ import annotations

from typing import Iterable, Mapping, Optional

try:  # pragma: no cover - dependency optional at runtime
    from graphviz import Digraph
except Exception:  # pragma: no cover - fallback when graphviz missing
    Digraph = None  # type: ignore


def render_task_graph(graph: Mapping[str, Iterable[str]], filename: Optional[str] = None) -> str:
    """Render *graph* as Graphviz DOT source.

    Parameters
    ----------
    graph:
        Mapping of node names to an iterable of child node names.
    filename:
        Optional path to write the generated DOT representation.  The
        function returns the DOT source in all cases allowing callers to
        further process or render the graph externally.
    """

    if Digraph is None:
        # Fallback: manually compose DOT representation without relying on
        # the ``graphviz`` package.  This keeps the function usable in
        # minimal environments such as the unit tests.
        lines = ["digraph G {"]
        for src, dsts in graph.items():
            if not dsts:
                lines.append(f'    "{src}";')
            for dst in dsts:
                lines.append(f'    "{src}" -> "{dst}";')
        lines.append("}")
        dot_source = "\n".join(lines)
        if filename:
            with open(filename, "w", encoding="utf8") as fh:
                fh.write(dot_source)
        return dot_source

    dot = Digraph()
    for src, dsts in graph.items():
        dot.node(src)
        for dst in dsts:
            dot.node(dst)
            dot.edge(src, dst)

    if filename:
        dot.save(filename)

    return dot.source


__all__ = ["render_task_graph"]

