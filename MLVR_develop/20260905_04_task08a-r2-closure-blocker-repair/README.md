# task08a-r2-closure-blocker-repair

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-05 |
| 状态 | 已完成 |
| 任务类型 | 新功能 / 算法实验 / 缺陷修复 / 性能优化 / 文档 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | |
| 关联知识库条目 | TASK08A |
| 涉及文件 | 例：`RMC/src/WeightWindow.h` ／ `AIMC_WWiteration/src/solver.py` |
| 分支 / 提交 | 例：`feat/mlvr-xxx` ／ `abc1234` |

---

## 0. 人类阅读摘要（模式 C 必填；A/B 按需）

**要回答的问题**：修复 Task08A-R2 审计发现的 Numba seed 调用兼容性、非法 consumed seed tuple 接受和 pytest 测试环境缺失，使正式 harness 能够被完整验证，同时证明输运物理和 WW 事件律未被改变。

**当前判断与边界**：修复前 V32 的共享 MC kernel 无法在 Numba nopython 模式编译，V9 接受 `iteration=0`，V31 无法运行完整 pytest。修复目标只覆盖 seed API/调用兼容性、测试依赖和证据；不产生 Task08B publication result，不重定义 Task01–07 物理结论。

**人需要在什么关口确认理解**：本任务已由用户明确授权开始修复、重跑测试和独立审核；必须在复核结论中明确区分 harness 可验证性与科学性能结论。

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：在不改变 Task01–07 输运、tally、伴随、WW 和 PINN 物理行为的前提下，修复 V9/V31/V32 阻塞，并完成全量回归与独立 Task08A-R2-V 复审。

**范围**：`AIMC_WWiteration/src/{experiment.py,mc.py,solver.py}`、seed regression test、测试依赖声明，以及 Claude Task08A-R2-V 证据目录。禁止运行 Task08B。

**验收标准**：Numba forward/adjoint kernel 可编译运行；非法 consumed seed tuples fail loudly；`pytest -q` 零失败零 collection error；Task01–07 focused regression 全部通过；独立 seed/collector/timing/manifest 审核重新运行；Task08A 是否 CLOSED 由所有 hard gates 决定。

**原始材料**：见 `docs/journal_revision/task_08ar2v_formal_harness_claude/assets/closure_matrix.md`、`pytest_full_output.txt` 和 `task01_07_regression_output.txt`；实施过程失败/通过原始输出将写入本任务 `logs/`。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：独立 Task08A-R2-V 发现 V32 的 Numba typing 回归、V9 的 iteration-zero 接口漏洞和 V31 的 pytest 环境缺失；用户随后授权修复并重跑测试。R2 collector/seed/timing 结构继续作为被审查对象，不能把既有报告当作 oracle。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `docs/journal_revision/task_08ar2v_formal_harness_claude/task_08ar2v_formal_harness_claude.md` | 原始 hard-fail 结论：V9/V31/V32。 |
| 2 | `src/mc.py:341-370` | `@njit(parallel=True)` MC kernel 的 seed helper 调用路径。 |
| 3 | `src/experiment.py:49-133` | consumed/base seed API 与 canonical affine helper。 |
| 4 | `assets/pytest_full_output_r2r.txt` | 修复后完整 pytest 的真实输出。 |

**影响面**：涉及 forward/adjoint MC kernel 编译、Task08 seed API、HPO/collocation base seed 调用、测试环境声明和 formal runner 日志路径；不更新历史结果，不运行 Task08B。

---

## 2A. 物理解释与可证伪假设（模式 C 必填）

**问题定式**：MC 每个 batch 必须得到可复现且不碰撞的有效 seed；Numba kernel 必须能实际编译；formal consumed tuple 只能对应冻结的训练/最终批次；全套回归必须可执行。

**可证伪假设**：若修复只改变 seed dispatch/API 边界而未改变物理算法，则 Task03 forward/adjoint kernel 会重新编译运行，Task01–07 regression 不变；若假设错误，则会出现数值回归、seed mismatch 或 Numba typing failure。

**物理—代码因果图**：
```text
root seed + frozen tuple
  ↓
experiment seed namespace/base helper
  ↓
MC affine effective seed → Numba run_mc_chunk → transport tally
  ↓
可复现 batch response；Task03 kernel executable；无物理事件律变化
```

**证据等级与治理标签**：修复前根因 E3；修复后 kernel/pytest/regression E3；独立 seed/collector 复核 E3。已冻结；可复现；边界已定义；原始证据已归档。

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A | | | ★推荐 |
| B | | | |
| C（不做/最小改动） | | | |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：采用最小 V32 Numba 兼容修复、显式 base/consumed seed API 分离、补充 pytest 开发依赖并重跑完整回归；随后更新独立审核，禁止 Task08B。
- **决定人 / 日期**：用户 / 2026-09-05
- **理由与约束**：用户明确授权“请开始修复，然后重跑测试，然后进行独立审核”；不得修改冻结物理算法、不得更新基准、不得运行 Task08B。

**人类理解确认（模式 C 必填，由人确认或转述后确认）**：
- 我理解本任务要判断/修复的物理关系是：每个 MC batch 的随机 stream 必须可执行、可复现且不碰撞；这不是改变输运概率律。
- 我理解当前根因假设是：普通 Python seed wrapper 被 `@njit` kernel 调用导致 V32；iteration-zero 与 consumed tuple 混淆导致 V9；环境缺 pytest 导致 V31。
- 若该假设错误，预期会看到：修复后仍有 Numba typing error、seed formula mismatch、科学回归或 pytest collection failure。
- 本次即使验证通过，仍不能推出：Task08B publication results、method ranking、无偏性或大规模物理性能结论。
- 我批准的范围，以及明确不批准的扩展：批准上述 harness/API/test repair 与 independent audit；不批准 Task08B、历史基准更新和物理算法重构。

**变更卡（模式 B/C 必填）**：
| 项 | 内容 |
|---|---|
| 问题与风险 | V9/V31/V32 阻塞正式 harness closure；seed dispatch 修复若改变公式会破坏 reproducibility。 |
| 拟改动 / 不改动 | 改 `experiment.py` seed API、`mc.py` Numba import、solver base-seed callers、测试依赖与 seed test；不改 transport/tally/WW/PINN law。 |
| 预期因果链 | canonical helper 可被 Numba 编译；consumed tuple fail-loud；pytest 可运行；回归恢复。 |
| 验证与失败停止条件 | 任一 Numba/pytest/regression/independent hard gate 失败则 CLOSED=NO。 |
| 回滚方式（若适用） | 以修复前 `2804471`/`82d759d` 作为审计参照，按 commit 回退修复提交；不覆盖历史结果。 |

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 修复 Numba seed dispatch | `src/experiment.py`, `src/mc.py` | canonical `effective_mc_seed` 加 `@numba.njit`，mc kernel 直接导入；Task03 forward/adjoint 可编译运行。 |
| 2 | 分离 base/consumed seed API | `src/experiment.py`, `src/solver.py` | 新增 `derive_base_seed`；consumed training/final tuples 只接受冻结范围；HPO/collocation 改走 base API。 |
| 3 | 修复 formal log artifact 位置 | `scripts/task08/run_corrected_experiments.py` | iterative `run.log` 改到 `results/task08_logs/`，避免污染 formal candidate directory。 |
| 4 | 准备 pytest 环境 | `requirements-dev.txt`; torch conda env | 安装 pytest 9.1.1；完整 pytest 已执行。 |
| 5 | 独立回归 | `docs/journal_revision/task_08ar2v_formal_harness_claude/assets/*_r2r.txt` | full pytest 38 passed；Task01–07 focused aggregate 0。 |

代码改动快照在最终提交前生成到本任务目录 `changes.diff`。

## 6. 验证 / 实验记录（④ · Agent 填，要贴真实输出）

| 验证项 | 命令 | 结果 |
|---|---|---|
| Seed/Numba smoke | `python tests/test_task08_seed_namespace.py`; `python tests/test_adjoint_transport.py` | `SUMMARY: 7 PASS, 0 FAIL`; `SUMMARY: 12 PASS, 0 FAIL` |
| Full pytest | `python -m pytest -q` | `38 passed in 5.15s`, exit 0 |
| Task01–07 focused | documented persistent scripts + smoke | `SUMMARY: 89 PASS 0 FAIL`; `aggregate_exit=0` |
| Independent seed matrix | `assets/independent_seed_matrix.py` | roots 2026/2027/12026; declared 763200; effective 223200; both collisions 0; range valid |
| Independent collector | `assets/collector_independent_oracle.py` | positive 8x1 exit 0; 16 negative cases all exit 1 |
| Timing oracle | `assets/timing_oracle.py` | `T_e2e_scientific=12`, wall=20, E2E FOM uses 12 |

关键真实输出保存在 `logs/` 与 Claude review assets；完整复核报告在 `docs/journal_revision/task_08ar2v_formal_harness_claude/`。

**实验设置**：root seeds 2026, 2027, 12026；formal planned semantics 30 iterations / 400000 train histories / 50 batches / 400000000 final histories / 100 batches；依赖 Python 3.11.15、pytest 9.1.1、numpy 2.4.6、numba 0.65.1、torch 2.11.0+cu128、h5py 3.14.0；未执行 Task08B。

**未覆盖到的验证**：未执行 400M-history publication matrix；未进行完整真实 dispatcher-to-formal-collector matrix；未动态证明 JIT warm-up 与 formal artifact equivalence。

## 6A. 结果解释卡（模式 C 必填）

| 问题 | 解释 |
|---|---|
| 结果支持/否定了哪个假设？ | 支持 V32 是 Numba dispatch typing 问题、V9 是 base/consumed tuple API 混淆、V31 是环境依赖缺失；修复后 seed/MC kernel 与全回归通过。 |
| 证据等级与治理标签及其依据？ | E3；已冻结、可复现、边界已定义、原始证据已归档。 |
| 通过/失败在物理或工程上分别意味着什么？ | 通过表示 harness API/kernel 可执行且既有 focused tests 未见回归，不表示科学方法性能改善。 |
| 不可外推的边界是什么？ | 不能外推到 Task08B publication ranking、400M 统计性能、无偏性比较或所有平台。 |
| 下一步是否需要升级范围或另立任务？ | 需要重新执行独立 R2-V；若所有 hard gates 通过，再单独授权 Task08B。 |

## 7. 结论与遗留（⑤ 归档）

- **结论**：V9/V31/V32 修复并通过重新运行的 seed、Numba、pytest 和 Task01–07 回归；独立 collector/timing/seed 复核已重跑。
- **遗留问题 / 后续待办**：Task08B 仍未授权；`READY` 不等于 `RUN`，正式期刊矩阵仍需用户单独授权。
- **知识库同步**：Task08A 为原型 harness 任务，未改变 MLVR 物理知识条目；保留 Claude 独立审核报告作为证据。
- **是否已提交**：修复与验证已提交并推送至 `origin/develop`：`1603c70`, `a2d2ca2`, `b61596e`, `67b21f2`, `f06aff2`。

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-09-05 19:39 | 立项 |
| 2026-09-05 20:xx | 用户授权修复；V9/V31/V32 修复完成，full pytest 与 focused regression 通过；独立复审归档完成 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |

**模式 C 必填；A/B 可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
