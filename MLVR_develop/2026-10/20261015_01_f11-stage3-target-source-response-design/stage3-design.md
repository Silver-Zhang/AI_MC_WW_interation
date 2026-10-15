# F11 Stage 3 具体实施设计（待用户批准与 Claude 独立审查）

本文件是实施提案，不是已实现接口。源码依据为 RMC `4810694b7a99dfc3ad7d27f7d443814f511f4829`；下述行号均按该提交实际工作树读取。唯一冻结设计为知识库04 §6/§7/§9/§14，本任务不修改04。G1用户原话及后续对话授权见 README §3。测试判据见 [test-plan.md](test-plan.md)。

## 1. 具体取舍与边界

1. 在现有 `CDInput / CDCalMode / CDExternalSource / CDSource / CDTally` 扩展；配置为小值结构，不建 Session、Controller 或 `src/MLVR/`，不复制固定源/源抽样循环。
2. parser只保留值、ID与输入来源；真正 TARGET/群/score 索引在 Stage2 一次初始化后，向**实际被绑定的 CDTally**解析。普通 `RunCalculation` 的按值对象不能被 parser 偷存地址。
3. 保留 Stage2 严格点源入口。只新增受 TARGET 约束的生成伴随源类别，所有有效初始权重仍逐历史严格等于1。**本阶段不开放一般分布式 Forward 源**；EXTERNALSOURCE 仍是唯一真实 Forward 定义，首版沿用 Stage2 点源限制。
4. 保留独立、不可变的 F/A canonical 源，每run继续用已有深值工作副本。配置不是源/模型的 owner。源的结构profile（Point/Target）与Stage3能量表示policy分开，后者不豁免合法性检查。
5. 在 `SumUpTally` 清除临时 mesh score 前聚合一次完整 history 的目标标量；独立累计 S1/S2/N，不增加 tally registry，不修改原 scorer、TallyData 或统计数学。
6. CLI 能解析 MLVR，但 Stage3 不运行完整调度：普通 executable 遇 MLVR 明确报告 scheduler 尚未实现，不静默按 Bootstrap N 运行普通 fixed-source。专用测试 driver 调真正生产 parser、prepared lifecycle 和 TARGET API；Stage4–6 不提前实现。
7. Stage3绑定源存在必须审批的局部适配：F/A均按完整物理边界检查；F按其映射群中心缓存速度，A按抽中群中心初始化速度。另采用下述保守 TARGET 几何支持范围。这些是 Stage3 提案的显式范围，不宣称已获生产修改批准。

## 2. 当前函数级链与扩展位置

| 当前源码位置 | 已核查事实 | Stage3 接入 |
|---|---|---|
| `src/main.cpp:142,155`；`ReadInputBlocks.cpp:134–163,376–379` | 读全部 block 后统一 `CheckInpBlock`，然后运行 | 新 MLVR block；旧 CheckInpBlock 前完成冲突检查及 Bootstrap N 赋值 |
| `CheckInpBlock.cpp:85–95`；`CheckTransport.cpp:52–70` | 旧固定源检查已经需要粒子数 | 不延后到输运时才填写 N |
| `ReadFixedSourceBlock.cpp:52–56,147–151,209–224` | POPULATION、SEED、ADJOINT 显式出现未有专用持久标记 | 增加 presence 记录，不能凭最终默认值判断冲突 |
| `ReadInputBlocks.cpp:292–296`；`ReadWeightWindow.cpp:52–53` | 顶层ADJOINT与WW各子卡有独立入口 | 记录显式冲突，即使最终 enabled=false 也不能漏过 |
| `RunCalculation.cpp:6–13,83–88` | geometry/material/particle/tally等按值，外源按引用；固定源分支无条件走普通包装入口 | parser不捕获这些对象地址；MLVR dispatch guard |
| `CalcFixedSource.cpp:78–84,115–140,142,773–775` | 初始化→唯一执行核心→一次 ProcessTally | 完整保留，不增加循环或新的 ProcessTally 调用 |
| `PrepareFixedSourceRun.cpp:167–208,211–227,230–321` | Stage2 owner/registry/model/output身份、CLEAR/SET/REBUILD、逐run计时及失败无receipt | 增加一次 TARGET绑定和每run前置校验；复用现有状态机 |
| `InitiateAll.cpp:131,156`；`InitiateTally.cpp:60–69`；`SingleTally.cpp:875–890` | MGACE加载后才展开Energy=-1、mesh数据长度和起始偏移 | TARGET实际群/score绑定放在完整初始化之后，不重复初始化 |
| `ReadExternalSourceBlock.cpp:30–47,54–66,87`；`CheckSourceAndDistri.cpp:6–30` | 源组件、分布建立，统一规范化和参数映射一次 | 构源工厂复用同一检查/初始化函数 |
| `ExternalSource.cpp:25–57,346–351,552–586` | source分数/偏倚比影响权重；现有严格点源白名单；工作源复制 | 保留点源检查；新增生成源专用结构验证；canonical只初始化一次 |
| `SampleParticle.cpp:24–50,57–86`；`SampleValue.cpp:25–45` | 分布可改变权重；无CELL不拒绝重采样；速度初始化早于MG转换 | 只允许工厂白名单；Stage3绑定源专用能量表示适配 |
| `SampleNeutronSource.cpp:180–205,235–280` | 抽样后已有严格单位权重audit；之后定位/importance检查，再物理能量转群号 | 保留audit；generated定位非法必须失败，不能kill后继续成功 |
| `ReadMeshTallyCard.cpp:258–294`；`MeshFun.cpp:297–300,479–485`；`ScoreMeshTally.cpp:39–117` | uniform返回长度，heter Normalize=1返回长度/V；能群与Tot分别计分 | 只读使用中央体积转换，不改计分 |
| `CalcFixedSource.cpp:218–236,253` | 每源历史的全部中子后代bank处理完，才SumUpTally | 在此已存在的history边界统计，不按后代计N |
| `SumUpTally.cpp:130–132`；`TallyData.cpp:45–51` | mesh临时score先统计，后清除 | 在132前加受控目标聚合，包含r=0 |
| `ProcessTally.cpp:330,364–365,389–393`；`InitialBatchSource.cpp:295–298` | 使用实际D=p_dTotStartWgt；现代码赋D=完成N | Stage2逐history权重audit和N=D=W0保持；TARGET不另猜分母 |

拟调用关系：

```text
ReadInputBlocks → ReadMLVRBlock → CheckMLVRInput → 原CheckInpBlock
    ├─ 普通输入 → 原RunCalculation → 原CalcFixedSource（不变）
    └─ MLVR输入 → 普通RunCalculation明确拒绝未开放scheduler

Stage3测试driver / 后续调度调用者
  InitializePreparedFixedSourceRuns（原API、一次）
  BindPreparedMLVRTarget（新增；仅ModelReady且首run前）
    ResolveMLVRTarget → 验证完整目标体积 → 编译indices/coefficients
    BuildMLVRForwardSource（复制原定义并绑定派生速度）+ BuildTargetAdjointSource → 完整结构验证 → 一次发布绑定
  RunPreparedMLVRFixedSource(spec, owners...)（新增；无循环）
    选对应canonical → 原RunPreparedFixedSource
      原model/WW/owner检查 + TARGET/source/role检查（CLEAR前）
      原Prepare → ResetRunScores + 按role开启目标统计
      原Execute → 完整history → SumUpTally → AccumulateTargetHistory → 原SumTallyBin
      原FinalizeFixedSourceRun（ProcessTally一次）→ FinalizeTargetResponse → receipt
  FinishPreparedFixedSourceRuns（原API）
```

## 3. 数据、所有权与接口

新增 `src/MLVRConfig.h`，仅标准头文件与值结构，兼容当前 C++11/14，不依赖C++17 optional：

```cpp
struct MLVRTargetInput {
  int meshTallyId = 0;
  std::vector<std::array<int,6>> regions; // 一基闭区间6元组
  std::vector<std::array<int,2>> groups;  // 低到高物理群闭区间
};
struct MLVRConfig {
  bool enabled = false;
  int iterations = 0;
  long long bootstrapNps = 0, adjointNps = 0, forwardNps = 0;
  std::uint64_t rootSeed = 0;
  MLVRTargetInput target;
  std::string command, workdir;
};
```

同头文件定义 `MLVRFieldLayout`（整张Field的展开xyz边界、flat索引规则、Vi/ci、G+1完整物理边界、G个中心、tally群slot及原定义标记）、`MLVRResolvedTarget`（该layout、去重I/J、VT、只读score indices与α、几何认证结果、canonical identity）、`MLVRTargetResponseResult`（下面统计字段和status）。记录原输入使用Energy=-1，因为初始化后此数组已被替换。**不存p_vScore裸指针**，存经过越界检查的整数偏移，使用实际owner在每history取值。

| owner | KEEP / CLEAR / SET |
|---|---|
| `CDCalMode` | MLVRConfig值；两份`std::shared_ptr<const CDExternalSource>` canonical（从输入深复制，调用方修改原输入不影响绑定）；绑定target/source身份；仅首run前一次建立 |
| `CDTally` | 私有resolved layout/target；独立本轮scalar accumulator（long double补偿S1/S2、uint64 N、enabled/status）；KEEP定义，CLEAR统计，SET角色 |
| `CDExternalSource` | 源组件、分布与其私有CDF；结构profile与能量表示policy、F固定群中心速度派生缓存；每run仍`ResetWorkingSourceFrom`深复制，包括采样可变工作字段 |
| `CDFixedSource` | 原N/D、bank、严格单位权重audit全部保留；无需新增一套source controller或profile状态 |

`CalMode.h`已有`CDExternalSource`前向声明，`Source.h:19`反向包含CalMode。使用上述const shared_ptr避免按值成员引入循环完整类型；创建/验证实现在包含完整类型的.cpp。不改变普通`CalcFixedSource`外源按值语义。

拟新增主要接口（完整参数为生产对象，不新增隐藏初始化布尔量）：

```cpp
// CDInput；实现 ReadMLVRBlock.cpp
void ReadMLVRBlock(MLVRConfig &config);
void CheckMLVRInput(CDCalMode &mode, CDFixedSource &fixed, CDRNG &rng,
    const CDAceData &ace, const CDTally &tally,
    const CDExternalSource &forwardSource) const;

// CDCalMode；绑定阶段实现 MLVRTarget.cpp，run包装实现在 PrepareFixedSourceRun.cpp
void BindPreparedMLVRTarget(const MLVRTargetInput &input,
    const CDExternalSource &forward, CDAceData &ace,
    CDGeometry &geometry, CDTally &tally);
FixedSourceRunReceipt RunPreparedMLVRFixedSource(const FixedSourceRunSpec &spec,
    CDNeutronTransport &neutron, CDPhotonTransport &photon,
    CDElectronTransport &electron, CDAceData &ace, CDFixedSource &fixed,
    CDMaterial &material, CDGeometry &geometry, CDParticleState &particle,
    CDTally &tally, CDRNG &rng, CDCriticality &criticality,
    CDSampling &sampling, CDPerturbation &perturb);

// CDExternalSource；实现 BuildTargetAdjointSource.cpp
static CDExternalSource BuildMLVRForwardSource(
    const CDExternalSource &forward, CDAceData &ace, CDGeometry &geometry);
static CDExternalSource BuildTargetAdjointSource(
    const MLVRResolvedTarget &target, CDAceData &ace, CDGeometry &geometry);
void CheckPreparedTargetSourceDefinition(const MLVRResolvedTarget &target,
    CDAceData &ace, CDGeometry &geometry) const;
PreparedSourceProfile GetPreparedSourceProfile() const; // RestrictedPoint / TargetAdjoint
void CheckPreparedTargetPhysicalSample(const CDParticleState &particle) const;
void CheckPreparedTargetLocatedSample(const CDParticleState &particle,
    const CDAceData &ace, const CDGeometry &geometry) const;

// CDTally；实现 MLVRTarget.cpp
void BindPreparedTarget(const MLVRResolvedTarget &target);
const MLVRResolvedTarget &GetPreparedTargetDefinition() const;
void BeginTargetResponseRun(FixedSourceRole role);
void AccumulateTargetHistory();
MLVRTargetResponseResult FinalizeTargetResponse(long long completed,
    double denominator, const FixedSourceWeightAudit &audit) const;
double ConvertMLVRFieldValue(std::size_t meshBin, double rawAve) const;
```

`ResolveMLVRTarget(input, ace, geometry, tally)` 是 `MLVRTarget.cpp` 内只读辅助函数，返回值结构。绑定只允许当前已绑定owner、ModelReady、!preparedHasRun且尚无TARGET；所有可拒绝检查在临时对象中完成后发布。原`preparedDefinition`保持不变，新增TARGET定义快照每run单独验证，**不得为接受模型改变而更新原fingerprint**。异常不得留下半绑定可运行状态。`CDTally::BindPreparedTarget`是上述绑定流程的低层接口，检查已初始化、未绑定、未有run统计；不作为第二个正式lifecycle入口。每次Run还验证CalMode/Tally两侧bound状态一致及TARGET快照，未绑定CalMode却私自安装/启用Tally目标同样在CLEAR前拒绝，不能绕过首run限制。

原`RunPreparedFixedSource`签名保持：未绑定TARGET时走原点源路径；绑定后只接受对应私有canonical对象（owner及实际内容核验），外部任意source、错误role/identity在CLEAR前拒绝。新包装只选择canonical并调用原Run，不自己prepare或输运；sourceIdentity由绑定生成，调用方非空且冲突则拒绝。TARGET Adj的maxEnergy由完整MG上界固定；不得从选中群的最高中心生成截断能。Stage3测试中的有限FF/FAF/AA序列是验收driver，不是生产K轮控制器。

## 4. 输入卡定稿提案

```text
MLVR
ITERATION = 3
BOOTSTRAP_NPS = 20000
ADJOINT_NPS = 100000
FORWARD_NPS = 100000
TARGET MESH = 1 REGION = 1 2 1 1 1 1  4 4 1 1 1 1 GROUPS = 1 3  8 10
SEED = 12345
COMMAND = "/absolute/path/MLVR Worker"
WORKDIR = "./mlvr_run"
```

八项均必填：ITERATION、三个NPS、TARGET、SEED、COMMAND、WORKDIR；值成员默认0/空，独立presence检查拒绝缺项，COMMAND/WORKDIR必须非空。一个MLVR block、一个TARGET card。REGION为非空6元组序列、GROUPS为非空2元组序列；分别取并集，物理选择为I×J。重复范围合法去重；重复key、第二TARGET、倒置/越界/空范围报错。沿现有block终止规则；TARGET行可按普通card连续读取选项，不引入“某空间对应另一个谱”的隐含语义。

K/N/SEED/MESH/index采用局部十进制token解析，先完整验证再转换，拒绝分数、指数、NaN、尾随字符、溢出。K≥1，各N为101…INT_MAX/2；seed为Type2合法非零奇数≤2^63−1。先做checked加乘验证`NB+K*(NA+NF)`及stride周期预算，再调用Stage2 `ValidatePreparedType2Substream`合同（`RNG/StrideRNG.cpp:267–280`）；只是预算校验，不执行迭代。TYPE必须2，STRIDE沿用原FIXEDSOURCE选项。

不能盲用`ReadCardOptions.cpp:228–250`的先cast后验证或double读seed。`FileIO.h:129–150`关键字会大写；`ReadIncludeBlock.cpp:90–105`字符串helper不支持引号内空格。新MLVR局部词法器只大写关键字，路径按字节保留大小写/内部空格；要求成对双引号，拒绝未闭合、NUL和行内额外值。本阶段不解释shell、不执行COMMAND、不创建WORKDIR。固定语法初版不支持引号内部转义双引号，明确报错；普通helper不改。

`CDInput`记录POPULATION/SEED/FIXEDSOURCE内ADJOINT及非WWP:N子卡的**显式出现**，同时按block存在性拒绝顶层ADJOINT、CRITICALITY/BURNUP/DEPLETION/KINETICS/QUASISTATIC等其它计算模式，并拒绝MCNP/WWG等不支持的减方差/特殊卡。不能只检查最后一次覆盖后的mode；保留Stage2允许的CellImportance语义，不把普通importance>0误列为冲突。所有block读完后统一拒绝冲突，值相同或写ADJOINT=0仍冲突；无MLVR时这些记录不改变任何旧赋值/检查。这里保证MLVR冲突检查顺序无关，不承诺取消RMC其他原有block依赖。

三个N、SEED、TARGET本阶段可供真实prepared API测试；K、COMMAND、WORKDIR解析保存但调度/外调未实现。解析后的配置记录输入来源文件/卡名；沿用原输入/include加载，保存其可复跑原文和哈希由测试归档负责。本阶段不宣称格式化输入writer已支持MLVR roundtrip。

## 5. TARGET绑定、体积和群映射

1. 按`CDMeshTally::p_nTallyID`唯一查找已有Field tally，非vector下标或OMeshInfo ID。接受Type1、中子TL、Cartesian、原Energy=-1、Normalize=1，无dose/absolute/特殊统计数学；继续原Stage2 profile全部限制。
2. heterogeneous REGION引用`CheckHeterMeshPara`展开后的fine bins（`MeshFun.cpp:395–430`）。统一布局flat=`x+Nx*(y+Ny*z)`，各轴严格有限递增，Vi=dx·dy·dz有限正数，维数乘法和score地址检查溢出。
3. 中央转换：uniform ci=1/Vi；heter ci=1。编译αi=(Vi/VT)ci，Field getter与TARGET共用同一layout；不改原Ave/Sum1/Sum2，不输出HDF5。
4. 物理群g=1…G从低到高：中心`p_vNeuMltCentErg[g-1]`；tally slot g−1；内部群号G−g+1。`CheckMgAceBlock.cpp:38–49`仅保存G个lower bounds；完整末上界Emax=`2*center.back()-lower.back()`，同`GetMgCs.cpp:272`。核对所有实际MGACE中心/宽度有限、群结构一致、相邻边界无不连续，容差采用不超过现有库结构检查的1e−6相对量级，零附近另用固定机器精度下限；不能仅对第一核素猜完整结构。
5. 选群中心必须严格位于对应物理边界内，并逐群验证`LocateMgErgGrp(center[g-1],Neutron)==G-g+1`。`GetMeshErgPtr`=`start+flat*(G+1)+g-1`（`SingleTally.cpp:893–898`）；最后Tot槽绝不再加一次。群检查用于每种已批准库，不声称任意MGACE均已验收。
6. 打印/receipt记录mesh ID、去重bins、VT、选群编号/中心/边界和整张G+1轴。输入非法与“合法但本轮零得分”分开。

### 完整体积有效性的保守实现范围（需审批）

八角点或有限随机点均不能证明一般CSG内部无孔。本阶段仅认证：root universe无随机/变换/lattice；每个完整选bin（含边界保守裕量）落在一个未填充、未变换、importance>0的根层cell，且可证明与其他根层cell无交叠。候选域由PX/PY/PZ半空间交集确定；其它root区域仅用相同轴向半空间和既有布尔运算进行区间真/假/不确定判断，不能证明不相交便拒绝。遇复杂曲面、跨cell箱、隐藏孔、fill区域与TARGET可能相交均报“TARGET geometry unsupported”，不新建通用几何引擎。

判定采用选box完整闭包的保守包含，几何裕量固定为`OController.GetZeroSenseDistance()+64*epsilon(double)*max(1 cm, |坐标|, 箱宽)`，采用严格包含/分离不等式；实际sense距离必须有限非负、记录进binding身份并在每run前检查未变。`CalcSurfSense.cpp:201–203`会把小于该sense距离的点按方向判面侧，当前默认值1e−8 cm（`Control/Control.h:34,64`），不能只用机器精度。不移动箱边、不裁掉体积。恰落在物理边界上而无法严格证明的箱也明确拒绝；不是靠重采样规避。可证明不相交的fill区域无需下钻。允许内部有效MAT=0真空，不把材料为空和几何无效混同。

源事实位置：`Universe.h:33–37,71–76,303–315,331,515–519,670–678`，`Boolean.h:50–60`，`CalcSurfSense.cpp:58–68`。`CheckCellDefinition.cpp:122–146`已把布尔面号转换为带符号**系统index**，不能按旧注释再当用户面号查一次。该保守限制只约束新TARGET生成源；Stage2点源的原CSG范围不缩减。运行时定位检查是额外防线，不代替完整体积证明。

## 6. TARGET → 伴随源

每个去重bin一个`CDSource`，原始FRACTION=Vi、BIASFRAC=Vi；neutron、weight=1、time=0。每组件X/Y/Z各一个type4区间均匀分布，VALUE={lo,hi}、PROBABILITY=BIAS={1}；全部组件共享一个type1离散能谱，VALUE为所选群中心、PROBABILITY=BIAS为等概率。由既有参数检查识别XYZ源（`CheckAndInitiateParameters.cpp:19–26,65–71`、`SamplePosFromXYZ.cpp:6–12`）。不设VECTOR/DIRECMIU，走现有各向同性分支（`SampleStartDirection.cpp:70–76`）。

每个distribution先设p_nDistriID并在p_ODistriIndex.AddUserIndex注册，再用SetTypeAndValues构造并加入p_vDitributions；组件设置X/Y/Z/ENERGY的p_vVariableDefined与SetDistriMap，随后AddSource及一次CheckSourceAndDistri。通过这条既有机制建立私有CDF与变量索引；工作副本不再次normalize。禁止CELL、TRANSFORM、WEIGHT-variable、依赖/子分布、特殊源、概率偏倚及其它未生成变量。实际权重链是

`w0 = (Fraction/BiasFrac) × 各分布(proba/bias) × sourceWeight = 1`。

同时保留现有逐history严格w==1与终检N=D=W0。静态等式、输入WEIGHT=1、最终D=N不能互相替代。

生成源验证必须遍历实际组件、索引和分布/CDF，不凭profile或sourceIdentity字符串放行。`SourceDistribution.h`增加const验证方法，验证工厂允许的bin/discrete形式、proba与bias逐位相同、CDF有限单调且末项1，并逐项等于允许概率的累计规范化值（只查尾项不足），禁止friend访问。`Source.h`增加`static CDSource MakeTargetComponent(const MLVRTargetBox&, int xId,int yId,int zId,int energyId)`及只读profile getter；私有profile随普通值复制，实际内容仍由外源验证器核验。另设私有typed能量policy（Legacy / MLVRPointGroupSpeed / MLVRSelectedGroupCenter），不以bool混淆物理MeV与内部群号；Forward工厂先用原点源检查，再由物理E查所属群并缓存其群中心速度，原E/方向/权重/分布不变。Source增加`MakeMLVRPointComponent(const CDSource&, double mappedGroupCenter)`，将该派生中心/速度及policy纳入绑定核验；旧unbound入口只接受Legacy。

`ExternalSource.cpp:49–57`组件抽样依赖累加分数，未命中时会直接返回。在CheckSourceAndDistri之后，工厂对最终组件概率采用固定末项残差策略使按原顺序double求和恰为1；fraction/bias赋同一值，所有分数严格正，误差限为`64*epsilon(double)*组件数`且每项相对Vi/VT不超过该预定界，超出或出现不可表示的极小概率则拒绝；记录调整量，不能改总抽样循环。CDF用现有构造机制，最后一项总和/总和=1再核验。

得到`p(i,g)=Vi/(VT*m)`、盒内均匀、角密度1/(4π)，故相空间单位源密度为1/(VT*m*4π)。保存Q=m、angularPdf=1/(4π)、`unitArtificialSource`尺度。响应是群求和，不能因群等概率把响应除m。绝对伴随重要性还涉及RMC角通量/反向方向约定，本阶段不把单位人工源场直接标成绝对重要性；测试用独立解析响应及源密度积分核对，不以频率测试代替尺度证明。

### 两处必要适配和运行时拒绝

- **最高群**：原`PrepareFixedSourceRun.cpp:260–264`检查front单能且以上界max(lower)判断，最高群中心不能通过。未绑定TARGET的旧Stage2点源分支保持；Stage3绑定的F点源及A生成谱分支均用完整Emax，F验证固定物理E所属群，A验证全部所选中心。Adjoint输运上限使用完整模型Emax，不能按TARGET选群最高能量裁剪潜在反向迁移。
- **速度初始化（F/A都须受控适配）**：`SampleParticle.cpp:76,81–83`尚持物理MeV就调用`GetNeuVelMg`；`GlobeFun.h:538–546`将其当群号索引`G-int(E+0.5)`，E<0.5可越界。Stage3-bound F通过原点源白名单后，在绑定时由物理E定位群，缓存并核验该**群中心**对应的速度；F的E不必等于中心，不能直接GetNeuVel(E)。A工厂抽中的本来就是物理群中心，使用已有GetNeuVel(E)即等价正确群速度。SampleParticle只对上述两种私有MLVR policy使用正确速度，原SampleFixSource仍在原位置把粒子物理能量转换成群号一次；不增加RNG调用、不改变源能量或抽样概率。普通及未绑定TARGET的Stage2仍使用Legacy路径。Stage3-bound F的初速度及相关飞行时间是**预期修正**，不得声称与旧错误初速度全部相等；新旧TL/RNG确定性回归、速度物理oracle分别验收。不得用UpdateNeuStateMg替代，因为它还读p_dExitErg（`ParticleStateFun.cpp:131–139`）。这是静态确认的坐标误用风险，本轮未动态复现。
- **无效点**：在`SampleNeutronSource.cpp:235–267`原kill/return之前，activeSource为已验证generated profile时，定位失败或importance0立即throw进入现有Failed/no receipt；不重采样、不丢弃历史后声称成功。还要逐样本确认所属源ID、盒范围、有限单位方向、实际选群和weight；采用上列PhysicalSample/LocatedSample两个明确的只读方法，前者紧接实际抽样及权重audit，后者在原MG映射完成后；定位错误在原kill之前拒绝，避免布尔参数混淆能量表示。检查不消耗RNG。

## 7. TARGET响应与RE

唯一hook为固定源重载`SumUpTally`的mesh分支，在`SumTallyBin`前：

`rh = Σ_selected αi * rawScore[GetMeshErgPtr(i,g-1)]`，`S1+=rh`，`S2+=rh²`，`N++`。

全部descendant已在原执行核心汇入同一临时score；一次history只平方一次。即使本history没命中任何目标slot，也必须N++。不按hit集合计N，不用batch局部Neu当累积N，不存全部历史/协方差。排序固定、逐项只读，原score/indexset/StatisticsTester和RNG不变。

`ResetRunScores`清理scalar S1/S2/N并禁用；Prepare随后按role启用：Forward启用，Adjoint保持NotApplicable。绑定不存在则全程no-op。原ProcessTally一次结束之后、成功receipt之前做`FinalizeTargetResponse`，核对N=requested=completed=D=weightAudit.sampled=W0，nonUnit=0；失败throw，不返回成功receipt。另用Σα·Ave复核mean，此项仅内部一致性，不冒充独立物理参考。

数值约定（测试前固定）：

- 每个所选rawscore、α、rh、S1/S2/rh²必须有限且非负；溢出或负值失败。
- long double补偿累加，`delta=N*S2-S1²`；`tau=64*epsilon(long double)*max(N*S2,S1²)`。delta在[-tau,0)夹0并记roundoffClamped；更负失败，禁止abs。RE=`sqrt(delta/(N-1))/S1`，转输出double后再检查有限。
- N=0拒绝成功；N=1返回mean、无RE、INSUFFICIENT_HISTORY（实际MLVR N>100，代数单测覆盖）；S1=S2=0为ZERO_SCORE，R=0、hasRE=false，不能把RE=0标成精确；S1=0但S2>0失败。正得分且零方差可VALID、RE=0。
- 结果结构：`targetIdentity, meshTallyId, targetVolume, physicalGroups, histories, sum1, sum2, mean, hasRE, relativeError, status, roundoffClamped`；在receipt追加该结构、sourceProfile及Q/angularPdf/尺度说明。Adjoint返回NotApplicable且无旧F结果。
- 保留Stage2 prepare/transport/tallyFinalize及T_MC计时口径；目标finalize计入本次tallyFinalize；旧StatisticsTester累计时间/FOM仍非本run指标，只例外明确时间字段，不整体跳过其统计。

## 8. 完整拟修改文件清单

下列均是**待批准计划**，本轮未写任何生产补丁。预计20个生产源码/头文件，另1个根构建文件；若实施需扩清单先说明原因。

| 路径（均相对RMC） | 操作与原因 |
|---|---|
| `src/MLVRConfig.h` | 新增：配置、TARGET/layout/result小值结构 |
| `src/ReadMLVRBlock.cpp` | 新增：局部安全词法/整数、TARGET解析、全block冲突检查 |
| `src/MLVRTarget.cpp` | 新增：TARGET解析绑定、中央体积/群转换、保守域证明、CDTally标量统计 |
| `src/BuildTargetAdjointSource.cpp` | 新增：CDExternalSource/CDSource工厂（含F速度派生绑定）、逐字段/CDF/样本校验；不写sampling内核 |
| `src/Input.h` | MLVR block注册、parser/check声明、显式输入来源标记 |
| `src/ReadInputBlocks.cpp` | 分派MLVR；旧CheckInpBlock前统一检查 |
| `src/ReadFixedSourceBlock.cpp` | POPULATION/SEED/ADJOINT显式来源，普通处理原样 |
| `src/ReadWeightWindow.cpp` | 静态/特殊WW子卡出现记录 |
| `src/RunCalculation.cpp` | MLVR尚无scheduler时明确拒绝，普通分派不变 |
| `src/CalMode.h` | 配置、一次绑定/单run包装API、const canonical owners |
| `src/PrepareFixedSourceRun.cpp` | TARGET/source/role CLEAR前校验、绑定源选择、统计SET与finalize receipt |
| `src/ExternalSource.h` | F复制工厂/A生成工厂、profile/policy核验、两阶段样本检查声明/私有来源信息 |
| `src/Source.h` | point副本/生成组件工厂、结构profile与typed能量表示policy、派生速度及只读getter |
| `src/SourceDistribution.h` | const工厂分布/CDF核验入口，实现在新增builder文件 |
| `src/SampleParticle.cpp` | 仅Stage3-bound F/A物理MeV阶段安全速度初始化；普通与unbound Stage2不变 |
| `src/SampleNeutronSource.cpp` | generated实际样本/定位/群映射检查，错误不得成功结束 |
| `src/Tally.h` | target/layout/独立scalar状态与方法 |
| `src/InitiateTally.cpp` | 原ResetRunScores增加scalar CLEAR/禁用，不重复注册 |
| `src/SumUpTally.cpp` | 固定源完整history的mesh清理前hook |
| `src/FixedSourceRunSpec.h` | receipt增加TARGET结果与单位人工源元数据；原spec/API保持 |
| `CMakeLists.txt` | 同现有serial测试条件增加独立Stage3测试子目录；src根目录glob重configure自动纳入新.cpp |

不计划修改`CalcFixedSource.cpp / TallyData.cpp / ProcessTally.cpp / ScoreMeshTally.cpp / MeshFun.cpp / GetMgCs.cpp / GlobeFun.h / Geometry.h`，不普修W11/W12/W13。`ExternalSource.cpp`原点源检查/复制/抽样均复用，新增方法落builder文件。无需修改`FixedSource.h / InitiateTrspt.cpp`：样本guard从已验证activeSource profile取角色，不再引入重复开关。

测试新增 `tests/mlvr_target/CMakeLists.txt`、`driver.cpp`、`compare.py`、少量输入/预定代数fixture；不改既有测试/reference。新target `RMCMLVRTarget`从最终RMC SOURCES排除恰好一个`main.cpp`，加入新driver及既有`tests/prepared_fixed_source_lifecycle/globals.cpp`，继承同编译宏/链接库；globals恰好定义一次，不改普通RMC或Stage2target。留存source list/link map检查，MPI/OMP/AIS/Python未开放profile仍明确拒绝。

## 9. 最少实施子步骤与批准门槛

1. **输入与绑定**：配置、presence、两阶段解析、layout/体积/群/几何认证及CLI guard；先通过解析/非法输入/索引代数门禁。
2. **生成源与受控适配**：源工厂、canonical F/A、严格验证、Stage3-bound F/A的MG速度和最高群适配；通过抽样/权重/尺度及边界安全门禁。
3. **history响应及整合**：scalar状态与hook、receipt、FF/FAF/AA+WW/fresh与普通回归；通过独立物理/统计oracle后交独立审查。

所有步骤均复用Stage2 Type2子流、KEEP/CLEAR/SET/REBUILD、model/registry/WW身份、严格初始权重、失败terminal和单一transport loop。非零裂变仍拒绝，未开放平台/复杂源不扩展。实施前从当前冻结HEAD建fresh baseline、记录编译器/flags/核数据身份；不能用历史未知binary或更新reference放行。回滚仅撤销届时本任务实际增量（包括新文件独立补丁），先保留用户修改；不reset或切分支。

设计判定：**READY FOR INDEPENDENT DESIGN REVIEW**。方案已具体化，尚无实现证据；上述保守几何限制、两处generated适配与21文件审批清单需用户和Claude审核。任何未通过门禁的项目不得标Ready或外推为完整F11能力。
