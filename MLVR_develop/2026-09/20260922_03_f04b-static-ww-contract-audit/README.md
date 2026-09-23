# f04b-static-ww-contract-audit

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-22 |
| 状态 | 已完成（静态审查；修复决策待人工） |
| 任务类型 | 静态代码审查 / 接口契约验证 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F04 |
| 涉及文件 | 只读 `RMC/src/{SampleNeutronSource.cpp,GetMgCs.cpp,ReadWeightWindow.cpp,WeightWindows.cpp,DoMeshWeightWindow.cpp,TrackWithWeightWindow.cpp,GlobeFun.h}` 与 WW 用户文档 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `b7d8a946`；RMC 无改动 |

---

## 1. 目标与范围（① 立项 · Agent 填）

**要做什么**：独立静态确认 MG neutron transport 中粒子状态能量/群表示与 native WW `WWE:N` 输入、lookup 的坐标体系是否一致。

**涉及什么**（仓库 / 模块 / 数据）：standard MGACE、fixed-source neutron、native `WWMESH`、neutron adjoint compatible path；只读源码与用户文档。

**怎样算完成**：输出 [`F04-B-static-WW-contract-audit.md`](F04-B-static-WW-contract-audit.md)，以 file:function:line 证据回答 `WW(r,E)` 或 `WW(r,g)`，给出唯一三选一结论；不修改代码。

**原始材料**（`logs/` 下有什么，原样保存）：本任务仅静态审查，无运行原始材料。

> **模式 C 追加 · 物理解释**：多群输运若以群编号表示状态，则权窗分箱也必须使用同一群坐标，或在 lookup 前有明确的物理能量→群编号转换。否则不同坐标轴上的数值比较会把粒子送入错误权窗，从而改变方差缩减策略并可能影响效率或统计行为。

---

## 2. 做法与证据（② 设计 · ④ 实施 · Agent 填）

**设计 / 定位**：独立审查报告见 [`F04-B-static-WW-contract-audit.md`](F04-B-static-WW-contract-audit.md)。静态链为：

```text
physical source energy
  → LocateMgErgGrp
  → p_dErg = discrete MG group coordinate
  → DoTrackMeshWeightWindow
  → setMeshWeightWindowBound(erg=p_dErg)
  → GetIntpltPos(literal WWE:N boundaries)
```

`SampleNeutronSource.cpp:268` 在 MG 下把 `p_dErg` 改为 `LocateMgErgGrp()` 返回的群坐标；`GetMgCs.cpp:263-296` 的返回值是整数群坐标，`GetErgValue()` 反向将其转为群中心物理能量。另一方面，`ReadWeightWindow.cpp:55-91` 原样保存 `WWE:N` 数字，`WeightWindows.cpp:45-65` 直接以 `p_dErg` 搜索该数组，未见 MeV↔群坐标转换。用户文档将 `WWE:N` 描述为 energy grid，并给出 MeV 示例。

**方案选择**：按请求只作静态审查；不运行大型算例、不修改 RMC、不以既有 F04/F02 报告为结论前提。因为 MG 状态表示、WW parser、lookup 及用户文档共同形成完整数据流，采用“Confirmed mismatch”而不是“Cannot determine”。

**实施要点**：RMC 源码、测试、benchmark、reference、模型均未修改；新增本任务局部静态报告。

**验证输出**：静态证据已经逐项列入报告的 Evidence Table；无动态运行。

**未覆盖到的验证**：不同现有用户输入是否已主动使用群坐标 `WWE:N`；错 bin 对实际 tally/FOM 的量化影响；任何转换或输入校验的修复方案。

---

## 3. 决策记录（③ · **人拍板**）

- **决定**（采纳什么方案）：用户提供 F04-B 静态审查任务，明确只读源码、禁止修复与 patch；按该范围完成并停止。
- **决定人 / 日期**：用户 / 2026-09-22
- **约束**：不修改 RMC、benchmark/reference、正式结论或分类；本档案只报告独立静态结论，后续是否立项修复由人工决定。

**变更卡（B/C 模式，各一行）**：
| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| MG state group coordinate 与物理 energy-grid 语义混用，导致 WW 选错能群 bin | 仅读取源码/用户文档并写报告；不改 RMC 或测试 | source→state→lookup 链与 parser/documentation 坐标证据能闭合即停止；不推导修复 | 仅新增档案文档；无 RMC 回滚 |

> **模式 C 追加 · 人类理解确认**：用户要求独立从源码确认坐标契约，且明确不修复、不运行大型算例；本报告将“状态群坐标 + literal energy grid 查找”视为需要人工决定后续处理的接口问题。

> 未拍板前，Agent 不得改动 `../RMC` 下的任何文件。



---

## 4. 结论与边界（⑤ 归档）

- **结论**：**Confirmed mismatch**（静态）。MG 输运态能量为离散群坐标（`SampleNeutronSource.cpp:268` → `GetMgCs.cpp:263-296` 的 `LocateMgErgGrp`），而 native `WWE:N` 按字面数值存储并直接参与查找（`ReadWeightWindow.cpp:55-91`；`WeightWindows.cpp:45-65`；`GetIntpltPos` 为纯数值边界搜索），解析与查找链均无 MeV↔群坐标转换；用户文档却将 `WWE:N` 描述为 energy grid 并给出 MeV 示例（`VarianceReduction.rst:88-101,176`）。forward 与 fixed-source adjoint 共用同一 lookup 坐标链（`DoMeshWeightWindow.cpp:42-44` 不带 adjoint 分支），并非 adjoint 独有分歧。逐项证据见报告 §6 Evidence Table。
- **不能推出什么**（边界）：不覆盖 CE、photon、耦合粒子、MLVR/WW 生成算法、动态实验与源码修改；不能判定现有用户输入实际如何选择 `WWE:N` 数值；未量化错 bin 对 tally/FOM 的影响；不含修复方案。
- **遗留 / 下一步**：是否将本确认升为阻塞缺陷（W10/F04 候选）、是否立项输入校验或坐标转换修复，由人工决定（根目录 `STATUS.md` 待拍板 #6）。
- **提交状态**：RMC 无改动（`b7d8a946`）；本档案随 2026-09-23 根工作区提交入库。

> **模式 C 追加 · 结果解释**：结果支持“MG 状态群坐标与 literal energy-grid 查找混用”这一接口风险假设，且该风险对 forward 与 fixed-source adjoint 同样成立；静态契约结论不替代带动态运行的输入行为验证。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-22 22:02 | 立项 |
| 2026-09-22 | 只读核对 source→state→lookup 链、parser 与用户文档证据，产出 `F04-B-static-WW-contract-audit.md`（Confirmed mismatch）。 |
| 2026-09-23 | 归档收尾：补全 §4 结论/边界与提交状态，随根工作区提交入库。 |

> 关键命令、误判与修正、未决分歧都写在这里；人机讨论较深时把要点并入本表，**不再单独建会话纪要文件**。原始聊天转储不要入仓（可能含凭据）。

**证据等级（可选）**：物理/审查结论可标 E0–E4；工程、文档、治理任务可省略。
