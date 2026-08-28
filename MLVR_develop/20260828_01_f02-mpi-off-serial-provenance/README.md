# f02-mpi-off-serial-provenance

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-28 |
| 状态 | 已完成（严格 MPI-off serial A） |
| 任务类型 | 验证基础设施 / 证据恢复 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F02 |
| 涉及文件 | 任务侧 MPI-off build provenance、formal 重跑与分类文档；`RMC/` 源码仅读 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `6d208751...` + W9 diff `5eec...`；不提交/推送 RMC |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：消除 F02 作用域中“serial”的歧义。以显式 `mpi=OFF` 的 fresh build 复现全部 40 条 angular 与 10 条 density formal，并验证运行 banner 为 MPI OFF；只有完整证据链闭合后，才允许冻结范围的 F02 保持 A。

**范围**：仅任务侧构建目录、输入、raw evidence、日志与文档。不得修改 RMC 源码、核数据、reference/benchmark，且不得提交/推送/切换 RMC 分支。

**验收标准**：fresh configure 明确记录 `MPI parallel: turned OFF`；runtime banner 为 `MPI parallel: OFF`；新 binary 与冻结 source/差异绑定；angular 40/40 与 density 10/10 raw formal 和严格 checker 通过；fresh CTest、SHA256 manifest 和独立审计通过。

**原始材料**：用户提供的独立审计结论指出 task 05 的 MPI-enabled one-rank execution 与“serial”标签存在歧义；本任务 `logs/` 将保存 MPI-off configure/build/banner、raw formal、strict reports、CTest 与 checksum。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：任务 05 的 source—binary identity、50 条 raw formal 和严格统计均已闭合，但其 banner 为 `MPI parallel: ON, 1 process(es)`。RMC CMakeLists 的 MPI 逻辑在未定义 `mpi` 时自动探测并启用 MPI；显式 `-Dmpi=OFF` 则设置 `MPI_USE OFF`。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `RMC/CMakeLists.txt:147-166` | 未定义 `mpi` 时若系统发现 MPI 则自动启用；需显式 `-Dmpi=OFF`。 |
| 2 | task 05 `fresh_banner_probe.txt` | 已验证 binary 为 MPI-enabled one-rank execution，不等同于严格 MPI-off build。 |
| 3 | 用户独立审计结论 | 推荐维持 C，或按严格 serial 方案执行 MPI-off fresh build + 50 条 formal。 |

**影响面**：仅 F02 的冻结运行时标签与其分类证据；不更新基准结果或修改 RMC。

**为什么之前没做/没发现**：（可选，但对改进机制很有价值）

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A：MPI-off fresh full matrix | 显式 `-Dmpi=OFF`，重跑 angular 40 条、density 10 条、CTest、checksum 和独立审计。 | 计算成本约等于 task 05，但消除作用域歧义。 | ★推荐 |
| B：重写范围标签 | 将 A 改称 MPI-enabled one-rank execution。 | 不验证严格 MPI-off serial；需要人接受语义变化。 | 不采用 |
| C：维持 C | 保留当前歧义，不再计算。 | 无计算成本，但 F02 不能满足严格 serial A。 | 不采用 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A — MPI-off fresh full matrix。
- **决定人 / 日期**：用户 / 2026-08-28（要求按严格 `serial = MPI-off build` 解释，推荐方案 2）。
- **理由与约束**：不得修改 RMC；不得更新 reference/benchmark 或删除失败输出。所有 formal 使用冻结 seeds、population、资产、mesh 和 strict gates；仅当 banner 明确 MPI OFF 时计入 A。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 建档并记录审计阻断 | 本 README、用户审计结论 | task 05 的 one-rank MPI execution 不足以无歧义支撑 MPI-off serial 标签。 |
| 2 | fresh MPI-off configure/build | `/tmp/mlvr_f02_mpi_off_build` | 显式 `-Dmpi=OFF`；configure 记录 `MPI parallel: turned OFF`，runtime banner 为 `MPI parallel: OFF`。 |
| 3 | angular formal 重跑 | `logs/angular_formal_mpi_off_20260828/` | 40/40 structural pass；raw report 绑定 MPI-off binary。strict checker 的逐 seed/aggregate 门槛通过。 |
| 4 | density formal 重跑 | `logs/density_formal_mpi_off_20260828/` | 10/10 structural pass；五对及合并互易性通过，合并 $z=0.0946746946$。 |
| 5 | 回归、完整性与独立审计 | CTest、SHA256、GPT poly-bridge | `test_fixed_source_adjoint` 1/1 passed；六项 checksum 通过；独立审计 ACCEPT。 |

**代码改动**：RMC 无改动；完成后生成 [changes.diff](changes.diff) 以快照冻结 W9 diff。

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
| MPI-off configure / banner | `logs/mpi_off_configure.txt`、`mpi_off_banner_probe.txt` | configure 明确 MPI OFF；runtime banner 为 `MPI parallel: OFF`、`OMP parallel: OFF`、Git `6d208751...`。 |
| source/binary identity | `source_snapshot.txt`、`changes.diff`、`binary.sha256` | HEAD `6d208751...`，W9 diff SHA256 `5eec...`；MPI-off binary SHA256 `f7354ed9...6d3e`。 |
| angular raw + strict | MPI-off angular runner/checker | 40/40 structural pass；八个 case/mode 的逐 seed 与 aggregate 统计均通过。 |
| density raw + strict | MPI-off density runner/checker | 10/10 structural pass；五对及合并均 $|z|\le3$，合并 $z=0.0946746946$。 |
| fixed-source regression | `ctest --test-dir /tmp/mlvr_f02_mpi_off_build -R '^test_fixed_source_adjoint$'` | 1/1 passed（0.74 s）。 |
| SHA256 manifest | `sha256sum -c logs/SHA256SUMS.txt` | raw reports、strict reports、W9 diff 与 MPI-off binary 共六项全部成功。 |

```
```text
Git commit  : 6d2087518e0d9f23574d629f5fde361c79f519e4
MPI parallel: OFF
OMP parallel: OFF
angular_raw_runs=40
density_raw_runs=10
density_combined_z=0.09467469456468869
test_fixed_source_adjoint=1/1 passed
independent_audit=ACCEPT
```
```

**实验设置**：冻结 seeds `17,23,41,59,83`；angular/density 均 50,000 histories/run；angular 每 run 1,000 GDB production samples；RNG type 2、stride `1000000`；`ais=OFF`；MPI 显式 OFF；OpenMP OFF。

**未覆盖到的验证**：MPI 多 rank、OpenMP、Windows、photon/耦合粒子、CE、AIS/HDF5 核数据、delayed、GPT、反射边界和 F03/F04/F06/F07 均不在范围内。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：严格 MPI-off serial 的 fresh source—binary identity、50 条 formal raw evidence、strict gates、CTest 和 checksum 均闭合；独立审计 ACCEPT。冻结 F02-B 为 **A — Ready（有界）**。
- **遗留问题 / 后续待办**：继续既有 F03 审查；MPI 多 rank、OpenMP 和其他范围外能力不继承 F02 A。
- **知识库同步**：已同步 F02 当前分类、serial 定义和物理导读。
- **是否已提交**：未提交/推送；RMC 未修改。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-28 01:57 | 立项 |
| 2026-08-28 | MPI-off fresh build、50 条 formal、strict gates、CTest、checksum 和独立审计完成。 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 读取用户独立审计建议 | 用户请求、task 05 banner | 接受 MPI-off serial 的严格解释，方案 A 已获得用户决定。 |
| 3 | 读取 CMake MPI 开关 | `RMC/CMakeLists.txt:147-166` | 确认未定义时自动探测 MPI；显式 `-Dmpi=OFF` 可关闭 MPI。 |
| 4 | fresh MPI-off build 与 banner probe | `/tmp/mlvr_f02_mpi_off_build` | configure 和 runtime 分别证明 MPI OFF；Git banner 与冻结 HEAD 一致。 |
| 5 | fresh MPI-off formal | task 01 raw runners | angular 40/40、density 10/10 structural pass，全部保留逐运行输入、stdout、stderr、输出及 exit code。 |
| 6 | strict / CTest / SHA256 | task 01 logs | 两份 strict report 均 passed；CTest 1/1 passed；六项 checksum 全部成功。 |
| 7 | 独立审计 | GPT poly-bridge | ACCEPT；无遗漏、范围外推或 MPI-enabled 结果复用问题。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
