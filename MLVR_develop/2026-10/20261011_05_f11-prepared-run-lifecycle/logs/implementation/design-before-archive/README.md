# f11-prepared-run-lifecycle

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-10-11；new_task.sh自动分配05 |
| 状态 | 实施中（用户已正式批准29文件及G0/Gate1–7） |
| 任务类型 | 新功能 / 状态生命周期设计 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | Codex |
| 关联知识库条目 | F11；唯一设计基线知识库04 |
| 涉及文件 | 当前只写本任务档案与进度/知识库指针；拟生产文件见lifecycle-design §5 |
| 分支 / 提交 | RMC Neural_Network_WW_Iteration / 330f091eb0296e0d0124237ba7d9a22b81aee852；根main / 80774e875f7bf759bbdef10fc5f6b31ea0f37afc（本次修订开始；原立项身份保留在logs） |

## 1. 目标与范围

实现一次完整模型初始化后的正式固定源多次运行准备，以同一批Geometry/Material/rawMGACE/Tally definitions支撑FF、FAF、AA，每个half-run独立且与fresh oracle确定性等价。依据用户完整Stage2任务，当前授权立项、源码分析和具体设计，§7要求设计完成后单独取得源码修改批准。

本次2026-10-11定向修订授权仅为只读核查、修改本Task05设计及同步进度指针。沿用原模式C任务05，不另建任务、不改Task06独立报告；用户最新请求§7/§8明确要求设计收口后停止、等待具体Stage2源码批准。

本阶段不实现CalcMLVR/Bootstrap-K控制、MLVR parser、TARGET自动源、Field/WW HDF5或外部重构；不改体积计分/W11/W12/阶段0结果/reference/核数据库，不commit/push/reset/切分支。普通fixed-source六模式与source copy semantics继续保留。

**物理解释（模式C）**：每个run的估计值只能含它自己的源历史（含零得分history）与后代，分母只属本run。切换A改变的是由相同raw核数据派生的算子，回F须恢复原正向角色/cache/WW policy；不能重新叠加上一A派生量。逐run的history/RNG/原始统计/派生数组/查窗与fresh完全一致才支持受限重复运行；任何一个half-run差异都会推翻“清理和重建已充分”的主张。

原始材料/身份：完整任务文本logs/user-request.txt（附件请求正文，不是聊天转储）；logs/repository-start.json，stage1-start.diff/源文件及其哈希，stage2-start-src-sha256.json，source-evidence.txt，environment.json及compiler/cmake/python/hdf5原输出。参考[Task13实验](../../2026-09/20260929_13_f11-persistent-session-e0-e4-execution/F11_E0_E4_Dynamic_Experiment_Report.md)和[Task14独立复核](../../2026-09/20260929_14_independent-f11-e0-e4-dynamic-review/Independent_F11_E0_E4_Dynamic_Review.md)，只借风险/门禁，不搬实验seam。

## 2. 做法与证据

交付四份待审批设计：

- [state-ownership.md](state-ownership.md)：KEEP/CLEAR/SET/REBUILD逐状态组与当前行号。
- [source-call-graph.md](source-call-graph.md)：现有混合传参/实际private helper、拟正式入口和caller所有权。
- [lifecycle-design.md](lifecycle-design.md)：完整C++签名、Prepare时序、Type2子流、生产改动文件和回滚。
- [test-plan.md](test-plan.md)：330f重建baseline、逐run fresh oracle、原七门禁及新增G0链接检查、源负例/计时精确白名单、零物理容差与执行命令。

原立项时的静态定位：CalMode.h:172/230/238/246/330证实Stage1 helper实际private；CalcFixedSource.cpp:147–769仍是唯一623行suite，ProcessTally仅:774；RunCalculation.cpp:6–13混合传值不适合反复进入。伴随数组+=在TreatAdjointMaterial.cpp:46/50/56等；TallyData.cpp:17–24未清Sum3/活动索引；Timer.h:96–99旧reset未清recordTime；StrideRNG.cpp:86–88使用function-static skip缓存。

选择：CDCalMode只增加三个受控public入口，内部Prepare协调各owner正式reset/rebuild；caller持有并持续借用同一批模型。固定raw数据/registry，局部active source副本，每run独立累计历史段。非零裂变产生项未门禁前在受限入口拒绝。

**生产实施/运行：无。** 未修改RMC，不创建假changes.diff；Stage1原补丁仅存logs/stage1-start.diff。本轮未编译、未输运、未执行Gate1–7；证据仅E1静态分析；完整源码/文档保护检查见logs/design-verification.json，归档自检原文见logs/archive-check/。Type2周期/有效seed的精确只读模运算记录在logs/rng-period-analysis.json，不是MC验收。

**独立审查后的三项定向修订**：审查依据为[Task06独立报告](../20261011_06_independent-f11-prepared-lifecycle-review/Independent_F11_Stage2_Review.md)及其risk-register/state-ownership-audit；原报告及其DESIGN REVIEW ONLY结论保持原样。本次实际HEAD下的原样修订请求见logs/design-revision/user-request.txt；新证据在[logs/design-revision/source-evidence.txt](logs/design-revision/source-evidence.txt)、extern-inventory.json、start.json；修订前五份文档原文另存before-*，不覆盖原logs。

| 问题 / 当前事实 | 定向方案与拟修改点 | 观察行为 / 门禁 / 未开放范围 |
|---|---|---|
| 全局链接：main.cpp:28–55定义单例，CMakeLists.txt:661–675将main纳入glob | 测试target源副本只排main，新增test-only globals.cpp逐对象定义一次；root CMake末尾注册，不改main或原tests/CMakeLists.txt；详见lifecycle-design §5.1 | G0源码表/宏/符号/link检查，G1普通回归；不支持宏下不注册prepared target，不宣称并行支持 |
| 权重：SampleParticle.cpp:25–29、SampleValue.cpp:11–73可修正实际w；InitialBatchSource.cpp:298只是D←历史数 | 严格无用户分布的单点/定能/定向单位源合同；ExternalSource校验；SampleNeutronSource.cpp新增采样后guard；FixedSource owner独立实测W0；详见§3.1 | 每history检查w==1，含零得分；N/D/W0及次数分别记录，违规run失败无成功receipt；G1普通加权源回归、G2–G6逐段核验、G7a/b负例；不开放任意权重源 |
| 计时：StatisticsFunc.cpp:124/184/218读Total，:177–180读非零history累计时间 | Prepare协调器steady_clock三段/求和receipt；旧统计公式保留并标legacy_mixed_not_per_run；详见§3.2 | G2–G6时间边界/标签检查，比较仅五个HDF统计后缀及对应内存字段例外，其余统计精确比较；不实现TARGET或新FOM评价 |

本轮静态收口检查（[verification.json](logs/design-revision/verification.json)；可重跑verify-docs.py）：848个RMC src文件及源码集合不变，合计859个保护文件（含Task06、KB04及构建入口）hash不变；RMC工作区仍干净。五节结构、本任务相对链接和git diff --check通过；归档检查exit=0、需处理0项（31条旧档案提示，本任务无提示）。待审批清单共29个文件：25个生产src文件（其中2个新增）、根CMake及3个新增测试文件，逐项见[planned-files.json](logs/design-revision/planned-files.json)和lifecycle-design §5。此处只运行文档/保护检查，没有CMake、编译、CTest或输运实验。

修订开始：root main/80774e875f7bf759bbdef10fc5f6b31ea0f37afc，RMC Neural_Network_WW_Iteration/330f091eb0296e0d0124237ba7d9a22b81aee852；两工作树干净，未推送本地提交均空。实际日志见start.json。本轮没有重新核验编译器/数据库运行可用性，以下环境是**原立项记录**，不得当作本轮新构建/测试证据；实施前按test-plan重新冻结身份。

真实环境与仓库检查输出（完整command/exit/stdout/stderr在logs）：

~~~text
RMC HEAD：330f091eb0296e0d0124237ba7d9a22b81aee852
RMC branch：Neural_Network_WW_Iteration
RMC status --porcelain：空
upstream ahead/behind：0 0；未推送提交：空
root HEAD：6e7516c14de322141aa2fb645e4de1ebdcc767ed
root branch：main；upstream ahead/behind：0 0
Stage1两源hash与其已验证构建manifest：一致
GCC 13.3.0 / CMake 3.28.3 / Python 3.12.3 / HDF5 1.10.10
保留Stage1 serial binary SHA：
2b432bc5898b939ae389b97da31b3eca934e6397f593da5a9703e5b4c1c1e07e
~~~

初查看到c3ef0934和Stage1两文件未提交修改；读取期间外部操作将Stage1存档到330f091e并同步远端，根仓库也更新到6e7516c。随后读回hash一致且工作树干净，故以330f为Stage2基线；本Agent没有执行提交/push。先前尝试比对dirty diff因其已提交而失败，改为保存已归档Stage1补丁与源hash，没有恢复/覆盖代码。

未覆盖验证：全部Stage2编译/输运/FF/FAF/AA/native-WW/RNG/资源/负例门禁；非零裂变连续切换；并行/Windows及受限profile之外功能。Stage1已有测试不能替代Stage2动态验证。

## 3. 决策记录

**最新决定：用户已正式批准生产实施。** 2026-10-11，授权原文见 [logs/implementation/user-authorization.txt](logs/implementation/user-authorization.txt)。批准最新lifecycle-design §5的29文件及G0/Gate1–7；不需再次提交设计审批。必须先fresh baseline冻结再改源码；清单外文件、冻结物理/输运算法/reference变化须停止该部分并补授权。此前待审批记录保留为历史，不代表当前权限。

**决定：本次三项修订已完成，Stage2源码修改仍待用户批准。** 建议批准当前[lifecycle-design §5完整清单](lifecycle-design.md#5-实际拟改文件理由回滚)及test-plan；批准后先完成330f fresh baseline冻结，再实施，不沿用修订前文件范围。

**决定人/日期：尚无Stage2源码批准。** 先前“批准，继续完成”针对Stage1；本次最新《Stage2—设计修订与实施前收口》§7/§8再次明确只授权设计、完成后等待批准。不能把这次修订或此前继续指令写成生产修改许可。

| 风险 | 改动范围 | 验证与停止条件 | 回滚 |
|---|---|---|---|
| A派生+=、统计/银行/粒子缓存残留、RNG段重叠、WW-off保留旧cutoff、timer/句柄重入 | 已有owner扩展+根目录轻量spec/Prepare cpp+受限test driver；保留普通loop/数学公式；无TARGET/Field/MLVR调度 | G0链接及Gate1–7逐run fresh、全部原始physics零容差；任意差异保留证据并定位，超出文件清单/物理修复停止补审批 | 保存330f每文件原文/hash；仅恢复本任务且hash吻合的增量，新增文件先留证据；不用reset/checkout |

**需批准的具体内容**：三个受控生产入口、各owner清理/重建方法、function-static RNG cache转owner及Type2用数保护、native WW运行间安装/关闭、timer新reset、受限测试target；prepared首版拒绝非零νΣf及未覆盖模式。普通入口和reference/数据库保持。

**此次额外审批范围**：新增触及生产`src/SampleNeutronSource.cpp`的prepared专用检查hook；新增测试`tests/prepared_fixed_source_lifecycle/globals.cpp`；在原FixedSource/ExternalSource/Prepare/spec文件中补权重audit、实际D/W0、三段耗时及旧统计标签。`tests/CMakeLists.txt`从拟改清单移除，改由根CMake末尾注册新子目录。原`main.cpp`、通用source抽样/分母/tally公式和reference仍不改。完整清单以lifecycle-design §5为准；额外文件或算法变化必须重新说明并批准。

**人类理解确认（模式C）：待取得。** 请确认受限FF/FAF/AA与逐段fresh一致只证明该子域生命周期，不证明一般可裂变材料/完整F11。未获得确认前，不写用户已理解或已批准。

## 4. 结论与边界

- **当前判定：READY FOR IMPLEMENTATION APPROVAL。** 三项实施前缺口已在设计层面关闭，具体方案/文件/运行时拒绝/比较门禁可供用户审批；未发现仍阻止提交审批的设计问题。此判定只说明设计收口，**不是Stage2实现ACCEPT**；仍无生产改动或动态通过结论，档案/台账继续待决策。修订方案尚待独立复核，不能把Task06对旧稿的审查改写成对本次新稿的通过。
- 已正式支持清理的状态：本阶段尚无新增实现；已有Stage1只有拆分入口。仅候选reset清单完成。
- 已确认模型只加载一次：当前仅拟合同，Stage2尚未动态证明；保留一次初始化的现有路径定位。
- FF/FAF/AA：未执行。fresh差异：尚未进行Stage2比较，不能写“无差异”。
- WW-on/RNG可复现：已有Stage1单run证据保留；Stage2连续更新/子流未验证。
- 裂变边界：prepared拟拒绝非零产生项；一般非零裂变FAFA不能借H2O门禁放行。
- Stage3基础：尚未具备通过验收的Stage2运行基础，不启动Stage3。
- 提交状态：本Agent未commit/push；RMC基线330f是外部阶段1归档操作，Stage2与该提交分开记录。原档案已随外部根工作区提交入库；本次修订随 2026-10-11 根工作区追加提交入库。

**仍未解决的适用范围**：任意源权重/用户分布、多源、并行/AIS/Python、一般非零裂变连续切换均未开放；旧StatisticsTester仍是legacy混合计时，不能作单run FOM；这些边界不会被本次设计收口提升Ready。

**结果解释**：E1支持需要清理/重建的具体位置与owner划分；尚不能证明该清单充分。完成受限动态门禁后才形成物理数值与生命周期结论。知识库04冻结正文、阶段0实验/转换口径不变，F11整体仍implementation not completed。

## 5. 过程记录

| 本地时间 | 操作/事件 |
|---|---|
| 2026-10-11 17:56 | new_task.sh f11-prepared-run-lifecycle F11 C 自动建立05；首次附件缺尾，后完整重传消除缺失 |
| 2026-10-11 18:02 | 读回外部Stage1归档后的根/RMC身份；保存原Stage1补丁、源与manifest，未覆盖工作区 |
| 2026-10-11 | 按KB04及Stage1/Task13/14指针检查owner相关路径；形成四份方案与预设门禁 |
| 2026-10-11 18:58 | 归档自检需处理0项（31项旧档案提示，本任务无提示）；848个src文件/04 hash不变，任务链接与五节结构检查通过 |
| 2026-10-11 | 收口时更正不存在的TallyProcess timer名称，补全fresh工作副本存活期取证；同步STATUS/INDEX/AGENT_CONTEXT和知识库指针，停止于§7审批 |
| 2026-10-11 20:14 +0800 | 按用户定向修订请求核对Task06及当前330f源码；补齐全局TU唯一性、源权重静态/运行时防线、三段计时和逐字段例外；更新五份方案，Task06/KB04/RMC均保持；停止于生产修改审批 |
