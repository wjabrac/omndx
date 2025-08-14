"""Bandwidth balancing utilities for mesh peers."""

from __future__ import annotations


class BandwidthBalancer:
    """Simple token based bandwidth balancer.

    The balancer tracks the number of bytes a peer has sent.  Each instance has
    a ``max_bandwidth`` which represents the total number of bytes that may be
    sent until the counter is reset.  The implementation is intentionally
    minimal and does not attempt to model time slices – tests are expected to
    reset the balancer manually when needed.
    """

    def __init__(self, max_bandwidth: int) -> None:
        self.max_bandwidth = max_bandwidth
        self._used = 0

    # ------------------------------------------------------------------
    def can_send(self, size: int) -> bool:
        """Return ``True`` if ``size`` bytes may be sent.

        If sending the data would exceed the maximum bandwidth the method
        returns ``False``.  Otherwise the internal counter is incremented and
        ``True`` is returned.
        """

        if self._used + size > self.max_bandwidth:
            return False
        self._used += size
        return True

    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Reset the used bandwidth counter."""

        self._used = 0


__all__ = ["BandwidthBalancer"]

