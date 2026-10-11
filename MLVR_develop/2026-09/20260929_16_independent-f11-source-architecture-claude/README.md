# independent-f11-source-architecture-claude

| 项目 | 内容 |
|---|---|
| 立项日期 | 2026-09-29 |
| 状态 | 已完成独立报告与设计（YES WITH CORRECTIONS）；README 于 2026-10-11 统一归档时补齐 |
| 任务模式 | C — 深度物理研究与学习 |
| 范围 | 独立 source-level audit 与 F11 production v1 architecture design。 |
| 原独立任务禁止项 | 不读 Task 15、不改 RMC/AIMC/STATUS/INDEX/KB、不 commit/push。 |

## 1. 目标与范围

直接读取 current RMC source，独立审查 F11 lifecycle、状态、source、tally、WW、input、Control 和 output 结构，并提出 production v1 架构。冻结范围是 standard MGACE、neutron fixed-source、serial、Cartesian Field、native track-mesh WW 与固定 K。

**模式 C · 物理解释：** 生产架构必须把不可变模型、每轮统计状态和正/伴随派生状态分离。重复 run 的正确性取决于这一状态边界，而不是仅仅将多次计算放入一个循环。

## 2. 做法与证据

先写 source questions，再读 current RMC source。Task 15 和本轮 Codex 输出不读。先形成 source事实，再允许以 Task 09–14 的动态证据限定设计风险，且不复制 Task 13 harness。

- [预审查问题](logs/pre-review-questions.md)
- [独立源码审查](Independent_RMC_F11_Source_Audit_Claude.md)
- [独立架构设计](Independent_F11_Architecture_Design_Claude.md)
- `logs/source-call-graph.md`、`state-ownership-table.md`、`source-evidence-index.md`、`design-options.md` 与 `risk-register.md` 保留原独立分析的证据和推理。

## 3. 决策

用户原授权仅限审查、设计和本任务档案写入，不据此开始 production implementation。

**人类理解确认：** 推荐架构只是在冻结范围内的 production v1 设计。原稿中的不同输入/WW/配置方案属于独立建议，不等同于已逐项批准的实施指令。

2026-10-11 后续决定：用户要求先将网页合并方案敲定入库，再本地 fetch 并逐步开发。现行设计见 [知识库 04](../../../MLVR_Knowledge/04_F11_v1_架构与实施设计.md)；本 README 的补齐由该后续文档任务完成，不是独立 reviewer 重新读取 Task 15 或修改本报告来迎合合并方案。

## 4. 结论与边界

原独立结论为 **YES WITH CORRECTIONS**：建议由 CDCalMode 组织 MLVR；抽出唯一固定源执行核心；明确生产 reset 与 F/A 重建；沿用现有数据所属类并增加少量根目录实现文件，不建平行 src/MLVR 子系统。原稿具体条件仍以独立设计末节为准。

原报告未实现生产接口，也未进行新的生产测试。Task 13/14 的非裂变串行实验不能替代非零裂变产生项的连续 F/A 验证。原稿与 Task 15 的差异，已由知识库 04 §2 记录合并取舍；不回写或覆盖这两份独立正文。

## 5. 过程

| 时间 | 阶段 | 记录 |
|---|---|---|
| 2026-09-29 | 立项与独立问题 | 原记录：完成 pre-review-questions.md，尚未读取 Task 15 或本轮 Codex 输出。 |
| 2026-09-29 | 原报告归档 | cf260610 已归档独立源码审查和设计正文；当时 README §4/§5 尚未补齐。 |
| 2026-10-11 | 后续统一归档补记 | 仅按已存在正文补齐本 README 的结论、链接和时间边界；不修改独立报告、代码或实验结果。 |
