# Preliminary source-only conclusion — Codex

2026-09-29；RMC `Neural_Network_WW_Iteration` / `5cfb0f771d0c5a2127c90d57e51ce672a4e3b616`；RMC 工作树干净。

独立性：先完成下列当前源码阅读再落此文件。开场按工作区规则读过 STATUS / AGENT_CONTEXT；它们和本会话之前 F10 上下文均不作为下列判断的证据。本轮没有读取 Claude 任务目录或 F02–F10 历史档案。以下全是源码事实 [S] 或明确标注推断 [I]，无动态运行证据。

1. [S] `main.cpp:57-169` 建立局部 model/material/Ace/tally/fixed-source/source/RNG 等对象，读一次 input，调用一次 `RunCalculation`，输出结束信息，然后 MPI_Finalize/return。`main.cpp:27-55` 同时存在 process-global Output/WW/timer/cal-mode/RNG/parallel 等对象。
2. [S] `RunCalculation.cpp:6-13` 将 geometry/material/tally/particle 等按值传入，Ace/fixed-source/RNG/external source 按引用；fixed-source 分支 `83-89` 只有一次调用。当前源码全局搜索 `CalcFixedSource(` 只命中定义与此调用点。
3. [S] `CalcFixedSource.cpp:73-80` 每次进函数先启动 FixedSource timer，再 `InitiateAll`；后者 `InitiateAll.cpp:130-156` 再执行 `InitiateMatAce` 和 tally 初始化。`InitiateMatAce.cpp:18-28` 包含核数据初始化与文件读取，当前入口不把加载与每轮 transport 分离。
4. [S] `FixedSource.h:192-214` 在构造时设 finish=-1 和计数为0；`InitialBatchSource.cpp:335-337` 结束后设 finish=5；`CalcFixedSource.cpp:108` 在 while 外检查 finish。`InitiateTrspt.cpp:60-100` 没有重置 finish、累计 histories/batch 或 particle stacks。[I] 直接原对象再次调用不能视为新一轮执行，会跳过主历史循环；重用需要完整的 per-run reset 边界。
5. [S] Adjoint 不是单一实时开关：`InitiateAll.cpp:130` 只把 Ace flag 设 true，`SampleNeutronSource.cpp:222,304-306` 只把 particle flag 设 true；没有对应 false 分支。`InitiateAll.cpp:196,202` 原地将 MeV 上限成员改成内部群号。[I] A→F 和再次初始化 A 都存在明确状态恢复问题。
6. [S] `TreatAdjointMaterial.cpp:22-57` 存在 adjoint 派生截面数组，用 resize 然后 += 填充；`InitiateAndClear.cpp:44-61` 对已有 nuclides 只 resize，未整体清除。[I] 复用数据库时不能未经清零再次建立该 cache；原始 XSS 与 adjoint 派生数据需要区分。
7. [S] `TallyData.cpp:17-24` 有保形状的 SetZero；`43-52` 以 history 累加并清 score；`83-100` 生成内存 Ave/RE。`InitiateTally.cpp:60-69` 在定义外持有 mesh tally data，但反复初始化会向 `p_pTallyDataPointer` push。[I] 有复用定义/清统计的基础，不等于已有完整 run reset。
8. [S] native WW lower/upper/survival 在 `WeightWindows.cpp:79-102` 按固定 mesh×energy 逐项赋值，查找直接读取这些数组 `45-69`；`72-78` native MG lookup 使用物理能量。[I] 同 shape 的数值更新有现成内部构件，必须同步三种权重并检查 MPI shared 存储路径，尚无已验证会话接口。
9. [S] MG centre/width 位于 nuclide XSS，`CheckMgAceBlock.cpp:41-49` 导出升序 centre/lower；`GetMgCs.cpp:272` 从 centre/lower 得到最高上界。[I] 完整 physical G+1 边界可由内存数据导出，不必解析打印文本，但需边界一致性校验。
10. [S] MPI_Init/Finalize 在 main；`CalcFixedSource.cpp:735-739` 每次结束有 barrier 和可选 WW MPI_Win_free。`Utility/Timer.h:123-125` reg 使用 emplace，重复注册不清已有 timer；stop 累加 runTime。[I] MPI 本身允许 main 内多次 transport，但当前资源、timer、请求和 run-state 的生命周期必须审查，不能由单次运行可用推导重复运行安全。
11. [S] AIMC 当前实际分支为 `feature/3d-two-group` / `9d749291d5f5070a00b9f88603428e686938cb7f`，与任务注明的 develop 不同；只读当前树，不切换。外部工作流调用机制留待下一步源码确认。

初步判断：[I] 存在可保留的模型/数据与局部清零、WW 数值赋值构件；现有 fixed-source 入口不是可直接重复调用的安全 session。不能据此选择最终 F11 架构。后续报告补全 source/MPI/output/global ownership、既有多阶段模式和最小实验建议；不运行实验。
