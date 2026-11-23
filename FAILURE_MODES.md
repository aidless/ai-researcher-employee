# 失败模式

这里列的是当前代码里已经发生的失败方式。计数以 README 的检查块为准，由 `make check` 重算；本文件不另报一套数字。夹具标签在 `eval/fixtures/gate_journal_matrix.json`。

## Journal 校验漏掉什么

`employee/journal.py` 的 `verify` 只重放文件里还在的那些行。

- `drop-tail`：删掉最后一行之后，剩下的前缀仍然算出合法的哈希链，`verify` 返回成功。append-only 只是写入方的约定，读入方不拒绝截断。
- `reorder-keys`：哈希是对 `prev` 加上按键名排序后的 `kind`/`payload` 计算的（`hashlib.sha256`）。只重排一行 JSON 的键，解析结果不变，`verify` 返回成功。这不是按字节封存。
- 整份文件换成另一条从 `GENESIS` 合法链下来的记录，也会通过。没有外部锚点、签名或已公布的链头。
- `append` 不先调用 `verify`。它把文件里最后一行的 `hash` 字段当作下一条的 `prev`，即使那一行已经坏了。
- 失败时返回的整数是「坏行之前已经通过的条数」，空行会被跳过，所以它不是文件行号。
- 路径不存在时抛 `FileNotFoundError`，而不是一个 `(False, …)` 结果。

会被抓住的改动也在同一夹具里：改 `prev`、改 `hash`、改 payload 而不重算哈希、追加一条伪造记录、对调前两行。

## 三闸的判据边界

- `gate_direction` 用中位数之差**严格大于** `noise_floor`。相等是 HOLD。这不是显著性检验，噪声底也没有对外部基准做过校准，它只是 `configs/employee.yaml` 里的参数。
- 候选或基线没有可用 metric 时，方向闸返回假，文案里写着 unknown、not failure。`should_promote` 只看布尔值，会把它当成和其他 HOLD 一样的短路，调用方如果只存布尔值，就分不清「未知」和「改进落在噪声底里」。
- `gate_seeds` 在种子不够时返回假，但文案里**没有** HOLD 这个词；方向闸和预算闸的失败文案里有。检查块里的 `gate_hold` 表示闸函数返回假，不是「文案含有某个词」。`None` 不计入有效种子，`0.0` 会计入。
- `should_promote` 遇到第一道失败就返回，后面的闸不会被执行，也不会被记下来。
- `run_episode` 调用 `should_promote` 时不传 token 用量，因此用的是默认值（零）。预算闸作为纯函数是有效的；在这条管线路径上它看不到真实用量。
- `s1_implement` 不经过三闸。`employee/pipeline.py` 把该阶段直接标成晋升，原因字符串是 `s1 baseline, no gate`。
- HOLD 不会让 `run_episode` 停下来。后面的阶段仍会执行；比较用的基线停在上一次晋升的阶段，而不是刚被 HOLD 的那一阶段。

## 回放不是实验

- `run_employee.py` 调用 `run_episode` 时传入 `fake=a.fake or True`。命令行上的 `--fake` 关不掉回放，这条路径到不了真实模型。
- `employee/worker.py` 的 `run_trial` 在 `fake` 为真时，用阶段下标和 seed 算一个 metric，并标 `llm="fake"`。那个公式只证明接线，不进入 README 的结果。
- `fake=False` 会把调用方给的代码写进临时目录并用子进程执行，超时时间之外没有容器、系统调用过滤或网络隔离。当前命令行到不了这条路径。

## 仓库里没有的东西

- 没有 `writeup.py`，也没有 `review.py`。以前的文档把它们写成占位实现，那是错的。
- `requirements.txt` 里只有 pytest 和 PyYAML。PyYAML 只在 `employee/pipeline.py` 的 `load_cfg` 里导入。`make check` 不导入 pytest 或 PyYAML，也不访问网络。
- 名字出现在旧文档里的 arx、just-agent、paper-writing-agent、rag-qa、agent-databench 都不是本仓库的依赖，本仓库也不引用它们的内部数字。
