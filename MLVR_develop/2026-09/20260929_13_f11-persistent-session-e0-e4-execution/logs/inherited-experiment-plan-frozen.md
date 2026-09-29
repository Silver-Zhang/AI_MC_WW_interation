# E0–E4 pre-run protocol v1

日期：2026-09-29。**判据在任何运行之前固定；这是实验协议冻结，不表示源码补丁已获批准。** 本版本尚未执行输运、编译或任何 fresh-process oracle。E0–E4 为实验编号，不是知识库的证据等级编号。

## 1. Scope and provenance

- standard MGACE，neutron，fixed-source，Linux serial，MPI OFF、OpenMP OFF、AIS OFF。
- Cartesian Type=1 track-length mesh，Energy=-1，Normalize=1；native track-mesh WW。
- 固定 H2O：1001.50m / 8016.50m，原子比 2:1，密度 1 g/cm³；MGACE ERGGRP=30 12，中子 30 群。
- 箱体采用已验证的 F07 简单模型：x∈[0,20] cm，y,z∈[-50,50] cm，外部真空；本次 tally/WW 空间网格均为 2×1×1，x 边界 [0,10,20]。几何出处是 `20260927_02_independent-f07-field-re-review/cases/make_f07_case.py`；新增的两 bin 实验输入仍须新 fresh-run 检查，不能沿用历史 PASS。
- 常规 point source：位置 (5,0,0)，能量 2 MeV，starting weight=1，fraction=1。E4 第二轮移至 (15,0,0)。A 使用同一可表达的 point source；本实验不验证 response→adjoint-source policy。
- A 的物理 MaxAdjointEnergy 保存为 30 MeV（parser 要求 neutron/photon 两个输入，均填 30）；只执行 neutron。每轮独立记录转换后的内部群号，不把该群号覆盖到协议物理值。
- RNG TYPE=2，STRIDE=1000000；所有 seed 均为正奇数；禁用 restart、stop-time、surface source、WWG、PTRAC、采样扰动、burnup、Python source、HDF5 Field interface。
- RMC 基线：`5cfb0f771d0c5a2127c90d57e51ce672a4e3b616`。root 基线：`2f20c8da61041d1412fd67592ec6b909d3c12782`。数据文件及模型来源哈希见 `fixture-provenance.json`。
- 旧档案的 `/tmp/rmc-f08-cell-ww-build/bin/RMC` 本机当前不存在；不以旧 executable 或旧输出冒充本次 oracle。批准后另建任务内 build，记录完整 compiler/CMake flags、依赖、binary 和输入哈希。

## 2. Case matrix / seed namespaces

| 实验 | run | role | N | seed | source x | WW | diagnostics |
|---|---|---|---|---|---|---|---|
| E0 | warmup + 7 measured repetitions, per role | F / A 分开 | 20000 | 10001 | 5 | WW1 | timing-only，SCHECK=0 |
| E1 | 1 / 2 | F / F | 2000 / 3000 | 11001 / 11003 | 5 / 5 | WW1 / WW1 | snapshots+RNG，SCHECK=0 |
| E2 | 1 / 2 / 3 | F / A / F | 3000 / 3000 / 3000 | 12001 / 12003 / 12005 | 5 / 5 / 5 | WW1 | snapshots+role/cache，SCHECK=0 |
| E3 | 1 / 2 | F / F | 3000 / 3000 | 13001 / 13003 | 5 / 5 | WW1 / WW2 | selected-bin trace，SCHECK=0 |
| E4 | 1 / 2 | F / F | 1500 / 3500 | 14001 / 14003 | 5 / 15 | WW1 / WW1 | full tally diagnostics，SCHECK=1、CHECK=1 |

每个 E1–E4 run 单独建立 fresh process 对照，不跨 seed/population/source/WW 复用 oracle。初始化一次的证明要求：same-process 序列的 ReadInputBlocks/ReadAceData 调用计数均为 1；model identity/content 快照保持预定不变量。两个 CLI subprocess 永远不能冒充同进程。

## 3. WW definitions

G=30，g 为物理能量升序的 0-based 群索引，i 为 x 空间 bin（0/1）。

- WW1 lower(i,g) = 2^(-1-i-(g mod 2))。
- WW2 lower(i,g) = WW1(i,g)/4。
- 固定 WUPN=5、WSURVN=3、MXSPLN=5；upper=5×lower，survival=3×lower。
- WWE:N 使用该冻结 MGACE 的 G−1 个内部物理边界；native parser 的首端 0 和末端 INFINITY 哨兵保留。这张 WW lookup 网格与真实 physical G+1 boundaries 分开记录，不能把哨兵当 MGACE 上界。
- 2×30 个 lower 值均有差异，空间/物理群/bins/WWP 本身完全相同。数值是精确二进制分数，有利于 exact check。
- 批准后按已固定数据文件生成具体 input 和 manifest，在执行前锁定哈希；不得根据输出调整 source、bin、WW 或阈值。

E3 记录**真实 transport 调用**的 particle position/direction/weight/role/internal group、物理能量、实际 mesh index、实际 WW energy-bin index、lower/survival/upper、history ID 和事件序号。完整 lookup 序列滚动 hash；至少保留前 256 个事件及预先指定 bin 的首个事件。必须在每个空间 bin 的 source-energy 对应 MG 群观察到事件；若自然轨迹未覆盖，不凭数组变化判 PASS，标 INCONCLUSIVE。不得用手工调用 lookup 代替输运激活证据。

## 4. Frozen exact comparison

same-process 与 fresh 使用相同可执行构建、scope、模型/材料/数据库、source、N、RNG 配置、WW、tally 和 normalization。fresh 保持完整初始化；same-process 从第二轮才使用明确的 test-only prepared-state 入口。

具体安排：E1–E4 采用同一 test-driver binary 的 fresh/sequence 两个模式；fresh 每次独立进程、只执行一次完整 Init。先将 driver fresh 与同源构建的原 CLI 做单次等价检查，再执行同进程对照；E0 则用原 CLI 的 probe-only 与 uninstrumented 两个构建。binary 身份和入口差异分开记录，不把同源的两个 executable 写成同一个 binary。

必须精确一致：

- requested/completed source histories，本轮 N 与 denominator；单位源本例 denominator 应为 N。
- 每 history 的 initial seed/position/preposition（或无碰撞的全序列摘要），结束 RNG identity；记录 generator type/seed0/stride。
- 全部 2×30 个 group bins 及单列的两个 Tot 的 Score、ScoreTemp、Sum1、Sum2、Ave、RE；snapshot 使用 lossless binary64 或十六进制浮点表示。
- bank：transport 前所有真实粒子 banks/descendants 为空；函数自己 push sentinel 后，正常结束允许 neutron raw stack depth=1，真实 descendants=0，其它 stacks=0；与 fresh raw 状态一致。不能错误地把哨兵要求为零，也不能把深度>1 当作空 bank。
- 每轮 tally registry 大小、pointer 指向本对象的关系、统计 index 列表；未重复登记。
- role/cutoff、selected WW lookup tuple 和 deterministic cache 内容符合对应 fresh run。

不比较跨进程虚拟地址、wall time、含时间的 FOM 数值。地址仅比较 same-process 内对象是否保持身份；跨进程比较内容/shape/hash。SCHECK 的时间数组只要求 reset 时清零和本轮更新，数值矩/计数/索引则 exact compare。

同一串行 binary 和相同 RNG 配置下，不预先接受统计近似代替 exact。首个不一致即保留 first-divergence 记录并判 FAIL；不能看完结果后放宽容差、改 seed 或做 lifecycle 修复。若由于新发现的合理机制必须改判据，另起 v2，经用户决定后重跑双方。

## 5. E0 timing accounting and quality gates

F/A 各 warmup 1 次、正式 7 次；交替 F/A 顺序运行，population 和 seed 固定。使用 warm-cache 协议：不清 OS page cache，不宣称实现严格 cold cache。记录实际 load、CPU、build、文件路径和每次原始 timing。

时钟：Linux CLOCK_MONOTONIC；parent launch/wait 与 C++ probes 用同一时钟，记录 ns。E0 关闭大数组 snapshot、history 和 WW trace，probe 不调用 RNG；不能把 E1–E4 的详细诊断时间混入 E0。

| 输出量 | 边界 / 合并口径 |
|---|---|
| T_process | parent launch→main.enter；包含 spawn/loader/static initialization，不声称是纯 fork 时间 |
| T_input | ReadInputBlocks scope；含 geometry/material input parsing + CheckInpBlock。input 内的 T_geometry 合并于此，不重复加和 |
| T_geometry/material_postinput | InitiateMatAce inclusive 减去 XS、adjoint、显式 material output；包括其它 material/geometry derived setup，不声称只有 geometry |
| T_xs | ReadAceData scope，包含 XSDIR/ACE IO、MGACE 检查和 MG 表派生；不再把这部分计入 material residual |
| T_adjoint_prepare | treatAdjointMaterial；F 为 N/A，A 单列 |
| T_transport_prepare | CalcFixedSource 入口到 loop 前，减去完整 model_prepare inclusive；包括 source/tally/bank/particle 初始化和固定入口 bookkeeping |
| T_transport | 原生产 neutron history/batch loop，包含 DistributeSource、source sampling、bank drain、history tally、batch-end bookkeeping；不是只测碰撞核函数 |
| T_tally_finalize | FinalizeLoadBalanceChecker（serial 无 MPI 工作）+ ProcessTally：Ave/RE/normalization/SCHECK 末处理 |
| T_output | 标记的 material output、fixed-source tail、OutputEnding 分项；其它早期 banner/generated-input I/O 明确包含在 startup glue 中，不声称全部文件 I/O 已单独分离 |
| T_total | parent launch→wait completion；不含 Python 创建/解析实验输入和分析结果的时间 |

时间区间使用嵌套 interval tree 求 exclusive time，不能把 inclusive timers 直接相加。额外保留 startup glue、shutdown/flush residue 和所有 probe 开销说明。三项总账：

`T_total = T_startup/init + T_transport + T_finalize/output`

其中 startup/init 为 transport_begin 之前的 wall time；material output 等早期输出作为其子项展示。finalize/output 为 transport_end 之后至 parent wait_end 的 wall time。启动占比按每次 `T_startup/init / T_total` 计算，然后报告均值与样本标准差（ddof=1），并报告各阶段均值/标准差。

质量门：完整 7 次且每次成功/边界配对/所有区间非负；总账闭合误差≤max(1 μs, T_total×1e-6)。正式样本 T_total 的 CV>10% 或启动占比 std>0.05 则性能结论 INCONCLUSIVE，保留原始数据，不自动换 N。另用 7 对 uninstrumented/probe-only fresh runs 检查观测开销，tally/RNG 必须一致；平均 wall time 增幅>5% 时不把测得占比外推为原程序性能。

## 6. E1 run reset contract to review

只在任务 harness 中准备每轮状态；不为 production 写 reset API。不复制/改写 history loop。

- 在 old-run snapshot 完成后重置 finish、current batch、完成 history、source count、collision/missed count、restart/interval、start-weight/origin、fission multiplicity/source statistics 和所有 particle banks。
- 保留 geometry/material/raw MGACE/tally definition/WW definition，记录对象 identity 与 immutable payload hash。
- RNG 同时设置 type、seed0、current seed、stride、position、position_pre，并记录首 history 的真正 seed；避免只设 seed0 延续 static fast path。
- 每轮 particle 临时状态及 XS/geometry caches 明确重建；列出被重建项与 fresh pre-transport 状态比较；不能只依赖 vector.resize(size,true)。
- 清 tally 六组数值、touched/stride index；统计 tester 按 N 重设，保留单次建立的索引/registry；输出文件按 run 独立命名，旧流关闭后清指针再开，timer 新建/reset 到相同初态。
- hook 的 prepared-state token 只有在上述快照核验通过后才能消费；首次 run 未 armed，必须走原 Init。

此 contract 的具体 harness 字段赋值尚未实现/编译，须与补丁一道审批后实施。发生未列明状态时先报告，不悄悄扩大 reset。

## 7. E2 role contract and stop-on-failure

E2 首先检验一个**明确声明的 test-only CLEAR/REBUILD contract**，不声称这些步骤目前自动存在：保存物理 cutoff 原值，每轮设定 FixedSource/AceData/Particle 三层 role；A 前从零建立 adjoint XS/fission arrays，F 使用原始 MG base；particle cache 随 role 重新建立，模型/XSS identity 和内容保留。

在 before switch / after clear / after rebuild / before transport / after finalize 保存三层 flags、物理 cutoff 与内部群号、所有 adjoint/fission 数组、相关 particle cache、source/tally/WW identity。与对应 fresh phase 比较；对一次性 true 传播、cutoff 再转换、+= 和 stale cache 四类点分别给出观测。

本 H2O 模型不含可提供非零裂变项的材料；fission-adjoint 数组只检查其预期零态，不把该结果外推为非零裂变项的重建验证，不为扩充覆盖擅自更换模型。

若该预先声明 contract 仍失败，停止该分支，定位首次不一致及 CLEAR / REBUILD / immutable-base redesign 类别；不现场追加修复。旧生产路径的四个风险只标静态证据，不把手动 clear 后的 PASS 说成“当前 RMC 天然可切换”。不自动扩展到 A→A 等额外序列。

## 8. E4 reset and memory extraction

E4 保留同一个 tally definition/storage owner；不再调用会重新 append registry 的 InitiateTally。先 snapshot Run1，再依照 §6 清 per-run 统计并断言全零/索引为空/registry 不增长；保留 mesh/bin/offset 定义。

在 ProcessTally 返回后、OutputSummary 前读取全部 value/RE；按 GetMeshErgPtr 导出 2×30 群数据，Tot 单列。与 `.Tally` 的比较以实际打印精度格式化 memory double 后 token 一致为准；不要求截断文本与内存 bitwise 相同。文本读回按 ID/mesh/group 定位，保留 zero-score bins；不是正式 F10 Adapter。

MGACE 内存检查：centre/width→每群 lower/upper；G+1 长度31、MeV、finite、strictly increasing、相邻 upper/lower 一致、最高 upper=2×lastCentre−lastLower、跨核素一致；tolerance 预定为 `max(1e-14 MeV, 1e-12×max(|a|,|b|))`，不得借 WW 哨兵补上界。Tally physical Group rows 的顺序与 lower 一致，内部 group g 映射到 physical index G−g。

判别两场：用所有群加总后的左 bin flux 占比 f_left；Fresh Run1 与 Fresh Run2 的 f_left 差须>0.10。若未产生可区分 pattern，E4 的污染排除证据 INCONCLUSIVE，不能只凭两个 seed 得到不同数值判通过。E4 正式 PASS 仍要求逐数组 exact oracle comparison。

## 9. Result classification and execution stop

- PASS：完成本实验全部 frozen gates。
- FAIL：实验实际执行且违反既定数值/状态条件。
- BLOCKED：缺少批准的 instrumentation/control seam 或无法获得必要环境/数据，未完成实验。
- INCONCLUSIVE：已运行但观测覆盖/计时质量不足。

当前 E0–E4 **全部 BLOCKED（not run）**。本任务第4、7、16节规定，暴露原循环入口/加入内部 instrumentation 需要修改生产源码时，先提交 proposed patch 后停止。禁止把宏、链接拦截、复制生产源码或在任务内私有快照改入口当成绕过审批的办法。

后续提案仅在本任务目录内 RMC source snapshot 应用；共享 `RMC/`、STATUS/INDEX/KB、reference 均保持原状。任何架构选择仍由用户另定。
