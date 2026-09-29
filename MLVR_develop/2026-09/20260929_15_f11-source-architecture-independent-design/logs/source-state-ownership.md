# State ownership / reset contract

基线同源码报告。表中动作是由当前源码与 Task 13/14 推导的生产入口契约，**不是当前已有完整 reset API**。B=Bootstrap，A/F=各 half-run。保留对象地址指实际 transport 使用的 owner，不是 main 中尚未初始化的副本。Task 13 的直接赋值、placement-new、friend 与 arm token 不作为生产接口。

| State | Owner | Lifetime | Bootstrap | A→F | F→A | Action |
|---|---|---|---|---|---|---|
| geometry / cells / geometry indices | RunCalculation 本地 CDGeometry，另有 global cellVec | 一次 RunCalculation | 初始化一次 | 保留 | 保留 | KEEP |
| material / converted density / nuc fractions | 同调用中的 CDMaterial | session | 初始化一次 | 保留 | 保留 | KEEP |
| raw MGACE XSS/JXS / group structure | main CDAceData 引用 / p_vNuclides | session | 读取、检查一次 | 保留 | 保留 | KEEP |
| adjoint total/scatter / fission derived arrays | CDAceData::p_vNuclides 的两组 adjoint vectors | mode generation | 清空 | 全清，保持空 | 全清后 treatAdjointMaterial | CLEAR / REBUILD |
| role flags | CDFixedSource / CDAceData / CDParticleState | half-run | 三者 false | 三者 false | 三者 true | SET，双向明确赋值 |
| neutron energy / weight cutoffs | CDNeutronTransport；FixedSource adjoint cutoff | half-run | 由物理输入解析 | 从原始物理输入恢复 | 从物理上界转换一次为群号 | SET，禁止对旧群号再转换 |
| tally per-history/per-cycle mode | CDTally | half-run | per-history=true / per-cycle=false | 同左 | 同左 | SET |
| tally definitions / mesh / offsets | RunCalculation 本地 CDTally::p_vMeshTally | session | InitiateTally 一次 | 保留 | 保留 | KEEP |
| tally registry / statistics index | CDTally registry 中的 CDTallyData* / tester index | owner lifetime | 注册一次 | 保留地址和长度 | 保留地址和长度 | KEEP，禁止再注册 |
| p_vScore / ScoreTemp / Sum1 / Sum2 / Ave / Re | 每个已注册 CDTallyData | half-run | 六数组归零 | 归零 | 归零 | CLEAR |
| Sum3 / touched set / scoreIndex2 / stride | CDTallyData | half-run | 归零或 clear | 同左 | 同左 | CLEAR；SetZero 单独不够 |
| StatisticsTester sums1–4 / time / bins / previous estimates / FOM / NPS arrays | 每个启用的 CDTallyData::p_OStatisticsTester | half-run | ReSize(N)，清 gather | 同左 | 同左 | CLEAR / SET，保留 index |
| TARGET response history sum and square（拟新增） | CDTally 的一个 scalar CDTallyData | half-run | 清零，启用 F response | 清零，启用 | 清零，A 不报告物理 response | CLEAR |
| physical source definition | 输入后的 CDExternalSource definition snapshot（拟保留） | session | 保存不可变定义 | 取此定义 | 保留 | KEEP |
| target source definition（拟构造） | 第二个普通 CDExternalSource 值对象 | session | TARGET resolve 后建立 | 保留 | 取此定义 | KEEP |
| active source / mutable distributions / sampled variable state | 每个 half-run 的 CDExternalSource 工作值 | half-run | physical definition 的干净副本 | physical 的干净副本 | target 的干净副本 | SET；没有新 source type |
| external initial banks / counts / spontaneous multiplicities | active CDExternalSource | half-run | 清空 | 清空 | 清空 | CLEAR；v1 拒绝自发裂变源 |
| p_nFinishCalculate | CDFixedSource | half-run | -1 | -1 | -1 | SET |
| p_llCurParNumEachPro / CurTotParNum / CurrentBatch / CurrentPARTICLE | CDFixedSource | half-run | 0 | 0 | 0 | CLEAR |
| restart / interval / position fields | CDFixedSource | half-run | 清理后按 N 重算 | 同左 | 同左 | CLEAR / SET；v1 无 restart |
| p_llUserInputParNum and source intervals | CDFixedSource | half-run | N_B + CheckFixedSource | N_F + CheckFixedSource | N_A + CheckFixedSource | SET |
| p_dTotStartWgt / p_dTotStartWgtOrigin | CDFixedSource | half-run | 清零；batch end 得到 N | 同左 | 同左 | CLEAR / SET；只在等权假设下=N |
| fixed-source / bank / miss / photon / electron counters | CDFixedSource | half-run | 全零 | 全零 | 全零 | CLEAR |
| collision counters / induced-gamma counters / neutron miss count | CDFixedSource / CDNeutronTransport | half-run | 全零 | 全零 | 全零 | CLEAR |
| four p_vFixedParticleSrcBank stacks, other source/fission/photon/electron working banks | CDFixedSource | half-run | 全清；loop 自己 push 一个 neutron sentinel | 同左 | 同左 | CLEAR；不能积累 sentinel |
| p_vSpontaFissNeuMul / other multiplicity arrays / p_sNextParticle | CDFixedSource | half-run | 清零 | 清零 | 清零 | CLEAR |
| particle coordinates / level / alive / backup / indices / cached nucleus XS / changed flags | CDParticleState | half-run | owner 内 reset 默认瞬态后重建几何尺寸和材料缓存 | 同左 | 同左 | CLEAR / REBUILD |
| adjointAccumulatedCrossSection / p_dTempAdjointxSection | CDParticleState | half-run/material/group | 清空、0 | 清空、0 | 清空，碰撞路径重建 | CLEAR / REBUILD |
| RNG generator / seed0 / stride / position / position_pre / skip-cache trigger | 从 main 传入的 CDRNG 引用 | half-run | 设置本 run seed，position=0，pre 非连续哨兵 | 同左 | 同左 | SET；不能只 SetSeed0 |
| WW mesh / finite full physical group axis / WWP | global OWeightWindow | session | 初始化同一 topology，禁止体积归一化 track | 保留 | 保留 | KEEP |
| WW lower / survival / upper | OWeightWindow::p_vMeshInformation[neutron][mesh][group] | half-run | 不激活 | 校验 WW_F 后三者一起生成 | 校验 WW_A 后三者一起生成 | SET via ProcessWeightWindow |
| active VR mode / WW booleans / cutoff coupling | OCalMode + OWeightWindow + neutron transport | half-run | WW off / analog-compatible settings | track-mesh WW on | track-mesh WW on | SET，不能只换 lower |
| session clocks / per-run clocks | global OTimer | session + half-run | session 不重置，run 新区间 | 新区间 | 新区间 | KEEP / CLEAR 或差值 |
| warning/error/lost counts | global Output / transport owners | session + half-run | 记录基点 | 记录 run delta | 记录 run delta | KEEP session / CLEAR run view |
| text/HDF5 handles / run identity | global Output session handles；拟新增显式 run 输出局部文件 | respective scope | 唯一路径 | 新唯一路径 | 新唯一路径 | SET；禁止重复 CloseFilePtrs/CheckIOFile |

## 行号依据

- Owner/copy：`RMC/src/main.cpp:27-88`，`RMC/src/RunCalculation.cpp:6-13`。
- 初始化与 cutoff：`RMC/src/InitiateAll.cpp:125-209`；`RMC/src/InitiateTrspt.cpp:60-100`；`RMC/src/ResetTrspt.cpp:24-31`（固定源版本注释掉）。
- FixedSource fields：`RMC/src/FixedSource.h:192-214`、`RMC/src/FixedSource.h:254-329`、`RMC/src/FixedSource.h:408-423`。
- batch/denominator：`RMC/src/InitialBatchSource.cpp:94-144`、`RMC/src/InitialBatchSource.cpp:295-342`。
- XS：`RMC/src/TreatAdjointMaterial.cpp:19-60`；`RMC/src/Nuclide.h:2922-2927`；`RMC/src/SampleFreeFlyDist.cpp:56-96`。
- Particle flags/caches：`RMC/src/ParticleState.h:395-436`、`RMC/src/ParticleState.h:529-534`；`RMC/src/SampleNeutronSource.cpp:222-278`。
- Tally：`RMC/src/InitiateTally.cpp:61-69`、`RMC/src/InitiateTally.cpp:232-232`；`RMC/src/TallyData.h:26-83`；`RMC/src/TallyData.cpp:17-68`；`RMC/src/StatisticsFunc.cpp:8-94`；`RMC/src/SetStatisticsIndex.cpp:30-42`。
- RNG：`RMC/src/RNG/RNG.h:405-431`；`RMC/src/RNG/StrideRNG.cpp:85-101`。
- WW：`RMC/src/WeightWindows.cpp:45-101`；`RMC/src/DoMeshWeightWindow.cpp:21-50`。
- Output：`RMC/src/CheckIOFile.cpp:141-169`；`RMC/src/CloseFilePtrs.cpp:27-74`；`RMC/src/OutputEnding.cpp:46-83`。

## 与 Task 13/14 交叉检查

逐项对照 Task 13 `logs/run-reset-contract.md` 的 CLEAR/SET/REBUILD/KEEP。Task 14 `Independent_F11_E0_E4_Dynamic_Review.md` 的 E1/E3/E4 接受 repeated run、三边界 WW 更新与同 owner tally reset；E2 只覆盖非裂变 H2O。完整映射见上表。研究 driver 重建 ParticleState、关闭全局输出文件、复位所有 timer 是实现手段；生产需要 owner 方法与显式输出作用域。pre-arm 的 fresh A particle flag=false 与 prepared A=true 是阶段差异；第一条 history 开始前生产入口统一检查三层 role。

未覆盖：本轮没有重新运行 E0–E4，没有生产 reset 实现或新的动态结果，未证明 MPI/OMP、任意源权重、裂变伴随。
