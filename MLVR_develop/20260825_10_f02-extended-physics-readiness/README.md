# f02-extended-physics-readiness

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-25 |
| 状态 | 实施中：先行可行性审计与 pilot |
| 任务类型 | 物理验证 / 现有能力审查 |
| 报告人 | Claude |
| 关联知识库条目 | F02 / W5 / W6 / W7 |
| 作用域 | standard MGACE + FIXEDSOURCE + neutron adjoint + `ais=OFF` |
| RMC 基线 | `Neural_Network_WW_Iteration` / `6d2087518e0d9f23574d629f5fde361c79f519e4` |

---

## 1. 任务定义

**目标**：在 W5/W6/W7 已修复的当前 RMC 上，执行独立、预冻结、可复现的扩展物理验证，判断严格作用域内的 F02 是否可评为 A — Ready。目标不是设法给出 A：任一失败、确定性错误、不可表达的必需矩阵维度或证据不足都保留/降低 C — Verify。

**范围**：只读 `RMC/` 生产代码；任务目录内生成验证输入、解析脚本、私有验证数据（仅在必要时）、日志和统计结果。明确排除 continuous-energy、photon、AIS/HDF5、GPT、delayed precursor、WW 组合和完整 MLVR。

**验收标准**：只有正式矩阵中散射、密度/空间非均匀、混合材料、NNUBAR=1 与 >1 裂变、强各向异性、几何/边界与稳健性均能被实际表达、通过冻结结构与统计判据，且无未闭合机制问题，才可建议 A — Ready。否则如实保持 C — Verify 或按错误降级。

**原始材料**：`logs/` 原样保存冻结基线、可行性审计、pilot、正式 manifest、命令、stdout/stderr、退出码、哈希、分析输出和最终完整性检查。

---

## 2. 调研与设计

**背景**：既有任务已提供 W5 非均匀密度响应级证据、W6 total-nubar 核一致性与 bank 可达性、W7 初始化修复、非裂变 H/O 两群对及 `10001.01m` g6↔g1 可裂变响应证据。它们不足以覆盖混合组成、真实密度 mesh、强 P1/P2 定向响应、多材料裂变和更广几何边界。

**证据链**：

| # | 位置 | 作用 |
|---|---|---|
| 1 | `RMC/src/TreatAdjointMaterial.cpp`、`SampleColliType.cpp`、`GetExitState.cpp` | 伴随散射/裂变核、抽样与权重机制。 |
| 2 | `MLVR_develop/20260825_08_f02-fissile-response-reciprocity-verification/` | 已完成的独立裂变响应基线，不混入本任务正式矩阵。 |
| 3 | `MLVR_develop/20260825_06_f02-w5-nonuniform-density-reciprocity-verification/` | 非均匀密度响应级先例。 |
| 4 | `MLVR_develop/20260825_01_f02-adjoint-numerical-verification/` | ASCII MGACE 1-based parser、群筛选和统计分析先例。 |

**影响面**：不改 RMC/reference/benchmark/核库；仅改变对 F02 当前证据等级的判断以及相关文档，且仅在结论最终形成后同步。

---

## 3. 方案

| 方案 | 做法 | 风险 | 采用条件 |
|---|---|---|---|
| A | 部署核数据和输入语法可覆盖全部冻结矩阵，pilot 后执行完整 formal | 成本高，要求每个机制真实可表达 | 仅 pilot 全覆盖通过时采用 |
| B | 部署数据先行；不可表达的必需机制用任务私有 MGACE + 读回 oracle | 必须验证私有数据格式及 RMC 消费路径 | 仅能准确生成并读回时采用 |
| C | 必需机制不可表达或 pilot 不通过，保留 C — Verify | 不产生 A 结论 | 默认安全路径 |

---

## 4. 决策（用户授权）

- **采纳方案**：按 A→B→C 的门禁顺序执行；先可行性审计，再 pilot；只有 pilot 对所有必需维度成功才冻结 formal manifest。
- **决定人 / 日期**：用户，2026-08-25。
- **授权与约束**：授权自主设计/执行只读生产代码的扩展验证、任务侧输入/脚本及必要服务器计算；禁止修改 RMC、reference、benchmark、核数据，禁止 commit/push/切分支，禁止观察结果后挑 seed、删除失败或改判据。若出现生产缺陷，保留最小复现、登记问题、另立修复任务并停在决策门禁。

---

## 5. 实施记录

| # | 操作 | 位置 | 结果 |
|---|---|---|---|
| 1 | 建立独立任务档案 | `new_task.sh f02-extended-physics-readiness F02` | 成功。 |
| 2 | 冻结当前生产基线和数据/可执行文件哈希 | `logs/baseline.txt` | 待记录。 |
| 3 | 部署核数据与输入能力可行性审计 | `coverage_feasibility.*` | 待执行。 |
| 4 | pilot | `cases/pilot/` | 只有可行性门禁通过后执行。 |
| 5 | formal manifest | `cases/formal/manifest.json` | 仅 pilot 全覆盖通过后生成并冻结。 |

---

## 6. 验证 / 实验记录

真实命令、输出、数据哈希、pilot/formal 结果和未覆盖项写入本节及 `logs/`；不得以 smoke 或 locator oracle 替代响应级物理验证。

## 7. 结论与遗留

待所有门禁完成后填写。若任一必需维度不可表达、未覆盖或失败，将明确保持 C — Verify 或降级。

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-25 | 立项；冻结前可行性审计开始。 |

## 9. 工作日志

| # | 操作 | 结果 |
|---|---|---|
| 1 | 建档与读取规则、当前上下文、开发流程、服务器指南 | 建立严格 A 门槛与禁止修改边界。 |
