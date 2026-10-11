# independent-f11-prepared-lifecycle-review

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-10-11 |
| 状态 | 已完成（**DESIGN REVIEW ONLY**；等待用户决定是否批准阶段2实施） |
| 任务类型 | F11 阶段2独立 source/design 审核 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | Claude |
| 关联知识库条目 | F11；知识库04阶段2约束 |
| 审核对象 | `20261011_05_f11-prepared-run-lifecycle`；RMC `330f091e` |
| RMC 分支 / 提交 | `Neural_Network_WW_Iteration` / `330f091eb0296e0d0124237ba7d9a22b81aee852` |

## 1. 目标与范围

独立回答：现有 RMC 是否已经能够在一次完整模型初始化后，正确执行多次 Forward/Adjoint fixed-source transport，并保持每一次结果的统计独立性和物理一致性。

本审核只读：不改 RMC、Task 05、参考结果、核数据库、`STATUS.md`、`INDEX.md` 或知识库；不 commit/push；不启动阶段3。独立结论见 [Independent_F11_Stage2_Review.md](Independent_F11_Stage2_Review.md)。

**模式C物理解释：** 每个 half-run 的估计量和归一化分母只能来自其自身源历史及后代。Forward/Adjoint 切换会改变角色、截止和派生截面，必须显式重建；旧 run 的 tally、bank、随机数段或派生数组留下任何残余，都会破坏统计独立性或物理一致性。

## 2. 做法与证据

- 在阅读 Task 05 设计前，先写入 [logs/pre-review-criteria.md](logs/pre-review-criteria.md)；其要求 FF、FAF、AA、WW-on、模型复用与普通回归的 fresh oracle 证据。
- 独立检查当前 Stage 1 wrapper / initialization / core / finalization 拓扑，确认生产 history/batch/descendant suite 仅一份，`ProcessTally` 仅由 finalizer 调用一次。见 [logs/source-call-graph.md](logs/source-call-graph.md)。
- 独立核对 `CDFixedSource`、tally/registry/statistics、ACE/adjoint、particle/source、RNG、WW、Timer/Output 与传参边界。见 [logs/state-ownership-audit.md](logs/state-ownership-audit.md)。
- 盘点 Task 05 的源修改、可执行 driver、build/transport 输出、snapshot 与 comparator 证据。见 [logs/codex-evidence-review.md](logs/codex-evidence-review.md) 和 [logs/independent-comparison.md](logs/independent-comparison.md)。

真实静态检查输出：

```text
RMC HEAD: 330f091eb0296e0d0124237ba7d9a22b81aee852
RMC diff from 330f091e to HEAD: empty
Stage-2 proposed lifecycle symbols in RMC/src: 0
Task 05 recorded production_code_modified_by_stage2: false
Task 05 recorded stage2_builds_and_transport_tests_executed: false
```

归档自检真实输出：

```text
汇总: 需处理 0 项；提示 31 项
```

提示均为其他历史档案；本任务未被报告为待处理项。

**未覆盖到的验证：** 所有阶段2动态门禁（FF、FAF、AA、WW-on、模型复用、负例与 Stage2 后普通回归）均未运行，因为 Task 05 尚未实施。没有伪造运行、数值比较或物理通过结论。

## 3. 决策记录

- **决定：** 本审核结论为 `DESIGN REVIEW ONLY`；不批准或替用户批准任何 RMC 修改。
- **决定人 / 日期：** 阶段2生产源码实施尚待用户决定。
- **约束：** 若实施，必须先取得 Task 05 §3 所列具体生产接口/文件范围的人类批准；此后按 fresh oracle 门禁重新独立审核。

| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| 重复 half-run 残留 bank/tally/adjoint/RNG/WW/Timer 状态 | 本审核不改任何生产对象；实施范围须另行批准 | E1–E6 任一缺失或出现物理差异即不得接受 persistent lifecycle | 本审核无生产改动，无需回滚 |

**模式C人类理解确认：** 尚未取得阶段2实施批准；不能把此前 Stage 1 的授权延伸为 Stage 2 授权。

## 4. 结论与边界

- **结论：** `DESIGN REVIEW ONLY`。Stage 1 的单一执行 core 为正确的结构前提；现有 RMC 不具有已实施的 repeated prepared fixed-source lifecycle。
- **设计判断：** Task 05 对 CLEAR/SET/REBUILD、原始数据保持、RNG 子流、WW 三界与非零裂变限制的处理方向与独立 source 审核一致；它仍只是待实施设计。实施前还须修正三项具体设计缺口：test target 的全局 singleton 链接所有权、非单位/偏倚 source distribution 下的真实初始权重与分母合同、以及由 process-global `Total` timer 导致的统计 FOM 计时归属。详见风险表。
- **不能推出什么：** 不可声称 FF/FAF/AA/WW-on/模型复用已通过；不可外推到裂变材料、CE、MPI/OpenMP、耦合粒子、restart、burnup、Python source 或完整 F11。
- **遗留 / 下一步：** 等待用户是否批准 Task 05 的具体 Stage 2 实施；若实施，必须完成 E1–E6 fresh-oracle 比较后再做动态独立复核。
- **提交状态：** 本审核未修改 RMC、未 commit/push。RMC 在审核结束仍为 `330f091e` 且工作树无本审核改动。档案随 2026-10-11 根工作区提交入库。

**模式C结果解释：** 本结论否定的是“已经实现并验证”的主张，不是否定该设计方向。当前源码中 role、统计、bank、随机数与全局 WW/Output 状态均有明确重置/重建需求；在没有实现和逐 run 证据前，它们不能被当作统计独立的 persistent transport。

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-10-11 | 按模式C创建独立审核档案；在读取 Task 05 设计前写入独立验收标准。 |
| 2026-10-11 | 检查 Stage 1 私有 helper、唯一 history loop、唯一 `ProcessTally` 和当前 source lifecycle owner。 |
| 2026-10-11 | 检查 Task 05 设计/静态证据及当前 RMC diff/符号；确认无 Stage 2 源码、driver、构建、输运或动态比较。 |
| 2026-10-11 | 完成独立报告、状态矩阵、风险表与归档自检；停止等待用户决定。 |
