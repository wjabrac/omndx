import asyncio
import pytest

from omndx.core.agent_router import AgentRouter
from omndx.runtime.metrics_collector import metrics


class DummyTask:
    pass


def test_router_success_records_metrics():
    metrics._values.clear()
    router = AgentRouter()
    router.register("DummyTask", lambda t: "ok")
    result = asyncio.run(router.route(DummyTask()))
    assert result == "ok"
    snap = metrics.snapshot()
    assert any(k.startswith("efficiency|") for k in snap)


def test_router_missing_handler():
    metrics._values.clear()
    router = AgentRouter()
    with pytest.raises(ValueError):
        asyncio.run(router.route(DummyTask()))
    snap = metrics.snapshot()
    assert any("failed" in k for k in snap)
