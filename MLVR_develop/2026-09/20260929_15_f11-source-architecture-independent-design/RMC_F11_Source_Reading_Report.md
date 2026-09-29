# RMC F11 Source Reading Report

2026-09-29 · Task 15 · 模式 C · **源码阅读完成，尚未实现**

## 导航与证据口径

A 生命周期；B 输入；C 固定源；D F/A；E source；F tally/Field；G WW；H 输出/外部进程；I 状态与动态证据；J 源码结论。

先形成本文及调用图、状态表，再形成独立设计文档。源码基线是 RMC `5cfb0f771d0c5a2127c90d57e51ce672a4e3b616`，根仓库 `daf91d604ed4b6d14fd418ac50ae464f4f0de229`。工作树快照见 `logs/repository-state.txt`。`RMC/src/...:a-b` 指本次读取的源码行号；“推导”与“已有行为”分别标明。本轮未编译、未运行 transport，也未复核整个物理内核。

## A. Program lifecycle

### A1. 谁创建、谁实际参与计算

`main.cpp:27-55` 定义进程级 Output、OMeshInfo、OXSParaTableVec、OWeightWindow、OStatus、OTimer、cellVec、OParticleTracker、OController、ORNG、OCalMode 与日志对象。`main.cpp:57-88` 又创建 main 局部 Input、Geometry、Material、AceData、Criticality、Burnup、Tally、Convergence、ParticleState、FixedSource、ExternalSource、各粒子 transport、Sampling 等。局部 `CDRNG ORNG`（60）遮蔽同名 global（37）；审查和 reset 必须跟踪实际传入引用，不能凭名字修改 global。

这些 main 局部对象通常存在到 main 返回，但 **main lifetime 不等于计算所用 owner lifetime**：

| RunCalculation 参数方式 | 实际对象 |
|---|---|
| 按值 | CDNeutronTransport、CDGeometry、CDCriticality、CDMaterial、CDParticleState、CDConvergence、CDTally、CDBurnup、CDSampling |
| 按引用 | CDCalMode、CDPhotonTransport、CDElectronTransport、CDAceData、Depth_Class、CDFixedSource、CDRNG、ME_Class、TTA_Class、CDAdjoint、CDExternalSource、CDKinetics、CDPerturbation |

依据：`RMC/src/RunCalculation.cpp:6-13`，声明一致于 `RMC/src/CalMode.h:152-158`。因此 repeated half-run 若置于一次 RunCalculation 内，其局部 Geometry/Material/Tally 等可以保留；反复调用 RunCalculation 则产生新的值参数，不能假定复用同一初始化后的 tally owner。Tally 内部注册的是对象成员地址，初始化后再复制尤其需要避免。

### A2. 当前调用顺序

`main.cpp:123-162`：CheckIOFile → logger/output heading → ReadInputBlocks → RunPlot → GenerateInpFile → OCalMode.RunCalculation → OutputEnding。RunCalculation 先 Sampling.InitialBeforeCalculation，再 switch；固定源分支直接 CalcFixedSource（`RunCalculation.cpp:14-24`、`RunCalculation.cpp:83-89`）。完整现有调用图见 [source-call-graph](logs/source-call-graph.md)。

**可保留的对象（推导）**：已初始化且地址稳定的几何、材料、raw MGACE、tally definition/registry、source definition、mesh/group/WWP topology。它们的派生伴随 XS、score、particle working state、source sampling state、run RNG/counters不能一并视为只读。

## B. Input architecture

`Input.h:46-72` 的 CDInput 保存 BlockDefined；`ReadInputBlocks.cpp:30-49` 读顶层关键字并转大写、检查重复。FIXEDSOURCE 直接设 CalMode.FixedSourceMode 并填 CDFixedSource/transport/RNG（134–140）；结束统一 CheckInpBlock（377–381）。新增 block 自然接在这层，并在 CDInput 声明 parser，采用已有 ReadCardOptions/CheckInputParas 风格；跨 block 冲突要在读完整张卡后判定，避免依赖输入顺序。

`ReadFixedSourceBlock.cpp:33-62` 管 population/fission，77–115 管 cutoff，117–160 管 RNG；209–235 管 ADJOINT，其中 ADJOINTCALCULATION 只在值=1时置 true，MAXADJOINTENERGY 的输入是 MeV。它不表示一次迭代调度。`ReadTallyBlock.cpp` 向 CDTally 建 definition，mesh parser 的 scope/bounds/energy/normalize 属 `ReadMeshTallyCard.cpp:31-85`、258–339；WeightWindow parser 填 global OWeightWindow（详见 G）。

配置候选的源码依据：

- **CDFixedSource** 已拥有 population、finish、adjoint flag、source-bank 等固定源配置/执行状态；适合持有一个具名配置值，但不意味着它必须负责进程启动/HDF5。
- **CDCalMode** 已拥有模式和运行分发；适合调度入口，不能仅因它调度就把所有 TARGET/tally 细节塞进去。
- **CDInput** 是 parser/BlockDefined 的 owner，不是重复运行状态 owner。
- **RMC::Control** 当前是 hash 与几何容差/深度控制（`Control/Control.h:18-67`），`ReadControlBlock.cpp:7-43` 只读 HASH；名字“Control”不能作为挂 iteration 的依据。

`GenerateInputFile.cpp:37-48` 是可选格式化输出，检索其 body 找到 CRITICALITY/TALLY/PRINT 等输出，没有完整 FIXEDSOURCE/EXTERNALSOURCE 重建段；CDFixedSource 虽在形参中，不代表已有可用固定源 round trip。因此新增 MLVR 时必须明确：补齐可再运行的格式化输出，或首版拒绝 MLVR 与格式化输入输出的组合并归档原卡/解析后的配置。只加一段 MLVR 文本不能宣称整个 `.FMTinp` 可复现。

## C. Fixed-source lifecycle

### C1. 初始化、batch、history 与 descendants

`CalcFixedSource.cpp:67-72` 接收主要 owner 引用，但 **CDExternalSource 又按值**，其抽样状态在这次调用内变动。

| 当前区间 | 作用 | repeated run 的约束 |
|---|---|---|
| `CalcFixedSource.cpp:73-95` | 注册/启动 timer；InitiateAll；particle cache 尺寸；其他粒子 XS | 含 full init，不可每 half-run 原样调用 |
| `CalcFixedSource.cpp:97-104` | last_t、TotalCount、load-balance 初值 | 每 run 的局部变量 |
| `CalcFixedSource.cpp:106-209` | neutron batch/history/descendant loop | transport 算法应保留一份 |
| `CalcFixedSource.cpp:210-717` | 其他粒子分支 | F11 不启用，也不能破坏普通运行 |
| `CalcFixedSource.cpp:719-749` | load-balance finalize、ProcessTally、可选模块/output、timer stop | 区分 run finalize 与 process/module ending |

Neutron：107 push bank sentinel；108 while finish<2；109 DistributeSource；113 history loop；119 GetRandSeed；131–132 SampleFixSource；167–185 transport 并排空后代 bank；197–203 每个 source history 一次 SumUpTally；207–208 PrcoessBatchEnd。后代粒子不另作为独立 MC observation。

`InitiateAll.cpp:125-209` 混合 raw material/ACE 初始化（130–131）、tally definition 建立（156）、binary restart、particle geometry arrays、per-history mode（171–172）、material fractions（176）、WWG/MCNP、cutoff 与 Python。`InitiateMatAce.cpp:18-28` 读原始 ACE，56–67 同时可能生成 adjoint material。不能把整个 InitiateAll 当轻量 run reset。

`InitiateTrspt.cpp:60-100` 只初始化部分 counter/denominator/bank；`ResetTrspt.cpp:24-31` 的固定源 reset 是注释代码，活跃版本属于 Criticality。当前源码没有可直接调用、已完整覆盖 Task 13 契约的固定源 repeated-run API。

### C2. Batch 与总 histories

`InitialBatchSource.cpp:7-38` 按 input/time interval 分配 source 并增加 batch；94–144 更新累计 histories、剩余量、restart boundary 等。`CheckTransport.cpp:51-72` 从本次 N/restart/stop time 得到初始 interval。在 serial、固定 N、无 restart/stop-time/time-reduce 的首版配置里，通常一次 run 就一个 existing batch；batch 机制仍要保留，不能把 k 当 batch number。

层级是 **iteration > half-run > existing fixed-source batch > source history > descendants**。StatisticsTester 的 `p_nBatch=20`（`StatisticsTester.h:31-31`）是统计诊断分组，不是 20 次 transport runs。

finish 的字段说明见 `FixedSource.h:408-423`；实际 `PrcoessBatchEnd` 在 bCalculationEnd 时设 5（`InitialBatchSource.cpp:335-337`），包括 N 已完成，不能只按字段注释将 5 理解成时间终止。

### C3. Denominator 实际行为

ordinary source 在 batch end 直接 `p_dTotStartWgt=p_llCurTotParNum`（`InitialBatchSource.cpp:295-298`）；surface source 另算（299–305），spontaneous multiplicity 还能修正（313–322）。`ProcessTally.cpp:364-393` 将此量作为 CalcAveRe 的 dM；`TallyData.cpp:83-99` 同时把 dM 当 observation count 用于 RE。

**结论**：当前 ordinary path 没有一般意义上逐 source history 累加实际 starting weight 的实现。等初始权重1、无 source bias、无自发裂变源时，完成 histories、总起始权重和归一化分母才一致。任意源权重不是改 metadata 名称即可支持；否则均值分母和 RE 的 N 也需要拆开。F11 首版需要显式约束、运行检查和记录真实 denominator。

## D. Forward ↔ Adjoint switching

### D1. 不是一个 flag

`InitiateAll.cpp:130-131` 在 FixedSource adjoint 时将 AceData flag 置 true；`SampleNeutronSource.cpp:222-223`、304–305 同样只向 particle 置 true。这些原始路径缺少反向赋 false 的契约。F→A→F 的准备必须显式设置 **FixedSource、AceData、ParticleState 三层**，并处理所有由其决定的缓存与 cutoff。

`TreatAdjointMaterial.cpp:19-60` resize adjoint vectors 后以 `+=` 汇总，包含 fission 与 scattering；resize 相同大小不会清零。每次重建 A 前必须先清空两组 derived arrays，F 则显式清除不使用的 derived data。raw XSS/JXS 保留，不能每次再做材料密度/索引转换。

`InitiateAll.cpp:192-203` 将物理 MeV cutoff **就地改成内部群号**；`GetExitState.cpp:191-195` 按反向群号比较。物理定义必须单独保留，每次切换从它解析出 runtime cutoff，禁止“群号再作为 MeV 输入”。

### D2. 真正使用 mode 的 transport 路径

- `SampleFreeFlyDist.cpp:56-96` 计算普通 macro XS，并在 adjoint 粒子情况下重算材料的 adjointAccumulatedCrossSection；这里不能概括成“用 adjoint total 直接替换自由程 total”。
- `SampleColliNuc.cpp:25-47` 用上述向量及核素 adjoint XS 抽样核素。
- `SampleColliType.cpp:157-197` 区分 adjoint scattering/fission，读 derived fission XS，并写 p_dTempAdjointxSection、修正 weight。
- `TreatImpliCapt.cpp:6-12` 在 MG adjoint 下跳过 implicit capture。
- `GetExitState.cpp:162-198` 抽样 adjoint exit，权重修正、伴随高能截止、裂变 descendants；F 使用另一分支（199–215）。

因此 ParticleState 的 group/material/nucleus/XS/backup 与 adjoint temporary cache 不能残留上轮值。`ParticleState.h:395-436`、529–534 提供构造默认值依据；生产 helper 必须重建 geometry-sized arrays/material fractions/核素 cache 后再 transport，不能仅清一个 role flag。

### D3. 动态证据边界

Task 13 reset contract 和 Task 14 独立复核支持 H2O standard MGACE 30g、serial 下 repeated preparation 可行。Task 14 对 E2 保留限制：nonzero adjoint fission rebuild 没有动态覆盖。源码确有 fission accumulation，因此不能从 H2O 两次 A 匹配推断裂变材料也正确。详见 [完整状态表](logs/source-state-ownership.md)。

## E. External source architecture

### E1. 现有表示足以承载简单 TARGET

`ExternalSource.h` 的源/分布向量与 CDIndex 是 definition owner；`ExternalSource.cpp:15-43` 添加源并归一化 fraction/bias，46–57 按 bias 选择源、用 fraction/bias 修正初始 weight。不是只能一个源：循环支持多 component；`CheckSourceAndDistri.cpp:21-29` 那条“size=1”注释不能凌驾代码。

`SourceDistribution.h:30-36` 已有 discrete=1、bin=4；`SetTypeAndValues.cpp:6-34` 建立并归一化概率；`SampleValue.cpp:25-45` 用 probability/bias 修正权重、返回离散值或区间均匀值。`Source.h:124-144` 提供参数检查、分布映射/绑定接口，`ReadExternalSourceBlock.cpp:30-66` 给出源与分布的注册顺序。

一个空间 bin 可用 CDSource 的 X/Y/Z 三个单区间 bin 分布；能量用 physical group center 的离散分布；每个选中 spatial bin 一个 component，component probability 携带体积因素。`CheckAndInitiateParameters.cpp:19-26`、65–72 接受 XYZ；`SampleVariableFromDistri.cpp:6-30`、102–103 取空间/能量；`SampleStartDirection.cpp:70-76` 默认各向同性。**不需新 source type，也不需将群号暴露给外部**。`SampleNeutronSource.cpp:267-278` 会把物理能量转内部群号。

### E2. 物理条件与需要的验证

若响应定义为 R=Σ a_ig φ_ig，φ 为 bin 体积平均的群积分通量，则 source density 与 a_ig/V_i 成正比；对整个 bin 抽样的质量是 density×V_i。不能把“每个 bin 等概率”当成所有 TARGET 的通用规则。群积分 tally 与当前离散 MG 转置不自动要求再乘 ΔE；明确响应定义后才能确定概率。

fraction=bias、distribution probability=bias、Source.Weight=1 时，每个 starting history 自然为1（`ExternalSource.cpp:25-57`，`SampleParticle.cpp:24-29`）。多 component 等权可由现有机制表示，但 Task 13 的单源例没有动态证明新 builder 正确，仍需单独验证。

`SampleParticle.cpp:57-74` 没指定 CELL 时接受 XYZ 样点，后续 SampleFixSource 才定位几何并可能 kill（`SampleNeutronSource.cpp:233-258`）。TARGET 应指有效计算域中的完整 mesh volumes；不能靠有损拒绝抽样悄悄把全 bin 概率改成材料交集概率。失效位置应使 MLVR run 失败，而非将不一致结果送给外部。

## F. Tally / Field architecture

### F1. 结果的真实 owner 与导出时机

`Tally.h:1025-1030`：definitions 在 p_vMeshTally，数据在 **CDTally::p_OMeshTallyData**。`InitiateTally.cpp:61-69` 初始化/扩容并将其地址加入 registry，232 调 SetStatisticsIndex。重复执行这段不是 reset，会再次注册。

`SingleTally.cpp:875-898` 将 Energy=-1 换为 MG 的 G 个 lower edges；每 spatial bin 存 G 个 group 加1个 Tot。数据定位必须用 GetMeshErgPtr，不能将 Tot 当第 G+1 群。`ScoreMeshTally.cpp:85-119` 向 owner score 加分；`SumUpTally.cpp:130-132` 在 source history 结束时积累；`TallyData.cpp:43-51` 用该 history 的总 score 求平方，再清 transient score。**多个 descendants 的相关性已在 history 内保留。**

导出应在本次 `ProcessTally` 后、下一次 reset 前：此时 Ave/RE 已完成，尚未经过 text 取舍/打印精度。若 TARGET 涉及多个 bins，response 的 RE 不能由各 bin RE 独立平方合成；需要在 SumUpTally 清除 score 前合成一次 response history score，再积累其平方。

### F2. 体积归一化的源码差异（本次新增发现，未做动态验证）

Type=flux 返回传入 flux 本身（`TallyType.cpp:46-48`）。TL scorer 分别调用 uniform CalcMeshTrck 与 heterogeneous CalcHeterMeshTrck（`ScoreMeshTally.cpp:39-45`），之后直接 weight×track length（61–85）。

- uniform Cartesian：`MeshFun.cpp:270-392` 返回原始 track length（300、346、383），没有读 p_bUseVol。
- heterogeneous Cartesian：`MeshFun.cpp:474-484`、540–545、611–616 在 p_bUseVol 时除 bin volume。
- parser 确实为两类保存 Normalize（`ReadMeshTallyCard.cpp:258-294`）。
- `ProcessTally.cpp:364-393` 只除 source denominator；text output 直接打印数组（`SingleTally.cpp:978-1000`）。

所以从这一条已读调用链推导：**uniform TL 的 Ave 不因 Normalize=1 自动成为体积平均值**。第一版 Field adapter 若两类均支持，必须明确 per-bin conversion：已除体积路径系数1，其余系数1/V_i；RE 不变。不能统一再除一次体积，也不能一律直接取 Ave。这是需用非单位体积、等几何两种 mesh 表示交叉验证的具体风险；本任务按用户限制不修源码、不更新 KB。

### F3. HDF5 与 full axes

`MeshTallyHDF5.cpp:40-99` 可借鉴完整空间边界的展开，但其三维 value 输出不承载完整 group/RE/status 契约；另一个 `OutputTallyh5.cpp:52-83` **已有 Mean/Re**，按 flattened bin 写 Result，并非“现有 HDF5 全部没有 RE”。两者都不是 F10 的带身份、归一化与全轴的 StatisticalField 文件。

`CheckMgAceBlock.cpp:38-60` 从 standard MGACE 中心和宽度求 lower，并反向存成物理升序；最高 upper 可由最高中心+半宽得到。`GetMgCs.cpp:263-278` 的群定位也用 2×center−lower 作为最高 upper。完整 G+1 必须回到 ACE 定义，并校验连续、有限、严格递增、所有核素的 full structure 一致；现有一致性检查主要比 lower，不可当完整 upper/center 已验证。

`.Tally` 只打印每群 lower（`SingleTally.cpp:978-989`），没有最高 upper，单独无法恢复完整 G+1。F11 在内存可直接读 ACE，不需猜 sidecar。空间轴从当前 CDMesh 的 uniform min/delta/count 或 heter coarse bounds/subdivision 展开（`MeshTallyHDF5.cpp:47-79`）。

status 最自然在专用输出 adapter 校验实际数值后生成：finite Ave>0 且 RE≥0 → VALID；Ave=0,RE=0 → ZERO_SCORE；负值、nonfinite、负 RE、zero+nonzero RE → error。ZERO_SCORE 表示未计到分，不能解释为真实通量确定等于0。

## G. Weight Window architecture

动态输运读 **OWeightWindow::p_vMeshInformation[particle][mesh][energy]** 的 lower/survival/upper（`WeightWindows.cpp:45-66`）。`WeightWindow.h:147-160` 的 legacy flat 参数数组与 mesh 不是唯一 runtime 真值。空间拓扑在 p_OWeightWindowMesh、能量在 p_vEnergyBins；native GetWeightWindowEnergy 将粒子内部群号转物理能量（`WeightWindows.cpp:72-77`）。

`ProcessWeightWindow`（`WeightWindows.cpp:79-101`）核对 flat lower 个数=space×groups 并生成 lower、WUPN×lower、WSURVN×lower。它未完整校验 finite/strict-positive/product overflow，因此 `ww.h5` 的 importer 必须先全面检查，再一次更新。只改旧 flat lower 不保证输运读到新 WW。

`ReadWeightWindow.cpp:277-287` 读 WWP:N，验证 WUPN>WSURVN>1；329–341 打开 neutron track mesh WW/改变 cutoff；419–427 为文本输入拼接 energy sentinel 并调用 ProcessWeightWindow。重复读 parser 会触碰 flags、cell vectors、sentinel，不宜用于动态文件更新。直接更新当前对象最短，也更容易锁定 topology。

`DoMeshWeightWindow.cpp:21-50` 对 mesh track 执行 lookup、splitting/roulette、tally，再按 track length 移动粒子。**从 tally 复用 mesh 几何时不能把 Normalize=1 的 flag 一同当作 WW track 设置**，应保证 WW `p_bUseVol=false`；输运移动要用真实长度。

静态 WWMESH、WWN/WWE、WWG、MCNP WW 与动态 MLVR 的 neutron lower 若同时生效，所有权不唯一。首版应输入期拒绝这种组合，仅复用 WWP 参数；动态角色与数值由 run 调度选择，不能靠输入顺序覆盖。

## H. Output / external executable

`CheckIOFile.cpp:141-169` 以 input basename 建 Result/Information/State HDF5；`OpenFilePtrs.cpp:72-109` 打开 material/Tally 为 w。`OutputSummary.cpp:184-207` 固定源结尾输出 tally 与 `OutputTallyh5(Final,0,0,0)`；若机械重复调用会复用同名结果路径。`SingleTally.cpp:993-995` 的 Tot 甚至使用 global p_fpTallyFilePtr，不能只换传入 FILE* 就认为已全部隔离。

`OutputEnding.cpp:46-83` 停 total timer、输出全局 summary、CloseFilePtrs；`CloseFilePtrs.cpp:27-74` 关闭很多全局 FILE* 而非 per-run session boundary。生产半轮不能借用整进程收尾或反复改 p_chInputFileName 来复用 CheckIOFile。

已有 HDF5 基础是 `RMC/include/rmc/file/hdf5/HDF5.hpp:62-128`、173–195、273–287：HighFive wrapper，ReadData/WriteData、属性、exist。`HDF5_misc.hpp:33-49` 已有节点覆盖与读取，没有 MLVR 类型/维度/身份规则；raw ReadData 会 resize。新文件需要在读取大数组前检查 shape/type/size，必要时对 wrapper 加通用 dataset info 查询。文件对象保持局部唯一 owner，Flush 后析构结束再启动外部；不能复制持有 raw pointer 的 wrapper，也不应假定显式 Close 后再析构的行为已验证。

源码检索 `system/popen/fork/execv/posix_spawn/waitpid` 仅发现 `OutputMXSFile.cpp:19-32` 用 system 执行 mkdir，未检查 exit code；这不构成可复用的可靠 external executable 机制。FileIO 是文本 parser（`FileIO.h:16-86`），PythonInterface 的源回调也不是本需求的 reconstruction 文件握手。

串行 error path：`PrintFile.cpp:6-58` 的 _ERROR 终止进程；`Output.h:183-226` 提供现有检查/报错入口。外部调用应在一次 half-run 已完成/文件已关闭之后、下一 run 准备之前；启动失败、非零退出/信号、缺失/损坏文件、身份不匹配都在同一调度层 fail-fast。不要把启动程序放入 history、tally scorer 或 WWP parser。

## I. 状态表与动态证据

完整表见 [source-state-ownership.md](logs/source-state-ownership.md)，覆盖 geometry/raw ACE、derived XS、三个 role flag、cutoff、所有 tally arrays/registry/statistics、source definitions/working states、banks/counters/finish/denominator、ParticleState、RNG、WW、timer/output。

参考：Task 13 `logs/run-reset-contract.md`；Task 14 `Independent_F11_E0_E4_Dynamic_Review.md` 的 E0–E4、normalization 与结论节。E1/E3/E4 接受；E0/E2/归一化带 H2O30g、单位单源、Linux serial 边界。E0 startup fraction 不是 persistent production speedup；本报告不承诺性能提升比例。历史 test driver 是状态证据，不是可直接并入 RMC 的架构。

## J. 阅读阶段结论与边界

1. 当前源码支持“同一组实际 owner 内重复 fixed-source run”的方向，但需要正式 owner reset/prepare；无现成 session API。
2. CalcFixedSource 将 full init、唯一 transport loop、finalization 放在一起；外面简单循环调用会重复初始化 tally/material 等。生产拆分必须保留原 batch/history/descendant 算法一份。
3. 现有 source/distribution、tally data、WWP/runtime WW 足够承接第一版简单 TARGET；缺少的是跨 run 契约、响应 history 聚合、交换文件/外部调用，而非全新输运模块。
4. source denominator、uniform mesh 体积转换、多 bin response covariance 是接口设计必须明确的物理/统计边界。
5. 非裂变 repeated-run 证据不能替代 nonzero fission F/A 测试，也没有 CE/MPI/OMP/coupled 支持结论。

本文到此完成源码阅读。具体代码组织、函数名称、输入语法与实施门禁在随后独立设计中提出；本轮没有任何生产代码改动。
