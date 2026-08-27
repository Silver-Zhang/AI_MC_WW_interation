# f02-formal-evidence-recovery

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-27 |
| 状态 | 待决策 |
| 任务类型 | 物理验证 / 证据恢复 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F02 |
| 涉及文件 | 任务侧 formal generator/checker、证据日志与 F02 分类文档；`RMC/` 仅读 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `6d208751...` + 已冻结 W9 diff；不提交/推送 RMC |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：处理 Claude 独立审核发现的证据可审计性缺口：角表示 40 条和 density-mesh 10 条 formal 的逐运行 raw transport 输出已按旧体积策略清理，只留下汇总；同时角表示 analyzer 最终状态只严格检查 aggregate，未将逐 seed 统计作为强制接受门禁。

**范围**：仅任务侧脚本、私有输入/资产、运行输出和文档。RMC 源码、核数据、reference/benchmark 不修改。运行范围仍限定 Linux x86_64、serial、`ais=OFF`、standard ASCII MGACE、fixed-source neutron forward/adjoint。

**验收标准**：若获准实施，重新生成冻结 formal 输入，以独立 raw checker 从每条 `stdout.log`、`stderr.log`、`inp.out` 和 `exit_code.txt` 验证结构门禁；将原始运行输出保存在任务档案；角表示 checker 强制每 seed 与 aggregate 的冻结统计门槛；任何失败保留原样并维持 C，不修改 RMC。

**原始材料**：Claude 审核结论由用户原样提供；既有 angular/density formal 的 manifest、汇总、HDF5、oracle 与脚本仍在原任务目录。新运行产生的 stdout/stderr/inp.out/exit-code 将原样存入本任务 `logs/`。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：最终 A 复核曾将 F02-B 标为 A — Ready（有界）。Claude 审核没有发现新的 RMC 物理缺陷，却正确指出：运行脚本会写 raw stdout/stderr，但旧任务遵从“logs 不存可再生成的 RMC 运行产物”的约定而清理了它们，导致独立审计无法重建每条结构门禁。审核还确认 `analyze_formal_matrix.py` 的最终 `status` 只检查 aggregate。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `20260826_02.../run_formal_matrix.py` | 每条 angular run 确实生成 `stdout.log`、`stderr.log`、`inp.out`，并从原始输出生成汇总字段；这些 raw 文件当前不在归档。 |
| 2 | `20260826_02.../analyze_formal_matrix.py` | `status` 仅使用 aggregate 的 support、mean、variance/Pearson 门槛，未强制逐 seed 统计。 |
| 3 | `20260827_01.../logs/formal_20260827/` | 保存 HDF5、manifest、formal/statistical report 与哈希，但未保存逐 run 输出。 |
| 4 | Claude 审核（用户提供） | 结论为 C — Verify；要求恢复 raw output 并用独立 checker 重建 formal 证据。 |

**影响面**：这是证据与分类问题，不是新的 RMC 物理 defect。实施成功才允许重新评估 F02 A；实施失败或不实施时，F02 应保持 C — Verify。无 reference/benchmark 更新。

**为什么之前没做/没发现**：旧任务把 RMC 运行目录视为可再生成产物而清理，和“独立复核每个 formal run”需求冲突。随后 final-A 复核过度依赖汇总报告，未审计 acceptance checker 的逐 seed 条件。

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A：完整重跑并保留 raw evidence | 以冻结快照重新生成 40 angular + 10 density formal；保存每条输入、stdout、stderr、inp.out、exit code 与哈希；新独立 checker 强制逐 seed + aggregate 门禁。 | 计算成本最高，但唯一能独立恢复 A 所需的运行证据。 | ★推荐 |
| B：仅修改 analyzer 并复算旧汇总 | 强制逐 seed 统计，但不重跑。 | 只能修正统计工具，不能恢复 raw transport 结构门禁；不足以恢复 A。 | 不推荐 |
| C：接受审核，保持 C | 不重跑，更新分类和文档如实反映证据缺口。 | 无计算成本，但 F02 暂不能作为 A 级基础。 | 可接受 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：待用户选择 A 或 C。
- **决定人 / 日期**：待定。
- **理由与约束**：不得修改 RMC；不得更新 reference/benchmark 或删除失败输出；若选 A，需同意把 50 条 raw formal outputs 作为必要证据保留，不按旧“可再生成产物”规则清理。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 建档并核对审核发现 | 本 README、既有脚本/归档 | 审核发现成立；当前尚未实施重跑。 |

**代码改动**：RMC 无改动。若获准，任务侧新增或调整独立 checker；届时记录准确文件与哈希。

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
| 当前审计 | Claude 审核 + 既有脚本/归档 | 已确认 angular/density raw transport 输出未保存；angular aggregate-only checker 问题成立。 |

```
尚未执行 formal 重跑；不得将既有汇总重新称为独立可审计 A 级证据。
```

**实验设置（若选择方案 A）**：复用原冻结 seed、population、资产/mesh、binary SHA256 与统计阈值；新 checker 的逐 seed 条件须在运行前记录。

**未覆盖到的验证**：当前未恢复 raw formal evidence；故 F02 A 结论不可维持。范围外的 photon、CE、AIS、并行、Windows、反射边界及相邻 F03/F04/F06/F07 仍不在本任务范围。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：待用户决策。当前独立审核支持 F02 为 C — Verify，而非 A。
- **遗留问题 / 后续待办**：选择 A 后完成 raw-evidence rerun；选择 C 后同步下调分类并继续审查 F03。
- **知识库同步**：决策后同步 F02 矩阵、上下文、物理导读和 INDEX。
- **是否已提交**：未提交/推送；RMC 未修改。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-27 20:00 | 立项 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 读取 Claude 审核与现有 formal 工具 | 用户审核文本、angular/density task | 审核所指 raw evidence 与 aggregate-only acceptance 问题均成立。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
