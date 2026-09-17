# task02r-final-metrics-pipeline-repair

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-04 |
| 状态 | 已完成（A — Repair implemented and locally verified） |
| 任务类型 | 缺陷修复 / 结果管线验证 |
| 任务模式 | B — 工程协作（默认） |
| 报告人 | Claude Opus 5 |
| 关联知识库条目 | Task 02 detector metrics serialization defect |
| 涉及文件 | `AIMC_WWiteration/src/solver.py`、`scripts/gen_table3.py`、`tests/test_final_metrics_pipeline.py`及 Claude 报告/assets |
| 分支 / 提交 | `develop` / 待提交 |

---

## 0. 人类阅读摘要（模式 C 必填；A/B 按需）

**要回答的问题**：Final Run 已正确计算的 detector batch-response metrics 是否完整写入 HDF5，并由 Table-3 consumer 以 HDF5 authoritative scalar 为首选，避免静默退化为 mean(cell-wise RE)。

**当前判断与边界**：修复完成：trained solver 写入 authoritative scalar；gen_table3 HDF5 优先、兼容中英文旧日志、禁用 cell-wise RE fallback；synthetic pipeline 与前置回归通过。只覆盖 serialization/parsing/result-consumer contract，不重新设计 detector estimator，不判断 FOM scientific definition。


## 1. 任务定义（① 立项 · Agent 填）

**目标**：建立 Final detector metrics contract：正确 Final statistics → HDF5 authoritative scalar fields → post-processing → gen_table3 → Table 3；禁止自动使用 mean(cell-wise RE)。

**范围**：仅 `src/solver.py`、`scripts/gen_table3.py`、`tests/test_final_metrics_pipeline.py` 和 Claude-owned report/assets；不修改 detector estimator、MC、WW、adjoint、FOM definition、network 或历史结果。

**验收标准**：solver 写出 8 个 scalar；HDF5 优先于冲突日志；英文/中文日志兼容；无 scalar/no log 返回 unavailable 而不读取 cell-wise map；FOM consistency、optim_group、端到端 synthetic 和既有回归通过；production diff 窄。

**原始材料**：`logs/regression_output.txt`、`logs/test_final_metrics_pipeline_output.txt`、`logs/solver_serialization_output.txt`。

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：trained solver `_run_final` 已计算 `final_box_flux/final_box_re/final_resp_samples/real_final_flux`，但旧 `final_data` 未写 detector scalar；`gen_table3` 读取失败后可 fallback 到 cell-wise RE map。

**证据链**：

| # | 位置 | 说明 |
|---|---|---|
| 1 | `src/solver.py:939-966` | Final elapsed、batch response 和 detector flux 已在同一流程计算 |
| 2 | `src/solver.py:981-997` | 写入 authoritative scalar schema；`optim_group=None` 存为 -1 |
| 3 | `scripts/gen_table3.py:181-210` | HDF5 scalar 优先，缺失时才兼容日志；不再 map fallback |
| 4 | `tests/test_final_metrics_pipeline.py` | 9 个 synthetic contract tests |
| 5 | `assets/solver_serialization_test.py` | mock forward batches 验证 8 个 schema fields |

**影响面**：影响 Final HDF5 provenance 和 Table-3 consumer；不会改变 response estimator、MC physics 或历史结果数值。

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A | Solver 持久化 scalar；consumer HDF5 优先，兼容日志；移除自动 cell-wise fallback | 旧无 scalar/log 文件不可用，需人工重跑或标记 unavailable | ★推荐 |
| B | 保留 cell-wise RE 平均 fallback | 违反 detector covariance 统计定义 | 不推荐 |
| C | 只改日志输出，不扩充 HDF5 schema | 机器可读 provenance 仍缺失 | 不推荐 |

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A（用户已明确授权 Task 02-R 窄范围修复）
- **决定人 / 日期**：用户授权 / 2026-09-04
- **理由与约束**：HDF5 authoritative；日志仅兼容；不修改 detector estimator mathematics、MC、WW、adjoint 或 FOM definition。

**变更卡（模式 B/C 必填）**：

| 项 | 内容 |
|---|---|
| 问题与风险 | trained solver 缺 scalar，Table 3 可能将 cell-wise RE 平均当 detector RE |
| 拟改动 / 不改动 | 改 solver serialization、gen_table3 priority/fallback、加 pipeline tests；不改统计估计器 |
| 预期因果链 | Final scalar → HDF5 authoritative → consumer read → correct Table 3 row |
| 验证与失败停止条件 | T1–T8、solver mock、mesh/smoke/Codex/Claude audit；任何 map fallback 可达则停止 |
| 回滚方式 | revert repair commit；历史结果不修改 |

## 5. 实施记录（④ · Agent 填）

| # | 操作 | 结果 |
|---|---|---|
| 1 | 固定 starting HEAD `4462e508...` | clean develop baseline |
| 2 | 修改 `src/solver.py` | single-source final_time；写 8 个 authoritative scalars |
| 3 | 修改 `scripts/gen_table3.py` | HDF5 priority；中英文 log fallback；移除 map fallback；FOM consistency |
| 4 | 新增测试与 mock serialization asset | T1–T8/T8b、8 schema fields |
| 5 | 保存 report/assets/logs | raw outputs archived |

**代码改动**：生产文件仅 `src/solver.py`、`scripts/gen_table3.py`；测试新增 `tests/test_final_metrics_pipeline.py`；`compute_results.py` 已检查无需改动。

## 6. 验证 / 实验记录（④ · Agent 填）

```text
Task 02-R pipeline: SUMMARY: 9 PASS, 0 FAIL
Solver serialization: PASS solver authoritative scalar schema
Mesh tests: SUMMARY: 5 PASS 0 FAIL
Repository smoke: SUMMARY: 89 PASS  0 FAIL
Codex Task 02: ALL SYNTHETIC TASK 02 AUDIT CHECKS PASSED
Claude Task 02: SUMMARY: 11 PASS, 0 FAIL
```

**实验设置**：无大规模 MC；solver test 使用 4 mock batches；依赖 Python 3.11.15、NumPy 2.4.6、Numba 0.65.1、h5py/torch existing env；未更新 benchmark/reference。

**未覆盖到的验证**：真实 4e8 Final Run、完整 Table 3 重新生成、FOM scientific suitability、response/WW/adjoint 未覆盖。

## 6A. 结果解释卡（模式 C 必填）

| 问题 | 解释 |
|---|---|
| 结果支持/否定了哪个假设？ | 支持 scalar persistence + HDF5 priority 可阻止 cell-wise RE fallback |
| 证据等级与治理标签及其依据？ | E2–E3：mock schema、synthetic consumer、prior regressions；raw evidence archived |
| 通过/失败意味着什么？ | serialization/consumer contract 正确；不表示 detector physics/FOM 已重审 |
| 不可外推边界 | 不外推到真实大型 MC、历史结果或论文结论 |
| 下一步 | 等人工审核；不要开始 Task 02-V 或 Task 03 |

## 7. 结论与遗留（⑤ 归档）

- **结论**：Task 02-R 修复完成，solver 写 authoritative final detector metrics；gen_table3 HDF5 优先，兼容两种日志，并不再自动读取 cell-wise RE map。全部 pipeline、solver schema、mesh、smoke、Codex 和 Claude audit 通过。
- **遗留问题 / 后续待办**：旧无 scalar/log 文件显示 unavailable；非对齐 detector box、非整除 particle count、sentinel RE 仍是已知 limitations。
- **知识库同步**：未修改知识库；待人工确认是否登记 pipeline contract。
- **是否已提交**：待提交；develop；不 push 前不做正式 Table 3 重算。

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-09-04 16:55 | 立项 |

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
