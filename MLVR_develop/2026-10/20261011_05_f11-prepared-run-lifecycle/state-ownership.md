# KEEP / CLEAR / SET / REBUILD 状态所有权

导航：§1 所有权矩阵；§2 风险与边界。定位绑定330f091e；完整抽查原文见 logs/source-evidence.txt。本表是拟实施清单，尚无正式reset实现或动态通过结论。

## 1. 按 owner 划分

| Owner / 当前源码 | KEEP | CLEAR | SET / REBUILD / 检查 |
|---|---|---|---|
| CDCalMode；CalMode.h:113–125、230–249 | 模型粒子模式；普通入口/私有core；固定physics与WW定义快照 | 每次receipt临时状态/steady-clock局部区间；不清整个CalMode | 新增私有生命周期枚举、owner绑定和累计history offset；设置本次neutron WW var-red与p_nChangeNeuCutWgt；拒绝非法状态重入 |
| CDGeometry / CDMaterial；InitiateAll.cpp:131、165–178、234–264 | 几何/材料定义、密度、基础核素索引；对象地址；固定能群；已有model内部结构 | 不清模型；binary/ptrac输出启用的输入在受限入口拒绝 | Material.SetupMatNucFrc仅重建particle拥有的p_vMatNucFrc/p_vMatNucID；不再次InitiateMatAce |
| CDAceData / Nuclide；InitiateMatAce.cpp:8–29、63–66；TreatAdjointMaterial.cpp:9–102 | NXS/JXS、XSS/PXSS、MG群边界与原始XS、核素定义和地址 | 每次清p_vAdjointCrossSection及p_vAdjointFissionCrossSection；F也清，不只把flag关掉 | p_bIsAdjoint=role；A在零化后的派生数组上调用原treatAdjointMaterial；F保留raw数据且派生为空；逐使用材料/核素/群检查νΣf，非零拒绝 |
| CDFixedSource；FixedSource.h:192–213、243–418 | 输入物理选项、maxMiss、load balance配置（受限NONE）；模型无关definition | 完成历史、batch、currentPARTICLE、源计数、独立起始权重audit（实际次数/W0/min/max/违规数，guard关闭）、collision N/P/E、miss、induced gamma、四类裂变multiplicity统计、分母、restart累计/时间interval临时量 | NPS>0且≤2^53并满足原bank容量限制；restart=0；finish=-1；interval按本次N和既有串行分配逻辑；角色flag；Adjoint最大能量从保存的物理MeV重新LocateMgErgGrp，绝不再转换旧内部群号；SetPreparedRun启用权重guard，SampleFixSource采样返回后逐history审计（含零得分），Finalize前后核对N/D/W0，成功才关闭guard/出receipt |
| FixedSource banks；FixedSource.h:283–309；CalcFixedSource.cpp:156、213–230 | bank容器类型和四个粒子槽，不持有活粒子 | ParticleStack逐槽清空；p_sNextParticle归零；fixed/photon/electron临时bank和计数清除；旧p_vFixedSrc内容清并按既有capacity逻辑配置 | CLEAR前检查上一轮已完成且无真实后代；core自己push一次neutron sentinel。结束neutron stack的一个哨兵不是残留粒子；其它槽/真实计数应为空。p_vFixedSrc预分配长度不是live bank计数 |
| CDNeutronTransport；NeutronTransport.h:37–41；InitiateTrspt.cpp:60–101 | 原physical energy cutoff、默认weight policy和物理选项 | p_nMissParticleCount与p_nMissNeutronCount等当前计数 | WW-on恢复普通native路径的weight cutoff=1e-8；WW-off恢复本次模型初始默认policy，禁止沿用上轮WW修改的值。首批用例默认0.25，显式特殊weight policy未门禁前拒绝 |
| CDTally；InitiateTally.cpp:57–145；Tally.h:893–943 | mesh/energy/Normalize/offset/bin定义、tally对象与pointer registry大小/指针顺序 | 对registry内每个TallyData清数值及临时集合；不反复InitiateTally、不resize definition容器、不push registry | p_bIsPerHstry=true、p_bIsPerCyc=false；已有tally flags保持；每次 N 用于统计诊断重置。首批只cell/Cartesian track mesh；CAP/FET/perturb/cs等专门状态未覆盖的输入拒绝 |
| CDTallyData；TallyData.h:33–83；TallyData.cpp:17–24；SumUpTally.cpp:66–72 | 已分配数值shape；登记关系；统计检查选定bin | Score、ScoreTemp、Sum1、Sum2、Sum3、Ave、RE全部零化；p_setScoreIndex、p_vScoreIndex2、p_vScoreStride清空 | stride/index2是当前history的活动工作列表，不是definition offset。新ResetForRun直接完整清理，旧SetZero行为不改；Sum3不强行改变原shape |
| CDStatisticsTester；StatisticsTester.h:39–174；StatisticsFunc.cpp:8–93 | p_vIndexOfTallyData、选定bin、batch/check/pdf定义与阈值 | Sum1–4、Time、largest/fluctuation、pdf/slope、检查flags、stored/count/current batch/temp、p_vGatherScores、Ave/RE/VoV/FOM/mean/shift等所有run数组 | 复用ReSize(N)并显式补齐scalar默认，如p_nCyc=1；NpsPerBatch依据当前N。首批SCHECK case的N为原诊断batch数的整数倍；不重写统计公式；旧FoMTot/FlucFOM依赖Total，batch FOM依赖非零history计时，随receipt标legacy_mixed_not_per_run；只有test-plan §3.1精确名单允许时间差异 |
| CDParticleState；ParticleState.h:395–416、423–714、854–996、1142–1183、1366–1373 | 不保存上轮物理缓存；model引用仍由caller持有 | 当前pos/dir/energy/time/weight和存活/终止状态；cell/surface/level定位栈、passed sets、几何暂存；nuc XS cache；temp抽样、secondaryEnergy/Particles、MGAdjFisMatrix及perturb临时量（对应选项拒绝） | owner方法按上述字段组显式恢复fresh默认；cell/mat/temp/density与逐核素temp-change flags=true；ONucCs匹配现有核素数；mat-nuc向量及nearest/Poisson/realDisplace按原Initialize形状重建；role和各粒子energyCutoff/importance/weight policy明确设置 |
| CDExternalSource；ExternalSource.h:151起；ExternalSource.cpp:25–44；CheckSourceAndDistri.cpp:6–8 | caller已规范化一次的canonical单个定点/定能/定向中子源，保存hash/identity；本阶段禁用所有用户distribution（仅保留0号占位） | active source的fixed-init neutron/photon banks及counts、临时surfsource状态（输入拒绝此模式） | 每run复制已验证canonical definition到局部工作source，再清临时库；不修改canonical；不再次归一化已经解析的active概率以免改变位序。新构造definition仅创建时复用旧CheckSourceAndDistri一次；CheckPreparedSourceDefinition静态白名单见lifecycle-design §3.1，不能以SOURCE WEIGHT=1替代实际采样检查 |
| 实际CDRNG；RNG.h:52–55、302–315、415–431；StrideRNG.cpp:76–101 | Type2乘数/模数/Rand算法；整个序列root seed与固定stride | 移到owner的skip cache失效；history用数计数归零；不得读同名未传入global ORNG | seed0=seed=effectiveSeed；position=0、position_pre=-1000；本次history段/总范围检查；owner cache有效性由RNG管理 |
| global CDWeightWindow；WeightWindow.h:160–242；WeightWindows.cpp:79–101；ReadWeightWindow.cpp:421–427 | Cartesian topology、neutron能量边界（含唯一Inf终边界）、WWP、mesh编号顺序 | 上轮native neutron lower/upper/survival及运行身份失效；不开/关WWG/MCNP共享资源 | 校验角色与fixed shape、positive finite lower及三界有限；复用原ProcessWeightWindow安装本次三界；WW-off关闭真实var-red查询链，可保留固定topology但不保留生效旧bounds |
| Output / OTimer；Output.h:278–298；OutputEnding.cpp:8–42；Utility/Timer.h:47–99 | 进程输出/HDF5句柄、Total/ReadInputBlock timer、OutputEnding只一次 | 仅run所用FixedSource/Tally timer：runTime、recordTime、startTime；拒绝清理running timer | 新ResetForPreparedRun；普通Timer.reset不改。core开始前开启FixedSource，Finalize后停止；输出句柄身份/FD有效性检查，任务私有snapshot每run关闭自身文件。CalMode另用steady_clock记录Prepare/Execute/Finalize三段及其和；Total绝不reset作本轮值，旧统计FOM仅作legacy数据 |

进程对象链接所有权保持两套executable各一份定义：普通main.cpp不变；测试globals.cpp独占13个无条件对象及原宏控制的2个对象，其余extern仍属原生产TU/库。实际输运RNG是driver局部runRng，不是全局::ORNG；完整定义/宏/CMake/G0合同见[lifecycle-design §5.1](lifecycle-design.md#51-测试target和全局定义的唯一所有权修订问题1)。这不改变KEEP/CLEAR/SET/REBUILD所有权。

CDFixedSource若干旧未使用字段在constructor未初始化，例如p_nFixedSrcBankCount/p_nPhotonBankCount/p_nMissParCount。新owner reset应明确写它们；fresh对照不读取未初始化的无效字节来宣称“完全状态相等”，只比较合法且实际使用的状态。

## 2. 物理风险与验伪

- 伴随派生量是散射/产生算子重建结果。resize相同shape不会清零；原函数46/50/56/74/79/85/98行使用+=。若不先清，A→A可能重复累计。每次A的整个派生数组必须逐项等于独立A oracle，不能只看最终Forward tally。
- SampleNeutronSource.cpp:222对A只置true，F没有相应置false，因此必须由正式粒子reset恢复F标志。fresh初始化至首次采样前Particle flag仍为默认false；prepared预先安装本次role，比较真实输运标志从采样后开始。
- F恢复必须同时恢复FixedSource/Ace/Particle角色、物理最大能量及cache/WW policy。仅关Ace标志不足以证明F输运恢复。
- 原最小neutron energy cutoff由ReadPhysicsBlock.cpp设置，当前MG路径未发现与Adjoint max相同的转换。Stage2保持普通fresh路径语义，首批采用既有微小默认值；不借生命周期任务修正其物理算法。
- raw核数据始终只读。H2O无非零裂变贡献，AA只能门禁其散射派生和零裂变数组；不证明一般可裂变材料。受限入口检查原始使用材料的产生项并拒绝非零νΣf，不可通过关闭产生过程伪装为H2O。
- 新源限制只证明受限单位权重合同；D按历史数赋值不等于测得W0。采样后hook只读粒子，在任何alive/kill早退之前检查一次，WW和后代权重不加入W0。实际分母赋值和tally公式不改；失败run无成功receipt。
- 三段steady-clock归CalMode本run；旧StatisticsTester仍含进程Total和非零history两类时间，不能把清数组当成时间口径转换。时长/例外门禁见test-plan §3.1。
- W11/W12及tally体积计分保持；全mesh比较的是原始RMC数据和同一既有转换后的任务私有视图，不建立Field API。尚无新物理验证结论，物理导读本轮不改。

静态证据强度E1；KEEP地址/定义不变、CLEAR覆盖、派生值和WW真实使用都仍需test-plan的动态门禁，不能由此表直接标Ready。
