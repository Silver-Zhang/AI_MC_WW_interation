# 基线、fresh oracle 与 Stage2 门禁（运行前判据）

导航：§1 身份/模型；§2 原七门禁与新增G0链接检查；§3比较标准/§3.1时间白名单；§4命令/证据/停止。当前只是设计，尚未生成运行输入/driver、编译或执行门禁；批准后先冻结baseline再修改生产源码。

## 1. 固定条件与基线

RMC baseline为330f091eb0296e0d0124237ba7d9a22b81aee852。两Stage1文件sha与已验证构建manifest一致；保留的Stage1串行binary在logs/environment.json绑定，不作为唯一基线。新建/tmp/20261011_05_f11-prepared-run-lifecycle/baseline-src及baseline-build私有副本；不在生产RMC运行会更新submodule的CMake、不checkout生产分支。

配置固定RelWithDebInfo、GCC13.3、CMake3.28.3、HDF5 1.10.10；MPI/OMP/AIS/Python-off、loadmodules=ON、test=ON、mpiproc/ompthrd=1，与Stage1相同。原立项记录为Python3.12.3、h5dump可用；当时没有h5py/numpy，不依赖它们比较。实施前重新确认上述环境；保存cache/flags/command/依赖、源码manifest和binary SHA。

数据库 /home/silver/NucXS_Library/RMC_DATA；xsdir sha256=970e85ad3e7f365868dcba69d348c1626d82b2c127534622af7a43fb01c9f62b，multigroup/mgxsnp sha256=1d26fac6d32bfb84539d59d5549d809b70e9d5a4f9e34c58034cb9f6cba57001。读取而不修改。H2O使用1001.50m/8016.50m，30n/12p。已有92235.50m只用于“非零产生项拒绝”负例，先记录其实际νΣf，不伪造产生项。

第一组模型从Stage1 MG输入复制到本任务，不改原文件：x=[0,20]、y/z=[-5,5]的H2O盒，4个x mesh、每bin体积500cm³；Type1/track TL/Energy=-1/Normalize1，cell+全30群及Tot mesh数据。前向F0：point(0.5,0,0)、+x、E=2MeV、unit weight；伴随A0：point(19.5,0,0)、-x、E=2MeV、physical neutron max=30MeV（fresh ADJOINT卡两值30/20，未启用photon保持20MeV默认）；F1可用point(1.5,0,0)以验证新源实际生效。core源抽样算法保持。源definition通过普通前端检查/规范化一次；prepared首版只允许单个固定POINT/ENERGY/VECTOR+DIRECMIU=1且WEIGHT=1的无用户分布源（lifecycle-design §3.1），不使用DISTRIBUTION。

所有序列独立进程初始化rootSeed=17、stride=100000、firstOffset=0；offset累计本序列已完成N。fresh的每一条run都有相同role/NPS/source/WW/seed0/seed/stride/local position=0/pre=-1000，而不把root17重复用于每个oracle。有效seed按lifecycle-design公式精确计算并留存十进制uint64，旧double输入parser不承载这些大seed。

## 2. 门禁矩阵

| Gate | 设置与执行 | 必要判据 |
|---|---|---|
| 0 构建/全局所有权 | root末尾新子目录注册；源表/compile_commands/link.map/nm检查，test=OFF与不支持宏配置的target注册检查 | main/globals各executable恰好一份；原生产TU宏/选项一致；无重复或未解析extern；普通RMC和原CTest注册保持。不是宣称MPI/OMP/AIS/Python prepared可用 |
| 1 普通回归 | 重建330f旧版与Stage2新版；复用Stage1五任务输入、9个原CTest、三组500-history只读诊断；LCG共用cache的普通Type1/Type3各补一个500-history旧/新对照（保持seed17/stride100000）；另从任务副本生成普通WEIGHT=2与普通WEIGHT变量分布两个旧/新对照各500 histories，不改变参考输入/结果 | physics零容差，源/RNG/IEEE数组/WW事件及输出同Stage1；原six-mode分支保留；不是仅“编译成功” |
| 2 FF | F0 N=1000 offset0；F1 N=2000 offset1000；各自fresh一次 | 每run完整数值/历史/RNG等价；N=1000/2000，实际D=独立W0=N且全部采样w=1；源identity与实际采样point改变；CLEAR前后、bank/registry不累积 |
| 3 FAF | F0 1000 O0；A0 1500 O1000；F0 2000 O2500；三个fresh | 每run均等价；Fixed/Ace/Particle role一致；A派生数组每项等fresh；最后F派生清空、cutoff与cache/weight policy恢复 |
| 4 AA | A0 1000 O0；A0 1500 O1000；两个fresh | 第二A仍逐元素等fresh、不+=叠加；散射与零裂变派生shape/内容检查；不得外推非零裂变支持 |
| 5 native WW | 同一F序列OFF → WW1 → WW2 → OFF，每runN=1000，offset0/1000/2000/3000；四个fresh；另FAF+WW三个500-history（F:WW1/A:WW2/F:WW1，offset0/500/1000）逐个fresh | WW1用Stage1交替lower0.1/1.0；WW2在固定shape上改为0.05/0.5；保持WWP；至少on case有split>0且roulette>0、bank pop/drain真实发生。真实查询记录mesh/物理energy/三界与本run数组吻合；OFF无WW查询且default weight cutoff恢复 |
| 6 模型/资源 | 上述全序列观察raw加载/注册调用；另固定N=100、F/A交替20个half-run，日志逐行写文件不累存 | raw MGACE读取/InitiateMatAce/InitiateTally各仅初始化一次；owner地址、raw数据digest、definition、registry大小/顺序保持。每runFinalize一次；end bank计数正常、timer停止、进程句柄有效、FD数不持续增长；warmup后live容器shape/capacity稳定 |
| 7 负例 | 下列每种各独立child process，也在完成一个run之后测试可前置拒绝的无效规格 | 规范化错误信息、非零退出；前置拒绝无新history/旧tally不变；准备后失败标Failed、不继续；不伪造成功receipt |

G2–G6每个成功half-run额外要求：receipt记录实际N/D/W0、逐history检查次数、min=max=1、违规数0及unitSourceWeightsVerified=true；源检查不多抽RNG、WW/后代权重不误计入W0。三段计时及旧统计标签必须满足§3.1。FF不同N、FAF/AA、FAF+WW和20轮复用仍一段一个fresh oracle，没有删减原门禁。

Gate7负例：未Initialize调用Run；重复Initialize；Finish后Run或重建prepared模型；wrong-owner引用；非法role枚举；N=0/负值；空/非neutron/非单位有效weight源；WW role错/shape错/负数/NaN；无固定WW topology时要求ON；非Type2/偶seed/stride=0/offset乘法溢出或越周期；stride=1触发真实history超额；执行未结束/重复Finalize的状态禁止（生产API不得提供手动finalize绕过入口）；非零νΣf材料拒绝；受限profile之外CE/photon/restart/TIME_REDUCE等至少代表性拒绝。

**G7a 源合同前置负例**：任务私有输入分别覆盖常数WEIGHT=2、WEIGHT=D1（至少两值；另恒1也拒绝）、SOURCE WEIGHT=1但ENERGY等分布带非平凡prob/bias、依赖/子分布、两个源FRACTION≠BIASFRAC、多源即使比例相等、无偏分布、非Point/有CELL/transform。普通parser须先能合法解析，保存规范化后的变量绑定与概率，才能认定是prepared拒绝而非语法错误；必要数值非法项以owner API传参验证，不伪造生产对象。每项首run和一个成功run后各一次，预期在CLEAR前拒绝，零新增GetRandSeed、旧结果不变、无成功receipt；不依赖输入WEIGHT字段或D=N作通过依据。

**G7b 采样后防线负例**：严格白名单内没有自然生成非单位权重的正常输入，不能声称用上述前置拒绝已覆盖采样后检查。driver新增`--mode source-weight-audit-selftest`，对独立CDFixedSource按正式ResetRunState/SetPreparedRun方法启动audit，然后直接调用生产CheckAndRecordPreparedSourceWeight(1.0/2.0/0.0/负数/NaN/Inf)及VerifyPreparedSourceWeights。检验正常单位值和实际累加、首次非单位/非有限抛异常、次数不足终检失败；没有friend、私有写入或替代transport loop。这仅是owner单元门禁，单列结果；整条Run失败传播由同一catch的真实stride超额负例及源码控制流复核覆盖，成功receipt只能在所有终检后构造。运行时若真实抽到非法w，必须在输运该粒子/Finalize之前失败，保留run/history/w/audit错误证据且该系列不得继续。不得为触发负例放宽source白名单或在生产接口加测试注入开关。

禁止人工写私有状态制造负例。重入/结束中的状态检查通过API序列及代码路径确认，不能为测试开放private field。正例所有half-run与真正fresh进程一对一匹配；不能只比较最后F、最终文本或两张输入数组。

若WW1/WW2未触发必需事件，判覆盖不足，保留结果并调整预先记录的新case（同时重建fresh），不能把零事件当通过。若要解除非零裂变限制，必须另经用户批准增加有非零裂变贡献的FAFA每段fresh与实际产生事件门禁；本版默认不解除。

## 3. 预设比较标准

1. 模型/核数据/编译参数/输入sha必须一致。完成NPS与归一化分母、batch、finish、collision/miss、合法bank计数、RNG参数和history始末seed完全相等。源历史及后代起始/结束记录包含type、pos/dir、group/energy、weight；零得分history仍在N与序列中。
2. 捕获Finalize前的原始Score/ScoreTemp/Sum1/Sum2/Sum3，以及Finalize后的所有tally Ave/RE、各30群与Tot、完整spatial bin。用每个double的IEEE uint64/hex或可还原hexfloat序列逐项比较，shape/顺序必须同，物理容差=0；摘要hash必须绑定原始序列文件。原mesh不除体积改写；任务私有通量视图可使用阶段0既有c_i表，对照也必须相等，但不宣称Field API完成。
3. touched/index2/scoreStride结束与下次开始的合法状态；registry地址相同只比较persistent各run间，不跨进程比较ASLR地址。fresh/persistent比较对象类型、shape、offset与定义hash；unused legacy未初始化字段不读取。当前fresh在SampleNeutronSource.cpp:222首次源采样后才把particle伴随flag置true；prepared CHECK提前置本次role。此采样前标志时序差异明确允许，必须在第一条源采样后及所有真实输运中逐history核对三类role，不能据此排除任何输运期差异。WW-off保留topology与fresh没有运行窗的数据representation可以不同，只允许明确的未启用存储差别；实际开关/policy与零查询必须等价。
4. 每次A全部派生向量与fresh逐项相同；F无旧派生。物理MeV及其A内部群号分别记录，不把群号作为下次物理输入。raw核数据内容/地址在persistent序列前后保持；只允许角色派生与粒子缓存变动。
5. StatisticsTester启用一组FF不同N门禁，采用20的整数倍N，并必须有非零得分≥50的实际诊断bin；不够则覆盖不足，不能跳过整个统计器。所有不依赖墙钟的scores/counts/mean/RE/VoV/PDF及其checks精确比较；只有§3.1逐字段白名单允许时间差异，并校验清零、shape、数值类别和语义标签。普通输出日期/构建banner/耗时/吞吐/临时路径按既有Stage1命名字段记录，不能用模糊正则删除任意数值行。所有例外路径在首次运行前固定于比较manifest。
6. Gate6先warmup前三次，后续各run定义/registry/FD身份、活动bank及固定shape/capacity不持续增加；记录/proc/self/status的VmRSS、FD数。第4→20次净RSS增加预设上限4MiB，超过就定位分配来源，不能事后放宽。RSS单点不等于泄漏证明；若失败或明确可疑再做有限sanitizer/heap诊断，与旧普通路径区别。未做sanitizer不得宣称完整内存安全。
7. 所有运行/比较exit=0方可通过；负例exit非零且拒绝在预期阶段。G0或Gate1–7任一链接/物理差异、未观察真实WW、重复初始化、状态污染或跨段超额都不能ACCEPT；保留失败证据，不更新reference或靠统计误差放行。

### 3.1 时间字段的封闭例外表与计时门禁

以下仅豁免fresh/persistent的时间数值相等；保留两侧原值、shape、发生run和例外理由。表外字段默认严格比较；缺失字段、非法shape、错run标签仍失败。按完整已枚举tally路径注册，禁止`*FOM*`/整个StatisticsTester对象跳过。

| 内存字段 | 真实依赖/当前位置 | HDF对应（相对具体诊断bin的Path） |
|---|---|---|
| `p_vTime` | 非零得分history的dSimTime累计；ProcessStatisticsBin.cpp:16/43 | 无直接输出 |
| `p_vLargestTime` | 最大得分history的时间；StatisticsFunc.cpp:96–100 | 无直接输出 |
| `p_vFoMPerCycle` | batch时间；StatisticsFunc.cpp:177–180 | `/Batches_of_FOM`（OutputTallyh5.cpp:283） |
| `p_vFoMTot` | 进程OTimer[Total]；StatisticsFunc.cpp:124–125 | `/FOM`（OutputTallyh5.cpp:217） |
| `p_vFlucFOM` | 进程Total + largestTime；StatisticsFunc.cpp:184/218 | `/Fluctuated_FOM`（OutputTallyh5.cpp:261） |
| `p_vFoMValueCheck`、`p_vFoMBehaviourCheck` | batch FOM检查；StatisticsFunc.cpp:331–358 | `/TenStatisticsChecks/FoMValueCheck`、`/TenStatisticsChecks/FoMBehaviourCheck`（OutputTallyh5.cpp:210–211） |
| Particle的`p_dSimulateTime` | history interval；CalcFixedSource.cpp:247 | 无直接对应统计HDF字段 |

因此HDF统计例外是以上**五个确切后缀**，不是整个统计dataset集合。StatisticsTester的Sum1–4、Nps/NonZero/Stored/CurrentBatch、Ave/RE/VoV、ZeroRe/NonZeroRe、PDF数据/slope、largest score、mean/shift/fluctuation的非FOM量以及其余八个诊断必须严格比较。特定空bin的既有NaN/Inf按同一已记录未定义类别匹配，有限物理值保持bitwise零容差；不能用时间例外隐藏某侧才出现的非法统计值。旧FOM未定义情况同样记录原因，不填epsilon。

- 每个run开始时reset后的七个统计时间/FOM成员必须为原定义零状态；过程history时间有限非负，shape匹配本N/check定义。FOM有效域按原公式分母/RE判定，不拿“时间例外”接受随机NaN/Inf或越界。G2至少一个有效统计bin用于验证公式依赖与标签，旧p_vFoMTot/p_vFlucFOM保留且标为进程相关，batch时间/FOM标为非零history口径，均不是本轮T_MC。
- receipt三段均有限非负，`timingScope=prepare+transport+finalize`，`statisticsTimingScope=legacy_mixed_not_per_run`、`statisticsFomIsRunMetric=false`。`mcSeconds`须与receipt三个double按同顺序相加的值bitwise相等；与独立保存steady-clock t3−t0的差≤`8*epsilon(double)*max(1,abs(t3−t0))`秒（仅舍入检验，绝非输运容差），不要求fresh/persistent耗时相等。GDB观察时间不作性能结论。
- 在启用SCHECK的FF两次Run之间，driver用steady_clock记录约100ms显式间隔（在下一t0之前）。核实Total仍连续、无reset/stop；下一run的t0/t1/t2/t3均在间隔之后，T_MC仅来自该四点。不能用旧Total或旧Time差替代这三个receipt字段。Finalize计时包含必要终检及停止run timer；Initialize、读取输入/spec/WW文件、snapshot写出不纳入。
- 比较器自测只修改**任务私有快照副本**：以上时间字段变化应报告允许差异；RE、Sum3、PDF、largest score、MeanBehaviourCheck/VoV检查各单独改变应非零退出；增加未知字段/删除字段也失败。测试不修改生产状态/reference。时间标签若漏写、旧FOM被冒充run指标，也失败。

## 4. 命令、证据与停止

以下是批准后要执行的命令模板，未运行。RUN_ROOT必须不存在，wrapper为每条命令保存cwd/环境/argv/stdout/stderr/exitcode。

~~~bash
F11_STAGE2_ROOT=/tmp/20261011_05_f11-prepared-run-lifecycle
F11_STAGE2_TASK=/home/workspace/AI_MC_WW_interation/MLVR_develop/2026-10/20261011_05_f11-prepared-run-lifecycle
F11_STAGE2_DB=/home/silver/NucXS_Library/RMC_DATA
mkdir -p "$F11_STAGE2_ROOT/baseline-src"
rsync -a --exclude=.git /home/workspace/AI_MC_WW_interation/RMC/ "$F11_STAGE2_ROOT/baseline-src/"
printf '%s\n' 330f091eb0296e0d0124237ba7d9a22b81aee852 > "$F11_STAGE2_ROOT/baseline-src/delivery/GITSHA"
cmake -S "$F11_STAGE2_ROOT/baseline-src" -B "$F11_STAGE2_ROOT/baseline-build" \
  -Dmpi=OFF -Dopenmp=OFF -Dloadmodules=ON -Dtest=ON \
  -Dmpiproc=1 -Dompthrd=1 -Dais=OFF -Dpythonapi=OFF -Dpersonal=OFF \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build "$F11_STAGE2_ROOT/baseline-build" -j 8
env -u RMC_MPI_TEST -u RMC_OMP_TEST RMC_DATA_PATH="$F11_STAGE2_DB" \
  RMC_PATH="$F11_STAGE2_ROOT/baseline-build/bin" OMP_NUM_THREADS=1 \
  ctest --test-dir "$F11_STAGE2_ROOT/baseline-build" --output-on-failure \
  -R '^test_(fixed_source_1|fixed_source_4|fixed_source_adjoint|var_reduce_wwmesh_n|fixed_source_photon|fixed_source_electron|fixed_source_photon_and_electron|fixed_source_neutron_and_photon_and_electron|RestartFixRead)$'
# Stage1 tools/run_cases.py、diagnose.py、capture_existing.py、compare.py
# 复用或复制适配到本任务，先检查其实际CLI，冻结baseline后才改生产树。
# 新stage2-src/stage2-build私有副本用同样configure/flags构建。
cmake --build "$F11_STAGE2_ROOT/stage2-build" --target RMC RMCPreparedLifecycle -j 8
# G0: configure同时保存source列表；测试target生成链接map，比较compile_commands及symbols。
nm -C --defined-only "$F11_STAGE2_ROOT/stage2-build/bin/RMC" > "$F11_STAGE2_TASK/logs/rmc-symbols.txt"
nm -C --defined-only "$F11_STAGE2_ROOT/stage2-build/bin/RMCPreparedLifecycle" > "$F11_STAGE2_TASK/logs/prepared-symbols.txt"
python3 "$F11_STAGE2_TASK/tools/check_prepared_linkage.py" \
  --build "$F11_STAGE2_ROOT/stage2-build" --manifest "$F11_STAGE2_TASK/logs/planned-linkage.json"
"$F11_STAGE2_ROOT/stage2-build/bin/RMCPreparedLifecycle" --mode source-weight-audit-selftest
"$F11_STAGE2_ROOT/stage2-build/bin/RMCPreparedLifecycle" \
  --mode persistent --input "$F11_STAGE2_TASK/inputs/model.inp" \
  --plan "$F11_STAGE2_TASK/inputs/faf.tsv" --data "$F11_STAGE2_DB" \
  --snapshot-dir "$F11_STAGE2_ROOT/persistent/faf"
gdb -q -batch -x "$F11_STAGE2_TASK/tools/trace_lifecycle.gdb" --args \
  "$F11_STAGE2_ROOT/stage2-build/bin/RMCPreparedLifecycle" \
  --mode fresh --input "$F11_STAGE2_TASK/inputs/fresh/faf-a.inp" \
  --effective-seed 2131104056799056913 --stride 100000 \
  --data "$F11_STAGE2_DB" --snapshot-dir "$F11_STAGE2_ROOT/fresh/faf-a"
python3 "$F11_STAGE2_TASK/tools/compare_lifecycle.py" \
  --persistent "$F11_STAGE2_ROOT/persistent" --fresh "$F11_STAGE2_ROOT/fresh" \
  --manifest "$F11_STAGE2_TASK/logs/planned-comparison.json"
~~~

driver/inputs/compare_lifecycle.py/check_prepared_linkage.py及两个manifest将在批准后的实施步骤创建，命令中的接口按本方案定义。不能把本段当实际执行证据。fresh模式走正常RunCalculation，只设置准确RNG参数，不调用新Prepare；完整内存数据由只读GDB在其实际工作副本栈帧仍有效时抓取（不能返回后读取main的Tally副本）。观察器配置的输出目录与snapshot-dir一致。必要只读GDB观察命令仍为gdb -q -batch -x task-owned-trace.gdb --args binary…；记录真实传入ORNG，不误读global同名对象。

批准后产物：logs/baseline-freeze.json，各build/ctest/run/negative/compare command与exit/stdout/stderr，所有输入及spec TSV，每run receipt、source/derived/RNG/bank/tally/WW snapshots、原始full序列lossless gzip及hash；binary/构建目录在/tmp，通过manifest绑定。不会把单文件>10MB未确认写入档案。

G0附加命令：在同一私有源码另以`-Dtest=OFF`配置确认target缺席并构建普通RMC；MPI/OMP/AIS/Python配置只按既有依赖可用性检查target注册条件，依赖缺失如实写未覆盖，不安装/改库绕过。根CMake源码门禁和serial实际链接必做；不得由条件分支审查声称对应并行输运已通过。G7a逐负例运行同一`--mode persistent --input ... --plan ...`入口并保存预期非零退出与失败阶段；G7b使用上述selftest命令，selftest自身退出0仅表示预期拒绝均发生，逐子项的异常/退出独立记录。

结束判定区分“编译成功/运行结束/确定性等价”。实现或门禁未完成为BLOCKED（说明具体原因）；全受限门禁通过但非零裂变/并行等未支持为ACCEPT WITH LIMITATIONS；不把限制外项写Ready。完成Stage2立即停止，不自动进入Stage3，不commit/push。
