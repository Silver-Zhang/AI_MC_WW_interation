# independent-f11-field-volume-review

| 项目 | 内容 |
|---|---|
| 立项日期 | 2026-10-11 |
| 状态 | 实施中（独立复核报告已成稿；README 未定稿） |
| 任务模式 | C — 深度物理研究与学习 |
| 范围 | 独立复核 F11 阶段 0 Field 体积归一实验。 |
| 限制 | 只写本任务档案；不修改 volume task、RMC、核数据库、reference、冻结设计、STATUS、INDEX、KB；不 commit/push。 |

## 1. 目标与范围

独立判断 uniform/heter Cartesian mesh 的 Field `Ave` 是否代表体积归一化标量通量密度，并审查实验中的轨迹长度/体积独立参考、source-history 归一化、能群与 `Normalize` 语义。

**模式 C · 物理解释：** 轨迹长度 tally 的原始累计量是长度贡献。只有经 source normalization 和空间 bin 体积除法后，才可作为标量通量密度。uniform/heter 网格若表示相同 physical bin，则两路径必须得到相同 density，而不是相同未除体积的长度和。

## 2. 做法与证据

先读取 current RMC scoring/normalization source，形成独立 Ave 含义与验收标准。完成该记录后，才读取 `f11-field-volume-normalization` 的报告、脚本和原始 evidence。允许只读再分析已有输出，不重新运行完整输运矩阵。

## 3. 决策

用户授权仅限独立审查与本任务档案写入。不得根据结果修复源码、改 reference、修改 Codex 任务或启动阶段 1。

**人类理解确认：** 接受的结果只能说明实际验证的 standard-MGACE、serial、固定 source、指定 mesh 和 NPS 范围。它不能自动推广到所有 tally estimator、非 Cartesian 网格、MPI/OpenMP、CE 或非单位权重 source。

## 4. 结论与边界

待独立计算和 evidence 审核完成后填写。

## 5. 过程

| 时间 | 阶段 | 记录 |
|---|---|---|
| 2026-10-11 | 立项 | 用户禁止修改 STATUS/INDEX，故手工建档而未调用 `new_task.sh`。 |
| 2026-10-11 | 源码先行 | 将在不读取目标实验结论前写下独立 Ave/体积验收判据。 |
