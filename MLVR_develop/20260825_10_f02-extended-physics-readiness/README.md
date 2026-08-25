# f02-extended-physics-readiness

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-25 |
| 状态 | 已完成：A 门禁未满足，维持 C — Verify |
| 任务类型 | 物理验证 / 现有能力审查 |
| 关联知识库条目 | F02 / W5 / W6 / W7 |
| 作用域 | standard MGACE + FIXEDSOURCE + neutron adjoint + `ais=OFF` |
| RMC 基线 | `Neural_Network_WW_Iteration` / `6d2087518e0d9f23574d629f5fde361c79f519e4` |

---

## 1. 任务定义

**目标**：独立、预冻结、可复现地扩展 F02 物理验证，并判断上述严格作用域是否可从 C — Verify 升级为 A — Ready。目标不是设法给出 A；任何失败、不可表达的必需机制或证据不足均保留/降低评级。

**范围**：只读 `RMC/`；任务目录内允许验证输入、脚本、日志和分析。排除 continuous-energy、photon、AIS/HDF5、GPT、delayed precursor、WW 组合与完整 MLVR。

**验收标准**：只有散射、密度/空间非均匀、混合材料、NNUBAR=1 与 >1 裂变、强各向异性、几何/边界和稳健性均能由预冻结 formal 矩阵实际表达并通过结构/统计判据，才允许建议 A。否则维持 C 或按缺陷降级。

**原始材料**：`logs/` 保存基线、可行性审计、两次 pilot 生成/运行输出、完整性检查；没有删除失败结果。

---

## 2. 调研与设计

**已知前证据**：W5/W6/W7 修复、非裂变 H/O、非均匀双区域响应和一组 NNUBAR=2 可裂变响应均有独立档案，但均不能替代本任务要求的完整、冻结扩展矩阵。

**机制审计**：见 [audit_mechanisms.md](tools/audit_mechanisms.md)。它复核了：P0 群转置、total-nubar 裂变核、局部密度权重、核素/反应抽样、银行后继和 tally 路径；并明确排除 delayed、CE、photon、AIS/HDF5、GPT 和 WW。

**部署数据与 harness 可行性**：见 `logs/coverage_feasibility.csv`。关键事实：

1. 可用 7 群 `c5g7td` 中裂变核素 `10001`–`10004` 都是 `NNUBAR=2`，`10005` 是 `NNUBAR=1`；部署路径能覆盖两类 nubar locator。
2. 当前部署表的 `NLEG=0`；没有现成的、已读回的强 P1/P2 定向 fixed-source-adjoint 响应 harness。
3. RMC 源码支持密度 mesh 输入，但本工作区没有经验证的任务私有 HDF5 density-mesh 写入器或可运行样例，不能把普通 cell `DENS` 替代为“已覆盖 density mesh”。
4. 当前隔离构建为 serial execution；banner 显示 MPI runtime 可用但本任务未配置/验证 OMP，Windows 无环境。

---

## 3. 方案与冻结门禁

| 方案 | 做法 | 判定 |
|---|---|---|
| A | 部署数据与 pilot 支持所有强制维度后冻结 formal manifest | 未满足 |
| B | 对部署数据无法表达的机制建立任务私有验证 MGACE/mesh 数据、读回 oracle 和理论核 | 未执行：需单独设计/审计，不能在本任务中临时替代 formal |
| C | 保留 C — Verify，并将缺口作为 A 门禁 | **采用** |

正式统计矩阵、五对 seeds 和 population 只允许在 pilot 对所有必需维度通过后冻结。由于 pilot 和可行性门禁未通过，**没有生成 formal manifest，也没有执行任何 formal case**；这符合“不以失败后改矩阵或改判据求 A”的规则。

---

## 4. 决策（用户授权）

- **采纳方案**：先可行性审计，再 pilot；仅在所有必需维度可表达、pilot 全通过时冻结 formal。
- **决定人 / 日期**：用户，2026-08-25。
- **授权与约束**：授权只读生产代码的扩展验证、任务侧输入/脚本和必要计算；禁止修改 RMC、reference、benchmark、核数据，禁止 commit/push/切分支，禁止事后挑 seed、删除失败或改判据。发现生产缺陷时应保留最小复现并停在修复门禁。

---

## 5. 实施记录

| # | 操作 | 结果 |
|---|---|---|
| 1 | `new_task.sh f02-extended-physics-readiness F02` | 建立独立档案 `20260825_10_...`。 |
| 2 | 冻结基线 | 记录 SHA、构建、核库/reference 哈希、工具链和 RMC 工作树。 |
| 3 | 隔离 configure/build | `/tmp/f02_ready_build` 构建成功；banner 显示 `6d208751...`。 |
| 4 | 部署数据/输入能力审计 | 生成 `deployed_mgace_inventory.csv` 和 `coverage_feasibility.csv`。 |
| 5 | 首次 pilot | 输入块间空行缺失，6/6 解析失败；完整失败输出保留于 `pilot_run.log`。pilot 阶段修复了任务输入生成格式，未进入 formal。 |
| 6 | 修正格式后重跑 pilot | NNUBAR=2 纯材料与混合材料前/伴随运行均退出 0、20,000 source histories、响应有限；NNUBAR=1 预选 `g6↔g1` 对中前向 RE=1、伴随响应为 0，pilot 失败。 |
| 7 | 门禁裁定 | 强 P1/P2、真实 density mesh 仍不可由已验证 harness 表达；NNUBAR=1 裂变对尚未筛选到有效响应。formal 不冻结，保持 C。 |

**生产代码改动**：无。本任务 [changes.diff](changes.diff) 为 0 byte。

---

## 6. 验证 / 实验记录

### 冻结基线

- RMC branch/SHA：`Neural_Network_WW_Iteration` / `6d2087518e0d9f23574d629f5fde361c79f519e4`。
- 独立 Release `ais=OFF` 构建成功；可执行文件、xsdir、`mgxsnp`、`c5g7td` 和 reference SHA256 见 `logs/baseline.txt`。
- `RMC` 状态为空，`changes.diff` 0 byte，reference 与核数据哈希在 `logs/final_integrity_check.txt` 中保持不变。

### Pilot（不进入正式判据）

冻结 pilot manifest SHA256：`e86ed15a0b4122db2d26549878c4a064765b62819737bca1443decfee514ea70`；population=20,000；forward/adjoint 使用不重叠 seed：

| pilot case | 数据 | forward/adjoint seed | 结果 |
|---|---|---:|---|
| `nnubar2_pure` | `10001.01m`，NNUBAR=2 | 101 / 103 | 两侧 exit 0，20,000 source histories，响应有限。 |
| `mixed_nnubar2_nonfissile` | `10001.01m + 10006.01m` | 113 / 127 | 两侧 exit 0，20,000 source histories，响应有限。 |
| `nnubar1_pure` | `10005.01m`，NNUBAR=1 | 107 / 109 | 前向 RE=1；伴随 tally=0，未形成有效配对响应，pilot 失败。 |

首次 pilot 的输入格式解析失败与第二次 NNUBAR=1 物理/统计失败均原样保存。分析脚本曾把 RMC banner 的 forum URL 文本误识别为异常；这只影响任务侧 pilot 检查器，不是 RMC error，且已在门禁判定中与真正的 `exit/source/tally` 结果分开处理。

### 为什么不运行 formal

正式矩阵必须含 NNUBAR=1、NNUBAR>1、真实 density mesh 与强 P1/P2 方向性。当前未完成：

- NNUBAR=1 裂变主导有效群对筛选与 pilot；
- 任务私有 density mesh HDF5 生成/读回 oracle；
- 强 P1/P2 前向/后向角分布数据、方向源/方向响应生成和读回 oracle。

因此任何只基于当前可运行 NNUBAR=2 或标量材料案例的 formal 都会违反用户要求的矩阵，且会错误地把局部通过外推为 A。

**未覆盖**：全部 formal 统计、三种非裂变几何/边界、正式三 density ratio/mesh、完整 mixed-material final response、两材料各三裂变群对、强 P1/P2、OMP、MPI physics consistency、Windows、delayed/AIS/HDF5/CE/GPT/WW。

---

## 7. 结论与遗留

- **结论**：本次独立扩展审查**不建议 A — Ready**；F02 在严格作用域内维持 **C — Verify**。原因不是发现新的已证实 RMC 生产缺陷，而是 A 门槛要求的多个关键维度尚未被实际表达和验证，且预选 NNUBAR=1 pilot 裂变对没有形成有效的双向响应。
- **遗留任务**：另立“验证数据/harness 扩展”任务，先建立并审计私有 MGACE P1/P2 前/后峰数据、density mesh HDF5 写入/读回、NNUBAR=1 裂变群对筛选与多材料裂变矩阵；通过 pilot 后新建、重新冻结 formal manifest，不能复用本任务的 pilot 作为 formal。
- **知识库同步**：F02 仍为 C — Verify；本任务的失败/缺口将登记为 A 门禁未满足，不把它登记为新的 RMC defect。
- **是否已提交**：未 commit/push/切分支；RMC 未修改。

### 供独立审查者复核的 prompt

> 请只读审查 `MLVR_develop/20260825_10_f02-extended-physics-readiness/`。核对 `logs/baseline.txt` 的 RMC SHA/哈希、`logs/coverage_feasibility.csv` 的强制维度、两次 pilot 日志与 `cases/pilot/manifest.json`，确认本任务没有冻结或运行 formal manifest。特别检查：NNUBAR=1 pilot 为何无法得到有效伴随响应；真实 density mesh 与强 P1/P2 方向性是否确有可运行读回证据。判定这些缺口是否足以阻止 standard MGACE fixed-source neutron adjoint 从 C — Verify 升级为 A — Ready；不得把 prior local tests 或本任务 NNUBAR=2 pilot 当作全范围证明。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-25 | 建档、冻结基线、隔离构建。 |
| 2026-08-25 | 数据/输入可行性审计、首次 pilot 格式失败和修正后重跑。 |
| 2026-08-25 | NNUBAR=1 pilot 与 P1/P2/density-mesh 门禁不足，停止 formal、维持 C。 |

## 9. 工作日志

| # | 操作 | 结果 |
|---|---|---|
| 1 | 阅读规则、上下文、工作流、服务器指南 | 确认仅读生产代码和 A 的严格门槛。 |
| 2 | 新建任务、冻结哈希和基线 | 生产树无改动，基线 SHA 正确。 |
| 3 | 检查部署 MGACE 和现有 harness | 发现 7 群表无 NLEG/P1/P2；density mesh 与定向响应没有已验证任务侧生成器。 |
| 4 | 重建当前 RMC | banner SHA 与基线一致。 |
| 5 | pilot | 原始格式失败保留；修正后 NNUBAR=2/mixed 可达，NNUBAR=1 响应不足。 |
| 6 | 冻结门禁结论 | 不产生 formal manifest，不修改 RMC，维持 C。 |
