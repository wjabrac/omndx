"""Simple RabbitMQ client wrapper.

Provides minimal publish/consume helpers around :mod:`pika`.  The class is
resilient to the absence of the library or a running broker, allowing the rest
of the system to operate without RabbitMQ.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Callable, Optional

try:  # pragma: no cover - optional dependency
    import pika
except Exception:  # pragma: no cover - fallback when pika is unavailable
    pika = None  # type: ignore


logger = logging.getLogger(__name__)


class RabbitMQClient:
    """Minimal convenience wrapper for RabbitMQ."""

    def __init__(self, url: str = "amqp://guest:guest@localhost:5672/%2F") -> None:
        self.url = url
        self._connection: Optional["pika.BlockingConnection"] = None
        self._channel: Optional["pika.channel.Channel"] = None
        if pika:
            try:
                params = pika.URLParameters(url)
                self._connection = pika.BlockingConnection(params)
                self._channel = self._connection.channel()
            except Exception:  # pragma: no cover - external service
                logger.warning("RabbitMQ connection failed", exc_info=True)
        else:
            logger.warning("pika not installed; RabbitMQClient disabled")

    # ------------------------------------------------------------------
    def publish(self, queue: str, message: Any) -> None:
        """Publish *message* to *queue* if a channel is available."""

        if not self._channel:  # pragma: no cover - safety guard
            return
        try:
            self._channel.queue_declare(queue=queue, durable=True)
            body = json.dumps(message)
            self._channel.basic_publish(exchange="", routing_key=queue, body=body)
        except Exception:  # pragma: no cover - external service
            logger.warning("Failed to publish to RabbitMQ", exc_info=True)

    def consume(self, queue: str, callback: Callable[[Any], None]) -> None:
        """Consume messages from *queue* delivering JSON payloads to *callback*.

        This method blocks; it is intended for simple integration scenarios.
        """

        if not self._channel:  # pragma: no cover - safety guard
            return
        try:
            self._channel.queue_declare(queue=queue, durable=True)

            def _on_message(ch, method, props, body):
                try:
                    payload = json.loads(body.decode("utf-8"))
                except Exception:  # pragma: no cover - defensive
                    payload = body
                callback(payload)

            self._channel.basic_consume(queue=queue, on_message_callback=_on_message, auto_ack=True)
            self._channel.start_consuming()
        except Exception:  # pragma: no cover - external service
            logger.warning("Failed to consume from RabbitMQ", exc_info=True)


__all__ = ["RabbitMQClient"]
