# w14-mg-source-velocity-repair

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-10-17 |
| 状态 | 已实施；Claude独立审核 **NEEDS CORRECTION · P1**（W14保持OPEN） |
| 任务类型 / 模式 | RMC 通用缺陷修复 / C |
| 报告人 | Codex |
| 关联知识库条目 | W14（未自行 CLOSED） |
| RMC 分支 / HEAD | `Neural_Network_WW_Iteration` / `4810694b7a99dfc3ad7d27f7d443814f511f4829`；本轮8个生产文件未提交修改 |
| 文档仓库分支 / HEAD | `main` / `50d9e0eada8016b3f7d71a08f1a2ff195f481559` |

## 1. 目标与范围

修复 W14-A 原始源把物理 MeV 当作内部群号算速度，以及 W14-B Bank 恢复把内部群号当作 MeV 算速度。正确关系是用实际所在群的 MGACE 群中心代入相对论速度公式，首段时间增量为 `L/v`。保持源能量转换合同、Bank 权重/源历史归属/调度，以及原稳态计分和 RNG 消耗。

范围包含普通 standard MGACE neutron Forward/Adjoint、固定能量及离散谱、真实 native WW split 和小型裂变 Bank、Stage2 FF/FAF 与 CE 代表性回归。按原授权不实施 Stage3、不改冻结04/数据库/reference，不提交或推送，不清理用户文件。

开工两仓库工作区均干净。真实 Git 输出、文件身份见 [baseline.json](logs/baseline.json)，用户授权原文摘录见 [user-authorization.md](logs/user-authorization.md)。既有依据：[Codex W14报告](../20261015_02_w14-codex-independent-validation/REPORT.md)、[Claude W14报告](../20261015_03_claude-w14-independent-review/Independent_W14_RMC_MG_Source_Velocity_Review.md)、[Stage2冻结验收§4](../20261011_05_f11-prepared-run-lifecycle/README.md#4-结论与边界)。历史独立报告保持原样。

## 2. 做法与证据

实施前因果链、验伪判据、范围和回滚见 [design-test-plan.md](design-test-plan.md)；实际完整生产补丁见 [changes.diff](changes.diff)。没有 RMC 新增未跟踪文件，也没有修改既有测试/reference。测试程序、输入及分析脚本保存在本任务，不改变 RMC 正式输运循环。

| 当前源码位置 | 实际修改及原因 |
|---|---|
| `RMC/src/SampleParticle.cpp:83` | MG 原始源通过 `LocateMgErgGrp(E,type,false)` 局部定位，再传群号给速度函数；`p_dErg` 仍保留采样 MeV。固定能量/分布源共用此位置。 |
| `RMC/src/AceData.h:1866`、`src/GetMgCs.cpp:263` | 定位函数增加默认 `bWarn=true`；速度预定位传 false，正常后续转换沿用原警告。新增有限物理能量和数组尺寸检查，定位算法/边界归群不变。原最低群警告逻辑未夹带修正。 |
| `RMC/src/GlobeFun.h:540` | `GetNeuVelMg(double dGroup,int G,const vector<double>&)` 在转换/索引之前检查有限整数群号1..G、G及数组尺寸；检查中心有限且正，调用原 `GetNeuVel(center)`。不clamp，不按值复制整个中心向量。 |
| `RMC/src/FixedSource.h:499,508`、`src/SampleNeutronSource.cpp:287,331` | Bank两函数末尾新增 `const CDAceData&`，恢复中子速度按 MG/CE 分支计算；使用已有 `p_dErg`，不改缓存、能群、权重、时间起点或出栈次数。 |
| `RMC/src/CalcFixedSource.cpp:232,320,454,457,631,743,746` | 仅为7处现有 Bank 调用传入 `CAceData`，neutron/photon/coupled 分支保留，没有复制/重写 history 循环。 |
| `RMC/src/PythonInterface/PythonInterface.cpp:151` | 复用相同局部群定位，修正 Python 源返回 MeV 的同一 W14-A 入口；启用宏的该 TU 编译通过，Python实际源运行未验证。 |

独立计算读取真实 ASCII MGACE（1001.50m、8016.50m，以及裂变用92235.50m）的中心和宽度，以50位Decimal计算 `v=c*sqrt(Ec*(Ec+2m))/(Ec+m)`，`c=299.792458 cm/shake`、`m=939.56542052 MeV`。速度预设相对容差1e-12；首飞时间的预设误差界为 `1e-12*max(|t_before|,|t_after|,|L/v|,1e-300)`。群号/索引精确比较；稳态回归物理容差0，未放宽判据。

所有运行命令、stdout/stderr、退出码、GDB JSONL、输入、构建配置、源/二进制/数据库身份均保留。精简结果见 [velocity-results.json](velocity-results.json)、[ordinary-comparison.json](ordinary-comparison.json)；目录与可复现命令见 [reproduce.md](reproduce.md)。[evidence-manifest.json](evidence-manifest.json) 记录逐文件SHA256。

构建为 GCC 13.3.0、CMake 3.28.3、GDB 15.1，Debug/O0、Linux serial、MPI/OMP/AIS/Python OFF、test ON、catcherr OFF。修复前从冻结HEAD独立归档全新构建，修复后独立源码目录按同参数全新构建。prepared target两测试TU使用真实CMake命令编译，链接复用各自刚构建的、逐项编译参数完全一致的生产对象；不复用身份不明历史binary。Python TU另按项目宏和include独立编译，不能等同整个Python配置链接或运行通过。

## 3. 决策

用户原始授权：“本次授权 W14 必要的 RMC 生产代码修改及测试。”

C·G1 问题定式已向用户解释：纠正两种能量表示混用带来的速度/时间错误和越界，同时要求稳态 Tally/RNG 确定性保持。用户回复原文（2026-10-17）：**“请开始修复”**。按该最新直接实施指令推进，未重复申请同一范围的代码权限；G2/G3因果链及验伪判据在实施前写入 design-test-plan.md 并向用户说明，没有伪记另有逐关问答。G4结果解释见§4及最终用户消息，**用户验收确认待回复**，独立审核待Claude进行。

| 风险 | 改动范围 | 验证与停止条件 | 回滚 |
|---|---|---|---|
| MeV/群号混用和越界；错误修改可能干扰原抽样/调度 | 8个已有生产文件，必要接口传参和同类源入口；不改输运/统计数学、reference或群号缓存 | 独立速度/首飞时间、真实后代、ASan、零容差稳态/RNG、prepared/fresh；失败先定位，不扩大容差 | 保留基线和完整patch；仅按本任务变更撤销相应行，避让后续用户修改，不自动reset/checkout |

## 4. 结论与边界

**实施已完成，但Claude独立审核结论为 NEEDS CORRECTION · P1；W14未关闭。** 修复任务限定的ordinary MG neutron固定能量源、WW后代bank、普通Forward诱发裂变bank及修复前后回归门禁得到支持；新增type-5 spontaneous-fission Watt源动态对照发现候选版回归，见[独立审核报告](../20261017_02_independent-w14-repair-review/Independent_W14_Repair_Review.md)。因此本任务原自验数据保留，但“当前没有已测范围内失败门禁”的范围需收窄：spontaneous-fission源/扩展bank为已确认P1失败路径，不能将W14标记CLOSED。

| 门禁 | 实际结果 |
|---|---|
| 原始源/后代速度与首飞时间 | **19/19用例**，每例101条源历史；12个固定能源F/A（低/中/较高/高及首末边界），2个离散谱F/A，2个MG WW F/A，1个裂变Bank，CE analog/WW各1。每例101个sample和mapped均核查，未把群号覆盖到源MeV状态。速度最大相对偏差 `3.052e-16`，时间最大缩放偏差 `3.104e-16`，均小于预设1e-12。 |
| W14-A具体数值 | 低能 `7.60695e-8 MeV` → g30，v=`0.003814850026663408 cm/shake`，首飞L=`0.1643847412446247 cm`，Δt=`43.09074802303591 shake`；`0.6615 MeV` → g13，v=`11.243664633572111`，首飞Δt=`0.06732749039338196`。原inf/错速已消除。 |
| W14-B真实后代 | Forward WW **285次**出库、Adjoint WW **54次**出库均按正确中心算速度且首飞时间通过。Forward首例g14/中心0.4015 MeV，v=`8.761446414522672`。独立U235小例有 **3次裂变后代出库**，首例g12/中心1.088 MeV，v=`14.414836198230065`，通过；CE WW另 **401次**出库保持MeV速度。 |
| ASan/UBSan原例及扩展 | **9/9运行退出0、无sanitizer诊断**：热群F/A、0.6615 F/A、WW F/A、离散谱F/A、裂变。对SampleParticle、SampleNeutronSource、ParticleStateFun、GetMgCs四个真实生产TU插桩，最终helper反汇编含ASan load8和float-cast-overflow检查；不是全程序/泄漏安全资格化。 |
| 非法输入防护 | **16/16负例拒绝、3/3合法群通过**，包含NaN/±inf、零/负/超界/非整数/巨大群号、G与数组尺寸、非法中心；带ASan/UBSan的独立helper测试退出0。 |
| 普通稳态/RNG回归 | **8/8修复前后精确一致**：MG F/A analog、MG F/A WW、MG F/A离散谱、CE analog/WW。每例101历史；Ave/RE及内存统计量、源/碰撞历史分母、空间/方向/能群/权重事件、逐历史与Bank RNG、WW行为一致；8份 `.Tally` 均逐字节相同，能群警告序列相同。统计器仅沿用Stage2逐字段wall-time/FOM例外，未跳过统计器整体。 |
| WW行为具体数字 | MG Forward：204次split判定、239次roulette判定、285次bank出库；MG Adjoint：26/132/54；CE：260/302/401，修复前后精确相同。split判定与实际push函数调用次数是不同计数，未混为同一指标。 |
| Stage2 FF/FAF+WW | **5/5轮与fresh-process oracle物理零容差一致**。FF为1000、2000历史；FAF+WW每轮500历史。模型仅初始化一次，每轮finalize一次，真实分母等于本轮N，源权重审计及RNG子流一致；最大draw分别1352/1856和5887/234/3997，均低于stride100000。 |
| 既有CTest | 修复前 **3/3**、修复后 **3/3**：`test_fixed_source_adjoint`、`test_fixed_source_1`、`prepared_source_weight_audit`；没有更新reference。 |

**独立审核发现的P1限制**：`CDExternalSource::SampleSimpleSpontaFissParticle` 在普通源采样后用Watt谱物理MeV覆盖能量，但不重算速度。对U-235 `PARTICLE=5` FISSMULT夹具，baseline完成，候选版在MG bank恢复处以`invalid internal group or center array`异常退出；扩展bank能量未保证为内部整数group。该调用族不在本任务ordinary源/普通诱发裂变bank自验覆盖内，不能以19速度例、9 sanitizer例或3次诱发bank恢复推断其通过。修复应另立获批任务；此处仅记录复核结果。详见[Claude独立审核](../20261017_02_independent-w14-repair-review/Independent_W14_Repair_Review.md)。

**物理解释（G4待用户确认）**：证据支持所测MG普通源与native WW/诱发后代的速度、首飞时间已纠正，同时所测稳态空间Tally与RNG保持。但Watt spontaneous-fission分支会在源速度初始化后替换物理能量，候选未同步速度，且扩展bank状态不满足新helper的整数群号合同，导致baseline可完成而候选异常退出。因此W14整体仍为NEEDS CORRECTION · P1，不得关闭。它不证明所有稳态通量/响应有偏，也不开放Stage2非零裂变连续F/A；此前F02/F03有界稳态结论不自动失效。

**独立遗留**：`p_nMultiGrpNumber`缓存不同步未修复。MG WW F/A中分别观察202/32次Bank缓存与p_dErg不一致；裂变Bank3次。速度/截面群号使用p_dErg，故不阻止本次已测速度门禁；Filter.cpp:75和ParticleTrack.cpp:343/363读取该缓存，带相关群过滤的统计/PTRAC语义尚未验证。CE没有MG缓存同步合同，不把CE的零缓存计作缺陷。

**未验证**：MPI/OMP/AIS、全Python源运行、MG photon/coupled、任意材料/模型/源形式、临界/动力学源的完整动态矩阵、所有时间分箱/velocity estimator输出、全程序/泄漏sanitizer及Windows。Python改动只通过启用宏TU编译；非零裂变只验证该普通Forward小模型的3次出库，不外推任意裂变谱与连续F/A。

原始证据保存在本任务 `logs/local-evidence/`（ignored，不入Git），约113 MiB；新构建及binary保留 `/tmp/w14-repair-20261017/`。没有清理用户文件。根仓库和RMC均未commit/push，RMC HEAD/分支保持不变，Stage3未实施。

## 5. 过程

| 日期 | 操作 / 事件 |
|---|---|
| 2026-10-17 | 自动脚本建立本任务，核对基线与干净工作树，读取两份独立证据；G1暂停并存用户授权。 |
| 2026-10-17 | 用户“请开始修复”；记录最小设计和预设判据，冻结基线独立构建；实施8文件修复并构建修复版。 |
| 2026-10-17 | 首次GDB被沙箱ptrace限制，保留日志后按已授权权限重试；没有修改inferior状态。 |
| 2026-10-17 | 测试输入生成器曾产生d100000000、分布块空行及空CEACE卡，均在输入解析阶段失败；修正测试输入，未改生产parser。失败日志保留，最终输入两侧一致。 |
| 2026-10-17 | 速度观察器函数入口/返回引用位置读数失效，改为明确函数内断点；原Stage2 BANK观察器也读到无效参数位置，改读Execute绑定的同一RNG对象。保留两版失败trace，完整重跑受影响门禁，零容差不变。 |
| 2026-10-17 | 完成19速度例、9 sanitizer例、8组普通回归、5轮prepared/fresh及两侧各3CTest，向用户发送中期快报。WW另有减少重复碰撞断点的补充观察，最终19例使用完整v3观察器。 |
| 2026-10-17 | Python TU显式宏编译首次缺少该配置include路径；按CMake实际PythonInterface include补齐后编译退出0，未宣称Python运行已覆盖。helper首次运行因沙箱LeakSanitizer受限失败，按预设关闭leak后退出0。 |
| 2026-10-17 | 保存补丁、关键计算/结果/原始证据和哈希清单，按“已实施、待独立审核”同步看板；G4等待用户结果确认，不提交、不进入Stage3。 |
| 2026-10-17 | Claude独立审核将W14判为NEEDS CORRECTION · P1 / OPEN：ordinary与WW限定路径通过，但type-5 spontaneous-fission Watt路径候选版exit 134、baseline exit 0；报告见`20261017_02_independent-w14-repair-review`。 |
| 2026-10-17 | Claude独立复核：ordinary fixed-energy、WW bank与普通Forward诱发裂变例通过限定审核；type-5 spontaneous-fission Watt路径候选版异常退出而baseline完成，判定NEEDS CORRECTION · P1 / OPEN。独立报告及共享状态指针见`20261017_02_independent-w14-repair-review`。 |
