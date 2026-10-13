"""Append-only journal (jsonl + sha chain). Offline verifiable."""
from __future__ import annotations

import hashlib
import json
import os


def _entry_hash(prev: str, payload: dict) -> str:
    body = prev + json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(body.encode()).hexdigest()


def append(log_path: str, kind: str, payload: dict) -> dict:
    prev = "GENESIS"
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    prev = json.loads(line)["hash"]
    entry = {"kind": kind, "payload": payload, "prev": prev}
    entry["hash"] = _entry_hash(prev, {"kind": kind, "payload": payload})
    os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def verify(log_path: str) -> tuple[bool, int]:
    """Replay the chain. Returns (ok, n_entries)."""
    prev = "GENESIS"
    n = 0
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("prev") != prev:
                return False, n
            want = _entry_hash(prev, {"kind": entry["kind"], "payload": entry["payload"]})
            if entry.get("hash") != want:
                return False, n
            prev = entry["hash"]
            n += 1
    return True, n
