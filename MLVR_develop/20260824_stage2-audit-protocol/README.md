# Task: Stage 2 audit protocol

日期：2026-08-24

状态：已完成

## 1. 任务目标

建立 Stage 2 RMC 功能审查的统一协议，使不同 Agent 对同一功能采用一致的审查深度、证据标准、输出模板和分类体系。

## 2. 范围

本任务只修改工作流和知识库文档。

不涉及：

- RMC 源码修改；
- AIMC_WWiteration 源码修改；
- RMC 接口设计；
- 功能修复；
- 数值算例运行。

## 3. 用户已拍板的规则

2026-08-24 网页端讨论后冻结：

- Stage 2 按 `Requirement → Existence → Actual Behavior → Requirement Match → Integration Compatibility → Targeted Verification → Classification` 审查；
- 审查深度分 L1–L4，按风险选择；
- 统一采用 A–F 六类结论；
- `Audit ≠ Repair`；
- 一次只审一个逻辑功能；
- 首项正式审查为 F02 多群 Adjoint transport。

## 4. 本次实施

已完成：

- 新增 `MLVR_Knowledge/03_RMC功能审查规范.md`；
- 更新 `02_RMC功能审查矩阵.md` 为 A–F 分类；
- 更新 `DECISIONS.md`，追加 D014–D017；
- 更新 `00_开发总纲与阶段路线.md`，Stage 2 标记为已启动；
- 更新 `AGENT_CONTEXT.md`；
- 整理 `MLVR_Knowledge/README.md` 文档地图；
- 建立第一项正式审查任务 `20260824_f02-mg-adjoint-transport-audit/`。

## 5. 验证

本任务为纯文档/流程构建，无 RMC/AIMC 源码改动，因此不运行物理或回归测试。

验收条件：

- 审查协议、分类、输出模板和首项任务均有明确落盘位置；
- Agent 上下文能直接指向当前 Stage 2 和 F02 任务；
- 未修改 RMC/AIMC 源码。

## 6. 结果

Stage 2 审查方法已冻结，首项 F02 任务已可交由本地 Agent 执行只读调查。
