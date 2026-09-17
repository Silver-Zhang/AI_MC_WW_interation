# f02-parallel-statistical-gate-calibration

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-31 |
| 状态 | 已完成 |
| 任务类型 | 算法实验 / 统计判据校准 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F02 |
| 涉及文件 | 仅任务侧统计检查器、运行记录与文档；`RMC/` 只读 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `b26a81a2...` |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：为多 MPI rank 的条件角分布验证定义预注册、可解释且控制多重比较的统计判据；不得事后把 task 01 的失败改判为通过。

**范围**：复核 task 01 的 rank-aware `MuLab` 原始报告，设计未来重跑的主检验与诊断检验。仅任务侧；不修改 RMC、核数据、reference/benchmark。

**验收标准**：用户批准判据后，检查器明确区分主检验与诊断检验、对多重 rank/seed 比较控制家族第一类错误，并在全矩阵重跑前冻结。

**原始材料**：task 01 的 2×1/4×1 raw/strict reports、strict exit summary 与独立审计；本任务只保存设计和后续真实复验输出。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：task 01 对每个 case/mode/seed/rank 共执行大量未校正的 $|z|\le3$ 检验。4×1 中 seed 41/rank 3 isotropic 的 $z=-3.15282$ 越界；支持域和方差通过，2×1 完整 strict 通过。该结果不能自行区分实现偏差与多重比较下的预期偶发越界。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `20260831_01.../strict_check_summary.txt` | 2×1 strict passed；4×1 strict failed 的原始退出码和统计量。 |
| 2 | `20260831_01.../check_ranked_angular_strict.py` | 失败原因是将每个 rank/seed 检验与主结论做逻辑 AND，未控制多重比较。 |
| 3 | `20260828_01.../check_angular_formal_strict.py` | 串行冻结门槛提供支持域、均值、方差/频数检验的已验证实现。 |

**影响面**：只影响未来 MPI/OpenMP 的证据判定；不回溯改变 task 01 结论、不修改生产代码或基准。

**为什么之前没做/没发现**：（可选，但对改进机制很有价值）

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A | 主检验按 case/mode 汇合全部 rank×seed 样本；支持域为零容忍，连续均值 $|z|\le3$、方差为既有 99% 区间，离散 Pearson 保持既有阈值。rank/seed 仅为诊断；若需要报警，对其 $p$ 值实施 Holm-Bonferroni familywise 校正。 | 主结论检验八个物理分布，避免将大量随机诊断当作物理主检验。 | ★推荐 |
| B | 保持每 rank/seed 皆为硬门槛，但把 $|z|$ 阈值按全家族 Bonferroni 校正。 | 极保守，样本量和运行成本高，易降低检验功效。 | 不推荐 |
| C（不做/最小改动） | 维持 task 01 的逐项 AND 判据。 | 并行范围保持 C — Verify，无法完成混合矩阵。 | 不采用 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A。
- **决定人 / 日期**：用户 / 2026-08-31。
- **理由与约束**：不得使用新判据追认 task 01 的 4×1 通过；必须保留该失败反例。冻结八个 case/mode 主检验、rank/seed 诊断范围、Holm-Bonferroni family和 `2×1/4×1/2×2/2×4` 复验矩阵。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 实现校准检查器 | `check_parallel_angular_calibrated.py` | 主检验汇合每个 case/mode 的全部 rank×seed 样本；rank/seed 保留为 Holm-Bonferroni 诊断。 |
| 2 | 重跑校准全矩阵 | `logs/formal_{mpi_2x1,mpi_4x1,omp_2x2,omp_2x4}/` | 每配置 40/40 结构运行均通过；四配置的八个 aggregate 主检验均通过。 |
| 3 | 保留原始诊断 | `logs/formal_mpi_4x1/calibrated_report.json` | 原 seed 41/rank 3 isotropic forward/adjoint 的 Holm 拒绝仍存在；未重新标记为通过。 |

**代码改动**：见 [changes.diff](changes.diff)，摘要：
- `check_parallel_angular_calibrated.py` —— 新增已批准的 aggregate 主检验与 Holm rank/seed 诊断；不改 `RMC/`。

生成方式：
```bash
git -C ../../RMC diff > changes.diff
# 改原型则：
git -C ../../AIMC_WWiteration diff > changes.diff
```

---

## 6. 验证 / 实验记录（④ · Agent 填，要贴真实输出）

| 验证项 | 命令 | 结果 |
|---|---|---|
| MPI `2×1` | 40 条、2 ranks × 1 thread | `status=passed`；结构通过；8/8 aggregate 通过；0 个 Holm family 拒绝。 |
| MPI `4×1` | 40 条、4 ranks × 1 thread | `status=passed`；结构通过；8/8 aggregate 通过；两个 isotropic Holm family 保留 seed 41/rank 3 拒绝。 |
| MPI+OpenMP `2×2` | 40 条、2 ranks × 2 threads | `status=passed`；结构通过；8/8 aggregate 通过；0 个 Holm family 拒绝。 |
| MPI+OpenMP `2×4` | 40 条、2 ranks × 4 threads | `status=passed`；结构通过；8/8 aggregate 通过；0 个 Holm family 拒绝。 |

```
mpi_2x1: status=passed structural=True aggregate=8/8 holm_families=0
mpi_4x1: status=passed structural=True aggregate=8/8 holm_families=2
omp_2x2: status=passed structural=True aggregate=8/8 holm_families=0
omp_2x4: status=passed structural=True aggregate=8/8 holm_families=0

mpi_4x1 isotropic adjoint [(41, 3, 0.0016169913451314702)]
mpi_4x1 isotropic forward [(41, 3, 0.0016169913451314702)]

raw report SHA256:
- `mpi_2x1`: `93f3e6274d4da4ba4ec801df6fc5dd0f6b2e2f4ef09f224498fe95cb85d33b33`
- `mpi_4x1`: `5c124c97ee5f0eab4d6fe351e560582be26f22633fd21c3caa814b9b4c7fc0d1`
- `omp_2x2`: `ca808ba6bd24e07da60ab6905447be13880e17db3adfa05b5a1a4ebfc688b21b`
- `omp_2x4`: `59e5b38c82f807a678f34bdbfc2a24a1c61b0c6430fbdbac5c37b666b3594770`
```

**实验设置（算法实验必填）**：
- 随机种子：`17,23,41,59,83`；RNG type 2、stride 1,000,000。
- 配置快照：每 transport 50,000 histories、每 rank 1,000 个生产 `MuLab`；四类两群私有 MGACE 表示；MPI `2×1/4×1` 与 MPI+OpenMP `2×2/2×4`。
- 依赖版本：Linux x86_64；Open MPI 4.1.6；GDB 15.1；MPI binary SHA256 `60ecf80d9bc8aa3b530d2364694573744edbf26055d85e0a5b7305c5063f33fe`。
- 基准对比：task 01 冻结 strict 矩阵与其 MPI `4×1` seed 41/rank 3 原始反例。

**未覆盖到的验证**：不覆盖超过 4 ranks、超过 4 threads/rank、跨节点、Windows、GPU、CE、AIS/HDF5 核数据、photon/耦合粒子、delayed、GPT、反射边界或任意机制组合；本统计任务也不替代响应级并行验证和独立审计。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：已批准的 aggregate 主检验在 `2×1`、`4×1`、`2×2`、`2×4` 全矩阵均通过。`4×1` 的原 seed 41/rank 3 isotropic forward/adjoint 在 Holm 校正后仍为诊断拒绝（$p=0.00161699$）；它不推翻已通过的 aggregate 主检验，但也不能被删除或追认为 task 01 strict pass。并行范围继续为 **C — Verify**，不据此提升 F02 的 A 作用域。
- **遗留问题 / 后续待办**：若要改变并行分类，需将响应级证据、条件角 aggregate 结果、独立 seed 复现与独立审计合并复核，并由用户另行决策。
- **知识库同步**：未更新全局分类或物理导读；本任务仅完成已批准的统计方法和矩阵验证。
- **是否已提交**：未提交、未 push；`RMC/` 未修改。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-31 15:08 | 立项 |
| 2026-08-31 | 完成四配置、共 160 条运行的校准角分布矩阵。 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 冻结方案 A | README 第 4 节 | 用户批准 aggregate 主检验、Holm 诊断及四配置复验矩阵。 |
| 3 | 校正离散诊断尾概率 | `check_parallel_angular_calibrated.py` | 使用 $\chi^2$ 自由度 2 的精确尾概率 `exp(-chi_square/2)`。 |
| 4 | 运行完整矩阵 | `logs/*_formal.log` | 160/160 结构运行完成，耗时 33m47s。 |
| 5 | 汇总诊断 | `logs/formal_*/calibrated_report.json` | 所有 aggregate 主检验通过；仅 `4×1` 的两个同形 isotropic family 触发 Holm 诊断。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
