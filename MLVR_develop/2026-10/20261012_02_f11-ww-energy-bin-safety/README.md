# F11 WW energy-bin P1 定向修复

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-10-12；new_task.sh 自动分配 02 |
| 状态 | 已完成（READY FOR INDEPENDENT REVIEW；待独立复核） |
| 任务模式 | C |
| 关联 | Task05；20261012_01 独立复核；知识库04唯一冻结基线 |

## 1. 目标与范围

修复 prepared native WW 的能量表形状/数值合同及共享查询的末界等值索引。仅修改 `PrepareFixedSourceRun.cpp`、`WeightWindows.cpp`、`WeightWindow.h`、原测试 `driver.cpp`。本轮增量见 [correction.diff](correction.diff)，包含原本未跟踪的两个文件；不是从330f091e起的整个Stage2补丁。

物理解释：B个能量边界只能对应B−1个权窗。内部等值仍归右侧区间，末界等值应归最后区间。`INFINITY_ENERGY=1e22` 是有限终止哨兵；查窗必须兼容它，但不表示MC物理源支持1e22 MeV。

## 2. 做法与证据

[源码依据](source-audit.md)记录修复前/后位置及预设判据；[命令](commands.md)和脚本支持复核。

| 验证 | 本轮实跑结果 | 精炼证据 |
|---|---|---|
| 普通RMC、prepared driver编译 | 两个目标退出0；GCC13.3、CMake3.28.3、RelWithDebInfo、MPI/OMP/AIS/Python OFF | regression-results build |
| G0 / CTest | 694个共用生产编译单元参数一致；13个全局对象各一次；10/10 CTest通过 | regression-results G0/CTest |
| 新形状/数值负例 | 26种×绑定前/首轮后/独立Install，共78/78；明确命中生产Validate抛错 | [negative-results.json](negative-results.json) |
| 真正lookup边界 | 12个有限能量精确返回预定三界，NaN/±Inf 3次受控拒绝；15/15 | regression-results lookup |
| ordinary native WW | 单窗及三窗各500历史；与修复前binary逐事件/IEEE值一致，Tally/材料及全部HDF数据一致，普通文本仅既定时间/构建身份例外 | regression-results ordinary_native_ww |
| prepared/fresh | FF 2、FAF 3、AA 2、WW OFF→1→2→OFF 4、FAF+WW 3、复用20、多能窗4，共38/38配对；物理容差0 | [regression-results.json](regression-results.json) |
| 既有负例 | 原合同66/66；上一轮WW标量/Universe等51/51 | regression-results existing_negatives |
| 定向ASan/UBSan | 两个改动生产cpp和driver插桩：78负例+lookup+四轮多窗，共80/80；无报告 | regression-results sanitizer |

三能窗ordinary实测18,450次查询，覆盖三个区间，894次分裂、1,063次轮盘；单窗22,518次查询、1,108次分裂、1,781次轮盘。前后轨迹SHA分别为 `fe6f3760…c3fbaf`、`4f863218…7c8d73f`，完整值在JSON。

首次绑定错误的模型初始化/CLEAR/source均0；首轮成功后的错误维持1/1/100，不执行第二轮，只有一个receipt；序列化的score、Sum1/2/3、Ave、RE、历史数、分母和RNG与拒绝前完全相同。GDB抛错栈直接经过owner验证，未借fingerprint拦截。独立Install还核查模式、截断值与激活标志不变。

所有运行原始命令、stdout/stderr、退出码、输入、snapshots、GDB及构建留在 `/tmp/20261012_02_f11-ww-energy-bin-safety/`，由 [evidence-manifest.json](evidence-manifest.json) 逐文件SHA256追溯；本任务归档16个文件；另同步6个进度/知识/物理说明文件，不搬运原始过程数据。历史Task05/Task07/最新独立审核原文保留。

## 3. 决策

用户[本轮授权原文](logs/authorization.txt)已明确批准三项定向源码修改和必要测试。模式C人类理解确认依据这份授权：修的是非法表拒绝和末端区间归属，split/roulette、RNG、tally物理公式保持原实现；不需重复申请相同权限。

统一owner方法在首次绑定、Run的fingerprint/CLEAR之前、enabled Install的下标访问及状态修改之前执行。未声明WW且OFF的合法模型保持支持。额外确认普通初始化会遍历四个粒子槽位，因此已安装mesh容器须保留这些槽位，受限入口拒绝非中子窗；仍在授权文件内完成。

仅可依据本轮增量撤回本轮四文件修改，不能reset或覆盖原29文件Stage2成果；`git apply --reverse --check correction.diff`已通过，只做检查未应用。累计Stage2 tracked/new-files快照留在本地 `evidence/final/`。未commit/push、切分支、改reference/核数据或知识库04。

## 4. 结论与边界

**READY FOR INDEPENDENT REVIEW**。修复与自验完成，建议提交Claude独立最终复核；不自行给Stage2最终ACCEPT。

| 用户验收问题 | 本轮回答 |
|---|---|
| neutron能量表下标是否保护 | 是，受限prepared三入口复用同一owner校验；共享查询另有outer/inner/有限能量/串行数据形状保护。未宣称所有普通WW API已全面加固 |
| 末界等值是否安全 | 是，生产lookup实际返回B−2区间及正确三界 |
| 是否兼容原生哨兵 | 是，末界必须为有限1e22；IEEE无穷拒绝 |
| 非法形状是否命中生产guard | 是，78项均有实际容器内容、明确错误及生产抛错栈 |
| 是否在CLEAR前拒绝 | 是，绑定前计数0；首轮后计数不再增加，旧结果保留 |
| 普通native WW行为是否保持 | 已测单窗/三窗前后完全确定性一致，实际split/roulette与输出受检 |
| FF/FAF/AA/WW是否逐次fresh一致 | 是，包含资源复用和新增多能窗，共38配对；初始化一次、registry/原始模型地址及RNG子流门禁通过 |
| 是否发现新的P0/P1 | 在本轮授权范围与动态覆盖内未发现；不外推全RMC安全性 |
| 是否建议独立复核 | 是；历史NEEDS CORRECTION结论保留，交由新复核判断P1是否关闭 |

结果解释：确定性一致支持正常查窗与连续运行行为保持；owner末界测试专门覆盖真实MG源到不了的哨兵等值。时间例外仅沿用既定字段名单，统计矩、RE、非时间诊断及trace继续精确比较；不从旧StatisticsTester的进程累计FOM推出本轮FOM。

边界不扩展：Linux串行standard MGACE、中子、Type2、受限单位点源、非零裂变产生项拒绝、Cartesian native WW；不实现TARGET/Field/正式FOM或Stage3。未新验MPI/OMP、MCNP专门回归或普通任意坏parser输入；sanitizer只插桩三编译单元，其他生产对象/库未插桩，关闭leak检查，不宣称全程序/泄漏验证。历史Universe两轮fresh配对及123项ordinary大门禁未整体重跑，本轮替代/重跑范围明确列在JSON；W11/W12/W13保持原状态。

## 5. 过程

立项→原始授权/现场快照→真实边界定位→四文件实施→编译/负例/确定性与sanitizer验证→小型归档。预设判据未放宽；初版与增加四槽完整性检查后的构建/ordinary结果均留本地，最终判定使用最终源码和binary。比较器后续只纠正单窗结果的区间编号展示（应为0），对同一原始轨迹重新分析通过，没有放宽判据。归档检查0个需处理项；31项提示均为既有历史档案。

开始时根仓库main/`037a7cf6`干净（identity快照在建档后捕获，已含新README/INDEX）；RMC为Neural_Network_WW_Iteration/`330f091e`，24 tracked修改+5 untracked，upstream ahead/behind均0。结束HEAD/分支未变；2,106个源码/测试文件校验仅授权四文件改变，原始与最终私有构建源码分别精确匹配；15,196个历史证据/冻结文档文件SHA未变，xsdir与mgxsnp SHA和此前记录一致。

本轮归档不提交，完成后停止，等待独立复核及用户后续决定。
