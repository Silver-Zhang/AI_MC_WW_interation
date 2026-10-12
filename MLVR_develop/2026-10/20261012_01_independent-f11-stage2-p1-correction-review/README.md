# independent-f11-stage2-p1-correction-review

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-10-12 |
| 状态 | 已完成（NEEDS CORRECTION） |
| 任务类型 | 模式 C / F11 Stage 2 P1 修复后的独立代码与证据复核 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | Claude（独立只读复核） |
| 关联知识库条目 | F11-lifecycle |
| 涉及文件 | `RMC/src/PrepareFixedSourceRun.cpp`、`RMC/src/WeightWindows.cpp`、`RMC/src/Universe.h`、Task05 `logs/p1-correction/` |
| 分支 / 提交 | 根仓 `main`；RMC `Neural_Network_WW_Iteration` / `330f091eb0296e0d0124237ba7d9a22b81aee852`；RMC 改动未提交 |

---

## 1. 目标与范围（① 立项 · Agent 填）

**要做什么**：对 Task05 在 Task07 两个 P1 缺口后的定向修复进行独立、只读的最终技术复核；判断是否可以替代 Task07 的修复前 `NEEDS CORRECTION` 结论，并据此判断 Stage 2 是否具备冻结/提交和进入 Stage 3 的条件。

**涉及什么**：当前 RMC 工作树中的 prepared fixed-source lifecycle 入口及 Task05 的 `logs/p1-correction/` 原始证据。重点为 Universe 语义 fingerprint、native mesh WW 参数/形状校验、负例命中路径、持续进程与 fresh-process 对照、普通 fixed-source 回归及证据身份。

**不做什么**：不修改 RMC、Task05、Task07、reference、核数据库或历史证据；不执行 reset/checkout/clean；不提交/推送；不启动 Stage 3。

**怎样算完成**：在独立准则下给出 `PASS`/`FAIL`/`INCONCLUSIVE`/`NOT VERIFIED` 判定，注明证据与边界，并明确是否允许最终技术验收、冻结和 Stage 3。

**原始材料**：Task05 `logs/p1-correction/`；Task07 原审核；当前 RMC 源码；本任务 `logs/pre-review-criteria.md` 与各专项复核记录。

> **模式 C 追加 · 物理解释**：复用固定模型不等于合并相邻 run 的样本。每个 half-run 都必须重新建立源历史、得分矩和统计分母；几何定义或权窗定义改变而未在 CLEAR 前拒绝，会使后一轮对应不同物理模型，破坏与独立 fresh-process oracle 的可比性。权窗的能量边界决定给定粒子属于哪个 lower/survival/upper 三界；容器形状失效时，受控拒绝是运行前物理合同的一部分。

---

## 2. 做法与证据（② 设计 · ④ 实施 · Agent 填）

**设计 / 定位**：先在 [pre-review-criteria.md](logs/pre-review-criteria.md) 冻结独立判据，再读取当前生产源码、Task05 增量补丁、Task05 原始命令/快照/JSON 结果和 Task07 历史结论。专项记录：

- [source-correction-audit.md](logs/source-correction-audit.md)
- [universe-fingerprint-review.md](logs/universe-fingerprint-review.md)
- [ww-validation-review.md](logs/ww-validation-review.md)
- [negative-gate-review.md](logs/negative-gate-review.md)
- [regression-review.md](logs/regression-review.md)
- [independent-comparison.md](logs/independent-comparison.md)
- [risk-register.md](logs/risk-register.md)

**方案选择**：采用“生产入口在索引前是否验证所有 caller-visible 容器形状”为 P1-02 必要条件。未因正常输入的回归通过而降低该条件；也未将 Task05 自验的 `READY FOR INDEPENDENT RE-REVIEW` 当成独立验收。

**实施要点**：无 RMC 代码改动。本任务只创建独立复核档案和指向性治理更新；没有 `changes.diff`，因为没有修改生产代码或原型代码。

**验证输出**：直接复查 Task05 correction-era 汇总与命令结果：

```text
regression-results.json:
  ordinary_checks=123, ordinary_passed=123
  ctest_passed=10
  half_runs=36, physical_tolerance=0
  legacy_negative_passed=66, p1_negative_passed=51

regression-command-results.json:
  ordinary-cases-command=0, gates-command=0,
  p1-negatives-command=0, universe-persistent-command=0,
  universe-fresh-command=0, ctest-command=0

当前生产源码：
  PrepareFixedSourceRun.cpp:286
    const auto &bins = OWeightWindow.p_vEnergyBins[1];
  在验证 outer p_vEnergyBins.size()>1 之前即发生索引。
```

**未覆盖到的验证**：未自行重跑 RMC 构建/数值用例，不重新执行 Task05 的脚本，也未运行 sanitizer。Type-2 hex lattice 只完成静态字段/路径覆盖审查，未做 correction-era 独立数值重跑。全量 HDF5 的所有 pair 仅部分独立抽查；既有时间/FOM 例外没有提升为正式每轮 FOM。

---

## 3. 决策记录（③ · 人拍板）

- **决定**：本任务是只读独立复核；不得直接修复新发现的 P1-02 能量边界容器形状缺口。
- **决定人 / 日期**：用户 / 2026-10-12（Task05 P1 修复后的独立最终复核请求）。
- **约束**：不动 RMC、参考结果、核数据库和 Task05/Task07 历史材料；不启动 Stage 3；是否提交/推送由用户决定。

**变更卡（B/C 模式，各一行）**：

| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| 独立复核结论可能与 Task05 自验相冲突 | 仅本档案、STATUS/INDEX/知识库及物理导读的结论指针；不改 RMC/Task05/Task07 | 生产源码先于结论；任一 P1 未闭合即 `NEEDS CORRECTION`，不进入 Stage 3 | 文档可按本档案过程记录复核；不覆盖历史证据 |

> **模式 C 追加 · 人类理解确认**：用户的批准边界是“独立判断修复是否真实闭合”，而不是授权进一步修复；Task07 原始 `NEEDS CORRECTION` 必须保留，只有新的独立结论才能判断当前代码。

---

## 4. 结论与边界（⑤ 归档）

### REVIEW CONCLUSION

```text
F11 Stage 2 P1 correction review: NEEDS CORRECTION
```

- **P1-01 Universe fingerprint：PASS（受限 profile）**。`universeDefinition()` 已覆盖受支持的确定性 CSG / Type-1 矩形 lattice / Type-2 六角 lattice 在位置、成员、邻接、变换与 lattice 定位中实际读取的稳定字段；随机介质、CLS/PBS/RSA/ODR/DEM 等未覆盖路径在 prepared 入口显式拒绝。真实 Universe origin、rotation、membership、lattice-fill mutation 的 correction-era 负例均在第二轮 CLEAR 前拒绝并保持首轮状态。
- **P1-02 native WW validation：FAIL**。WUPN、WSURVN、MXSPLN 及派生界限验证已有实质修复并有 51/51 定向负例；但 `OWeightWindow.p_vEnergyBins[1]` 在验证 outer vector 包含 neutron entry 之前被索引。`InstallPreparedNativeState()` 也重复同类未受保护的 neutron entry 索引。此外 native lookup 在能量恰等于最后边界时可取得末端 boundary 索引，却只对大于最后边界进行回退；prepared entry 未验证边界有限、严格递增或末端安全性。该行为违反本任务预设的“先验证 outer particle/energy-bin shape，后访问 neutron entry”准则，且缺少对应的外层/内层 energy-bin 形状及端点负例。
- **持续/新进程回归：PASS（已审证据范围内）**。Task05 correction-era 记录 FF、FAF、AA、WW、FAF-WW、reuse 与新增 Universe 序列共 36 persistent/fresh pair，物理容差为零；原始 JSON 状态及解压 trace payload 的独立比较为 36/36 一致。普通比较 123/123、CTest 10/10、旧负例 66/66、P1 负例 51/51 均有保存的执行记录。
- **普通行为：PASS（代表性范围）**。本 P1 补丁仅触及 prepared 入口与测试 driver；Task05 保存的 ordinary fixed-source 对照为 123/123。此不等于一般 prepared API 的任意 caller-mutated 容器状态已安全。

**不能推出什么（边界）**：

- 不接受 Stage 2 为最终技术验收、代码冻结或提交条件；不允许以此开始 Stage 3。
- 不外推到非零裂变、MPI/OMP/AIS/Python、CE、耦合粒子、restart/surface source、任意分布/加权源、随机介质或完整 F11 闭环。
- Type-2 hex lattice 动态数值覆盖未由本轮独立复跑确认。
- 旧 StatisticsTester FOM 仍是 `legacy_mixed_not_per_run`，不是本阶段正式 FOM。
- delivery manifest 中 `MLVR_develop/INDEX.md` 有一处当前哈希不匹配；保护的历史证据 11,551/11,551 项哈希通过。该差异是治理/溯源风险，不是数值一致性结论。

**遗留 / 下一步**：新开经用户拍板的缺陷修复任务后，先集中验证 `p_vEnergyBins` 与 `p_vWeightWindowPara` 的 outer/inner shape，再进行任何 neutron 索引；要求 neutron energy boundaries 至少两个、有限且严格递增，并修正 terminal endpoint 到最后合法 WW interval 的映射。新增绑定前和首轮后 outer-short/empty、inner-empty/one-boundary、duplicate/descending/non-finite/terminal-equality boundary 负例，并证明 post-run 拒绝发生在 CLEAR 前且首轮 receipt、RNG、tally、分母保持。修复后需再次进行独立复核。

**提交状态**：本审查未修改 RMC，未 commit/push。RMC 仍为 `Neural_Network_WW_Iteration` / `330f091e` 加 Stage 2 未提交工作树；根工作区文档同样未提交，提交决定保留给用户。

> **模式 C 追加 · 结果解释**：Universe fingerprint 的修复意味着受支持的确定性几何定义不能在两次独立 half-run 之间静默变更。WW scalar 保护意味着不合法分裂/轮盘参数不会进入 native 算法；但 energy-bin 外容器未先验证时，程序可能在任何物理守卫或状态保护前进行越界访问。因此现有回归可以证明已覆盖合法模型在指定 profile 内保持等价，不能证明 malformed caller-visible WW 模型能被安全拒绝。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-10-12 | 建立 Mode-C 独立复核任务，先写 pre-review criteria。 |
| 2026-10-12 | 读取 Task07 原始 P1 结论、Task05 correction diff/manifest/negative/regression evidence 与当前生产源码。 |
| 2026-10-12 | 审核 Universe stable fields 与受支持 CSG/rectangle/hex transport 读路径；确认随机/DEM 类路径受 profile guard 拒绝。 |
| 2026-10-12 | 审核 WW 参数类型、native roulette/splitting `double→int` 路径、绑定前及每轮 guard 与 51 项负例。 |
| 2026-10-12 | 发现 `p_vEnergyBins[1]` 在 outer-shape 验证前被访问；复核 prepared installer 存在同类索引，且 driver 无能量边界形状 mutation。 |
| 2026-10-12 | 独立汇总 correction-era 36 persistent/fresh、123 ordinary、10 CTest、66 legacy-negative、51 P1-negative 及保护证据哈希情况。 |
| 2026-10-12 | 结论定为 `NEEDS CORRECTION`；停止，不修复、不提交、不启动 Stage 3。 |

**证据等级**：P1-01 为 E1+E3（源审计与生产 mutation 负例）；P1-02 未闭合，缺口为 E1 源码事实；合法 profile regression 为已保存的 E3 证据，经本轮直接审查，不等同于本轮重新运行。
