"""Worker: sandboxed trial execution. Fake mode replays presets (pipeline check only)."""
from __future__ import annotations

import subprocess
import tempfile
import os

from .models import TrialResult

MAX_OUTPUT = 4000


def run_trial(stage: str, seed: int, code: str, timeout_s: int = 15, fake: bool = True) -> TrialResult:
    if fake:
        # 回放：只证明接线，结果必须标 llm=fake；
        # 按阶段递增伪造改进，保证默认噪声底下全晋升（能力声明无效，仅管道自检）
        from .models import STAGES
        boost = STAGES.index(stage) * 0.02 if stage in STAGES else 0.0
        return TrialResult(stage=stage, seed=seed, metric=0.5 + boost + seed * 0.001,
                           note="replay", llm="fake")
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "trial.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        try:
            p = subprocess.run(
                ["python3", path], capture_output=True, text=True,
                timeout=timeout_s, cwd=td,
            )
            out = (p.stdout or "")[-MAX_OUTPUT:]
            metric = _parse_metric(out)
            note = "ok" if p.returncode == 0 and metric is not None else f"rc={p.returncode}"
            return TrialResult(stage=stage, seed=seed, metric=metric, note=note, llm="real")
        except subprocess.TimeoutExpired:
            return TrialResult(stage=stage, seed=seed, metric=None, note="timeout", llm="real")


def _parse_metric(out: str) -> float | None:
    for line in reversed(out.strip().splitlines()):
        if line.startswith("METRIC:"):
            try:
                return float(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None
