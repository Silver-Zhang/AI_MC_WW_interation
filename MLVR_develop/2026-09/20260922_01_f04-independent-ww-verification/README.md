# f04-independent-ww-verification

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-22 |
| 状态 | 已完成（独立实验验证；正式分类待人工决定） |
| 任务类型 | 独立验证 / 组合功能实验 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F04 |
| 涉及文件 | 只读 `RMC/src/{SampleNeutronSource.cpp,GetMgCs.cpp,ReadWeightWindow.cpp,WeightWindows.cpp,GlobeFun.h,SaveSplitParticles.cpp}`；任务局部 `verification/` 输入、脚本、输出和报告 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `b7d8a946`；验证期间未修改 RMC |

---

## 1. 目标与范围（① 立项 · Agent 填）

**要做什么**：独立验证 MG fixed-source neutron adjoint + native WW 的能量/能群接口契约、无偏性、FOM 与 split bank 状态；不接受既有 F04 结论作为前提。

**涉及什么**（仓库 / 模块 / 数据）：RMC standard ASCII 30-group H2O、Linux MPI-off serial、native `WWMESH` track mesh；仅新增任务局部输入/脚本/报告。

**怎样算完成**：输出用户指定的 `verification/01_WW_energy_group_contract.md` 与 `verification/02_adjoint_WW_unbiasedness_test.md`，保存全部配对输入/日志/tally，给出 z-score、FOM 及可复核边界；不修改 RMC、不更新正式 benchmark/reference/分类。

**原始材料**（`logs/` 下有什么，原样保存）：`logs/` 保存 energy-contract smoke、配对结果汇总及运行 console；每个原始 case 的 `inp`、stdout/stderr、`inp.Tally` 保存在 `verification/cases/`。

> **模式 C 追加 · 物理解释**：WW 应只改变采样方差，不改变伴随 response 的期望值；因此用独立 seed 的 WW-on/off response 差及联合统计误差形成 $z$ 检验。FOM 还必须计入运行时间，低 RE 本身不等于效率提升。MG 状态使用离散群坐标时，WW bin 边界必须使用相同坐标。

---

## 2. 做法与证据（② 设计 · ④ 实施 · Agent 填）

**设计 / 定位**：

- 能量/群契约结论和逐行源码证据：[`verification/01_WW_energy_group_contract.md`](verification/01_WW_energy_group_contract.md)。核心发现是：MG source sampling 把 `p_dErg` 改为离散群坐标；native `setMeshWeightWindowBound` 用该数值直接搜索 literal `WWE:N` 数字，未做 MeV→群坐标转换。
- 无偏性、FOM 和 split/roulette 状态链实验：[`verification/02_adjoint_WW_unbiasedness_test.md`](verification/02_adjoint_WW_unbiasedness_test.md)。

**方案选择**：使用新的 seeds `(211,223,227,229,233)`、新的多群 WW 边界与独立 5 cm H2O 球；固定 $2\times10^5$ histories/branch。WW-on source 必然在首段 split，避免“卡被读入但没有生效”。response 选取 group 16 的非零 tally，预冻结判据为每个 seed 及合并 $|z|\le3$。

**实施要点**：未修改 RMC；新增任务局部 `verification/generate_cases.py`、`run_compare.py`、10 个 case 的输入/原始输出、两份验证报告。未修改 benchmark/reference/model。

**验证输出**：

```text
MG/WW contract: Potential mismatch
  p_dErg is MG group coordinate after LocateMgErgGrp.
  native WW lookup searches literal WWE:N numbers with that coordinate.

paired response group 16:
  analog = 1.44845798 ± 0.00127416
  WW     = 1.44657885 ± 0.000988232
  combined z = -1.16537
  all per-seed |z| <= 3: yes

mean FOM:
  analog = 962949.40
  WW     = 820602.59
  FOM ratio = 0.8522
```

**未覆盖到的验证**：physical-MeV `WWE:N` 与 group-coordinate `WWE:N` 的定量 bin-selection probe（当前运行证据结合源码判为接口风险）；深穿透生产问题；多 mesh、MPI/OpenMP、耦合粒子、CE、point mesh、反射边界和跨节点。


---

## 3. 决策记录（③ · **人拍板**）

- **决定**（采纳什么方案）：
- **决定人 / 日期**：
- **约束**（能不能动接口 / 基准 / 算力预算…）：

**变更卡（B/C 模式，各一行）**：
| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| | | | |

> **模式 C 追加 · 人类理解确认**：把“人现在理解了哪些关系、批准了什么范围”留下来——问答原文或一两句转述均可。

> 未拍板前，Agent 不得改动 `../RMC` 下的任何文件。



---

## 4. 结论与边界（⑤ 归档）

- **结论**：独立实验在 group-coordinate `WWE:N` 设计下通过伴随 WW 无偏性统计检验（合并 $z=-1.16537$），但不显示 FOM 提升（比值 0.8522）。独立源码/运行验证发现 **MG `p_dErg` 与 literal physical-MeV `WWE:N` 存在 Potential mismatch**：当前 lookup 没有坐标转换。
- **不能推出什么**（边界）：WW-on/off 统计通过不能消除能量契约风险，因为实验刻意使用群坐标边界；不说明物理 MeV 风格的 `WWE:N` 正确。不能推广到其他粒子、并行、网格、核数据或生产深穿透问题。
- **遗留 / 下一步**：按用户指令停止，不改 RMC、不更新 F04 正式结论。应由人工决定是否把 `Potential mismatch` 升为 F04/F08 的 D/E 候选，并另立读入契约修复/验证任务。
- **提交状态**：RMC 无改动（`b7d8a946`）；验证资产随本档提交；RMC 运行产物（`verification/cases/`）按归档体积规范不入库、仅保留本地。

> **模式 C 追加 · 结果解释**：本实验支持“在协调的群坐标 WW 输入下，当前伴随+WW estimator 未见统计偏差”；同时独立确认接口层可能把群坐标和物理能量混用。若真实输入约定是 MeV，这一风险即会影响 WW bin 选择，即使本均匀测试仍偶然通过。


---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-22 19:59 | 立项 |
| 2026-09-22 | 创建独立验证资产；确认 RMC 工作区 clean，基线 `b7d8a946`。 |
| 2026-09-22 | 静态追踪确认 MG source 会以 discrete group coordinate 覆盖 `p_dErg`，WW 查窗直接使用 literal `WWE:N` 数字；生成 `01_WW_energy_group_contract.md`。 |
| 2026-09-22 | 初版 physical-style `WWE:N` smoke 首先因下界数量与群数不匹配被拒绝；修正后作为 contract discriminator 正常执行。该输入修正记录在本档案，未修改 RMC。 |
| 2026-09-22 | 完成五独立 seed、2,000,000 histories 的 paired experiment；得到无偏性统计通过、但 FOM 未提升的结果；生成第二份报告。 |
| 2026-09-22 | 按用户指令停止，等待人工决定是否将 energy/group contract 风险进入修复阶段。 |

> 关键命令、误判与修正、未决分歧都写在这里；人机讨论较深时把要点并入本表，**不再单独建会话纪要文件**。原始聊天转储不要入仓（可能含凭据）。

**证据等级（可选）**：物理/审查结论可标 E0–E4；工程、文档、治理任务可省略。
