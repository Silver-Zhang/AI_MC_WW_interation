# f11-prepared-run-lifecycle

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-10-11；new_task.sh自动分配05 |
| 状态 | 待决策 |
| 任务类型 | 新功能 / 状态生命周期设计 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | Codex |
| 关联知识库条目 | F11；唯一设计基线知识库04 |
| 涉及文件 | 当前只写本任务档案与进度/知识库指针；拟生产文件见lifecycle-design §5 |
| 分支 / 提交 | RMC Neural_Network_WW_Iteration / 330f091eb0296e0d0124237ba7d9a22b81aee852；根main / 6e7516c14de322141aa2fb645e4de1ebdcc767ed |

## 1. 目标与范围

实现一次完整模型初始化后的正式固定源多次运行准备，以同一批Geometry/Material/rawMGACE/Tally definitions支撑FF、FAF、AA，每个half-run独立且与fresh oracle确定性等价。依据用户完整Stage2任务，当前授权立项、源码分析和具体设计，§7要求设计完成后单独取得源码修改批准。

本阶段不实现CalcMLVR/Bootstrap-K控制、MLVR parser、TARGET自动源、Field/WW HDF5或外部重构；不改体积计分/W11/W12/阶段0结果/reference/核数据库，不commit/push/reset/切分支。普通fixed-source六模式与source copy semantics继续保留。

**物理解释（模式C）**：每个run的估计值只能含它自己的源历史（含零得分history）与后代，分母只属本run。切换A改变的是由相同raw核数据派生的算子，回F须恢复原正向角色/cache/WW policy；不能重新叠加上一A派生量。逐run的history/RNG/原始统计/派生数组/查窗与fresh完全一致才支持受限重复运行；任何一个half-run差异都会推翻“清理和重建已充分”的主张。

原始材料/身份：完整任务文本logs/user-request.txt（附件请求正文，不是聊天转储）；logs/repository-start.json，stage1-start.diff/源文件及其哈希，stage2-start-src-sha256.json，source-evidence.txt，environment.json及compiler/cmake/python/hdf5原输出。参考[Task13实验](../../2026-09/20260929_13_f11-persistent-session-e0-e4-execution/F11_E0_E4_Dynamic_Experiment_Report.md)和[Task14独立复核](../../2026-09/20260929_14_independent-f11-e0-e4-dynamic-review/Independent_F11_E0_E4_Dynamic_Review.md)，只借风险/门禁，不搬实验seam。

## 2. 做法与证据

交付四份待审批设计：

- [state-ownership.md](state-ownership.md)：KEEP/CLEAR/SET/REBUILD逐状态组与当前行号。
- [source-call-graph.md](source-call-graph.md)：现有混合传参/实际private helper、拟正式入口和caller所有权。
- [lifecycle-design.md](lifecycle-design.md)：完整C++签名、Prepare时序、Type2子流、生产改动文件和回滚。
- [test-plan.md](test-plan.md)：330f重建baseline、逐run fresh oracle、七门禁、零物理容差与执行命令。

当前静态定位：CalMode.h:172/230/238/246/330证实Stage1 helper实际private；CalcFixedSource.cpp:147–769仍是唯一623行suite，ProcessTally仅:774；RunCalculation.cpp:6–13混合传值不适合反复进入。伴随数组+=在TreatAdjointMaterial.cpp:46/50/56等；SetZero.cpp:17–25未清Sum3/活动索引；Timer.h:96–99旧reset未清recordTime；StrideRNG.cpp:86–88使用function-static skip缓存。

选择：CDCalMode只增加三个受控public入口，内部Prepare协调各owner正式reset/rebuild；caller持有并持续借用同一批模型。固定raw数据/registry，局部active source副本，每run独立累计历史段。非零裂变产生项未门禁前在受限入口拒绝。

**生产实施/运行：无。** 未修改RMC，不创建假changes.diff；Stage1原补丁仅存logs/stage1-start.diff。本轮未编译、未输运、未执行Gate1–7；证据仅E1静态分析；完整源码/文档保护检查见logs/design-verification.json，归档自检原文见logs/archive-check/。Type2周期/有效seed的精确只读模运算记录在logs/rng-period-analysis.json，不是MC验收。

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

**决定：待用户批准。** 建议采纳lifecycle-design的受限owner生命周期接口与test-plan，批准后先完成330f fresh baseline冻结，再按§5文件清单修改生产源码并运行门禁。

**决定人/日期：尚无Stage2源码批准。** 先前“批准，继续完成”针对Stage1；最新“继续完成”推进当前工作，完整Stage2 §7明确要求具体方案提交后再批准，不能转写为尚未提出代码的批准。

| 风险 | 改动范围 | 验证与停止条件 | 回滚 |
|---|---|---|---|
| A派生+=、统计/银行/粒子缓存残留、RNG段重叠、WW-off保留旧cutoff、timer/句柄重入 | 已有owner扩展+根目录轻量spec/Prepare cpp+受限test driver；保留普通loop/数学公式；无TARGET/Field/MLVR调度 | Gate1–7逐run fresh、全部原始physics零容差；任意差异保留证据并定位，超出文件清单/物理修复停止补审批 | 保存330f每文件原文/hash；仅恢复本任务且hash吻合的增量，新增文件先留证据；不用reset/checkout |

**需批准的具体内容**：三个受控生产入口、各owner清理/重建方法、function-static RNG cache转owner及Type2用数保护、native WW运行间安装/关闭、timer新reset、受限测试target；prepared首版拒绝非零νΣf及未覆盖模式。普通入口和reference/数据库保持。

**人类理解确认（模式C）：待取得。** 请确认受限FF/FAF/AA与逐段fresh一致只证明该子域生命周期，不证明一般可裂变材料/完整F11。未获得确认前，不写用户已理解或已批准。

## 4. 结论与边界

- **当前判定：BLOCKED（等待§7明确源码批准；不是实验失败）。** 源码分析、具体接口/文件方案与门禁已经可review；尚无Stage2生产改动或动态通过结论，档案/台账状态为待决策。
- 已正式支持清理的状态：本阶段尚无新增实现；已有Stage1只有拆分入口。仅候选reset清单完成。
- 已确认模型只加载一次：当前仅拟合同，Stage2尚未动态证明；保留一次初始化的现有路径定位。
- FF/FAF/AA：未执行。fresh差异：尚未进行Stage2比较，不能写“无差异”。
- WW-on/RNG可复现：已有Stage1单run证据保留；Stage2连续更新/子流未验证。
- 裂变边界：prepared拟拒绝非零产生项；一般非零裂变FAFA不能借H2O门禁放行。
- Stage3基础：尚未具备通过验收的Stage2运行基础，不启动Stage3。
- 提交状态：本Agent未commit/push；RMC基线330f是外部阶段1归档操作，Stage2与该提交分开记录。档案随 2026-10-11 根工作区提交入库。

**结果解释**：E1支持需要清理/重建的具体位置与owner划分；尚不能证明该清单充分。完成受限动态门禁后才形成物理数值与生命周期结论。知识库04冻结正文、阶段0实验/转换口径不变，F11整体仍implementation not completed。

## 5. 过程记录

| 本地时间 | 操作/事件 |
|---|---|
| 2026-10-11 17:56 | new_task.sh f11-prepared-run-lifecycle F11 C 自动建立05；首次附件缺尾，后完整重传消除缺失 |
| 2026-10-11 18:02 | 读回外部Stage1归档后的根/RMC身份；保存原Stage1补丁、源与manifest，未覆盖工作区 |
| 2026-10-11 | 按KB04及Stage1/Task13/14指针检查owner相关路径；形成四份方案与预设门禁 |
| 2026-10-11 18:58 | 归档自检需处理0项（31项旧档案提示，本任务无提示）；848个src文件/04 hash不变，任务链接与五节结构检查通过 |
| 2026-10-11 | 收口时更正不存在的TallyProcess timer名称，补全fresh工作副本存活期取证；同步STATUS/INDEX/AGENT_CONTEXT和知识库指针，停止于§7审批 |
