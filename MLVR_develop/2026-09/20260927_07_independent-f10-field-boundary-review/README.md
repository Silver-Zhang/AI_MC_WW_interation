# independent-f10-field-boundary-review

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-27 |
| 状态 | 已完成 |
| 任务类型 | 独立设计审查 / F10 Field Reconstruction boundary |
| 任务模式 | C — 深度物理研究与学习 |
| 关联知识库条目 | F10 |
| 报告 | [Independent-F10-Field-Boundary-Design-Review.md](Independent-F10-Field-Boundary-Design-Review.md) |

## 1. 目标与范围

独立审核 F10 的 `StatisticalField → ReconstructedField → WW Builder` 数据边界是否完整、低耦合且适合第一版 MLVR。只审设计；不实现 parser、Field class、reconstruction、WW generation 或 scheduler，不修改 RMC。

> **模式 C 物理解释**：RMC 原始统计场的 value/RE/status 与经过处理的 reconstructed value 是不同量。边界必须防止把 MC RE 伪装成 reconstruction uncertainty，也必须防止物理 MeV 与 RMC 内部 reverse group index 混用。

## 2. 做法与证据

### 独立性

先仅依据第一版 MLVR 流程写入 `logs/pre-developer-claim-conclusion.md`，之后才阅读 Codex F10 设计。没有读取或复述其结论来形成初始判断。

### 审查结果

设计的三段分离、二维 `[Nspace,G]` shape、physical-energy ascending contract、two-state `statistical_status`、role/stage/iteration 语义、Adapter/ResponseDefinition/WW Builder 分界，以及避免 over-design 的取舍均合理。

需要三项小修正：

1. 冻结 Type=1 scalar flux Adapter 必须拒绝 negative raw `Ave`，而不是标为 `VALID`；
2. metadata 显式记录 source-normalization denominator/identity；
3. 明确 value 的 source-normalized track-length flux-density unit convention。

完整逐项审核见本目录报告。

### 未覆盖

不评估具体 parser/metadata serialization、reconstruction algorithm、WW formula、F11 scheduling、HDF5 schema、ML feature contract 或 RMC 实现。

## 3. 决策记录

- **决定**：用户指定独立 F10 设计审核；先写独立最小合同，后读取 Codex 文档；仅记录建议，不实现代码。
- **决定人 / 日期**：用户 / 2026-09-27。
- **约束**：禁止 RMC 修改、F11 启动、Reconstruction algorithm、WW generation 和 Field 数据结构实现。

**变更卡**：
| 风险 | 范围 | 验证与停止条件 | 回滚 |
|---|---|---|---|
| 设计隐藏 RMC/WW/workflow 耦合或过度扩展 | 仅设计文档审查；不改源码 | 检查 raw/reconstructed field、group/mesh/metadata/roles/adapter/WW boundary；发现 blocker 仅记录 | 无代码改动，无回滚 |

> **人类理解确认**：此审核只决定 F10 数据合同是否可作为之后实现的边界，不批准任何实现。

## 4. 结论与边界

- **结论**：**ACCEPT WITH MINOR CORRECTIONS**。设计符合第一版最小、纯粹、低耦合边界；完成 §2 三项语义补充后可作为实现前的冻结设计。
- **不能推出什么**：不证明 parser、reconstruction、WW Builder、ResponseDefinition、HDF5 schema、F11 调度或 ML 模型已经实现或正确。
- **遗留 / 下一步**：人工决定是否接受三项小修正并更新 F10 design；之后才可另立实现任务。
- **提交状态**：RMC 未修改、无 commit/push；档案与前置独立结论随 2026-09-27 根工作区提交入库。

> **结果解释**：此设计保留 raw MC 统计和 processed field 的明确边界，阻止 group-coordinate/MeV、Tot/group、RE/reconstruction uncertainty 和 role/stage/iteration 的典型混淆；minor corrections 是输入 validation 和 provenance 精化，不改变架构。

## 5. 过程记录

| 时间 | 操作 |
|---|---|
| 2026-09-27 | 建立 independent Mode-C F10 设计审核档案。 |
| 2026-09-27 | 保存 pre-developer 最小合同。 |
| 2026-09-27 | 读取并逐项审核 F10 design；归档 ACCEPT WITH MINOR CORRECTIONS。 |

证据等级：E1（独立架构/数据合同审查）；没有实现或运行证据，符合只审设计范围。
