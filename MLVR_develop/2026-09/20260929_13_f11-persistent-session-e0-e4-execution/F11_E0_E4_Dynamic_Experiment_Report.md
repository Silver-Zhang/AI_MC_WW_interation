# F11 E0–E4 Dynamic Experiment Report

2026-09-29 · **E0–E4：全部 PASS（仅在本实验 lifecycle contract 下）**

## 1. 结论与范围

| Experiment | Verdict | Main finding |
|---|---|---|
| E0 | PASS | F/A 各7次阶段时间完整、闭合；warm-cache 启动占比 F 2.956%、A 36.884% |
| E1 | PASS | F1/F2 每轮与独立 fresh 精确一致；第二轮3000 histories，未带入第一轮统计 |
| E2 | PASS | 显式角色/派生表/particle cache 准备后，F→A→F 三轮状态与 fresh 对照成立 |
| E3 | PASS | WW2 的1,247,301次真实查窗与 fresh WW2 全序列一致，实际读取新 lower/survival/upper |
| E4 | PASS | 同一 tally owner 清零后得到独立第二场；2×30 Ave/RE 与文本一致，真实31条边界已导出 |

冻结域：standard MGACE / neutron / fixed-source / Cartesian Type=1 track-length tally / Energy=-1 / Normalize=1 / native track-mesh WW / Linux / MPI OFF / OpenMP OFF。H2O 箱体、30群、2空间 bin、单位单源；不扩展 CE/photon/coupled/burnup/weighted source/HDF5 Field API。

**结果不表示 production RMC 已有 persistent API。** 原入口仍每次全初始化；本次通过 task-private P1 gate 和显式 CLEAR/SET/REBUILD 才取得这些结果。未选定全外耦合、hybrid、persistent 或 fully internal 架构。

## 2. Provenance / authorization / build

- RMC：`Neural_Network_WW_Iteration`，`5cfb0f771d0c5a2127c90d57e51ce672a4e3b616`，开始及结束 clean。
- root 起点：`f4730fdb036ea8530faab228b2e8c38e81482f6b`。未切分支/reset/clean/commit/push。
- 用户本轮已明确批准 P0/P1、driver、snapshot/comparator、构建、fresh oracle 与 E0–E4；[原文](logs/user_task_original.txt)。仅在任务内私有 snapshot 应用实验 patch。
- 编译器 GCC 13.3.0、CMake 3.28.3、C++14、Release（-O3 -DNDEBUG）、HDF5 1.10.10；串行、AIS OFF、Python API OFF、catcherr OFF。依赖 submodule revision、真实 flags/配置/失败及成功构建输出完整保留。
- [实际私有 snapshot diff](changes.diff)：9个 src 文件（Task 11 的8个 probes 文件 + `CalMode.h` 条件 friend access）；另有私有构建支持/离线依赖加载及 delivery/GITSHA。没有 history loop 副本、公式或物理分支修改。
- [宏关闭文本等价检查](logs/default-off-source-check.txt) 通过；[source base hashes](logs/snapshot-base-sha256.txt)、[build info](logs/build-info.txt)、[binary SHA256](logs/binary-sha256.txt)、[开始状态](logs/repository-state-start.txt)、[结束状态](logs/repository-state-end.txt)。

`verification/build/plain` 为内部 P0/P1 关闭构建；`probe` 为开启构建。v2的两种CLI均包含相同的计算结束后标量collector，观察实际denominator/RNG，不进入输运循环；不能将其称为完全没有任何观察指令的binary。两者包含原 CLI `RMC` 和 task-private `F11Driver`。plain driver 只允许 fresh；其返回点读数用于无插桩 moments/RNG 对照。条件 friend 不改变 class layout 或生产签名。

## 3. Frozen contract and executable harness

完整字段级操作：[run-reset-contract.md](logs/run-reset-contract.md)。实现：[driver](verification/harness/driver_main.cpp)、[P0/P1 callbacks](verification/harness/probes.cpp)、[declarations](verification/harness/probes.hpp)、[比较器](verification/harness/compare.py)。

- CLEAR：finish/completion/batch/source/collision counters、banks（包括上一轮 sentinel）、starting weights、source临时库、tally六组数组/touched/stride索引、statistics tester每轮数组、timer与run diagnostics。
- SET：N、seed0/stride/position/preposition、source point、run/output identity、WW lower。
- REBUILD：mode flags、adjoint XS/fission派生表、物理 cutoff→内部群、particle scratch/cache、WW survival/upper。
- KEEP：geometry/material/raw MGACE、tally owner/registry/index/mesh/group、WW mesh/energy/parameters。真实 owner地址与相关内容/hash 均核查不变。
- 首轮 full Init；后续准备完成才 arm，一次消费；preconditions 不成立 hard fail。每个 sequence 的 input/model/XS 调用计数均为1。

预先允许的一项 phase 差异：原 fresh A 在首次 SampleFixSource 才把 particle role 设 true；prepared A 在 arm 前提前设 true。该例外在首次数值运行前写入合同；其它 pre-transport cache/role/cutoff/数组仍精确对照，运行后的三层角色完全匹配。

冻结模型和 N/seed/WW 来自 Task 11；[输入 manifest](verification/fixtures/manifest.json)、[生成脚本](verification/harness/make_fixtures.py)、[运行前哈希](logs/pre-run-freeze.json)。E0 运行前仅修正 Python runner 的等待方式：timing mode 使用阻塞 OS wait，避免 timeout polling 带入短运行耗时；无 RMC/判据修改，见 [记录](logs/pre-e0-runner-note.json)。

## 4. Baseline gates — PASS

两组：Forward N=2000/S=11001；Adjoint N=3000/S=12003。每组执行 plain driver、probe driver、probe原CLI，共6个独立进程。

| Gate | Forward | Adjoint |
|---|---|---|
| fresh driver vs 原 CLI（finalized snapshot） | exact | exact |
| P0-off vs P0-on（driver返回点） | exact | exact |
| history counts / denominator / source / banks / role | 一致 | 一致 |
| 全部 Score/ScoreTemp/Sum1/Sum2/Ave/RE | exact | exact |
| RNG seed0/current seed/stride/position/preposition | exact | exact |
| 全62行 `.Tally`（含2个Tot）/左bin Tot diagnostic response | exact | exact |

[真实 gate 输出](logs/p0-noninterference.txt)、[逐次命令和退出状态入口](logs/gates-execution-v2.txt)。P0-off 的端点 RNG identity 有直接证据；没有伪称采集了无插桩 binary 的逐history轨迹。P0-on 保存全部 history 起始seed序列，正式 fresh/sequence 间逐行相同。

有限 binary64 数值以17位十进制输出，比较时按 binary64 bit pattern；整数 seed 独立保留。统计 checker 非有限诊断量用 nan/inf token，未比较 NaN payload；时间/FOM和其时间依赖检查不纳入 exact physics gate，但原值留档。[序列化检查](logs/float-serialization-check.txt)。

## 5. E0 — timing / observer overhead

**版本与补测说明**：E1–E4 使用v1 binary，保存在 `verification/build/archived-v1/`；其 gates 和源实现封存在 `logs/implementation-v1/`。初次E0 v1的计时质量通过，但缺逐run内存归一化metadata，因此未作为最终完整交付。v2增加公共结束点只读标量collector后重做gates与E0；下列数据仅来自v2，未混合或择优取样。[修改原因/范围](logs/endpoint-metadata-amendment.md)、[v2运行前哈希](logs/pre-e0-v2-freeze.json)、[v1原始汇总](logs/implementation-v1/E0-timing-decomposition.json)。CLEAR/SET/REBUILD和阈值均未改变。

每种 role：probe warmup1 + measured7；plain CLI 同样 warmup1 + paired measured7。共32进程，N=20000、seed10001、WW1、warm filesystem cache；没有清cache或cold-start主张。所有编译完成后才做性能运行。

下表单位 **ms，mean ± sample std（ddof=1）**。input 内几何检查合并于 input；model residual 排除了 XS/adjoint/material output；transport 是真实 source-history/batch loop（包括抽源、bank、计分）。

| Stage | Forward | Adjoint |
|---|---:|---:|
| process / loader | 3.8543 ± 0.8761 | 4.6516 ± 0.7810 |
| input + input 内几何检查 | 0.2412 ± 0.0508 | 0.3104 ± 0.0753 |
| input 后 geometry/material residual | 0.0359 ± 0.0060 | 0.0434 ± 0.0106 |
| XS / MGACE load + prepare | 15.5155 ± 1.2566 | 16.5040 ± 1.5019 |
| adjoint preparation | N/A | 0.0040 ± 0.0004 |
| transport preparation（排除 model） | 0.0224 ± 0.0039 | 0.0211 ± 0.0033 |
| history / batch transport loop | 680.2990 ± 6.0842 | 35.0961 ± 0.5038 |
| tally finalization | 0.0037 ± 0.0004 | 0.0034 ± 0.0005 |
| 显式 output scopes | 2.7294 ± 0.0503 | 2.6883 ± 0.0441 |
| startup glue / early I/O | 1.1787 ± 0.2900 | 1.4651 ± 0.3038 |
| shutdown / flush residue | 1.5413 ± 0.1658 | 1.4472 ± 0.1545 |
| total | 705.4214 ± 6.0247 | 62.2346 ± 2.6706 |

总账（单位ms）：

| Role | Startup/init | Transport | Finalize/output | Total | Startup fraction（mean ± sample std） |
|---|---:|---:|---:|---:|---:|
| F | 20.8549 | 680.2990 | 4.2675 | 705.4214 | 2.9563% ± 0.3133个百分点 |
| A | 23.0054 | 35.0961 | 4.1330 | 62.2346 | 36.8838% ± 2.2905个百分点 |

`total=startup/init+transport+finalize/output`；早期 material output 已在 startup 子项里，不能重复加到总账。区间配对、嵌套关系、非负/exclusive闭合均通过。

paired plain/probe 平均 wall-time overhead：**F +0.683%、A +0.840%**，均≤5%。total CV：F 0.854%、A 4.291%，均≤10%；startup fraction std≤0.05。paired physics `.Tally` 与结束点 RNG/source metadata 全相同，每次实测 denominator=20000。

证据：[14次原始分解及汇总](verification/E0/timing-decomposition.json)、[全部32次执行目录索引](verification/E0/runs.json)、[真实运行输出](logs/e0-execution-v2.txt)。每个目录保存 parent launch/wait ns、C++原始 timing events、stdout/stderr、exit code、input和binary hash。

**解释边界**：本模型 warm-cache 启动成本约20.9ms（F）/23.0ms（A）；F相对占比小、A相对占比大。这不是 persistent 实测加速，也不意味着这些时间都可省略；每轮源/tally/mode准备仍存在。不由此选择架构。

## 6. E1 — Forward→Forward PASS

F1(N=2000,S=11001)→F2(N=3000,S=11003)。两轮均有独立 fresh；包括每个 history seed序列、全部62槽位统计/状态/输出 exact。F2确实完成3000 histories，denominator=3000，registry=1。

before-clear、after-clear、after-rebuild、before-transport、after-transport、after-finalize 均有 snapshot；第二轮六数组全零、touched空、真实bank空，原loop结束只有 neutron sentinel（raw sizes `[0,1,0,0]`），无真实descendant残留。输入/XS各只初始化一次，owner与base contents保持。

证据：[完整判据结果](verification/E1/verdict.json)、[fresh F2](verification/fresh/E1_F2/E1_F2.snapshots.jsonl)、[同进程 F2](verification/same_process/E1/E1_F2.snapshots.jsonl)。

## 7. E2 — Forward→Adjoint→Forward PASS

N=3000 each；S=12001/12003/12005。三轮 final state + fresh output均exact；同时通过 pre-transport mode/cutoff/derived arrays/particle cache对照，不能仅凭tally判断。

| Transition | 直接观察 |
|---|---|
| F→A | adjoint/fission arrays 从空基态开始；重建后 FixedSource/AceData/particle flags=`1/1/1` |
| A cutoff | 物理输入30 MeV；原 LocateMgErgGrp 转为内部群1，最高物理上界17 MeV；与 fresh 一致 |
| A→F | flags=`0/0/0`；cutoff恢复未启用的F默认20；adjoint派生数组清空；particle缓存重建 |
| 第三个F | 与Fresh F2全数组/RNG/state/输出exact；无检测到的A残留 |

[状态转换数组/缓存证据](verification/E2/verdict.json)、[A全过程](verification/same_process/E2/E2_A.snapshots.jsonl)、[最后F全过程](verification/same_process/E2/E2_F2.snapshots.jsonl)。

**H2O无非零裂变项**：A的fission派生表为零，F清空；本实验验证F/A lifecycle mechanism，不证明非零adjoint-fission arrays的完整rebuild。没有扩展 fissile 模型。

## 8. E3 — WW hot update PASS

N=3000 each，S=13001/13003；WW2 lower=WW1/4，固定 upper=5×lower、survival=3×lower，mesh/energy/WWP不变。

| Run | 全部真实lookup events | source-group空间bin0 / bin1事件数 | 与fresh |
|---|---:|---:|---|
| WW1 | 305,270 | 3,661 / 243 | 全有序序列exact |
| WW2 | 1,247,301 | 9,753 / 1,356 | 全有序序列exact |

source 2MeV对应 physical group0=20（外部第21群），实际 MG centre=1.985MeV、内部transport群10、WW energy-bin0=20。WW2两个空间bin实际读到 lower=0.125/0.0625、survival=0.375/0.1875、upper=0.625/0.3125。

[查窗证据汇总及first selected events](verification/E3/verdict.json)、[同进程WW2完整TSV](verification/same_process/E3/E3_WW2.ww.tsv)、[fresh WW2完整TSV](verification/fresh/E3_WW2/E3_WW2.ww.tsv)。每条记录含history、位置/方向/权重、粒子类型、物理能量、spatial bin、物理group0、内部group、selected energy-bin和三个bounds。事件数量只提供规模信息；PASS来自完整序列对照及直接bounds/coordinate核验。

## 9. E4 — reset / memory Field PASS

Run1 x=5/N=1500/S=14001→Run2 x=15/N=3500/S=14003；SCHECK=1。

- Run2前：Score/ScoreTemp/Sum1/Sum2/Ave/RE全零，touched/stride索引空，checker moments/counts/time全零且N/20重设；registry始终1，统计索引始终62且无重复。
- 同一tally owner/storage、mesh/group定义保留；没有重新InitiateTally。
- ProcessTally完成后、OutputSummary前取内存：每轮2×30 value/RE；2个Tot另列；与`.Tally`按原4位科学计数格式全62行匹配，与对应fresh全精度数组exact。
- 两个fresh场左bin总flux占比：0.7211213 / 0.2860071，差 **0.4351142 > 0.10**，达到预声明可辨别门槛。

[判据与reset证据](verification/E4/verdict.json)、[Run2快照](verification/same_process/E4/E4_S2.snapshots.jsonl)、[Run1 Field](verification/E4/E4_S1.field.json)、[Run2 Field](verification/E4/E4_S2.field.json)。这是实验导出，没有实现正式 F10 Adapter/API。

## 10. Actual G+1 boundaries

从实际loaded MGACE memory的centre/width/lower构造，两个核素均校验；31个有限、严格升序MeV边界，最高edge=**17MeV**，centre±width/2连续且跨核素相符；逐条Tally Group/lower行对应物理升序。外部Field axis无内部反向群号，Tot不占群轴。

真实数值：[Run1的31个edge](verification/E4/E4_S1.physical-edges-MeV.json)、[Run2的31个edge](verification/E4/E4_S2.physical-edges-MeV.json)、[边界检查](verification/E4/E4_S2.boundary-checks.json)。最低edge按实际double保留约`1.39e-10 MeV`。没有用WW的0/∞哨兵补MGACE上界。

## 11. Source normalization

每轮保存requested/completed、实际total starting source weight/denominator、单源初始weight、component fraction/bias probabilities：[归一化记录](logs/source-normalization.json)，诊断轮次的原始值在phase snapshot，E0在各run的`.run-metadata.json`。

本fixture source initial weight=1、单组件probability=1；所有正式same-process 9轮及其9个fresh对照、最终gates与E0均有实际归一化记录；`N == completed == denominator`。**这是本fixture的实测关系，不是一般的N与源归一化分母等价定理**。未验证任意源权重，也未更改F10 frozen contract。

## 12. Failures / limitations

正式gates与E0–E4均未出现物理/lifecycle FAIL；没有RMC缺陷修复或根据结果追加reset。初期仅处理实验代码编译/API接入问题：ParticleStack没有const size/empty、object-library依赖include传播、CalcFixedSource私有访问；原始失败log保留，所有正式执行使用各自版本记录的binary hash。

未覆盖：CE、photon、coupled、MPI/OpenMP、burnup、任意源权重、非零裂变adjoint派生表、多mesh/复杂geometry、长期多轮内存增长、任意input热替换。E0只对该warm-cache小模型有效。未实现正式Session/Controller/Field/WW Builder/Reconstruction/ResponseDefinition/convergence/best-FOM。

## 13. Evidence / reproduction

最终证据集 **51个进程、56次calculation、705000 requested histories**，所有进程exit=0；其中6个gate进程、9个formal fresh、4个same-process sequence（9轮）、32个E0。正确性来自前述checks，不以exit=0代替判断。[inventory](logs/execution-inventory.json)。包含保留的v1 gates/E0初步记录在内，全档案共89进程、94次calculation、1,360,000 requested histories，全部原始记录保留。

- 构建：配置命令见`logs/configure-probe-02.txt`、`logs/configure-plain.txt`；最终flags与依赖见`logs/build-info.txt`和两个build的CMakeCache/compile_commands。
- 运行：每目录`execution.json`给精确argv、cwd、环境、parent timing、binary hash、exit；`sequence.txt`、完整input、stdout/stderr和原RMC输出均保留。
- 门槛：`F11_EVIDENCE_TAG=replica_ python3 verification/harness/run_experiments.py gates`；正式：同脚本`matrix`与`e0`（先复制整个任务到新的验证目录，在副本执行；原档案不覆盖。精确复现E1–E4使用archived-v1 binaries/source；最终E0使用v2）。
- 仅重算汇总、不重跑RMC：`python3 verification/harness/analyze_results.py`。[实际分析输出](logs/analysis-output.txt)、[机器可读汇总](logs/experiment-summary.json)。
- P0缓冲观察再写出，E0只启用phase timing和共用结束点metadata；诊断trace的写入耗时没有混入E0性能结论。
- [证据文件哈希清单](logs/artifact-manifest.sha256)、[清单范围及校验方式](logs/artifact-manifest-policy.md)、[归档自检](logs/final-verification.txt)。

## 14. What the human needs to decide

证据支持：在这个冻结子域中，明确管理run state、mode-derived state、输出和RNG后，可以用同一个模型/XS owner连续驱动原输运循环，并取得与fresh相同的结果。

接下来由用户决定是否先独立复核该实验包，以及这些有限证据是否足以进入F11架构设计。性能收益还需按目标问题规模衡量；本任务到E0–E4证据交付停止，不替用户选架构。
