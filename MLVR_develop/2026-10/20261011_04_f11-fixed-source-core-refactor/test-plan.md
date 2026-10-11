# 阶段1基线与回归计划（事前，未执行）

## 当前环境与执行关口

当前RMC HEAD=c3ef093497ea42c54569a87ed3696642c8b42931，工作树干净；相对本地upstream=0 ahead/0 behind，无本地未推送提交。GCC13.3.0、CMake/CTest3.28.3、Python3.12.3、HDF51.10.10、PyYAML可用；h5dump和mpicxx存在，系统Python无h5py/numpy（不安装、不假称可用）。详见logs/repository-state.json、test-environment.json及版本原始输出。

现有/tmp/f11-volume-rmc-build-snapshot为5cfb.../RelWithDebInfo/-O2 -g/MPI-off/OMP-off/test-off的阶段0构建，**不是当前HEAD的fresh baseline**，不作为本阶段对照binary。该缓存/flags只作环境调查保存。

**待审批后执行**：先复核同一HEAD且生产树无冲突→保留未修改源快照并fresh configure/build/run→冻结baseline证据/输入/核数据/实际flags→才应用两文件生产补丁→独立目录fresh configure/build/run→确定性比对与既有CTest→按实际结果归档。当前没有构建/输运/CTest结果。

## 用例与覆盖

| 用例 | 原始输入/历史/种子 | 验证 |
|---|---|---|
| MG neutron analog | inputs/mg-neutron-analog.inp，5000，Type2/seed17/stride100000 | 普通源、材料MGACE、mesh/cell的Ave/RE、N/分母、实际RNG状态/轨迹 |
| MG native track WW | inputs/mg-neutron-native-ww.inp，同上，native WWMESH/WWP，无WWG | 下界0.1/1.0交替；必须实际观察splitting和roulette，各自事件数>0，否则覆盖不足；后代流/统计完全相同 |
| MG neutron adjoint | inputs/mg-neutron-adjoint.inp，同上，ADJOINT原卡 | 伴随Ace/Particle标志、群截止、统计和分母完全相同；不作互易性或多次切换结论 |
| Ordinary CE neutron | 既有test_fixed_source_1，原输入1000，Type2/seed1/stride100000 | CE/TMS既有兼容路径，原CTest通过及baseline字节对照 |
| pure Photon | 既有test_fixed_source_photon，原输入100000 | P分支、电子辅助链、原CTest及确定性对照 |
| pure Electron | 既有test_fixed_source_electron，原输入10000 | E分支及原CTest/对照 |
| Photon+Electron | 既有test_fixed_source_photon_and_electron，原输入2000 | PE分支及原CTest/对照 |
| Neutron+Photon+Electron | 既有test_fixed_source_neutron_and_photon_and_electron，原输入2000 | NPE与后代链，原CTest/对照 |
| Neutron+Photon | inputs/np-representative.inp，2000，Type2/seed17/stride100000 | 从NPE既有输入复制，仅ParticleMode N P、显式RNG；补足NP实际分支，普通结束语义 |
| 既有MG/WW测试 | test_fixed_source_adjoint（原1M）、test_var_reduce_wwmesh_n（原100k） | 既有reference不变、CTest通过；不能替代前面的确定性比较 |
| 多batch及接续 | inputs/mg-neutron-batch.inp（5000、interval=1000）、既有test_RestartFixRead及test_fixed_source_4 | 前者要求5个batch并记录接续写出；接续测试覆盖ReadBinary，fixed_source_4保留复杂普通源回归 |

接续测试须原样复制其inp_binary并先确认baseline可运行；缺项记录限制，不造reference。无RNG卡的现有输入保持原样，默认CDRNG rngLCG63_0、seed1/stride100000（RNG.h:415–416与52–55），真实有效种子/位置仍从实际传入对象记录。

本任务新输入只在任务目录，尚未验证解析/运行；配置快照见inputs及logs/planned-inputs.json。没有AIMC训练，src/config.py dataclass、CUDA/PyTorch不适用。不使用阶段0真空例替代本阶段有碰撞/WW/伴随验证。

## 事前验收标准

1. 相同输入（SHA256）、核数据库、种子/有效RNG段、编译器/优化/宏和进程数；逐例退出码=0，实际源数/finish/batch计数/归一化分母完全相等。
2. 原`.Tally`逐字节相等，所有Ave/RE/空bin/群/Tot不作统计容差。对最终内存Score/ScoreTemp/Sum1/Sum2/Ave/RE采用IEEE值完全相等的检查，避免只验证打印精度掩盖改变。单源历史得分/后代处理顺序不得改变。
3. 在小诊断副本（前三MG输入只把N改500，baseline/refactor相同）用只读GDB抓SampleFixSource进入前的真实传入ORNG、每history/后代源状态/终态、统计结束及WW事件。禁止friend、token、跳过初始化或写入进程状态；这些断点只验证普通完整路径，生产函数仍全部正常调用。记录RNG类型、RN_SEED/RN_SEED0/RN_STRIDE/RN_POSITION/RN_POSITION_PRE；不误读全局同名ORNG。整序列/终态必须一致。
4. WW诊断在DoMeshWeightWindow.cpp低于下界与高于上界分支、SaveSplitParticles的bank操作读取状态/事件，split与roulette触发数必须>0，且baseline/refactor事件、bank-drain顺序和结果完全相同。只输入WW卡、或只看最终tally相同不足以确认覆盖。
5. 每进程完整InitiateAll调用1次、最终ProcessTally固定源重载1次、registry登记不增加、源工作副本不新增外泄。模型初始化后所有owner地址关系有效。core内不能含初始化、ProcessTally或进程级收尾。
6. HDF5不比较文件二进制（构建/时间等元数据会变）。使用h5dump比较物理数值dataset及形状；预先列出确切非物理时间/path字段后只排除这些字段，不能忽略整个结果文件或笼统删除浮点数据。
7. 普通stdout/.out输出结构、顺序、warnings/missing、source number、碰撞计数、面源/微扰/WWG/接续物理内容保持。唯一允许变动：明确的构建时间、墙钟日期/耗时、颗粒吞吐率、包含时间因子的FOM以及测试目录路径。先列字段白名单，不对其余physics做容差。timer reg/start/interval/stop调用顺序和覆盖范围必须原样，新增函数调用不会使实际耗时精确一致。
8. 既有CTest遵从其原reference比较器；**额外**执行baseline/refactor确定性比对，不用CTest的既有数值容差替代本任务精确回归。严禁execute.py的-u/--update；禁止新写既有reference。
9. 两生产文件之外没有修改；执行体保持原623行token/语句顺序和六模式分支。只一个ExecuteFixedSourcePrepared实现、一套原分支/循环body，不是硬把六粒子分支压成一个for。

## 审批后执行命令

下列是待执行命令，不是成功记录。所有步骤用任务runner保存完整命令、cwd、stdout/stderr/exitcode、版本/manifest；runs及二进制放/tmp，不入logs。

```bash
TASK=/home/workspace/AI_MC_WW_interation/MLVR_develop/2026-10/20261011_04_f11-fixed-source-core-refactor
RMC_BASE_HEAD=c3ef093497ea42c54569a87ed3696642c8b42931
F11_RUN_ROOT=/tmp/20261011_04_f11-fixed-source-core-refactor
RMC_DB=/home/silver/NucXS_Library/RMC_DATA
# 必须先核验HEAD和工作树；发现新冲突先停止，不覆盖现有目录。
mkdir -p "$F11_RUN_ROOT/baseline-src"
rsync -a --exclude=.git /home/workspace/AI_MC_WW_interation/RMC/ "$F11_RUN_ROOT/baseline-src/"
# 只在私有副本填写真实HEAD的构建元数据；不改变任何生产源文件。
printf '%s\n' "$RMC_BASE_HEAD" > "$F11_RUN_ROOT/baseline-src/delivery/GITSHA"
cmake -S "$F11_RUN_ROOT/baseline-src" -B "$F11_RUN_ROOT/baseline-build"   -Dmpi=OFF -Dopenmp=OFF -Dloadmodules=ON -Dtest=ON   -Dmpiproc=1 -Dompthrd=1 -Dais=OFF -Dpythonapi=OFF -Dpersonal=OFF   -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build "$F11_RUN_ROOT/baseline-build" -j 8
# 每个新输入在新的独立cwd执行；stdout/stderr/退出码保存，不能吞失败。
for CASE_NAME in mg-neutron-analog mg-neutron-native-ww mg-neutron-adjoint mg-neutron-batch np-representative; do
  CASE_DIR="$F11_RUN_ROOT/baseline-runs/$CASE_NAME"
  mkdir -p "$CASE_DIR"
  cp "$TASK/inputs/$CASE_NAME.inp" "$CASE_DIR/inp"
  ( cd "$CASE_DIR" && "$F11_RUN_ROOT/baseline-build/bin/RMC" -i inp -d "$RMC_DB" )
done
# 新用例及原测试全按计划执行，先冻结baseline。
env -u RMC_MPI_TEST -u RMC_OMP_TEST RMC_DATA_PATH="$RMC_DB"   RMC_PATH="$F11_RUN_ROOT/baseline-build/bin" OMP_NUM_THREADS=1   ctest --test-dir "$F11_RUN_ROOT/baseline-build" --output-on-failure   -R '^test_(fixed_source_1|fixed_source_4|fixed_source_adjoint|var_reduce_wwmesh_n|fixed_source_photon|fixed_source_electron|fixed_source_photon_and_electron|fixed_source_neutron_and_photon_and_electron|RestartFixRead)$'
# baseline全部完成并确认后，才可应用已批准提案。
# 独立refactor-src/refactor-build使用同样configure与物理输入；保存实际changes.diff和源hash。
# 相同new-input执行命令换为refactor-build/bin/RMC，同一ctest命令换目录。
```

严禁直接向生产RMC执行带loadmodules的CMake：其get_submodule可能更新依赖。无.git私有副本使用已存在的vendored依赖；submodule操作警告原样记录，若无法构建则停下分析，不能擅自修改生产构建源码。baseline与新构建的delivery/GITSHA仅为私有构建身份；修改后的binary必须另绑定changes.diff及工作树源hash，不能仅凭同HEAD的banner宣称代码相同。

数据比较命令：`cmp baseline/inp.Tally refactor/inp.Tally`；HDF5先`h5dump -n <file>`列路径，按明确的物理dataset做`h5dump -y -w 0 -d <exact_dataset> <file>`并比较原始数值转储；诊断GDB命令`gdb -q -batch -x <task-owned-readonly-trace.gdb> --args <exe> -i inp -d "$RMC_DB"`。具体runner/比较/trace脚本实施时存任务tools下并保存命令/输出；不改生产调试宏，当前没有伪造这些未执行脚本的结果。

MPI条件分支编译检查：baseline与refactor各再建MPI=ON/OpenMP=ON/test=OFF的独立目录，其他参数一致（mpicxx已存在）；不借MPI编译成功宣称MPI数值回归。F11首版严格MPI/OMP-off。TIME_REDUCE/墙钟stop-time、Python源插件、MCNP共享WW、WWG、统计诊断等复杂可选运行未列完整矩阵：保留原代码并记录未覆盖，不因结构重构把它们提升Ready。时间截止改变实际N可能取决于调度；不把这类用例伪装成确定性fixed-N对照。

## 失败与停止规则

baseline编译/输入/核数据/原reference失败先保留原始证据，不能在新源码中顺带修复或更新参考来掩盖。baseline与新版本任何确定性差异、registry错误、ProcessTally重复或实际WW覆盖缺失都不得ACCEPT；定位差异并按授权范围修正重构，超范围修改先停下说明。验收区分编译成功、运行正常、数值一致三种结论。当前全部为计划，未运行。
