# f10-field-reconstruction-boundary

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-27 |
| 状态 | 已完成（F10 **design frozen；implementation not completed**） |
| 任务类型 | 接口设计 / 统计场数据边界 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | Codex |
| 关联知识库条目 | F10 |
| 涉及文件 | 本档案、`F10_Field_Interface_Design.md`、`MLVR_Knowledge/02_RMC功能审查矩阵.md`、`STATUS.md`、`MLVR_develop/INDEX.md`；RMC 只读 |
| 分支 / 提交 | 根工作区 `main`；随本档提交（2026-09-27）；RMC 未修改 |

---

## 1. 目标与范围（① 立项）

**目标**：冻结 `RMC .Tally → Field Adapter → StatisticalField → Field Reconstruction → ReconstructedField → WW Builder` 的第一版数据边界。完成标准是 [设计文档](F10_Field_Interface_Design.md) 覆盖原始任务的 15 项交付章节，三条路径、shape/角色/坐标不变量及拒绝条件明确；同步审查矩阵、状态页和台账，并清楚标注设计与实现的区别。

**范围**：仅 standard MGACE fixed-source neutron、Cartesian Type=1 track-length、`Energy=-1`、`Normalize=1`、serial text `inp.Tally` 的已审查子域。只写设计与记录；不改 RMC，不写 parser、C++ class、Reconstruction/WW 算法或 F11 scheduler。

**原始材料**：`logs/user_task_original.txt` 是用户粘贴任务的原样副本，SHA256 `8eac310dbf9014d69751743d23133a6f850a327ce6b809b7c9b896f18a1cebbc`。

> **模式 C · 物理解释**：同一空间×多群二维网格中，Forward、Adjoint 和 Bootstrap 的数值都可用同一形状承载，但分别是 φ、φ†、φ₀，必须用显式 role 区分。RMC 的零得分 `Ave=0, RE=0` 不能当成精确零场；重构后的值不是一次新的 MC 估计，不能继承原始 MC RE。若空间或物理能群顺序错位，数值会被交给错误的 WW 位置，接口即失败。

---

## 2. 做法与证据（② 设计 · ④ 实施）

**设计 / 定位**：复用 F05 `20260927_03` 的 Forward 2×30 `.Tally`、F06 `20260926_01/03` 的 Cartesian x-fastest / 物理能量升序证据、F07 `20260927_01/02` 的 RE 和 zero-score 语义、F12 `20260927_04` 的 Bootstrap 生命周期以及 F03/F09 独立 response 边界。RMC 只读检查 `RMC/src/SingleTally.cpp:877-882,976-992`：`Energy=-1` 使用 MG bin vector，文本每群输出一个 `Energy Bin` 下界并有 `Tot`；`RMC/src/InitiateAndClear.cpp:67` 该 vector 长度为 G；`RMC/src/CheckMgAceBlock.cpp:39-54` 从 MGACE centre/width 算 lower bound。由此发现 `.Tally` 自身没有完整 G+1 边界，最后上界不能猜测；设计要求 authoritative MG definition / run-sidecar 并在 Adapter 中核验。

**方案选择**：用户已冻结 Adapter / Reconstruction / WW Builder 三段职责。本文采用外部 `[space, physical-energy group]` 零基逻辑索引与显式 role/stage/iteration；不暴露 RMC reverse internal group coordinate。保留两态 status；ReconstructedField 不设 MC RE。完整细节在 [设计文档](F10_Field_Interface_Design.md)。

**实施要点**：只新增本任务设计文档和原始任务副本，并同步三处进度入口；无 RMC/AIMC 代码改动，无 `changes.diff`（代码改动快照规则不适用）。

**验证输出**：文档合同的轻量核对；真实命令和输出记于 `logs/design_check.txt`。核对 15 个交付章节、三路径、数组形状、原始材料一致性与仓库改动范围；未运行新的 MC 算例。

**未覆盖到的验证**：本任务没有 Adapter/parser、Reconstruction 或 WW Builder 实现与运行验证；没有完整群边界 sidecar 的实际读取/核验；没有 MPI/OpenMP、HDF5、CE/耦合粒子、非 Cartesian 验证，也未亲自运行 WW-on field-bin 校准。后续 F07 独立复核 `20260927_02` 已完成受限的 10-seed WW-on field-bin 校准；F06 既有 geometry/source warning 与 direct group oracle 限制维持原分类。

---

## 3. 决策记录（③ · 人拍板）

- **决定**：用户在本任务原文中明确批准总体架构，并要求本次只冻结数据边界；按该已授权方案完成设计归档。
- **决定人 / 日期**：用户 / 2026-09-27（`logs/user_task_original.txt` §Goal、§1、§15–§16）。
- **约束**：不修改 RMC；不实现 parser/class/算法/WW Builder；不启动 F11；不更新 benchmark/reference；设计完成即停止。

**变更卡**：

| 风险 | 改动范围 | 预期因果链及验证 / 停止条件 | 回滚 |
|---|---|---|---|
| 空间/群错位或 zero-score 被误读为高可信度 | 设计文档、档案、矩阵与看板；不改 RMC 或算法 | 显式边界/索引、状态与拒绝条件 → 后续实现可按合同校验；15 章及三路径核对后停止 | 回退本任务文档与进度记录 |

> **模式 C · 人类理解确认**：用户原文直接确认了三段职责、Forward/Adjoint/Bootstrap 物理身份、`RE=0` 零得分风险、同 mesh/group 以及“设计完成即停止”的范围；本记录只转述这些明示条款。G+1 完整边界获取与校验是本次只读检查导出的实现前待办，并未记作用户对具体 sidecar 实现方式的批准。

---

## 4. 结论与边界（⑤ 归档）

- **结论**：F10 第一版数据合同 **design frozen**。`StatisticalField`、`ReconstructedField`、Cartesian/物理能群索引、两态 status、Adapter/Reconstruction/WW Builder 边界、三条路径及 shape invariants 已定义；**implementation not completed**。F10 不按 RMC 已实现能力分类为 A — Ready。
- **证据**：[设计文档](F10_Field_Interface_Design.md) §1–§15；`logs/design_check.txt` 的文档核对结果；已有 F05/F06/F07/F12 档案和上述 RMC 只读位置。
- **边界**：这是首版 serial text MG neutron 子域的设计，不代表 Adapter/parser、Reconstruction、WW、scheduler 或 ResponseDefinition 对接已经工作，也不证明更广泛物理/统计适用性。完整 G+1 群边界来源尚需未来实现确定并验证。
- **遗留 / 下一步**：仅登记设计文档 §15 的实现问题；遵守用户停止规则，不在本任务启动后续实现。
- **提交状态**：RMC 未修改、无 commit/push；档案、设计文档与原始任务副本随 2026-09-27 根工作区提交入库。
- **2026-09-27 复核后修订**：独立审查 `20260927_07` 给出 **ACCEPT WITH MINOR CORRECTIONS**；用户明确批准三项修正。修订任务 `20260927_08_f10-minor-corrections-f07-sync` 已将负 `Ave` 拒绝、source-normalization denominator/provenance、`value` 单位口径写回设计文档。F10 **design frozen** 从这次修订完成后成立，仍是 **implementation not completed**。

> **模式 C · 结果解释**：设计明确了将 RMC tally 的空间/物理群得分及 RE 无歧义地移交给方法无关 Reconstruction 所需的条件，并将处理后的场与原始 MC 统计分开。文档核对通过只证明合同完整一致，不是运行时数据转换、物理场重构质量或 WW 效果的证据。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-27 16:05 CST | 模式 C 立项；原始任务原样保存于 `logs/`。 |
| 2026-09-27 | 只读抽查 F05/F06/F07/F12 档案及 RMC 相关输出/群边界源码；确认 `.Tally` 不含最后物理上界。 |
| 2026-09-27 | 按用户冻结方案写 15 节设计，补足完整边界来源与拒绝条件；同步 F10 进度入口，文档核对后停止。 |
| 2026-09-27 | 独立复核要求三项小修正；用户批准后由 `20260927_08` 写回设计，正式关闭设计冻结的待修项。 |
