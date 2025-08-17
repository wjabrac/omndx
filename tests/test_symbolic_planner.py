import pytest
from omndx.core.symbolic_planner import SymbolicPlanner


def test_plan_string() -> None:
    planner = SymbolicPlanner()
    assert planner.plan("a -> b") == ["a", "b"]


def test_plan_iterable() -> None:
    planner = SymbolicPlanner()
    assert planner.plan(["x", "y"]) == ["x", "y"]


def test_plan_none_returns_empty() -> None:
    planner = SymbolicPlanner()
    assert planner.plan(None) == []


def test_plan_invalid_raises() -> None:
    planner = SymbolicPlanner()
    with pytest.raises(ValueError):
        planner.plan(42)
