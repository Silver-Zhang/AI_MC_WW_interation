# f10-minor-corrections-f07-sync

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-27 |
| 状态 | 已完成（F10 design frozen；implementation not completed） |
| 任务类型 | 接口合同修订 / F07 状态同步 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | Codex |
| 关联知识库条目 | F10 / F07 |
| 涉及文件 | F10 设计与原档案、F07 档案、`02_RMC功能审查矩阵.md`、`STATUS.md`、`MLVR_develop/INDEX.md` |
| 分支 / 提交 | 根工作区提交前基线 `9777c01b9c65edad729567d8e469a32dc1e94fcf`；档案随 2026-09-27 根工作区提交入库；RMC 未修改 |

---

## 1. 目标与范围（① 立项）

**目标**：将用户批准的 F10 三项 minor corrections 写回 [设计文档](../20260927_06_f10-field-reconstruction-boundary/F10_Field_Interface_Design.md)：负 Type=1 `Ave` 必须拒绝；metadata 记录实际 source-normalization denominator / total starting source weight 与来源；明确 source-normalized track-length flux density 的单位口径。再把 F07 后续独立复核完成的受限 WW-on field-bin 校准同步到当前状态入口。

**范围**：只修订合同与状态记录；不进入 F11、不实现 Adapter/parser、Field class、Reconstruction、WW Builder，不修改 RMC 或基准。原始用户消息原样保存于 `logs/user_request_original.txt`；独立复核原件在 `../20260927_07_independent-f10-field-boundary-review/` 和 `../20260927_02_independent-f07-field-re-review/`。

> **模式 C · 物理解释**：第一版 Type=1 标量通量是非负物理量，因此负的原始 `Ave` 不能当作有效场传递。`Ave` 经过源权重分母与体积归一化；仅有 history 数不足以识别非单位源权重下的口径。F07 的 WW-on 经验校准说明一个已测 field bin 的报告不确定度与独立运行散布相容，不等于所有 bins 或源模式都已校准。

---

## 2. 做法与证据（② 设计 · ④ 实施）

**设计 / 定位**：用户引用提交 `9777c01b9c65edad729567d8e469a32dc1e94fcf` 并明确批准三项小修正。F10 独立复核 `20260927_07` §13 列出相同修正；原 F10 设计 §3/§7/§8/§9 存在对应缺口。F07 独立复核 `20260927_02` 报告 §11：10 个独立 `N=10,000` native WW-on run、PTRAC-active，经验 SD `0.159123`、报告 RMS sigma `0.179255`、`Q_WW=0.88769`；其 §14 仍排除全部 bins、非单位/不等源权重、MPI/OpenMP 等。原 F07 开发者任务自身没有跑此专门校准。

**方案选择**：不改 F10 架构，仅补校验规则、metadata 与单位；F07 保持 C — Verify，并将“仍缺”改为“独立复核已完成一个 bin 的受限校准”。早期 F07 档案保留当时范围，§4 增加后续证据说明。

**实施要点**：修改 F10 设计三处语义及 Adapter 合同、F10 原档案复核后修订记录、F07 原档案后续证据说明，并同步矩阵、状态页和台账。无代码改动，故无 `changes.diff`。

**验证输出**：`logs/document_check.txt` 记录三项文字检查、F07 `Q` 与范围核对、`git diff --check`、归档自检和 RMC 工作树状态的真实命令输出。

**未覆盖到的验证**：没有新 MC 运行；没有 Adapter 运行时拒绝负值或 normalization provenance 的实现验证；没有进一步的 WW-on bins/配置校准。

---

## 3. 决策记录（③ · 人拍板）

- **决定**：用户接受 F10 总体架构，并明确要求三项修正写回后正式冻结；同时授权修正 F07 当前状态，暂不进入 F11。
- **决定人 / 日期**：用户 / 2026-09-27（`logs/user_request_original.txt`）。
- **约束**：修订止于设计与状态；不修改 RMC、不更新基准、不开始实现或 F11。

**变更卡**：

| 风险 | 改动范围 | 预期因果链及验证 / 停止条件 | 回滚 |
|---|---|---|---|
| 负通量被误收、源归一化失去溯源、F07 当前状态过期 | F10 合同、F07/F10 档案、矩阵/看板/台账；无 RMC 代码 | 三项合同文字一致，F07 仅称受限单 bin 校准，文档检查通过即停止 | 回退本任务文档改动 |

> **模式 C · 人类理解确认**：用户原文逐项给出 `Ave>0/0/<0` 的处理、所需 normalization metadata、cm 几何单位口径，并认可设计主体；用户还指出 Claude 已完成 F07 WW-on 校准且要求同步。这里只记录用户明示内容，不推定其批准更广范围或实现。

---

## 4. 结论与边界（⑤ 归档）

- **结论**：F10 独立复核的三项 minor corrections 已全部写入设计文档；至此 **design frozen**，仍为 **implementation not completed**。F07 一个 field bin 的 WW-on 经验校准已由独立复核完成，当前 F07 仍为 **C — Verify**。
- **证据**：[F10 设计文档](../20260927_06_f10-field-reconstruction-boundary/F10_Field_Interface_Design.md) §3/§7/§8/§9；F07 独立复核 `../20260927_02_independent-f07-field-re-review/Independent-F07-Field-Statistical-Uncertainty-Review.md` §11/§14；`logs/document_check.txt`。
- **边界**：文档语义冻结不代表 Adapter/parser/算法/WW Builder 已实现。F07 校准只涉及受限 serial text 同一 field bin 的 10-seed native WW-on 样本；zero-score、全部 bins、非单位/不等源权重和 MPI/OpenMP 仍不在已证范围。
- **遗留 / 下一步**：遵守用户指令，本任务不启动 F11；后续实现另立任务。
- **提交状态**：RMC 未修改、无 commit/push；档案与原始请求副本随 2026-09-27 根工作区提交入库。

> **模式 C · 结果解释**：修正后合同明确拒绝与首版非负标量通量不符的输入，并使 `value` 的单位与源权重分母可追溯。F07 的独立运行散布为一个 WW-on bin 的 RE 尺度提供经验支持，但不消除零得分和未测配置的统计风险。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-27 | 读取用户修正、F10 独立复核 §13 与 F07 独立复核 §11/§14；按模式 C 建档。 |
| 2026-09-27 | 写回 F10 三项修正；同步 F07/F10 档案、审查矩阵、STATUS 与 INDEX。 |
| 2026-09-27 | 完成文档核对与归档自检；按用户要求停止，不进入 F11。 |
