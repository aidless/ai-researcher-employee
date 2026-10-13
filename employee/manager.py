"""Manager: fixed curriculum + gated promotion. Deterministic (v0.1)."""
from __future__ import annotations

from . import gates
from .models import STAGES, TrialResult


def should_promote(cand: list[TrialResult], base: list[TrialResult], cfg: dict,
                   tokens_used: int = 0) -> tuple[bool, list[str]]:
    reasons = []
    ok, r = gates.gate_seeds(cand, cfg["gates"]["min_seeds"])
    reasons.append(r)
    if not ok:
        return False, reasons
    ok, r = gates.gate_direction(cand, base, cfg["gates"]["noise_floor"])
    reasons.append(r)
    if not ok:
        return False, reasons
    ok, r = gates.gate_budget(tokens_used, cfg["gates"]["budget_tokens"])
    reasons.append(r)
    return ok, reasons


def curriculum() -> list[str]:
    return list(STAGES)
