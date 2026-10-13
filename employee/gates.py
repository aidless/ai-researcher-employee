"""Stage promotion gates: seeds / direction-vs-noise / budget. Pure functions."""
from __future__ import annotations

from statistics import median

from .models import TrialResult


def gate_seeds(trials: list[TrialResult], min_seeds: int) -> tuple[bool, str]:
    ok_vals = [t for t in trials if t.metric is not None]
    if len(ok_vals) >= min_seeds:
        return True, f"seeds {len(ok_vals)}>={min_seeds}"
    return False, f"seeds {len(ok_vals)}<{min_seeds} (need {min_seeds})"


def gate_direction(
    cand: list[TrialResult], base: list[TrialResult], noise_floor: float
) -> tuple[bool, str]:
    c = sorted(t.metric for t in cand if t.metric is not None)
    b = sorted(t.metric for t in base if t.metric is not None)
    if not c or not b:
        return False, "HOLD: missing metric (unknown, not failure)"
    delta = median(c) - median(b)
    if delta > noise_floor:
        return True, f"delta {delta:.4f} > floor {noise_floor}"
    return False, f"HOLD: delta {delta:.4f} <= floor {noise_floor}"


def gate_budget(tokens_used: int, budget_tokens: int) -> tuple[bool, str]:
    if tokens_used <= budget_tokens:
        return True, f"tokens {tokens_used}<={budget_tokens}"
    return False, f"HOLD: tokens {tokens_used}>{budget_tokens}"
