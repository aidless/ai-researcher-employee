# ai-researcher-employee —— 自己的 AI 研究员工（骨架 v0.1）

[![CI](https://github.com/aidless/ai-researcher-employee/actions/workflows/ci.yml/badge.svg)](https://github.com/aidless/ai-researcher-employee/actions/workflows/ci.yml)

> 🗂 **仓库族谱**：「自主研究循环」主线仓是 [ai-researcher](https://github.com/aidless/ai-researcher)（证据链签字版）；本仓定位是骨架 v0.1 的 manager/worker 分离参考实现。

> **披露**：本仓为自主实现的研究管线骨架。设计思想部分参考了
> SakanaAI/AI-Scientist-v2 的公开设计（课程式 manager/worker 分离、
> Journal 实验账本、阶段门控晋升——见 `docs/ARCHITECTURE.md` 的思想对照表，
> **未复制其任何代码/提示/模板**，详见许可说明）。
> 任何由本系统生成的论文手稿必须在摘要或方法节显著声明机器生成。

## 管线（4 主阶段，manager 定课程，worker 只执行）

```
idea.json → S1 初实现 → S2 基线调参（禁改结构） → S3 创新探索 → S4 消融
                │            │                       │              │
                └──── Journal（append-only账本，sha链）─────────────┘
                              │ 门控晋升（种子数/方向/预算三闸）
                              ▼
                    writeup（模板渲染） → review（清单制）
```

## 诚实性约束（从 arx 继承）

- `--fake` 是管道回放：直接提交预设 metric，仅验证接线，结果行带
  `llm: fake`，不允许出现在能力声明里。
- 阶段晋升必须过三闸：`min_seeds` / 指标方向与噪声底比较 / token预算。
  任一不过即 `HOLD`，记入 Journal，不静默丢弃。
- Journal 是 append-only jsonl + sha 链，`verify` 命令可离线重放校验。
- 不知道的记 `unknown`，不猜。

## 快速开始

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest tests/ -q
.venv/bin/python run_employee.py --fake --idea ideas/demo.json
.venv/bin/python run_employee.py --verify logs/demo.jsonl
```

Quickstart 实测（2026-11-10，Linux · Python 3.12，真实输出节选）：

```text
$ python3 -m pytest tests/ -q
........                                                                 [100%]
8 passed in 0.11s

$ python3 run_employee.py --fake --idea ideas/demo.json
{ "idea": "demo-gated-pipeline",
  "stages": { "s1_implement": {"promoted": true, "reasons": ["s1 baseline, no gate"]},
              "s2_baseline_tune": {"promoted": true, "reasons": ["seeds 2>=2",
                  "delta 0.0200 > floor 0.005", "tokens 0<=200000"]}, ... } }

$ python3 run_employee.py --verify <journal.jsonl>
{"verify_ok": true, "entries": 5}
```

## Results

### P1 真实 LLM 实跑结果：not yet measured

本仓 **尚未做过任何一次真实 LLM（P1 级）实跑**，因此没有真实结果数字可报。
原因（如实）：

1. 仓库内不存在任何真实运行的日志/结果文件——`logs/` 只在 `--fake` 回放时生成
   （默认 `logs/demo.jsonl`，不入库），仓库中也未提交任何 `.jsonl`；
2. 真实跑需要接通 worker 的 LLM 调用与 API 预算（4 阶段 × 多种子 × token 闸），
   该接线在骨架 v0.1 中未完成（见 `docs/ARCHITECTURE.md` 的未接入清单）；
3. 按本仓诚实性约束，`--fake` 回放的指标**不构成能力声明**，不允许被当作结果引用。

### 已实测的管线级数字（`llm: fake`，仅验证接线，2026-11-10 实跑）

| 检查 | 结果（真实输出） |
|---|---|
| 单元测试 | `8 passed in 0.11s`（tests/test_gates.py + test_journal.py + test_pipeline.py） |
| `--fake` 回放 | demo idea 四阶段全部 `promoted: true`；三闸判据逐条通过（`seeds 2>=2`、`delta 0.0200 > floor 0.005`、`tokens 0<=200000`） |
| Journal 校验 | `{"verify_ok": true, "entries": 5}`（append-only jsonl + sha 链，离线重放通过） |
| Journal 指标值 | s1: 0.5→0.501；s2: 0.52→0.521；s3: 0.54→0.541；s4: 0.56→0.561（全部 `llm: fake`） |

## What this doesn't claim / Limits

- 不声明任何真实研究能力：所有已跑数字均来自 `--fake` 管道回放（journal 行带 `llm: fake`）。
- worker 的文献检索、外部工具调用尚未接入（见「与现有资产的关系」表中「后续接入」项）。
- writeup 阶段的 49 校验门属于 [paper-writing-agent](https://github.com/aidless/paper-writing-agent)，本仓未接入。
- P1 真实实验数字 not yet measured（原因见 Results 节）；接入后所有晋升仍须过三闸并落 Journal。

## 目录导览

| 路径 | 内容 |
|---|---|
| `run_employee.py` | CLI：`--fake` 回放 / `--verify` journal 离线校验 |
| `employee/` | manager/worker 分离实现（pipeline、journal、gates、models） |
| `configs/employee.yaml` | 阶段门控参数（min_seeds / 噪声底 / token 预算） |
| `ideas/demo.json` | 示例 idea（fake 回放用） |
| `tests/` | 8 个单元测试（门控、journal sha 链、管线） |
| `docs/ARCHITECTURE.md` | 架构说明 + 与 SakanaAI/AI-Scientist-v2 的思想对照表（未复制代码） |


## 与现有资产的关系（只连不抄）

| 资产 | 复用点 |
|---|---|
| arx（autonomous-researcher） | 门控思想（noise floor / MDE）、Merkle账本格式 |
| just-agent | 记忆检索层（后续把 worker 的文献/context 接到它） |
| paper-writing-agent | writeup 阶段的 49 校验门（后续接入） |
| rag-qa | 文献检索 RRF 融合（后续替换 semantic_scholar 直调） |
| agent-databench | `--fake` 回放评测纪律 |

## 许可

MIT（本仓自写代码）。设计对照见 `docs/ARCHITECTURE.md`；Sakana v2 为
source-available（RAIL 衍生），本仓与其无代码关系。
