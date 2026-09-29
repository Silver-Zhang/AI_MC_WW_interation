# F11 RMC persistent execution audit, Claude

| 项目 | 内容 |
|---|---|
| 立项日期 | 2026-09-29 |
| 状态 | 已完成（独立报告；F11 方向待拍板） |
| 任务模式 | C — 深度物理研究与学习 |
| 关联知识库条目 | F11 前置审查 |
| 范围 | 仅静态审查 RMC、AIMC_WWiteration 与允许的 F02–F10 已归档证据；不修改源码、共享台账、知识库或基准。 |
| 独立性 | 未读取 `20260929_09_f11-rmc-runtime-architecture-audit-codex/`。 |

## 1. 目标与范围

独立审查当前 RMC 是否具备在单一进程中反复完成 forward/adjoint fixed-source calculation 的结构基础，并识别可持久化、必须重置及尚需实验验证的状态。产物为 F11 决策提供事实依据，不选择最终架构，也不实现接口或控制器。

完成标准：输出含源码证据、明确置信标签、最小必要实验与人工决策问题的审查报告。

## 2. 做法与证据

先完成只基于当前 RMC 源码、测试和输入示例的 preliminary view，后才读取允许的 F02–F10 归档作交叉核验。AIMC 责任另行独立定位。证据按 SOURCE CONFIRMED、ARCHIVE SUPPORTED、INFERENCE、UNKNOWN 标注。

- 主报告：[Independent_RMC_Persistent_Execution_Audit_Claude.md](Independent_RMC_Persistent_Execution_Audit_Claude.md)
- 独立初判：[logs/preliminary-independent-architecture-view.md](logs/preliminary-independent-architecture-view.md)
- 源码地图：[logs/source-map.md](logs/source-map.md)
- 版本与证据说明：[logs/evidence-notes.md](logs/evidence-notes.md)

## 3. 决策

本任务授权仅限独立静态审查与档案写入。不得修改 RMC、AIMC、共享知识库、STATUS 或 INDEX，也不得选择 F11 最终架构。对 RMC 改动和 F11 架构选型仍须由人工另行拍板。

**人类理解确认：** 静态审查只能区分可定位的状态与结构性风险，不能证明 repeated-run、MPI 或 mode switch 的数值正确性。报告中的 E1–E6 是实现或集成前必须单独立项的最小验证，不构成已获批准的实施。

## 4. 结论与边界

- **结论：** 当前 RMC 是单次命令行生命周期，缺少经证明的 persistent fixed-source session。fixed-source reset、Forward/Adjoint 转换、WW hot update、tally snapshot 和输出隔离均存在明确的生命周期缺口或未验证边界。
- **证据：** 主报告引用 current RMC 的 `main`、fixed-source 初始化/输运、tally、WW、material/ACE、MPI 和 output 路径；AIMC 责任表引用其 active `src/`。
- **边界：** 未执行任何实验，未验证 MPI/OpenMP/CE/耦合粒子，未选择最终架构，未修改 RMC/AIMC 或基准。任何同进程安全结论都必须经 E1–E6 的独立实验确认。

## 5. 过程

| 时间 | 阶段 | 记录 |
|---|---|---|
| 2026-09-29 | 立项 | 按用户指定独立范围建立档案；未调用 `new_task.sh`，以避免修改被明确禁止的 INDEX。 |
| 2026-09-29 | 独立初判 | 在读取 F02–F10 档案前完成 preliminary view。 |
| 2026-09-29 | 静态审查 | 完成 current RMC 生命周期/状态/模式/WW/tally/output 审查，并以允许档案作受限交叉核验。 |
| 2026-09-29 | 停止 | 报告完成，状态置为待决策；未修改共享 STATUS/INDEX。 |
