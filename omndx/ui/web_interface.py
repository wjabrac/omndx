"""Very small web interface using the standard library.

TODO:
- Telemetry: instrument requests and responses.
- Metrics: expose uptime and per-endpoint timing.
- Security: add authentication and input validation.
- Resiliency: support graceful shutdown and restart.
"""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # pragma: no cover - network side effect
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OMNDX running")


def serve(port: int = 8000) -> HTTPServer:
    server = HTTPServer(("", port), _Handler)
    return server


__all__ = ["serve"]
