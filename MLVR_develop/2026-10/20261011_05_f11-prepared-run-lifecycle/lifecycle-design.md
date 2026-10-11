# Stage2 具体实施方案（待批准）

导航：§1 合同与范围；§2 C++接口；§3 Prepare顺序；§4 RNG；§5改动文件/回滚。设计唯一基线为知识库04 §3.3/§5/§14。这里只细化Stage2，不修改冻结规则。

## 1. 合同与范围

caller在一个连续栈帧持有完整模型与工作对象。CDCalMode提供一次初始化、一次run、结束三个public入口；每次run内部清理并调用原私有执行core，不接受caller声明“我已经初始化”的token。模型、raw核数据、tally definition/registry在Initialize后固定且不得复制/移动；每个run有自己的active source和清零统计。接口只允许完整half-run间切换，执行中不能修改source/WW。

第一批生产prepared入口限定standard MGACE、neutron-only、Linux串行、RNG Type2、普通现有单位初始权重源、Cartesian Type1/track-length/Energy=-1/Normalize=1、native track-mesh WW。MG群数随固定模型，首批门禁使用30n/12p H2O。source/role/NPS/有效RNG段/native lower可变；geometry/material/rawXS/群/mesh/WWP保持。Bootstrap/K循环不属于这个入口。

prepared入口明确拒绝：CE/MG-HDF5、MPI/OMP/AIS、photon/coupled、burnup/kinetics/perturb/material sampling/TMS、restart/surface-source/停止时间/TIME_REDUCE、Python源、spontaneous-fission源、MCNP/point/cell WW/WWG、CAP/FET/cs等未覆盖tally功能以及特殊weight policy。不删除或限制普通CalcFixedSource的这些已有分支。固定NPS应可由原单run/batch机制完整结束，且已有bank分配的int容量换算必须无溢出，不新增batch参数。

首次支持边界不包含非零裂变产生项。读取原数据后检查使用材料中各核素/群的νΣf；任意非零（或非有限非法数据）拒绝prepared执行，不修改raw数据/不关闭裂变来通过。一般裂变材料需单独非零贡献F→A→F→A门禁通过再放开。

私有生命周期为 Uninitialized → ModelReady → Preparing → Executing → Finalizing → Finalized →（Preparing…）→ Closed，及 Failed。对未初始化、重入、wrong-owner和非法规格先拒绝，保留已有合法结果；CLEAR之后任何失败将序列标Failed并记录阶段，禁止继续或复用已分配RNG段。Finish只标记本入口Closed，不关闭进程资源；初始化成功后同一批对象不能再次全初始化，也不允许在该进程建立第二个prepared模型或转普通入口重初始化。由于全局WW/Output，只允许一个活动序列；不引入可持有第二模型的Session/Manager。

## 2. 拟定 C++ 接口

以下是待批准的新增签名，不是当前已经存在的API。数据定义位于根src/FixedSourceRunSpec.h，C++类型使用既有long long历史计数和uint64种子。

~~~cpp
enum class FixedSourceRole { Forward, Adjoint };

struct FixedSourceSeriesSpec {
  std::uint64_t rootSeed;
  std::uint64_t stride;
  std::uint64_t firstHistoryOffset;
};
struct FixedSourceWWSpec {
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
  FixedSourceWWSpec weightWindow;
};
struct FixedSourceRunReceipt {
  std::uint64_t runId;
  FixedSourceRole role;
  long long requestedHistories;
  long long completedHistories;
  double normalizationDenominator;
  std::uint64_t rootSeed, effectiveSeed, stride, historyOffset;
  std::uint64_t finalSeed;
  long long finalPosition, finalPositionPre;
  long long batches, collisions, missedParticles;
  std::string sourceIdentity, weightWindowIdentity;
};
~~~

runId在序列内严格递增，identity只作审计，正确性依靠真实source/WW数据检查，不凭字符串认为数据合法。maxAdjointEnergyMeV每次均为物理值；Forward忽略伴随输运截止但恢复保存的物理默认值。两种role均非法时拒绝，不静默落入Forward。

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
void InstallPreparedNativeState(const FixedSourceWWSpec &spec,
    FixedSourceRole role, CDGeometry &geometry, CDCalMode &mode,
    CDNeutronTransport &neutron, double defaultWeightCutoff);
// Utility::Timer
void ResetForPreparedRun();
~~~

HasNonzeroPreparedFissionProduction只查询实际使用材料，按当前1-based群号1…G调用standard MG getter，不改GetMgCs算法；locator缺失/范围错误拒绝，不能把无法核查的产生项当零。CheckPreparedSourceDefinition检查restricted ordinary neutron source、合法distribution、有效weight；可以在验证副本上复用旧CheckSourceAndDistri，不对canonical/active数据重复归一化。有效初始权重不仅要求SOURCE WEIGHT=1，还要求Fraction/BiasFrac不引入非单位偏倚。active工作对象由Run局部创建，ResetWorkingSourceFrom只复制definition与清临时库。

粒子方法按state-ownership逐组显式清理，不使用外部逐字段赋值、placement-new或盲目复制上一run。Stage1三个helper的签名/原623行suite保持；普通CalcFixedSource按值source保持，仅加已进入prepared模型生命周期的冲突检查；从未进入新API的普通路径行为保持。

错误规格/状态采用新API内的invalid_argument/logic_error，driver捕获记录并非零退出；准备/输运中错误标Failed。旧RMC错误处理和普通输入检查不改，旧fatal错误仍由进程失败证据判定，不承诺从输运错误恢复继续。

## 3. 固定 Prepare 顺序

Initialize先注册已有FixedSource/Tally timer，保存默认physics/weight policy，建立Forward/WW-off基础状态；在禁止material sampling的受限profile下仍复用sampling.InitialBeforeCalculation一次，然后完整调用Stage1 InitializeFixedSourceModel一次。Init使用已解析合法输入N建立定义形状；首个run也必须经过同一Prepare，不能跳过清理。模型初始化时间由任务私有clock记录，不新增生产timer枚举。

1. **前置检查**：ModelReady/Finalized；绑定对象、registry/definition/WW shape与输出句柄有效；上次已Finalize一次、真实后代已排空、run timer不在running。验证role/NPS/source/WW/能量物理值/子流总范围；候选lower复制成已检查工作数据后才CLEAR。无效规格产生零条输运历史，旧结果不被抹掉。
2. **CLEAR**：FixedSource.ResetRunState；Neutron计数；Tally.ResetRunScores（含Sum3/活动索引/StatisticsTester）；Ace.ClearPreparedDerivedData；Particle.ResetForFixedSourceRun；WW.ClearPreparedNativeState；本次FixedSource/Tally timer全量reset。删除旧sentinel，不能删除尚未完成真实后代。
3. **SET**：FixedSource.SetPreparedRun设置本次N/interval/restart=0/finish=-1/role/物理max；复制canonical source为active；ConfigurePreparedType2Substream设置实际rng；本次WW身份/开关按spec。runId与sourceIdentity只记录，不替代物理检查。
4. **REBUILD**：Ace.PrepareFixedSourceMode在零数组上复用原伴随算法或F清空状态；FixedSource.RebuildPreparedRunCutoffs从物理MeV定位A群号；native WW复用ProcessWeightWindow生成三个界限并恢复正确weight policy；particle重建mat-nuc/geometry形状与XS cache/role/cutoffs。
5. **CHECK**：N与分母初始值、所有Score/Sum零、活动集合空、每槽bank空（core尚未加哨兵）、registry不变；三个role标志一致；A派生shape合法/F派生无残留；实际RNG状态匹配；真实native查询数据与role正确；min-energy cutoff保持旧语义。
6. **执行**：开启本次FixedSource timer，调用唯一ExecuteFixedSourcePrepared；core沿原时序采样/输运/WW/统计，不能另写loop。
7. **统计结束**：FinalizeFixedSourceRun一次，检查completed=N、实际分母=N（单位有效初始权重且无自发源）、finish=2、真实后代排空、RNG的历史段数量与N一致；停止timer，FinishPreparedType2Substream关闭run guard；返回receipt并允许caller读取本次统计。

时间覆盖按阶段分别记Prepare/core/Finalize。原普通路径timer顺序不动；本阶段不实现F11目标响应/FOM API。StatisticsTester的已有FOM使用Total墙钟，所以它的时间/FOM与fresh可以不同，原始physics数组不可不同。进程Output/HDF句柄不在half-run关闭；已有临时统计文本可能追加，测试私有快照分run保存，不把它冒充最终MLVR归档。

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
| src/PrepareFixedSourceRun.cpp（新增） | Initialize/Prepare/Run/Finish协调和检查；无history loop、无模型owner |
| src/FixedSourceRunSpec.h（新增） | 上述轻量spec/receipt/role；无parser/模型/资源owner |
| src/CalcFixedSource.cpp | 普通入口prepared生命周期冲突检查；原初始化/623行suite/Finalize/普通tail不重写 |
| src/FixedSource.h、src/InitiateTrspt.cpp | FixedSource reset/set/cutoff方法；NeutronTransport计数方法在现有相关cpp追加；不再次InitiateAll |
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
| CMakeLists.txt、tests/CMakeLists.txt、tests/prepared_fixed_source_lifecycle/CMakeLists.txt（新增）、driver.cpp（新增） | 受限test target及正式API driver；既有reference/测试模型保持 |

Output.h/OutputEnding.cpp只读，不新增生产文件归档协议；Prepare在CalMode检查已有公开句柄，driver输出任务私有snapshot。RunCalculation.cpp/main.cpp不改；不建立src/MLVR。实现中若发现额外owner状态要求更改此表之外生产文件，应先补具体原因与审批记录。

批准后先在私有副本重建330f baseline，保存源manifest、编译选项和Gate1原输出，之后才改生产树。本任务changes.diff只对330f包含Stage2增量；新增untracked生产文件单独git diff --no-index /dev/null保存并加入清单，不以空git diff漏报。logs/stage1-start.diff为已提交Stage1原补丁，不算本任务改动。

回滚不reset/checkout：保存每个修改文件的330f原文/sha；只在无他人新改动且hash吻合时逐文件恢复本任务旧内容，新增文件也先验证是本任务创建，再移到任务证据目录。若发现并行改动，停止由用户处理。全部禁止commit/push、参考值/核数据库更新；Gate失败保留原文并定位，不能扩大物理容差。
