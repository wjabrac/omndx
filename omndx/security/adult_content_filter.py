"""Heuristic based adult content filtering.

The :class:`AdultContentFilter` class provides a very small text based filter
that checks input for a list of blocked keywords.  The intent is to allow test
scenarios to easily flag obviously inappropriate content without relying on
heavy machine learning models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Set


@dataclass
class AdultContentFilter:
    """Simple keyword driven content filter."""

    blocked_keywords: Set[str] = field(
        default_factory=lambda: {
            "porn",
            "xxx",
            "sex",
            "nude",
        }
    )

    def is_safe(self, text: str) -> bool:
        """Return ``True`` if *text* does not contain blocked terms."""

        lowered = text.lower()
        return not any(word in lowered for word in self.blocked_keywords)

    def filter(self, items: Iterable[str]) -> Iterable[str]:
        """Yield only items that pass :meth:`is_safe`."""

        for item in items:
            if self.is_safe(item):
                yield item


__all__ = ["AdultContentFilter"]

