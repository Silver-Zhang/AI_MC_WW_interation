# f09-response-fom-closure

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-27 |
| 状态 | 已完成 |
| 任务类型 | 轻量功能验证 / Response statistics + FOM information |
| 任务模式 | A — 受约束自动化 |
| 报告人 | Agent |
| 关联知识库条目 | F09 |
| 涉及文件 | RMC 只读；本任务输入与运行证据 |
| 分支 / 提交 | 根工作区 `main`；RMC 未修改 |

---

## 1. 目标与范围（① 立项 · Agent 填）

验证第一版 formal Forward iteration 可从 RMC 同一次 serial fixed-source run 获得 scalar target response `R`、response relative error `RE_R` 与 `T = Time in Fixed Source Calculation`，供外部计算 `FOM = 1 / (RE_R^2 * T)`。

限定范围：standard MGACE、neutron、fixed-source Forward、MPI-off/OpenMP-off serial、text `inp.Tally`、Type=1 track-length tally。明确排除 Bootstrap、adjoint、field RE 深审查、WW 数学、controller 与 RMC 内部 FOM。

完成标准：同一次正式 Forward run exit 0，target scalar response 与其 RE 非零，stdout/output 中可读取 fixed-source runtime；证据能关联 `particle_population`、`run_identity`、`stage=formal_forward`、`iteration_id` 与 WW 状态。

**原始材料**（`logs/` 下有什么）：`formal_forward.inp`、`formal_forward.Tally`、`formal_forward.stdout`、`formal_forward.stderr`、`formal_forward.inp.out`；本任务只保留可复核的小型 text/stdout 证据。

> **模式 C 追加 · 物理解释**：F09 的对象是同一次 run 内同一 target 的统计量：scalar `R` 与其统计误差 `RE_R` 必须来自同一 tally 行，`T` 必须与该 run 的计算量口径一致。若 `R`/`RE_R` 非零且 `T` 可从同一次 run stdout 读取，则外部 FOM $=1/(RE_R^2 T)$ 可复核；若混用不同行、不同 run 或不同时间口径，则 FOM 不可复核。

---

## 2. 做法与证据（② 设计 · ④ 实施 · Agent 填）

**设计 / 定位**：复用 F01/F05 已验证的 standard MGACE Forward mesh tally 输入。scalar `R` 取第一个 Cartesian mesh spatial bin `(1,1,1)` 的 `Tot` 行 `Ave`；它是该 cell/mesh 区域、全 30 MG energy groups 的 neutron Type=1 track-length flux tally，`Normalize=1`。`RE_R` 取同一 `Tot` 行的 `RE`。历史输出显示 RMC stdout/out 可同时提供 `Time in Fixed Source Calculation` 与 `Total Calculation Time`；本任务冻结前者为 FOM 的 `T`。

**方案选择**：采用单次 formal Forward run；不做 WW-on paired comparison，避免将 F09 扩展为 WW 效率或无偏性复核。

**实施要点**：无 RMC 代码改动；无 `changes.diff`。新增输入见 `formal_forward.inp`。
**验证输出**（贴真实命令与输出；物理结论从严，工程/文档从简）：

```text
Code version: 3.5.0
Git commit  : b7d8a946417eea091a30c09c233054aa077570ee
MPI parallel: OFF
OMP parallel: OFF
******** Calculation mode: fixed-source ********
Neutron collisions per source particle: 224.71
RMC Calculation Finish.
Total Calculation Time                   = 1.0508e+01 seconds
Time in Fixed Source Calculation         = 1.0507e+01 seconds

Target mesh bin (1,1,1), Tot:
R = 3.1144E+01
RE_R = 1.7665E-03

Final Tally Tot rows:
target (1,1,1): Ave=3.1144E+01  RE=1.7665E-03
other  (1,1,2): Ave=3.8061E-02  RE=2.9213E-02

FOM = 1 / ((1.7665e-3)^2 * 10.507 s)
	= 3.04995888026261e4 1/s

stderr bytes: 0

`Total Calculation Time = 10.508 s` is auxiliary; frozen FOM timing is
`T_fixed = Time in Fixed Source Calculation = 10.507 s`.
```

**未覆盖到的验证**（如实写；没有就写“无”）：MPI/OpenMP、CE、photon/coupled、HDF5 response interface、自动 FOM、自动停止、组合多 run FOM、WW-on FOM 对比均未验证。

---

## 3. 决策记录（③ · **人拍板**）

- **决定**：采用唯一空间 bin 的全能群 `Tot Ave/RE` 作为 scalar `R/RE_R`；采用同一次 run 的 `Time in Fixed Source Calculation` 作为 `T`；仅进行单次 formal Forward。
- **决定人 / 日期**：用户任务要求 / 2026-09-27
- **约束**：不修改 RMC，不设计完整 `ResponseRecord` class/JSON/database，不实现 controller，不将 Bootstrap 纳入 FOM。

**变更卡（B/C 模式，各一行）**：
| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| 将不同输出行或不同时间口径混用，导致 FOM 不可复核 | 仅新增任务输入、证据和归档；不改 RMC | 同一 run 同时出现非零 `Tot Ave`、非零 `Tot RE`、fixed-source time 与 exit 0 后停止 | 删除任务证据，不涉及 RMC |

> **模式 C 追加 · 人类理解确认**：用户任务要求仅验证“同一次 formal Forward run 能否提供可复核的 `R`/`RE_R`/`T`”；批准范围仅此——不设计 `ResponseRecord` schema、不实现 FOM controller、不将 Bootstrap 纳入 FOM。

> 未拍板前，Agent 不得改动 `../RMC` 下的任何文件。



---

## 4. 结论与边界（⑤ 归档）

- **结论**：**F09 = A — Ready（限定第一版子域）**。同一次 formal Forward serial run 可靠提供非零 `R=3.1144E+01`、非零 `RE_R=1.7665E-03` 和 `T=10.507 s`；外部可直接计算单-run FOM `3.04995888026261e4 1/s`。
- **不能推出什么**（边界）：不外推至 Bootstrap FOM、WW efficiency、组合多 run FOM、自动停止或并行/耦合域。
- **遗留 / 下一步**：无；按 stop rule 停止，不实现 FOM controller、收敛判据、F10/F11 或 Bootstrap FOM。
- **提交状态**：RMC 未修改、无 commit/push；档案与 text/stdout 证据（根目录与 `logs/` 副本）随 2026-09-27 根工作区提交入库；原始 `.inp.out`/`.fissmul`/`.material`/`.rossialpha`/`.cumrossialpha` 与 `*.h5` 按体积规范不入库、仅保留本地。

> **模式 C 追加 · 结果解释**：结果支持“单-run response 统计与 fixed-source timing 可从同一份输出复核”这一假设；示例 FOM 数值不代表收敛判据或跨 run 最优性；边界见上列“不能推出什么”。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-27 12:59 | 立项；建立 F09 目录与输入设计 |
| 2026-09-27 13:06 | 完成 200k-history formal Forward run；修正单 mesh warning 后以 2 spatial bins 重跑；exit 0 |
| 2026-09-27 13:07 | 从同一次输出提取 `R`、`RE_R`、fixed-source time 并计算单-run FOM；归档原始输入、Tally、stdout、stderr |

**ResponseRecord 最小信息（仅记录合同，不实现 schema）**：`response_value`、`response_RE`、`fixed_source_time`、`particle_population`、`run_identity`、`stage=formal_forward`、`iteration_id`（首版可为 `none`）、`WW=off`。

**FOM timing rule**：单次 run 使用 `FOM = 1 / (RE_R^2 * T_run)`；若未来组合独立 runs，必须使用 `T_total = sum(T_i)`，不能使用平均 runtime。Bootstrap 的 `phi0 + RE0` 不参与 formal FOM。

> 关键命令、误判与修正、未决分歧都写在这里；人机讨论较深时把要点并入本表，**不再单独建会话纪要文件**。原始聊天转储不要入仓（可能含凭据）。

**证据等级（可选）**：物理/审查结论可标 E0–E4；工程、文档、治理任务可省略。
