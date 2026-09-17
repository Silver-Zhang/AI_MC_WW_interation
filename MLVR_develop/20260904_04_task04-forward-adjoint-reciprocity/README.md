# task04-forward-adjoint-reciprocity

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-04 |
| 状态 | 已完成（A — reciprocity corrected and verified，限定范围） |
| 任务类型 | 物理审查 / 缺陷修复 / 数值验证 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | Claude Opus 5 |
| 关联知识库条目 | Task 03 repaired multigroup adjoint normalization |
| 涉及文件 | `AIMC_WWiteration/src/mc.py`、`tests/test_forward_adjoint_reciprocity.py`；Claude 报告/assets |
| 分支 / 提交 | `develop` / 待提交 |

---

## 0. 人类阅读摘要（模式 C 必填；A/B 按需）

**要回答的问题**：当前 repaired forward/adjoint transport，在不启用 WW 的条件下，是否对 code-native source、group coefficient、空间 box average 和角度归一化满足 observable-level reciprocity。

**当前判断与边界**：Task 03 暴露的 adjoint scattering total defect 已修复；Task 04 R1/R2/R3 production MC 在 `|z|≤3` 且 combined relative SE<5% 下通过。A 仅限当前二维两群、非裂变、各向同性散射、均匀 box source、当前 Cartesian mesh/BC 和 code-native scalar observable；不等于完整 WW/iteration/NN 或任意工程 reciprocity。

**人需要在什么关口确认理解**：生产修复已由用户授权；Task 04 结论等待人工确认后进入下一任务。


## 1. 任务定义（① 立项 · Agent 填）

**目标**：独立推导并验证 `<r,L^{-1}q>=<L^{-†}r,q>` 在当前 MC 实现中的 code-native formula；覆盖 selected-group equal/unequal-volume 与 total-group cases；若发现 normalization defect，做最小修复。

**范围**：仅 forward/adjoint reciprocity、source/group/spatial/angular normalization 和 batch-level comparison；新增 deterministic/matrix/MC audit assets；禁止修改 WW、detector estimator、iteration、FOM definition、NN/PINN/U-Net、历史结果。

**验收标准**：G1–G16 required gates；R1–R3 WW-zero MC `|z|≤3`、combined relative SE≤5%；exact A/A.T oracle；Task 01/02/03/smoke regression；production diff only minimal adjoint normalization.

**原始材料**：`logs/exact_matrix_oracle_output.txt`、`logs/reciprocity_mc_output.txt`、`logs/reciprocity_unit_tests_output.txt`、`logs/full_regression_output.txt`。

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：Task 03 已修复 adjoint shared-kernel scattering normalization；Task 04 进一步检查 source response normalization。当前 adjoint source sampling 使用 `c/C`，因此 absolute pairing 需要外乘 `C`；total response `c=ones(G)` 时 `C=2`。

**证据链**：

| # | 位置 | 说明 |
|---|---|---|
| 1 | `src/mc.py:407-430` | adjoint 使用 `S.T`、传入 source spectrum |
| 2 | `src/solver.py:338-345` | solver 用 BOX_OPTIM_TARGET 和 selected delta/total spectrum |
| 3 | `src/utils.py:438-488` | batch response 先 box-average 再算 statistics |
| 4 | `assets/exact_matrix_oracle.py` | independent A/A.T machine-precision check |
| 5 | `assets/run_reciprocity_mc.py` | independent R1/R2/R3 response assembly，WW zero |
| 6 | `assets/reciprocity_mc_output.txt` | R1/R2/R3 all PASS at 500k×50 |

**影响面**：修复只改变 shared-kernel adjoint weight multiplier；forward row sum remains unchanged. Absolute source-strength factor只显式用于 audit pairing，不改变 selected-group iteration/WW code。

## 2A. 物理解释与可证伪假设（模式 C 必填）

**问题定式**：forward response uses detector-box average of group-coefficient-weighted `T/N`; adjoint response uses source-box average of forward-spectrum-weighted adjoint `T/N`, multiplied by `C=sum(c)`. Equal cell volumes and normalized spatial/angular source PDFs must not introduce extra `V_D/V_S` or `4π` factor.

**可证伪假设**：若 formula 正确，R1 selected equal-volume、R2 selected unequal-volume、R3 total-group after `C=2` should be statistically equal with independent seeds; wrong A.T matrix should fail exact oracle; omitting C in R3 should produce the observed ~1/2 scale.

**物理—代码因果图**：

```text
forward source p_f, c, normalized boxes, isotropic angle
  ↓
forward run + adjoint run with S.T and p_adj=c/C
  ↓
Q=T/N_b; batch-first box averages Rf and C*Ra_raw
  ↓
independent means/SE/z
  ↓
observable-level reciprocity verdict
```

**证据等级与治理标签**：exact oracle and deterministic contracts E3; R1–R3 production MC E3; current `未冻结`、`可复现`、`边界已定义`、`原始证据已归档`。

## 3. 方案选项（② 设计/定位 · Agent 填）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A | 先 operator/source derivation，再 WW-zero R1/R2/R3；仅在 defect proof 后改 shared total normalization | 需要 500k×50 CPU 运行 | ★推荐 |
| B | 直接比较当前 source/adjoint outputs，不显式推导 C | 可能把 total source scale defect 隐藏为 global factor | 不推荐 |
| C | 用深穿透论文几何作为唯一 reciprocity gate | analog response 精度不足，无法形成可靠 closure | 不推荐 |

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A（用户授权 Task 04 conditional repair）
- **决定人 / 日期**：用户授权 / 2026-09-04
- **理由与约束**：先证明再修复；WW 完全 neutralized；不修改 detector/WW/iteration/neural/FOM；selected-group path 必须保持。

**人类理解确认（模式 C 必填）**：用户明确要求从 code-native source、response 和 C factor 推导，并将 full reciprocity 限定为 Task 04；最终人工 review 待补。

**变更卡（模式 C 必填）**：

| 项 | 内容 |
|---|---|
| 问题与风险 | 修复前 adjoint total multiplier来自 forward/global semantics，会破坏 observable reciprocity；total source sampling还可能隐藏 C=G factor |
| 拟改动 / 不改动 | 改动仅为 Task 03 shared-kernel normalization；Task 04 新增测试/报告，未改 response/WW/solver |
| 预期因果链 | supplied matrix row total → correct one-collision adjoint operator → R1/R2/R3 reciprocity |
| 验证与失败停止条件 | A/A.T、R1/R2/R3 precision、regressions；任何 hard gate fail 不关闭 |
| 回滚方式 | revert Task 03 repair commit，不影响报告/审计资产 |

## 5. 实施记录（④ · Agent 填）

| # | 操作 | 结果 |
|---|---|---|
| 1 | 检查 starting SHA/clean develop | `46f8ed7`，clean |
| 2 | 读 Task 03/source/response paths | 建立 code-native reciprocity formula |
| 3 | 创建 exact matrix/oracle/normalization assets | 完成 independent checks |
| 4 | 运行 R1–R3 WW-zero MC | 500k histories × 50 batches；3/3 PASS |
| 5 | Task 04 deterministic contracts | 10/10 PASS |
| 6 | 写入 report/assets | production repair only shared normalization |

**代码改动**：最终 production change 属于 Task 03 `src/mc.py`；本 Task 04 未增加 production code。新增 `tests/test_forward_adjoint_reciprocity.py` 和报告/assets。

## 6. 验证 / 实验记录（④ · Agent 填）

```text
Exact A/A.T: PASS; abs error=1.3877787807814457e-17; wrong adjoint rejected
R1: Rf=1.508821239445e-04 Ra=1.507946203029e-04 REf=1.715638e-02 REa=1.658858e-02 z=0.024308 combined=2.386490e-02 PASS
R2: Rf=7.721081758417e-05 Ra=7.351287392706e-05 REf=2.341019e-02 REa=2.582753e-02 z=1.410646 combined=3.478489e-02 PASS
R3: Rf=2.947084516259e-04 Ra=2.875904472803e-04 raw=1.437952236402e-04 C=2 z=1.055535 combined=2.316165e-02 PASS
Task 04 contracts: SUMMARY 10 PASS 0 FAIL
Task 03: SUMMARY 12 PASS 0 FAIL
Task 01: SUMMARY 5 PASS 0 FAIL
Task 02: SUMMARY 9 PASS 0 FAIL
Smoke: SUMMARY 89 PASS 0 FAIL
```

**实验设置**：R1–R3 each 500,000 histories/direction, 50 batches, `ww_zero`, independent direction offsets 0/200000000, seeds/case IDs recorded in script; conda `torch`, Python 3.11.15, NumPy 2.4.6, Numba 0.65.1；不更新 benchmark/reference。

**未覆盖到的验证**：deep penetration paper geometry as hard gate、full anisotropic/fission reciprocity、WW/iteration/neural downstream、absolute physical source-rate reciprocity、R4 boundary-sensitive case 未作为本任务硬门。

## 6A. 结果解释卡（模式 C 必填）

| 问题 | 解释 |
|---|---|
| 结果支持/否定哪个假设？ | 支持 code-native `C` factor、normalized box average 和 isotropic angular cancellation；支持 repaired adjoint operator在R1–R3范围内与forward统计一致 |
| 证据等级与治理标签 | A/A.T E3；R1–R3 E3；可复现、边界已定义、raw evidence archived；最终 closure 等人工确认 |
| 通过/失败意味着什么？ | 通过意味着当前 bounded observable/source contract 下 reciprocity统计闭合；不意味着全MC或WW/adjoint globally validated |
| 不可外推边界 | anisotropic angle、fission、任意几何/partial-cell、WW、iteration、NN、physical absolute source response |
| 下一步 | 人工审核 Task 04；下一步如获准进入 WW audit |

## 7. 结论与遗留（⑤ 归档）

- **结论**：Task 04 证明并修复了前置 adjoint normalization defect的后续observable影响；R1 selected equal-volume、R2 selected unequal-volume、R3 total-group均在 WW-zero、500k×50 下 `|z|≤3` 且 combined relative SE<5% 通过。Task 04 本身无新增 production change。
- **遗留问题 / 后续待办**：完整 reciprocity beyond bounded model、boundary-sensitive R4、anisotropic/fission、physical absolute source normalization、WW semantics 留待后续任务。
- **知识库同步**：未修改知识库；待人工冻结后更新已知问题/方法记录。
- **是否已提交**：待提交；develop；不开始 Task 05。

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-09-04 18:31 | 立项 |

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
