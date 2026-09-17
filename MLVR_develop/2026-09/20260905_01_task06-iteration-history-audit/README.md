# task06-iteration-history-audit

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-05 |
| 状态 | 已完成（A — audit + minimal repair verified） |
| 任务类型 | 缺陷修复 / 统计与数据流验证 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | Claude Opus 5 |
| 涉及文件 | `AIMC_WWiteration/src/solver.py`、`scripts/compute_results.py`、`tests/test_flux_accumulator_history.py`、`tests/test_iteration_dataflow.py`及本目录 assets |
| 分支 / 提交 | `develop` / 待提交 |

---

## 0. 人类阅读摘要

**要回答的问题**：自适应双向迭代中，每轮实际使用的 WW、当前 MC batch、历史累计统计、模型训练和下一轮 WW 是否按正确因果顺序连接；HDF5 是否能区分 current/raw、historical/cumulative 和 AI prediction，并恢复 WW provenance。

**当前判断与边界**：发现并修复了一个确证的 HDF5 provenance defect：Step 8 更新 `_current_adj_ww` 后，原代码在 Step 9 用同一 mutable state 保存 `adj_ww_used`，因此 iter-k 可能记录 W_adj[k+1] 而非实际使用的 W_adj[k]。同时确认 FluxAccumulator 逐 batch Welford 正确、无重复累计、forward/adjoint 池隔离、当前 FOM 使用当前 batch。新增 cumulative fields，使训练实际看到的历史场可审计。结论不覆盖 NN/PINN 科学质量、WW 生成公式、FOM selection bias 或 Task 07/08。

**人类理解关口**：本轮按用户已给出的 Task 06 数学契约和修复范围实施；未改 `src/mc.py`、WW split/roulette、detector estimator、WW scientific formula、FOM definition、模型结构或训练 loss。

## 1. 任务定义

**目标**：验证 adaptive bidirectional iteration 的因果顺序、历史统计、best-WW 配对和 HDF5 provenance，并仅修复已证明的 provenance/persistence 缺口。

**范围**：AIMC_WWiteration 的 `src/solver.py`、`src/learning.py`（只读）、`src/io.py`（只读）、`scripts/compute_results.py` 和 persistent tests；不更新 results/reference。

**验收标准**：数学推导；独立 Welford oracle；deterministic three-iteration solver trace；heterogeneous-WW forward/adjoint oracle；best-WW 和 fallback 静态检查；轻量 2-iteration HDF5 integration；Task 01–05 regressions 和 smoke 通过。

**原始材料**：`logs/baseline.txt` 保存起始仓库状态；`assets/*_output.txt` 保存真实测试输出。

## 2. 调研与设计

### 证据链

| # | 位置 | 说明 |
|---|---|---|
| 1 | `src/solver.py:336-354` | adjoint MC 先于 adj accumulator update；历史统计输入 raw batch。 |
| 2 | `src/solver.py:494-530` | forward MC 后更新独立 fwd accumulator。 |
| 3 | `src/solver.py:532-569` | opt/real response、FOM、best selection 使用当前 `fwd_batch_*`，不是 cumulative map。 |
| 4 | `src/solver.py:648-679` | forward prediction 生成下一轮 adj WW；原状态随后被覆盖。 |
| 5 | `src/solver.py:689-719` | 原 `adj_ww_used`/`fwd_ww_used` 取 mutable current state，且原先没有 cumulative fields。 |
| 6 | `src/learning.py:737-790` | `FluxAccumulator.update()` 对每个 raw batch 独立执行 Welford；零值保留。 |
| 7 | `src/learning.py:107-145` | `DataBuffer` 是遗留类；当前 solver 路径没有调用。 |
| 8 | `scripts/compute_results.py:104-125` | consumer 复制每轮字段；新增 provenance/historical fields。 |

### 物理—代码因果图

```text
W_adj[k] ∈ history-before-k
  ↓ snapshot
run_adjoint_mc → A[k,b] raw normalized batch scores
  ↓ update once per batch
H_adj[k] → cumulative adj field → model_adj[k] → pred_adj[k]
  ↓
W_fwd[k] → snapshot → run_forward_mc → F[k,b]
                         ├→ current response/FOM/best-WW
                         └→ H_fwd[k] → cumulative fwd field → model_fwd[k] → pred_fwd[k]
                                                                            ↓
                                                                         W_adj[k+1]
```

### 统计论证

若 `W_k` 只依赖此前 history，且 `E[X_k | F_{k-1}] = μ`，则 `D_k=X_k-μ` 是 martingale difference，因而 `E[N⁻¹ΣX_k]=μ`。不同 WW 可造成异方差，但不自动造成 expectation bias。这里仅证明 equal-weight batch history 的无偏性，不声称其在异方差下方差最优，也没有引入 inverse-variance weighting。

### 方案选项与决策

| 方案 | 做法 | 代价 / 风险 | 选择 |
|---|---|---|---|
| A | 在实际 MC 调用点 snapshot WW；保存 used/next；持久化 cumulative fields；补 deterministic tests | HDF5 增长，consumer schema 增加字段 | ★采用 |
| B | 仅改字段命名/报告，不保存历史场 | provenance 仍无法重建训练输入 | 不采用 |
| C | 重设计迭代或改历史统计权重 | 超出 Task 06，改变科学方法 | 不采用 |

## 3. 确认的缺陷与修复

### P9 — `adj_ww_used` provenance defect

原流程在 iter-k 的 Adjoint MC 使用 `_current_adj_ww`，随后 forward model prediction 可能更新 `_current_adj_ww` 为下一轮 map，Step 9 又保存 `_current_adj_ww`。因此 `adj_ww_used` 可能与真实调用参数不一致，且原 `adj_ww_next` 也可能与 used map 相同。

修复：

- iter 开始 `adj_ww_used = self._current_adj_ww.copy()`，MC 使用 snapshot；
- forward MC 前 `fwd_ww_used = self._current_fwd_ww.copy()`，MC 使用 snapshot；
- Step 8 生成后 `adj_ww_next = self._current_adj_ww.copy()`；
- HDF5 分别保存 `adj_ww_used`、`fwd_ww_used`、`adj_ww_next`；
- fallback/no-next-update 时，保存 unchanged next snapshot（仅非 final iteration）。

### P10 — historical-field persistence gap

原 solver 用 cumulative fields 训练，但 HDF5 只保存 current `adj_flux_g`/`fwd_flux_g`，无法重建本轮 training 实际看到的 history。修复新增：

```text
adj_acc_flux_g, adj_acc_re_g,
fwd_acc_flux_g, fwd_acc_re_g
```

保留原 current fields，不改变其语义；`compute_results.py` 同步复制新增字段和 `adj_ww_next`。

## 4. 验证 / 实验记录

### Accumulator exact oracle

```text
H1 mean == concatenate: PASS
H2 M2/sample variance: PASS
H3 RE == production oracle: PASS
H4 zero batch retained: PASS
H5 update chunks == one update: PASS
H6 n_batches_total: PASS
H7 adj/fwd pools independent: PASS
SUMMARY: 7 PASS, 0 FAIL
```

最大误差：

```text
max mean error = 1.421e-14
max variance error = 3.638e-12
max RE error = 2.220e-16
N = 7 synthetic raw batches
```

### Deterministic solver trace

```text
SUMMARY: 19 PASS, 0 FAIL
```

sentinel trace：

```text
iter1: adj-used=11, fwd-used=22, adj-next=33
iter2: adj-used=33, fwd-used=44, adj-next=55
iter3: adj-used=55, fwd-used=66, no unused next map
```

同时验证：每轮 cumulative count 为 `2,4,6`；历史 fields 存在；current/historical fields 不混淆；best WW 不被 current iteration look-ahead 使用；final WW 与记录的 best map 配对。

### Historical heterogeneous-WW MC oracle

固定合法 map sequence：neutral、group-dependent、spatial-dependent；每轮 8 batches、总 24 history batches；neutral reference 为 50 batches。

```text
forward batches=24 n=24 max_mean_err=2.082e-17 max_var_err=2.711e-20 max_re_err=1.110e-15
forward reference=4.913551310409e-02 accumulated=4.969146072090e-02 z=2.424625 combined_rel_SE=4.614318e-03
adjoint batches=24 n=24 max_mean_err=1.388e-17 max_var_err=3.388e-20 max_re_err=1.443e-15
adjoint reference=2.348897844349e-02 accumulated=2.355679224689e-02 z=0.277046 combined_rel_SE=1.039084e-02
```

两条 history 均满足 `|z|<=3` 且 combined relative SE <5%。

### Adaptive martingale oracle

```text
trials=20000 mean=3.00124773 expected=3.00000000 SE=0.00281324 z=0.443520
PASS
```

### Lightweight integration

```text
exit=0
iter_1: adj_ww_used=True fwd_ww_used=True adj_ww_next=True adj_acc_flux_g=True fwd_acc_flux_g=True counts=2,2
iter_2: adj_ww_used=True fwd_ww_used=True adj_ww_next=False adj_acc_flux_g=True fwd_acc_flux_g=True counts=4,4
```

运行配置：`plain_dnn`、2 iterations、100 train particles × 2 batches、100 final particles × 2 batches、1 CPU core；仅功能验证，不是科学结果。

依赖环境：conda `torch`，Python 3.11；NumPy、Numba、PyTorch、h5py、matplotlib 为该环境现有版本；Task 06 未更新 benchmark/reference。

## 5. G1–G20

| Gate | Result |
|---|---|
| G1 mathematical iteration contract | PASS |
| G2 adaptive conditional-unbiasedness derivation | PASS |
| G3 Welford exact mean | PASS |
| G4 Welford exact variance/RE | PASS |
| G5 zero batches retained | PASS |
| G6 no history double-count | PASS |
| G7 adj/fwd history isolation | PASS |
| G8 current metrics independent of history | PASS |
| G9 adj[k] WW handoff | PASS after snapshot repair |
| G10 fwd[k] WW handoff | PASS after snapshot repair |
| G11 next-adj[k+1] handoff | PASS after snapshot repair |
| G12 no best look-ahead | PASS |
| G13 best copy/final provenance | PASS |
| G14 HDF5 adj_ww_used provenance | PASS after repair |
| G15 HDF5 adj_ww_next provenance | PASS after repair |
| G16 historical training fields auditable | PASS after repair |
| G17 heterogeneous-WW history oracle | PASS |
| G18 fallback state consistency | B — static path checked; no separate forced-failure production run |
| G19 Task01–05 regressions | PASS |
| G20 smoke/integration regression | PASS |

## 6. PRE-REPAIR classification

| 项目 | 分类 | 依据 |
|---|---|---|
| P1 iteration causal order | A | actual call order is adjoint → forward → next adjoint |
| P2 adj→fwd handoff | A | prediction precedes forward MC |
| P3 fwd→next-adj handoff | A | prediction follows forward MC/history update |
| P4 FluxAccumulator mathematics | A | independent exact oracle |
| P5 adaptive-history validity | B | conditional-unbiased argument + MC oracle required |
| P6 no double count | A | raw batches only; no DataBuffer call path |
| P7 current/historical metric separation | A | FOM/response consume current batch arrays |
| P8 best-WW causality | A | best updated only after current FOM |
| P9 HDF5 WW provenance | D | mutable current map mislabeled used/next |
| P10 historical-field persistence | B | training history not persisted, provenance gap |
| P11 fallback semantics | B | code preserves current valid maps; limited dynamic coverage |

Overall pre-repair: **D — confirmed scientific provenance defect**.

## 7. POST-REPAIR classification

- P1–P8: A/B unchanged and verified.
- P9: A — snapshot semantics and HDF5 trace verified.
- P10: A — cumulative fields persisted and copied by consumer.
- P11: B — fallback semantics statically consistent; forced-failure branch is not a large-MC gate.

Overall: **A — corrected and verified within the stated prototype scope**.

## 8. Restrictions and open items

- No Task 06 repair was made to Task 05 conservative stack capacity inequality.
- No inverse-variance weighting was introduced.
- No model warm start, replay buffer, training/loss/PDE change, WW formula change, detector estimator change or FOM definition change.
- `DataBuffer` remains unused legacy code and was not deleted.
- Historical MC oracle uses moderate geometry and fixed legal maps, not NN-generated WW.
- Full extreme-WW stress, larger platform matrices, anisotropic/fission cases and journal-scale reruns remain out of scope.
- Winner's curse / selection bias of best training FOM is deferred to Task 08.
- Do not start Task 07.

## 9. 结论与提交

Task 06 的确证问题是 WW HDF5 provenance 和 historical-field persistence，而不是 MC bias 或 accumulator mathematics。最小修复已完成，persistent exact/dataflow tests、heterogeneous history oracle、lightweight HDF5 integration、Task 01–05 regressions 和 smoke 均通过。已提交并 push：`7c87fa2ebb5c058857f4bdff54813991f95072b9`。

**知识库同步**：Task 06 结论属于 AIMC_WWiteration journal-revision 独立档案；未修改 RMC 知识库条目，因为本任务没有改变 RMC capability 结论。

**原始证据**：见 `assets/`；生产快照见 [changes.diff](changes.diff)。

## 10. 时间线 / 工作日志

| 时间 | 事件 |
|---|---|
| 2026-09-05 | 固定 baseline `7c9a2d29...`，创建 Task 06 C 档案 |
| 2026-09-05 | 静态追踪 solver、accumulator、DataBuffer、HDF5 consumers |
| 2026-09-05 | 发现 `adj_ww_used` mutable-state provenance defect 和 historical persistence gap |
| 2026-09-05 | 新增 exact accumulator oracle 与 deterministic solver trace |
| 2026-09-05 | 实施 snapshot/cumulative-field 修复，新增 consumer field list |
| 2026-09-05 | 完成 heterogeneous-WW、martingale、2-iteration HDF5 integration 和 Task01–05/smoke regressions |
