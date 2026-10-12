# 基线调用链与正式新增入口

导航：§1 基线源码；§2 生产入口与所有权；§3 测试入口；末节为实际实施对应。原定位绑定330f091e，当前改动后行号另存logs/implementation/source-map-final.txt，保留基线证据。

## 1. 基线源码

~~~text
main.cpp:139–160
  ReadInputBlocks → GenerateInp → RunCalculation
    RunCalculation.cpp:6–13：混合按值/按引用参数
    cSampling.InitialBeforeCalculation（:22）
    fixed-source case → CalcFixedSource
      CalcFixedSource.cpp:67–112
        注册/启动 FixedSource、Tally timer；局部 CDBurnup
        InitializeFixedSourceModel（:114–139）
          FixedSource.InitiateAll（InitiateAll.cpp:125–210）
            Material.InitiateMatAce → 原始核数据加载/材料准备
            Particle.energyCutoff / InitiateTrspt
            Tally.InitiateTally → definition 与 pointer registry
            ReadBinary / 几何定位缓存 / SetupMatNucFrc
            旧 WWG/MCNP、权重截止、伴随截止群定位等普通功能
        ExecuteFixedSourcePrepared（:141–770）
          唯一执行 suite：:147–769，共623行、六种粒子模式
          neutron：:156–259
            sentinel → DistributeSource / InitialBatchSource
            每历史：GetRandSeed → SampleFixSource（当前普通抽样链见下文；本HEAD尚无prepared权重hook）
              TrackHistory → native WW → descendants drain
              SumUpTally → PrcoessBatchEnd
        FinalizeFixedSourceRun（:772–775）
          唯一 ProcessTally（:774）
        普通微扰/WWG/MPI/面源/OutputSummary/Python收尾
        停止 FixedSource timer
  main.cpp:162：整个进程 OutputEnding 一次
~~~

当前 CalMode.h 的 private 段从172行开始；Stage1三个方法在230/238/246行，下一 public 段在330行。它们实际是内部方法。Stage1部分文字把它们称为 public，与现源码不符；本任务按源码定位，不改写阶段1实验记录。

RunCalculation 的 Geometry、Material、ParticleState、Tally、NeutronTransport、Criticality、Burnup、Sampling 等是按值参数；AceData、FixedSource、实际 ORNG、ExternalSource 等为引用。反复调用 RunCalculation 会重新产生部分工作对象；tally registry 又存内部数据指针，不能用第二次调用或复制已初始化 Tally 实现持久运行。

普通 CalcFixedSource 的 CDExternalSource 参数仍按值：执行 core 引用本次包装入口的副本，运行期源库变化不回写调用者定义。Stage2保留这一签名。

## 2. 拟新增生产入口与所有权

~~~text
同一调用栈中的 caller（当前 test driver；未来 CalcMLVR）
  持有 Geometry / Material / AceData / Tally / Particle / 输运对象
       FixedSource / 实际RNG / Sampling / Perturb / Burnup / 源定义
  ↓ 全部借用引用，模型初始化后不得复制或搬动
CDCalMode::InitializePreparedFixedSourceRuns
  检查串行受限模式/未初始化，绑定 owner 地址
  建立 Forward、WW-off 初始状态；sampling.InitialBeforeCalculation一次
  注册已有FixedSource/Tally timer；完整 Stage1 Initialize 一次
  保存固定定义、原物理截止、WW mesh/群/WWP 与 registry 身份
  ↓
caller 提供单个 RunSpec + const source definition
CDCalMode::RunPreparedFixedSource
  校验系列状态；steady-clock t0
  校验参数/静态source白名单（尚未清除任何旧结果）
  构造局部 active source 工作对象
  private PrepareFixedSourceRun
    CLEAR → SET → REBUILD → CHECK
  steady-clock t1 → private ExecuteFixedSourcePrepared：原唯一 suite
    每history仍由SampleFixSource采样
      普通源SampleSourceParticle返回 → prepared专用CheckAndRecordPreparedSourceWeight
      此后才可能kill/输运/WW；零得分也核查，descendant不重复核查
  steady-clock t2 → 核验实际N/D/W0及所有采样次数
  private FinalizeFixedSourceRun：ProcessTally 一次
  后验N/D/W0/银行/角色/RNG；关闭run guards、停止本次 timer；steady-clock t3
  返回带三段时间、实际D/W0及legacy统计标签的成功receipt
  任一采样/执行/统计期异常 → Failed，无成功receipt、禁止继续
  ↓
caller 在下次 Prepare 前读取本次 tally/任务私有快照
  可再次调用同一个 RunPreparedFixedSource，不重新初始化模型
  ↓
CDCalMode::FinishPreparedFixedSourceRuns
  确认完成、停止timer、标Closed；随后正常进程结束
  ↓
caller/正常进程结束：OutputEnding 一次
~~~

仅新增三个受控 public 方法；Stage1三个私有 helper 和 Prepare 继续私有。CalMode保存小型运行状态与非拥有的绑定信息，不创建第二套 Geometry/Material/Ace/Tally。绑定对象、canonical Forward/Adjoint 源定义以及 CDBurnup 必须活到 Finish 返回。Run内的 active source 只活到该 half-run 返回；下一次从 canonical definition重新创建干净工作副本。receipt仅有标量/身份，不持有 tally 指针。

Initialize必须是这批对象的第一次模型初始化；不允许拿已走过普通 CalcFixedSource 的对象补盖“initialized”标志。重复Initialize、交叉绑定另一批对象、在执行中Run或Finish、同进程第二个活动入口均拒绝。由于 OWeightWindow/Output/OTimer 为进程全局，本版只允许一个活动 prepared 序列，也拒绝其间进入另一个普通 fixed-source。Finish后仍不允许在该进程重建prepared模型或转普通路径重初始化；本版一次进程只有这一序列，结束即正常进程收尾。

普通 RunCalculation 的接口、六种粒子分支和普通包装入口保持；未来在其一次调用的同一栈帧中使用新API。本阶段不新增 CalcMLVR 或改变主程序模式分派。

## 3. 测试入口

新增 test-only executable RMCPreparedLifecycle，使用生产类与上述 public API，不使用 friend、placement-new、初始化绕过 token 或自建输运循环。入口位于 tests/prepared_fixed_source_lifecycle/driver.cpp；全局定义独占 tests/prepared_fixed_source_lifecycle/globals.cpp，driver不得再定义。生产实现新增根 src/PrepareFixedSourceRun.cpp 和轻量数据头，同时扩展既有owner；唯一新采样核查hook在SampleNeutronSource.cpp，loop不复制。

根CMake在全部feature定义之后、最终policy POP之前注册新子目录；Linux、test=ON且MPI/OMP/AIS/Python全关闭时，子CMake从RMC target的SOURCES属性副本**仅排除绝对路径src/main.cpp**，加入driver.cpp及globals.cpp各一次；复用生产libraries/编译属性，普通RMC及tests/CMakeLists.txt保持。逐全局的唯一TU、其余extern的既有定义、宏和G0检查见[lifecycle-design §5.1](lifecycle-design.md#51-测试target和全局定义的唯一所有权修订问题1)，不能只凭“按main初始化”代替链接合同。

~~~text
普通RMC：生产源（含main及其全局定义） + 原libraries
测试RMCPreparedLifecycle：相同生产源 − main.cpp + driver.cpp + globals.cpp + 原libraries
  globals.cpp：Output/OMeshInfo/OXSParaTableVec/OWeightWindow/OStatus/OTimer/cellVec/
               OParticleTracker/OController/::ORNG/OCalMode/两个Logger；
               OPythonInterface与OParallel仍按原宏定义（本测试配置关闭）
  其余extern：仍在Data/Photon/Constants/Parallel生产TU及Depth库，不在测试TU复制
  driver：全局OCalMode + 局部runRng（与main局部ORNG语义一致） + 稳定模型owner
~~~

driver调用原前端读输入和建立输出，只在计算分派位置选择：

- persistent：一次 Initialize，逐行 Run，最后 Finish。
- fresh：每个进程仅一次普通 RunCalculation；所有模型初始化/普通包装/ProcessTally照常执行。大整数有效seed从十进制字符串按 uint64 精确读取，调用既有RNG设置方法后进入普通路径。

计划文件是测试私有 TSV，不是生产 MLVR parser。它只选择已有源定义、role/NPS和native lower，不从TARGET造源。fresh逐例使用相同源与WW的普通输入卡；禁止使用新 Prepare 作为唯一 fresh oracle。快照由公开的既有数据/受控 receipt读取；需要观察history/WW事件和raw-load次数时复用任务私有只读GDB，观察器不改变运行状态。

**fresh内存取证**：RunCalculation的Tally/ParticleState/NeutronTransport等工作副本会在返回时销毁。fresh的原始数组/cache/role必须由只读GDB在Execute/Finalize实际引用参数所在栈帧仍存活时抓取，不能在返回后读取main中的未初始化副本。fresh driver的snapshot-dir只管理输出位置和可在返回后读取的引用owner记录；完整数值快照由观察器取实际工作对象。persistent则可在Run返回后、下一Prepare之前直接读取原绑定Tally，history/WW事件仍在执行期观察。两种取证均不得写入被测状态。

## 4. 三项修订的实际调用位置

源链（330f091e）：CheckSourceAndDistri.cpp:6–29做一次定义检查/规范化 → ExternalSource.cpp:50–57按FRACTION/BIASFRAC赋初始因子 → SampleParticle.cpp:25–29重置/分布修正/乘p_dWeight → SampleVariableFromDistri.cpp:13–16允许WEIGHT变量抽样 → SampleValue.cpp:11–73含prob/bias修正 → ExternalSource.cpp:347–349返回最终粒子。拟hook在SampleNeutronSource.cpp:203之后，早于:224–265的alive/几何早退；不是在WW后测权重。InitialBatchSource.cpp:298按完成N赋D，ProcessTally.cpp:364使用D；新audit独立取样累计W0，不改这两处。

计时链（330f091e）：OutputHeading.cpp:29启动进程Total → StatisticsFunc.cpp:124、184/218读取Total → OutputEnding.cpp:46停止。另有CalcFixedSource.cpp:168/247的history interval → ProcessStatisticsBin.cpp:16–20/43的非零history时间 → StatisticsFunc.cpp:177–180/331–358的batch FOM/两个检查。新CalMode三段steady-clock只包围正式调用边界（t0/t1/t2/t3），不改旧统计调用链或全局Total；精确输出映射见test-plan §3.1。


## 实施对应（2026-10-11）

当前生产入口为CalMode.h:42–51；实现为PrepareFixedSourceRun.cpp中的Initialize/Run/Finish，private Prepare组织owner方法。Run → Prepare → 原ExecuteFixedSourcePrepared → 原FinalizeFixedSourceRun → 终检/receipt；普通CalcFixedSource仅增加进程owner冲突检查，原三helper及六模式分支保留。实际行号与补丁由logs/implementation/source-map-final.txt绑定。

测试链接：根CMake末尾受test/Linux/serial/AIS-off/Python-off条件注册。tests/prepared_fixed_source_lifecycle/CMakeLists.txt复制RMC的SOURCES并恰好排除一份原main.cpp，driver.cpp拥有测试main，globals.cpp拥有其余13个无条件单例，原库/TU持有的extern不重复定义。G0的源集合、694个共同生产TU编译选项和nm定义计数在logs/linkage/。普通main.cpp与tests/CMakeLists.txt均未修改。

fresh driver在普通ReadInputBlocks之后设置准确seed/实际N，然后调用原RunCalculation，工作副本存活期间由只读GDB取得快照；persistent调用三个正式public接口。driver只遍历run规格，没有history/batch/descendant循环。结束时由caller仅调用一次OutputEnding。

## P1入口检查补记（2026-10-12）

Initialize：checkProfile → checkNativeParameters（native topology存在）→ 原一次初始化 → 扩展Universe definition。Run：既有preflight → checkProfile → checkNativeParameters（绑定native topology）→ definition匹配 → source/spec/derived WW检查 → 原Prepare/CLEAR → 唯一Execute/Finalize。没有新输运循环或链接目标。[当前源码事实](logs/p1-correction/source-audit.md)。
