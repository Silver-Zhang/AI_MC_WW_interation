# 项目状态（人只看这一页）

> **最后更新：2026-10-12**。F11 v1 设计冻结；Stage2 P1 修复后的独立复核结论为 **NEEDS CORRECTION**：Universe fingerprint 在受限 profile 内闭合，但 WW energy-bin container shape 在索引前未完整验证。RMC 未提交（复核明确不得冻结/提交）；本轮归档已提交入库。
> [正式设计](MLVR_Knowledge/04_F11_v1_架构与实施设计.md) ｜ [阶段2档案](MLVR_develop/2026-10/20261011_05_f11-prepared-run-lifecycle/README.md) ｜ [任务台账](MLVR_develop/INDEX.md) ｜ [Agent交接](MLVR_Knowledge/AGENT_CONTEXT.md)

## 1. 当前进度

| 内容 | 状态 |
|---|---|
| F11总体 | design frozen；完整production implementation not completed |
| 阶段0 | 限定转换结论及独立报告保留；实验、W11/W12未修改 |
| 阶段1 | 唯一固定源核心拆分已完成，RMC基线330f091e；结论与边界见原任务§4 |
| 阶段2 | **独立复核：NEEDS CORRECTION**；P1-01 Universe fingerprint 在确定性 CSG/rectangle/hexagon profile 内闭合，P1-02 WW energy-bin outer shape 在 neutron 索引前缺少验证；[独立结论](MLVR_develop/2026-10/20261012_01_independent-f11-stage2-p1-correction-review/Independent_F11_Stage2_P1_Correction_Review.md)；三个正式入口及各 owner 状态管理已实现，但不得冻结或进入 Stage3。 |
| 仓库 | RMC仍在Neural_Network_WW_Iteration / 330f091e；29个批准文件为本地未提交改动（复核明确不得冻结/提交，待 P1-02 修复并复试）。先前归档已入库；本轮 P1 增量证据与文档已提交入库；未切分支或更新reference/核数据库 |

## 2. 下一步与授权

Task05 的 P1 自验已完成，但独立复核发现 P1-02 尚未闭合。下一步不是 Stage3：须先由用户决定是否新开授权修复任务，补齐 WW energy-bin outer/inner shape 的 production guard 和负例，然后再次独立复核。本轮归档已提交入库；RMC 未 commit/push。

| 阶段 | 当前状态 |
|---|---|
| 0：Field体积归一 | 限定结论可供后续使用 |
| 1：固定源核心 | 已实现；历史证据保留 |
| 2：CLEAR/SET/REBUILD、重复运行 | 独立复核 `NEEDS CORRECTION`；完成 P1-02 容器形状修复并再次独立复核前，不得冻结/提交或进入 Stage3 |
| 3–6：TARGET/Field/WW文件/外部调用/闭环 | 未开始；需要新阶段授权 |

## 3. 证据与设计边界

Task05 `logs/p1-correction` 的 correction-era 36 配对 run、普通回归及生产 guard 负例保留；独立复核确认合法受限输入的持续/新进程等价与 ordinary 代表回归，但 `p_vEnergyBins[neutron]` 在 outer shape 证明前被访问，且 native terminal boundary equality 未安全映射，故不具备 malformed caller-visible WW 状态的安全拒绝保证。非零裂变、并行、任意权重/分布源等仍未开放；新 Field API 和正式 FOM 仍未实现。

04冻结正文、阶段0实验和tally体积数学公式未改。新增W13为旧能群cell SCHECK崩溃，prepared入口拒绝该组合，scorer修复需单独任务。旧HDF重复导出与本轮快照的边界见Task05和[物理说明](MLVR_Physics_Guide/04_同进程独立固定源计算.md)。

## 4. 其他待办

W11/W12/W13、P1-02 energy-bin shape 修复及 AIMC/论文线不在本轮。Stage2 的合法输入 regression 通过不等于 complete API safety，也不等于完整 F11 Ready。

## 5. 维护方式

每阶段单独授权；实施、自验、独立复核与最终验收分别记录。本轮已停止，不自动开始Stage3。
