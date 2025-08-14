"""Lightweight web dashboard built with FastAPI."""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI

from ..core import TagLogger


def create_app(logger: Optional[TagLogger] = None) -> FastAPI:
    """Create and configure a FastAPI application.

    The application exposes a handful of endpoints that exercise the
    :class:`TagLogger` for demonstration purposes.
    """

    logger = logger or TagLogger("web")
    app = FastAPI()

    @app.get("/ping")
    def ping() -> dict[str, str]:  # pragma: no cover - trivial
        return {"status": "ok"}

    @app.post("/start")
    def start() -> dict[str, bool]:
        logger.info("start requested", tag="start")
        return {"started": True}

    @app.get("/metrics")
    def metrics() -> dict[str, int]:
        return logger.get_metrics()

    # Expose the logger via the application state for consumers that may
    # want direct access.
    app.state.logger = logger
    return app


def run(host: str = "127.0.0.1", port: int = 8000, logger: Optional[TagLogger] = None) -> None:
    """Run the FastAPI application using ``uvicorn``."""

    import uvicorn

    uvicorn.run(create_app(logger), host=host, port=port)


__all__ = ["create_app", "run"]

