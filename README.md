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

## 快速开始

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest tests/ -q
.venv/bin/python run_employee.py --fake --idea ideas/demo.json
.venv/bin/python run_employee.py --verify logs/demo.jsonl
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
