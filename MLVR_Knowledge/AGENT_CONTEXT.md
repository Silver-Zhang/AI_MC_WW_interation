# Agent 快速上下文卡片

> **新会话 / 换模型先读这一页，不要通读知识库。** 最后更新：2026-10-11。
> 本页只留骨架和指针；实际设计及证据以权威文档与对应任务为准。

## 接手顺序

1. 根目录 [STATUS.md](../STATUS.md)：现在做到哪一步、下一步是否已授权。
2. [F11 v1 正式设计](04_F11_v1_架构与实施设计.md)：按当前阶段读取，不必每次通读。
3. [设计入库档案](../MLVR_develop/2026-10/20261011_01_f11-design-freeze/README.md) §1/§3/§4；后续再读实际实施任务对应章节。

## 当前主线

F11 v1 已由网页讨论形成统一方案并于 2026-10-11 入库：**design frozen；production implementation not completed**。

RMC 内部控制 Bootstrap 和固定 K 轮 Adjoint→Forward；现有 RMC 类扩展，固定源 history/batch 核心只保留一份；RMC 内部从简单 TARGET 构造伴随源。外部程序仅负责 Field→重构场→WW lower，经 HDF5 文件交换；不在 RMC 绑定高级机器学习模型。

本次用户只授权先写设计文档，随后自己在本地 fetch，再逐步开发或测试。**不得因文档写了阶段 0–6 而自动执行测试、改源码或 push RMC。** 决策见 [D020](DECISIONS.md#d020)。

## 权威顺序

- 现行 F11 架构、物理口径、数据语义和实施顺序：知识库 **04**。
- 历史 F01–F12 分类与证据：[02 审查矩阵](02_RMC功能审查矩阵.md) + 对应任务 §4。
- Task 15/16 保留为独立提案，合并取舍见 04 §2；不能分别按两稿冲突内容开工。
- 旧 F03 外部 response→source、F10 text-only 通道等与 04 不同的设计，仅保留历史语境；新内部构源和 HDF5 接口尚需实现/验证，不借旧测试放行。

## 必须保留的边界

- 首版 standard MGACE、中子固定源、Linux 串行、Cartesian Type=1、Energy=-1、Normalize=1、native track-mesh WW；固定模型、网格、群和 WWP。
- Bootstrap 无 WW、不是正式 iteration；一轮=A+F；不新增 batch 参数，不跨 iteration 合并统计；不自动收敛、best-anchor 或成品计算。
- Field=[Nspace,G] 的 value+RE+status；原始场与重构场分开，重构场不复制 MC RE。
- Field 体积归一候选转换尚未动态确认；不能把 Normalize=1 一律解释为 Ave 已是通量密度。
- 起始权重、伴随尺度、多 bin 响应 history 统计、随机数段和 FOM 计时以 04 为准。非零裂变产生项须对应连续 F/A 门禁通过后才开放。

## 下一步

本地 fetch 后先阅读设计；用户单独确认后，按 04 §14 从阶段 0 的体积归一最小验证开始，再进行固定源核心拆分和正式重复运行。**当前未运行阶段 0，也未开始生产实现。**

## 工作纪律

沿用根目录 AGENTS/CLAUDE 与 [工作流](../MLVR_develop/README.md)：选 A/B/C 模式，立项→设计→人拍板→实施自验→归档。未经授权不得改 RMC、切其分支或 commit/push，不更新参考结果。每次接手记录实际本地 branch/HEAD/worktree；本页历史源码 SHA 不是当前源码已核验的替代。

物理与新增接口做针对性验证，工程/文档从简；说不清的标未验证，不扩成无限验证。只在任务 §4 与对应矩阵维护结论证据，其余文档放指针。文档同步不另设阻塞开发的大任务。
