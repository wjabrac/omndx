from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Protocol
import uuid
import fcntl

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None

try:  # optional observability stack
    from opentelemetry import metrics, trace  # type: ignore
    from opentelemetry.sdk.metrics import MeterProvider  # type: ignore
    from opentelemetry.sdk.metrics.export import (
        MetricExporter,
        MetricExportResult,
        PeriodicExportingMetricReader,
    )  # type: ignore
    from opentelemetry.sdk.resources import Resource  # type: ignore
    from opentelemetry.sdk.trace import TracerProvider  # type: ignore
    from opentelemetry.sdk.trace.export import (
        SimpleSpanProcessor,
        SpanExportResult,
        SpanExporter,
    )  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    trace = None
    metrics = None


# ---------------------------------------------------------------------------
# Configuration and task models
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class OrchestratorConfig:
    """Declarative configuration for the orchestrator.

    Parameters may be loaded from JSON/YAML and overridden at runtime.
    """

    max_concurrency: int = 5
    retry_attempts: int = 3
    backoff_factor: float = 0.5
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 30.0
    task_timeout: float = 30.0
    service_rate_limits: Dict[str, tuple[int, float]] = field(default_factory=dict)
    service_concurrency: Dict[str, int] = field(default_factory=dict)
    autoscale_interval: float = 0.5
    wal_path: str | Path = Path("orchestrator.wal")
    leader_lock_path: str | Path | None = None
    trace_file: str | Path | None = None
    metrics_file: str | Path | None = None
    admin_port: int | None = None

    def __post_init__(self) -> None:
        self.wal_path = Path(self.wal_path)
        if self.leader_lock_path is not None:
            self.leader_lock_path = Path(self.leader_lock_path)
        if self.trace_file is not None:
            self.trace_file = Path(self.trace_file)
        if self.metrics_file is not None:
            self.metrics_file = Path(self.metrics_file)

    @classmethod
    def from_file(cls, path: str | Path, **overrides: Any) -> "OrchestratorConfig":
        data: Dict[str, Any]
        p = Path(path)
        if p.suffix in {".yaml", ".yml"}:
            if yaml is None:
                raise RuntimeError("pyyaml required to load YAML config")
            data = yaml.safe_load(p.read_text())
        else:
            data = json.loads(p.read_text())
        data.update(overrides)
        return cls(**data)


@dataclass(slots=True)
class TaskSpec:
    service: str
    payload: Dict[str, Any]
    priority: int = 0
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: str = field(default="pending")
    result: Any = field(default=None)
    retries: int = field(default=0)
    start_time: float | None = field(default=None)
    end_time: float | None = field(default=None)
    deadline: float | None = None


@dataclass(order=True, slots=True)
class _QueuedTask:
    priority: int
    task_id: str = field(compare=False)


@dataclass(slots=True)
class _CircuitState:
    failures: int = 0
    opened_at: float | None = None

    def allow(self, threshold: int, timeout: float) -> bool:
        if self.opened_at is None:
            return True
        if time.time() - self.opened_at > timeout:
            # Reset circuit after cooldown
            self.failures = 0
            self.opened_at = None
            return True
        return False

    def record_success(self) -> None:
        self.failures = 0
        self.opened_at = None

    def record_failure(self, threshold: int) -> None:
        self.failures += 1
        if self.failures >= threshold and self.opened_at is None:
            self.opened_at = time.time()


@dataclass(slots=True)
class _TokenBucket:
    capacity: int
    refill_rate: float
    tokens: float = field(init=False)
    updated: float = field(default_factory=time.monotonic)

    def __post_init__(self) -> None:
        self.tokens = float(self.capacity)

    def consume(self, amount: int = 1) -> tuple[bool, float]:
        now = time.monotonic()
        elapsed = now - self.updated
        self.updated = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        if self.tokens >= amount:
            self.tokens -= amount
            return True, 0.0
        needed = amount - self.tokens
        return False, needed / self.refill_rate if self.refill_rate else float('inf')


class WriteAheadLog:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    async def append(self, record: Dict[str, Any]) -> None:
        line = json.dumps(record)
        async with self._lock:
            await asyncio.to_thread(self._write, line)

    def _write(self, line: str) -> None:
        with self.path.open("a") as f:
            f.write(line + "\n")

    async def load(self) -> list[Dict[str, Any]]:
        if not self.path.exists():
            return []
        return await asyncio.to_thread(self._read)

    def _read(self) -> list[Dict[str, Any]]:
        with self.path.open() as f:
            return [json.loads(line) for line in f.read().splitlines() if line]


class FileLeaderElector:
    def __init__(self, path: Path):
        self.path = path
        self._fh: Any | None = None

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fh = self.path.open("w")
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            fh.close()
            return False
        self._fh = fh
        return True

    def release(self) -> None:
        if self._fh:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
            self._fh.close()
            self._fh = None


class FileSpanExporter(SpanExporter):
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def export(self, spans: list[Any]) -> SpanExportResult:  # pragma: no cover - invoked indirectly
        with self.path.open("a") as f:
            for span in spans:
                data = {
                    "name": span.name,
                    "context": f"{span.context.trace_id:x}:{span.context.span_id:x}",
                    "attributes": dict(span.attributes),
                }
                f.write(json.dumps(data) + "\n")
        return SpanExportResult.SUCCESS


class FileMetricExporter(MetricExporter):
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def export(self, metrics_data: list[Any]) -> MetricExportResult:  # pragma: no cover
        with self.path.open("a") as f:
            for record in metrics_data:
                f.write(repr(record) + "\n")
        return MetricExportResult.SUCCESS


class AdminServer:
    def __init__(self, orch: "Orchestrator", port: int) -> None:
        self.orch = orch
        self.port = port
        self._server: asyncio.AbstractServer | None = None

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle, "127.0.0.1", self.port)
        sock = self._server.sockets[0]
        self.port = int(sock.getsockname()[1])

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        data = await reader.read(65536)
        request = data.decode()
        method, path, _ = request.partition("\r\n")[0].split(" ")
        body = ""
        if "\r\n\r\n" in request:
            body = request.split("\r\n\r\n", 1)[1]
        if method == "GET" and path == "/status":
            payload = json.dumps(self.orch.status()).encode()
            response = (
                b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: "
                + str(len(payload)).encode()
                + b"\r\n\r\n"
                + payload
            )
        elif method == "POST" and path == "/config":
            overrides = json.loads(body or "{}")
            changes = self.orch.update_config(overrides)
            payload = json.dumps({"ok": True, "changes": changes}).encode()
            response = (
                b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: "
                + str(len(payload)).encode()
                + b"\r\n\r\n"
                + payload
            )
        else:
            response = b"HTTP/1.1 404 Not Found\r\nContent-Length:0\r\n\r\n"
        writer.write(response)
        await writer.drain()
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()


# ---------------------------------------------------------------------------
# Service protocol and orchestrator implementation
# ---------------------------------------------------------------------------


class Service(Protocol):
    name: str

    async def run(self, payload: Dict[str, Any]) -> Any:
        ...


class Orchestrator:
    """Concurrent task orchestrator with retry, backoff and circuit breaker."""

    def __init__(
        self,
        config: OrchestratorConfig | None = None,
        services: Optional[list[Service]] = None,
        *,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.config = config or OrchestratorConfig()
        self.services: Dict[str, Service] = {
            svc.name: svc for svc in services or []
        }
        self.logger = logger or logging.getLogger("omndx.orchestrator")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        self._queue: "asyncio.PriorityQueue[_QueuedTask]" = asyncio.PriorityQueue()
        self._tasks: Dict[str, TaskSpec] = {}
        self._running: Dict[str, asyncio.Task] = {}
        self._circuit: Dict[str, _CircuitState] = {}
        self._rate_limits: Dict[str, _TokenBucket] = {
            name: _TokenBucket(capacity, rate)
            for name, (capacity, rate) in self.config.service_rate_limits.items()
        }
        self._semaphores: Dict[str, asyncio.Semaphore] = {
            name: asyncio.Semaphore(limit)
            for name, limit in self.config.service_concurrency.items()
        }
        self._shutdown = asyncio.Event()
        self._workers: list[asyncio.Task] = []
        self._scaler: asyncio.Task | None = None
        self._wal = WriteAheadLog(self.config.wal_path)
        lock_path = self.config.leader_lock_path or self.config.wal_path.with_suffix(".lock")
        self._leader = FileLeaderElector(Path(lock_path))
        self._admin: AdminServer | None = None

        # observability
        self.tracer = None
        self.meter = None
        if trace is not None and metrics is not None:
            resource = Resource.create({"service.name": "omndx-orchestrator"})
            tp = trace.get_tracer_provider()
            if not isinstance(tp, TracerProvider):
                tp = TracerProvider(resource=resource)
                trace.set_tracer_provider(tp)
            if self.config.trace_file:
                tp.add_span_processor(
                    SimpleSpanProcessor(FileSpanExporter(Path(self.config.trace_file)))
                )
            self.tracer = trace.get_tracer(__name__)

            mp = metrics.get_meter_provider()
            if not isinstance(mp, MeterProvider):
                mp = MeterProvider(resource=resource)
                metrics.set_meter_provider(mp)
            if self.config.metrics_file:
                exporter = FileMetricExporter(Path(self.config.metrics_file))
                reader = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
                mp.add_metric_reader(reader)
            self.meter = metrics.get_meter(__name__)
            self._metric_tasks_succeeded = (
                self.meter.create_counter("tasks_succeeded") if self.meter else None
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, service: Service) -> None:
        self.services[service.name] = service

    def status(self) -> Dict[str, Any]:
        return {
            "queue": self._queue.qsize(),
            "tasks": {tid: t.status for tid, t in self._tasks.items()},
        }

    def update_config(self, overrides: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        changes: Dict[str, Dict[str, Any]] = {}
        for key, value in overrides.items():
            if hasattr(self.config, key):
                old = getattr(self.config, key)
                setattr(self.config, key, value)
                changes[key] = {"old": old, "new": value}
        if changes:
            asyncio.create_task(self._wal.append({"event": "config_override", "changes": changes}))
        return changes

    async def add_task(
        self,
        service: str,
        payload: Dict[str, Any],
        *,
        priority: int = 0,
        deadline: float | None = None,
    ) -> str:
        bucket = self._rate_limits.get(service)
        if bucket:
            allowed, retry_after = bucket.consume()
            if not allowed:
                raise RuntimeError(f"rate limit exceeded; retry after {retry_after:.2f}s")
        task = TaskSpec(service=service, payload=payload, priority=priority, deadline=deadline)
        self._tasks[task.id] = task
        await self._queue.put(_QueuedTask(priority, task.id))
        await self._wal.append({"event": "add", "task": asdict(task)})
        self._log("info", "task_submitted", task_id=task.id, service=service)
        return task.id

    async def cancel_task(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False
        if task.status == "pending":
            task.status = "cancelled"
            await self._wal.append({"event": "status", "task_id": task.id, "status": task.status})
            return True
        if task.status == "running":
            running = self._running.get(task_id)
            if running:
                running.cancel()
            task.status = "cancelled"
            await self._wal.append({"event": "status", "task_id": task.id, "status": task.status})
            return True
        return False

    async def join(self) -> None:
        await self._queue.join()

    async def start(self) -> None:
        if self._workers or self._scaler:
            return
        if not self._leader.acquire():
            raise RuntimeError("orchestrator already active")
        await self._recover()
        self._shutdown.clear()
        self._workers.append(asyncio.create_task(self._worker()))
        self._scaler = asyncio.create_task(self._autoscale())
        if self.config.admin_port is not None:
            self._admin = AdminServer(self, self.config.admin_port)
            await self._admin.start()
            self.config.admin_port = self._admin.port

    async def stop(self) -> None:
        self._shutdown.set()
        if self._admin:
            await self._admin.stop()
            self._admin = None
        if self._scaler:
            self._scaler.cancel()
            with contextlib.suppress(BaseException):
                await self._scaler
            self._scaler = None
        for w in self._workers:
            w.cancel()
        with contextlib.suppress(Exception):
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        self._leader.release()

    async def __aenter__(self) -> "Orchestrator":
        await self.start()
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.stop()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _worker(self) -> None:
        while not self._shutdown.is_set():
            try:
                queued = await asyncio.wait_for(self._queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                continue

            task = self._tasks.get(queued.task_id)
            if not task or task.status == "cancelled":
                self._queue.task_done()
                continue

            if task.deadline and time.time() > task.deadline:
                task.status = "failed"
                self._log(
                    "error", "task_deadline_exceeded", task_id=task.id, service=task.service
                )
                self._queue.task_done()
                continue

            if not self._circuit_allow(task.service):
                # Requeue later with backoff
                await asyncio.sleep(self.config.backoff_factor)
                await self._queue.put(queued)
                self._queue.task_done()
                continue

            svc = self.services.get(task.service)
            if not svc:
                task.status = "failed"
                self._queue.task_done()
                self._log("error", "service_missing", task_id=task.id, service=task.service)
                continue

            task.status = "running"
            task.start_time = time.time()

            async def _run() -> Any:
                sem = self._semaphores.get(task.service)
                if self.tracer:
                    span_cm = self.tracer.start_as_current_span(
                        task.service, attributes={"task_id": task.id}
                    )
                else:
                    span_cm = contextlib.nullcontext()
                with span_cm:
                    if sem:
                        async with sem:
                            return await self._execute_with_retry(svc, task)
                    return await self._execute_with_retry(svc, task)

            runner = asyncio.create_task(_run())
            self._running[task.id] = runner
            try:
                task.result = await runner
                task.status = "succeeded"
                self._circuit.setdefault(task.service, _CircuitState()).record_success()
                self._log("info", "task_succeeded", task_id=task.id, service=task.service)
            except Exception as exc:  # pragma: no cover - exercised in tests
                task.status = "failed"
                self._log(
                    "error",
                    "task_failed",
                    task_id=task.id,
                    service=task.service,
                    error=str(exc),
                )
            finally:
                task.end_time = time.time()
                self._running.pop(task.id, None)
                await self._wal.append({"event": "status", "task_id": task.id, "status": task.status})
                if self._metric_tasks_succeeded and task.status == "succeeded":
                    self._metric_tasks_succeeded.add(1)
                self._queue.task_done()

    async def _execute_with_retry(self, svc: Service, task: TaskSpec) -> Any:
        last_exc: Exception | None = None
        for attempt in range(self.config.retry_attempts):
            try:
                timeout = self.config.task_timeout
                if task.deadline is not None:
                    timeout = min(timeout, max(0.0, task.deadline - time.time()))
                return await asyncio.wait_for(svc.run(task.payload), timeout=timeout)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - retried in tests
                last_exc = exc
                task.retries += 1
                self._circuit.setdefault(task.service, _CircuitState()).record_failure(
                    self.config.circuit_breaker_threshold
                )
                if attempt + 1 >= self.config.retry_attempts:
                    break
                backoff = self.config.backoff_factor * 2 ** attempt
                self._log(
                    "warning",
                    "task_retry",
                    task_id=task.id,
                    service=task.service,
                    attempt=attempt + 1,
                    delay=backoff,
                )
                await asyncio.sleep(backoff)
        assert last_exc is not None
        raise last_exc

    async def _recover(self) -> None:
        records = await self._wal.load()
        for rec in records:
            if rec.get("event") == "add":
                task = TaskSpec(**rec["task"])
                self._tasks[task.id] = task
            elif rec.get("event") == "status":
                task = self._tasks.get(rec["task_id"])
                if task:
                    task.status = rec["status"]
                    if task.status in {"succeeded", "failed", "cancelled"}:
                        task.end_time = task.end_time or time.time()
        for task in self._tasks.values():
            if task.status not in {"succeeded", "failed", "cancelled"}:
                task.status = "pending"
                self._queue.put_nowait(_QueuedTask(task.priority, task.id))

    async def _autoscale(self) -> None:
        while not self._shutdown.is_set():
            desired = min(
                self.config.max_concurrency, max(1, self._queue.qsize())
            )
            current = len(self._workers)
            if desired > current:
                for _ in range(desired - current):
                    self._workers.append(asyncio.create_task(self._worker()))
            elif desired < current:
                for _ in range(current - desired):
                    worker = self._workers.pop()
                    worker.cancel()
            await asyncio.sleep(self.config.autoscale_interval)

    def _circuit_allow(self, service: str) -> bool:
        state = self._circuit.setdefault(service, _CircuitState())
        return state.allow(
            self.config.circuit_breaker_threshold, self.config.circuit_breaker_timeout
        )

    def _log(self, level: str, event: str, **data: Any) -> None:
        message = json.dumps({"event": event, **data})
        getattr(self.logger, level)(message)


# ---------------------------------------------------------------------------
# Example services for demonstration and tests
# ---------------------------------------------------------------------------


class ApiService:
    name = "api"

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(payload.get("delay", 0.05))
        if payload.get("fail"):
            raise RuntimeError("api failure")
        return {"echo": payload.get("value")}


class FileService:
    name = "file"

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        path = Path(payload["path"])
        data = payload.get("data", "")
        await asyncio.to_thread(path.write_text, data)
        return {"written": len(data)}


class WorkerService:
    name = "worker"

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(payload.get("delay", 0.05))
        x = payload.get("x", 0)
        y = payload.get("y", 0)
        return {"result": x + y}


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------


async def example() -> None:  # pragma: no cover - illustrative only
    config = OrchestratorConfig(max_concurrency=3)
    services = [ApiService(), FileService(), WorkerService()]
    async with Orchestrator(config, services) as orch:
        await orch.add_task("api", {"value": 1})
        await orch.add_task("worker", {"x": 2, "y": 3}, priority=1)
        tmp = Path("example.txt")
        await orch.add_task("file", {"path": str(tmp), "data": "hello"})
        await orch.join()
        print("Results:")
        for task in orch._tasks.values():
            print(task.id, task.result)


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(example())
