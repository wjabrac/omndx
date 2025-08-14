"""End-to-end tests for CLI and web UI components."""

from __future__ import annotations

import os
import sys

# Ensure package root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from omndx.core import TagLogger
from omndx.ui.cli_shell import CliShell
from omndx.ui.web_interface import create_app
from omndx.ui.realtime_log_viewer import LogStreamer
from omndx.ui.graph_viz import render_task_graph


def test_cli_basic_workflow() -> None:
    logger = TagLogger("cli-test")
    shell = CliShell(logger)
    shell.onecmd("start")
    shell.onecmd("metrics")
    assert logger.get_metrics()["start"] == 1


def test_web_ui_basic_workflow() -> None:
    logger = TagLogger("web-test")
    app = create_app(logger)
    client = TestClient(app)

    resp = client.post("/start")
    assert resp.json()["started"] is True

    resp = client.get("/metrics")
    assert resp.json()["start"] == 1


def test_realtime_log_viewer_streams_logs() -> None:
    logger = TagLogger("stream-test")
    streamer = LogStreamer(logger)
    gen = streamer.stream()
    logger.info("hello world")
    msg = next(gen)
    assert "hello world" in msg
    streamer.close()


def test_graph_viz_outputs_dot() -> None:
    graph = {"a": ["b", "c"], "b": [], "c": []}
    src = render_task_graph(graph)
    assert "a" in src and "b" in src and "c" in src
    assert "->" in src
