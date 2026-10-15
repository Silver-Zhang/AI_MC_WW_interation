# W14 — RMC 多群中子源速度初始化独立审核（Claude）

| 项 | 内容 |
|---|---|
| 审核日期 | 2026-10-15 |
| 审核基线 | RMC `Neural_Network_WW_Iteration` / `4810694b7a99dfc3ad7d27f7d443814f511f4829` |
| 报告人 | Claude，独立审查；未读取 Codex 本轮 W14 报告或其结论 |
| 分类 | **CONFIRMED · P1 · E3（限定 probe）** |
| 范围 | 普通 standard MGACE fixed-source neutron 外源的源速度初始化；附带追踪固定源 bank 恢复及指定 F02/F03/F04 历史覆盖 |
| 实施状态 | 只读审查与隔离诊断；未修改 RMC、reference、核数据库或共享状态文件；未修复 |

## 1. 独立结论

**W14 成立。** 普通 MG fixed-source 输入的 `SOURCE ENERGY` 是物理 MeV。`CDSource::SampleParticle()` 把它写入 `p_dErg` 后，在 `SampleFixSource()` 将能量定位到内部群号之前，就把这个物理值交给 `GetNeuVelMg()`；后者把参数当作内部群号舍入并用 `k=G-int(E+0.5)` 读取群中心数组。两种坐标被混用：

- 对物理能量 `E<0.5 MeV`，舍入群号为 0，因此 `k=G`，恰好是长度为 G 的向量的一位越界读取；本次 ASan probe 确认真实堆越界。
- 对合法但非低能的源，索引可能仍在向量内，却会选择错误中心能量，初始化出错误速度。
- 随后 `SampleFixSource()` 会正确地把源能量映射成 MG 群号，但没有重新计算速度；初速错误确实到达首次飞行。

同一 ordinary source 初始化链供 Forward 与 Adjoint 共用；伴随标记是在 source sampling 后设置，不改变 velocity 分支。因此两个模式都受影响。该错误首先是**初始化错误**，且已证明成为**首次使用错误**；它不自动证明所有稳态空间通量或反应率估计都错误。首次速度直接用于飞行时间，且也被时间/速度类观测量使用；本次没有资格化的稳态 response oracle 来证明普通稳态通量有系统偏差。

## 2. 证据等级和证据身份

- **SOURCE VERIFIED (E1)**：本审查直接读取冻结 RMC 工作树源码。生产路径的相关源码文件 SHA256 与实际 GDB 所用构建源码副本相同；RMC HEAD 保持 `4810694b`，RMC 工作树 clean。
- **INDEPENDENTLY EXECUTED (E3，受限)**：在 `/tmp/w14-claude-review/` 使用既有 MPI-off 普通 RMC Debug/O0 binary 做 GDB 只读检查；另从当前冻结 RMC 源码的独立副本配置并构建 ASan/UBSan/float-cast-overflow binary，实际执行低能源输入。构建源 SHA 与当前 RMC 中相关文件一致；非受限全矩阵没有执行。
- **INFERRED**：首次飞行距离来自几何与 `-log(U)/宏观总截面`，而非速度；指定普通 TL/collision flux estimators 本身不直接乘初速。因此当前证据不能将速度错误直接外推为稳态通量/反应率的普遍数值偏差。
- **UNVERIFIED**：各类时间 tally、velocity estimator、普通 filter、所有裂变后代/衍生源，以及修复前后正式物理 observable 比较。未运行完整 F02/F03/F04 矩阵。

真实 probe 的输入和 GDB/ASan 输出只保存在 `/tmp/w14-claude-review/`，未与 Codex 共用目录。关键运行观察：

```text
高能源 16.0 MeV，G=30，Adjoint：
AFTER_SAMPLE e=16 v=4.9053375868571196
  由该速度反算的动能为 0.1258 MeV；实际选中的是错误数组项。
FIRST_FLY group=1 v=4.9053375868571196 len=5.9113577869800125

高能源 16.0 MeV，Forward：
AFTER_SAMPLE e=16 v=4.9053375868571196
FIRST_FLY group=1 v=4.9053375868571196 len=5.9113577869800125

低能源 0.2435 MeV，Adjoint：
AFTER_SAMPLE e=0.24349999999999999 v=0
AFTER_MAP group=15 prior_v=0 center=0.24349999999999999
FIRST_FLY group=15 v=0 len=5.9113577869800125
```

低能源 ASan 观察：

```text
ASAN_OPTIONS=detect_leaks=0; 低能源 ordinary source (0.2435 MeV)
exit = 1
ERROR: AddressSanitizer: heap-buffer-overflow
READ of size 8
0 bytes after a 240-byte region
GetNeuVelMg (GlobeFun.h:544)
  <- CDSource::SampleParticle (SampleParticle.cpp:82)
  <- CDExternalSource::SampleSourceParticle (ExternalSource.cpp:347)
  <- CDFixedSource::SampleFixSource (SampleNeutronSource.cpp:202)
```

同一插桩 binary 的 0.6615 MeV 对照退出 0、没有 ASan 内存错误；但从源码表达式可知该源仍可能选错索引而得到错误速度。该 sanitizer 运行还输出了无关的既有 UBSan 诊断（`Universe.h:664` enum/bool load，`StrideRNG.cpp:132` 有符号乘法溢出）；本报告不把这些诊断归因于 W14。相应 ASan 堆越界栈独立明确落在 `GetNeuVelMg()` 数组读取。

动态 binary 的内嵌 banner 是 `330f091e`，不是本次冻结 RMC HEAD；因此本报告不把 banner 当作源码身份。用于本 probe 的 `SampleParticle.cpp`、`SampleNeutronSource.cpp`、`GlobeFun.h`、`ParticleStateFun.cpp` 等逐文件 SHA256 均与冻结 RMC HEAD 相符；最终 ASan binary 是从当前 RMC `4810694b` 独立源码副本新建。未将该限定 probe 冒充正式基线完整性/全面回归证明。

## 3. 逐项裁定

| 项目 | 结论 | 源码/动态依据 |
|---|---|---|
| MeV 与群号是否混用 | **是，确定** | Source card 读入值落入 `p_dEnergy`；`SampleParticle()` 在群转换之前把它传给以群号索引的 helper；`SampleFixSource()` 才调用 `LocateMgErgGrp()`。见 `ReadSourceCard.cpp:846-853`、`SampleParticle.cpp:76-85`、`SampleNeutronSource.cpp:269-279`、`GlobeFun.h:538-546`。 |
| 初始速度是否错误 | **是，确定** | GDB 中 16 MeV Forward/Adjoint 均得到 4.9053375869 cm/shake；按相对论公式反算为 0.1258 MeV 速度，而实际群映射后为 group 1，对应中心 16 MeV，正确速度 54.6310903661 cm/shake。0.2435 MeV 则得到速度 0；它映射 group 15、中心 0.2435 MeV，正确速度 6.8239725209 cm/shake。 |
| 是否存在越界风险 | **是，真实且已动态确认** | 对 `G=30, E=0.2435`：`int(E+0.5)=0`，`k=30`；合法中心数组下标只能是 `0..29`。ASan 报 240-byte allocation 后 0-byte read。此处的源值本身在 MGACE 支持范围内。 |
| Forward 是否受影响 | **是** | 普通 fixed-source Forward 走同一 `CDSource::SampleParticle()` 与 `SampleFixSource()`，没有以 adjoint 状态选择 velocity 的分支。低/高输入 probe 和 source call chain 均支持。 |
| Adjoint 是否受影响 | **是** | `SampleFixSource()` 在 ordinary sampling 之后才设 `p_bIsAdjointParticle`；此标志不会重算或替换 `p_dVel`。低/高输入 probe 复现同样行为。 |
| 首次自由飞行是否受影响 | **是** | source 到 `TrackHistory()`、`RayTracking()` 及首次 `FlyByLength()` 之间未发现 velocity 重写。GDB 在首次 `FlyByLength()` 入口读到与 `SampleParticle()` 相同的初速。`FlyByLength()` 按 `p_dTime += dLength/p_dVel` 使用速度；低能 probe 首段速度为 0。 |
| 首次飞行距离、碰撞截面是否由此错速直接改变 | **已检查路径中没有直接依赖** | `SampleFreeFlyDist()` 由宏观截面和 RNG 采样长度；MG 截面依靠已正确转换的 `ErgGrp()`。普通 track-length score 使用 `wL`。这是受检路径的源码结论，不能覆盖所有源类型或 UB 对未覆盖代码的影响。 |
| 稳态物理结果是否必然错误 | **未证明** | 初速错误确定；时间增量会错。但普通稳态 TL/collision 估计器不直接使用 `p_dVel`，本次没有资格化独立 response oracle 来证明通量/反应率有偏。不得把初始化缺陷自动等同于所有既有稳态数值错误。 |
| F02/F03 是否存在覆盖缺口 | **存在，但历史任务范围不同** | F02 明确把源语义排除交给 F03，重心为伴随算子/密度/nubar/互易性；F03 覆盖 source sampling 和最终 group/权重映射，但动态门禁检查群号、源支持/权重与稳态响应，不检查速度/首次时间/内存安全。F04 验证 adjoint+WW 组合和 tally，不核对速度。详见第 5 节。 |

### 源能量阶段和关键下标

- `CDSource::p_dEnergy` 默认注释为 4 MeV；ordinary EXTERNALSOURCE `ENERGY` 数值存入此字段，分布也可写入 `p_dEnergy`。固定源常见 ENERGY 是物理 MeV，随后以 ACE lower-bound 表定位群。
- `GetNeuVel(E)` 直接按物理动能 MeV计算相对论速度。
- `GetNeuVelMg(g,G,centers)` 则要求内部 1-based 群号 `1≤g≤G`，下标 `k=G-g` 对应反向存储的群中心数组。群中心数据由 MGACE 的 centers/widths 构造，并按低到高存储。
- `LocateMgErgGrp(E)` 输入物理能量，输出反向编码后的内部群号。该输出以后才被保存在 `p_dErg` 并转换 `p_nMultiGrpNumber`。
- 对 `G=30,E=0.2435`，误用时 `g=round(E)=0,k=30`；越界。对 `E=16`，误用时 `g=16,k=14` 合法但错误；GDB 初速与 center index 14 的 0.1258 MeV 对应，而物理 16 MeV 转换后是 group 1，正确中心在 index 29。

## 4. 首次输运和对结果的影响边界

### 直接确认的依赖

1. `CDFixedSource::TrackHistory()` 在第一次 `RayTracking()` 前检查的是能量 cutoff、输出/backup状态，没有调用 `UpdateNeuStateMg()`。
2. `CDFixedSource::RayTracking()` 采样几何边界与自由程，按既有 WW/scorer 流程推进粒子；无 WW 分支在 tally 后调用 `FlyByLength()`，后者使用 `p_dVel` 累积时间。
3. MG 宏观截面按正确映射后的内部 group 读表；`SampleFreeFlyDist()` 从总截面采样 `-log(U)/Σ_t`，该公式不读 `p_dVel`。空间位移为 `direction × length`，本身也不读速度。
4. 普通 track-length tally 计 `weight × track length`；collision estimator 用碰撞前权重和截面。velocity estimator `weight × p_dVel`、时间分箱 `track length/p_dVel` 则直接受速度错误影响，但本次没有运行这些输出模式。
5. 碰撞后固定源路径调用 `UpdateNeuStateMg()`，以碰撞后内部群号重新计算速度；这不能回溯修复源到首碰撞前的时间。固定源 neutron bank 在 `SampleFromParticleBank()` 恢复时另有 `GetNeuVel(p_dErg)`，但这里恢复的 p_dErg 是内部群号，所以 bank 后代也可能把群号当 MeV 算速度；本轮静态定位该通用风险，未动态运行 bank/裂变后代。

### 不作的推论

- 不声称所有普通稳态通量、反应率或历史 F02/F03 的正向—伴随互易性必然错误。
- 不声称时间 tally 或速度 estimator 的具体误差已由输出值动态量化；这些是源码上确定的依赖关系，实际输出影响未验证。
- 不把低速 `p_dVel=0` 导致的首次 `dLength/v` 非有限时间推广成普通空间积分 tally 必然偏差。
- 不用“进程退出 0”作为正确性证据；这个缺陷可能在有限索引下静默选错速度，也可能越界但暂时没有 crash。

## 5. F02 / F03 / F04 历史审查回顾

### F02

- F02-B 范围明确为 standard MGACE fixed-source neutron adjoint 算子物理核、W5 局部密度、W6 双 nubar 与受限正反向互易性；任务 README §1 明确排除 F03 source semantics 和 F04 WW 组合。本次问题属于源初态跨表示与速度/时间，不是已声明的散射/裂变伴随核判据。
- F02 V0 使用 30 群 H/O `fixed_source_adjoint` 输入（source energy 0.6 MeV），V2/V4 source/response 与碰撞权重和稳态 scalar response 为主，没有速度输出或首次时间 oracle。F02 任务 README §2 §4 与 §6 对这一问题没有显式 acceptance criterion。
- V0/V4 的稳态互易结果并不等价于源速度已被检查；因为普通 TL tally 与碰撞群转换不直接依赖速度，首段空间观测可以与错误时间并存。

### F03

- F03 直接读取并列出 `SampleParticle.cpp` 与 `SampleNeutronSource.cpp`，并追踪到“抽样源 → 设置 adjoint flag → LocateMgErgGrp”链。这表示问题有机会被代码审查发现，不能说采样文件完全在范围之外。
- 但 F03 目标是 response-to-source 表达、位置/方向/能量、群定位、权重与 response 复合量。其动态门禁用 `PRINT SOURCE` 的最终 `erg` 验证选中群，并对固定 cell/group 的 source weighted first moment 和稳态响应互易做 gate；没有记录 `p_dVel`，也没有 first-flight/time 或内存安全 oracle。F03 使用的低群 0.2435 MeV 本应可暴露错误速度；留存 source trace 只有最终群号，adjoint run 有 photon upper-bound warning，但没有记录速度校验。故：**静态采样链审查存在遗漏；F03 的动态目标与观测量本身不能发现该速度缺陷。**

### F04

- F04 明确聚焦 fixed-source neutron adjoint 与 native `WWMESH` 的组合链、split/roulette 和 WW on/off paired tally。静态追踪了 source/bank adjoint flag 恢复，但没有把速度初始化列为判据。
- 实际 paired oracle 使用低群 0.2435 MeV。档案记录了群/tally与稳态 paired response，不含 velocity 或首段时间检查；从其观测量不能排除本问题。
- 这不会推翻 F04 的受限稳态 WW 统计结果；它将其能力边界限于已测 observable，不能外推到时间/速度 estimator、bank 子代速度安全或 sanitizer 安全。

### 范围判断与最小历史补证

此前任务各自的物理目标有合理边界：F02 检伴随算子，F03 冻结有限响应→源映射，F04 检 WW 是 variance transform。未对 source velocity 加测试不是对所有既有物理结论的整体否定；但 F03 读取过源链，应把“读取相关源码≠覆盖每一个 particle-state field”明确写作边界。

最小补证为：在 F02/F03/F04 各选一个低物理能源代表输入，以同一冻结源码做仅针对该例的 GDB/速度 oracle；验证物理 `E→mapped g→ACE center→v` 和首次 `FlyByLength` 所用速度。再以一条低群 ASan/UBSan targeted probe 证明越界路径。无需重跑完整矩阵；若修复后主张 bank descendants 也安全，另加一个 native WW split bank 出队检查。

## 6. 最终裁定与处置建议

1. **W14 是否成立？** 是，且分成两个相关但分离的入口风险：普通源采样时 MeV 被当群号；固定源 bank 出队时内部群号被当 MeV。第一个已通过 GDB + targeted ASan 证实。第二个在本轮为 SOURCE VERIFIED，未独立动态执行。
2. **严重程度？** **P1。** 在声明支持的普通 standard MGACE fixed-source neutron F/A 范围，合法低能能源会造成 heap OOB；其它能源还会静默给错速度，污染初始时间。不是 P0，因为未证明普遍稳态估计器错误或全面计算不可用；但应视作安全/时间状态正确性阻塞。
3. **最合理的修复位置？** 通用粒子状态建模边界，而非 F11 新 TARGET 层：普通初始源在 `CDSource::SampleParticle()` 应基于物理 MeV 先定位内部群，按对应中心算速度，同时保留既有 source energy 到 `SampleFixSource()` 的物理输入合同；要避免重复 warning/locator与多次 mapping 不一致。Bank 恢复必须区分 CE MeV 与 MG group，并用对应 ACE 群中心算速度。新增 helper 可把“物理MeV→group→center velocity”和“已有内部group→center velocity”拆成类型明确的 API。索引范围检查可作为防御，但不能代替修正坐标语义。
4. **是否阻塞 F11 Stage 3 生产实施？** 是，至少阻塞任何依赖新 source/velocity adapter 的生产实施与其验收；建议先另行授权通用 W14 修复并独立复核，避免 Stage3 在坏的 common sampler 上叠加私有绕行。用户原授权只要求验证与报告，不含 RMC 修复，本轮不实施。
5. **需复核的既有结论？** 不要求重跑/撤销既有稳态 F02/F03/F04 formal 结论；需限制解释边界。针对性核对其低群 F/A 源首次速度与时间状态，尤其 F03/F04 0.2435 MeV 输入。凡声称时间响应、速度估计器、首次时间/生成时间或 bank 后代速度安全的结论，应暂停沿用并专项复验。若修复声称不改变稳态 tally/RNG，可用 1–2 个代表 fixture 做修复前后确定性比较；正式再归属由修复任务决定。

## 7. 证据/未验证清单与保护边界

### 本轮实际执行

- 实际冻结 RMC 基线：branch `Neural_Network_WW_Iteration`，HEAD `4810694b7a99dfc3ad7d27f7d443814f511f4829`，工作树 clean。
- 普通 GDB binary 来源于外部 Stage2 archive 的构建，内嵌 banner `330f091e`；我没有把它冒充 HEAD `4810694b` 的 binary。逐文件比对显示 SampleParticle、SampleNeutronSource、GlobeFun、ParticleStateFun、RayTracking 等本问题关键源码与当前冻结源码 hash 相同；普通 source GDB evidence因此可用于这些未变函数的运行顺序观察，但不提供严格整个 binary provenance。
- 独立 sanitizer binary 在 `/tmp/w14-claude-review/source-copy` 从当前冻结 RMC 源码新构建；hash SHA256 `7390b0432319e8090b41ba9c7a286d95543efb632047cc5aa155a33d4452e6a2`。CMake Debug/O0、GCC 13.3.0、MPI/OMP/AIS/Python off，启用 AddressSanitizer/UndefinedBehaviorSanitizer/float-cast-overflow。该全程序插桩执行还报告若干既有 UBSan 项（Universe bool/enum 读取，StrideRNG signed overflow）；独立 ASan 报告仍明确显示越界发生在 `GetNeuVelMg()` 读取中心数组。
- `0.2435 MeV` adjoint 输入：GDB 读到 sample e=0.2435、v=0，定位 group=15；ASan `READ size 8`，240-byte vector allocation后 0 bytes；stack exact top 为 `GetNeuVelMg <- SampleParticle <- SampleSourceParticle <- SampleFixSource`。
- `0.2435 MeV` forward 输入：同一 source sample v=0，首次 `FlyByLength` v=0；普通 run 退出0但 stderr/stdout 记录一条 upper-energy warning与非零 collision count。不得解释为低速正确。
- `16 MeV` Forward/Adjoint：两者 sample/first flight 均用 v=4.9053375868571196；预期群1中心16 MeV速度约54.6310903661。
- `0.6615 MeV` sanitizer control：退出0、无 ASan OOB；静态与 GDB mid case 显示合法索引仍可以选错群/速度。
- GDB的post-flight时间断点在优化构建对成员可见性有限；低速使 `L/v` 为除零这一结论由源码表达式及同次 GDB记录的 `L>0,v=0` 直接推出。ASan已提供独立内存故障实证。

### 未覆盖

没有以完整 `4810694b` 源码重构 ordinary Debug binary，也没有跑完整历史 formal；没有运行可定量的 steady-state reference oracle；没有真实时间 tally/velocity estimator 输出对照；没有直接动态验证 WW descendant bank 恢复或裂变 bank；不覆盖其它粒子、CE、parallel、AIS/Python source、criticality/kinetics source constructors。

### 保护检查

本轮未修改任何共享文件；未修改 RMC、test source、nuclear data、reference、frozen KB04、STATUS、INDEX 或本地 W14 archive；未 commit/push/reset/checkout/clean。收尾：RMC HEAD仍为 `4810694b`、工作树 clean；冻结 KB04 SHA256 `aeed2760f84427bdd8d139182d7bb3f4193c0c63f67decec1d42c7aad7a676b0`不变。Codex档案里存在 W14 记录，但按“不得读取 Codex 本轮结论”要求，本次形成结论时没有查阅或采用它。

> 原授权要求报告后直接发给用户等待联合审查。用户之后另行要求正式归档并批准同步共享台账；其归档属于用户后续明确授权，不改变此前技术报告的独立形成边界。
