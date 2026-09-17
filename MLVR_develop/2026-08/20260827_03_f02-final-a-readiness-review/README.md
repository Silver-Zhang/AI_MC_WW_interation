# f02-final-a-readiness-review

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-27 |
| 状态 | 已完成（F02-B 有界 A — Ready） |
| 任务类型 | 物理审查 / 证据归并 / 文档 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F02 |
| 涉及文件 | 只读 `RMC/`；更新 F02 知识库、物理导读和任务台账 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / base `6d2087518e0d9f23574d629f5fde361c79f519e4` + 冻结 W9 三行 diff；未提交/推送 RMC |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：在 W5/W6/W7/W9 修复、角表示、真实 density mesh、NNUBAR=1/混合裂变材料等独立任务均已完成后，按冻结的第一版 F02 需求做最终风险复核，裁定 standard ASCII MGACE fixed-source neutron adjoint 是否可由 C — Verify 升为有界 A — Ready。

**范围**：只读 RMC；审查 Linux x86_64、serial、`ais=OFF`、standard ASCII MGACE、fixed-source neutron forward/adjoint。F03 伴随源定义、F04 adjoint+WW、F06/F07 场与 RE 均保持独立审查。明确不外推到 photon 完整能力、CE、AIS/HDF5 核数据、delayed、GPT、MPI/OpenMP、Windows、反射边界或任意机制组合。

**验收标准**：逐项映射冻结需求和已识别高风险机制；厘清“更多几何/边界”和“强 P1/P2”是否属于真实冻结门槛；独立复核分类；冻结 base、diff、binary 和 formal 身份；同步所有当前结论文档，且不修改、提交或推送 RMC。

**原始材料**：`logs/frozen_snapshot.txt` 原样保存 branch、HEAD、工作树、diff SHA256 和 binary SHA256；`logs/changes_diff_sha256.txt` 保存快照哈希；各 formal 原始输出仍保存在对应独立任务目录。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：F02 冻结需求只要求 RMC 能执行第一版框架需要的多群伴随输运，没有规定任意数量的几何、所有边界类型或所有机制笛卡尔积。历史 C 门槛列出的角表示、density mesh、NNUBAR=1/多材料和 frozen formal 已分别闭合；剩余任务是防止开放式覆盖清单阻止一个有明确作用域的能力分类。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `MLVR_Knowledge/01_双向迭代基础框架_方法与功能需求.md` F02 | 冻结需求是“执行本框架需要的多群伴随输运”，相邻 source/WW/field 能力独立编号。 |
| 2 | `20260825_01`、`20260825_05`–`08` | P0 非裂变互易性、W5/W6/W7 修复及非均匀密度、NNUBAR>1 裂变响应均有运行证据。 |
| 3 | `20260825_11`、`20260825_12`、`20260826_01` | W9 动态反例与三处修复闭环；neutron 是 F02 作用域内必要项。 |
| 4 | `20260826_02` | 四类其余 MGACE 条件角表示 40/40 clean，40,000 个生产样本通过冻结统计门槛。 |
| 5 | `20260827_01` | HDF5 position-dependent density mesh 10/10 clean，合并 $z=0.0984$。 |
| 6 | `20260827_02` | 部署 NNUBAR=1 及 NNUBAR=1 主导混合裂变材料 20/20 clean，合并 $z=0.9563/0.3748$。 |
| 7 | `logs/frozen_snapshot.txt` | formal 对象为 base `6d208751...` + W9 diff SHA256 `5eec92f9...c756` + binary SHA256 `8fff3f0f...f13c2`。 |

**影响面**：只改变 F02-B 的证据分类和适用范围说明，不替代 F03/F04/F06/F07 审查，不更新 reference/benchmark。A 仅归属于已验证冻结工作树快照，不归属于 base commit `6d208751...` 单独。

**为什么之前没做/没发现**：此前三个明确 A 门槛尚未闭合；各独立任务为防止局部结果外推，均保守保留 C。全部门槛完成后仍沿用旧句子，造成“更多几何/边界”成为未量化开放式门槛。

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A：按冻结需求做有界 A 裁定 | 汇总机制证据，明确验证对象和排除项；不要求无限几何或所有机制组合。 | 必须避免把 A 外推到相邻能力或未测平台。 | ★推荐 |
| B：再增加任意几何矩阵 | 自选更多球、盒、边界和组合继续 formal。 | 没有冻结终点，新增一个案例后仍可要求下一个；违反风险导向审查。 | 不推荐 |
| C：保持 C | 即使明确门槛全部通过仍不分类。 | C 将不再表示“关键证据缺失”，失去分类体系的信息价值。 | 不采用 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A — 按冻结第一版需求和风险机制做有界 A 裁定。
- **决定人 / 日期**：用户 / 2026-08-27（持续授权按推荐方案执行，直至 A 门槛可诚实满足）。
- **理由与约束**：RMC 不修改、不重置、不 commit/push/切分支；不更新 reference/benchmark；A 必须绑定 base + frozen diff + binary 快照，并明确排除未验证能力。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 重读冻结需求与审查协议 | 确认 F02 不包含 F03/F04/F06/F07，也没有“任意几何/边界”数量要求。 |
| 2 | 建立 evidence-to-requirement matrix | W5/W6/W7/W9、P0、角表示、density mesh、两类 nubar 与混合材料均有独立证据。 |
| 3 | 复核角表示术语 | `NLEG/ISANG` 是群对条件余弦表示；旧“强 P1/P2”不是准确的 Legendre 矩描述。 |
| 4 | 两次独立复核 | 一次支持有界 A 但误把未 commit 当阻断；第二次专门裁定未 commit 不是物理阻断，可用冻结 diff/binary 闭合身份。 |
| 5 | 冻结工作树快照 | 记录 base、唯一三行 diff、diff/binary SHA256；未改变 RMC。 |
| 6 | 同步文档 | 更新审查矩阵、问题台账、上下文卡片、物理导读、INDEX，并纠正混合比例 stale 文本。 |
| 7 | 最终完整性检查 | 根仓库与 RMC `diff --check` 均无输出；RMC 仍仅有 W9 文件；diff/binary 哈希保持不变；当前结论 stale 扫描无输出。 |

**代码改动**：见 [changes.diff](changes.diff)。该文件仅是 RMC 当前既有 W9 三行未提交补丁的冻结快照，不是本任务新改动；SHA256 为 `5eec92f929ca93caaabeaacd64d5c92f44f1dc89c61c11997ab962fe8957c756`。

生成方式：
```bash
git -C ../../RMC diff > changes.diff
# 改原型则：
git -C ../../AIMC_WWiteration diff > changes.diff
```

---

## 6. 验证 / 实验记录（④ · Agent 填，要贴真实输出）

| 验证项 | 命令 | 结果 |
|---|---|---|
| 冻结身份 | `git -C RMC ...`、`sha256sum` | branch `Neural_Network_WW_Iteration`；HEAD `6d208751...`；唯一修改 `src/GetMgExitErgMu.cpp`；diff 3+/3-；diff SHA256 `5eec92f9...c756`；binary SHA256 `8fff3f0f...f13c2`。 |
| 角表示 formal | `20260826_02` 正式报告 | 40/40 clean；40,000 样本；支持域、矩、方差/Pearson 门槛通过。 |
| density mesh formal | `20260827_01` 正式报告 | 10/10 clean；位置依赖读回；合并 $z=0.0984397473$。 |
| NNUBAR/material formal | `20260827_02` 正式报告 | 20/20 clean；纯 NNUBAR=1 与混合材料合并 $z=0.9562519706/0.3747657993$。 |
| 独立分类复核 | 两个只读 subagent | 一致确认显式物理门槛已闭合；专门复核确认未 commit 不阻断有哈希身份的工作树快照分类。 |
| 归档完整性 | `logs/final_integrity_check.txt` | 根/RMC diff check clean；RMC status 仅 `M src/GetMgExitErgMu.cpp`；stale 当前结论扫描无匹配。 |

```
F02 final A-readiness frozen evidence snapshot
Neural_Network_WW_Iteration
6d2087518e0d9f23574d629f5fde361c79f519e4
 M src/GetMgExitErgMu.cpp
rmc_diff_sha256=5eec92f929ca93caaabeaacd64d5c92f44f1dc89c61c11997ab962fe8957c756
rmc_diff_numstat=3 3 src/GetMgExitErgMu.cpp
rmc_binary_sha256=8fff3f0f534d2a2a116e033a26cf4bb62005c5b6d62b29925423b97bb74f13c2
```

**实验设置**：本任务不新增随机实验；复用各 formal 已冻结的 seeds、population、manifest、依赖与真实输出。

**未覆盖到的验证**：完整 photon/耦合粒子、CE、AIS/HDF5 核数据、delayed、GPT、MPI/OpenMP、Windows、反射边界，以及 density mesh × 裂变 × 强角分布等任意组合。它们不属于本次有界 A，但不得被 A 标签隐含放行。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：F02-B 改判 **A — Ready（有界、冻结工作树快照）**。适用对象严格为 RMC base `6d208751...` + W9 diff SHA256 `5eec92f9...c756` 构成的源码快照及 formal 所用 binary SHA256 `8fff3f0f...f13c2`；能力范围是 Linux serial、`ais=OFF`、standard ASCII MGACE fixed-source neutron adjoint。base commit 单独不含 W9，不能称为 Ready revision。
- **几何/边界裁定**：已验证真空球、球壳/多区域和双盒界面，足以覆盖已识别的几何迁移、泄漏和材料/密度界面风险；“更多几何/边界”不是冻结 F02 的开放式门槛。反射边界等未测机制明确排除，后续按实际第一版算例需求单独审查。
- **角术语裁定**：旧“强 P1/P2”不准确。当前 MGACE 路径使用群对条件余弦表示；负/正单变量、多 bin、离散余弦与 isotropic 分支均已分别闭合，不声称验证传统全 Legendre P1/P2 矩输运。
- **遗留问题 / 后续待办**：由用户决定何时提交/推送 W9；提交后需记录新 commit，但不必为当前冻结快照重复物理 formal。继续按依赖顺序审查 F03，而不是扩展 F02 的无限覆盖列表。
- **知识库同步**：更新 `02_RMC功能审查矩阵.md`、`06_已知问题与改进建议.md`、`AGENT_CONTEXT.md`、`MLVR_Physics_Guide/`、任务 INDEX；修正 NNUBAR 混合比例。
- **是否已提交**：未提交/推送；RMC 保持用户要求的未同步状态。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-27 16:13 | 立项 |
| 2026-08-27 | 完成冻结需求、几何/边界与角术语复核；两次独立复核闭合分类和未提交快照身份问题。 |
| 2026-08-27 | F02-B 改判有界 A — Ready，开始同步知识库和物理导读。 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 重读需求、审查协议和全部 F02 证据 | 知识库与任务档案 | 显式 C 门槛已全部闭合。 |
| 3 | 全工作区搜索几何/边界与 P1/P2 文本 | 知识库、任务档案、RMC 只读源码 | “更多几何/边界”不是冻结需求；旧 P1/P2 术语不准确。 |
| 4 | 独立全面复核 | Claude poly-bridge subagent | 支持 narrow A；指出未提交身份风险。 |
| 5 | 独立身份专项复核 | GPT poly-bridge subagent | 审查规范不要求 clean HEAD；base + diff + binary 可构成严格验证对象。 |
| 6 | 冻结证据快照 | `logs/frozen_snapshot.txt`、`changes.diff` | diff/binary 哈希和唯一工作树边界已记录。 |
| 7 | 最终诊断与完整性检查 | 文档 diagnostics、`git diff --check`、stale scan | 11 个改动文档 diagnostics 均无错误；格式检查和 stale 扫描均 clean。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
