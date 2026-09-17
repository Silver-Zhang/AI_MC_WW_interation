# task01r-mesh-tally-repair-claude

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-04 |
| 状态 | 已完成（A — Repair verified，限定 exact per-cell tally） |
| 任务类型 | 缺陷修复 / 物理验证 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | Claude Opus 5 |
| 涉及文件 | `AIMC_WWiteration/src/mc.py`；Claude 报告与资产位于 `docs/journal_revision/task01r_mesh_tally_repair_claude/` |
| 分支 / 提交 | `task01r-claude` / 待提交 |

## 结论

基于固定 baseline `6b7bc27a5c3651d1c18d6f63e96d19aea26f4924`，独立实现 `@njit` Cartesian DDA scorer，替换 midpoint-only tally。D1–D3 deterministic matrix、独立 AABB slab oracle 的 10,000 条 randomized differential、path conservation、group isolation、no scorer RNG、no scalar state mutation 和 existing smoke regression 均通过。

真实关键输出：

```text
randomized differential: N=10000 failures=0 max_cell_err=1.709e-10 mean_cell_err=1.235e-13 max_total_err=3.638e-12 touched_mismatches=0
fixed trace totals repaired=9.225000000000 old=9.225000000000 expected=9.225000000000 cellwise_different=True
noninvasiveness: scorer_random_calls=False scalar_state_unchanged=True tally_sum=0.425000000000
benchmark segments=20000 old_midpoint_s=0.025740 exact_dda_s=0.048190 slowdown=1.87x
SUMMARY: 89 PASS  0 FAIL
```

Final classification: **A — Repair verified**, strictly limited to exact per-cell scorer repair on the tested rectangular in-domain mesh contract. No claim is made about adjoint, WW, detector response, RE, FOM, neural models, iteration, or paper results.

## 变更与证据

- Production diff: [`changes.diff`](changes.diff)
- Raw verification outputs（2026-09-17 从 Claude 工作副本补录）: [`logs/`](logs/) —— `verify_exact_tally_output.txt`（exact tally 全矩阵 PASS + 10,000 条 randomized differential）、`smoke_test_output.txt`（89 PASS 0 FAIL）
- Claude report: `AIMC_WWiteration/docs/journal_revision/task01r_mesh_tally_repair_claude/task01r_mesh_tally_repair_claude.md`（**该路径在 AIMC 工作区与已提交历史中均不存在，引用待修复**）
- Existing relevant smoke test: `tests/smoke_test.py` → `89 PASS 0 FAIL`

## 范围外

未修改或审查 Codex 实现；未修改 develop；未审查/修改 adjoint、WW/split/roulette、detector response/RE、FOM、DNN/PINN/U-Net、HPO、accumulator、历史结果或会议论文结果。大型 MC、非均匀网格、任意几何和下游影响需另立任务。

## 人工关口

等待人工将 Claude 与 Codex 独立实现和证据并列比较，再决定 develop 采用哪套实现；本分支不 merge/push develop。
