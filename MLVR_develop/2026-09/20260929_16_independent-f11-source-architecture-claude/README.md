# independent-f11-source-architecture-claude

| 项目 | 内容 |
|---|---|
| 立项日期 | 2026-09-29 |
| 状态 | 实施中（独立审查与设计；README 未定稿） |
| 任务模式 | C — 深度物理研究与学习 |
| 范围 | 独立 source-level audit 与 F11 production v1 architecture design。 |
| 禁止项 | 不读 Task 15、不改 RMC/AIMC/STATUS/INDEX/KB、不 commit/push。 |

## 1. 目标与范围

直接读取 current RMC source，独立审查 F11 lifecycle、状态、source、tally、WW、input、Control 和 output 结构，并提出 production v1 架构。冻结范围是 standard MGACE、neutron fixed-source、serial、Cartesian Field、native track-mesh WW 与固定 K。

**模式 C · 物理解释：** 生产架构必须把不可变模型、每轮统计状态和正/伴随派生状态分离。重复 run 的正确性取决于这一状态边界，而不是仅仅将多次计算放入一个循环。

## 2. 做法与证据

先写 source questions，再读 current RMC source。Task 15 和本轮 Codex 输出不读。先形成 source事实，再允许以 Task 09–14 的动态证据限定设计风险，且不复制 Task 13 harness。

- [预审查问题](logs/pre-review-questions.md)
- `logs/source-call-graph.md`、`state-ownership-table.md`、`source-evidence-index.md`、`design-options.md` 与 `risk-register.md` 将保留源码证据和设计推理。

## 3. 决策

用户授权仅限审查、设计和本任务档案写入。不得据此开始 production implementation。

**人类理解确认：** 推荐架构只是在冻结范围内的 production v1 设计。任何 RMC 改动、input card、外部命令协议、F11 scope 扩展与最终实现都必须另行拍板。

## 4. 结论与边界

待审查完成后填写。

## 5. 过程

| 时间 | 阶段 | 记录 |
|---|---|---|
| 2026-09-29 | 立项与独立问题 | 完成 `pre-review-questions.md`，尚未读取 Task 15 或本轮 Codex 输出。 |
