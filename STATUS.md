# 项目状态（人只看这一页）

> **最后更新：2026-10-11**。F11 v1设计冻结；阶段1核心结构重构完成，**ACCEPT WITH LIMITATIONS，待独立复核/用户验收**；阶段2未开始。
> [正式设计](MLVR_Knowledge/04_F11_v1_架构与实施设计.md) ｜ [阶段1档案](MLVR_develop/2026-10/20261011_04_f11-fixed-source-core-refactor/README.md) ｜ [任务台账（86项）](MLVR_develop/INDEX.md) ｜ [Agent交接](MLVR_Knowledge/AGENT_CONTEXT.md)

## 1. 当前进度

| 内容 | 状态 |
|---|---|
| F11总体 | design frozen；完整production implementation not completed |
| 阶段0 | 限定转换结论及独立报告保留；实验、W11/W12未修改 |
| 阶段1 | 获用户明确批准后，完成两文件Initialize/ExecutePrepared/Finalize；[结论/证据/边界](MLVR_develop/2026-10/20261011_04_f11-fixed-source-core-refactor/README.md#4-结论与边界) |
| 验证 | 旧/新CTest均9/9；103/103确定性比较；RNG/IEEE统计/WW事件一致；MPI/OMP只编译 |
| 仓库 | RMC branch/HEAD不变，批准的两文件留工作树；本Agent无commit/push/切分支/reset |

## 2. 下一步与授权

先独立复核/用户验收[实际补丁](MLVR_develop/2026-10/20261011_04_f11-fixed-source-core-refactor/changes.diff)和阶段1原始证据。是否提交由用户决定。

| 阶段 | 当前状态 |
|---|---|
| 0：Field体积归一 | 限定结论已可供后续使用 |
| 1：固定源核心 | 完成，待独立复核；本任务停止 |
| 2：CLEAR/SET/REBUILD、重复运行 | 未开始，需新任务及明确授权 |
| 3–6：TARGET/Field/WW/外部调用/闭环 | 未开始 |

prepared入口尚不具备正式reset能力，不能直接重复调用当作F11闭环。未覆盖并行数值、Windows、完整可选功能等，详见任务§4。

## 3. 证据与设计边界

04冻结正文未改；Task15/16不作为独立实施指令。新Field API仍未实现，体积计分/scorer/reference均未修改。Stage1只有结构与已测普通fresh-process行为的结论，不外推到同进程角色切换。

原始102/103全HDF比较差异仅为六个wall-clock FOM数据值；按事前允许的时间类别精确归类后，物理容差保持0。失败和分类证据完整保留在任务档案。

## 4. 其他待办

W11/W12修复、复核README收口、RMC提交/push、AIMC/论文线不在本轮。

## 5. 维护方式

每阶段单独授权；实现、自验、独立复核与最终验收分开记录。本阶段1完成后停止，不自动开始阶段2。
