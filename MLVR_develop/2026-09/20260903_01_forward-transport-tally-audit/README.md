# forward-transport-tally-audit

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-03 |
| 状态 | 已完成（D — Defect，限定 cell-wise tally） |
| 任务类型 | 物理审查 / 数值验证 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | Claude Opus 5 |
| 关联知识库条目 | 无（新发现：cell-wise midpoint tally） |
| 涉及文件 | `AIMC_WWiteration/src/mc.py`、`AIMC_WWiteration/docs/journal_revision/task_01_forward_transport_tally_audit_claude/task_01_forward_transport_tally_audit_Claude.md`；生产代码未修改 |
| 分支 / 提交 | AIMC `develop` ／ 已提交 `6b7bc27`（已并入 `main`）；本仓库登记归档 `5f587cc` |

---

## 0. 人类阅读摘要（模式 C 必填；A/B 按需）

**要回答的问题**：当前 forward MC 是否按理论完成自由飞行、碰撞和群转移，并且 spatial mesh tally 是否把每段粒子路径按实际几何交集分配到所有穿过的 cell。

**当前判断与边界**：自由程、隐式捕获代数、正向群选择器和方向采样与当前配置的理论形式一致；确定性测试确认当前 cell-wise tally 把整段路径放到 midpoint cell，而不是按 cell intersection 分解，因此限定范围内分类为 D。总路径长度仍守恒。结论只覆盖 `AIMC_WWiteration` 当前 HEAD、二维两群 prototype forward kernel 和本报告的确定性/最小统计测试；不外推到 adjoint、WW、detector response、RE、FOM、网络或 RMC。

**人需要在什么关口确认理解**：已完成只读审查；生产代码修改尚未批准，也未执行。


## 1. 任务定义（① 立项 · Agent 填）

**目标**：建立 forward transport 理论 oracle，静态追踪正向 history，并用确定性跨 mesh trajectory、自由程统计和群转移统计验证当前实现；独立判断 total path length 守恒与 cell-wise spatial attribution 是否分别正确。

**范围**：仅 `AIMC_WWiteration`；只读检查 `src/mc.py` forward kernel 和相关常量，新增 `AIMC_WWiteration/docs/journal_revision/task_01_forward_transport_tally_audit_claude/task_01_forward_transport_tally_audit_Claude.md` 及 `AIMC_WWiteration/docs/journal_revision/task_01_forward_transport_tally_audit_claude/assets_Claude/` 诊断资产。不审查 adjoint、detector response/RE、WW、PINN/DNN/U-Net、iteration、FOM 或论文结果。

**验收标准**：报告包含数学参考、逐函数静态映射、D1/T1/T2/T3 真实输出、total-vs-cell-wise 区分、影响分层、Final Classification 和后续行动；不修改生产代码或历史结果。

**原始材料**：`AIMC_WWiteration/docs/journal_revision/task_01_forward_transport_tally_audit_claude/assets_Claude/audit_tests_output.txt`（诊断原始 stdout）、`assets_Claude/track_length_oracle_output.txt`（确定性 oracle stdout）、`static_audit_notes.txt`（静态证据摘要）。

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：`src/mc.py:97-223` 实现单 batch history；`run_forward_mc` 在 `src/mc.py:337-350` 传入正向散射矩阵和源谱；当前 tally 注释已经说明“按飞行路径中点记账”。标准 track-length estimator 要求每个 cell 累加该 segment 与 cell 的真实交集长度。

**证据链**：

| # | 位置 | 说明 |
|---|---|---|
| 1 | `src/mc.py:154-160` | `d_fly=-log(U)/sigma_t`，并与 boundary distance 取最小 |
| 2 | `src/mc.py:173-175` | 碰撞后 `weight *= sigma_s_total/sigma_t` |
| 3 | `src/mc.py:76-93` | 散射矩阵行归一化条件抽样 |
| 4 | `src/mc.py:162-167` | midpoint 所在 cell 接收完整 `weight*dist` |
| 5 | `task_01_forward_transport_tally_audit_claude/assets_Claude/track_length_oracle_output.txt` | `[0.8,1,1,0.7]` 被 midpoint 路由为 `[0,3.5,0,0]`，总和均为 3.5 |
| 6 | `task_01_forward_transport_tally_audit_claude/assets_Claude/audit_tests_output.txt` | T1/T2 统计输出与 T3 四种 dx 输出 |

**影响面**：直接影响 forward cell-wise flux field；潜在影响使用该 field 的训练标签、重要性重构和 WW，但本任务未运行这些下游路径。没有更新基准/reference/result。

**为什么之前没做/没发现**：早期无偏性文档和代码注释关注 split/roulette 期望守恒，未将“总路径长度守恒”与“cell-wise 路径分解正确”分开验证。

## 2A. 物理解释与可证伪假设（模式 C 必填）

**问题定式**：对每个 segment，正确关系是 `tally_i += w*l_i`，其中 `l_i` 是 segment 在 cell i 内的实际交集长度；只有 `sum_i tally_i = w*dist` 不能证明空间分布正确。成功判据为 D1 每个 cell 与 oracle 相等；总和判据单独检查。

**可证伪假设**：若当前 midpoint routing 是真实实现，则 segment `[0.2,3.7]` 会产生 `[0,3.5,0,0]`，而非 exact `[0.8,1.0,1.0,0.7]`；若假设错误，实际可注入 kernel 的路径应逐 cell 返回 exact decomposition。T1/T2 若失败，则分别推翻自由程/群选择器的静态判断。

**物理—代码因果图**：

```text
Sigma_t, random xi, current group
  ↓
src/mc.py:154-160
  ↓
d_fly and dist=min(flight,boundary)
  ↓
free-flight distribution / segment endpoint

segment endpoints + mesh
  ↓
src/mc.py:162-167 midpoint routing
  ↓
one cell receives w*dist
  ↓
total preserved but cell-wise field differs from Σ_i w*l_i
```

**证据等级与治理标签**：自由程/群选择器为 E2–E3（最小动态测试）；cell-wise midpoint 缺陷为 E3（确定性 oracle）；总体 `未冻结`、`部分可复现`、`边界已定义`、`原始证据已归档`。

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A | 本任务只读审查；另立任务设计 cell-boundary intersection 修复和回归矩阵 | 当前问题暂不修复，期刊重算需等待；但符合人工关口 | ★推荐 |
| B | 在本任务直接修改 `src/mc.py`，将 segment 分解到多个 cell | 越过人工拍板，扩大范围并混入实现/物理验证 | 不推荐 |
| C（不做/最小改动） | 接受 midpoint field，仅在报告中注明 | 不能满足标准 cell-wise track-length estimator，风险留给下游 | 不推荐 |

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A（本记录只审查，不修改生产代码）
- **决定人 / 日期**：由人工审核本报告后确认
- **理由与约束**：本任务明确禁止直接修 tally；不得更新基准或论文结果；下游影响只记录，不在本任务验证。

**人类理解确认（模式 C 必填，由人确认或转述后确认）**：待人工审核填写。

**变更卡（模式 B/C 必填）**：

| 项 | 内容 |
|---|---|
| 问题与风险 | midpoint routing 保持整段 tally 总量，但不保持 cell-wise 空间路径分解；可能污染 forward spatial field |
| 拟改动 / 不改动 | 本任务只新增审查报告和诊断资产；不改 `src/`、`scripts/`、`tests/` 或历史结果 |
| 预期因果链 | 跨 cell segment → 完整 `w*dist` 归 midpoint cell → cell-wise flux 空间偏差 → 可能影响下游 field-based components |
| 验证与失败停止条件 | D1 exact mismatch 已足够判定 cell-wise defect；不扩展到下游模块 |
| 回滚方式（若适用） | 删除本任务新增报告/资产即可；生产代码无改动，无需代码回滚 |

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 记录环境和 conda 环境 | `conda env list`; `conda run -n torch ...` | 发现 `torch` 环境可用 NumPy/Numba；未安装新依赖 |
| 2 | 静态追踪 forward kernel | `nl -ba src/mc.py`; `nl -ba src/utils.py` | 建立 free-flight、collision、group、boundary、tally 映射 |
| 3 | 创建只读诊断脚本 | `AIMC_WWiteration/docs/journal_revision/task_01_forward_transport_tally_audit_claude/assets_Claude/audit_tests.py` | 生成 D1/T1/T2/T3 诊断；不导入训练模块、不写生产文件 |
| 4 | 运行统计/确定性诊断 | `NUMBA_NUM_THREADS=1 conda run -n torch python ...` | T1/T2 与理论一致；D1 midpoint mismatch；T3 总和相等但 cell-wise 误差显著 |
| 5 | 写入正式审查报告 | `AIMC_WWiteration/docs/journal_revision/task_01_forward_transport_tally_audit_claude/task_01_forward_transport_tally_audit_Claude.md` | 完成 16 个要求章节 |

**代码改动**：无。生产代码未修改，因此不生成生产代码 `changes.diff`。

## 6. 验证 / 实验记录（④ · Agent 填，要贴真实输出）

| 验证项 | 命令 | 结果 |
|---|---|---|
| Environment | `conda run -n torch python ...` | Python 3.11.15；NumPy 2.4.6；Numba 0.65.1；Numba threads 1 |
| D1 cross-cell | `conda run -n torch python docs/journal_revision/task_01_assets/track_length_oracle.py` | exact `[0.8,1,1,0.7]`; midpoint `[0,3.5,0,0]`; total both 3.5 |
| T1 free flight | `audit_tests.py` | mean 4.0008072742 vs 4; relative `2.018186e-04`; variance 15.9481616720 vs 16; relative `-3.239895e-03` |
| T2 group transitions | `audit_tests.py` | g0 max abs error `1.42e-4`; g1 `1.890909e-5` |
| T3 mesh routing | `audit_tests.py` | dx 4/2/1/0.5 midpoint cellwise L1 relative `0.844508/0.844508/0.877648/0.890598`; total difference at display ≤1e-10 |

真实原始输出位于 `AIMC_WWiteration/docs/journal_revision/task_01_forward_transport_tally_audit_claude/assets_Claude/audit_tests_output.txt` 和 `assets_Claude/track_length_oracle_output.txt`；完整解释见正式报告第 10–13 节。

**实验设置**：

- 随机种子：T1 NumPy Generator `20260903`；T2 Numba seed `20260903` 与 `20260904`；T3 NumPy Generator `20260903`。
- 配置快照：`Sigma_t=[0.25,0.35]`；`Sigma_s=[[0.10,0.06],[0.02,0.20]]`；mesh/domain/BC 如第 1 节；不运行 production MC。
- 依赖版本：Python 3.11.15、NumPy 2.4.6、Numba 0.65.1；CUDA/PyTorch 未参与测试。
- 基准对比：独立 exact cell-intersection oracle vs midpoint-equivalent routing；不是论文 benchmark，也不更新 reference。

**未覆盖到的验证**：完整 `run_forward_mc` 长 history、斜线/负方向 segment、反射边界、碰撞/边界竞争的动态 instrumented kernel、WW、detector response、adjoint、非均匀材料、三维和 RMC 均未覆盖。

## 6A. 结果解释卡（模式 C 必填）

| 问题 | 解释 |
|---|---|
| 结果支持/否定哪个假设？ | 支持“当前 cell-wise tally 使用 midpoint routing 而非 exact segment decomposition”；不否定 free-flight 和 group selector 的局部判断 |
| 证据等级与治理标签及依据？ | D1/T3 为 E3；T1/T2 为 E2–E3；结论未冻结、部分可复现、边界已定义、原始证据已归档 |
| 通过/失败在物理或工程上分别意味着什么？ | T1/T2 通过表示局部随机抽样形式符合理论；D1 失败表示 spatial attribution 不能称为标准 cell-wise track-length estimator |
| 不可外推边界是什么？ | 不能从本任务推断 detector response 数值偏差、WW 无偏性、FOM、神经网络结果、adjoint 或 RMC 工程能力 |
| 下一步是否需要升级范围或另立任务？ | 需要人工审核后另立 Task 02，单独设计生产 tally 修复和完整回归；不在本任务直接修复 |

## 7. 结论与遗留（⑤ 归档）

- **结论**：forward free-flight、隐式捕获代数、正向群选择器和各向同性方向公式与当前理论参考一致（限定当前正截面配置）；当前 cell-wise mesh tally 对跨 cell segment 的实现为 midpoint routing。D1 确定性 oracle 给出 exact `[0.8,1.0,1.0,0.7]`、actual `[0,3.5,0,0]`。完整 segment 的总 `weight×dist` 在测试中守恒，但 cell-wise spatial distribution 不正确。Final Classification 为 **D — Defect**，仅针对本任务范围内的 cell-wise tally。
- **遗留问题 / 后续待办**：斜穿/负方向/多维边界交叉、边界截断、完整 kernel instrumentation、性能和 stack 交互仍待专项验证；下游 detector response/WW/field 影响尚未证明。
- **知识库同步**：未修改知识库；本结论是当前 AIMC 原型新审查记录，待人工确认后决定是否同步 `MLVR_Knowledge/06_已知问题与改进建议.md`。
- **是否已提交**：AIMC 仓库已提交 `6b7bc27`（`develop`，已并入 `main`）；本仓库登记归档 `5f587cc`。

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-09-03 22:39 | 立项 |
| 2026-09-03 | 完成环境、静态追踪、D1/T1/T2/T3 诊断和正式报告；结论限定 cell-wise tally 为 D |
| 2026-09-03 | 等待人工审核；不修改生产代码 |

---

## 9. 工作日志（逐步操作记录）

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 读取项目上下文与流程 | `MLVR_Knowledge/AGENT_CONTEXT.md`, `MLVR_develop/README.md` | 按模式 C 执行物理审查，生产代码修改需人工决策 |
| 2 | 记录环境 | `conda env list`, `conda run -n torch` | 使用已有 `torch` 环境；未配置完整 AI/PyTorch 训练环境 |
| 3 | 阅读 forward 源码 | `src/mc.py:76-223,337-350` | 完成 history 和 tally 静态映射 |
| 4 | 构造理论 oracle | `task_01_forward_transport_tally_audit_claude/assets_Claude/track_length_oracle.py` | 定义精确 cell intersection 与 midpoint 对照 |
| 5 | 运行 D1/T1/T2/T3 | `task_01_forward_transport_tally_audit_claude/assets_Claude/audit_tests.py` | 真实输出归档；总路径守恒、cell-wise 分解失败 |
| 6 | 撰写报告 | `AIMC_WWiteration/docs/journal_revision/task_01_forward_transport_tally_audit_claude/task_01_forward_transport_tally_audit_Claude.md` | 完成要求章节和边界说明 |
| 7 | 归档 Task 01 | 本 README | 结论待人工审核，不提交、不修复 |
