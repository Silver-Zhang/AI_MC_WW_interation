# 任务总台账

> 一行一个任务。新增由 `new_task.sh` 自动追加，状态变化手工/由 Agent 更新。
> 状态词表见 [README.md](README.md)。

## 进行中 / 已处理

| 立项日期 | 任务 | 类型 | 状态 | 关联KB | 提交 |
|---|---|---|---|---|---|
| 2026-08-25 | [f02-w5-nonuniform-density-reciprocity-verification](20260825_f02-w5-nonuniform-density-reciprocity-verification/README.md) | 算法实验 / 现有能力验证 | 已完成 | W5 | 200k 原批次严格门槛失败；1M 全量精度升级通过逐种子、分组与总体判据 |
| 2026-08-25 | [f02-w5-local-density-adjoint-weight-fix](20260825_f02-w5-local-density-adjoint-weight-fix/README.md) | 缺陷修复 | 已完成 | W5 | 两处权重分母使用局部总原子密度；三种密度权重恢复 $1:1:1$；回归通过；未提交 |
| 2026-08-25 | [f02-w7-neutron-only-adjoint-init-fix](20260825_f02-w7-neutron-only-adjoint-init-fix/README.md) | 缺陷修复 | 已完成 | W7 | 按粒子模式隔离伴随能群上限；原崩溃输入退出 0，既有回归 1/1 通过；未提交 |
| 2026-08-25 | [physics-guide-topic-refactor](20260825_physics-guide-topic-refactor/README.md) | 文档 | 已完成（复核校正） | F02 / W5 / W6 / W7 | 按物理功能重构导读；校正 tally/银行/吸收语义；补充 W7 修复逻辑与门控图 |
| 2026-08-25 | [human-physics-guide](20260825_human-physics-guide/README.md) | 文档 | 已完成 | F02 / W5 / W6 / W7 | 建立 `MLVR_Physics_Guide/`，整理当前结论及三缺陷物理解读；未修改 RMC |
| 2026-08-25 | [f02-adjoint-numerical-verification](20260825_f02-adjoint-numerical-verification/README.md) | 算法实验 / 现有能力验证 | 已完成（第一阶段） | F02 / W5 / W6 / W7 | V0 通过；V2 数值确认 W5；V4 两群对互易性通过；V3 功效不足且被 W7 阻断；未修改 RMC/reference |
| 2026-08-24 | `20260824_workflow-baseline` | 工作流/知识库基线 | 已完成 | 00 / AGENT_CONTEXT / DECISIONS | GitHub history |
| 2026-08-24 | `20260824_stage1-framework-requirements` | 功能需求基线 | 已完成并确认 | 01 / 02 / DECISIONS | GitHub history |
| 2026-08-24 | `20260824_stage2-audit-protocol` | 审查规范 | 已完成 | 02 / 03 / DECISIONS | GitHub history |
| 2026-08-24 | `20260824_f02-mg-adjoint-transport-audit` | RMC只读功能审查（F02-A） | 已完成 | F02 / 03 | 未修改 RMC |
| 2026-08-24 | `20260824_f02-adjoint-physics-verification` | RMC只读物理正确性审查（F02-B） | 待决策 | F02 / W5 / W6 | 独立复核及 Claude 第二轮反驳再复核完成；成员/getter 数据流与已登记双 nubar 实表均维持 W5/W6，完整能力 E、受限子域 C；待人工复核；未修改 RMC |

## 待办储备（来自知识库 06 文档，尚未立项）

按优先级排列，处理时用 `./new_task.sh <短名> <KB编号>` 立项。

| KB编号 | 问题/想法 | 级别 | 优先级 |
|---|---|---|---|
|  |  |  |  |
