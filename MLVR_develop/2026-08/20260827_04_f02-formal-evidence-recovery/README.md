# f02-formal-evidence-recovery

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-27 |
| 状态 | 已完成（独立复核接受，F02 恢复有界 A） |
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

- **采纳方案**：A — 完整重跑并保留 raw evidence。
- **决定人 / 日期**：用户 / 2026-08-27（“先整理一下repo，然后提交同步进度，然后按照计划完成方案A”）。
- **理由与约束**：不得修改 RMC；不得更新 reference/benchmark 或删除失败输出；50 条 raw formal outputs 是本任务必要证据，明确例外于旧“可再生成产物”清理规则。Angular 与 density 均复用冻结 seeds、population、数据资产、输入语义和 binary SHA256；独立 checker 必须强制每 seed 与 aggregate 的结构/统计门槛。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 建档并核对审核发现 | 本 README、既有脚本/归档 | 审核发现成立。 |
| 2 | 冻结方案 A | README 第 4 节 | 用户明确批准完整重跑和 raw evidence 保留。 |
| 3 | 编写独立 raw runners/checkers | 本任务四个 Python 脚本 | 不修改 RMC；分别保留 angular/density 原始输出，并强制 angular 逐 seed + aggregate 门禁。 |
| 4 | 工具首轮反例 | `logs/angular_formal_raw_20260827/`、`logs/density_formal_raw_retry1_20260827/` | 两个 runner 先后暴露 task-side `str.parent` 路径错误；angular 首次 retry 又暴露相对 GDB probe 路径错误；density 首次 retry 暴露 tally 实际写入 `inp.Tally`。失败目录原样保留，不计入 formal。 |
| 5 | angular raw formal 重跑 | `logs/angular_formal_raw_retry1_20260827/` | 40/40 structural pass；每条保留 `inp`、stdout、stderr、`inp.out`、exit-code、GDB 输出和返回样本。 |
| 6 | density raw formal 重跑 | `logs/density_formal_raw_retry2_20260827/` | 10/10 structural pass；每条保留 `inp`、stdout、stderr、`inp.out`、`inp.Tally`、exit-code。 |
| 7 | 严格独立统计 | 两个 strict checker | angular 每 seed + aggregate 全部通过；density 五对及合并全部 $|z|\le3$。 |
| 8 | 重建与回归 | `/tmp/mlvr_f02_rmc_build` | 重新构建仍得到 binary `8fff...f13c2`；`test_fixed_source_adjoint` 1/1 passed。 |
| 9 | 独立复核 | GPT poly-bridge | 先指出 `SHA256SUMS.txt` 的两条裸计数行使 `sha256sum -c` 非零；修正后四份报告哈希均验证成功，复核接受恢复有界 A。 |

**代码改动**：RMC 无改动。任务侧新增 `run_angular_formal_raw.py`、`check_angular_formal_strict.py`、`run_density_formal_raw.py`、`check_density_formal_strict.py`。`.gitignore` 明确忽略可再生成的 `inp.PTRAC` 大文件；审核所需输入、stdout、stderr、`inp.out`、tally、exit-code、报告和哈希均保留。

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
| angular raw structural | `run_angular_formal_raw.py` | 40/40：exit 0、stderr 0、异常扫描 0、Finish 1；raw report SHA256 `92e3b595...ceb97fa4`。 |
| angular strict statistical | `check_angular_formal_strict.py` | 八个 case/mode 组合均通过；每 seed 和 aggregate 分别强制支持域、$|z|\le3$、variance 或 Pearson 门槛；报告 SHA256 `4e191d19...747cf3e3`。 |
| density raw structural | `run_density_formal_raw.py` | 10/10：exit 0、Source Number=50000、stderr 0、Warning/Error=0、Finish 1、有限正 tally；raw report SHA256 `032ad204...9ce50fb1`。 |
| density strict statistical | `check_density_formal_strict.py` | 五 seed 都满足 $|z|\le3$，合并 $z=0.0946746946$；报告 SHA256 `ea7098df...706b191`。 |
| binary/rebuild/regression | `cmake --build ...`、CTest | base `6d208751...` + diff `5eec92f9...c756` 重建得到 binary `8fff3f0f...f13c2`；`test_fixed_source_adjoint` 1/1 passed。 |
| checksum manifest | `sha256sum -c logs/SHA256SUMS.txt` | 四份 angular/density raw/strict report 均“成功”；独立复核接受该完整性闭环。 |

```
```text
angular_raw_runs=40
density_raw_runs=10
binary_sha256=8fff3f0f534d2a2a116e033a26cf4bb62005c5b6d62b29925423b97bb74f13c2
rmc_head=6d2087518e0d9f23574d629f5fde361c79f519e4
rmc_diff_sha256=5eec92f929ca93caaabeaacd64d5c92f44f1dc89c61c11997ab962fe8957c756
1/1 Test #62: test_fixed_source_adjoint ... Passed
```
```

**实验设置**：angular 为四类 × forward/adjoint × seeds `17,23,41,59,83`、50,000 histories/run、1,000 GDB 生产样本/run、density `1.0`；density 为 forward/adjoint × 同五 seeds、50,000 histories/run、HDF5 `density=[0.5,2.0]` g/cm³。RNG type 2、stride `1000000`；Python 3.12.3、GDB 15.1、HDF5 C 工具链。

**未覆盖到的验证**：范围外的 photon、CE、AIS、并行、Windows、反射边界及相邻 F03/F04/F06/F07 仍不在本任务范围。工具首轮失败不属于 RMC 失败；已保留但不作为 formal。待独立复核本任务的 raw reports 后才重新裁定 F02 分类。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：方案 A 已完整执行。40 angular 与 10 density formal 的每条 raw evidence 均已归档；angular 强制每 seed + aggregate，density 强制五对 + aggregate；checksum manifest 可由 `sha256sum -c` 完整验证。独立复核接受将有界 F02 恢复为 **A — Ready**。
- **遗留问题 / 后续待办**：F03 及后续独立能力按既定顺序审查；范围外能力不继承 F02 A。
- **知识库同步**：已恢复 F02 有界 A，并记录证据恢复任务。
- **是否已提交**：未提交/推送；RMC 未修改。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-27 20:00 | 立项 |
| 2026-08-27 | 用户批准方案 A；重跑 50 条 formal，保留 raw evidence，并通过严格 checker。 |
| 2026-08-27 | 独立复核先发现 checksum manifest 格式问题；修复后四份报告哈希全部通过，接受恢复有界 A。 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 读取 Claude 审核与现有 formal 工具 | 用户审核文本、angular/density task | 审核所指 raw evidence 与 aggregate-only acceptance 问题均成立。 |
| 3 | 用户批准方案 A | 用户请求 | 授权重跑并保留审核必须的 raw evidence。 |
| 4 | 写 runner/checker 并做语法/资产预检 | task scripts、private MGACE、HDF5 writer | Python 编译、两群 asset 生成、HDF5 schema 列表通过。 |
| 5 | angular 首轮与 retry1 失败 | raw logs | 先后发现 Path 转换和相对 probe 路径错误；未误称为 RMC failure。 |
| 6 | angular retry1 40 条重跑 | raw logs | 40/40 structural pass；strict checker 因未缓存 bootstrap 过慢，终止后加内存缓存并完整重跑 checker。 |
| 7 | density 首轮与 retry1 失败 | raw logs | 先后发现 Path 转换和 tally parser 目标文件错误；raw stdout 表明 RMC 实际运行 clean。 |
| 8 | density retry2 10 条重跑 | raw logs | 10/10 structural pass，strict reciprocity 通过。 |
| 9 | 重建、CTest、hash/体积审查 | build、logs、`.gitignore` | 二进制身份不变；PTRAC 是可再生成大产物而非审核要求，忽略；其余 raw evidence 保留。 |
| 10 | 独立复核与 checksum 修复 | GPT poly-bridge、`SHA256SUMS.txt` | 裸 `40/10` 计数行会使 checksum CLI 非零；重写为严格四条 hash manifest 后，复核接受 A。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
