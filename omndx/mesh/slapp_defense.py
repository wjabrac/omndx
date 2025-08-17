"""Minimal SLAPP (Strategic Lawsuit Against Public Participation) defence placeholder.

TODO:
- Telemetry: flag suspicious message events.
- Metrics: count potential SLAPP attempts over time.
- Security: integrate with content moderation and legal review.
- Resiliency: support configurable rule sets and updates.
"""
from __future__ import annotations


def is_suspicious(message: str) -> bool:
    """Very naive check for abusive content."""
    banned = {"lawsuit", "cease and desist"}
    text = message.lower()
    return any(term in text for term in banned)


__all__ = ["is_suspicious"]
