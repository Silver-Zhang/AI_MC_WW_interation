# Proposed Experimental Patch

状态：**提案，未应用、未编译、未运行；需要用户批准。**

可复核文件：[source-side diff](verification/proposal/proposed-experimental.patch)、[hook 声明草案](verification/proposal/f11_probe_hooks.hpp.draft)、[基线哈希](verification/proposal/patch-base-manifest.json)。hook 草案仅有声明，尚无 callback 实现或 test driver，因此本包不是可执行 harness。`git apply --check` 只核对 diff 上下文，不构成编译/数值验证。

## Why required

1. **E0 无现成的非重叠时间边界。** FixedSource timer 在 InitiateAll 前启动，最终 tally/output 后停止；Tally timer用于路径计分。外部 wall time 减 FixedSource 无法分离 XS/init/transport。证据：`RMC/src/CalcFixedSource.cpp:73`、`RMC/src/CalcFixedSource.cpp:78`、`RMC/src/CalcFixedSource.cpp:721`、`RMC/src/CalcFixedSource.cpp:749`、`RMC/src/TallyByTL.cpp:30`。外部 profiler 可提供不同粒度信息，但不能由这些现有输出得到本任务所需分解；本提案选择显式局部 probes。
2. **E1/E2/E3/E4 要复用真实生产 loop，同时只初始化一次。** 每次 CalcFixedSource 无条件进入 InitiateAll→InitiateMatAce/ReadAceData→InitiateTally。若绕过该函数、复制原循环到 harness，验证的是复制版本；若原样重复函数，会重新读库且重复初始化，不满足被测目标。需要一个可审查的实验入口开关。证据：`RMC/src/CalcFixedSource.cpp:78`、`RMC/src/InitiateAll.cpp:130`、`RMC/src/InitiateAll.cpp:156`、`RMC/src/InitiateMatAce.cpp:27`。
3. **E3 必须看真实查窗。** selected bin 是 setMeshWeightWindowBound 的局部 ergPos；transport 后只比较数组不能证明下一轮使用了 WW2。证据：`RMC/src/WeightWindows.cpp:45`、`RMC/src/DoMeshWeightWindow.cpp:42`。
4. **E4 应在 owner 有效且归一化完成处 snapshot。** 内存数据已有，不需要 Field API；ProcessTally 后、OutputSummary 前是明确位置。证据：`RMC/src/CalcFixedSource.cpp:721`、`RMC/src/OutputTally.cpp:247`。单独读取这些 public members 的 harness 并不需要新 accessor；本次阻塞在如何驱动真实循环而保留一次初始化。

这是对当前选定实验方法的边界说明，不声称所有调试器/链接技术都无法观察程序。用链接拦截跳过初始化也会改变被测执行流程，不能借“不编辑原文件”规避本任务审批规则。

## Patch layers

### P0 — observation only

编译宏 `RMC_F11_PROBE`，提供阶段时间、run-state snapshot、每 history RNG identity 和真实 WW selection trace。observer 参数使用 const；不调用 RNG，不改粒子/源/XS/tally/WW 数值；缓冲记录后输出。

E0 timing mode 只启用少量 phase marks；heavy snapshots、history 与 WW observer 为禁用状态。E1–E4 diagnostic mode 才读取数组/生成 hash。预算和 overhead gate 已在 frozen plan 中固定。

### P1 — explicitly gated control seam

另一个宏 `RMC_F11_REUSE_EXPERIMENT` 只在 P0 同时开启时合法。在 `CalcFixedSource` 的原 Init 调用外加一个 experimental prepared-state token 判断。未 armed 时仍完整调用原 Init；任务 driver 按已审合同完成 reset/role/WW/source 准备、验证 preconditions 后，才允许下一次调用跳过 full Init。

**P1 改变实验 binary 的初始化执行路径，不能称作纯观测。** 它不修复 finish/role/cutoff/cache/tally 等生产逻辑；相应 CLEAR/REBUILD 操作只在新的任务内 test driver 中显式实现并记录。history loop、collision/scattering/fission、WW splitting/roulette、Sum1/Sum2 和 RE 公式维持原调用路径。

未写 Session 类、Controller、公开 API 或生产 reset 方法。driver 只服务固定 E1–E4 序列，不作为最终 F11 实现。

## Files/functions affected

下表逻辑路径相对 RMC 基线；**批准后拟只在本任务目录的私有源码快照中应用**，例如 `verification/proposal/RMC-snapshot/src/...`。复制生产函数后修改同样需要本次批准。当前未创建/修改此快照，更未修改共享 RMC 工作树。

| 文件 / 原行号 | hook / 修改 | 用途 |
|---|---|---|
| `src/main.cpp:57,162,169` | main enter/exit、ending output scope、flush | E0 process/total 对账；原 CLI fresh run |
| `src/ReadInputBlocks.cpp:16` | input scope | E0 input+geometry checking 合并项；一次解析计数 |
| `src/ReadAceData.cpp:15` | XS scope/call count | E0 XS+MG 派生；same-process 读库次数=1 |
| `src/InitiateMatAce.cpp:8,81` | inclusive model scope、material output 子项 | E0 model residual，避免 XS 重复计时 |
| `src/TreatAdjointMaterial.cpp:9` | adjoint scope/call count | E0 A 派生时间；E2 rebuild 次数 |
| `src/CalcFixedSource.cpp:73,78,106,119,719,721,749` | phase marks、snapshot、neutron history seed observer；P1 Init gate | E0–E4 的真实循环驱动/诊断；不复制 loop |
| `src/DoMeshWeightWindow.cpp:42` | 实际查窗前记录 particle context | E3 transport 粒子状态与 lookup 对应 |
| `src/WeightWindows.cpp:69` | 查表后、返回前记录实际 ergPos/三个 bounds | E3 证明读到新值，而非仅更新容器 |

共 8 个源码文件；新增函数定义和 test-driver/build/comparison scripts 只放本任务目录，尚未实施。头文件由任务 build 的 forced include 注入；不改生产 CMakeLists、类成员布局或公开签名。所有宏关闭时，删除实验条件块后应与原源码逐行一致（忽略空白），见自检。

## Test driver contract after approval

- 新建 standalone 测试 main，链接当前源文件实现，避免链接两个 main。按原解析路径建立一次 geometry/material/source/tally/WW；direct reference 调用原 CalcFixedSource，保留模型对象身份。不能反复调用按值 RunCalculation 来掩盖状态。
- E1–E4 fresh oracle 与 sequence 使用同一个 test-driver binary：fresh mode 每个进程只跑一轮且完整 Init；sequence mode 第二轮起才允许 P1。另将 driver 的 fresh 结果与相同源文件构建的原 CLI 对照，验证单次入口等价；原 CLI 的 uninstrumented/probe-only 构建用于 observer 无扰动与 E0 开销检查。所有 run 独立目录/文件名，stdout/stderr/exit code 和完整输入固定。
- 字段级 reset、role/cache preparation 和结果提取均在 driver；具体合同见 [frozen plan](logs/experiment-plan-frozen.md) §6–§8。未实施这些合同，不能把 P1 gate 单独当作可运行能力。
- E2 清零/重建合同在第一次运行前固定；运行发现新 mismatch 后只记录和分类，不边跑边修。
- E4 同一个 tally owner、mesh/group/registry，清统计；不重建 whole tally 对象来冒充 reset 保留定义。
- snapshots 包含 immutable base hash 与派生状态分区；跨进程比较内容，进程内才比较地址；metadata、timing/FOM 不伪装成 bitwise 可比物理结果。

## Expected evidence

| 实验 | 预期采集，不是已有结果 |
|---|---|
| E0 | F/A 各 1 warmup +7 measured 的原始阶段事件、mean/std、启动占比与计时闭合/observer-overhead 检查 |
| E1 | fresh F1/F2 和同进程两轮的 history/RNG/bank/denominator/Score/Sum1/Sum2/Ave/RE exact diff；model load count=1 |
| E2 | fresh F/A/F 对照；role/cutoff/adjoint/fission XS/particle cache 的每步快照；first divergence 或预声明 contract 下的一致性 |
| E3 | WW1→WW2 数组、派生参数，以及真实 particle→mesh/bin→bounds 的事件；对 fresh WW2 exact comparison |
| E4 | reset前/后的全零及 registry/index 检查，独立第二轮 field，memory→text 精度一致性，MGACE physical G+1 boundaries |

## Risk / review boundaries

- 最大风险是 P1 跳过 Init 后缺失某个准备步骤，或 test driver 多清一个状态而掩盖当前默认行为。用 pre/post 快照、调用次数和明确合同约束；结论必须写“该 test-only contract 下”的 PASS。
- snapshot/WW trace 会改变耗时；E0 与诊断模式分开，并检查 instrumentation 开销。Time/FOM 不用于 exact physics comparison。
- `CDTally` 含 raw-pointer registry，不能依赖浅复制恢复；需保留 owner 并验证 registry 的自引用关系。
- 观察 hook 不得执行额外 Random()，也不得改变已有表达式求值；particle context 在正常 lookup 前记录，actual ergPos 从原函数读取。
- 本草案只做 context/default-off 静态检查，未证明编译、链接或运行正确。批准后实现 callbacks/driver 时如需新增生产行为改动，仍须重新报告。
- 回滚/隔离：只移除任务内 experimental snapshot/build 或撤掉其 patch；共享 RMC 和 benchmark/reference 不动。此处未执行清理操作。

## Approval requested

已完成的静态检查见 [真实输出](logs/preparation-check.txt) 和 [只读检查脚本](verification/proposal/check_draft.py)：`git apply --check` exit=0；8文件的 base/draft 哈希及宏关闭后的非空行文本一致性通过。未应用 diff，未创建私有源码快照，未编译；这些 PASS 不属于 E0–E4 的动态结果。

是否批准在**本任务目录内的私有 RMC 源码快照**上应用本提案的 P0 probes 和 P1 初始化 gate，并实现任务内测试 driver，按已冻结判据继续 E0–E4？

批准范围不包含修复运行中新发现的问题、改变生产输运逻辑、正式 F11 架构实现、公共文件同步或 commit/push。该批准之所以必要，直接来自本任务第4、7、16节的停止规则；当前还没有获得。
