"""User interface components and interaction helpers.

TODO:
- Telemetry: centralize UI event tracking.
- Metrics: measure user engagement and latency.
- Security: sanitize user inputs across interfaces.
- Resiliency: ensure components degrade gracefully offline.
"""

from .observability_dashboard import ObservabilityLinks

__all__ = ["ObservabilityLinks"]

