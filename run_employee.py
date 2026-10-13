"""CLI: --fake replay, --verify journal replay."""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from employee import journal as J
from employee.models import Idea
from employee.pipeline import load_cfg, run_episode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--idea", default="ideas/demo.json")
    ap.add_argument("--config", default="configs/employee.yaml")
    ap.add_argument("--log", default="logs/demo.jsonl")
    ap.add_argument("--fake", action="store_true")
    ap.add_argument("--verify", default=None)
    a = ap.parse_args()
    if a.verify:
        ok, n = J.verify(a.verify)
        print(json.dumps({"verify_ok": ok, "entries": n}))
        return 0 if ok else 1
    with open(a.idea, encoding="utf-8") as f:
        idea = Idea.from_dict(json.load(f))
    cfg = load_cfg(a.config)
    summary = run_episode(idea, cfg, a.log, fake=a.fake or True)
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
