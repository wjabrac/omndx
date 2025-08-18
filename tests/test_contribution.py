from omndx.contribution.credit_tracker import CreditTracker
from omndx.contribution.llm_access_gate import LlmAccessGate
from omndx.contribution.trust_score_calculator import TrustScoreCalculator
from omndx.contribution.usage_throttler import UsageThrottler
import time


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


def test_trust_score_calculator() -> None:
    calc = TrustScoreCalculator()
    for _ in range(15):
        calc.record("alice")
    assert calc.score("alice") == 1.0
    assert calc.score("bob") == 0.0


def test_usage_throttler(monkeypatch) -> None:
    throttle = UsageThrottler(interval=1.0, max_calls=2)
    times = [0.0]

    def fake_time() -> float:
        return times[0]

    monkeypatch.setattr(time, "time", fake_time)
    assert throttle.allow("user") is True
    assert throttle.allow("user") is True
    assert throttle.allow("user") is False
    times[0] = 2.0
    assert throttle.allow("user") is True
