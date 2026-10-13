from employee import journal as J


def test_journal_append_verify(tmp_path):
    log = str(tmp_path / "t.jsonl")
    J.append(log, "idea", {"name": "x"})
    J.append(log, "stage", {"stage": "s1", "promoted": True})
    ok, n = J.verify(log)
    assert ok and n == 2


def test_journal_tamper_detected(tmp_path):
    log = str(tmp_path / "t.jsonl")
    J.append(log, "idea", {"name": "x"})
    with open(log, "a", encoding="utf-8") as f:
        f.write('{"kind":"stage","payload":{},"prev":"WRONG","hash":"00"}\n')
    ok, _ = J.verify(log)
    assert not ok
