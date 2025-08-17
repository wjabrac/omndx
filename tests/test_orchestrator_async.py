import asyncio
import json
from pathlib import Path
import sys
import pathlib

import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from omndx.orchestrator import (
    ApiService,
    FileService,
    Orchestrator,
    OrchestratorConfig,
    WorkerService,
)


@pytest.mark.asyncio
async def test_orchestrates_heterogeneous_services(tmp_path: Path) -> None:
    config = OrchestratorConfig(max_concurrency=3, wal_path=tmp_path / "wal.log", trace_file=tmp_path / "trace.jsonl")
    services = [ApiService(), FileService(), WorkerService()]
    async with Orchestrator(config, services) as orch:
        t_api = await orch.add_task("api", {"value": 42})
        await orch.add_task("file", {"path": str(tmp_path / "out.txt"), "data": "hello"})
        t_work = await orch.add_task("worker", {"x": 1, "y": 2})
        await orch.join()

    tasks = orch._tasks
    assert tasks[t_api].result == {"echo": 42}
    assert tasks[t_work].result == {"result": 3}
    assert (tmp_path / "out.txt").read_text() == "hello"


class FlakyService:
    name = "flaky"

    def __init__(self) -> None:
        self.calls = 0

    async def run(self, payload: dict) -> dict:
        self.calls += 1
        if self.calls < 2:
            raise RuntimeError("boom")
        return {"ok": True}


@pytest.mark.asyncio
async def test_retries_and_backoff(tmp_path: Path) -> None:
    flaky = FlakyService()
    config = OrchestratorConfig(retry_attempts=3, backoff_factor=0, wal_path=tmp_path / "wal.log")
    async with Orchestrator(config, [flaky]) as orch:
        tid = await orch.add_task("flaky", {})
        await orch.join()
    assert flaky.calls == 2
    assert orch._tasks[tid].status == "succeeded"


class SlowService:
    name = "slow"

    async def run(self, payload: dict) -> dict:
        await asyncio.sleep(0.5)
        return {"done": True}


@pytest.mark.asyncio
async def test_cancellation(tmp_path: Path) -> None:
    slow = SlowService()
    config = OrchestratorConfig(max_concurrency=1, wal_path=tmp_path / "wal.log")
    async with Orchestrator(config, [slow]) as orch:
        tid = await orch.add_task("slow", {})
        await asyncio.sleep(0.1)
        await orch.cancel_task(tid)
        await orch.join()
    assert orch._tasks[tid].status == "cancelled"


@pytest.mark.asyncio
async def test_prioritization(tmp_path: Path) -> None:
    svc = WorkerService()
    config = OrchestratorConfig(max_concurrency=1, wal_path=tmp_path / "wal.log")
    orch = Orchestrator(config, [svc])
    low = await orch.add_task("worker", {"x": 1, "y": 1}, priority=10)
    high = await orch.add_task("worker", {"x": 2, "y": 2}, priority=1)
    await orch.start()
    await orch.join()
    await orch.stop()
    assert orch._tasks[high].start_time < orch._tasks[low].start_time


class LimitedService:
    name = "limited"

    async def run(self, payload: dict) -> dict:
        await asyncio.sleep(0.01)
        return {"done": True}


@pytest.mark.asyncio
async def test_rate_limit_and_concurrency(tmp_path: Path) -> None:
    limited = LimitedService()
    config = OrchestratorConfig(
        service_rate_limits={"limited": (1, 5)},
        service_concurrency={"limited": 1},
        max_concurrency=3,
        wal_path=tmp_path / "wal.log",
    )
    async with Orchestrator(config, [limited]) as orch:
        await orch.add_task("limited", {})
        with pytest.raises(RuntimeError):
            await orch.add_task("limited", {})
        await asyncio.sleep(0.3)
        t1 = await orch.add_task("limited", {})
        await asyncio.sleep(0.3)
        t2 = await orch.add_task("limited", {})
        await orch.join()
    assert orch._tasks[t2].start_time >= orch._tasks[t1].end_time


class StuckService:
    name = "stuck"

    async def run(self, payload: dict) -> dict:
        await asyncio.sleep(1)
        return {"never": True}


@pytest.mark.asyncio
async def test_task_timeout(tmp_path: Path) -> None:
    stuck = StuckService()
    config = OrchestratorConfig(task_timeout=0.1, wal_path=tmp_path / "wal.log")
    async with Orchestrator(config, [stuck]) as orch:
        tid = await orch.add_task("stuck", {})
        await orch.join()
    assert orch._tasks[tid].status == "failed"


class HangingService:
    name = "hang"

    async def run(self, payload: dict) -> dict:
        await asyncio.sleep(0.5)
        return {"ok": True}


@pytest.mark.asyncio
async def test_wal_recovery(tmp_path: Path) -> None:
    svc = HangingService()
    cfg = OrchestratorConfig(max_concurrency=1, wal_path=tmp_path / "wal.log")
    orch1 = Orchestrator(cfg, [svc])
    await orch1.start()
    tid = await orch1.add_task("hang", {})
    await asyncio.sleep(0.1)
    await orch1.stop()
    orch2 = Orchestrator(cfg, [svc])
    await orch2.start()
    await orch2.join()
    assert orch2._tasks[tid].status == "succeeded"
    await orch2.stop()


@pytest.mark.asyncio
async def test_leader_election(tmp_path: Path) -> None:
    cfg = OrchestratorConfig(wal_path=tmp_path / "wal.log", leader_lock_path=tmp_path / "lock")
    svc = WorkerService()
    orch1 = Orchestrator(cfg, [svc])
    orch2 = Orchestrator(cfg, [svc])
    await orch1.start()
    with pytest.raises(RuntimeError):
        await orch2.start()
    await orch1.stop()


@pytest.mark.asyncio
async def test_admin_override(tmp_path: Path) -> None:
    cfg = OrchestratorConfig(max_concurrency=1, wal_path=tmp_path / "wal.log", admin_port=0)
    svc = WorkerService()
    async with Orchestrator(cfg, [svc]) as orch:
        port = orch.config.admin_port
        body = json.dumps({"max_concurrency": 2}).encode()
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        req = (
            b"POST /config HTTP/1.1\r\n" +
            b"Host: localhost\r\n" +
            f"Content-Length: {len(body)}\r\n\r\n".encode() + body
        )
        writer.write(req)
        await writer.drain()
        await reader.read(1024)
        writer.close()
        await writer.wait_closed()
        assert orch.config.max_concurrency == 2


@pytest.mark.asyncio
async def test_tracing_output(tmp_path: Path) -> None:
    trace_file = tmp_path / "traces.jsonl"
    cfg = OrchestratorConfig(
        max_concurrency=1,
        wal_path=tmp_path / "wal.log",
        trace_file=trace_file,
    )
    svc = WorkerService()
    async with Orchestrator(cfg, [svc]) as orch:
        tid = await orch.add_task("worker", {"x": 1, "y": 1})
        await orch.join()
    lines = trace_file.read_text().splitlines()
    assert any(tid in line for line in lines)
