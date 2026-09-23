# independent-mg-ww-repair-review

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-23 |
| 状态 | 已完成 |
| 任务类型 | 独立审查 / MG WW 能量坐标契约修复复核 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | （未署名） |
| 关联知识库条目 | F04 |
| 涉及文件 | 只读 RMC 源码、用户手册、tests 与未提交 repair diff；任务局部 build、脚本、日志与报告（RMC 未修改） |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration`（只读，未修改）；根工作区 `main` 随本档提交（2026-09-23） |

---

## 1. 目标与范围（① 立项 · Agent 填）

**要做什么**：独立复核 `20260923_01` 的 MG native WW 能量契约修复是否正确、完整、无未声明副作用；不接受开发者结论为前提，先形成独立结论再看修复档案。
**涉及什么**（仓库 / 模块 / 数据）：只读 current RMC source、未提交 9-file repair diff、RMC 用户手册与 tests；任务目录内独立 MPI-off/OpenMP-off build、forward/adjoint/CE bin smoke 与 deep parser/lookup smoke；不改 `RMC/`。
**怎样算完成**：产出 `Independent-MG-WW-Weight-Window-Repair-Review.md`，给出结论（含限制）与未覆盖项；前置独立结论存 `logs/pre-developer-claim-conclusion.md`。
**原始材料**（`logs/` 下有什么，原样保存）：repair diff 快照、构建/运行日志、bin-selection 摘要（PTRAC 原件仅本地）、deep regression 输出与 review evidence manifest。

> **模式 C 追加 · 物理解释**：修复把内部群坐标先还原为群中心物理能量，再与 `WWE:N` 物理 MeV 边界比较，使查窗发生在同一坐标轴；若修复正确，forward/adjoint 在同一输入下应选择与物理边界一致的 WW bin，且 CE 行为不变；若 bin 选择与物理能量不符或 CE 回归改变，则修复不成立。群内分界在群中心表示下无唯一物理映射——这是复核确认的固有边界。

---

## 2. 做法与证据（② 设计 · ④ 实施 · Agent 填）

**设计 / 定位**（读了什么、查到什么；关键证据给 `文件:行号` 或数据位置）：先独立检查 current RMC source、uncommitted 9-file repair diff、RMC 用户手册和现有 tests；初步结论在未阅读开发档案前写入 `logs/pre-developer-claim-conclusion.md`。之后才读 `20260923_01` 修复档案作 §7 对比。

**方案选择**（选了什么、放弃了什么、为什么）：以 native `WWE:N` physical-MeV contract 为独立定式；检查 source→MG group→lookup 数据流、helper 覆盖和 reverse group order；用任务目录独立 MPI-off build 与 forward/adjoint/CE smoke、deep parser/lookup smoke 验证。未创建任何 RMC patch。

**实施要点**（改了什么；改动快照见 `changes.diff`，无代码改动写“无”）：RMC 无改动；审查证据为 `logs/current-repair.diff`、source/binary identity、当前 build 输出、动态 logs 和 `Independent-MG-Weight-Window-Repair-Review.md`。无 `changes.diff`，因为本任务不改 RMC。

**验证输出**（贴真实命令与输出；物理结论从严，工程/文档从简）：

```text
Current repair build: MPI off / OpenMP off, RMC v3.5.0-alpha.0-310-gb7d8a946.
MG forward / MG adjoint / CE bin smoke: all completed after input syntax correction.
Direct bin identifier/lower-bound observable: unavailable; PTRAC only records action events.
Independent deep parser/lookup smoke: z=-0.17667, apparent FOM ratio=0.52301;
not accepted as statistical evidence because independent RNG streams were not established.
Final review verdict: Repair is correct with explicit limitations.
```

**未覆盖到的验证**（如实写；没有就写“无”）：direct bin-index oracle; exact MG/WWE boundary equality; WWE inside a group; independent-seed deep statistical replication; MG photon/electron; point-mesh behavior; MPI/OpenMP; MCNP WWINP; CE reference regression.


---

## 3. 决策记录（③ · **人拍板**）

- **决定**（采纳什么方案）：按用户任务书执行独立只读审核：检查 current RMC source、uncommitted repair diff、RMC docs、tests；对 current source 在任务目录做独立 build 与最小验证；最终才读取本次修复档案对比开发者主张。
- **决定人 / 日期**：用户 / 2026-09-23。
- **约束**（能不能动接口 / 基准 / 算力预算…）：禁止修改 RMC 源码、测试、基准与参考结果；允许仅在本任务档案创建 build、输入、脚本、日志和报告。

**变更卡（B/C 模式，各一行）**：
| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| 接口语义可能仍不充分或修复可能改变 CE/MCNP 行为 | 仅任务档案内构建与测试；不改 `RMC/` | 明确区分静态证据、最小动态证据与未验证路径；测试失败不创建 patch | 删除任务生成的 build/runs；RMC 无回滚需求 |

> **模式 C 追加 · 人类理解确认**：用户要求的范围是独立审查 current repair，不接受既有结论；只读 RMC 和运行任务内验证；若发现问题，只记录根因、证据与建议方向并停止。

> 未拍板前，Agent 不得改动 `../RMC` 下的任何文件。



---

## 4. 结论与边界（⑤ 归档）

- **结论**：**Repair is correct with explicit limitations.** Current repair correctly maps native MG internal group state to its physical group-centre energy for `WWE:N` lookup and shares this path forward/adjoint; CE is identity. Full evidence/report: `Independent-MG-Weight-Window-Repair-Review.md`.
- **不能推出什么**（边界）：不证明 unresolved `WWE:N` edge inside an MG group has a unique physical interpretation; no direct selected-bin/lower-bound test or independent-seed deep statistical replication was obtained.
- **遗留 / 下一步**：人工决定 native input contract：require MG-aligned `WWE:N`, or document/enforce centre projection at parse time; then add deterministic bin-selection tests for forward, adjoint, equality/extremes.
- **提交状态**：本审查无 RMC 改动；修复已由 `20260923_01` 本地 commit（`5cfb0f77`，未 push）；`logs/bin-selection/*.PTRAC` 原件按体积规范不入库、仅保留本地；本档案随 2026-09-23 根工作区提交入库。

> **模式 C 追加 · 结果解释**：修复消除了群号与 MeV 的直接数值比较，支持 native WW 在群中心代表能量下的确定性选择；群内分界仍无唯一物理解释，不能外推到任何未明示的 group-boundary、MCNP 或并行语义。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-23 20:35 | 立项 |
| 2026-09-23 | 只读检查 current RMC source 与未提交 repair diff，形成前置独立结论（`logs/pre-developer-claim-conclusion.md`，先于开发档案）。 |
| 2026-09-23 | 任务目录独立 MPI-off build 与 forward/adjoint/CE bin smoke 完成（修正输入语法后）。 |
| 2026-09-23 | bin-selection 探针多轮 retry/final 运行与 deep parser/lookup smoke（z=-0.17667 因 RNG 未独立而不作统计证据）；未获得 direct bin-ID observable。 |
| 2026-09-23 | 产出最终报告与结论 “Repair is correct with explicit limitations”（含未覆盖项与接口加固建议）。 |
| 2026-09-23 | 归档收尾：补全头部与 §1，随根工作区提交入库。 |

> 关键命令、误判与修正、未决分歧都写在这里；人机讨论较深时把要点并入本表，**不再单独建会话纪要文件**。原始聊天转储不要入仓（可能含凭据）。

**证据等级（可选）**：物理/审查结论可标 E0–E4；工程、文档、治理任务可省略。
