# independent-f07-field-re-review

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-27 |
| 状态 | 已完成 |
| 任务类型 | 独立统计审查 / F07 field RE |
| 任务模式 | C — 深度物理研究与学习 |
| 关联知识库条目 | F07 |
| RMC revision | `5cfb0f771d0c5a2127c90d57e51ce672a4e3b616` |
| 报告 | [Independent-F07-Field-Statistical-Uncertainty-Review.md](Independent-F07-Field-Statistical-Uncertainty-Review.md) |

## 1. 目标与范围

独立审查 fixed-source neutron field 的每个 spatial×energy bin RE 是否是 history-level tally mean 的统计不确定度。范围仅为 standard MGACE、Cartesian Type=1 track-length mesh、`Energy=-1`、`Normalize=1`、serial text，含 forward、adjoint 的统计机制和 native track-mesh WW bank correlation。

不修改 RMC，不审核 F08/F09/F10，不设计 Field 数据结构。

> **模式 C 物理解释**：RE 只有在每个独立 source history 的全 family 贡献先合并、再计算 mean 的 sample variance 时，才可解释为 field mean 的相对标准误差。WW split daughters 不能成为独立样本。

## 2. 做法与证据

### 独立性

先只审 current RMC source/docs/tests 和 fresh runtime，保存 `logs/pre-developer-claim-conclusion.md`；之后才读取 F07 developer archive 比较。RMC source tree clean，未修改任何 RMC 文件。

### 关键证据

- score/history: `ScoreMeshTally.cpp:60-118`, `CalcFixedSource.cpp:167-203`, `SumUpTally.cpp:112-133`
- moments/formula: `TallyData.cpp:43-100`, `ProcessTally.cpp:360-394`
- WW bank: `SaveSplitParticles.cpp:16-49`, `SampleNeutronSource.cpp:285-328`
- output: `SingleTally.cpp:939-1004`

### 运行证据

独立 MPI-off/OpenMP-off build。fresh matrix 为 5 seed N scaling（2,500/10,000/40,000）、10 seed analog empirical scatter、10 seed WW-on PTRAC empirical scatter、Normalize 0/1 和 unreachable zero-score bin。

主要结果：

```text
N scaling RE ratios: 1.97473 and 1.99319
Analog M=10: Q=0.84927
WW-on M=10 (PTRAC-active): Q=0.88769
Normalize raw/norm: approximately 200,000 cm3; RE differences=0
zero-score: Ave=0, RE=0 (placeholder, not confidence)
```

原始/汇总证据保留于 `logs/f07-matrix-results.json`、`logs/ww-calibration-results.json`、`logs/ww-ptrac-events.json`、`logs/matrix-tallies/` 和 `logs/ww-ptrac-seed101.txt`。

### 未覆盖

非单位/不等源权重、MPI/OpenMP、restart、CE/coupled、其他 estimator、极端 cancellation、所有 field bins 的经验校准及 downstream zero-score policy。

## 3. 决策记录

- **决定**：用户批准独立只读 F07 审查、任务目录内 build/run/log/report；不改 RE 算法、zero-score、RMC source/reference/benchmark。
- **决定人 / 日期**：用户 / 2026-09-27。
- **约束**：不开始 F08/F09/F10，不建立 Field class，不把 RE=0 改为 validity mask。

**变更卡**：
| 风险 | 范围 | 验证与停止条件 | 回滚 |
|---|---|---|---|
| split descendants 被错作独立样本或 RE 尺度不对 | 只读 source/bank/tally；任务内 N scaling/scatter/WW test | 必须追溯 bank drain→history sum；WW 必须 PTRAC 证明激活；未覆盖项保留 C | 删除 task-generated build/runs；RMC 无回滚 |

> **人类理解确认**：用户要求 RE 的独立统计单位、WW correlation、zero/rare score 和经验误差尺度被独立检查，而非只看程序输出一个 RE。

## 4. 结论与边界

- **结论**：**C — Verify**。在相同源权重的 standard MGACE fixed-source neutron Type=1 Cartesian `Energy=-1` `Normalize=1` serial text 子域，per-bin RE 是 source-family history mean 的相对标准误差；native WW descendants 会在一次 `SumUpTally` 前合并。
- **不能推出什么**：`RE=0` 不代表高置信；不外推到 unequal source weights、MPI/OpenMP、CE/coupled、其他 tally、所有 WW/rare bins；未宣称 A。
- **遗留 / 下一步**：单独决定 downstream zero-score invalid policy；若需要扩大范围，先审 non-unit sources/parallel 与 RE numerical stability。
- **提交状态**：RMC 未修改、无 commit/push；档案与整理后证据（`matrix-tallies/`、`matrix-summaries/`、汇总 JSON）随 2026-09-27 根工作区提交入库；`logs/ww-ptrac-seed101.txt`（7.6 MB PTRAC 原件）按体积规范不入库、仅保留本地。

> **结果解释**：N scaling、analog/WW independent-run scatter 与 Normalize invariance 支持当前 RE 的 source-history uncertainty scale。zero-score guard、weighted source 语义和无 cancellation clamp 是继续保持 C 的原因。

## 5. 过程记录

| 时间 | 操作 |
|---|---|
| 2026-09-27 | 建立 independent Mode-C F07 档案。 |
| 2026-09-27 | 独立审查 tally moments、fixed-source loop、WW bank drain 和 source weight，写 pre-developer conclusion。 |
| 2026-09-27 | 完成 fresh serial N scaling、M=10 analog/WW scatter、zero score、Normalize tests，随后读取 developer archive 比较。 |
| 2026-09-27 | 完成报告；RMC source clean。 |

证据等级：公式/控制流 E1；runtime structure E2；N scaling/scatter/Normalize/WW activation E3，限定 scope。
