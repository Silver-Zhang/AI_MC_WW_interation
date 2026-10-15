# F11 Stage 3 设计独立审查

| 项 | 内容 |
|---|---|
| 审查日期 | 2026-10-15 |
| 审查对象 | [Stage3 具体实施设计](stage3-design.md) 与 [最小验收设计](test-plan.md) |
| 源码基线 | RMC `Neural_Network_WW_Iteration` / `4810694b7a99dfc3ad7d27f7d443814f511f4829` |
| 审查类型 | Claude 独立设计审查；静态源码与方案核对 |
| 总体结论 | **NEEDS REVISION** |
| 实施状态 | 未授权、未实施；未构建、未运行输运 |

## 1. 范围与判定方法

独立检查 Stage 3 的输入与 TARGET、体积/群映射、TARGET 伴随源、source-history 响应与 RE、Prepared lifecycle/Stage 2 兼容性、拟修改文件及测试门禁。审查依据为上表所列冻结 RMC 源码身份、任务中的设计与测试文档、F11 冻结设计及 Stage 2 最终档案。没有把方案作者的自查或拟运行测试当作实现证据。

本报告只判断设计是否足以进入后续批准，不批准生产修改，不改变知识库 04 的冻结规则，也不代表 Stage 3 已实现或通过物理验收。

## 2. 结论摘要

串行固定源 history hook 的源码时序支持该设计方向：后代 bank 在完整 history 结束前处理完；现有 `SumUpTally` 位于 `SumTallyBin` 清分数之前；因此在清除临时 score 前按选定 bin/group 聚合一次标量，并为零得分 history 显式增加 N，能够保留 history 相关性。没有发现 P0。

但方案与测试合同之间仍有两项 P1 缺口，尚不能按当前文本进入实现审批：

1. **P1 — MPI TARGET 响应的全局语义/拒绝路径不闭合。** 设计把 `S1/S2/N` 放在 `CDTally` 的独立 accumulator 中，现有汇总链主要处理普通 tally 数组；设计和测试以 serial 为主，也泛称未开放 profile 应拒绝，但没有明确生产入口在哪一处、以何状态拒绝 MPI，或定义 TARGET scalar、N、完成历史数及补偿累计的跨 rank 归约合同。若 MPI 被允许运行而 accumulator 未归约，receipt 中的响应/RE 将是 rank-local 或不一致。
2. **P1 — T4 独立 raw-segment/history oracle 尚不可复现。** 测试计划要求只读 GDB 记录原始段并重建完整 history、后代关系及 N；但没有给出可执行的断点/观测脚本、记录格式和 root-history/descendant 关联规则。拟修改清单不含 `ScoreMeshTally.cpp` 的 observer/trace；准备 profile 又拒绝 PTRAC。故 T4 目前是验收目标，不是可直接执行、可复核的 oracle 合同。不能仅以普通 `Ave` 或被测转换 helper 代替独立参考。

另有一项 **P2 实施门禁**：现有 type-4 bin 分布的抽样端点和区间均匀性，需要先对真实生产 sampler 做小型 micro-oracle；这是实施时可由门禁关闭的风险，不单独构成当前 P1。

## 3. 关键核对

| 主题 | 审查判断 | 证据与边界 |
|---|---|---|
| TARGET、体积和群映射 | 设计定式与冻结接口总体一致：区域并集去重、按体积转换、按所选物理群求和，并区分物理群与内部群坐标。 | 设计明确列出 `Energy=-1` 的 G+1 tally 布局及 Tot 槽处理；这仍是设计合同，尚无新接口动态验证。复杂几何保守拒绝范围应保留。 |
| TARGET→伴随源 | bin 按体积、群等概率、方向各向同性、单位人工初始权重的设计概率与尺度分离方向清楚。 | 设计保留现有源抽样/权重审计并提议逐字段及 CDF 检查；实际分布抽样、尺度、源能量映射和单位权重尚无实现证据。 |
| history-level R/RE | 在 serial 路径中，于 `SumTallyBin` 清除前读取选中 score，并按完整 history 只形成一个 `r_h`，统计 S1/S2/N，理论上正确保留跨 bin/group 相关性和零得分历史。 | `RMC/src/CalcFixedSource.cpp` history/bank-drain 链、`RMC/src/SumUpTally.cpp` 调用边界及 `RMC/src/TallyData.cpp` 清理顺序支持该时序；`RMC/src/ProcessStatisticsBin.cpp` 不修改临时 score。这里只确认串行现有时序，不是新 accumulator 的动态验证。 |
| Stage 2 兼容与源适配 | 保留未绑定旧点源路径、canonical F/A 及深值工作副本的意图明确；W14 的物理 MeV/内部群号速度适配需限制在 Stage3-bound F/A。 | `RMC/src/SampleParticle.cpp` 与 `RMC/src/GlobeFun.h` 支持该坐标风险判断。不能由静态审查声称低能路径已动态复现或修复；普通路径不应被本设计默默扩展。 |
| MPI 与测试范围 | 当前测试计划只明确 serial 构建；必须把生产运行时拒绝或完整 MPI 合同写成可审查的具体设计。 | `RMC/src/GatherTally.cpp` 的现有路径没有覆盖新 TARGET scalar accumulator；新增设计须明确 global N、S1/S2 与 receipt 语义。 |

## 4. 最小修订要求

1. 对 MPI 选择并写明唯一合同：
   - 首版在 MLVR/TARGET 的生产运行入口明确拒绝 MPI，并指定拒绝发生在任何运行状态变更之前；或
   - 设计完整的 TARGET scalar 归约、global completed/N、S1/S2 数值累计语义及 receipt 一致性，并增加 MPI 验收。
2. 将 T4 改成可复现门禁：提供真实可运行的只读 GDB observer/脚本、原始记录 schema、history/后代关联与覆盖检查；或在获批文件清单中加入最小 test-only observer，并定义其不改输运行为的证明。若无法提供独立 raw-segment oracle，应收窄测试计划的独立性主张并给出替代的独立参考，不能把被测转换结果当 oracle。
3. 在实施前对现有 type-4 bin sampler 增加真实生产调用的端点、区间支持域及均匀性 micro-oracle；不要仅因方法名或输入区间推断分布正确。

修订不应放宽单位初始权重、完整 history 统计、零得分计 N、独立物理参考或 Stage 2 未绑定点源回归要求；也不能通过扩大容差或改 reference 消除失败。

## 5. 证据等级与范围边界

- **SOURCE VERIFIED（E1）**：本审查直接依据 RMC 冻结源码检查串行 history/bank-drain、score 清理时序、既有源采样与 MG 速度调用链。
- **DESIGN REVIEWED（E1）**：TARGET、源构造、响应统计、接口/所有权和拟测门禁按方案核对；发现上述两项 P1 与一项 P2。
- **NOT RUN**：没有编译、CTest、源抽样、输运、统计复算、GDB 观测或 sanitizer；T1–T6 全部仍是计划。
- **不外推**：不判定设计提案之外的 RMC 行为，不证明绝对伴随重要性或完整输运互易性，不扩大到 MPI/OMP/AIS/Python、任意源、非零裂变或复杂几何能力。

**最终分类：NEEDS REVISION。** 设计作者的 “READY FOR INDEPENDENT DESIGN REVIEW” 是送审状态，不等于本次独立审查接受，也不构成生产修改批准。修订与实施均须遵循原任务中的用户审批边界。
