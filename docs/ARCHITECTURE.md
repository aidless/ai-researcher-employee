"""Design notes: what we learned from reversing others (ideas only, no copied code)."""

# AI-Scientist-v2（Sakana，source-available/RAIL衍生）思想对照
#
# | v2 设计              | 本仓对应实现                  | 差异                       |
# |----------------------|-------------------------------|----------------------------|
# | AgentManager 定4主阶段课程 | manager.STAGES + 阶段目标表 | v2 由 LLM 生成子阶段目标，本仓 v0.1 用固定课程表（确定性优先） |
# | Journal{plan/code/结果/metric} | journal.py append-only账本 | v2 节点含代码+VLM反馈；本仓只记 metric+摘要+sha链（轻量） |
# | 最优节点隔离复用防污染 | worker 每次在独立 workdir 跑 | 同思想，简化实现 |
# | 多种子+图聚合后才晋升 | gates.py 三闸（种子数/方向/预算） | v2 用 LLM 选优；本仓用中位数>噪声底（可复算） |
# | 引文→成稿→反射解耦 | writeup.py（模板渲染，v0.1占位） | 引文检索后续接 rag-qa，不直调外部 API |
# | 文本+视觉双通道评审 | review.py 清单制（v0.1占位） | VLM 通道记为 unknown，暂不实现 |
# | token追踪+断点续跑 | Journal 即断点（重放 verify） | token 计数后续接 |
#
# 许可边界：本文件只记录思想。Sakana v2 的代码、提示词、模板一律不入仓；
# REA 取证证据见 /tmp/opencode/rea-aiscientist-v2.json（evidence ev_40a2b54e…，
# root ea62dd14…，0矛盾，10节点——Python仓，JS分析器覆盖有限，如实记录）。
