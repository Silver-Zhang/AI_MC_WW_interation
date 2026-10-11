# F11阶段1：固定源执行核心重构

| 项目 | 内容 |
|---|---|
| 立项日期 | 2026-10-11，new_task.sh自动分配04；沿用同一任务 |
| 状态 | 已完成（ACCEPT WITH LIMITATIONS；待独立复核/用户验收） |
| 任务模式 | C — 深度物理研究与学习 |
| 类型 / 关联KB | 最小结构重构；F11，04 §3.3/§5/§14 |
| 实施授权 | 用户在方案提交后明确回复“批准，继续完成”，记录见§3 |
| 实际改动 | 仅RMC/src/CalMode.h、RMC/src/CalcFixedSource.cpp；已按用户决定以单次提交存档推送 `330f091e` |
| 提交/保护 | 本Agent轮内未commit/push、切分支或reset；未改核数据库、既有测试/reference、W11/W12或阶段0实验；用户于 2026-10-11 决定将本改动以单次提交存档推送（RMC `330f091e`）；档案随根工作区提交入库（关键数据；原始运行/构建/诊断产物留本地，逐项 SHA256 见 logs/archive-manifest.json） |

## 1. 目标与范围

以冻结知识库04为唯一设计基线，将普通CalcFixedSource拆为一次完整初始化、唯一prepared execution core和一次最终统计；普通wrapper继续拥有外源按值副本、CBurnup寿命、计时及可选收尾。只实现阶段1；不实现CalcMLVR、parser/TARGET/Field/WW接口、外部命令、CLEAR/SET/REBUILD或同进程重复运行。

**模式C物理解释**：结构移动不应改变源历史随机数、碰撞/散射/裂变/权重、真实后代次序或history得分与分母。固定种子fresh-process应得到确定性一致物理结果。实际墙钟时间和含时间的FOM可以不同；其统计定义、调用范围和输出语义须保持。prepared接口不代表已有完整reset能力。

## 2. 做法与证据

### 代码与接口

[source-map.md](source-map.md)保存原HEAD源码图、owner/传参及实施工作树位置；[refactor-design.md](refactor-design.md)保留获批方案；[test-plan.md](test-plan.md)保留事前判据及执行补充；[changes.diff](changes.diff)是实际生产补丁，[proposed-refactor.diff](proposed-refactor.diff)是审批前提案。无新增未跟踪生产文件。

普通路径：CalcFixedSource→InitializeFixedSourceModel→ExecuteFixedSourcePrepared→FinalizeFixedSourceRun→原普通输出/可选收尾。函数均为已有CDCalMode public成员，不引入Session/Controller/Manager或src/MLVR。

| 实际文件/行号 | 变化 |
|---|---|
| CalMode.h:230/238/246 | 声明三个新成员；prepared/reset边界注释 |
| CalcFixedSource.cpp:67–112 | 原签名和source按值保持；wrapper保留timer reg/start/stop、局部CBurnup和原可选尾部 |
| CalcFixedSource.cpp:114–139 | 原77–95初始化块原样移动，包括现有InitiateAll、缓存及电子/光子准备 |
| CalcFixedSource.cpp:141–770 | 唯一execution core，原97–719共623行原样位于147–769，含全部六模式分支及FinalizeLoadBalanceChecker |
| CalcFixedSource.cpp:772–775 | 唯一最终ProcessTally调用；每次普通计算wrapper只调用Finalize一次 |

原623行body SHA256为65828f852a7fb5b8cf34332970257ac795702cf84a1a51503f3b54ca98a42173；实施后完全相同且仅出现一次。普通初始化块/原可选尾部也逐字保留，证据logs/implementation-structure.json。外源core引用指向wrapper的局部按值副本；CBurnup仍在wrapper活到返回；初始化后不复制tally/model/particle owner。原history/batch/descendant代码是一套六分支suite，不是六分支被删减为一个算法。

### 身份、环境与执行次序

RMC全过程分支Neural_Network_WW_Iteration，HEAD c3ef093497ea42c54569a87ed3696642c8b42931，初始干净且相对本地upstream无未推送提交。原根HEAD/状态见logs/repository-state.json；批准续作时实际根HEAD见logs/approval-resume-state.json（用户在两轮间已将设计档案入库）。本Agent本轮没有提交。所有原修改保留；结束只增加两批准生产文件差异。

GCC13.3.0、CMake/CTest3.28.3、Python3.12.3、HDF51.10.10；h5dump/mpicxx/PyYAML可用，不依赖系统h5py/numpy。无训练，src/config.py/CUDA/PyTorch不适用。串行与MPI/OMP两对构建均使用RelWithDebInfo/-O2 -g/同宏选项；实际flags/CMakeCache在logs，比较103/103中包含两对defines/flags完全相等检查。

baseline及refactor均从当前树复制到/tmp独立源码/构建目录，源码/src/include与版本绑定；只在私有delivery/GITSHA填入实际HEAD，避免生产CMake触发submodule更新。modified binary身份以HEAD+changes.diff+source manifest+binary SHA闭合，不靠同HEAD banner冒充代码相同。

完整命令/cwd/env/UTC开始时间/stdout/stderr/退出码位于logs/<baseline/refactor>-configure、build、mpi-configure、mpi-build、ctest及各cases。四组配置/编译退出均0，source manifest、flags、缓存、four-binaries.json保留；二进制和构建目录在/tmp不入档案。核数据库根/home/silver/NucXS_Library/RMC_DATA，MG实际xsdir/mgxsnp身份在test-environment.json，其余原用例使用同一实际库和未修改输入。

**顺序**：先未修改源码fresh configure/build、5任务用例、3诊断、9/9 CTest与MPI/OMP编译→baseline-freeze.json→应用获批两文件补丁→新版fresh configure/build→同用例/CTest/诊断→严格比较。旧阶段0 binary未作为唯一或当前基线。

新增adjoint输入缺模块空行，首次只输入校验失败（退出1）；仅修任务输入空行，物理设置/判据不变，原失败保留baseline-cases/mg-neutron-adjoint，有效旧例在baseline-corrected-cases。第一次apply相对补丁路径找不到，退出128无修改；绝对路径应用退出0。未为此改生产算法或reference。

既有execute.py会清理成功输出，因此首次修改前CTest提供通过证据，但原始产物被删除。后续为保留确定性对照，又用**已冻结未修改binary**与冻结原输入直接运行九例，在baseline-existing-cases/refactor-existing-cases保存真实输出；没有重建/改变旧binary，没有改运行器或reference。

### 验证及真实输出

任务5例输入、种子/配置快照在inputs与logs/executed-inputs.json。MG四例N=5000、Type2/seed17/stride100000；native WW实际下界0.1/1.0交替；batch interval=1000形成5个batch。NP代表N=2000、同显式RNG；现有九例原输入/原随机配置不变。

| 用例 | 旧/新退出码 | 实际源数 | 数值与输出 |
|---|---|---:|---|
| MG neutron analog | 0/0 | 5000/5000 | Tally逐字、HDF5物理、摘要一致 |
| MG neutron native WW | 0/0 | 5000/5000 | 同上；后代行为另有诊断 |
| MG neutron adjoint | 0/0 | 5000/5000 | 同上；旧/新均1个原有群上界warning |
| MG neutron multi-batch | 0/0 | 5000/5000 | 同上，全部接续HDF5一致 |
| NP代表 | 0/0 | 2000/2000 | 同上；旧/新均676个既有warning，不在本轮修复 |
| 既有9例直接捕获 | 全部0/0 | 原输入不变 | N/P/E/PE/NPE、CE/TMS、MG、native WW、接续结果一致 |
| 既有CTest | 0/0 | — | 旧9/9，新9/9，reference未更新 |
| MPI/OMP构建 | 0/0 | — | 只编译，不外推为并行数值回归 |

两边CTest真实输出末行均为：

```text
100% tests passed, 0 tests failed out of 9
```

三MG小诊断只改N=500，走普通完整初始化/输运/统计。只读GDB，无friend/token/写内存/跳初始化。源、真实RNG、所有tally前的物理段、history score、最终Score/ScoreTemp/Sum1/Sum2/Ave/RE原始IEEE字节、分母、registry和源复制关系全比较；每例Init=1、Process=1、M=500，registry=2且都属当前owner，源副本隔离为true。

| 500历史诊断 | 旧/新计数或SHA |
|---|---|
| Forward | segment=9666；整事件SHA b16d35e4bb5be9dd555c4458380c97032fdd6b61b5f7ac4e2b3ae19c257bdadd |
| Adjoint | segment=1844；整事件SHA e5b84b59c175ab2020223a1b2ab5b9342c50fb271b0229996d93e8af386340dc |
| Native WW | split=1108、roulette=1781、bank sample=2099、track=2599、segment=21315；整事件SHA 5444946ffdfbe9ad1617459aaf2e1b66b2d8dc77640a1b8211c86eecbac1c093 |

全部诊断result.json（含完整vector bits）相等，源/随机/段/history整体SHA也逐项相等；GDB原始stdout为lossless gzip，manifest保存解压SHA；并非只比较RMC文本打印。

**严格比较**：初次全HDF比较102/103，唯一差异为fixed_source_4统计检查的六个wall-clock FOM数据值。源码StatisticsFunc.cpp:124–125/180/218明确包含实测时间；按事前test-plan §7允许计时/FOM变动的类别，将精确六路径DATA值归类，类型/形状仍保留，所有其它值要求完全一致。原失败结果/diff在logs/comparison，分类证据timing-FOM-classification.json；未放宽物理容差，也未更新reference。

最终比较真实输出（logs/final-comparison-command，退出0）：

```text
Exact comparison: 103 / 103
Failed: []
```

包含14组ordinary输出：Tally逐字、.out只规范事前时间字段、material完全一致；HDF5全部dataset用17有效位比较，仅上述六个FOM的DATA体规范，dtype/shape仍相等。HDF完整原始转储gzip已保留；physical tolerance=0。不以统计误差一致替代确定性回归。

## 3. 决策

用户先要求“完成源码分析和具体修改方案后，先停止，等待用户批准RMC源码修改”；分析与具体补丁提交后，用户直接回复**“批准，继续完成”**。该授权覆盖两个文件最小重构和已列验证，实际实施未扩大到后续F11功能。

**人类理解确认**：用户批准了上轮明确说明的原623行仅移动、普通外源工作副本/CBurnup生命周期保留、ProcessTally每次一次、完整初始化不作reset、基线与回归的方案。最终新结果解释尚待用户/独立复核接收，不伪造人已接受新结果。

| 变更卡 | 内容 |
|---|---|
| 问题与风险 | 原入口混合模型加载/输运/统计/输出；抽取可能改变随机数、后代或owner寿命 |
| 已改对象 | 仅CalMode.h与CalcFixedSource.cpp，3个成员入口 |
| 保持边界 | 物理公式、tally体积语义、source sampling、已有六模式、reference与数据保持 |
| 验证 | 已冻结旧binary→新fresh程序；零物理容差、9/9原CTest、3组完整诊断；MPI/OMP仅编译 |
| 回滚 | 用实际changes.diff先反向apply-check；只有确认无人后改才反向应用这两文件，不reset/覆盖其它工作 |

## 4. 结论与边界

**ACCEPT WITH LIMITATIONS（阶段1结构与限定ordinary fresh-process回归；待独立复核/用户验收）。**

**模式C结果解释**：同一物理源历史的随机数、物理段与history score序列、最终IEEE统计和源隔离完全一致，且全6模式代表fresh回归/原CTest通过，支持“此次函数边界提取未改变已测普通计算”。时间/FOM数值随实际运行变化不属于物理回归；相关数学与原timer调用/覆盖范围保持。此结论不证明重复运行、owner reset或完整F11已经实现。

| 最终验收问题 | 回答 |
|---|---|
| 普通CalcFixedSource仍正常？ | 是，5新用例+9原例及CTest全部正常；原入口/外源按值签名保留 |
| 只有一份实际执行代码？ | 是，唯一ExecuteFixedSourcePrepared含原623行/6分支suite；hash相同，未复制/重写 |
| 初始化/执行/统计职责清楚？ | 是，3个成员边界；普通timer、CBurnup及可选收尾仍在wrapper |
| Forward/MG Adjoint/native WW回归通过？ | 是，确定性输出及500历史诊断一致；WW分裂/轮盘/bank真实命中 |
| 原数值与输出行为保持？ | 已测范围完全一致；明确的墙钟/时间FOM数据值允许变化，没有物理容差 |
| 为阶段2提供prepared入口？ | 是，公开确切签名并保留现有对象引用，未加入隐藏状态布尔组合 |
| 哪些对象缺正式reset？ | FixedSource完成/批次/计数/bank与哨兵；ExternalSource工作源库/面源进度；tally统计/高阶诊断/索引集合（保留registry）；AceData角色/伴随派生/物理群截止；ParticleState几何/截面/微扰/伴随缓存；RNG段及跳跃状态；WW三界/瞬态；Timer逐次计时、Output逐次文件生命周期。详见source-map末节 |

**未覆盖到的验证**：同进程F→F/F→A→F/多轮、正式CLEAR/SET/REBUILD、TARGET/Field/WW新接口；MPI/OMP数值运行、TIME_REDUCE/墙钟stop-time、完整WWG/MCNP shared-WW、Python源插件、Windows、GPU/大型算例均未覆盖。原可选分支源码/次序保留；不能拿编译成功或serial代表例替代这些运行门禁。未修W11/W12，未改阶段0体积实验；03复核档案的遗留README未在本轮处理。

本次完成即停止，不自动进入阶段2。RMC/根仓库均不commit/push，生产补丁留工作树供人复核与决定提交。

## 5. 过程

| 日期（Asia/Shanghai） | 记录 |
|---|---|
| 2026-10-11 | 读取指定入口/04/阶段0复核，建C任务，分析current HEAD与所有权 |
| 2026-10-11 | 提交两文件具体提案及事前判据，停在人工源码审批关口 |
| 2026-10-11 | 用户批准后续作；核查无冲突，保存实际根/RMC状态 |
| 2026-10-11 | 原HEAD fresh串行+MPI/OMP配置编译、5用例、9CTest、3诊断完成；保存baseline-freeze后实施 |
| 2026-10-11 | 原样应用提案并生成实际changes.diff；新版两配置编译、所有用例/CTest/诊断完成 |
| 2026-10-11 | 补存被CTest运行器清理的原例输出；保留输入语法失败与首次102/103比较，按预设时间分类最终103/103 |
| 2026-10-11 | 保存lossless原始证据及manifest，更新STATUS/INDEX/KB接口变更指针；完成阶段1，停止 |
| 2026-10-11 | 用户决定以单次提交存档并推送：RMC `330f091e`（c3ef0934→330f091e，分支与 origin 同步）；档案/STATUS/INDEX 提交状态同步 |

归档最终自检（logs/final-implementation-verification.*，退出0）：仅批准的两生产文件变化，846个其它src文件/04正文/主数据库身份保持；branch/HEAD不变，无本Agent提交或推送，git diff --check通过，归档需处理0项（历史提示31项未越范围处理）。新增任务验证工具完整补丁另存new-task-tools.patch；原始证据及其它新增档案文件逐项SHA256见logs/archive-manifest.json。
