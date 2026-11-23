# PREREG — ai-researcher-employee

本文件声明当前骨架可检验的机制假设和边界。版本字符串以 `pyproject.toml` 为准，并出现在 README 的检查块里。计数只写在那个检查块里，由 `make check` 重算；这里不再抄一份。

与 SakanaAI/AI-Scientist-v2 的关系只限于 `docs/ARCHITECTURE.md` 里的设计备忘。那份备忘不是实测，本仓也没有复制对方的代码、提示词或模板。

## 1. 研究问题

一个课程式 manager/worker 管线，怎样让阶段晋升只发生在可复算的判据上？本仓把这个问题收成离线机制：后一阶段能否晋升，由三道纯函数决定，每次决定追加进一条哈希链账本，外部可以重放。

## 2. 假设（都可被现有代码打假）

- **H1（闸是晋升通道）**：除了课程表的第一阶段，`manager.should_promote` 只根据 `gate_seeds`、`gate_direction`、`gate_budget` 决定。任一闸返回假就不再晋升，并记入 Journal。第一阶段的例外写在 `employee/pipeline.py`，也写在 `FAILURE_MODES.md`。
- **H2（账本可重放，但不是字节封存）**：`employee/journal.py` 的 `verify` 重放哈希链。改 `prev`、改 `hash`、改 payload 而不重算哈希，会被判失败。删掉尾部或只重排 JSON 键则不会。这是限度，不是额外的成功声明。
- **H3（闸可复算）**：三道闸没有 I/O，也没有随机源。同一组 `TrialResult` 和同一组参数，输出确定。

## 3. 评测

- 冻结标签：`eval/fixtures/gate_journal_matrix.json`。检查器只读它，并调用闸函数和 `journal.verify`。
- 离线测试：`tests/test_gates.py`、`tests/test_journal.py`、`tests/test_pipeline.py`。
- 验收题：`eval/cases.jsonl`，由 `eval/run_cases.py` 现算。`eval/run-report.json` 的 `detail` 必须和这次现算一致。
- 闸参数的当前文本在 `configs/employee.yaml`。验收题 `CFG-01` 直接读这个文件，不经过 PyYAML。

## 4. 成功标准

`make check` 退出码为零。它在 README 检查块和上面任何一次重算不一致时失败，也在验收题被故意改坏一条期望值后仍然全绿时失败。

## 5. 边界

- 不证明研究结论。回放 metric 带 `llm: fake`，禁止写进能力声明。
- 不证明模型已接入。命令行路径强制走回放。
- 不证明能写论文。仓库里没有 writeup 模块，也没有 review 模块。
- 不证明噪声底已经校准，也不证明方向闸是统计检验。

## 6. 复现

```bash
make check
```

不需要 API key，也不需要网络。
