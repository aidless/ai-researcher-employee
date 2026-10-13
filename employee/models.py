"""Core data types. Pure, no I/O."""
from __future__ import annotations

from dataclasses import dataclass, field


STAGES = ["s1_implement", "s2_baseline_tune", "s3_explore", "s4_ablate"]


@dataclass
class Idea:
    name: str
    title: str
    hypothesis: str
    experiments: list = field(default_factory=list)
    risks: str = "unknown"

    @classmethod
    def from_dict(cls, d: dict) -> "Idea":
        exps = d.get("Experiments", d.get("experiments", []))
        if isinstance(exps, str):
            exps = [exps]
        return cls(
            name=d.get("Name", d.get("name", "untitled")),
            title=d.get("Title", d.get("title", "")),
            hypothesis=d.get("Short Hypothesis", d.get("hypothesis", "")),
            experiments=list(exps),
            risks=d.get("Risk Factors and Limitations", d.get("risks", "unknown")),
        )


@dataclass
class TrialResult:
    stage: str
    seed: int
    metric: float | None  # None = failed/unknown, never 0-imputed
    note: str = ""
    llm: str = "fake"
