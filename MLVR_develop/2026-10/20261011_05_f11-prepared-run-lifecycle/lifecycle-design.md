# Stage2 具体实施方案（已批准实施）

导航：§1 合同与范围；§2 C++接口；§3 Prepare顺序、§3.1 源权重合同、§3.2 计时；§4 RNG；§5 改动文件/回滚、§5.1 全局对象链接。设计唯一基线为知识库04 §3.3/§5/§14。这里只细化Stage2，不修改冻结规则。

## 1. 合同与范围

caller在一个连续栈帧持有完整模型与工作对象。CDCalMode提供一次初始化、一次run、结束三个public入口；每次run内部清理并调用原私有执行core，不接受caller声明“我已经初始化”的token。模型、raw核数据、tally definition/registry在Initialize后固定且不得复制/移动；每个run有自己的active source和清零统计。接口只允许完整half-run间切换，执行中不能修改source/WW。

第一批生产prepared入口限定standard MGACE、neutron-only、Linux串行、RNG Type2、§3.1限定的单个定点/定能/定向单位权重源、Cartesian Type1/track-length/Energy=-1/Normalize=1、native track-mesh WW。MG群数随固定模型，首批门禁使用30n/12p H2O。source/role/NPS/有效RNG段/native lower可变；geometry/material/rawXS/群/mesh/WWP保持。Bootstrap/K循环不属于这个入口。

prepared入口明确拒绝：CE/MG-HDF5、MPI/OMP/AIS、photon/coupled、burnup/kinetics/perturb/material sampling/TMS、restart/surface-source/停止时间/TIME_REDUCE、Python源、spontaneous-fission源、MCNP/point/cell WW/WWG、CAP/FET/cs等未覆盖tally功能以及特殊weight policy。不删除或限制普通CalcFixedSource的这些已有分支。固定NPS应可由原单run/batch机制完整结束，且已有bank分配的int容量换算必须无溢出，不新增batch参数。

首次支持边界不包含非零裂变产生项。读取原数据后检查使用材料中各核素/群的νΣf；任意非零（或非有限非法数据）拒绝prepared执行，不修改raw数据/不关闭裂变来通过。一般裂变材料需单独非零贡献F→A→F→A门禁通过再放开。

私有生命周期为 Uninitialized → ModelReady → Preparing → Executing → Finalizing → Finalized →（Preparing…）→ Closed，及 Failed。对未初始化、重入、wrong-owner和非法规格先拒绝，保留已有合法结果；CLEAR之后任何失败将序列标Failed并记录阶段，禁止继续或复用已分配RNG段。Finish只标记本入口Closed，不关闭进程资源；初始化成功后同一批对象不能再次全初始化，也不允许在该进程建立第二个prepared模型或转普通入口重初始化。由于全局WW/Output，只允许一个活动序列；不引入可持有第二模型的Session/Manager。

## 2. 拟定 C++ 接口

以下签名已按用户正式授权实现；原设计及实施具体化分别保留在本节和§6。数据定义位于根src/FixedSourceRunSpec.h，C++类型使用既有long long历史计数和uint64种子。

~~~cpp
enum class FixedSourceRole { Forward, Adjoint };

struct FixedSourceSeriesSpec {
  std::uint64_t rootSeed;
  std::uint64_t stride;
  std::uint64_t firstHistoryOffset;
};
struct FixedSourceWeightWindowSpec {
  bool enabled;
  FixedSourceRole appliesToTransportRole;
  std::string identity;
  std::vector<double> lower; // mesh-major, energy-minor；shape来自固定native定义
};
struct FixedSourceRunSpec {
  std::uint64_t runId;
  FixedSourceRole role;
  long long sourceHistories;
  double maxAdjointEnergyMeV;
  std::string sourceIdentity;
  FixedSourceWeightWindowSpec weightWindow;
};
struct FixedSourceWeightAudit {
  long long sampledHistories;   // 实际经过采样后检查点的次数，含零得分历史
  long long nonUnitHistories;   // 非有限或不等于1；成功时必须为0
  double initialWeightSum;      // 独立逐次累加实测w；不是从N或D赋值
  double minimumInitialWeight, maximumInitialWeight;
};
struct FixedSourceRunReceipt {
  std::uint64_t runId;
  FixedSourceRole role;
  long long requestedHistories;
  long long completedHistories;
  double normalizationDenominator; // 实际用于ProcessTally的D
  FixedSourceWeightAudit sourceWeightAudit;
  bool unitSourceWeightsVerified; // 仅全数检查并核对N=D=W0后为true
  double prepareSeconds, transportSeconds, tallyFinalizeSeconds, mcSeconds;
  double measuredMcSeconds; // 独立 t3-t0 舍入核对
  std::string timingScope; // 固定"prepare+transport+finalize"（KB04 §12.1）
  std::string statisticsTimingScope; // "legacy_mixed_not_per_run"
  bool statisticsFomIsRunMetric; // 固定false；不提供TARGET/FOM新指标
  std::uint64_t rootSeed, effectiveSeed, stride, historyOffset;
  std::uint64_t finalSeed, maximumHistoryDraws;
  long long finalPosition, finalPositionPre;
  long long batches, collisions, missedParticles;
  std::string sourceIdentity, weightWindowIdentity;
};
~~~

runId在序列内严格递增，identity只作审计，正确性依靠真实source/WW数据检查，不凭字符串认为数据合法。maxAdjointEnergyMeV每次均为物理值；Forward忽略spec中的伴随输运截止并恢复CDFixedSource未启用时的物理默认值20 MeV。两种role均非法时拒绝，不静默落入Forward。

CDCalMode新增public签名如下。this就是CalMode owner，不再让caller传一个可能不同的cCalMode；传入所有模型/工作对象均为引用。

~~~cpp
void InitializePreparedFixedSourceRuns(
    const FixedSourceSeriesSpec &series,
    CDNeutronTransport &neutron, CDPhotonTransport &photon,
    CDElectronTransport &electron, CDAceData &ace,
    CDFixedSource &fixed, CDMaterial &material, CDGeometry &geometry,
    CDParticleState &particle, CDTally &tally, CDBurnup &burnup,
    CDRNG &rng, CDCriticality &criticality, CDSampling &sampling,
    CDPerturbation &perturb);

FixedSourceRunReceipt RunPreparedFixedSource(
    const FixedSourceRunSpec &spec,
    const CDExternalSource &sourceDefinition,
    CDNeutronTransport &neutron, CDPhotonTransport &photon,
    CDElectronTransport &electron, CDAceData &ace,
    CDFixedSource &fixed, CDMaterial &material, CDGeometry &geometry,
    CDParticleState &particle, CDTally &tally, CDRNG &rng,
    CDCriticality &criticality, CDSampling &sampling,
    CDPerturbation &perturb);

void FinishPreparedFixedSourceRuns();
~~~

CalMode内部保存生命周期、下一个history offset、上一runId、只借用的owner地址、registry指针/shape签名、原physical cutoffs及default weight policy、固定WW topology/energy/WWP身份和输出句柄身份。它们是运行合同检查数据，不管理模型所有权。绑定的burnup虽不参与core也必须活到Finish；该受限入口不允许其内容改变。未初始化时Run不能靠拥有同名对象绕过Initialize。

Prepare保持private，签名为：

~~~cpp
void PrepareFixedSourceRun(
    const FixedSourceRunSpec &spec,
    const CDExternalSource &sourceDefinition, CDExternalSource &activeSource,
    CDNeutronTransport &neutron, CDAceData &ace,
    CDFixedSource &fixed, CDMaterial &material, CDGeometry &geometry,
    CDParticleState &particle, CDTally &tally, CDRNG &rng);
~~~

所需owner方法（其实现追加在对应现有cpp，不改旧数学函数）：

~~~cpp
// CDFixedSource
void ResetRunState();
void SetPreparedRun(long long histories, FixedSourceRole role,
                    double maxAdjointEnergyMeV);
void RebuildPreparedRunCutoffs(CDAceData &ace);
void CheckAndRecordPreparedSourceWeight(double sampledWeight);
void VerifyPreparedSourceWeights(long long expectedHistories) const;
FixedSourceWeightAudit GetPreparedSourceWeightAudit() const;
// CDNeutronTransport
void ResetPreparedRunCounters(double weightCutoff);
// CDTally / CDTallyData / CDStatisticsTester，各在自己的类中
void ResetRunScores(long long histories);       // CDTally
void ResetForRun(long long histories);          // CDTallyData
void ResetForRun(long long histories);          // CDStatisticsTester
// CDAceData
void ClearPreparedDerivedData();
void PrepareFixedSourceMode(FixedSourceRole role, int particleMode);
bool HasNonzeroPreparedFissionProduction(CDMaterial &material);
// CDParticleState
void ResetForFixedSourceRun();
void RebuildForFixedSourceRun(CDGeometry &geometry, CDMaterial &material,
    CDAceData &ace, FixedSourceRole role,
    double neutronEnergyCutoff, double neutronWeightCutoff);
// CDExternalSource
void CheckPreparedSourceDefinition(CDGeometry &geometry) const;
void ResetWorkingSourceFrom(const CDExternalSource &definition);
// CDRNG
void ConfigurePreparedType2Substream(std::uint64_t rootSeed,
    std::uint64_t historyOffset, std::uint64_t histories,
    std::uint64_t stride);
void FinishPreparedType2Substream();
// CDWeightWindow
void ClearPreparedNativeState();
void InstallPreparedNativeState(const FixedSourceWeightWindowSpec &spec,
    FixedSourceRole role, CDGeometry &geometry, CDCalMode &mode,
    CDNeutronTransport &neutron, double defaultWeightCutoff);
// Utility::Timer
void ResetForPreparedRun();
~~~

HasNonzeroPreparedFissionProduction只查询实际使用材料，按当前1-based群号1…G调用standard MG getter，不改GetMgCs算法；locator缺失/范围错误拒绝，不能把无法核查的产生项当零。CheckPreparedSourceDefinition按§3.1白名单检查已经由普通前端完成一次检查/规范化的canonical definition；不调用旧CheckSourceAndDistri二次规范化，不接受未完成解析的任意手工对象。active工作对象由Run局部创建，ResetWorkingSourceFrom只复制definition与清临时库。采样后检查和独立W0累计归CDFixedSource，不归测试driver。

粒子方法按state-ownership逐组显式清理，不使用外部逐字段赋值、placement-new或盲目复制上一run。Stage1三个helper的签名/原623行suite保持；普通CalcFixedSource按值source保持，仅加已进入prepared模型生命周期的冲突检查；从未进入新API的普通路径行为保持。

错误规格/状态采用新API内的invalid_argument/logic_error，driver捕获记录并非零退出；准备/输运中错误标Failed。旧RMC错误处理和普通输入检查不改，旧fatal错误仍由进程失败证据判定，不承诺从输运错误恢复继续。

## 3. 固定 Prepare 顺序

Initialize先注册已有FixedSource/Tally timer，保存默认physics/weight policy，建立Forward/WW-off基础状态；在禁止material sampling的受限profile下仍复用sampling.InitialBeforeCalculation一次，然后完整调用Stage1 InitializeFixedSourceModel一次。Init使用已解析合法输入N建立定义形状；首个run也必须经过同一Prepare，不能跳过清理。模型初始化时间由任务私有clock记录，不新增生产timer枚举。

1. **前置检查**：ModelReady/Finalized；绑定对象、registry/definition/WW shape与输出句柄有效；上次已Finalize一次、真实后代已排空、run timer不在running。验证role/NPS/source/WW/能量物理值/子流总范围；候选lower复制成已检查工作数据后才CLEAR。无效规格产生零条输运历史，旧结果不被抹掉。
2. **CLEAR**：FixedSource.ResetRunState（含起始权重audit清零/guard关闭）；Neutron计数；Tally.ResetRunScores（含Sum3/活动索引/StatisticsTester）；Ace.ClearPreparedDerivedData；Particle.ResetForFixedSourceRun；WW.ClearPreparedNativeState；本次FixedSource/Tally timer全量reset。删除旧sentinel，不能删除尚未完成真实后代。
3. **SET**：FixedSource.SetPreparedRun设置本次N/interval/restart=0/finish=-1/role/物理max；复制canonical source为active；启用FixedSource的prepared源权重guard；ConfigurePreparedType2Substream设置实际rng；本次WW身份/开关按spec。runId与sourceIdentity只记录，不替代物理检查。
4. **REBUILD**：Ace.PrepareFixedSourceMode在零数组上复用原伴随算法或F清空状态；FixedSource.RebuildPreparedRunCutoffs从物理MeV定位A群号；native WW复用ProcessWeightWindow生成三个界限并恢复正确weight policy；particle重建mat-nuc/geometry形状与XS cache/role/cutoffs。
5. **CHECK**：N与分母初始值、所有Score/Sum零、活动集合空、每槽bank空（core尚未加哨兵）、registry不变；三个role标志一致；A派生shape合法/F派生无残留；实际RNG状态匹配；真实native查询数据与role正确；min-energy cutoff保持旧语义。
6. **执行**：开启本次FixedSource timer，调用唯一ExecuteFixedSourcePrepared；core沿原时序采样/输运/WW/统计，不能另写loop。
7. **统计结束**：先VerifyPreparedSourceWeights(N)及核对completed=N、D=N=W0，再FinalizeFixedSourceRun一次；后验确认ProcessTally使用的实际D没有变化、finish=2、真实后代排空、RNG的历史段数量与N一致；停止timer并关闭本run的源权重/RNG guard；只在所有检查成功后返回receipt。采样权重失败时不得进入Finalize或返回成功receipt。

时间边界、旧StatisticsTester的两种时间来源及逐字段例外见§3.2。进程Output/HDF句柄不在half-run关闭；已有临时统计文本可能追加，测试私有快照分run保存，不把它冒充最终MLVR归档。

### 3.1 源形式、实际权重与分母（修订问题2）

**当前事实（330f091e）**：Source.h:49–51/454的`p_dWeight`只是源的一个系数。ExternalSource.cpp:25–43分别规范化FRACTION和BIASFRAC（未指定bias时替代为fraction），:50–57按bias选源并把粒子权重置为fraction/bias。SampleVariableFromDistri.cpp:8–16可以从WEIGHT变量分布重新写`p_dWeight`；SampleValue.cpp:11–18/25–31/38–73还能因子分布、离散/直方/插值的probability/bias比值修正粒子权重。SampleParticle.cpp:14–29在被接受的抽样尝试中再乘`p_dWeight`；ExternalSource.cpp:347–349完成普通抽样并保存source neutron weight。InitialBatchSource.cpp:295–298却直接把当前完成历史数赋给`p_dTotStartWgt`，:313–322另有自发裂变修正；ProcessTally.cpp:364–393实际以该值作D。故输入WEIGHT=1、每次实际w=1、D=N是三个不同命题；只断言最后一个会漏检前两个。

**确定采用的首版白名单**（不扩展任意权重归一化，也不改变KB04冻结规则）：

- OrdinarySource，恰好一个`p_vSource`，PARTICLE=1；固定POINT恰好三个有限坐标，固定正有限ENERGY、固定有限非零VECTOR且DIRECMIU=1。允许的显式变量只有FRACTION、BIASFRAC、PARTICLE、POINT、VECTOR、DIRECMIU、ENERGY、WEIGHT；WEIGHT可省略为默认1。ENERGY须落在固定MG模型可接受的物理能量范围。F0/F1/A0均已属于此子集；方向算法原有的Rand调用照旧保留，不能因定向而删抽样。
- `p_dWeight==1.0`；源原始FRACTION=1，BIASFRAC只允许未给定默认0或显式1。已规范化的外部源`p_vFraction`、`p_vBiasFrac`均须为单元素`[1.0]`，有限且相等。前端的普通一次规范化保留；本入口只读核验，不重新规范化，不能通过修正概率掩盖非法定义。
- 禁止所有用户DISTRIBUTION（包括看似恒1的WEIGHT分布、无偏能量分布、偏倚/依赖/子分布）。`p_vDitributions.size()==1`仅允许构造器保留的0号占位（ExternalSource.h:47–49），不能错误要求empty。所有源的分布名称/枚举/用户索引map、层级列表必须无绑定，`p_vDistriIndex`全部0；形状/标志不一致同样拒绝。
- 禁止多源、CELL约束、transform、surface/restart/Python/自发源、球/柱/体源和其余抽样形式；transform数组只保留0号占位，TIME=0/NORM=1等非启用默认状态必须一致。未定义的备用值不当成采样配置；canonical来自合法普通前端，接口不承担修复任意损坏C++对象。无偏分布和各向同性等可能守恒的形式也暂不开放，需新增证明/门禁后单独扩围，不能因此删普通路径功能。

**运行时实现边界**：新增一处生产hook在`SampleNeutronSource.cpp`的`CDFixedSource::SampleFixSource`普通源分支，当前:203之后、:204之前（共同的`#endif`之后）。此处`SampleSourceParticle`已返回最终源权重，尚未执行alive提前返回、几何丢失/零重要性kill（:224–265）、输运/WW；读`cParticleState.p_dWgt`，仅当FixedSource自己的prepared guard启用时调用`CheckAndRecordPreparedSourceWeight`。不写粒子、不抽随机数、不统计descendant；因此零得分/随后被kill的源history也经过检查一次。prepared禁用的普通路径只多一个恒false guard判断，旧抽样/权重/分母赋值完全保持；唯一623行transport suite不改。

`FixedSource.h`新guard有类内默认false（普通构造不依赖新Prepare）；`SetPreparedRun`启用guard；`ResetRunState`清计数、和、min/max及guard；三项新audit方法实现放`InitiateTrspt.cpp`，audit存储在`CDFixedSource`，轻量数据类型在`FixedSourceRunSpec.h`。正常样本要求`isfinite(w) && w==1.0`，**不设近似容差、不重标权重**；先记录实际采样次数，独立累加有限w，第一条有限样本设置min/max，此后更新极值。发现非单位/非有限值，记录nonUnitHistories、history序号和原值后立即抛runtime_error；NaN/Inf不加进有限和，错误日志明确partial audit。Run协调器catch后标Failed、记runId/sourceIdentity/失败阶段、禁止继续，调用者拿不到成功receipt；已有部分tally只能作为失败证据。

Finalize前`VerifyPreparedSourceWeights(N)`核验audit采样次数=N、nonUnit=0、min=max=1、实测W0=N；Run协调器另外核对completed=N及实际D=N；receipt在Finalize后保存实际D、同一audit和`unitSourceWeightsVerified=true`。W0绝不由N/D反向填充。为double精确单位累加，N≤2^53且仍受原bank整数容量更严格限制。成功后关闭guard；Failed系列不得重用。错误规格仍在CLEAR之前拒绝，保留旧有效结果。

**可观察门禁**：G2/G3/G4/G5/G6每段均检查N/D/W0、每history w和检查次数；G7a逐输入拒绝WEIGHT-variable/偏倚/依赖/多源/非单位源；G7b直接调用同一owner audit方法的无私有注入单元负例，补足严格白名单下无法自然到达的非单位/NaN运行时防线。采样hook及Run失败传播另做控制流检查；不把owner单测写成同进程输运证据。普通可用的加权/分布源须补旧/新回归，证明限制仅在prepared入口生效。

### 3.2 单run计时与旧统计FOM（修订问题3）

**当前事实（330f091e）**：OutputHeading.cpp:12/29注册并启动进程Total；OutputEnding.cpp:46停止，:82关闭句柄。StatisticsFunc.cpp:124–125的`p_vFoMTot`及:184/218的`p_vFlucFOM`使用这个进程时间。另一条链是CalcFixedSource.cpp:168/247–253的history interval，经ProcessStatisticsBin.cpp:16–20/43只对非零得分history累计`p_vTime`和largestTime，再由StatisticsFunc.cpp:177–180生成batch FOM，:331–358生成两个FOM诊断。因此旧统计计时是**混合口径**，不是每个字段都基于Total，更不是本轮T_MC。Timer.reset()在Timer.h:96–99遗漏recordTime，重置FixedSource/Tally不能修复Total的归属。

**确定方案**：不改上述公式或普通计时逻辑。新`RunPreparedFixedSource`在`PrepareFixedSourceRun.cpp`用独立`std::chrono::steady_clock`记录局部区间，不新增timer枚举，也不reset/stop进程Total。生产receipt字段及固定timingScope见§2；这些计时值不从旧FOM或Total倒推。

| 区间 | 起止与归属 |
|---|---|
| Prepare | t0：合法系列状态检查后、source/WW/spec前置检查及active副本创建之前；t1：Prepare所有CLEAR/SET/REBUILD/CHECK完成并启动本次FixedSource timer后、调用Execute之前。包含源校验/复制、WW三界安装、RNG配置；不含一次性Initialize和计划/WW文件读入 |
| transport | t1至t2（唯一Execute返回即刻）。包含源抽样、权重guard、history/batch/descendant/WW及原有循环内统计与诊断开销，不称为纯粒子飞行CPU时间；不为计时改原loop |
| tally finalize | t2至t3：权重/分母终检、唯一Finalize/ProcessTally、bank/role/RNG终检、关闭本run guards和停止本次FixedSource timer；t3在成功receipt组装与快照文件写出之前。包含本轮统计结束和必要收尾 |
| T_MC | `prepareSeconds + transportSeconds + tallyFinalizeSeconds`，在生产侧按这一加法赋`mcSeconds`；应与steady-clock区间t3−t0符合浮点舍入。Scope固定`prepare+transport+finalize`；用户称的T_tally_finalize即冻结设计T_finalize |
| 进程Total | 原来从Heading至Ending，覆盖初始化/所有run/间隔及输出，保持原语义。只作进程指标/只读观察证据，不能当run时长 |

保留旧core/ProcessTally内部原有stdout、临时统计文件等开销，随所属区间计入；排除caller在边界外的快照、正式Field写出/WW文件读取/外部算法。这与KB04 §12.1指定的文件交换排除项一致。失败只有带阶段的错误/部分耗时日志，无成功receipt和MC成功指标。观测GDB会增加墙钟；带GDB的数值门禁不用于性能排名。

`statisticsTimingScope="legacy_mixed_not_per_run"`和`statisticsFomIsRunMetric=false`随每个prepared receipt输出；driver在私有snapshot及导出的旧统计数据manifest附同样标签。若输出legacy统计文件，必须有对应run-id sidecar元数据；不把文件中的旧FOM复制为run FOM。Stage2不添加TARGET响应/RE_R/FOM计算，也不改普通OutputSummary/OutputEnding/HDF格式。

**精确比较例外**：内存仅`p_vTime`、`p_vLargestTime`、`p_vFoMPerCycle`、`p_vFoMTot`、`p_vFlucFOM`、`p_vFoMValueCheck`、`p_vFoMBehaviourCheck`及粒子`p_dSimulateTime`属于已有可证明的时间派生字段；HDF仅OutputTallyh5.cpp:210–217/261/283写出的5个相应后缀可例外，完整名单在test-plan §3.1。时间数组仍须正确reset/shape/归属；旧非run FOM必须保留值并标注口径。其余StatisticsTester的矩、Ave、RE、VoV、PDF、largest score、非时间诊断严格比较；禁止整个StatisticsTester忽略，禁止泛匹配所有含FOM或Time的键。

**门禁**：G2/G3/G4/G5/G6检查三段非负有限、求和恒等与每次timer正确停止；G2启用SCHECK的第二run在两次run之间加已记录的约100ms driver间隔，证明Total增加而该间隔在t0之外。G1普通输出/数值回归保持；比较器自测必须拒绝RE/Sum3/PDF/非时间check的人工损坏，仍保存并列出每个允许时间差异。时间域的允许舍入和不要求fresh等时详见test-plan，不能放宽物理容差。

## 4. Type2 子流

固定根种子s（正奇数，小于2^63）、stride S>0；第r次offset O为累计已成功完成的源历史数（初始可指定firstHistoryOffset）。Type2乘数a=3512401965023503517、加数0、模数2^63。定义：

~~~text
effectiveSeed(r) = s × a^(O × S) mod 2^63
第r次第h条源历史（h从0开始）：
  seed = s × a^((O+h) × S) mod 2^63
本次实际RNG：seed0=seed=effectiveSeed，position=0，position_pre=-1000
成功结束后 O ← O + N
~~~

只复用现有LCG/skip-ahead算法，不另造RNG。先以除法检查(O+N)≤floor(2^61/S)，并检查加法/乘法溢出后才计算skip。该乘数mod8=5，奇seed的周期是2^61，不能用模数2^63当周期。精确模运算证据在logs/rng-period-analysis.json（属于只读数学分析，不是MC通过）。

GetRandSeed的GK/CK/ISEED目前是function static（StrideRNG.cpp:86–88）。将其移到LCG63_0 owner，新增cache valid；Configure和RNG状态设置/copy失效缓存。valid且position连续时沿旧公式，否则重算；相同单实例普通路径的序列必须Gate1完全一致。继承此实现的其它普通RNG仍需原回归，prepared仅允许Type2。

prepared guard在每次GetRandSeed开始重置本源history draw count；Rand（以及经它实现的SkipRand）包括source、碰撞、WW和全部后代的每次draw均计数。允许最多S次，第S+1次在产生/使用数值前拒绝，整个run失败而不继续分配重叠段；不因超stride改种子/扩大S。普通运行guard关闭，不改变旧抽样次序。每次确认GetRandSeed次数=N，并保存最大学史用数与最终seed/position/pre。

root17/stride100000时offset0、1000、3000、4500的有效seed分别为17、2131104056799056913、2677826766351137809、1970214766957607441。一般effective seed超过2^53；旧RNG卡经double解析可能丢失整数。fresh test driver按stoull完整读取十进制seed，使用既有SetSeed0/SetSeed/SetStride/SetPosition/SetPositionPre设置实际ORNG，然后正常一次RunCalculation。测试输入RNG卡仍为安全小整数；不改普通parser，不把大整数写进卡片造成oracle失真。其余源/角色/WW/N通过等价普通输入设置。

## 5. 实际拟改文件、理由、回滚

| 文件（均相对RMC） | 拟改动 |
|---|---|
| src/CalMode.h | 三个受控public入口、private Prepare、生命周期/非拥有绑定/固定policy；旧helper保留private |
| src/PrepareFixedSourceRun.cpp（新增） | Initialize/Prepare/Run/Finish协调、失败传播、D/W0终检、独立三段计时和receipt口径；无history loop、无模型owner |
| src/FixedSourceRunSpec.h（新增） | 上述轻量spec/receipt/role/source-weight audit，含三段时长和legacy统计标签；无parser/模型/资源owner |
| src/CalcFixedSource.cpp | 普通入口prepared生命周期冲突检查；原初始化/623行suite/Finalize/普通tail不重写 |
| src/FixedSource.h、src/InitiateTrspt.cpp | FixedSource reset/set/cutoff及源权重guard/audit/终检方法；NeutronTransport计数方法也追加在InitiateTrspt.cpp；不再次InitiateAll |
| src/SampleNeutronSource.cpp（本次补入清单） | SampleFixSource普通源采样返回后的prepared专用权重检查hook；不改抽样算法、不写粒子、不动core |
| src/NeutronTransport.h | 声明计数/default policy恢复接口 |
| src/Tally.h、src/InitiateTally.cpp | 新run-score reset遍历既有registry；原InitiateTally不改 |
| src/TallyData.h、src/TallyData.cpp | 包含Sum3与索引的完整reset；旧SetZero不改 |
| src/StatisticsTester.h、src/StatisticsFunc.cpp | 独立ResetForRun复用ReSize并补齐run scalar/工作集合；保持原统计公式 |
| src/AceData.h、src/TreatAdjointMaterial.cpp | 派生数据清理、role重建及非零裂变检测；旧伴随算法/原数据读取不改 |
| src/ParticleState.h、src/ParticleStateFun.cpp | owner内显式瞬态清理/按原shape重建；不复制模型 |
| src/ExternalSource.h、src/ExternalSource.cpp | canonical校验及干净active source；旧普通copy semantics与抽样算法不改 |
| src/RNG/RNG.h、src/RNG/StrideRNG.cpp | owner skip cache、Type2子流配置、prepared用数检查；旧LCG公式保留 |
| src/WeightWindow.h、src/WeightWindows.cpp | 本次native三界安装/关闭和真实policy切换；不改split/roulette/查窗算法 |
| src/Utility/Timer.h | 新prepared全量reset；旧普通reset保持 |
| CMakeLists.txt | 在全部feature定义之后新增受限测试子目录；普通RMC源/链接及原tests注册保持，细节见§5.1 |
| tests/prepared_fixed_source_lifecycle/CMakeLists.txt（新增） | 派生RMC源列表，精确排除main.cpp，加driver/globals，复用libraries/编译属性，注册新测试 |
| tests/prepared_fixed_source_lifecycle/driver.cpp（新增） | 正式API driver，fresh入口、receipt/snapshot口径、源audit单测模式；不定义进程全局对象 |
| tests/prepared_fixed_source_lifecycle/globals.cpp（新增，本次补入清单） | 测试executable独占的全局对象定义，精确清单/宏见§5.1；普通RMC不编入 |

tests/CMakeLists.txt从原拟改清单移除：新子目录由根CMake末尾显式添加，既有测试注册不变。Source.h/SampleParticle.cpp/SampleVariableFromDistri.cpp/SampleValue.cpp/InitialBatchSource.cpp/ProcessTally.cpp/OutputTallyh5.cpp/OutputHeading.cpp全部只读；不修通用源或统计公式。

Output.h/OutputEnding.cpp只读，不新增生产文件归档协议；Prepare在CalMode检查已有公开句柄，driver输出任务私有snapshot。RunCalculation.cpp/main.cpp不改；不建立src/MLVR。实现中若发现额外owner状态要求更改此表之外生产文件，应先补具体原因与审批记录。

批准后先在私有副本重建330f baseline，保存源manifest、编译选项和Gate1原输出，之后才改生产树。本任务changes.diff只对330f包含Stage2增量；新增untracked生产文件单独git diff --no-index /dev/null保存并加入清单，不以空git diff漏报。logs/stage1-start.diff为已提交Stage1原补丁，不算本任务改动。

回滚不reset/checkout：保存每个修改文件的330f原文/sha；只在无他人新改动且hash吻合时逐文件恢复本任务旧内容，新增文件也先验证是本任务创建，再移到任务证据目录。若发现并行改动，停止由用户处理。全部禁止commit/push、参考值/核数据库更新；Gate失败保留原文并定位，不能扩大物理容差。

### 5.1 测试target和全局定义的唯一所有权（修订问题1）

**当前事实**：CMakeLists.txt:661–673通配并合并生产源，:674–675建立RMC并链接`${libraries}`；RNG静态库在:629–632另行加入，Python可选库在:637–653。main.cpp:28–55同时定义入口依赖的13个无条件全局对象和2个条件对象。只排main而不补定义会缺符号，保留main又加driver会产生两个main；把测试globals放src/则会被普通glob重复编入。

**唯一选择**：原`main.cpp`完全不改。新增测试专用`tests/prepared_fixed_source_lifecycle/globals.cpp`作为测试target的全局定义translation unit，driver只含入口和局部模型。两个executable互相不链接，各有且仅有自己的main及以下定义：

| 定义（保留main中的顺序/namespace） | 普通RMC唯一TU | RMCPreparedLifecycle唯一TU | 条件 |
|---|---|---|---|
| `CDOutput Output`；`CDMeshInfo OMeshInfo`；`CDXSParaTableVec OXSParaTableVec` | src/main.cpp:28–30 | tests/prepared_fixed_source_lifecycle/globals.cpp | 无 |
| `CDWeightWindow OWeightWindow`；`CDStatus OStatus`；`Utility::RMCTimer OTimer` | src/main.cpp:31–33 | 同上 | 无 |
| `CellVector cellVec`；`CDPTRAC OParticleTracker`；`RMC::Control OController` | src/main.cpp:34–36 | 同上 | 无 |
| `CDRNG ORNG`；`CDCalMode OCalMode` | src/main.cpp:37–38 | 同上 | 无 |
| `RMC::IO::Logger OLogger`、`OProcLogger` | src/main.cpp:39–43 | 同上，保留namespace | 无 |
| `CDPythonInterface OPythonInterface` | src/main.cpp:48–51 | 同上，含相同PythonInterface头 | `USE_PYTHON_API` |
| `CDParallel OParallel` | src/main.cpp:53–55 | 同上 | `USE_MPI` |

头文件取main的生产类型声明所需集合：CalMode.h、Input.h、PhotonTransport.h、ElectronTransport.h、Utility/Timer.h、Utility/IO/Logger.h、Status.h、Control/Control.h，Python头保留原guard。不得在driver或任何header再定义这些对象，也不include main.cpp。OMP/AIS没有额外main全局定义；类型布局仍必须服从同一生产宏，不能为driver局部#undef。

其它extern沿原TU/库定义一次：`Data::DataBase::{indexFilesPath,DataPath,hdf5Directory,readHDF5}`在Data/Data.cpp:14–20；`Data::PhotonAtomicDataBase::{with_hdf5,elements,elements_index}`在Photon.cpp:549–552；`RMC::Config::Parallel::isMaster`在Utility/Config/Parallel.cpp:4–12（仅USE_MPI）；BurnupConstants.cpp:7/116/118/130/189的五个reaction/Q映射、NuclideConstants.cpp:8的MASS_ELEMENT随生产源；DepthOut/DepthRpt在DEPTH/DepthMain.cpp:17随Depth静态库。完整extern搜索在logs/design-revision/extern-inventory.json；这些符号绝不复制到globals.cpp。AIS/并行/Python依赖由原库/宏机制管理，本target不自行提供假stub。

**CMake边界（已按批准方案实现）**：根CMake在所有add_definitions完成后、末尾`cmake_policy(POP)`之前添加新子目录，条件为test=ON、CMAKE_SYSTEM_NAME=Linux、mpi/MPI_USE/openmp/OMP_USE/ais/pythonapi/USE_PYTHON_API全部关闭；不移动原tests子目录或修改其CTest注册。这样也继承:698之后的DEBUG_ATTACH/BACKTRACE/CATCH_ERROR等最终目录宏。子CMake用`get_target_property(... RMC SOURCES)`取得原列表的局部副本，核实绝对路径`${PROJECT_SOURCE_DIR}/src/main.cpp`恰好出现一次，再`list(REMOVE_ITEM ...)`仅排除此文件；不重新glob另一份生产清单，不修改原`source`变量或RMC target。加且仅加driver.cpp、globals.cpp各一次；生产新增Prepare cpp由原src glob取得，RNG/Depth仍只通过`${libraries}`链接而非再编入其源码。

测试target继承同目录C++标准、flags、include/link目录，并显式复用RMC target的COMPILE_DEFINITIONS/COMPILE_OPTIONS/INCLUDE_DIRECTORIES与`${libraries}`；不复制旧binary的flag猜测配置。普通RMC的add_executable、target_link_libraries、install保持原样。特殊MPI/OMP/AIS/Python构建不会创建本测试target；对应生产宏仍原样传给普通RMC。globals中的条件定义与main一致是防漂移约束，不表示本测试或prepared已支持这些模式。

driver使用全局`OCalMode`，另以明确名字`runRng`持有并传递实际RNG（对应main.cpp:60的局部ORNG）；全局`::ORNG`必须链接存在，但不得误当作该run RNG。main.cpp:142–162的输入/输出前端与进程收尾由driver调用同一生产方法；计算点persistent仅调用三个公开lifecycle API，fresh仅普通RunCalculation。不得借global副本复制模型或另造loop。

**验收G0**：configure导出compile_commands，逐生产TU比较两个target的宏/包含目录/选项（仅object/output路径可不同）；检查target源表/链接map排除了原main、globals仅一个object、所有列出的全局定义唯一，`nm -C --defined-only`核对最终两个executable各一份main和无条件globals；非main的extern仍由原TU/库提供。链接不得存在重复/未解析符号。test=OFF下新target不存在且普通源集合只增加已批准的生产API文件；不支持宏配置不注册此target，已有普通RMC构建继续正常。须同时构建RMC和RMCPreparedLifecycle并跑G1普通回归，不能仅凭文档宣称链接已通过。

**新增范围与风险**：相比修订前，生产多触及SampleNeutronSource.cpp一处guard；测试新增globals.cpp，移除不必要的tests/CMakeLists.txt修改。前者的普通分支/RNG不变由G1含加权源回归验证；后者有与main清单漂移风险，由extern inventory、源列表/符号唯一性检查及宏比较门禁约束。测试TU定义重复于另一个executable的main是明确隔离的构建安排，不在同一链接单元内重复定义。上述29文件已由最新正式授权批准并实现；当前补丁、构建与门禁结论见README §2/§4。


## 6. 2026-10-11 实施对应与具体化

用户已正式批准§5全部29文件及G0/Gate1–7，原文在logs/implementation/user-authorization.txt；此前审批说明是设计历史。本版没有扩大文件清单。实际补丁为changes.diff与new-files.diff；实施结论只在README §4维护。

- 生产入口实际位于CalMode.h:42起，协调实现PrepareFixedSourceRun.cpp；Stage1唯一执行核心没有复制或改写。全局owner预约在Closed/Failed后仍保留，禁止第二模型和普通入口重新初始化。
- `sourceHistories`实际上限为`INT_MAX/2`，兼顾原bank容量的整数转换；受限源能量还须位于固定MG群范围。receipt增补`maximumHistoryDraws`及`measuredMcSeconds`，不增加新物理评价量。
- 源审计成功终检后显式关闭guard；普通采样仅多一个默认false的分支。实际非法权重由owner单元负例验证，运行中失败传播由真实stride超额验证；两种证据不混同。旧parser只允许标量WEIGHT，`WEIGHT=D1`在原版即语法失败，因此没有将其报告为普通输运正例。用户分布负例通过ENERGY、方向依赖/子分布及FRACTION/BIASFRAC覆盖；WEIGHT绑定另用公开源definition对象负例。
- StatisticsTester仅在已有选定诊断bin时调用ReSize(N)，防止原本空的未启用PDF向量被新建；清除本run旧统计临时文件，避免未导出HDF时的跨run污染。旧统计公式和普通reset不改。
- 未修改330f baseline确认：`TallyCellByTL.cpp:205–215`的按能群cell SCHECK可访问空volume数组并崩溃。该文件不在授权清单，保持原样；prepared显式拒绝这个组合。测试仍保留全30群cell/mesh物理数据，同时增加无ENERGY的总通量cell诊断（按能群cell CHECK=0），完整检验RE/VoV/PDF等。失败输入、baseline堆栈及新入口拒绝证据均保留，不能把本任务当作该旧缺陷的修复。
- 产生项检查覆盖全部已加载核素，是使用材料核素的保守超集；不改变raw数据。输出/HDF对象地址及主输出FD须保持有效；Total继续计时，FixedSource/Tally两个run计时器在成功和失败收尾停止。
- `RMCPreparedLifecycle`调用真实public API。fresh模式在普通输入解析后通过公开CDFixedSource population及原CheckFixedSource设置N（小于输入卡最小101的N=100也如此），再走普通RunCalculation；不调用新Prepare，不跳过完整初始化。精确uint64 seed由公开RNG setter设置，避免原double parser损失精度。

模型definition比对是本入口的防误用检查，不是允许caller修改其余模型内部字段的许可；所有Geometry/Material/rawXS/tally/WW定义必须固定。复杂几何、材料、非零裂变及未列的运行选项仍不借本次H2O门禁外推。没有TARGET/Field API或新FOM指标。


测试输出隔离补充：普通OutputTallyh5含创建一次的table及条件字段，不能用累计文件充当一张新快照。测试driver在第二次及以后导出前仅清自己的旧Tally HDF组，再调用原writer；global Output及HDF句柄身份保持。生产lifecycle API不承担Field/HDF导出，本次没有更改OutputTallyh5.cpp。原失败与修正后逐轮HDF/PDF证据见test-plan §5。


截止值补充核对：初次cutoffs检查发现Forward中未启用的伴随上限保留了spec的30 MeV，而普通Forward字段默认20 MeV。虽此前逐history数值已相等，仍在已批准的SetPreparedRun内明确恢复20 MeV；Adjoint继续将本次物理30 MeV定位为内部群1，回Forward恢复20而不是重复转换群1。最终全量gates-04同时严格比较这些字段，原差异记录保留在logs/cutoffs。
