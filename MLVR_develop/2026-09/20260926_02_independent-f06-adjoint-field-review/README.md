# independent-f06-adjoint-field-review

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-26 |
| 状态 | 已完成（C — Verify，限定 normalized text Cartesian serial） |
| 任务类型 | 独立审查 / F06 空间×能群伴随场 tally |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | （未署名） |
| 关联知识库条目 | F06 |
| 涉及文件 | 只读 RMC mesh tally parser/scoring/output 源码与 docs；任务局部 build、输入脚本、日志与报告（RMC 未修改） |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration`（只读，未修改）；根工作区 `main` 随本档提交（2026-09-26） |

---

## 1. 目标与范围（① 立项 · Agent 填）

**要做什么**：独立审查 RMC 是否能在冻结的 MG fixed-source neutron adjoint serial 子域输出 MLVR 需要的空间×能群伴随标量通量场。
**涉及什么**（仓库 / 模块 / 数据）：只读 RMC mesh tally parser/scoring/accumulation/output；任务目录内 serial build、输入、运行与报告。
**怎样算完成**：先保存独立预结论，再运行最小判别性 mesh tests，最后才读 F06 Codex 档案；形成独立报告并停在审查结论。
**原始材料**（`logs/` 下有什么，原样保存）：`logs/pre-developer-claim-conclusion.md`、源码/构建/运行摘要、Tally 文本、HDF5 header 与审查证据。

> **模式 C 追加 · 物理解释**：合格场须是可恢复的每个空间 bin × 每个 MG group 的 source-normalized 标量通量密度；`Normalize=0` 仅是体积积分轨长分数，不能当作 $\phi^\dagger$。若 group 映射、体积归一化或文本输出维度任一处不成立，则该假设被推翻。

---

## 2. 做法与证据（② 设计 · ④ 实施 · Agent 填）

**设计 / 定位**（读了什么、查到什么；关键证据给 `文件:行号` 或数据位置）：独立追踪 `ReadMeshTallyCard → SetupMeshTally → TallyByTL/ScoreMeshTallyByTL → SumUp/ProcessTally → text/HDF5 output`；详见 `Independent-F06-Adjoint-Spatial-Energy-Field-Review.md`。

**方案选择**（选了什么、放弃了什么、为什么）：用 type-1、`Energy=-1`、`Normalize=0/1` 的两空间不等体积 Cartesian mesh，比较 forward/adjoint 和 raw/normalized 语义；只读 build/run。

**实施要点**（改了什么；改动快照见 `changes.diff`，无代码改动写“无”）：未改 RMC。创建任务局部输入脚本、独立 serial build、真实输出及审查报告；无 `changes.diff`。

**验证输出**（贴真实命令与输出；物理结论从严，工程/文档从简）：

```text
Current RMC serial build: v3.5.0-alpha.0-311-g5cfb0f77.
Adjoint two-bin mesh: raw-to-normalized volume ratios = 49,999.24 and 150,000.0 cm3.
Text output shows 2 spatial bins × 30 MG rows; HDF5Mesh /Type1 shape=(2,1,1), no energy axis.
Classification: C — Verify, scoped to normalized textual Cartesian field.
```

**未覆盖到的验证**（如实写；没有就写“无”）：MPI/OpenMP; clean boundary-warning-free geometry; F07 statistics; energy-aware HDF5; direct single-group oracle; CE/coupled particles; field consumer.


---

## 3. 决策记录（③ · **人拍板**）

- **决定**（采纳什么方案）：按用户要求独立审查 F06 输出能力：先保存独立预结论，再运行最小判别性 mesh tests，最后才读 01 号开发档案。
- **决定人 / 日期**：用户 / 2026-09-26。
- **约束**（能不能动接口 / 基准 / 算力预算…）：只读 RMC；允许任务目录内 build/run/log/report；发现问题只记录、不修复；不开始 F07。

**变更卡（B/C 模式，各一行）**：
| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| 输出维度/归一化语义可能不满足 F06 需求 | 只读源码 + 任务目录最小运行；不改 RMC | estimator/weight/volume/group/output 链闭合 + raw/normalized 体积比核对即停止；未覆盖项保留为 C 边界 | 删除任务目录生成物；无 RMC 回滚 |

> **模式 C 追加 · 人类理解确认**：独立复核、不接受既有结论；不把“程序有输出”当作 field 正确（范围与边界见 §4）。

> 未拍板前，Agent 不得改动 `../RMC` 下的任何文件。



---

## 4. 结论与边界（⑤ 归档）

- **结论**：C — Verify：在 standard MGACE fixed-source neutron adjoint、Type=1 Cartesian `Energy=-1`、`Normalize=1`、serial text output 范围，现有链可解释为 \(\phi^\dagger_{i,g}\)。
- **不能推出什么**（边界）：HDF5Mesh 不是 space×energy field；`Normalize=0` 不是 flux density；不证明 F07 统计、并行、边界-warning、CE/耦合粒子或 field-consumer 行为。
- **遗留 / 下一步**：人工决定是否接受 text-first field interface，或另立任务实现/验证 energy-aware machine-readable output；F07 单独处理统计。
- **提交状态**：RMC 未改动、无 RMC commit/push；档案随 2026-09-26 根工作区提交入库；两张 50 MB noisy 首批原始 stdout 按体积规范不入库、仅保留本地。

> **模式 C 追加 · 结果解释**：轨长权重场在 `Normalize=1` 下具有 \(\sum w\ell/V\) 标量通量意义；空间/能群文本输出结构通过。HDF5 缺能群轴和 runtime boundary warnings 阻止扩展为 A。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-26 05:13 | 立项 |

> 关键命令、误判与修正、未决分歧都写在这里；人机讨论较深时把要点并入本表，**不再单独建会话纪要文件**。原始聊天转储不要入仓（可能含凭据）。

**证据等级（可选）**：物理/审查结论可标 E0–E4；工程、文档、治理任务可省略。
