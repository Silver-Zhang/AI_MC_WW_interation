# F11 Persistent Session Minimal Experiments E0–E4

2026-09-29 · RMC `5cfb0f771d0c5a2127c90d57e51ce672a4e3b616` · **STOP: proposed source patch awaits approval**

本报告记录本次准备工作与执行阻塞，不是已完成的动态实验报告。**RMC runs = 0，fresh-process oracle runs = 0；E0–E4 均为 BLOCKED。** 没有性能数字或数值比较结果。

## 1. Scope

standard MGACE、中子固定源、Cartesian Type=1 track-length mesh tally、Energy=-1、Normalize=1、native track-mesh WW、Linux、MPI/OpenMP OFF。采用 F07 H2O 箱体几何，派生为两空间 bin、30 中子群；派生算例尚未 fresh-run 验证。[完整协议](logs/experiment-plan-frozen.md) §1–§3 记录 source/N/seed/WW、数据来源及非目标。

参考：[Codex 独立审查](../20260929_09_f11-rmc-runtime-architecture-audit-codex/RMC_Runtime_Architecture_Audit_Codex.md)、[Claude 独立审查](../20260929_10_f11-rmc-persistent-execution-audit-claude/Independent_RMC_Persistent_Execution_Audit_Claude.md)。本次抽查同一 RMC 基线；既有审查结论不充当新实验结果。

## 2. Frozen acceptance criteria

判据在运行前固定于 [protocol v1](logs/experiment-plan-frozen.md)，与源码改动批准分开：

- 同一串行 binary、对应 N/source/seed/WW/tally/normalization 的 fresh oracle；E1–E4 每一轮均需对照。
- history count、RNG identity、Score/ScoreTemp/Sum1/Sum2/Ave/RE、bank 状态、starting-weight denominator 做 exact comparison；全 2×30 群及 Tot 分开核对。
- registry 不增长，指针指向同一 owner 内相应数据；进程内确认对象 identity，跨进程比内容，不比地址。
- E2 三层 role、物理 cutoff/内部群表示、adjoint/fission 数组与 particle cache 必须对应 fresh；先声明 CLEAR/REBUILD 合同，失败停止定位。
- E3 实际 transport lookup 事件必须显示 WW2 及其派生 bounds；E4 reset 全零、第二场可区分、memory/text 按输出精度一致、G+1 物理边界成立。
- E0 F/A 各 warmup 1 次 + 正式 7 次，warm filesystem cache，mean/sample std；计时闭合、波动与 observer 开销门见协议 §5。

PASS/FAIL 仅在实际执行后评定；覆盖或计时质量不足为 INCONCLUSIVE；当前未获源码实验改动批准为 BLOCKED。不会运行后放宽判据。

## 3. E0 performance

**BLOCKED — 未运行。** `FixedSource` timer 包含初始化及结尾处理（`CalcFixedSource.cpp:73–80,719–749`），现有 Tally timer 包含输运中的计分，不能直接构成所需非重叠阶段。所选方案需要 test-only timing hooks，触发任务第7节停止规则。

| 量 | Forward mean/std | Adjoint mean/std | 拟用口径 |
|---|---|---|---|
| T_process | 未测 | 未测 | parent launch→main.enter，含 loader/static init |
| T_input | 未测 | 未测 | ReadInputBlocks，合并 input 内几何检查 |
| T_geometry/material | 未测 | 未测 | model inclusive 减 XS/adjoint/material output |
| T_xs | 未测 | 未测 | ReadAceData，含 MG 数据准备 |
| T_adjoint_prepare | N/A（该路径未调用） | 未测 | treatAdjointMaterial |
| T_transport_prepare | 未测 | 未测 | loop 前初始化，排除完整 model 子区间 |
| T_transport | 未测 | 未测 | 原 neutron history/batch loop |
| T_tally_finalize | 未测 | 未测 | FinalizeLoadBalanceChecker + ProcessTally |
| T_output | 未测 | 未测 | 显式 output probes；早期零散 I/O 在 startup glue 中 |
| T_total | 未测 | 未测 | parent launch→wait |
| startup/init fraction | 未测 | 未测 | 每次启动阶段/总耗时，再算均值和 std |

`T_total = T_startup/init + T_transport + T_finalize/output` 为待测总账；早期 material output 属于启动子项，不能再次相加。当前没有启动占比或 persistent 加速预估。[E0 记录](verification/E0/README.md)。

## 4. E1 Forward→Forward

**BLOCKED — 未运行。** 计划 F1(N=2000,S=11001)→F2(N=3000,S=11003)，同一模型只初始化一次，每轮对应 fresh。

入口阻塞：`CalcFixedSource.cpp:78` 无条件 `InitiateAll`，后者重进 model/XS 和 tally 初始化。原样调用两次不满足目标；复制 history loop 也不能证明原入口的复用。拟议 P1 只提供受控 init gate，字段 reset 留在任务 driver 并显式记录。

需重置 finish/completed/source counts、banks/descendants、starting weights、RNG position/cache、particle caches、六组 tally 数组及索引、timer/diagnostics/output。`InitiateTrspt` 当前只处理其中一部分；不能把“再次调用 init”当作已验证 reset。[E1 记录](verification/E1/README.md)、协议 §6。

## 5. E2 Forward→Adjoint→Forward

**BLOCKED — 未运行。** N 均为3000，seed=12001/12003/12005；三轮分别对应 fresh。

| 静态关注点 | 当前证据 | 计划观察；没有动态污染结论 |
|---|---|---|
| role 单向传播 | `InitiateAll.cpp:130` 只在 true 时设置 AceData | FixedSource/AceData/Particle 三层 flag，每次切换前后 |
| cutoff 量纲变化 | `InitiateAll.cpp:192–203` 原地 MeV→group | 独立保存30 MeV；逐次记录内部群号 |
| adjoint 累加 | `TreatAdjointMaterial.cpp:22–56` resize 后 += | 从零 rebuild 前后、fission 与 scattering 数组 |
| particle cache | `CalcFixedSource.cpp:81–82` resize 同尺寸不保证重置 | 显式重建后对照 fresh 内容/dirty 状态 |

预声明 test-only CLEAR/REBUILD 合同见协议 §7。若第三个 F 不同，先保存 first divergence 并区分 CLEAR/REBUILD/immutable-base 问题，不立即修复。即使合同下 PASS，也不声称未经该准备的当前默认入口能自然切换。

H2O 非裂变材料只能检查 fission-adjoint 容器的预期零态，不能证明有非零裂变项时的重建正确；本实验边界保留。[E2 记录](verification/E2/README.md)。

## 6. E3 WW hot update

**BLOCKED — 未运行。** 固定两空间 bin、30 群与 WUP/WSURV/MXSPLN；WW2 全部 lower 为 WW1 的1/4，upper=5×lower、survival=3×lower。两轮 seed=13001/13003，N=3000。

静态可见 `ProcessWeightWindow` 派生三种 bounds；实际 track loop 经 `DoMeshWeightWindow.cpp:42` 调用 `setMeshWeightWindowBound`，局部 ergPos 和读取结果在 `WeightWindows.cpp:45–69`。提案 P0 在此记录粒子状态和实际选中 bin/bounds，P1 支持第二轮原 loop。

需要 both selected spatial bins 的真实查窗覆盖及 fresh WW2 完整事件摘要对照；只更新数组、手动 lookup、最终 FOM 均不足以 PASS。[E3 记录](verification/E3/README.md)。

## 7. E4 tally reset / memory extraction

**BLOCKED — 未运行。** Run1 (x=5,N=1500,S=14001)→Run2 (x=15,N=3500,S=14003)，SCHECK/CHECK 开启，tally 定义和 owner 保留。

- `TallyData.cpp:17` 的 SetZero 清六组数值，不清 touched/index sets 或统计 tester。还需核查 `SetStatisticsIndex.cpp:29–43` 的索引追加和 `InitiateTally.cpp:69` 的 registry 登记，避免每轮重复。
- 候选读取点：`CalcFixedSource.cpp:721` ProcessTally 返回后、OutputSummary 前。`OutputTally.cpp:247–248` 读取 mesh Ave/Re 数组；需要实际内存 vs `.Tally` token 校验才能确认本实验提取结果。
- G+1 候选来源：MGACE centre/width/lower；`CheckMgAceBlock.cpp:38–61` 与 `GetMgCs.cpp:231–272` 提供映射/最高上界计算线索。计划提取31个物理升序 MeV 边界，验证连续性、跨核素一致性和 Tally 行映射；尚未提取。

本次没有 Field 数组文件、G+1 数值文件或正式 F10 API。`.Tally` 的每群下界、WW 的0/∞哨兵都不能单独代替完整物理边界。[E4 记录](verification/E4/README.md)。

## 8. Fresh-process oracle comparison

| 实验 | 计划独立 fresh cases | 完成 fresh runs | 完成 same-process sequences | comparison |
|---|---|---:|---:|---|
| E1 | F1、F2 | 0 | 0 | 未比较 |
| E2 | F1、A、F2 | 0 | 0 | 未比较 |
| E3 | WW1、WW2 | 0 | 0 | 未比较 |
| E4 | source1、source2 | 0 | 0 | 未比较 |

E0 warmup/measured/overhead 对照也均未执行。旧目录的 outputs 和曾存在的 `/tmp` binary 不计入本次 oracle。批准后须固定编译器/flags/dependencies、binary、完整输入、数据库哈希、运行命令、stdout/stderr/exit code，再运行；当前 absence 用 null/空列表记录，不以0表示未测耗时。

## 9. Confirmed reusable states

**动态确认可复用的状态：无。** 下列仅是源码识别的候选复用对象：

| 候选 | 所需实验限制 |
|---|---|
| geometry/material/nuclide raw MGACE | identity + immutable payload 保持；ReadInputBlocks/ReadAceData 各一次 |
| tally mesh/group/offset definition | 同一 owner，registry/index 不重复登记 |
| WW mesh/energy/parameter definition | 定义不变，仅 lower 与派生 bounds 改变 |

具体内容/地址不变量由 snapshots 验证后才能升格为本模型范围内的动态结论。静态结构存在不等于其完整生命周期安全。

## 10. Confirmed per-run states

**源码确认会在单次运行中写入的状态类别**（尚未动态证明 reset 完整）：

| 类别 | 样例 / 证据 |
|---|---|
| calculation progress、bank、denominator | FixedSource 构造初值；InitialBatchSource 的结束标志和 starting-weight 更新；CalcFixedSource history/bank loop |
| RNG current state 和函数 static cache | `RNG/StrideRNG.cpp:85–102` |
| score/moments/Ave/RE/touched indices | `TallyData.cpp:17–101` |
| statistical checker 历史数据 | `SetStatisticsIndex.cpp`、`StatisticsFunc.cpp` |
| role/cutoff/particle derived cache | §5 四类源码位置 |
| timing/diagnostics/output | `CalcFixedSource.cpp` 开始/结束及 OutputSummary |

“confirmed per-run”在此只指静态写路径；它不表示拟议 driver 已穷尽所有状态或被验证正确。

## 11. Confirmed blockers

1. **B0：E0 时间边界缺少批准的 probes。** 现有粗粒度 timer 不能直接分离本任务要求的 init/transport/finalize。
2. **B1：E1–E4 缺少批准的 prepared-state 原 loop 入口。** 当前 CalcFixedSource 每次全初始化；需要显式 P1 gate。
3. **B2：E3 真实局部查窗、E4 finalization snapshot 尚无本次采集链。** P0 提供位置，callbacks/driver 尚未实现。

这些是当前实验执行阻塞；§5 的单向 flag、cutoff、+=、cache 是待实测风险，**没有把它们写成已经发生的运行 FAIL**。[补丁提案](Proposed_Experimental_Patch.md) 包含 Why required、8个文件/函数、Expected evidence、Risk 和审批范围。

## 12. Remaining unknowns

- 启动/读库/输运占比及 observer 开销；E0 warm-cache 条件外不外推。
- 每轮完整 reset 是否足够、RNG static fast path 是否正确重新定位。
- F→A→F 在预声明合同下是否 exact equivalent；无非零裂变项覆盖。
- WW2 在指定空间×能群 bin 的实际运输覆盖及 fresh 一致性。
- SCHECK/tally registry 完整清理、内存/文本对应、真实 G+1 数值。
- 提案尚未编译/链接；8文件 patch 之外是否还需源码改动未验证，如需要则另报审批。

静态自检只支持“提案对应当前源码、未应用、无共享文件变动”，不消除上述未知项。

## 13. Implications for F11 design

当前可以确定实验需要显式声明模型寿命与每轮准备步骤，并对真实输运路径取证。尚无动态结果支持选定全外耦合、hybrid、persistent RMC 或 fully internal，也没有加速收益估计。未编写 Session/Controller/Field API/WW Builder/Reconstruction/ResponseDefinition/convergence/best-FOM/MPI persistent 实现。

## 14. What the human needs to decide

请审阅 [Proposed Experimental Patch](Proposed_Experimental_Patch.md)：是否批准在**本任务目录内私有 RMC 源码快照**上应用 P0 观测插桩和 P1 初始化 gate，并实现任务内 driver，按固定判据继续 E0–E4。

审批是用户任务第4、7、16节明确要求的停止关口。共享 RMC 保持原状；实验失败先定位，不追加修复。该决定仅允许实验继续，架构选择留待用户基于结果另行决定。
