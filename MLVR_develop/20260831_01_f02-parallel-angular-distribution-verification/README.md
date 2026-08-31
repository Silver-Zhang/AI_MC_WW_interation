# f02-parallel-angular-distribution-verification

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-31 |
| 状态 | 已完成（严格门槛未通过） |
| 任务类型 | 算法实验 / 并行正确性验证 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F02 |
| 涉及文件 | 仅任务侧运行器、检查器、日志与文档；`RMC/` 只读 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `b26a81a2...` |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：补齐 MPI 多 rank 与 MPI+OpenMP 下生产 `MuLab` 条件角分布证据，关闭前一并行专项的唯一 CONDITIONAL 缺口。

**范围**：Linux x86_64、standard ASCII 两群私有 MGACE、fixed-source neutron forward/adjoint；MPI `2×1/4×1` 与混合 `2×2/2×4`。不修改 RMC、核数据、reference/benchmark。

**验收标准**：每配置运行四类角表示 × forward/adjoint × 五冻结 seeds 共 40 条；每个 MPI rank 经 GDB 取得 1,000 个生产 `MuLab` 返回样本；退出、banner、stderr、anomaly 和样本数量均通过结构门禁；每 rank、每 seed 和聚合样本通过既有支持域、均值、方差或离散频数 strict gates。

**原始材料**：`logs/` 保存每配置命令、GDB stdout/stderr、transport stdout/stderr、raw/strict report、二进制和脚本 hash；大文件由 `.gitignore` 排除。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：任务 30 已证明六配置的运行、density/fissile 响应和 angular 输运结构，但未在多 rank 采样条件角返回值，独立审计因此为 CONDITIONAL。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `20260826_02.../sample_mulab_gdb.py` | 已验证的 x86_64 return-boundary GDB 观测器。 |
| 2 | `20260828_01.../check_angular_formal_strict.py` | 已冻结的支持域、均值、方差与离散频数门槛。 |
| 3 | `RMC/src/OutputHeading.cpp` | 运行 banner 提供实际 MPI/OMP 配置。 |

**影响面**：仅 F02 MPI/OpenMP 分类证据；不改变输入接口、基准或生产源码。

**为什么之前没做/没发现**：（可选，但对改进机制很有价值）

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A | 在每 rank 启动 GDB，分别保存并检查其 1,000 个样本；另行完整 transport。 | 成本高，但直接证明各 rank 分布。 | ★推荐 |
| B | 仅 rank 0 采样。 | 不能排除 rank 特异分布错误。 | 不采用 |
| C（不做/最小改动） | 保持 CONDITIONAL。 | 并行不继承 A。 | 不采用 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A。
- **决定人 / 日期**：用户 / 2026-08-31。
- **理由与约束**：用户授权“按照计划完成，将工作收尾”；冻结 seeds `17,23,41,59,83`、50,000 histories/transport、每 rank 1,000 GDB 样本、既有 strict gates。保留失败产物；不改 RMC、核数据或 reference/benchmark。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 建立 rank-aware GDB probe | `gdb_mulab_rank_probe.py` | 每个 MPI rank 将首批生产样本写入独立 JSON，避免 MPI stdout 交错。 |
| 2 | 2×1 pilot | `logs/pilot_2x1_retry4/` | 8/8 structural pass；每 rank 20 样本的 strict gate 通过。 |
| 3 | 2×1 formal | `logs/formal_mpi_2x1_retry1/` | 40/40 structural pass；每 rank 1,000 样本的 strict gate 通过。 |
| 4 | 4×1 formal | `logs/formal_mpi_4x1_retry1/` | 40/40 structural pass，但预冻结的每-rank strict gate 失败；按停止规则不执行混合配置。 |
| 5 | 独立审计 | `independent_audit.txt` | CONDITIONAL：物理/停止结论准确；补存 strict 检查的真实退出状态与汇总输出。 |

**代码改动**：见 [changes.diff](changes.diff)，摘要：
- `RMC/` 无改动；任务侧新增 rank-aware GDB probe、运行器和 strict checker。

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
| 2×1 pilot | 4 表示 × forward/adjoint × seed 17，2 ranks、每 rank 20 样本 | 8/8 structural pass；strict passed。 |
| 2×1 formal | 4 表示 × forward/adjoint × 5 seeds，2 ranks、每 rank 1,000 样本 | 40/40 structural pass；strict passed。 |
| 4×1 formal | 同上，4 ranks、每 rank 1,000 样本 | 40/40 structural pass；strict failed。seed 41/rank 3 的 isotropic forward/adjoint 均值为 `-0.0575624`，$z=-3.15282$；支持域和方差均通过。 |

```
严格 gate 对 4×1 返回非零，因此停止后续 `2×2` 与 `2×4`，未修改 seed、样本量或判据。
```

**实验设置（算法实验必填）**：
- 随机种子：`17,23,41,59,83`；RNG type 2、stride 1,000,000
- 配置快照：50,000 histories/transport；每 rank 1,000 生产 `MuLab` 样本；四类两群私有 MGACE 资产
- 依赖版本：Open MPI 4.1.6、g++ 13.3.0、GDB 15.1
- 基准对比：既有 MPI-off strict angular 分布门槛

**未覆盖到的验证**：4×1 strict 失败后按停止规则未运行 `2×2/2×4`；不覆盖超过 4 ranks、跨节点、Windows、CE、AIS/HDF5、photon/耦合粒子、delayed、GPT、反射边界及任意机制组合。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：2×1 的并行角分布 strict gate 通过；4×1 的 40 条输运结构均通过，但一个预冻结 per-rank isotropic 均值统计量越过 $|z|=3$，因此该严格矩阵未通过。该反例不能单独证明 RMC 物理 defect，但不能支持提升 MPI/OpenMP 的 F02 分类。
- **遗留问题 / 后续待办**：保持 MPI/OpenMP 为 C — Verify。若需要继续，须由用户重新决定是否采用适合多重 per-rank 检验的预注册统计设计；不得事后改阈值、换 seed 或追加样本掩盖本次失败。
- **知识库同步**：不修改全局 F02 分类；任务档案和 INDEX 记录失败结论。
- **是否已提交**：分支 / commit hash ／ 由谁在何时 push

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-31 01:11 | 立项 |
| 2026-08-31 | 2×1 formal 通过；4×1 在 seed 41/rank 3 触发预冻结 per-rank mean gate，按停止规则归档。 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 观测器 pilot | 2×1、8 个小样本输运 | 首版提前停止会触发 MPI abnormal termination；改为采样后禁用入口/返回断点，正常 finalize。 |
| 3 | 2×1 formal | 40 条、2 ranks、每 rank 1,000 样本 | 所有结构、per-rank、per-seed 与 aggregate gates 通过。 |
| 4 | 4×1 formal | 40 条、4 ranks、每 rank 1,000 样本 | 结构门禁通过；isotropic forward/adjoint 的同一 seed/rank 均值 $z=-3.15282$，strict failed。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
