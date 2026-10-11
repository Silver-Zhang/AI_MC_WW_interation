# independent-f11-stage2-implementation-review

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-10-11 |
| 状态 | 已完成（**NEEDS CORRECTION**；受限动态门禁通过，但保留两个 P1 API 完整性缺口） |
| 任务类型 / 模式 | F11 Stage 2 实际生产实现与动态证据独立审核 / C |
| 报告人 | Claude |
| 关联知识库条目 | F11；知识库04 |
| 审核对象 | 当前 RMC working tree、Task 05 实际补丁/测试程序/原始 gates-04 证据 |
| RMC 分支 / 基线 | `Neural_Network_WW_Iteration` / `330f091eb0296e0d0124237ba7d9a22b81aee852` |

## 1. 目标与范围

独立审核 Stage 2 是否真实实现一次模型初始化后的同进程多次 Forward/Adjoint fixed-source transport，并使各 half-run 与独立 fresh-process oracle 严格一致。

本任务只读：没有修改 RMC、Task 05、reference、核数据库、STATUS、知识库或 Stage 3；没有 commit/push；没有修复发现的问题。

**模式C物理解释：** 每轮估计量只应包含本轮源历史及其后代，分母是本轮实际起始权重和；A/F切换必须重建角色相关算子、cutoff、particle/cache 和 WW 派生状态。当前审核结论适用于明确受限的 Linux serial standard MGACE neutron profile，不外推为完整 F11。

## 2. 做法与证据

- 在读取 Task 05 最终 PASS 摘要前写入 [logs/pre-implementation-review.md](logs/pre-implementation-review.md)。
- 检查 RMC 当前 HEAD、branch、tracked diff、untracked 文件，并与 Task 05 批准的29文件清单核对。
- 直接审核 public API、唯一输运 core、各 owner 的 CLEAR/SET/REBUILD、source-weight hook、RNG、WW、Timer/FOM 与普通入口。
- 独立读取 G0、Gate1–7 原始 command/exit/result、final receipt、snapshot、trace、linkage、ordinary comparison、negative cases 与 comparator self-test。
- 独立抽查 FF、FAF、AA、WW raw/final/derived/receipt/trace 并重新计算 N/D/W0、seed/offset、source/finalize 事件和关键 hash；没有调用 Task 05 comparator 逻辑。

主要交付：

- [Independent_F11_Stage2_Implementation_Review.md](Independent_F11_Stage2_Implementation_Review.md)
- [logs/source-diff-audit.md](logs/source-diff-audit.md)
- [logs/state-ownership-review.md](logs/state-ownership-review.md)
- [logs/gates-verification.md](logs/gates-verification.md)
- [logs/independent-numerical-comparison.md](logs/independent-numerical-comparison.md)
- [logs/risk-register.md](logs/risk-register.md)

## 3. 真实审核输出摘要

```text
RMC HEAD: 330f091eb0296e0d0124237ba7d9a22b81aee852
Stage2 working-tree scope: 24 tracked + 5 untracked = 29 approved files
final gate artifacts: 34 half-runs, 17500 histories per side
independent receipt recomputation: all_N_D_W0=True
source_count_matches=True
finalize_once=True
```

最终原始证据的抽查结果：

- G0 linkage：PASS；test OFF/ON、main/globals 唯一性和编译选项证据存在。
- Gate1 ordinary：123/123，physical tolerance 0；最终 CTest 10/10 exit 0。
- FF / FAF / AA / WW comparator：均 exit 0、physical tolerance 0、errors 0；FF仅保留封闭的时间/FOM字段例外。
- WW1/WW2：存在实际 split、roulette、bank 和 WW query 事件。
- source receipts：N=D=W0、min=max=1、违规数0，且 source event 数量=N、Finalize 每轮一次。

## 4. 最终结论与边界

```text
NEEDS CORRECTION
```

受限 Stage 2 已真实实现并通过其自验及本轮证据抽查，但当前 public prepared API 仍有两个必须修正的 P1 完整性缺口：

1. prepared definition fingerprint 没有覆盖 `geometry.p_vUniverse` 的内容，只记录其 size；两轮之间的 universe fill/transform mutation 可能不触发绑定模型 guard。
2. prepared WW validation 检查 lower 及乘积有限性，但没有显式验证 WUPN、WSURVN、MXSPLN 自身 finite/positive/contract-valid；普通 parser 的校验不能替代 caller-visible API guard。

此外，legacy StatisticsTester FOM 明确是 process-cumulative，不是新 prepared per-run metric；receipt 已标记 `legacy_mixed_not_per_run` / `statisticsFomIsRunMetric=false`，因此不作为隐藏失败，但不得拿来作正式 MLVR FOM。

### 不能推出什么

- 不能把当前结果外推到非零裂变连续 F/A、MPI/OpenMP/AIS/Python prepared 数值生命周期、CE、耦合粒子、restart/surface source、复杂或任意加权分布源。
- 不能宣称完整 F11 Bootstrap/K、TARGET、Field、WW HDF5、外部重构闭环已经实现。
- 不建议在两个 P1 缺口修复和负例补充前无条件验收或进入 Stage 3。

### 提交状态

本审核未修改 RMC、未修改 Task 05、未修改 reference/核数据库，未 commit/push。RMC 仍为 `330f091e` 加本地 Stage 2 working-tree 改动。

## 5. 过程记录

| 时间 | 事件 |
|---|---|
| 2026-10-11 | 读取工作流上下文、STATUS、AGENT_CONTEXT、KB04；确认 Task 05 已实施且 RMC 为330f基线加本地改动。 |
| 2026-10-11 | 建立 Task 07；在最终 PASS 摘要前写入独立 pre-implementation criteria。 |
| 2026-10-11 | 审核29文件实际diff/untracked文件、public API、唯一core、owner reset/rebuild和G0链接所有权。 |
| 2026-10-11 | 审核 final gates-04、ordinary comparison、negative evidence、linkage、receipt、comparator selftest和失败台账。 |
| 2026-10-11 | 独立抽查 FF/FAF/AA/WW raw snapshots、trace、receipt，并复算 N/D/W0、seed/offset、事件和时间标签。 |
| 2026-10-11 | 记录两个 P1 API integrity gaps 与 P2 legacy FOM限制；停止等待用户决定。 |
