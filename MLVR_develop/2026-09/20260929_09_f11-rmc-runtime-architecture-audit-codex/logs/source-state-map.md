# Source state map

证据基线、[S]/[I]/[U] 定义见主报告 §2。下表中“需要 reset”是 **[I] 独立新 run 应满足的条件**；“已有操作”是 **[S] 当前源码事实**。表内路径相对工作区。重点为 MG neutron fixed-source；不宣称覆盖所有编译组合。

| State | Owner | Lifetime | Mutable? | Needs reset between runs? / 已有操作 | Risk | Source evidence |
|---|---|---|---|---|---|---|
| geometry cells/surfaces/universes | CDGeometry | main 对象；RunCalculation 按值副本 | 是 | 冻结模型定义可保留；粒子定位另清 | VarySurf、特殊几何和面源输出状态不等于不可变几何 | `RMC/src/Geometry.h:1227`、`RMC/src/RunCalculation.cpp:8`、`RMC/src/InitiateMatAce.cpp:69` |
| material composition/index/density | CDMaterial | RunCalculation 按值副本 | 是 | 冻结模型保留已派生内容；变化后需重建映射/派生量 | 反复 Convert/Vary 的幂等性未全面证明 | `RMC/src/RunCalculation.cpp:9`、`RMC/src/InitiateMatAce.cpp:19`、`RMC/src/InitiateMatAce.cpp:63` |
| raw ACE / NXS/JXS/XSS | CDAceData::p_vNuclides | main，按引用传递 | 是 | 不变库可保留；ClearData 只 clear Nuclides | 当前每次 Init 仍重新加载；其他全局配置不随 ClearData 清除 | `RMC/src/AceData.h:1650`、`RMC/src/InitiateAndClear.cpp:11`、`RMC/src/InitiateAndClear.cpp:44`、`RMC/src/ReadAceData.cpp:427` |
| MG centre/lower/P0 tables | CDAceData | 同 AceData | 是 | 不变库/group 可保留；库变更则重建 | 最高 upper 没有现成 G+1 公共向量 | `RMC/src/InitiateAndClear.cpp:66`、`RMC/src/CheckMgAceBlock.cpp:38` |
| adjoint XS cache | each CDNuclide in AceData | 随 Nuclide | 是 | 复用已构造版本或从零重建 | resize 后 +=；同尺寸重新初始化累加旧值 | `RMC/src/TreatAdjointMaterial.cpp:22`、`RMC/src/TreatAdjointMaterial.cpp:46` |
| role config | FixedSource::p_bIsAdjoint | main，引用 | 是 | 每轮明确 role | 没有自动双向传播 | `RMC/src/FixedSource.h:270`、`RMC/src/ReadFixedSourceBlock.cpp:228` |
| AceData role | AceData::p_bIsAdjoint | main，引用 | 是 | 与当前 run role 一致 | InitiateAll 仅 true 分支赋值 | `RMC/src/InitiateAll.cpp:130` |
| particle role | CDParticleState | RunCalculation 副本，反复抽样/transport | 是 | fresh history/run 与 role 一致 | Sample/Pop 仅置 true；构造 false 不等于运行间清零 | `RMC/src/ParticleState.h:529`、`RMC/src/SampleNeutronSource.cpp:222`、`RMC/src/SampleNeutronSource.cpp:304` |
| adjoint max energy | FixedSource | main，引用 | 是 | 保持物理输入和内部群号可区分 | 原地覆盖后重新初始化会把群号当能量 | `RMC/src/InitiateAll.cpp:192` |
| particle geometry / XS caches | ParticleState，含 p_vONucCs、dirty flags | history/run 间同对象 | 是 | 更新 role、material、energy 时正确失效 | resize 同尺寸不恢复 true；完整条件未动态测 | `RMC/src/CalcFixedSource.cpp:81`、`RMC/src/SampleFreeFlyDist.cpp:85`、`RMC/src/InitiateAll.cpp:162` |
| source definitions/distributions/transforms | ExternalSource | main；CalcFixedSource 按值副本 | 是 | Forward 可保留定义；变更 source 要替换和重新检查 | AddSource/子分布检查有 append，不是 reset | `RMC/src/CalcFixedSource.cpp:71`、`RMC/src/ExternalSource.cpp:15`、`RMC/src/CheckSourceAndDistri.cpp:59` |
| source fractions/bias | ExternalSource | 同 source | 是 | 新定义需归一化且与抽样权重一致 | in-place 归一化；不能把改一个 fraction 视为整源更新 | `RMC/src/ExternalSource.cpp:25`、`RMC/src/ExternalSource.cpp:56` |
| requested population / intervals | FixedSource | main，引用 | 是 | 每轮设置并重算派生 interval | 旧 remaining/restart/统计规模可污染新轮 | `RMC/src/CheckTransport.cpp:51`、`RMC/src/InitialBatchSource.cpp:94` |
| completed histories / batch / finish | FixedSource | main，引用 | 是 | 独立 run 清；构造有初值，InitiateTrspt 不全清 | finish=5 直接阻止下一次 loop | `RMC/src/FixedSource.h:192`、`RMC/src/InitialBatchSource.cpp:335`、`RMC/src/CalcFixedSource.cpp:108` |
| neutron descendants/sentinel；各类 particle bank | FixedSource stacks/vectors | FixedSource 生命周期 | 是 | run 边界无旧 history 后代，sentinel 状态明确 | 每次进入又 push sentinel；另有耦合 bank | `RMC/src/FixedSource.h:213`、`RMC/src/CalcFixedSource.cpp:107`、`RMC/src/CalcFixedSource.cpp:167` |
| collision / missed counts | FixedSource + transport | 混合 main/ref 与副本 | 是 | 当前 InitiateTrspt 清部分计数 | 不能扩展为所有 photon/electron/诊断也已清 | `RMC/src/InitiateTrspt.cpp:79` |
| denominator / starting-weight state | FixedSource::p_dTotStartWgt / Origin | main，引用 | 是 | 每轮重新建立并导出实际口径 | 普通源赋 history 数，surface/fission 另修正；不是任意源权重实测和 | `RMC/src/InitialBatchSource.cpp:295`、`RMC/src/InitialBatchSource.cpp:321` |
| RNG generator/seed/stride/position | main 局部 ORNG；另有同名全局 | main/进程 | 是 | 每轮明确 type、seed、stride、position/preposition | 只改 seed0 不保证刷新 stride cache | `RMC/src/main.cpp:37`、`RMC/src/main.cpp:60`、`RMC/src/RNG/RNG.h:506` |
| RNG skip parameters / cached seed | GetRandSeed 函数 static | 进程 | 是 | 满足缓存重算条件 | 多对象共享、重配/并发风险 | `RMC/src/RNG/StrideRNG.cpp:85`、`RMC/src/RNG/StrideRNG.cpp:139`、`RMC/src/RNG/StrideRNG.cpp:190` |
| tally mesh/bins/index offsets | CDTally::p_vMeshTally | RunCalculation 副本 | 是 | 固定定义可保留；offset 与数组布局一致 | Energy=-1 被替换为实际 bins；返回 main 不保留该副本 | `RMC/src/SingleTally.cpp:875`、`RMC/src/RunCalculation.cpp:10` |
| score/sum1/sum2/mean/RE | CDTallyData | 随 Tally owner | 是 | 每 run 清统计；SetZero 保留形状 | 不含 touched indices / statistics tester reset | `RMC/src/TallyData.cpp:17`、`RMC/src/TallyData.cpp:83` |
| touched-index set / stride lists | CDTallyData | current history，容器随 owner | 是 | 正常 SumTallyBin 清 set；中断/新 run 保证无旧索引 | SetZero 不清这些容器 | `RMC/src/TallyData.cpp:43`、`RMC/src/TallyData.cpp:55` |
| tally storage pointer registry | CDTally::p_pTallyDataPointer | 随 Tally owner | 是 | 登记一次，重建时唯一/无悬空别名 | InitiateTally 追加；按值复制 raw-pointer registry 有别名风险 | `RMC/src/InitiateTally.cpp:69`、`RMC/src/ProcessTally.cpp:353` |
| statistics check indices / moments / batch progress | CDTallyData::p_OStatisticsTester | 随 TallyData | 是 | 新 run 清并按 population 重配；ReSize 已清多项数组 | SetStatisticsIndex 追加 index；不能只 SetZero tally | `RMC/src/SetStatisticsIndex.cpp:36`、`RMC/src/StatisticsFunc.cpp:8`、`RMC/src/StatisticsFunc.cpp:52` |
| native WW spatial mesh / energy bins | global OWeightWindow | 进程 | 是 | 固定定义可保留 | energy 末端 INFINITY 哨兵不是真实最高群边界 | `RMC/src/ReadWeightWindow.cpp:419`、`RMC/src/ReadWeightWindow.cpp:431` |
| WW lower/upper/survival arrays | OWeightWindow::p_vMeshInformation | 进程 | 是 | 按本轮 WW 同步三项参数 | 没有 F/A 双槽；需要 ranks 一致 | `RMC/src/WeightWindows.cpp:79` |
| shared WW window/address/displacements | OWeightWindow，USE_MPI/MCNP 条件 | 建立至 fixed-source 末端 free | 是 | 下一轮明确重建/同步/释放规则 | free 后地址不能用于 lookup；默认 native 不启用 | `RMC/src/ReadMCNPWeightWindowCard.cpp:307`、`RMC/src/WeightWindows.cpp:268`、`RMC/src/CalcFixedSource.cpp:737` |
| WWG / fixed-source pointer | global OWeightWindow | 进程，条件分支初始化 | 是 | 保持指针 owner 有效；生成累积与数值表区别处理 | 重建 FixedSource 后可能指向旧 owner；WWG 不等于 native 表替换 | `RMC/src/WeightWindows.cpp:168`、`RMC/src/InitiateAll.cpp:177`、`RMC/src/CalcFixedSource.cpp:728` |
| rank/size/thread config / MPI types | global OParallel | MPI job | 是 | 固定 job 配置可保留 | 不是每轮重新 MPI_Init；decomposition 需单独生命周期核验 | `RMC/src/InitiateParallel.cpp:20`、`RMC/src/InitiateParallel.cpp:74`、`RMC/src/CheckIOFile.cpp:124` |
| load-balance MPI request/flag/counters | FixedSource | run 操作，成员跨 run | 是 | 已有 FinalizeLoadBalanceChecker 等待并清 request/flag；计数另重置 | 未完成 collective 与失败路径未全面验证 | `RMC/src/CalcFixedSource.cpp:12`、`RMC/src/CalcFixedSource.cpp:57` |
| domain communicator | OParallel | 解析 domain 配置后 | 是 | 固定 domain 可保留；重建需明确释放 | 本次未证明全部 communicator cleanup | `RMC/src/DomainDecomposition.cpp:15`、`RMC/src/DomainDecomposition.cpp:29` |
| timers / stop-time / FOM clock | global OTimer + Output | 进程 | 是 | 区分 session / run；现 reg/start 不清累计，reset 不清 recordTime | 时间与 FOM 跨 run 混用 | `RMC/src/Utility/Timer.h:47`、`RMC/src/Utility/Timer.h:96`、`RMC/src/Utility/Timer.h:123`、`RMC/src/StatisticsFunc.cpp:124` |
| output names/FILE*/warnings/restart | global Output | 进程，OpenFilePtrs→CloseFilePtrs | 是 | 每轮路径/归属/完成状态明确；按失败范围管理 | fclose 后未置空；错误路径可 exit；restart 可能继承 | `RMC/src/CheckInpBlock.cpp:99`、`RMC/src/CloseFilePtrs.cpp:28`、`RMC/src/PrintFile.cpp:52` |
| loggers | global OLogger/OProcLogger | 进程 | 是 | 日志 scope/文件策略需明确 | fatal 直接 exit，非可恢复 run error | `RMC/src/Utility/IO/Logger.h:164`、`RMC/src/Utility/IO/Logger.h:221` |
| logger initialized flag | init_global_logger 内 static | 进程 | 是 | session 初始化只执行一次；重新初始化不是现成能力 | 第二次调用抛 logic_error | `RMC/src/Utility/IO/Logger.cpp:63` |
| Universe 0 defined flag | ReadUniverseBlock 内 static | 进程 | 是 | 固定模型保留时不需重解析；重读新 input 需另处理 | 即使新建 CDInput/Geometry，flag 仍为 true | `RMC/src/ReadUniverseBlock.cpp:12`、`RMC/src/ReadUniverseBlock.cpp:27` |
| used-material vector | CheckUsedMat 内 static vector | 首次调用至进程结束 | 是 | 不同模型复查需重新确定尺寸和初值 | 首次尺寸保留、旧 flags 保留；固定模型无重查时不触发 | `RMC/src/CheckUsedMat.cpp:7`、`RMC/src/CheckUsedMat.cpp:12` |
| PTRAC filter objects | ReadParticleTrackBlock 内多个 static | 进程 | 是 | 新 filter 配置不能假定重新构造 | 构造参数取首次到达该分支的输入；指针被加入 tracker | `RMC/src/ReadParticleTrackBlock.cpp:54`、`RMC/src/ReadParticleTrackBlock.cpp:61` |
| photon atomic data globals | Data::PhotonAtomicDataBase | 进程 | 是 | from_hdf5 已在旧 elements 非空时 free；耦合模式仍需专审 | neutron MG 复用结论不自动覆盖该库 | `RMC/src/Photon.cpp:547`、`RMC/src/Photon.cpp:554` |
| burnup once flag / geometry expansion static scratch | CheckDepletionNuc / ExpdGlobalCell | 进程 | 是 | repeated burnup/model 初始化需另审 | 既有 burnup loop 不证明 fresh-run 幂等 | `RMC/src/CheckDepletionNuc.cpp:8`、`RMC/src/ExpdGlobalCell.cpp:9` |
| generated input material-file counter | GenerateInputFile 内 static nIndex | 进程 | 是 | 输出身份/目录规则需明确；非 transport 状态 | 重复生成 input 时编号累加 | `RMC/src/GenerateInputFile.cpp:314` |
| nuclear-data paths / HDF5 config | Data::DataBase namespace globals | 进程 | 是 | 同库可保留；换库须与数据对象一致 | ClearData 不清这些配置；不是数据 owner | `RMC/src/Data/Data.cpp:14`、`RMC/src/Data/Data.cpp:22` |
| CalMode / Status / Controller / cellVec / MeshInfo / XSParaTableVec | main 定义的 globals | 进程 | 是 | 固定配置可保留；动态模式/diagnostics 须审查 | 无统一 reset，部分特殊功能未覆盖 | `RMC/src/main.cpp:27`、`RMC/src/CheckInpBlock.cpp:65` |
| PTRAC | global OParticleTracker | 进程，history 中更新 | 是 | 若启用，清本轮筛选/计数/输出缓冲状态 | 未完成完整跨 run reset 审查 | `RMC/src/main.cpp:35`、`RMC/src/ScoreMeshTally.cpp:52` |
| Python source interpreter | global OPythonInterface，USE_PYTHON_API | run init→条件 finalize | 是 | 重复 interpreter/source-module 生命周期未验证 | 不能把 C++ source 的复用结论直接外推 | `RMC/src/main.cpp:50`、`RMC/src/InitiateAll.cpp:205`、`RMC/src/CalcFixedSource.cpp:743` |
| file-static mesh constants | MeshFun / ScoreMeshTally | 进程 | 否 | 不需要 reset | 常量不是缓存，不据 static 关键字误报 | `RMC/src/MeshFun.cpp:7`、`RMC/src/ScoreMeshTally.cpp:7` |

总结 [I]：stable model data、run mutable data 和 process resources 目前交织在对象和函数中。上述 reset 条件并非已实现的方法清单，尤其不等于“调用 SetZero + 改 role”即可得到独立新计算。
