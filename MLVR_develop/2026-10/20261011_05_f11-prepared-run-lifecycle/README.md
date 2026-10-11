# f11-prepared-run-lifecycle

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-10-11；原new_task.sh自动分配05，沿用本任务 |
| 状态 | 已完成（限定范围，自验通过；独立复核见任务07：NEEDS CORRECTION） |
| 任务类型 / 模式 | F11 Stage2正式生命周期实现 / C |
| 报告人 | Codex |
| 设计基线 | 知识库04；Task06原独立设计审查保留 |
| 修改范围 | 批准的29文件：24个已跟踪修改、5个新增；[清单](logs/implementation/actual-files.json) |
| 仓库身份 | 根main / 7171b29e；RMC Neural_Network_WW_Iteration / 330f091e；开始时无已有冲突改动、无未推送提交；本次未提交/推送/切分支 |

## 1. 目标与范围

实现一次完整模型初始化后的正式固定源多次运行入口，保持同一批Geometry、Material、raw MGACE、Tally definition和输运对象，连续执行相互独立的Forward/Adjoint half-run。逐段与普通RunCalculation的fresh-process oracle确定性比较。

本阶段仅支持受限Linux serial、standard MGACE、中子固定源、Type2 RNG、单个定点/定能/定向且实际单位初始权重源、Cartesian TL tally、native mesh WW及已验证的非裂变材料条件。没有CalcMLVR、TARGET、Field API、外部重构或完整FOM评价；未改W11/W12、阶段0结果、reference、核数据库和冻结04。未进入Stage3。

**物理解释（模式C）**：复用的是模型，不合并各轮样本。每条源历史及其后代的得分只进入本轮；零得分历史也在N内。单位有效起始权重需要独立实测W0并核对实际D，不能从输入WEIGHT=1或代码D←N直接推出。角色切换必须重建派生算子并恢复粒子/cache/WW策略；A→A不能重复累加。

## 2. 做法与证据

先在私有目录fresh configure/build未修改330f，完成8个普通正例、9个CTest及三组500-history诊断，**20:39:55 +0800冻结后才改生产代码**。[baseline-freeze.json](logs/baseline-freeze.json)绑定原源码、binary、编译配置和核数据库；WEIGHT=D1在原parser就失败，单列保留，不算输运通过。

实现三个public入口InitializePreparedFixedSourceRuns、RunPreparedFixedSource、FinishPreparedFixedSourceRuns；private Prepare按各owner执行KEEP/CLEAR/SET/REBUILD。普通入口只增加进程owner冲突保护，原Stage1 execution core逐字保持，唯一输运循环未复制。源审计hook在实际采样后、输运前核查w；RNG原公式保留，skip缓存转owner并检查子流/逐history用数；WW安装三界或恢复OFF策略；receipt独立记录三段steady-clock时间。

接口、状态与调用图：[lifecycle-design](lifecycle-design.md)、[state-ownership](state-ownership.md)、[source-call-graph](source-call-graph.md)。预设标准与实际命令入口：[test-plan](test-plan.md)。当前源码定位：[source-map-final.txt](logs/implementation/source-map-final.txt)。

| 门禁 | 真实结果 | 关键证据 |
|---|---|---|
| G0 构建/链接 | 两个executable成功链接；694个共同生产TU编译选项相同；各13个无条件全局单例及main各定义一次；test=OFF普通构建成功；不支持宏配置不注册prepared target | [linkage](logs/linkage/result.json)、[test-off](logs/linkage/test-off.json)、implementation/stage2-build-11 |
| G1 普通回归 | 123/123确定性比较；原9个CTest及新增权重audit共10/10；Forward、Adjoint、WW、Type1/2/3、常数WEIGHT=2及原photon/electron/coupled代表分支保持 | [最终比较](logs/ordinary-comparison-final-03/results.json)、[CTest原始输出](logs/implementation/final-ctest-02/stdout.txt)、logs/refactor-* |
| G2 FF | 1000→2000，每段源/RNG/原始矩/Ave/RE/VoV/PDF等价；源位置实际改变 | [FF比较](logs/gates-04/ff/comparison.json) |
| G3 FAF | 1000→1500→2000，三段均等fresh；最终F派生清空，角色及截止恢复 | [FAF比较](logs/gates-04/faf/comparison.json) |
| G4 AA | 1000→1500，两次完整A派生数组均逐项等fresh，无重复累加 | [AA比较](logs/gates-04/aa/comparison.json) |
| G5 WW | OFF→WW1→WW2→OFF及FAF+WW每段等fresh；实际三界、split/roulette/bank均观察并验证 | [WW比较](logs/gates-04/ww/comparison.json)、[FAF+WW](logs/gates-04/faf-ww/comparison.json) |
| G6 模型/资源 | 20轮F/A；完整初始化、MGACE读取、tally注册各一次；owner/raw/registry身份稳定；FD测量值19恒定；第4→20轮RSS净增84KiB，低于事前4MiB限制 | [复用比较](logs/gates-04/reuse/comparison.json)、[资源原表](logs/gates-04/reuse/persistent/resources.tsv) |
| G7 拒绝/失败 | 66/66负例按预期拒绝；前置拒绝旧数值/计数/RNG不变；真实stride超额后无成功receipt且无法重试/Finish；实际权重owner单测7/7 | [负例结果](logs/negative-final-02/results.json)、[运行时失败](logs/negative-final-02/stride-runtime/command/stdout.txt)、CTest |

最终34个half-run，对照侧同样34个fresh进程，**每侧17500条源历史**。所有成功run实际N=D=W0，检查次数=N，min=max=1，违规数0。逐run数字、seed、draw上限、Ave/RE和事件数量见[run-results.md](run-results.md)与[完整摘要](logs/gate-results.json)。例如WW1/WW2的split/roulette/bank分别为2072/3397/3975和3313/5675/7499；实际查窗三界逐条符合本轮lower×原WWP。

FF启用一个总通量cell及124个mesh诊断bin；两轮所有实际输出PDF（63/73个bin）及完整HDF（2519/2859个dataset）严格匹配，见[exports-final](logs/exports-final/ff/comparison.json)。只豁免事前列明的七个统计时间成员及五种HDF时间字段，其shape/数值类别/归属仍检查。比较器25项自测拒绝非时间字段、未知/缺失字段及非法时间类别的改动：[自测](logs/comparator-selftest.json)。没有把旧FOM作为本轮指标。

截止字段追加核查已修正并进入最终门禁：F未启用的伴随max恢复默认20 MeV；本次A的物理30 MeV转换为群1；返回F恢复20。三类role、实际neutron cutoff/weight policy及派生数组均与fresh一致。非零产生项负例的U235原始νσf和材料数密度也已取出，其νΣf范围约0.00732490096–3.24095584 cm⁻¹，初始化拒绝，见[核数据实测](logs/implementation/fission-raw-final/nu-sigma-f.json)。

**补丁与身份**：[changes.diff](changes.diff)包含24个跟踪文件；[new-files.diff](new-files.diff)完整包含5个新增文件。不能只取前者。[final-manifest.json](logs/implementation/final-manifest.json)绑定最终源码/私有构建副本/编译配置/binary/数据库/补丁；原baseline及未授权文件保护检查通过。GCC13.3、CMake3.28.3、HDF5 1.10.10、RelWithDebInfo，MPI/OMP/AIS/Python均off。baseline banner为330f，私有Stage2 banner为空Git SHA；身份以完整manifest核对，未冒用baseline SHA。

每条运行命令、cwd、stdout/stderr、退出码和原始数据均留存于上述目录的command/或implementation/。失败与修正见[失败台账](logs/implementation/failure-ledger.md)，没有删除失败用例或更新reference。构建、binary和完整私有运行目录在`/tmp/20261011_05_f11-prepared-run-lifecycle/`；任务原始压缩轨迹和快照保留本地，哈希见evidence-manifest.json。

## 3. 决策记录

**用户已正式批准实施**，原文：[user-authorization.txt](logs/implementation/user-authorization.txt)。批准最新设计§5的29文件与G0/Gate1–7，不需重复审批；本次严格在此范围内完成。早期设计待审批记录保留在logs/design-revision及logs/implementation/design-before-archive，不能把历史待审批状态当成当前权限。

**人类理解确认（模式C）**：用户授权明确限定单位有效权重、独立half-run、非零裂变/并行未开放及逐段fresh等价；本次按该合同实施。新结果仍待用户审阅和独立复核，未把Task06对旧设计的审查写成对本次代码的验收。

实施中对旧能群cell SCHECK崩溃采取受限入口拒绝，未触及清单外scorer。测试driver仅清自己的上一张HDF Tally输出组来隔离快照，保持同一输出句柄；没有更改生产writer、数学公式或F11总体设计。

回滚应以330f和manifest为依据，逐文件保留当前结果后只撤销本任务增量；新增5文件与补丁需一起处理，不用reset/checkout覆盖工作区。何时提交/推送仍由用户决定，本轮没有执行。

## 4. 结论与边界

**ACCEPT WITH LIMITATIONS —— 受限Stage2实现与自验完成；独立复核见任务07（NEEDS CORRECTION，2 项 P1）。**

| 验收问题 | 回答 |
|---|---|
| 1. 真正同进程多次运行？ | 是；一次Initialize，同一模型/对象上多次正式Run，每次Finalize一次。 |
| 2. FF、FAF、AA？ | 全部逐段确定性通过，并包含FAF+WW。 |
| 3. 模型完整初始化一次？ | 是；动态计数与owner/raw/registry身份共同验证。 |
| 4. RNG/tally/source/WW残留或差异？ | 最终受限门禁未发现物理差异；权重、子流、统计和实际查窗均通过。 |
| 5. 每次与fresh oracle一致？ | 是；34/34配对，物理容差0；时间例外逐字段记录。 |
| 6. 普通RMC行为？ | 已测普通分支123/123确定性比较、原9个CTest通过；source copy semantics与唯一core保持。 |
| 7. 尚未通过Gate？ | 最终受限G0/G1–7全部通过；历史失败已分类保留，限制外项目未验收。 |
| 8. Stage3技术条件？ | 受限运行基础已具备；先独立复核并取得新阶段授权。本任务停止，不启动Stage3。 |

**未解决及未覆盖边界**：

- 数值结论绑定本任务H2O、固定模型/群/网格、指定源和WW参数；不外推任意材料、复杂几何或所有可选功能。一般非零裂变连续F/A仍被拒绝。
- MPI/OMP/AIS/Python只检查了target注册条件，未开展这些配置的多轮数值验收；CE、耦合粒子、restart、复杂/加权/分布源等不属于prepared支持范围。普通已有功能的代表回归不等于prepared支持。
- **W13未修复**：未修改baseline已复现能群cell SCHECK崩溃。新入口拒绝该组合，用独立总通量cell诊断；W11/W12及体积语义保持。
- 旧HDF writer不是完整覆盖式per-run输出，测试只隔离自己的输出组。Field/WW HDF5、TARGET及正式FOM仍未开发。
- 起始权重运行时负例属于owner API单测；合法严格白名单不会自然生成非法初始权重。真实Run失败传播由stride超额门禁覆盖，未用私有注入伪造输运。
- 旧StatisticsTester FOM明确标为legacy混合时间。GDB会影响所测耗时，本轮不作性能排名或加速比结论。未做sanitizer/Windows/无限规模资源验证。

**结果解释**：本次证据支持限定对象生命周期和角色切换已实现；不代表完整F11闭环完成，也不改变冻结04或阶段0转换结论。Task06原报告保持原样；本次代码尚未取得独立审查结论。

## 5. 过程记录

| 时间（2026-10-11，+0800） | 事件 |
|---|---|
| 17:56起 | 原任务自动建档、源码定位、生命周期设计；Stage1基线由外部归档为330f，Agent未提交。 |
| 20:14起 | 按Task06补齐全局所有权、实际权重和单run时间三项设计缺口；设计历史原文保留。 |
| 正式授权后 | 核查根/RMC干净状态及本地upstream，记录完整授权和身份；先构建未修改baseline。 |
| 20:39:55 | 冻结baseline，随后开始29文件实施；私有构建、原普通回归、G0与逐段门禁。 |
| 实施/自验 | 保存编译错误、旧SCHECK崩溃、观察器失败、HDF快照残留和截止字段差异；逐项修正授权范围内实现或明确拒绝，见失败台账。 |
| 最终归档 | gates-04、ordinary-comparison-final-03、negative-final-02、exports-final及最终CTest全部完成；保存补丁、身份和原始证据，同步STATUS/INDEX/知识库/物理导读；停止待独立复核，无commit/push。 |
| 归档轮 | 用户指示整理提交；大产物（trace jsonl.gz、状态快照、stdout/stderr 等约 363MB）留本地，哈希清单 logs/artifact-manifest.sha256；档案与判定证据随根工作区提交并推送双远端；RMC 未提交。 |
