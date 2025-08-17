"""Simple adult content filter.

TODO:
- Telemetry: emit events when content is flagged.
- Metrics: track false positives and negatives.
- Security: expand vocabulary and context-aware checks.
- Resiliency: allow dynamic rule updates without downtime.
"""
from __future__ import annotations

import re

BANNED_WORDS = {"explicit", "nsfw"}


def contains_adult_content(text: str) -> bool:
    pattern = re.compile("|".join(re.escape(w) for w in BANNED_WORDS), re.I)
    return bool(pattern.search(text))


__all__ = ["contains_adult_content"]
