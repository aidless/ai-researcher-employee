# ai-researcher-employee

研究管线的阶段晋升如果只靠人或模型的一句话，事后就无法复算。
本仓库把课程表固定下来；第一阶段直接记为晋升，其后的晋升只经过种子数、方向相对噪声底、预算三道纯函数，每次决定追加进一条哈希链账本。
它回答机制能否被离线重放，不回答任何研究课题是否成立。

**结果与限度。** 标签事先写在 `eval/fixtures/gate_journal_matrix.json`，`make check` 再调用 `employee.gates` 和 `employee.journal.verify` 重算。闸夹具里返回真（`gate_pass`）与返回假（`gate_hold`）的条数、干净链通过条数（`clean_chains_verified`）、注入改动被抓住（`tamper_caught`）与被放过（`tamper_missed`）的条数，都在下面的检查块里。README 里每一个独立出现的数字都必须等于这次重算，否则检查失败。限度：方向闸比较的是中位数之差和噪声底，相等算 HOLD，这不是显著性检验；删掉账本尾部，或只重排一行 JSON 的键，校验仍然通过；`--fake` 的指标是回放公式，不进入本结果；命令行无法关掉回放；没有真实模型实验；`writeup.py` 与 `review.py` 不在本仓库里。失败模式见 `FAILURE_MODES.md`。

<!-- CHECK:BEGIN -->
package_version: 0.1.0
requires_python_at_least: 3.10
license: MIT
runtime_requirements: pytest,pyyaml
stages: 4
gate_functions: 3
gate_fixtures: 13
gate_pass: 5
gate_hold: 8
clean_chains_verified: 4
tamper_cases: 7
tamper_caught: 5
tamper_missed: 2
offline_tests_passed: 8
acceptance_cases_passed: 20
acceptance_cases_total: 20
acceptance_cases_failed: 0
<!-- CHECK:END -->

[![CI](https://github.com/aidless/ai-researcher-employee/actions/workflows/ci.yml/badge.svg)](https://github.com/aidless/ai-researcher-employee/actions/workflows/ci.yml)

## 怎么复算

```bash
make check
```

使用系统自带、且满足检查块里 `requires_python_at_least` 的 Python。不需要 API key，不访问网络，不安装第三方包。`make check` 会重跑 `tests/` 里的离线测试、`eval/cases.jsonl` 里的验收题，并对照 `eval/run-report.json` 里已经提交的 `detail`。验收题的自检会故意改坏一条期望值，改坏后必须变红。

`requirements.txt` 里的 pytest 和 PyYAML 不参与上面的计数。PyYAML 只被 `employee/pipeline.py` 的 `load_cfg` 使用。已经装了 pytest 时，可以用 `make test` 再跑一遍同一批测试函数。

## 机制（可在仓内对上号）

课程表是 `employee/models.py` 的 `STAGES`：`s1_implement`、`s2_baseline_tune`、`s3_explore`、`s4_ablate`。`employee/manager.py` 的 `curriculum()` 原样返回这份列表。三道闸是 `employee/gates.py` 的 `gate_seeds`、`gate_direction`、`gate_budget`。`employee/journal.py` 把记录追加进 jsonl，并用前一条哈希串起下一条。

`gate_hold` 表示闸函数返回假。种子闸失败时的文案不含 HOLD 这个词；方向闸和预算闸的失败文案含有它。夹具把这两种情况都标成 HOLD。

## 不在本结果里的东西

- `--fake` 以及命令行的默认路径是管道回放。`run_employee.py` 传入的是 `fake=a.fake or True`。回放行上的 `llm` 字段为 `fake`。那些 metric 不是能力，也不是论文材料。
- 没有接入真实 LLM、文献检索或评审模型。
- 下列名字不是本仓库的依赖，也没有被合并进来：arx、just-agent、paper-writing-agent、rag-qa、agent-databench。本仓库不引用它们的内部数字。
- `docs/ARCHITECTURE.md` 是设计备忘，不是对 SakanaAI 那个 AI Scientist 仓库的实测，也不是本仓结果。本仓代码、提示词和模板都是自写的，许可是检查块里的 `license`（全文在 `LICENSE`）。

## 目录

| 路径 | 作用 |
|---|---|
| `employee/gates.py` | 三道晋升闸，纯函数 |
| `employee/journal.py` | append-only jsonl 与哈希链，`verify` 可离线重放 |
| `employee/manager.py` | 固定课程表与 `should_promote` |
| `employee/pipeline.py` | `run_episode`：想法走完课程表并写入 Journal |
| `employee/worker.py` | 单次 trial；回放模式只证明接线 |
| `eval/fixtures/gate_journal_matrix.json` | 冻结标签（先于检查器写定） |
| `eval/check_claims.py` | `make check` 的重算入口 |
| `eval/cases.jsonl` | 验收题，期望值由现算对上 |
| `tests/` | 离线测试：`test_gates.py`、`test_journal.py`、`test_pipeline.py` |
| `configs/employee.yaml` | 闸参数与 worker 参数 |
| `FAILURE_MODES.md` | 当前代码已经表现出的失败方式 |

## GitHub About

About 存在仓库设置里，不在 git 中。与本 README 对齐、供维护者贴上的句子是：

> 离线可复算的研究管线骨架：固定课程、纯函数晋升闸与 append-only 实验账本（Journal）。计数由 make check 重算；没有真实模型实验。

## 许可

MIT。版权声明见 `LICENSE`。
