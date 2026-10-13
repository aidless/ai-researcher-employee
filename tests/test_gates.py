from employee import gates
from employee.models import TrialResult


def T(stage, seed, m):
    return TrialResult(stage=stage, seed=seed, metric=m)


def test_seeds_gate():
    ok, _ = gates.gate_seeds([T("s", 0, 1.0)], 2)
    assert not ok
    ok, _ = gates.gate_seeds([T("s", 0, 1.0), T("s", 1, 1.1)], 2)
    assert ok


def test_direction_gate_noise():
    base = [T("s", 0, 0.5), T("s", 1, 0.5)]
    ok, _ = gates.gate_direction([T("s", 0, 0.501), T("s", 1, 0.501)], base, 0.005)
    assert not ok  # 在噪声底内 -> HOLD
    ok, _ = gates.gate_direction([T("s", 0, 0.6), T("s", 1, 0.6)], base, 0.005)
    assert ok


def test_direction_gate_unknown():
    ok, msg = gates.gate_direction([T("s", 0, None)], [T("s", 0, 0.5)], 0.005)
    assert not ok and "unknown" in msg


def test_budget_gate():
    assert gates.gate_budget(10, 100)[0]
    assert not gates.gate_budget(101, 100)[0]
