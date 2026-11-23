#!/usr/bin/env python3
"""Recompute the README check block from the code and the frozen fixture.

The fixture owns the labels. This script calls the gate functions and
``journal.verify``, runs the offline tests and the acceptance cases, then
fails if README.md disagrees. It does not rewrite the fixture or the README.
"""
from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "eval" / "fixtures" / "gate_journal_matrix.json"
README = ROOT / "README.md"
REPORT = ROOT / "eval" / "run-report.json"
BEGIN = "<!-- CHECK:BEGIN -->"
END = "<!-- CHECK:END -->"
PROTOCOL = (
    "Labels in this file are the spec. eval/check_claims.py must recompute "
    "verdicts and must not rewrite this file."
)
NUM = re.compile(r"(?<![A-Za-z0-9_])\d+(?:\.\d+)?")
VER = re.compile(r"(?<![A-Za-z0-9_])v\d+(?:\.\d+)*", re.IGNORECASE)
FORBIDDEN_MODULES = {"yaml", "pytest", "_pytest"}


def die(errors: list[str]) -> None:
    for err in errors:
        print(f"[FAIL] {err}", file=sys.stderr)
    raise SystemExit(1)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def standalone_numbers(text: str) -> list[str]:
    found = [m.group(0) for m in NUM.finditer(text)]
    found.extend(m.group(0) for m in VER.finditer(text))
    return found


def split_check_block(text: str) -> tuple[str, dict[str, str]]:
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        raise ValueError("README must contain exactly one CHECK block")
    begin = text.index(BEGIN)
    end = text.index(END)
    if end < begin:
        raise ValueError("CHECK block ends before it starts")
    outside = text[:begin] + text[end + len(END):]
    block = text[begin + len(BEGIN):end]
    claims: dict[str, str] = {}
    for lineno, raw in enumerate(block.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"CHECK block line {lineno} is not key: value")
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if not key or not value:
            raise ValueError(f"CHECK block line {lineno} has an empty key or value")
        if key in claims:
            raise ValueError(f"duplicate CHECK key {key}")
        claims[key] = value
    return outside, claims


def diff_claims(recomputed: dict[str, str], claimed: dict[str, str]) -> list[str]:
    errors = []
    missing = sorted(set(recomputed) - set(claimed))
    extra = sorted(set(claimed) - set(recomputed))
    if missing:
        errors.append("README check block missing " + ", ".join(missing))
    if extra:
        errors.append("README check block has extra " + ", ".join(extra))
    for key in sorted(set(recomputed) & set(claimed)):
        if recomputed[key] != claimed[key]:
            errors.append(
                f"{key}: recomputed {recomputed[key]!r} != README {claimed[key]!r}"
            )
    return errors


def trials(metrics: list) -> list:
    from employee.models import TrialResult

    return [
        TrialResult(stage="s", seed=i, metric=None if value is None else float(value))
        for i, value in enumerate(metrics)
    ]


def run_gate(spec: dict) -> tuple[bool, str]:
    from employee import gates

    name = spec["gate"]
    if name == "seeds":
        return gates.gate_seeds(trials(spec["metrics"]), int(spec["min_seeds"]))
    if name == "direction":
        return gates.gate_direction(
            trials(spec["cand"]), trials(spec["base"]), float(spec["noise_floor"])
        )
    if name == "budget":
        return gates.gate_budget(int(spec["tokens_used"]), int(spec["budget_tokens"]))
    raise ValueError(f"unknown gate {name}")


def score_gates(rows: list[dict]) -> tuple[dict[str, int], list[str]]:
    errors = []
    passed = held = 0
    seen = {"seeds": set(), "direction": set(), "budget": set()}
    ids = []
    for spec in rows:
        ids.append(spec["id"])
        try:
            ok, message = run_gate(spec)
        except Exception as exc:  # noqa: BLE001 — surface the fixture id
            errors.append(f"gate {spec.get('id')}: raised {type(exc).__name__}: {exc}")
            continue
        actual = "PASS" if ok else "HOLD"
        seen.setdefault(spec["gate"], set()).add(actual)
        if actual == "PASS":
            passed += 1
        else:
            held += 1
        if actual != spec["expect"] or message != spec["message"]:
            errors.append(
                f"gate {spec['id']}: got {actual}|{message!r} "
                f"expected {spec['expect']}|{spec['message']!r}"
            )
    if len(ids) != len(set(ids)):
        errors.append("duplicate gate fixture id")
    for gate, outcomes in seen.items():
        if outcomes != {"PASS", "HOLD"}:
            errors.append(f"gate {gate} does not have both PASS and HOLD ({outcomes})")
    return {"gate_fixtures": len(rows), "gate_pass": passed, "gate_hold": held}, errors


def write_chain(path: Path, entries: list[dict]) -> None:
    from employee import journal as journal

    if path.exists():
        path.unlink()
    if not entries:
        path.write_text("", encoding="utf-8")
        return
    for entry in entries:
        journal.append(path.as_posix(), entry["kind"], entry["payload"])


def score_chains(rows: list[dict]) -> tuple[int, list[str]]:
    from employee import journal as journal

    errors = []
    verified = 0
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for spec in rows:
            path = root / f"{spec['id']}.jsonl"
            try:
                write_chain(path, spec["entries"])
                ok, count = journal.verify(path.as_posix())
            except Exception as exc:  # noqa: BLE001
                errors.append(f"chain {spec.get('id')}: raised {type(exc).__name__}: {exc}")
                continue
            if ok and count == len(spec["entries"]):
                verified += 1
            else:
                errors.append(
                    f"chain {spec['id']}: verify returned {(ok, count)} "
                    f"for {len(spec['entries'])} entries"
                )
    return verified, errors


def apply_tamper(path: Path, spec: dict) -> None:
    op = spec["op"]
    if op == "append-raw":
        with path.open("a", encoding="utf-8") as handle:
            handle.write(spec["raw"])
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    if op == "drop-last":
        lines = lines[:-1]
    elif op == "swap":
        i, j = int(spec["i"]), int(spec["j"])
        lines[i], lines[j] = lines[j], lines[i]
    elif op == "set-prev":
        obj = json.loads(lines[int(spec["index"])])
        obj["prev"] = spec["value"]
        lines[int(spec["index"])] = json.dumps(obj, ensure_ascii=False)
    elif op == "set-hash":
        obj = json.loads(lines[int(spec["index"])])
        obj["hash"] = spec["value"]
        lines[int(spec["index"])] = json.dumps(obj, ensure_ascii=False)
    elif op == "mutate-payload":
        obj = json.loads(lines[int(spec["index"])])
        obj["payload"][spec["key"]] = spec["value"]
        lines[int(spec["index"])] = json.dumps(obj, ensure_ascii=False)
    elif op == "reorder-keys":
        obj = json.loads(lines[int(spec["index"])])
        reordered = {
            "hash": obj["hash"],
            "prev": obj["prev"],
            "payload": obj["payload"],
            "kind": obj["kind"],
        }
        lines[int(spec["index"])] = json.dumps(reordered, ensure_ascii=False)
    else:
        raise ValueError(f"unknown tamper op {op}")
    text = "\n".join(lines)
    path.write_text((text + "\n") if text else "", encoding="utf-8")


def score_tampers(base: list[dict], rows: list[dict]) -> tuple[dict[str, int], list[str]]:
    from employee import journal as journal

    errors = []
    caught = missed = 0
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for spec in rows:
            path = root / f"{spec['id']}.jsonl"
            try:
                write_chain(path, base)
                before = path.read_bytes()
                apply_tamper(path, spec)
                after = path.read_bytes()
                if before == after:
                    errors.append(f"tamper {spec['id']}: mutation did not change the file")
                    continue
                ok, count = journal.verify(path.as_posix())
            except Exception as exc:  # noqa: BLE001
                errors.append(f"tamper {spec.get('id')}: raised {type(exc).__name__}: {exc}")
                continue
            actual = "missed" if ok else "caught"
            if actual == "caught":
                caught += 1
            else:
                missed += 1
            if actual != spec["expect"]:
                errors.append(
                    f"tamper {spec['id']}: verify {(ok, count)} classified {actual}, "
                    f"label says {spec['expect']}"
                )
    return {
        "tamper_cases": len(rows),
        "tamper_caught": caught,
        "tamper_missed": missed,
    }, errors


def run_offline_tests() -> tuple[int, list[str]]:
    errors = []
    passed = 0
    defined = 0
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        module = load_module(f"offline_{path.stem}", path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        defined += sum(
            1
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        )
        for name in sorted(dir(module)):
            if not name.startswith("test_"):
                continue
            fn = getattr(module, name)
            if not callable(fn):
                continue
            try:
                if "tmp_path" in inspect.signature(fn).parameters:
                    with tempfile.TemporaryDirectory() as tmp:
                        fn(tmp_path=Path(tmp))
                else:
                    fn()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"test {path.name}::{name}: {type(exc).__name__}: {exc}")
                continue
            passed += 1
    if defined != passed:
        errors.append(f"offline tests defined {defined} but passed {passed}")
    return passed, errors


def run_acceptance() -> tuple[dict[str, int], list[str]]:
    cases = load_module("acceptance_cases", ROOT / "eval" / "run_cases.py")
    errors = []
    rows = cases.load_cases(cases.CASES)
    results = []
    for row in rows:
        ok, detail = cases.run_case(row)
        results.append({"id": row["id"], "ok": ok, "detail": detail})
        if not ok:
            errors.append(f"acceptance {row['id']}: {detail}")
    passed = sum(1 for row in results if row["ok"])
    failed = len(results) - passed
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    by_id = {row["id"]: row for row in report["results"]}
    fresh = {row["id"]: row for row in results}
    if set(by_id) != set(fresh):
        errors.append("eval/run-report.json ids do not match eval/cases.jsonl")
    else:
        for case_id, row in fresh.items():
            if by_id[case_id]["detail"] != row["detail"] or by_id[case_id]["ok"] is not True:
                errors.append(
                    f"run-report {case_id}: stored {by_id[case_id]!r} != fresh {row!r}"
                )
    if report.get("total") != len(results) or report.get("passed") != passed:
        errors.append(
            f"run-report totals {report.get('passed')}/{report.get('total')} "
            f"!= fresh {passed}/{len(results)}"
        )
    if report.get("failed") != failed or report.get("selftest") is not False:
        errors.append("run-report failed/selftest fields do not match a clean run")
    mutated = [dict(row) for row in rows]
    mutated[0] = dict(mutated[0], expected="__selftest_impossible_value__")
    mutated_passed = sum(1 for row in mutated if cases.run_case(row)[0])
    if mutated_passed >= len(mutated):
        errors.append("acceptance selftest stayed green after an expected value was broken")
    return {
        "acceptance_cases_passed": passed,
        "acceptance_cases_total": len(results),
        "acceptance_cases_failed": failed,
    }, errors


def project_meta() -> tuple[dict[str, str], list[str]]:
    errors = []
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', text)
    requires = re.search(r'(?m)^requires-python\s*=\s*">=([^"]+)"\s*$', text)
    if version is None or requires is None:
        errors.append("pyproject.toml is missing version or requires-python")
        return {}, errors
    parts = requires.group(1).split(".")
    try:
        needed = tuple(int(part) for part in parts)
    except ValueError:
        errors.append(f"cannot parse requires-python {requires.group(1)}")
        needed = ()
    if needed and sys.version_info[: len(needed)] < needed:
        errors.append(
            f"interpreter {sys.version.split()[0]} is older than {requires.group(1)}"
        )
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    license_name = "MIT" if license_text.startswith("MIT License\n") else ""
    if not license_name:
        errors.append("LICENSE does not start with 'MIT License'")
    names = []
    for raw in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        names.append(re.split(r"[<>=!\[]", line, maxsplit=1)[0].strip().lower())
    return {
        "package_version": version.group(1),
        "requires_python_at_least": requires.group(1),
        "license": license_name,
        "runtime_requirements": ",".join(sorted(names)),
    }, errors


def structural_counts() -> tuple[dict[str, int], list[str]]:
    from employee.manager import curriculum
    from employee.models import STAGES

    errors = []
    if list(curriculum()) != list(STAGES):
        errors.append("manager.curriculum() is not models.STAGES")
    tree = ast.parse((ROOT / "employee" / "gates.py").read_text(encoding="utf-8"))
    gate_functions = sum(
        1
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("gate_")
    )
    return {"stages": len(curriculum()), "gate_functions": gate_functions}, errors


def recompute(fixture: dict) -> tuple[dict[str, str], list[str]]:
    errors = []
    if fixture.get("protocol") != PROTOCOL:
        errors.append("fixture protocol sentence was rewritten")
    claims: dict[str, str] = {}
    meta, meta_errors = project_meta()
    errors.extend(meta_errors)
    claims.update(meta)
    counts, count_errors = structural_counts()
    errors.extend(count_errors)
    gate_counts, gate_errors = score_gates(fixture["gates"])
    errors.extend(gate_errors)
    counts.update(gate_counts)
    verified, chain_errors = score_chains(fixture["clean_chains"])
    errors.extend(chain_errors)
    counts["clean_chains_verified"] = verified
    tamper_counts, tamper_errors = score_tampers(fixture["tamper_base"], fixture["tampers"])
    errors.extend(tamper_errors)
    counts.update(tamper_counts)
    tests_passed, test_errors = run_offline_tests()
    errors.extend(test_errors)
    counts["offline_tests_passed"] = tests_passed
    acceptance, acceptance_errors = run_acceptance()
    errors.extend(acceptance_errors)
    counts.update(acceptance)
    if counts["gate_pass"] + counts["gate_hold"] != counts["gate_fixtures"]:
        errors.append("gate pass/hold do not add up to the fixture count")
    if counts["tamper_caught"] + counts["tamper_missed"] != counts["tamper_cases"]:
        errors.append("tamper caught/missed do not add up to the tamper count")
    if counts["acceptance_cases_passed"] + counts["acceptance_cases_failed"] != counts["acceptance_cases_total"]:
        errors.append("acceptance pass/fail do not add up to the case count")
    for key, value in counts.items():
        claims[key] = str(value)
    return claims, errors


def selftest_detector() -> list[str]:
    errors = []
    sample = "count is 9.\n" + BEGIN + "\nx: 1\n" + END + "\npython3 s1_implement sha256\n"
    outside, _claims = split_check_block(sample)
    found = standalone_numbers(outside)
    if found != ["9"]:
        errors.append(f"digit scanner selftest got {found}, want ['9']")
    if standalone_numbers("python3 s1_implement sha256 v0") != ["v0"]:
        errors.append("digit scanner missed a v-prefixed version or flagged an identifier")
    tampered = {"gate_pass": "1", "gate_hold": "1"}
    if not diff_claims({"gate_pass": "0", "gate_hold": "1"}, tampered):
        errors.append("claim diff selftest stayed green")
    bad_gate, gate_errors = score_gates(
        [{
            "id": "selftest-bad-label",
            "gate": "budget",
            "tokens_used": 1,
            "budget_tokens": 1,
            "expect": "HOLD",
            "message": "nope",
        }]
    )
    if not any("selftest-bad-label" in err for err in gate_errors) or bad_gate["gate_pass"] != 1:
        errors.append("gate label selftest did not notice a wrong HOLD label")
    return errors


def third_party_imports() -> list[str]:
    loaded = sorted(name for name in sys.modules if name.split(".")[0] in FORBIDDEN_MODULES)
    if loaded:
        return ["third-party modules imported during check: " + ", ".join(loaded)]
    return []


def main() -> int:
    sys.path.insert(0, str(ROOT))
    import os

    os.chdir(ROOT)
    errors = selftest_detector()
    try:
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        readme = README.read_text(encoding="utf-8")
        outside, claimed = split_check_block(readme)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        die(errors + [str(exc)])
    stray = standalone_numbers(outside)
    if stray:
        errors.append("README numbers outside the CHECK block: " + ", ".join(stray))
    recomputed, recompute_errors = recompute(fixture)
    errors.extend(recompute_errors)
    if recomputed:
        errors.extend(diff_claims(recomputed, claimed))
    errors.extend(third_party_imports())
    if errors:
        die(errors)
    print("check ok")
    for key in sorted(recomputed):
        print(f"{key}: {recomputed[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
