"""Offline pipeline: idea -> 4 stages -> journal. Fake by default."""
from __future__ import annotations

import json

from . import journal as J
from . import manager, worker
from .models import Idea


def load_cfg(path: str) -> dict:
    import yaml
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_episode(idea: Idea, cfg: dict, log_path: str, fake: bool = True) -> dict:
    J.append(log_path, "idea", {"name": idea.name, "title": idea.title, "fake": fake})
    prev_stage_trials = []
    summary = {"idea": idea.name, "stages": {}, "fake": fake}
    for stage in manager.curriculum():
        trials = [
            worker.run_trial(stage, seed, "", timeout_s=cfg["worker"]["timeout_s"], fake=fake)
            for seed in range(cfg["worker"]["seeds_per_stage"])
        ]
        if stage == "s1_implement":
            promoted, reasons = True, ["s1 baseline, no gate"]
        else:
            promoted, reasons = manager.should_promote(trials, prev_stage_trials, cfg)
        J.append(log_path, "stage", {
            "stage": stage,
            "metrics": [t.metric for t in trials],
            "promoted": promoted, "reasons": reasons,
            "llm": trials[0].llm if trials else "fake",
        })
        summary["stages"][stage] = {"promoted": promoted, "reasons": reasons}
        if promoted:
            prev_stage_trials = trials
    return summary
