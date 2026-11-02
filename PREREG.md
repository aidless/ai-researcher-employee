# PREREG — ai-researcher-employee (骨架 v0.1)

> 预注册规格：本文件声明**本仓库在 v0.1 状态下可检验的研究假设、评测方案、
> 成功标准与明确边界**。它反映仓库真实内容（`employee/gates.py` 三闸纯函数、
> `employee/journal.py` append-only sha 链、`employee/pipeline.py` 离线管线、
> `tests/` RED→GREEN 断言），不含任何虚构数字或未实现能力。
>
> 与 SakanaAI/AI-Scientist-v2 的差异：本仓只借鉴其公开**设计思想**
> （`docs/ARCHITECTURE.md` 对照表），代码、提示词、模板一律未复制。

## 1. 研究问题

一个「课程式 manager/worker 分离」的自主研究管线，如何保证**阶段晋升**
只发生在可复算的判据上，而不是模型或人的主观判断？本仓把这个问题做成
**可离线复现的机制问题**：四主阶段（`s1_implement → s2_baseline_tune →
s3_explore → s4_ablate`）中，后段能否晋升由三闸纯函数决定，且每个决定都
落在 append-only 的 sha 链账本里，可被外部重放校验。

## 2. 假设（H1–H3，全部可证伪）

- **H1（闸门是唯一通道）**：阶段晋升只由 `manager.should_promote` 的
  三闸（`gate_seeds` / `gate_direction` / `gate_budget`，`employee/gates.py`）
  判定；任一闸不过即 `HOLD` 并记入 Journal，不静默丢弃。
- **H2（账本可校验）**：Journal 是 append-only jsonl + sha 链
  （`employee/journal.py`）；`verify` 重放整个链，任何一条 `prev`/`hash`
  被改动即返回 `(False, n)`。
- **H3（门控可复算）**：三闸是**纯函数**（无 I/O、无随机），给定相同
  `TrialResult` 序列与配置，输出确定且可离线重算。

## 3. 评测方案

- **管线**：`run_episode(idea, cfg, log_path, fake=True)` 离线跑四阶段；
  worker 每 seed 在独立 workdir 执行，逐阶段 append 到 Journal。
- **闸门**：`gate_seeds`（有效种子数 ≥ `min_seeds`）、`gate_direction`
  （候选相对基线中位数差 > `noise_floor`，缺失记 `unknown` 不算失败）、
  `gate_budget`（token 用 ≤ `budget_tokens`）。参数在
  `configs/employee.yaml`（`min_seeds: 2`、`budget_tokens: 200000`、
  `noise_floor: 0.005`、`seeds_per_stage: 2`）。
- **判据**：三闸均为**确定性**判据（中位数 vs 噪声底），不是统计显著性检验；
  没有对 seed 分布做方差分析，也没有校准噪声底取值。

## 4. 成功标准

1. `tests/test_gates.py` 对每条闸都做 RED→GREEN：在噪声底内 → `HOLD`；
   超出 → 通过（本仓已实现，8 项离线测试全过）。
2. `tests/test_journal.py` 实测注入篡改行后被 `journal.verify` 检出。
3. `tests/test_pipeline.py` 验证全 4 阶段晋升；噪声底抬高后 `s2` 起 `HOLD`。
4. `--fake` 管道回放逐阶段提交预设 metric，结果行带 `llm: fake`。

## 5. 明确边界（不证明什么）

- **不证明任何研究结论**：`--fake` 跑出的 metric 是回放值，`llm: fake`
  标记即证据，禁止进入能力声明或论文正文。
- **不证明模型已接入**：管线 v0.1 是**离线**（全 CPU、无真实 LLM/文献检索/
  评审模型）；`writeup.py` 与 `review.py` 是占位实现，VLM 视觉通道记为
  `unknown`，未实现。
- **不证明与 Sakana v2 的衍生关系**：本仓无代码关系，只借鉴公开设计思想。
- **不证明能产出完整论文**：骨架验证的是「manager/worker 分离 + 门控 +
  账本」的机制，不是论文成稿能力。

## 6. 数据与复现

- 配置：`configs/employee.yaml`；演示 idea：`ideas/demo.json`。
- 复现：
  ```bash
  python3 -m pytest tests/ -q        # 8 项，全部离线、无 API key
  python3 run_employee.py --fake --idea ideas/demo.json
  python3 run_employee.py --verify logs/demo.jsonl
  ```
