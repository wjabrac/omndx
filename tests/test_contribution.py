from omndx.contribution.credit_tracker import CreditTracker
from omndx.contribution.llm_access_gate import LlmAccessGate


def test_credit_tracker() -> None:
    tracker = CreditTracker()
    tracker.add("alice", 5)
    assert tracker.consume("alice", 3) is True
    assert tracker.balance("alice") == 2


def test_access_gate() -> None:
    tracker = CreditTracker()
    tracker.add("bob", 1)
    gate = LlmAccessGate(tracker)
    assert gate.allow("bob") is True
    assert gate.allow("bob") is False
