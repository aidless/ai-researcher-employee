# ai-researcher-employee —— 自己的 AI 研究员工（骨架 v0.1）

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

## 本仓证明了什么 / 不证明什么

**证明了什么（可复算的工程事实）：**

- 4 主阶段管线（s1_implement → s2_baseline_tune → s3_explore → s4_ablate）能
  用纯离线逻辑跑通：manager 定课程表，worker 每 seed 在独立 workdir 执行，
  Journal 逐阶段 append 并构成 sha 链（`employee/journal.py`）。
- 阶段晋升门控是**纯函数**且可离线重算：`gate_seeds`（有效种子数≥min_seeds）、
  `gate_direction`（中位数差 > noise_floor，缺失记 unknown 不算失败）、
  `gate_budget`（token 用 ≤ 预算）。`tests/test_gates.py` 对每条都做了
  RED→GREEN（在噪声底内 → HOLD；超出 → 通过）。
- Journal 的 append-only 与篡改检测：`journal.verify` 重放整个链，任何一条
  `prev`/`hash` 被改动即返回 `(False, n)`；`tests/test_journal.py` 实测注入
  篡改行后被检出。
- `--fake` 管道回放：`run_episode(..., fake=True)` 逐阶段提交预设 metric，
  结果行带 `llm: fake`，能验证接线而无需任何 API key/网络。
  `tests/test_pipeline.py` 验证全 4 阶段晋升、噪声底抬高后 s2 起 HOLD。

**不证明什么（边界，fail-closed）：**

- `--fake` 跑出的任何 metric **不是实验结论**：它是回放值，`llm: fake`
  标记即证据，禁止进入能力声明或论文正文。
- 管线骨架是 v0.1：writeup（`writeup.py`）与 review（`review.py`）目前是
  占位实现，VLM 视觉通道记为 `unknown`，**未实现**。本仓不声称能产出
  完整论文——它验证的是「manager/worker 分离 + 门控 + 账本」的骨架。
- 三闸是**确定性**判据（中位数 vs 噪声底），不是统计显著性检验；没有
  对 seed 分布做方差分析，也没有校准噪声底取值。噪声底是配置参数
  （`configs/employee.yaml`），其合理性未被外部基准验证。
- 与 SakanaAI/AI-Scientist-v2 **无代码关系**：本仓只借鉴其公开设计思想
  （见 `docs/ARCHITECTURE.md` 对照表），代码、提示词、模板一律未复制。
  这是"思想对照 + 自写实现"，不是衍生作品。
- 尚未接入真实 LLM/文献检索/评审模型：`rag-qa`（RRF 融合）、
  `paper-writing-agent`（49 校验门）、`just-agent`（记忆层）在 README 中
  是**规划**而非已合并依赖。当前 `requirements.txt` 只有 pytest + pyyaml。

## 快速开始

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest tests/ -q        # 8 项，全部离线、无 API key
.venv/bin/python run_employee.py --fake --idea ideas/demo.json
.venv/bin/python run_employee.py --verify logs/demo.jsonl
```

测试套件离线可跑：`tests/test_gates.py`、`tests/test_journal.py`、
`tests/test_pipeline.py` 共 8 项，全部不需要网络或模型调用。

## 目录结构

```
ai-researcher-employee/
├── employee/
│   ├── models.py      # 纯数据类型：Idea / TrialResult / STAGES（无 I/O）
│   ├── gates.py       # 三闸纯函数：seeds / direction-vs-noise / budget
│   ├── journal.py     # append-only jsonl + sha256 链，verify 可离线重放
│   ├── manager.py     # 课程表（4 主阶段）+ should_promote 编排
│   ├── worker.py      # 每 seed 独立 workdir 执行
│   ├── pipeline.py    # run_episode：idea → 4 阶段 → Journal（默认 fake）
│   └── __init__.py
├── configs/employee.yaml   # 门控参数（min_seeds / noise_floor / budget）
├── ideas/demo.json         # 示例 idea（--fake 回放输入）
├── tests/                  # 8 项离线测试（gates / journal / pipeline）
├── docs/ARCHITECTURE.md    # 与 AI-Scientist-v2 的思想对照表（无代码复制）
├── run_employee.py         # CLI 入口（--fake / --verify / --config）
└── pyproject.toml          # pytest testpaths = tests
```

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
