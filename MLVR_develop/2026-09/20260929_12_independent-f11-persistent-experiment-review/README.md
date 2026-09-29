# independent-f11-persistent-experiment-review

| 项目 | 内容 |
|---|---|
| 立项日期 | 2026-09-29 |
| 状态 | 已完成（独立复核报告；实验批准待拍板） |
| 任务模式 | C — 深度物理研究与学习 |
| 范围 | 独立审核 F11 E0–E4 实验的证据充分性；仅写本任务档案。 |
| 禁止项 | 不修改 RMC/AIMC、不修改 Task 11、不更新 STATUS/INDEX/KB、不补跑实验、不选择最终架构、不 commit/push。 |

## 1. 目标与范围

审核 E0 performance decomposition、E1 same-process Forward→Forward、E2 Forward→Adjoint→Forward、E3 WW hot update 和 E4 tally reset plus memory Field extraction 的实际证据是否足以支持其主张。

**模式 C · 物理解释：** 同进程第二轮必须是独立 MC 样本。最终 tally 看似合理不足以证明 source denominator、统计矩、RE、bank 或 Forward/Adjoint 角色没有残留。

## 2. 做法与证据

在读取 Task 11 结果前，先依据 Task 09 与 Task 10 两份独立源码审查形成独立验收标准。随后只读 Task 11 的报告、状态、原始验证产物和 proposed patch，并抽查当前 RMC 的生命周期、伴随、WW、tally 与 MG-energy 路径。

- [独立验收标准](logs/pre-result-acceptance-criteria.md)
- [证据核对](logs/evidence-check.md)
- [最终独立审核](Independent_F11_Persistent_Experiment_Review.md)

## 3. 决策

用户授权仅限证据审查与任务档案写入。不得根据审核结果修改源码或补跑实验。

**人类理解确认：** E0–E4 即使全部通过，也只能说明冻结测试域内的 test-only contract，不自动决定采用 persistent RMC。当前 Task 11 的 P1 是改变初始化控制流的实验 seam，不是纯观察插桩；其具体 driver/reset/snapshot 实现尚未可审查。

## 4. 结论与边界

- **结论：** E0–E4 均为 **INCONCLUSIVE**，因为全部 BLOCKED 且没有运行。Task 11 的预先固定判据能有效防止常见假阳性，但不构成动态证据。
- **证据：** 所有 Task 11 状态均记录 `executed=false`、零 RMC run、零 fresh oracle、空 measurement/comparison；proposal 仅通过 `git apply --check` 和 default-off 静态自检。
- **边界：** 未审查或运行正式 F11；未改变 RMC/AIMC；串行 H2O 的拟议 E2 即使将来通过，也不能验证非零裂变伴随数组、MPI 或 OpenMP。
- **建议：** 在批准 P1 前先要求可审查的 task-private driver、callback/snapshot schema、exact reset list、build plan 与 comparator。P0 与 P1 应按该完整实验包决定，而不是把现有声明草案误当可执行最小 patch。

## 5. 过程

| 时间 | 阶段 | 记录 |
|---|---|---|
| 2026-09-29 | 立项与独立标准 | 完成 Task 11 读取前验收标准。 |
| 2026-09-29 | 结果与补丁审查 | 审核 Task 11 的 BLOCKED 状态、冻结协议、proposal 和当前 RMC 源码定位。 |
| 2026-09-29 | 停止 | 输出独立结论；未修改 Task 11、RMC、AIMC、共享台账或知识库。 |
