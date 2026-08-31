# f02-mpi4-angular-seed-replication

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-31 |
| 状态 | 已完成 |
| 任务类型 | 算法实验 / 独立复现 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F02 |
| 涉及文件 | 仅任务侧运行、检查和归档；`RMC/` 只读 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `b26a81a2...` |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：使用与 task 01 不重叠的新随机流，独立检验 MPI `4×1` 中 seed 41/rank 3 各向同性均值诊断异常是否重复。

**范围**：Linux x86_64、MPI `4×1`、四类两群私有 MGACE 表示、forward/adjoint。复用 task 01 的 rank-aware GDB probe 和 task 02 已批准主检验；不修改 RMC、核数据或 reference/benchmark。

**验收标准**：四表示 × forward/adjoint × 五个新 seed 共 40 条，每条每 rank 1,000 个 `MuLab` 样本；结构门禁通过；按 task 02 主检验评估 aggregate，Holm 诊断用于判断异常是否在独立流复现。

**原始材料**：task 01 失败报告、task 02 校准报告、每条新运行的 GDB/transport 原始材料和 raw/strict reports；`logs/` 大文件由 `.gitignore` 排除。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：task 01 的 `4×1` 中，seed 41/rank 3 在各向同性 forward/adjoint 都有 $z=-3.15282$，但支持域、方差及 task 02 的 aggregate 主检验通过。该新实验不替代原始失败，专门判别其是否在独立流重现。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `20260831_01.../strict_check_summary.txt` | 记录原 seed 41/rank 3 诊断异常。 |
| 2 | `20260831_02.../check_parallel_angular_calibrated.py` | 已批准的 aggregate 主检验及 Holm 诊断。 |
| 3 | `20260831_01.../run_ranked_angular_formal.py` | 已验证的每 rank 独立样本运行器。 |

**影响面**：只影响对诊断异常的解释；不改变生产实现、输入接口、基准或既有分类。

**为什么之前没做/没发现**：（可选，但对改进机制很有价值）

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A | 新 seeds `101,103,107,109,113` 重跑完整四表示/前伴随 `4×1` 矩阵。 | 可区分原异常是否在独立流中重复。 | ★推荐 |
| B | 仅重跑 isotropic。 | 成本低，但不能同时确认其余表示保持正常。 | 不采用 |
| C（不做/最小改动） | 不运行独立流。 | 只能保留不确定解释。 | 不采用 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A。
- **决定人 / 日期**：用户 / 2026-08-31。
- **理由与约束**：用户授权按独立复现计划实施。冻结新 seeds `101,103,107,109,113`、50,000 histories/transport、每 rank 1,000 样本、MPI `4×1` 和 task 02 判据；保留原 seed 41 反例，不因新结果回写或删除。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 生成并执行独立复现矩阵 | 复用 task 01 `run_ranked_angular_formal.py`；MPI `4×1` | 四表示 × forward/adjoint × 五新 seed 的 40/40 条运行均完成，结构门禁均通过。 |
| 2 | 应用已冻结校准判据 | 复用 task 02 `check_parallel_angular_calibrated.py` | 八个 aggregate 主检验均通过；八个 Holm rank/seed 诊断 family 均无拒绝。 |

**代码改动**：见 [changes.diff](changes.diff)，摘要：
- 未修改 `RMC/`、核数据、reference/benchmark；`changes.diff` 为空快照。

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
| 40 条 rank-aware 角分布运行 | `run_ranked_angular_formal.py --population 50000 --sample-count 1000 --seeds 101 103 107 109 113 --ranks 4 --threads 1` | 40/40 `pass=True`；`all_structural_pass=true`。 |
| aggregate 主检验与 Holm 诊断 | `check_parallel_angular_calibrated.py --report raw_ranked_transport_report.json --output calibrated_report.json` | `status=passed`；8/8 aggregate 通过；0 个 Holm 拒绝。 |
| 证据完整性 | `sha256sum raw_ranked_transport_report.json calibrated_report.json` | raw report: `a7f5d7d30e4f48280cdcbf7b7be06a87e527bb9865da4ff47fecadd476fc8961`；calibrated report: `086bd74b5cd828856f9dd6e044f67ef107b7537ac05613462368f639c46f6282`。 |

```
generated_runs=40
manifest_sha256=17e5b02fa88a5deada72f7efc35102f538b774ad831ec031a8d205ff814ecb56
01/40 isotropic forward seed=101 pass=True
...
40/40 discrete_cosine adjoint seed=113 pass=True

status= passed
structural= True
discrete_cosine adjoint: aggregate_pass=True n=20000 holm_rejects=0
discrete_cosine forward: aggregate_pass=True n=20000 holm_rejects=0
equiprobable_multi_bin adjoint: aggregate_pass=True n=20000 holm_rejects=0
equiprobable_multi_bin forward: aggregate_pass=True n=20000 holm_rejects=0
isotropic adjoint: aggregate_pass=True n=20000 holm_rejects=0
isotropic forward: aggregate_pass=True n=20000 holm_rejects=0
one_variable_positive adjoint: aggregate_pass=True n=20000 holm_rejects=0
one_variable_positive forward: aggregate_pass=True n=20000 holm_rejects=0
```

**实验设置（算法实验必填）**：
- 随机种子：`101,103,107,109,113`（与原 `17,23,41,59,83` 不重叠）。
- 配置快照：MPI `4×1`；每 transport 50,000 histories；每 rank 1,000 个 `MuLab`；density `1.0`；私有两群资产目录 `/tmp/mlvr_f02_angular_formal_20260827_retry2/assets`。
- 依赖版本：Linux x86_64；Open MPI 4.1.6；GDB 15.1；RMC binary SHA256 `60ecf80d9bc8aa3b530d2364694573744edbf26055d85e0a5b7305c5063f33fe`。
- 基准对比：不涉及 RE/FOM 基准；对照为 task 01 原 seed 41/rank 3 各向同性诊断异常。

**未覆盖到的验证**：本任务只独立复现 MPI `4×1`、threads `1`；不覆盖 task 02 已批准的 `2×1`、`2×2`、`2×4` 全矩阵，亦不覆盖 Windows、GPU 或生产规模问题。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：独立冻结随机流未复现 task 01 的 seed 41/rank 3 异常：40/40 结构运行完成，8/8 aggregate 主检验通过，8 个 Holm family 均为零拒绝。这支持原异常是孤立随机流诊断现象的解释，但不删除、不改判 task 01 的 strict failed 反例；MPI/OpenMP 分类仍为 **C — Verify**。
- **遗留问题 / 后续待办**：执行 task 02 已批准的 `2×1`、`4×1`、`2×2`、`2×4` 校准全矩阵；只有该矩阵与独立审计闭合后，才能讨论并行范围分类。
- **知识库同步**：未更新知识库或物理导读；本结果未改变既有分类或物理结论。
- **是否已提交**：未提交、未 push；`RMC/` 无代码改动。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-31 15:42 | 立项 |
| 2026-08-31 | 完成独立 MPI `4×1` 新 seed 角分布矩阵与校准检查。 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 冻结设计 | README 第 4 节 | 用户批准方案 A：五个独立 seed、40 条 `4×1` 运行，并保留原 seed 41 反例。 |
| 3 | 运行 formal 矩阵 | `logs/formal_mpi_4x1_new_seeds_run.log` | 672.049 s；40/40 `pass=True`。 |
| 4 | 统计汇总 | `logs/formal_mpi_4x1_new_seeds/calibrated_report.json` | aggregate passed；8 个 Holm family 均无拒绝。 |
| 5 | 代码诊断 | 复用的三份 Python 脚本 | 编辑器诊断均为 `No errors found`。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
