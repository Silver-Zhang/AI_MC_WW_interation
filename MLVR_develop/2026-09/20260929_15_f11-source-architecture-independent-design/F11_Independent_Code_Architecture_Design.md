# F11 Independent Code Architecture Design

2026-09-29 · Task 15 · **独立建议，待人工拍板；没有实现**

## 0. 出发点与范围

已先完成 [源码阅读报告](RMC_F11_Source_Reading_Report.md)；时间记录见 `logs/source-report-completed.txt`。以下新函数/文件名均为**建议名称**，不得误读为现有 API。现有函数以源码行号为依据。配置与物理口径的新增限制均在末节列为决策项。

冻结功能照任务原文：standard MGACE、neutron fixed-source、serial、Cartesian field、native track-mesh WW；Bootstrap 不计入 K；每次正式 iteration 是 A+F；TARGET 为现有 mesh 的空间 bins×物理 MG 群；RMC 负责序列/源/响应统计/运行/WW/调用外部，外部仅 reconstruction+WW mapping，返回 lower。没有 mesh/group mapping、CE、耦合粒子、MPI/OMP persistent、任意响应、restart/recovery、模型算法选择。

本设计选择**同一个 RMC 进程、一次 RunCalculation 内完成所有 half-runs**。不是新通用 Session 对外 API，也不把 Task 13 driver 搬入生产。依据：实际 owner 在 RunCalculation 值参数中（`RMC/src/RunCalculation.cpp:6-13`）；raw data/definition 可以保留，run state 必须由 owner 准备。

## 1. 三种代码组织的比较与选择

| 方案 | 组织 | 优点 | 主要代价/风险 |
|---|---|---|---|
| A 新 `src/MLVR/` subsystem | 新 session/controller/field/WW adapters，持有 RMC owners | 边界集中，未来多执行器可扩展 | 当前 owners 与 globals 分散且 RunCalculation 有值副本；易产生双 owner、广泛接口搬迁或复制 loop；首版没有多后端需求 |
| B 全放现有文件 | 在 RunCalculation/CalcFixedSource 中加 iteration，parser/tally/WW 文件内加全部逻辑 | 文件最少，调用直接 | 已有 CalcFixedSource 约750行且含多粒子分支；文件 IPC、解析、transport 更难分别审查；“少文件”不等于少耦合 |
| **C 推荐：现有类负责自身状态，少量独立 cpp 承载新增功能** | CDCalMode 调度；CDFixedSource 配置与 run state；source/tally/ACE/particle/WW owner helpers；专用 parser/Field IPC/external 实现文件 | 顺着现有分发和数据 owner，history loop 一份；把新边界集中到可单独验证的实现单元 | 仍需较仔细拆 CalcFixedSource 和补 reset；不是零侵入 |

选择 C 的依据不是目录偏好：模式分发已经在 CalMode（`RunCalculation.cpp:83-89`）；tally 真值在 CDTally（`Tally.h:1025-1030`）；WW 真值在 global OWeightWindow（`WeightWindows.cpp:45-66`）；source 已有可组合表示（`ExternalSource.cpp:15-57`）。新建全套平行 owner 没有必要。

配置建议：新增一个无继承、无运行逻辑的 `MLVRConfig` 值类型，作为 `CDFixedSource::mlvr` 成员。理由是 K、三组 NPS、TARGET 和外部命令共同定义固定源运行方案，CDFixedSource 已经通过 parser→RunCalculation 以引用存在。单独 header 是给 Input/CalMode/FixedSource 共享类型，不创建“配置管理器”。解析后的 mesh/group/response index 只保存明确的值或稳定索引，不保存会因 vector 扩容失效的指针。OController 仍是 hash/几何配置，其现有职责不含调度（`Control/Control.h:18-67`）。

## 2. 推荐 production call graph

```text
main                                      [现有入口，所有权不搬家]
 ├─ ReadInputBlocks
 │   ├─ ReadMLVRBlock                      [新增，保存 mlvr]
 │   └─ CheckInpBlock + CheckMLVRInput     [新增跨 block 检查]
 └─ CDCalMode::RunCalculation              [只调用一次]
     └─ FixedSourceMode:
         ├─ mlvr.disabled → CalcFixedSource [原普通路径]
         └─ mlvr.enabled  → CalcMLVR        [新增；iteration loop 在这里]
             ├─ InitializeFixedSourceModel [从旧 Init 抽出；Bootstrap/F 状态；一次]
             ├─ ResolveMLVRTarget / full axes / physical source snapshot
             ├─ ExternalSource::BuildMLVRAdjointSource
             ├─ WeightWindow::InitializeMLVRTopology
             ├─ RunMLVRHalf(BootstrapForward, 0, N_B, physical source, WW off)
             │   ├─ PrepareFixedSourceRun   [owner helpers；含 checks]
             │   ├─ ExecuteFixedSourceRun   [唯一原 batch/history/descendant loop]
             │   └─ FinalizeFixedSourceRun [MLVR输出选择]
             │       ├─ Tally::ProcessTally [一次，读取实际 owner]
             │       ├─ Tally::FinalizeMLVRResponse [F response history sums]
             │       └─ Output::WriteMLVRRun + Tally::WriteStatisticalFieldH5
             ├─ InvokeMLVRExternal → WeightWindow::LoadMLVRWeightWindowH5 → WW_A1
             └─ for k=1..K:
                 ├─ RunMLVRHalf(Adjoint,k,N_A,target source,WW_Ak)
                 ├─ InvokeMLVRExternal → LoadMLVRWeightWindowH5 → WW_Fk
                 ├─ RunMLVRHalf(Forward,k,N_F,physical source,WW_Fk)
                 │     └─ response / RE / FOM_k
                 └─ InvokeMLVRExternal → LoadMLVRWeightWindowH5 → WW_A(k+1)
main → OutputEnding                       [全进程收尾，仅一次]
```

`CalcMLVR` 是 CDCalMode 的成员，`RunMLVRHalf` 是同文件内的有类型私有成员/helper；不拥有第二份 model。所有 transport 参数引用同一次 RunCalculation 的实际 owners，source 工作对象以引用传入执行 helper。只允许在第一次 init 前形成那些原有值参数；初始化后不再复制 CDTally/CDGeometry/CDMaterial/ParticleState 全对象。

full init 与 finalization 的来源：`CalcFixedSource.cpp:73-95`、719–749。A→F→A 每步使用统一 PrepareFixedSourceRun，不能只有角色变化时才 reset；F→F 也必须清 score、bank、RNG/counters。

最后 F_K 后仍调用外部并校验/保存 WW_A(K+1)，符合冻结流程；不执行 A(K+1)。因此完成 K 时有 **2K+1 次 MC run、2K+1 次 external invocation**。只有 Forward 的 response/FOM 是正式迭代指标；A field 的 RE 属该 adjoint MC run，不是物理 Forward response 的误差。

## 3. CalcFixedSource 如何拆，哪些内容保持

推荐拆分，普通入口保留原名字与现有语义。不能只在它外面循环：InitiateAll 重入会触碰 tally registry/material 转换，且旧 source 参数按值（`CalcFixedSource.cpp:67-80`）。

| 原区间 | 建议归属 | 约束 |
|---|---|---|
| 73–75 timer register/start | 普通 CalcFixedSource wrapper；MLVR 显式 session/run 计时 | 普通路径开始时点不变 |
| 76–95 full-init body | `CDCalMode::InitializeFixedSourceModel`，保持原 InitiateAll 调用与其他粒子初始化 | 普通调用一次；MLVR 只在 Bootstrap 前一次；CBurnup 临时量留在此 helper |
| **97–719** | **`CDCalMode::ExecuteFixedSourceRun`** | 原 last_t/TotalCount、所有粒子 branches、batch/history/descendant、RNG 调用顺序、SumUpTally、load-balance finalize 保持一份；source 改为引用形参 |
| 721 ProcessTally | `CDCalMode::FinalizeFixedSourceRun` 的公共首步 | 每 half-run 一次，不得在写 Field 时又 CalcAveRe |
| 723–740 optional perturb/WWG/MPI teardown | 普通 finalization 的原分支 | MLVR 输入期拒绝这些组合；不能删旧分支或在运行中跳过应做的普通行为 |
| 741–748 surface/output/Python ending | 普通 finalization 原输出策略；MLVR 调 `WriteMLVRRun` | 不借旧 summary 自动覆盖 Result；Python 源回调在 v1 拒绝 |
| 749 timer stop | 对应 wrapper/run 层 | 普通旧计时范围保留；MLVR 范围见 §10 |

这只抽执行段，不重新编写 neutron loop。PrepareFixedSourceRun 是新增入口，不伪装成原 InitiateTrspt 已具备的能力。它统一调用各 owner reset/set/rebuild，执行前进行不变量检查；具体表见 [状态所有权表](logs/source-state-ownership.md)。

最小入参不引入一串不透明的 heap wrapper：沿用现有引用列表，加一个小 `FixedSourceRunSpec`（role、N、seed、physical cutoff、source/WW identity）。`FinalizeFixedSourceRun` 用明确的普通/MLVR 输出选择，保持 ProcessTally 的公共调用；不设计通用 plug-in callback 框架。

抽取的第一门禁是普通 neutron fixed-source fresh-process 与抽取前同输入同 seed 比较，不用“F11 能运行”替代旧入口回归。其他粒子 branches 不在本轮动态物理验证范围，但必须编译并保留原路径。

## 4. 生产准备与所有权契约

[完整表](logs/source-state-ownership.md) 是实现 checklist，包含 State/Owner/Lifetime/Bootstrap/A→F/F→A/Action 七列。下面规定执行顺序，防止“清了字段但重建顺序错”。

1. 确认上轮已 finalized、所有 history/descendant 均结束、没有打开的交换 HDF5；run ID 必须单调且未使用。记录 session counters/timer 基点。
2. `CDFixedSource::ResetRunState` 清所有完成量/interval/restart/bank/nextparticle/multiplicity/collision/lost/denominator，四类 banks 清空。Execute 自己放一个 neutron sentinel；准备阶段不重复 push。
3. `CDTally::ResetRunScores(N)` 保持 definitions/offsets/registry 和 statistics index；清六数组、Sum3、touched/stride，启用的 tester ReSize(N) 并清 gather。禁止再次 InitiateTally 或 SetStatisticsIndex（`InitiateTally.cpp:61-69`，`SetStatisticsIndex.cpp:30-42`）。response scalar 同时清零。
4. 从不可变 physical/target definition 建本 run 的 active CDExternalSource 工作副本并清 transient banks/counts；不复制 model。设置 N，再 CheckFixedSource 重算 interval，finish=-1。
5. 先显式 SET FixedSource/AceData role；ParticleState在下一步reset完成后SET同一role。`CDAceData::PrepareFixedSourceMode` 在每次 A 前清 adjoint XS/fission vectors 后 treatAdjointMaterial；F 清 derived vectors并置false。KEEP 原始 ACE 与已转换材料。
6. `CDParticleState::ResetForFixedSourceRun` 在 owner 内恢复构造默认瞬态，重建几何层级/nearest surface、材料分数、核素 cache/changed mask；调用现有 setup 部件。生产不用 driver 的 placement-new 或外部 friend 直接赋所有字段。重建完毕后从RunSpec显式SET particle role，使三层一致，后续不得再重置该标志。
7. 恢复原始物理 cutoff，再从 ACE 解出本 run runtime group cutoff；MLVR A 的最高物理能量取已验证 full MG 上界，覆盖全部库群。F 恢复 Forward energy cutoff；WW-on 的 weight cutoff 和 flags 按现有 native WW 路径一致设置（`InitiateAll.cpp:188-203`）。
8. RNG 在实际引用 owner 上设 run seed0/type/stride、position=0、position_pre 非连续哨兵，确保 static skip cache 重新计算（`RNG/StrideRNG.cpp:85-101`）。验证 source/WW apply role和iteration，激活已校验的 WW。
9. 首 history 前断言：arrays 零、registry 大小/地址稳定、banks 空、N/interval 正确、三层 role一致、source weight合同成立、WW拓扑/角色正确。失败立即终止，不“尽量运行”。

**RNG 推荐首版边界**：先支持已验证的 Type=2（LCG63_0），保留用户合法 STRIDE；SEED 为全计划基种子。为 run ordinal j 预先按累计 histories×stride 做确定性的 skip-ahead，得到独立的 run seed0；该 run position 从0开始。这样 fresh oracle 用解析出的 seed0/stride 即可复现。检查乘法/周期溢出及每 history 取数不超 stride，所有 resolved seeds 和 offset 归档；未通过该检查不得宣称 stream 不重叠。复用当前 skip arithmetic（`RNG/StrideRNG.cpp:85-101`），不发明新的 RNG 算法。Type 1/3/4/5 要补同类 oracle 后开放。

## 5. Input-card 草案与冲突检查

以下是拟新增 production 语法，尚未实现。整数/浮点数保持现有解析风格；路径专门读取保留大小写的引号字符串，不能经 keyword 大写转换。示例 GROUP 两端必须替换为实际 MGACE 的合法边界。

```text
FIXEDSOURCE
PARTICLE FISSION = 0 0
RNG TYPE = 2 STRIDE = 152917

EXTERNALSOURCE
... existing forward physical source cards ...

TALLY
... existing Cartesian neutron Type=1 track-length mesh tally, ID=1, Energy=-1 ...

WEIGHTWINDOW
WWP:N 5 3 5

MLVR
ITERATION = 3
BOOTSTRAP_NPS = 100000
ADJOINT_NPS = 100000
FORWARD_NPS = 200000
TARGET MESH = 1 REGION = 1 2 1 1 1 1 GROUP = 1.0e-9 2.0e1
SEED = 13579
COMMAND = "/absolute/path/reconstruct_ww"
WORKDIR = "/absolute/path/run-output"
```

- `ITERATION` K≥1；三个 NPS 均为整数并满足现有 >100 的检查（`ReadFixedSourceBlock.cpp:53-56`）。重复项/未知项/缺失必需项均报错。
- TARGET.MESH 是**mesh tally ID**，不是 OMeshInfo 的另一套 mesh ID。REGION 为一组或多组六整数 `(ix_lo ix_hi iy_lo iy_hi iz_lo iz_hi)`，1-based、闭区间，取空间 bin 并集；重叠去重并打印 canonical 列表，防止重复计权。仅一个 TARGET response。
- GROUP 为一组或多组物理能量端点 `(E_low E_high)`，MeV，选中其间完整 MG groups；只接受与 ACE full edges 一致的端点，归一到 ACE 的精确值，拒绝部分群/越界。非连续群以多个区间表示，合并去重；无外部 RMC 内部反向群号。
- existing FIXEDSOURCE 保留 fission/cutoff/RNG type/stride 等适用配置；MLVR 接管 N 和角色。**同时显式指定 PARTICLE.POPULATION 或 RNG.SEED 与 MLVR 时拒绝**，不做无提示覆盖。ReadFixedSourceBlock 需保存 presence bit；CheckMLVRInput 在旧 CheckFixedSource 前把 N_B 设置成初始 N。
- ADJOINT/ADJOINTCALCULATION/MAXADJOINTENERGY 整张卡与 MLVR 冲突，包含显式0；记录 presence，避免现有“只置true”的行为掩盖冲突。由调度统一选择 A/F；A 上界取完整 MG 顶边。
- TALLY 必须 neutron、Type=1 flux、track-length、有限 Cartesian、完整 Energy=-1 groups；无 Dose/AbsoluteValue/其他 response multiplier。Normalize=0/1 都可读取，但 Field/response 应用 §7 的显式转换，记录原输入。
- WWP:N 复用已有参数/default；要求 finite、WUPN>WSURVN>1、MXSPLN合法。任何 neutron static WWMESH/WWN/WWE/WWG/MCNP WW 与 MLVR 拒绝；不通过“后读覆盖先读”化解。
- v1 拒绝 CE/AIS另一数据库后端、非 neutron mode、MPI/OMP execution、surface/restart/Python sources、自发裂变 source、source bias/weight distribution/non-unit starting weight、stoptime/time-reduce、binary restart、perturbation/burnup/WWG 等未覆盖副作用。普通 source 可多 component，但全部保持等权1。物理裂变材料开放条件见 T12。
- `GenerateInpFile` 暂不扩完整 fixed-source serializer。MLVR 与 `p_bIsInputFilePrint` 组合 fail-fast；原输入及 resolved config/seed/source/axes 清单另行归档。依据是当前 writer 没有完整固定源重建链（`GenerateInputFile.cpp:37-48` 及其 CRITICALITY/TALLY 等输出分段）。

**检查层次**：ReadMLVRBlock 检语法；CheckMLVRInput（由读完 block 后调用）检跨卡冲突/范围；InitializeFixedSourceModel 后 ResolveMLVRTarget 检 ACE 物理边界、tally offsets/体积、材料支持域；每 run Prepare 与 WW import 再检身份及运行不变量。枚举仍用 FixedSourceMode，不需加一个影响各模式判断的新 RmcCalcMode。

## 6. TARGET → response → adjoint source

### 6.1 建议明确的首版物理定义（待拍板）

设选择空间集合 I、能群集合 J，V_i 是 full Cartesian bin volume，V_T=Σ_i∈I V_i。建议 TARGET 表示**所选空间并集上的体积平均、所选能群的积分通量之和**：

`R = Σ_i∈I Σ_g∈J (V_i / V_T) φ_i,g`。

φ 是 source-normalized volume-averaged、group-integrated scalar flux density；R 的几何单位仍 cm⁻² per unit starting source weight。空间是体积平均；能群求和，不除群数，也不除/乘 ΔE。这个具体响应口径是本设计提出的选择，任务只冻结了非负标量通量，尚未指定平均还是积分。

在所选 bin 和群内，响应密度 `r_i,g = 1/V_T`，所以 source component 总质量为 `r_i,g V_i`。`Q = Σ_i,g r_i,g V_i = |J|`；归一化 sampling mass `p(i,g)=V_i/(V_T |J|)`。因此 bin按体积抽样、群等概率；**体积因子在 density→概率质量时加入**，不是把已经体积平均的 tally 再乘一次体积后忘记 V_T。

若以后接受非均匀 response coefficient，需要重新设计需求；首版不新增任意 response function framework。

### 6.2 构建路线与 owner

1. ResolveMLVRTarget 生成 canonical bin/group lists、V_i/V_T、每个响应所需 GetMeshErgPtr 索引与 raw-score→density 系数（§7）。这是值数据计划，不是新 source 实现。
2. `CDExternalSource::BuildMLVRAdjointSource` 创建一个**普通 CDExternalSource 定义对象**。每个 i 一个 CDSource；fraction=V_i/V_T，bias与fraction相同，Weight=1，Particle=1。
3. 每个 component 使用三个 bin=4 分布，各只有该 bin 两端点、概率1，完成 X/Y/Z 定义标志与 SetDistriMap。能量共享 discrete=1 分布，values 是选中群的物理 centers，概率均为1/|J|，bias相同。默认各向同性；不加 CELL rejection/transform。
4. 分布通过既有 CDIndex 注册（保持其 dummy/index 约定），AddSource、CheckSourceAndDistri 统一绑定/校验。不拼输入字符串再调用 parser，也不向全局输入 source append。
5. 每次 A 从这个 definition 得到干净 active source；SampleFixSource 原路径把物理能量转内部群号。Bootstrap/F 从保存的 physical source 得到 active source，不覆盖 physical definition。

依据：`ReadExternalSourceBlock.cpp:30-66`，`Source.h:124-144`，`CheckSourceAndDistri.cpp:6-29`，`ExternalSource.cpp:25-57`，`SampleValue.cpp:25-45`，`SampleNeutronSource.cpp:267-278`。使用一个轻量 resolved-target 值与两个 CDExternalSource definition 足够；没有必要创建新的 source type 或代理采样对象。

### 6.3 归一化、方向与无效目标

起始历史必须等权1；概率抽样的非均匀性不等于权重非均匀。记录 `history_count=N`、`total_starting_source_weight=N`、`normalization_denominator=N`、normalization_kind及 source identity；运行时校验抽样前后 starting weight 为1，denominator和完成数一致。不要记录用户请求 N 来冒充实际完成数。现有统计公式把 dM 同时当 N（`TallyData.cpp:83-99`），所以不能只允许任意权重后“补一个 metadata”。

方向约定必须记录：对 angular flux 的标准 dΩ 积分定义，物理 adjoint source density 是 r，归一化的各向同性 sampling density 是 `r/(4πQ)`。因此 MC A field 是单位人工 starting source 的 field，绝对 adjoint 解需另考虑 `4πQ` 的尺度及所采用的 angular convention；记录 `Q` 与 `angular_pdf=1/(4π)`，**首版 WW mapping 只使用明确 source-normalized field，不把它宣称为已校准绝对 importance**。T5 的 reciprocity/解析例门禁验证离散 MG 与方向归一化的对应，不能仅凭 source frequencies 通过就宣布物理等价。

拒绝空集、越界、zero/negative/nonfinite volume、Q≤0、不完整群、源点落入无效/零重要性计算域。目标 mesh 全 bin 均匀分布在统计上就是上述定义；如果目标包含几何外部空洞，不能默默按有效材料体积分布重新解释。输入先检查可判断条件，运行出现无效 target 样点即 fail-fast。有效目标但测得 R=0 是 ZERO_SCORE；它不自动变成“非法目标”，也不能赋 FOM=∞。

### 6.4 response RE 的具体实现位置

`CDTally` 持有一个 scalar CDTallyData，不与 mesh registry 混淆。在 `SumUpTally(long long,double)` 的 mesh `SumTallyBin` **之前**（`SumUpTally.cpp:130-132`）读当前 history 的 selected scores：

`r_h = Σ_i,g (V_i/V_T) c_i score_h[i,g]`，其中 c_i 是 raw tally到density的系数。

累积 `S1=Σ_h r_h`、`S2=Σ_h r_h²`，每个 source history 一次，全部 descendants 已完成。FinalizeMLVRResponse 用 N>1：

`R=S1/N`，`RE_R=sqrt((N*S2/S1²-1)/(N-1))`（S1>0）；S1=0按zero-score处理。

可复用 CDTallyData::CalcAveRe(N,1)；浮点导致的 tiny negative variance 须按预先规定的舍入容差处理并记录，真正非finite/负方差报错。此 scalar 的 squared sum包含不同 bins/groups的协方差，不能用各 bin RE 拼接。校验 R 与同轮 Field 加权和在浮点容差内一致；A 不输出“Forward response”。

## 7. field.h5：写入位置、数值转换与契约

**owner/function**：新增 `CDTally::WriteStatisticalFieldH5(path, resolvedTarget, runInfo, AceData)`，调用时点为 ProcessTally 与 response finalize 后、reset 前。实现放 `MLVRFieldIO.cpp`，复用 RMC::File::HDF5，独立交换 schema；不修改旧 Result/MeshTally HDF5 的消费者契约。

### 7.1 raw Ave 转成确定的 Field measure

对现有 Type=1 track-length Cartesian 实现，明确 `c_i`：

| 当前 scorer 路径 | 原数组度量 | c_i |
|---|---|---|
| uniform CalcMeshTrck，Normalize=0或1 | weighted track length / source denominator | 1/V_i |
| heter CalcHeterMeshTrck，Normalize=0 | 同上 | 1/V_i |
| heter CalcHeterMeshTrck，Normalize=1 | 已除 V_i | 1 |

`value=c_i*Ave`，`RE=原 RE`。数据 owner 的数组不就地改写，response聚合使用同一个系数表，防止两份逻辑不一致。依据：`MeshFun.cpp:296-304`、342–346、379–387 对比474–484；`ScoreMeshTally.cpp:61-101`；`ProcessTally.cpp:364-393`。这是对当前源码的 adapter 约定；将来修正 uniform scorer 时必须同步 schema provenance/转换测试，防止重复归一化。

Field 单位明确写成：**source-normalized track-length flux density；几何单位为 cm 时，几何量纲为 cm⁻² per unit starting source weight**。每群已积分，无 MeV⁻¹。负 Ave/value拒绝；finite value>0 且RE有限非负→VALID；value=0且RE=0→ZERO_SCORE；其他组合报错。ReconstructedField 由外部产生，不复制 MC RE，重构与WW mapping仍为两个步骤。

### 7.2 Schema 草案

为直接复用现有 vector HDF5 写法，数据集采用一维展平、另外强制四维 shape，避免隐式 ndarray 顺序：`shape=[Nz,Ny,Nx,G]`，`axis_order="z,y,x,energy"`，g最快；`i_spatial=ix+Nx*(iy+Ny*iz)`。mesh tally实际指针仍用 GetMeshErgPtr 读取，去掉 Tot 槽。此布局是待冻结的文件草案，不是已实现格式。

| 字段 | 内容与校验 |
|---|---|
| schema_version / shape / axis_order | 版本、正维度、checked product；value/RE/status 均为长度 product 的数组 |
| value / RE / status | float64/float64/明确数值枚举；同shape |
| mesh/x_edges, y_edges, z_edges | 完整 finite strictly increasing boundaries，含两端；不做 mapping |
| energy/edges_MeV | 完整 G+1、物理升序；全部核素共用的 ACE structure |
| role / stage / iteration / run_ordinal | role=bootstrap_forward/adjoint/forward；stage=bootstrap/formal；bootstrap iteration=0 |
| history_count / requested_history_count | 实际完成 N / 请求 N；v1 必须相等 |
| normalization_denominator / total_starting_source_weight / normalization_kind | 从完成状态导出并核对；v1等权1下都=N |
| value_units / energy_measure / source_tally_measure / volume_conversion | 单位、group_integrated、原scorer路径、c_i规则 |
| run_id / field_id / mesh_id / energy_id / source_id / target_id / applied_ww_id | 身份、来源；bootstrap applied_ww_id=none |
| provenance | RMC revision/build、输入/ACE来源与内容标识、seed/type/stride、WWP、source normalization Q/方向约定、timing scope |

首版 identity 使用独占session_id加固定对象标识：mesh_id=session_id+mesh tally ID，energy_id=session_id+唯一group结构ID；source/target/field/WW同理标识其生成位置。身份校验还必须逐项比较完整canonical数组、单位、axis convention，不能只信任ID字符串。生产边界不依赖std::hash或新crypto库。复现实验归档由launch/验证工具另保存原input/ACE/executable的SHA-256清单；内容hash是证据附件，不代替运行时full-axis比较。

G+1 从 standard MGACE center/width 解出全部边界，校验相邻 upper/lower连续及所有核素一致后选用canonical数组；不从 `.Tally` 的G个lower猜最高上界，也不用 WWMESH 的0/∞sentinel（`CheckMgAceBlock.cpp:38-60`，`GetMgCs.cpp:263-278`）。空间 full edges 按现有 MeshTallyHDF5 展开逻辑复用小 helper（`MeshTallyHDF5.cpp:47-79`）。

写 `field.h5.tmp`，flush并结束局部文件owner作用域，成功后同目录rename为field.h5；验证文件关闭/存在后调用外部。不借 Output.p_Result 的全局句柄。raw HDF5 wrapper不可复制；需要 shape/type查询时只增加最小通用dataset-info接口（`HDF5.hpp:91-128`、273–287，`HDF5_misc.hpp:33-49`）。

## 8. ww.h5：校验后注入已有 WW owner

新增 `CDWeightWindow::LoadMLVRWeightWindowH5(path, expectedRunInfo, fixedTopology)`。外部输出 `/lower`、shape/axis_order、full mesh/energy identities（含全轴，便于核验）、producer field_id、**apply_role / apply_iteration**、ww_id/schema_version；不返回 survival/upper，更不改 source/iteration参数。

1. 先读取小metadata，检查版本、类型、rank、shape、checked product、预期空间/群轴；禁止读取shape未知的巨量array后才比尺寸。既比较身份，也比较canonical full axes。首版不接受近似不同mesh或group mapping。
2. 检查 producer field_id是刚写的Field，apply身份正确：B0→A1、Ak→Fk、Fk→A(k+1)。不能仅验证文件名或mtime；同目录旧文件也不能复用。
3. 读入临时lower vector，逐元素 finite且strictly positive；不接受0、负数、NaN、∞作disable哨兵。检查 WUPN/WSURVN及乘积finite，设置资源/尺寸上限。
4. 全部通过后，当前 OWeightWindow topology与canonical energy不变，调用既有 ProcessWeightWindow 生成三边界（`WeightWindows.cpp:79-101`）。新 WW generation记录在runInfo；下一run准备才激活相应native track-mesh flags。
5. `p_OWeightWindowMesh` 从tally复制几何/topology值，强制`p_bUseVol=false`；内部能群按物理升序G+1有限轴，native lookup使用group center（`WeightWindows.cpp:72-77`）。测试第一/最后群以及每个 bin，不能只检查第一个lower。

不复用 ReadWeightWindow parser：它会改变calmode/flags、处理sentinel并重设某些arrays（`ReadWeightWindow.cpp:6-43`、329–341、419–427）。复用的是WWP、topology表示、ProcessWeightWindow和实际transportlookup。

## 9. 外部程序与 fail-fast

`CDCalMode::InvokeMLVRExternal` 在独立 `MLVRExternal.cpp` 实现；由CalcMLVR调用。source搜索只有未经检查的mkdir system先例（`OutputMXSFile.cpp:19-32`），不能将其扩成带shell字符串的协议。

首版Linux serial：COMMAND为可执行文件绝对路径，RMC构造独立argv（`--field <absolute field.h5> --ww <absolute ww.h5> --apply-role ... --apply-iteration ...`）；使用fork+execv+waitpid或等价可检查API，在child设当前run工作目录，父进程同步等待。COMMAND需要参数时由用户提供wrapper executable，不设计shell插值语言。stdout/stderr分别写run目录external日志，waitpid处理EINTR/信号退出；不重试。Windows在配置检查明确未支持，不走system降级。

WORKDIR必须是新建的独占session根（已存在且非空拒绝），相对路径按输入目录解析成绝对路径；父进程不反复chdir。启动前关闭field临时句柄，确认本run无旧ww.h5；外部成功写tmp并rename，RMC仍完整校验返回文件。外部挂起的超时策略不做自动恢复，首版记录进程状态并允许用户终止；若加入有限timeout也只fail-fast，不重试或换模型。

| 失败 | 首次检查位置 | 结果 |
|---|---|---|
| parser/unsupported/conflict | ReadMLVRBlock / CheckMLVRInput | 在输运前报错 |
| target/axes/source无效 | ResolveMLVRTarget / builder | 初始准备终止 |
| reset/role/bank/seed/N不满足 | PrepareFixedSourceRun | 下一history不得开始 |
| Field写失败或缺失 | WriteStatisticalFieldH5 / 调度 | 不启动外部 |
| exec不存在、启动失败、nonzero exit、signal | InvokeMLVRExternal | 记录状态与stderr路径，终止 |
| ww.h5缺失/打不开/schema损坏 | LoadMLVRWeightWindowH5 | 不更新active WW |
| lower/shape/mesh/group/role/iteration/field_id不符 | 同上 | 不修补、不沿用上轮WW，终止 |
| transport lost target source、denominator不符 | sampling/run finalize | 本run标记失败，不发往外部 |

错误汇总使用现有串行 `_ERROR` 路径（`PrintFile.cpp:6-58`），先把独立run manifest中的failed阶段/诊断持久化再终止。局部IO错误先交回调度层，不依赖exit后的析构来关闭/提交文件；只有全部完成才标run/session completed。无复杂恢复状态机。

## 10. Batch、输出、response/FOM 与归档

### 10.1 不新增 batch 参数

iteration k管理 A/F 顺序；每 half-run 的 N传给 CDFixedSource；原 DistributeSource/PrcoessBatchEnd管理 existing batches；每 history包含全部descendants。依据：`CalcFixedSource.cpp:106-209`，`InitialBatchSource.cpp:7-38`、94–144，`CheckTransport.cpp:51-72`。

首版固定 N、无 restart/stoptime/time-reduce，在 serial 下 interval=N，完成后退出，通常单batch。保留原batch loop，**不把 NPS切成自创batch，不以StatisticsTester的20个诊断分组替代source histories**。当前 serial SumUpTally参数是 Neu（`CalcFixedSource.cpp:197-203`），在多batch时会重新从1开始；本设计不宣称已经验证其跨batch诊断索引，未来开启那些受限选项前需单独核验。无需为F11新增输入batch参数。

### 10.2 文件与句柄

建议每次成功创建一个独占session根：

```text
WORKDIR/
  session-manifest.json
  original-input/                 # 原卡与 include 材料，保留来源
  resolved-config.json            # canonical TARGET, axes, N, source, seed plan
  bootstrap/                     # role=bootstrap_forward, iteration=0
    field.h5  ww.h5               # ww apply=adjoint, iteration=1
    run.json  run.log  external.stdout  external.stderr
  iter-0001/adjoint/
    field.h5  ww.h5               # ww apply=forward, iteration=1
    run.json  run.log  external.stdout  external.stderr
  iter-0001/forward/
    field.h5  ww.h5               # ww apply=adjoint, iteration=2
    run.json  run.log  external.stdout  external.stderr
  ...
  metrics.csv
```

只对新目录写文件，拒绝复用已有非空WORKDIR；不覆盖历史reference/benchmark。`CDOutput::WriteMLVRRun` 用明确的path/本地FILE或ofstream写run.log/run.json，Field writer自己持有交换HDF5。全局session Output/Result不在half-run换名、关闭或重开；MLVR不调用旧的per-run OutputSummary→OutputTallyh5(Final,0,0,0)。main既有OutputEnding最后执行一次。文本需要mesh明细时单独扩显式path导出，并修正Tot的global FILE*依赖后才使用；**首版交付field.h5+run summary已满足per-iteration输出，不强求完整旧.Tally副本**。

### 10.3 FOM 的时间定义

正式 Forward指标：`FOM_k = 1/(RE_R,k² * T_MC,k)`。`T_MC` 明确从本half-run准备开始到ProcessTally/response finalize结束，包含mode重建、source准备与MC，不含一次性raw-model init、Field磁盘输出、external reconstruction与WW读取。分别记录 `T_init, T_prepare, T_transport, T_tally_finalize, T_field_io, T_external, T_ww_import, T_session_wall`；定义 `T_MC=T_prepare+T_transport+T_tally_finalize`。该时间定义待拍板。

普通CalcFixedSource原timer从初始化前到summary后（`CalcFixedSource.cpp:73-75`、749）保持不变；不得把两个范围不同的FOM直接称为同口径提速。若要研究总成本，另用累计session wall列，不能把external成本藏在MC FOM里。

MLVR使用局部/新增区间timer计算T_MC，原OTimer.FixedSource仍为history时间统计提供interval。每轮正确清runTime和recordTime再start，不能只调用Timer.reset（其未清recordTime：`Utility/Timer.h:82-99`）；全局Total始终保留。`OTimer.reg`采用emplace而非覆盖（123–125），重注册不是reset。

N>1、R>0、0<RE_R<∞、T_MC>0才报告有效FOM；R=0标ZERO_SCORE且FOM缺失；正R但RE=0时标FOM_UNDEFINED，不输出∞。保留原因，不能靠epsilon伪造有限排名。metrics.csv只汇总k=1..K Forward；Bootstrap可单列诊断，A仅记录运行统计/field RE，不混入K或Forward FOM。

归档保留raw Field的MC RE；external reconstructed field不带伪MC RE。adaptive K轮的各run统计分别报告，不把依赖前轮WW的多轮均值无条件当独立样本合并估计误差。

## 11. Existing files to modify

这是实施建议清单，本任务未修改这些文件。实现范围按通过的阶段逐项展开。

| 现有文件（均在RMC） | 建议改动及理由 |
|---|---|
| `src/Input.h` | MLVR parser/check声明、BlockDefined/presence登记；沿用当前解析owner（46–72，172–194） |
| `src/ReadInputBlocks.cpp` | 顶层MLVR分发；读完后统一check，避免block顺序影响（134–140，377–381） |
| `src/ReadFixedSourceBlock.cpp` | 保存POPULATION/SEED/ADJOINT显式presence，才能可靠拒绝冲突（33–62，117–160，209–235） |
| `src/CheckInpBlock.cpp` | 调CheckMLVRInput；在现有CheckFixedSource之前设N_B；GenerateInpFile冲突检查（85–95） |
| `src/ReadWeightWindow.cpp` | 记录实际出现的静态WW card类型供冲突检查；不改变普通WW构造（277–287，329–341） |
| `src/CalMode.h` / `src/RunCalculation.cpp` | 新增私有调度/执行/准备函数声明和FixedSourceMode内部开关；不广泛改RunCalculation的值/引用签名（152–158 / 83–89） |
| `src/CalcFixedSource.cpp` | 按§3抽init、execute、finalize；新增prepare orchestration，唯一history loop保持（67–749） |
| `src/FixedSource.h` / `src/InitiateTrspt.cpp` | mlvr配置、run spec、ResetRunState；现有init不足以覆盖reset（192–329 / 60–100） |
| `src/AceData.h` / `src/TreatAdjointMaterial.cpp` | PrepareFixedSourceMode双向flags/clear/rebuild、full group edges读取/校验小helper；防止+=残留（TreatAdjointMaterial 22–57；CheckMgAceBlock 38–60） |
| `src/ParticleState.h` / `src/InitiateAll.cpp` | owner reset方法与共享geometry/material cache setup helper；full init调用顺序保留，run prepare复用必要部分（InitiateAll 145–176、192–203） |
| `src/ExternalSource.h` / `src/ExternalSource.cpp` | builder声明；普通definition与mutable工作状态的清理/等权检查入口（ExternalSource 15–57） |
| `src/SampleNeutronSource.cpp` | MLVR模式下source起始权重/无效target点检查；错误在污染tally前退出；普通路径保持（180–278） |
| `src/Tally.h` / `src/InitiateTally.cpp` | response scalar/resolved index、ResetRunScores/Field声明；保持registry只初始化一次（Tally 1025–1030；InitiateTally 61–69） |
| `src/TallyData.h` / `src/TallyData.cpp` | 完整run reset helper，在现有SetZero之外清Sum3/touched/stride（TallyData.cpp 17–68） |
| `src/StatisticsTester.h` / `src/StatisticsFunc.cpp` | owner级ResetForRun封装ReSize/gather清理，不重建index（StatisticsFunc 8–94） |
| `src/SumUpTally.cpp` / `src/ProcessTally.cpp` | response的history聚合与结束统计；不改mesh estimator定义（130–132 / 364–393） |
| `src/WeightWindow.h` / `src/WeightWindows.cpp` | InitializeMLVRTopology/Load声明，validated lower安装及WWP检查复用ProcessWeightWindow（79–101） |
| `src/Output.h` / `src/OutputSummary.cpp` | WriteMLVRRun独立path输出；不反复调用session收尾（OutputSummary 184–207） |
| `src/RNG/RNG.h` / `src/RNG/StrideRNG.cpp` | seed-plan skip与明确ResetRun入口，检查stride预算，不复制static状态（StrideRNG 85–101） |
| `include/rmc/file/hdf5/HDF5.hpp` / `HDF5_misc.hpp` | 若现有API不足，加只读dataset type/rank/extent查询；IO adapter在分配前校验，不向wrapper塞MLVR语义（HDF5.hpp 118–128、273–287） |

`main.cpp`、`InitialBatchSource.cpp`、`ScoreMeshTally.cpp`、`DoMeshWeightWindow.cpp`、`GenerateInputFile.cpp` **无需为推荐v1主动改算法**。uniform volume差异先由Field/response adapter显式转换；普通计分不悄悄改变基准。Prepare/response的新调用通过owner方法和已有SumUpTally入口接入。

## 12. New files justified

推荐六个新文件，全部保持在现有src平面，不创建新的runtime class层：

| 新文件 | 内容/既有类 | 为什么单独成文件 |
|---|---|---|
| `src/MLVRConfig.h` | MLVRConfig、ResolvedTarget/RunInfo等少量值类型 | 多owner需共享配置/协议值；塞进Input会引入parser依赖，塞进CalMode会把I/O绑定大型运行头；不做manager |
| `src/ReadMLVRBlock.cpp` | CDInput::ReadMLVRBlock / CheckMLVRInput | 完整新block及quoted path规则，符合现有每block一个cpp风格；不能伪装现有FIXEDSOURCE ADJOINT卡 |
| `src/CalcMLVR.cpp` | CDCalMode::CalcMLVR / RunMLVRHalf / target resolve | 全部工作流在一个可读单元；不是再复制一次transport；RunCalculation保持分发职责 |
| `src/BuildMLVRAdjointSource.cpp` | CDExternalSource::BuildMLVRAdjointSource | 从mesh响应到已有source的非平凡转换，有体积/能群/定义校验；与已有通用抽样代码分别审查，但class仍是ExternalSource |
| `src/MLVRFieldIO.cpp` | CDTally::WriteStatisticalFieldH5 / CDWeightWindow::LoadMLVRWeightWindowH5及共享axes/shape校验 | 新双向版本化交换契约；旧MeshTally/Result schema不同，强塞其中会混淆消费者/归一化；无需再拆Field class/WW class |
| `src/MLVRExternal.cpp` | CDCalMode::InvokeMLVRExternal及受限进程启动helper | 新OS进程生命周期、日志/退出检查；当前FileIO只是parser，没有可复用机制；从数值执行函数隔离平台代码 |

这些cpp由现有 `CMakeLists.txt:661-671` 的source glob收集，增加文件后必须重新configure再build。若增加具体依赖必须显式改CMake并记录理由；本方案不要求引入ML runtime、Python embedding或新的crypto库。

## 13. P1–P9 minimal-change implementation plan

每阶段单独可复核diff/命令/真实输出，完成门禁后进入下一阶段。实现时另建实施档案并取得RMC改动授权；本设计文件不是代码授权。

| 阶段 | 修改范围 | 最小验证/进入下一阶段条件 | 必须保留 |
|---|---|---|---|
| **P1 input only** | MLVRConfig、ReadMLVRBlock、Input/ReadInputBlocks/CheckInpBlock、presence记录 | parse合法样例与冲突样例；K/NPS/TARGET/path原样与canonical回显；invalid组合在输运前失败 | 普通输入解析、旧运行模式；暂不宣称MLVR可运行 |
| **P2 repeated fixed-source production lifecycle** | CalMode/RunCalculation/CalcFixedSource、各owner reset、RNG、独立run IO基础 | T1/T3；非裂变F→A→F的T4；同owner/registry不增长、完整reset ledger；fresh-process oracle同seed匹配 | 唯一history/batch loop、旧普通入口及计时；没有Task13 driver依赖 |
| **P3 target→adjoint source** | builder/ExternalSource、TARGET resolve、Tally response、SumUpTally/ProcessTally、sampling guards | T5：不等体积多bin、多群概率/等权/定位、解析或互易例；response history S1/S2独立核对 | physical source定义；不把bin RE相加 |
| **P4 Field export** | MLVRFieldIO、AceData full edges、Tally converter、必要HDF5 info查询 | T6，含均匀/非均匀同几何非单位体积，full G+1、status非法值、normalization | 无二次volume除法、Tot不作能群、旧输出schema |
| **P5 external + WW import** | MLVRExternal、WeightWindow、field identity/atomic I/O | T7/T8，stub executable返回已知lower并测试所有故障；验证runtime三界和实际transportlookup | 外部只返回lower；校验前不改active WW |
| **P6 Bootstrap** | CalcMLVR的Bootstrap半轮与一次握手 | T2：fresh Forward oracle、WW明确关闭、B0→A1、N_B/seed/Field一致 | Bootstrap不计K；不引入K=0的正式输入约定，阶段性harness可停在B后 |
| **P7 one A→F** | CalcMLVR完整k=1顺序与metrics | T9；3次MC+3次外部；A1/F1各自oracle；F1后的WW_A2也验证归档 | A/F来源、role与WW不得对调 |
| **P8 K iterations** | loop边界、身份与run目录、汇总 | T10 K=3：7次MC/7次external，末尾WW_A4；每run oracle、registry/FD稳定 | 不提前按RE停止；不合并跨run原始统计 |
| **P9 metrics/archive** | OutputSummary新增方法、resolved config/seed/session manifest、metrics导出 | T11与T1–T10最终门禁；T_MC分项及FOM计算可复核，失败run无completed标志 | 输出不覆盖、无伪绝对adjoint/伪RE、旧基准不更新 |

**T12并行于阶段门禁的逻辑条件，而非在代码完成后补一句说明**：只发布非裂变受限v1可先保持fissile guard；一旦要允许裂变MGACE或声称general MG adjoint，必须在P7/P8放行前通过T12。这里“并行”指验证条件可安排，不要求或授权并行agent工作。

## 14. Test plan 与 fresh-process oracle

以下是未来实施的测试设计，**本任务均未执行**。同编译器/选项/数据/seed/stride/physical source/cutoff/WW、serial下，先比较确定性source序列、history计数、S1/S2、Ave/RE与WWlookup；输出时间不要求字节一致。若必要数值容差，事先固定并解释来源，禁止为过关扩大容差。physics sanity和unbiasedness用独立seed集合及预先定义的统计判据，不把“RE范围内”当逐bin任意放宽许可。

fresh oracle保留两条：普通回归用抽取前fresh binary；每个half-run用同修订生产binary的普通固定源fresh process，生成等价静态source/WW卡及resolved run seed，比较到该run结束。HDF5与text打印精度不混用；需要同精度时在验证构建中读owner arrays。使用oracle辅助工具，不把测试driver当生产调度。

| ID | 测什么/真实证据要求 | Gate |
|---|---|---|
| **T1 ordinary fixed-source regression** | representative standard-MG neutron：analog和native WW-on；新旧binary同seed，source/history、S1/S2、Ave/RE、三界/lookup一致；旧outputs含义保持。抽取覆盖所有编译branch；未做的CE/coupled物理测试明确列出 | **v1必需**，P2开始和P9结束 |
| **T2 Bootstrap** | 生产Bootstrap vs fresh F，physical source一致、WW未使用、实际N_B/denom/seed、完整Field与B0→A1；phase init只一次 | **v1必需** |
| **T3 F→F** | 同owner consecutive F（同spec用于精确reset对照；不同N/seed/WW用于污染检查）；registry地址/长度稳定；六数组+Sum3/statistics/touched/banks/counters初值真实dump；fresh各自匹配 | **v1必需** |
| **T4 F→A→F** | nonfissile MG；三层flag/cutoff/cache/adjoint arrays每阶段dump，第二次F与freshF一致，再加A→A核查+=不累积；含WW-on例 | **v1必需**；不据此声称fission正确 |
| **T5 TARGET source/response** | 至少两个不等体积bin、多个非连续群；固定seed频数与体积概率、空间均匀/方向各向同性/weight=1/群定位；独立score oracle计算每history response S1/S2及跨bin协方差；小型MG解析/互易case确认源/响应归一化；无效目标及非单位源拒绝 | **v1必需** |
| **T6 field.h5** | 每字段、shape/axis/角色、full boundaries、N/denom；uniform vs heter等几何且V≠1，Normalize0/1四种path按转换后相符；G群排除Tot；最高upper；负/NaN/zero+RE异常拒绝。正确的ZERO_SCORE接受 | **v1必需**；volume风险未过不得标cm⁻² |
| **T7 ww.h5** | unique-pattern lower覆盖全部bins/groups；native lookup同数组且survival/upper=WWP倍率；换第二套lower使实际访问变动；mesh volume flagfalse；坏维度/类型/axis/边界/role/field_id、0/negative/nonfinite/overflow被拒 | **v1必需** |
| **T8 external failure** | stub分别exit0/非0/信号/缺文件/坏HDF5/旧identity/部分tmp；含带空格路径；终止点在下一history之前，不回退旧WW；真实returncode/stdout/stderr/manifest | **v1必需** |
| **T9 one formal iteration** | K=1完整B0→A1→F1；记录3个half-run和3次external，最终WW_A2存在；source/WW角色、N、response/RE/FOM复算；每半轮fresh-process | **v1必需** |
| **T10 K=3** | 7个half-run、7次external，WW_A4最终保存；每轮fresh oracle；固定seed-plan复跑数值一致，registry/内存owner/FD无单轮残留增长；不同N_B/N_A/N_F | **v1必需** |
| **T11 result archive** | 两次独立WORKDIR数值可复现/不会覆盖；input/include、版本/构建/依赖/ACE内容标识、source/TARGET/axes、seed-plan、WWP、timing_scope、metrics/外部版本齐全；异常路径保留失败阶段；FOM不是NaN/∞伪指标 | **v1必需** |
| **T12 fissile F/A lifecycle** | 使用真实nonzero νΣf/χ、finite可计算的固定源MG case；F→A→F→A，每次adjoint scattering与fission数组从零重建且与fresh匹配；验证fission descendants、bank完整排空、target互易/物理response sanity、WW-on下与analog统计一致 | **一般MG/裂变支持声明前必需**；若v1开放裂变则也是v1发布门禁 |

“受限v1”指standard MGACE中的已验证非裂变范围，并显式拒绝未开放fissile材料，而不是默认处理后在报告脚注写未验证。T12通过也仅扩到其验证范围，不自动覆盖所有特殊源/数据/角分布。

future extension：任意starting weights需要分离normalization D与统计N并验证加权估计；CE/coupled；MPI/OMP owners与reduction；一般response；mesh/group mapping；restart恢复；更广RNG支持。它们不属于本次实现清单，也不用于拖延上述v1门禁。

## 15. 风险与待决策事项

| 风险 | 当前证据 | 本设计的具体控制 |
|---|---|---|
| 重复run状态残留，尤以derived fission、cutoff单位、tally registry、particle/RNG cache为主 | `TreatAdjointMaterial.cpp:22-57`、`InitiateAll.cpp:192-203`、`InitiateTally.cpp:61-69`、`StrideRNG.cpp:85-101` | owner helper、完整state表、一次model init、T3/T4/T12 fresh oracle |
| Field/response单位与统计口径不一致 | uniform raw track vs heter normalized；ordinary denom=N；history squares | 同一c_i表用于Field和response；等权1合同；history内合并后求平方；T5/T6 |
| 每轮WW/文件身份或输出生命周期混淆 | globalWW三界、globalResult写Final、源工作状态可变 | immutable definition+active副本；唯一run路径、双向apply/provenance检查、校验后一次安装；T7–T11 |

实现前需要人拍板：推荐C方案及唯一loop拆分边界；TARGET的空间体积平均/群积分求和口径；等权1、Type2、受限非裂变和格式化输入输出禁用等首版边界；T_MC/FOM定义与文件schema/身份约定。K顺序、RMC/外部分工、Bootstrap不计K等已冻结需求不重新请求决定。

## Independent recommendation

1. **代码组织**：采用混合方案C。沿用CalMode、FixedSource、ExternalSource、Tally、AceData、ParticleState、WeightWindow、Output/RNG的实际owner；新增少量实现文件承接输入/调度/交换协议。无需新`src/MLVR/`子系统或第二套model/session对象。
2. **iteration loop**：放在新增`CDCalMode::CalcMLVR`，由一次`RunCalculation`的FixedSourceMode分支进入。Bootstrap一次，然后k=1..K执行A→external→F→external，F_K后也保存并校验WW_A(K+1)。全流程共2K+1次MC和2K+1次external。
3. **CalcFixedSource**：保留普通wrapper；将76–95抽full initialization、97–719抽唯一execute loop、721–748分公共tally finalize与普通/MLVR输出，timer在各入口明确管理。新增owner-based PrepareFixedSourceRun，不重复调用InitiateAll，不复制history/batch loop。
4. **扩展现有类**：FixedSource持配置与run reset；CalMode调度；ExternalSource构造简单TARGET source；AceData/ParticleState做双向mode与cache准备；Tally输出Field并按history聚合response；WeightWindow校验/装载lower并用WWP生成三界；Output/RNG提供明确的run记录与seed计划。
5. **必要新文件**：`MLVRConfig.h`、`ReadMLVRBlock.cpp`、`CalcMLVR.cpp`、`BuildMLVRAdjointSource.cpp`、`MLVRFieldIO.cpp`、`MLVRExternal.cpp`。它们承载实际新增逻辑，仍实现既有类的方法；不增加通用controller、source代理或transport副本。
6. **最大三个风险**：①F/A残留状态及非零fission重建；②volume/source normalization与多bin response RE；③WW角色/迭代身份、global output生命周期。特别是当前uniform TL scorer没有读取Normalize flag，Field不能一律直接复制Ave；需要明确c_i转换并过非单位体积门禁。H2O动态结果不能代替fissile T12。
7. **需要拍板**：是否采用上述代码边界；TARGET是否取空间体积平均、选群求和；是否接受等权1/Type2及T12前拒绝fissile等v1限制；确认T_MC/FOM与交换schema。收到明确实施授权后才进入新实施任务。本任务到设计文档为止，不改RMC、不运行生产实现、不更新公共状态。
