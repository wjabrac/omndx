import sys
import time
from pathlib import Path

import pytest

# Ensure package root on path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from omndx.core.sandbox_manager import (
    SandboxManager,
    SandboxTimeout,
)


def sample_function() -> int:
    print("hello from sandbox")
    print("an error", file=sys.stderr)
    return 42


def test_execute_streams_output_and_return_value():
    manager = SandboxManager()
    result = manager.execute(sample_function, timeout=5)
    assert result.return_value == 42
    assert "hello from sandbox" in result.stdout
    assert "an error" in result.stderr
    assert result.exit_code == 0


def slow_function():
    time.sleep(2)


def test_execute_timeout():
    manager = SandboxManager()
    with pytest.raises(SandboxTimeout):
        manager.execute(slow_function, timeout=0.5)
