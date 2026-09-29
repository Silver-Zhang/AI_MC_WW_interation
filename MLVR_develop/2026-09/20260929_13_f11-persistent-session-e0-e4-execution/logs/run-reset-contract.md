# F11 task-private run preparation contract v1

本合同在任何数值运行之前写定。继承 Task 11 的 N/seed/source/WW/阈值；用户 Task 13 已批准实现与执行。代码为 `verification/harness/driver_main.cpp`（`driver_body.inc` 是生成片段），调用原 `CalcFixedSource`，不复制 history loop。

## 1. Scope / entry / CLEAR

第一次从原 main 的 CheckIOFile→OutputHeading→ReadInputBlocks→RunPlot→GenerateInpFile 路径解析一次，随后直接调用原 CalcFixedSource 完整 Init。第二轮起，执行以下操作，snapshot 后 arm，再进入同一个函数并消费一次 token。

| 实际对象 / field / function | 逐轮操作 |
|---|---|
| `CDFixedSource.p_nFinishCalculate` | SET -1 |
| `p_llCurParNumEachPro,p_llCurTotParNum,p_llCurrentBatch,p_llCurrentPARTICLE` | CLEAR 0 |
| `p_llParNumRestart,p_llParticlePosEachPro,p_llParIntervalEachPro` | CLEAR 0；禁止 restart |
| `p_llUserInputParNum`、`CheckFixedSource()` | SET 本轮 N；原函数重设 p_llParNumToInputInterval 和 p_llTimeParInterval |
| `p_dTotStartWgt,p_dTotStartWgtOrigin` | CLEAR 0；正常 PrcoessBatchEnd 再计算 denominator，不手工写最终 N |
| `p_nFixedSrcCount,p_nFixedSrcBankCount,p_nPhotonBankCount,p_nElectronBankCount,p_nMissParCount` | CLEAR 0 |
| `p_llTotCollisionCount,p_llTotGammaColliCount,p_llTotElectronColliCount,p_dTotInducedGammaCount` | CLEAR 0 |
| `p_vFixedParticleSrcBank[*].ParticleBank` | CLEAR（包含旧 neutron sentinel）；原 CalcFixedSource 为新轮 push sentinel |
| `p_vFixedSrc,p_vFixedSrcBank,p_vPhotonBank,p_vElectronBank` | CLEAR；`InitiateTrspt` 按入口状态重新准备 storage |
| `p_vSpontaFissNeuMul,p_vInduceFissNeuMul,p_vSpontaFissPhoMul,p_vInduceFissPhoMul,p_sNextParticle` | 保持 shape，元素归零 |
| `CDNeutronTransport.p_nMissParticleCount,p_nMissNeutronCount` | CLEAR 0 |
| `CDExternalSource.p_vFixedInitSrcBank,p_vFixedInitPhoSrcBank` | CLEAR；相应 p_nFixedInit*Count=0 |
| `CDExternalSource.p_vSpontaFissNeuMul,p_vSpontaFissPhoMul` | 元素归零；单源组件定义保留 |
| `CDTally.p_pTallyDataPointer[*]->SetZero()` | 清 Score/ScoreTemp/Sum1/Sum2/Ave/RE；p_vSum3 元素归零 |
| `p_setScoreIndex,p_vScoreIndex2,p_vScoreStride` | CLEAR；不只调用 SetZero |
| `CDStatisticsTester.p_vGatherScores` | CLEAR |
| `CDStatisticsTester.ReSize(N)` | 仅 SCHECK 开启时调用；其原函数归零 moments/历史计数/批次/临时分数/时间/FOM/check arrays，重设 N/20；不调用 SetStatisticsIndex，原索引不追加 |
| `Utility::OTimer` | 赋新 RMCTimer，清整个 timer map；OutputHeading 开始新的 Total timer |
| `Output.p_nWarningCount,p_nErrorCount` | CLEAR；输出 warning 重新来自本轮路径 |

SCHECK=0 时 tester 保持原空状态，不能用 ReSize 引入原 fresh 不存在的 pdf 工作数组。源对象在生产 CalcFixedSource 内按值复制；observer 保存其实际局部定义与临时 bank，driver 改的是下一次复制所用的外部源定义。

## 2. SET

- `run_id`：sequence manifest 的唯一名；P0.set_run 清上一轮的观察缓冲，累计 Init/XS 调用次数保留。
- `p_llUserInputParNum=N`；N/seed 与 Task 11 一致，stride=1000000。
- `CDExternalSource.p_vSource[0].p_vPoints={x,0,0}`；source energy=2 MeV、particle=1、weight=1、fraction=1；其它冻结定义保持。按 phase snapshot 记录输入归一化后的 fraction/bias arrays。
- RNG：`ResetRNGType(rngLCG63_0)`，`SetSeed0(seed)`、`SetStride(1000000)`、`SetPosition(0)`、`SetPositionPre(-1000)`。新 generator 的 current seed 为构造初值1，与原 input parser 只改 Seed0 的 fresh 行为一致；首 history 的 GetRandSeed 强制重新计算函数 static skip cache。P0 不调用 RNG 抽样。
- WW identity：使用固定2×30网格、相同 energy bins 和 WWP=(5,3,5)。lower 为 `ldexp(1,-1-i-g%2)/(WW2?4:1)`。通过原 `ProcessWeightWindow` 写三种 bounds，保留定义。

## 3. REBUILD

- `CDFixedSource.p_bIsAdjoint` 与 `CDAceData.p_bIsAdjoint` 每轮明确 SET bool。
- 所有真实核素 `p_vAdjointCrossSection` 与 `p_vAdjointFissionCrossSection` CLEAR；记录 `mode_zero_base`。A 才调用原 `treatAdjointMaterial`，由 raw XSS 重建；F 保留空派生表，与 fresh F 一致。H2O 只能覆盖 fission 派生表的零态。
- 物理 cutoff 从冻结输入另行保存：A 30 MeV，F 默认20 MeV（不激活）。A 的 `p_dMaxAdjointNeutronEnergy=LocateMgErgGrp(30,Neutron)`，photon 保持30但不执行；F 恢复20/20。禁止拿旧 internal cutoff 当 MeV 再转换。
- `CDParticleState` 在原地址析构/重新构造（不浅拷贝旧缓存）；重设 role；按原 InitiateAll 的串行 neutron 分支重新设置四种 energyCutoff、nearest particle/Poisson arrays、realDisplace、`SetupMatNucFrc`；新建 p_vONucCs，并把 p_vIsNucLocCellTmpChanged 设为 true。
- `InitiateTrspt` 只作为上述明确清理后的局部准备；不调用 InitiateAll/InitiateMatAce/ReadAceData/InitiateTally；`p_bIsPerHstry=true,p_bIsPerCyc=false`。
- WW 通过原 `ProcessWeightWindow` 同时更新 lower、5×lower upper、3×lower survival。

**预先声明的 phase 差异**：fresh A 在第一次 SampleFixSource 才将 particle adjoint 设 true；prepared A 在 arm 前就设 true。比较 pre-transport state 时承认这一赋值时点差异，只允许 fresh-A false→prepared-A true；有效输运与最终 snapshot 三层角色必须全部匹配 A。F 没有这一例外。该例外在运行前定义，不能扩展到 XS/cache/输出不一致。

## 4. KEEP / identity

保持 geometry/material/nuclide owners，raw XSS、几何 surface/type/bounds/cell material/fill 拓扑、材料密度/核素表、tally mesh/offset/group definition、WW mesh/energy/WWP。snapshot 同时记录已定义字段的内容/hash 与 owner/address。原始 source 复制的地址不作为复用条件；比较其实际定义。tally owner 和数值 storage 保留，不能重新 InitTally 冒充 reset。

## 5. Output lifecycle

每轮原 OutputEnding 关闭本 scope 实际打开的 FILE*。下一轮将 output/tally/material/cyc/fission-multiplicity FILE* 置 nullptr；删除并清空旧 Result/Info/State HDF5 wrappers，以独立 `inp_<run_id>` 文件名再调用 CheckIOFile/OutputHeading/OpenFilePtrs。不再次 ReadInputBlocks。日志主 logger 为整个 process，stdout 含有所有轮；每轮 `.out/.Tally` 和默认 RMC HDF5 sidecars 独立。HDF5 sidecars 是原 RMC 行为，不是新 Field API。输出跨轮错误归 OUTPUT/session issue，不能只看 tally 判断成功。

## 6. Armed token / hard fail

`RMC_F11_REUSE_EXPERIMENT` 默认关闭。test driver 必须 set_run 后才能 arm；已有未消费 token、非MG30、N≤100、finish/counters不清零、粒子bank不空、三层role不一致、registry不唯一/不自指、六组tally不为零、touched不空、RNG位置/stride不符或非单位单源，均 exit=90，保存 hard-fail 和已有缓冲。token 一次消费；第一次未 armed，仍完整 Init。

`CalMode.h` 在 `RMC_F11_DRIVER_ACCESS` 下仅给 task driver friend 访问，不改变布局/生产签名/计算逻辑。baseline P0-disabled driver 也需要此访问以在返回后只读 moments/RNG；不启用 P1 序列。

## 7. Comparison and failure policy

- fresh driver vs CLI 的原 loop 单次执行：至少 F，另包含 A；两者都采集 P0 内部 snapshot。
- observer non-interference：P0-off driver 和 P0-on driver 的返回点全状态/moments/RNG identity 及 `.Tally` exact；另比 CLI。P0-off 无 per-history 插桩，因此只主张其端点 RNG identity，不伪造未插桩逐history trace。P0-on 的完整 history seed trace 在 fresh/sequence 间 exact。
- all62 tally slots（60组+2 Tot）、moments 和 binary64 数值 exact；时间/FOM/checks 中明确依赖时间者保留原值但不做 exact physics gate。response diagnostic 定义为左空间 bin 的 Tot；不是正式 ResponseDefinition。
- fresh A 的角色时点例外仅限上节；模型内容、active role、cutoff、derived tables、cache、banks和归一化须满足约定。
- E3 全部 transport lookup 原始 TSV 保存；完整有序事件 exact，并确认 source-energy physical group 在两个 spatial bins 均被访问；不足则 INCONCLUSIVE。
- E4 left-flux fraction 差>0.10；field为2×30，Tot另列；31边界必须从实际 loaded memory 导出（fixture离线边界仅用于生成输入）。memory/text采用原4位科学计数格式比较。
- E0计时/波动/开销阈值继承Task11：7次、closure≤max(1μs,total×1e-6)、CV≤10%、startup fraction std≤0.05、mean overhead≤5%。warm cache，无cold主张。编译完成后才运行计时。
- harness baseline 不成立 → HARNESS INVALID，停止全部；已声明 lifecycle 合同下实验不成立 → 保留 first divergence，不修改 production 或追加 reset；继续逻辑独立实验。

## 8. E0 metadata completion (v2, before final E0)

见 endpoint-metadata-amendment.md：两种CLI在calculation返回后增加相同的只读标量collector，输出每run实际N/completed/denominator/weight/probabilities/RNG；计入finalize/output。内部P0/P1-off与on共用该外部采集步骤。未改任何CLEAR/SET/REBUILD/KEEP、物理比较容差或性能门槛。V1 E0保留作初步记录，最终性能使用独立v2的1+7样本。E1–E4使用已封存v1二进制及原合同，不需重跑。
