# independent-f06-adjoint-field-review-r2

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-26 |
| 状态 | 已完成 |
| 任务类型 | 独立物理审查 / F06 空间×能群伴随场 tally |
| 任务模式 | C — 深度物理研究与学习 |
| 关联知识库条目 | F06 |
| RMC revision | `5cfb0f771d0c5a2127c90d57e51ce672a4e3b616` |
| 报告 | [Independent-F06-Adjoint-Spatial-Energy-Field-Review-r2.md](Independent-F06-Adjoint-Spatial-Energy-Field-Review-r2.md) |

## 1. 目标与范围

独立判断 current RMC 是否能在 standard MGACE fixed-source neutron adjoint、Cartesian mesh、MPI-off/OpenMP-off serial 范围输出第一版 MLVR 所需的 \(\phi^\dagger_{i,g}\)。不审核 CE、photon/coupled、angular flux、time、ML reconstruction、WW generation 或 F07 统计。

原始证据位于 `logs/`；本轮未修改 RMC 源码、测试、基准或参考结果。

> **模式 C 物理解释**：合格字段必须是每个空间 bin 和每个 MG transport group 的 source-normalized scalar flux density。`Normalize=0` 仅是 volume-integrated track-length score，不能直接当作 \(\phi^\dagger\)。

## 2. 做法与证据

### 独立性

先只阅读 current RMC source/docs/tests，并先保存 `logs/pre-developer-claim-conclusion.md`；之后才允许对比已有 F06 档案。当前 RMC source tree clean，未发生源码改动。

### 关键证据

- parser: `ReadMeshTallyCard.cpp:174-188,257-267`
- MG setup/index: `SingleTally.cpp:875-899`, `GetMgCs.cpp:231-297`, `CheckMgAceBlock.cpp:38-53`
- score: `TallyByTL.cpp:24-54`, `ScoreMeshTally.cpp:60-118`, `TallyType.cpp:46-49`
- accumulation/normalization: `TallyData.cpp:43-100`, `ProcessTally.cpp:360-394`
- spatial indexing: `MeshFun.cpp:151-184,270-387`
- output: `SingleTally.cpp:939-1004`, `MeshTallyHDF5.cpp:40-99`

### Runtime evidence

独立 MPI-off/OpenMP-off build 成功。Fresh two-bin adjoint/forward cases use Type=1, `Energy=-1`, paired `Normalize=0/1` mesh tallies. Corrected wide transverse geometry produced separate spatial/group text rows and volume ratios; HDF5 inspection showed `/Type1` spatial shape `(2,1,1)` without energy dimension. The first narrow geometry was rejected as noisy due to large location-warning count and is not used as positive evidence.

真实输出见 `logs/adjoint-Tally-corrected.txt`、`logs/forward-Tally-corrected.txt`、`logs/adjoint-MeshTally1-h5-header.txt`、`logs/adjoint-MeshTally1-Type1.txt` 与 summary logs。

### 未覆盖

直接 selected-bin oracle；无边界 warning 的生产级几何；MPI/OpenMP；HDF5 energy-aware output；CE/coupled；F07 RE/statistical qualification。

## 3. 决策记录

- **决定**：按用户要求重新独立审核；只读 RMC，任务目录内允许 build/run/log/report；发现问题只记录，不修复。
- **决定人 / 日期**：用户 / 2026-09-26。
- **约束**：不修改 RMC source/test/reference/benchmark，不开始 F07，不设计 Field class。

**变更卡**：
| 风险 | 范围 | 验证与停止条件 | 回滚 |
|---|---|---|---|
| tally 可能不是所需 \(\phi^\dagger_{i,g}\)，或 output 维度丢失 energy | 只读源码与运行；不改 RMC | 追踪 estimator、weight、volume、group map、output；未覆盖项保留 C/F | 删除任务目录 generated runs，不需回滚 RMC |

> **人类理解确认**：本轮目标是复核已有 F06 判断，不把“程序有输出”当作 field 正确，也不把文本 tally 自动升级为 HDF5 field 接口。

## 4. 结论与边界

- **结论**：**C — Verify**，限定于 standard MGACE fixed-source neutron adjoint、Type=1 Cartesian、`Energy=-1`、`Normalize=1`、MPI-off/OpenMP-off serial、文本 `inp.Tally`。
- **不能推出什么**：HDF5Mesh 不提供 space×energy field；`Normalize=0` 不是 flux density；不推出 F07 statistics、并行、CE、耦合粒子或无 warning 的生产质量。
- **遗留 / 下一步**：若需要机器可读字段，另立任务设计 energy-aware HDF5；若需要提高分类，先做无几何 warning 的 deterministic group/bin oracle，再交 F07。
- **提交状态**：RMC 未改动、无 commit/push；档案随 2026-09-26 根工作区提交入库。

> **结果解释**：源码和 runtime 支持“normalized text Cartesian mesh 可解释为 \(\phi^\dagger_{i,g}\)”这一限定假设；HDF5 维度缺失、边界 warning 和统计未审查阻止 A — Ready。

## 5. 过程记录

| 时间 | 操作 |
|---|---|
| 2026-09-26 | 建立独立 R2 Mode-C 档案。 |
| 2026-09-26 | 先阅读 current RMC source/docs/tests，保存 pre-developer conclusion。 |
| 2026-09-26 | 完成 serial build 与 fresh adjoint/forward mesh runs；保留真实输出摘要。 |
| 2026-09-26 | 完成第二轮报告；RMC source clean。 |

证据等级：静态 E1；runtime reachability E2；volume/group/output targeted behavior E3（受 warnings 限定）。
