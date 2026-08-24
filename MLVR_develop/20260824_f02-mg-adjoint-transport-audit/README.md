# Task: F02 — Multigroup Adjoint Transport Audit

日期：2026-08-24

状态：Ready for local read-only audit

关联知识库：

- `MLVR_Knowledge/01_双向迭代基础框架_方法与功能需求.md`
- `MLVR_Knowledge/02_RMC功能审查矩阵.md`
- `MLVR_Knowledge/03_RMC功能审查规范.md`
- `MLVR_Knowledge/DECISIONS.md`

## 1. Requirement

本任务只审查 F02：**RMC 是否真实具备第一版框架所需的多群 Adjoint transport，以及其实际物理实现是否能够被后续双向迭代框架依赖。**

第一版需求边界：

- 仅考虑 multigroup adjoint，不审查 continuous-energy adjoint；
- 本任务重点是伴随输运本体；
- Adjoint source 的完整语义归 F03；
- Adjoint field/RE 的完整能力归 F06/F07；
- Adjoint + WW 兼容性归 F04；
- 可记录这些相邻功能的交叉证据，但不得在本任务中替代其独立审查结论。

## 2. 审查前必须记录

本地 Agent 开始前先记录：

```text
RMC repository path:
RMC branch:
RMC HEAD commit SHA:
git status --short:
审查日期:
Agent/模型:
```

若 RMC 工作区存在未提交修改，只读审查可以继续，但必须记录状态，不能覆盖、整理或修改这些内容。

## 3. 本任务必须回答的问题

### Q1 — 如何启用多群 Adjoint transport？

追踪从输入/配置到运行时状态的完整入口：

```text
input / option
  ↓
parser / initialization
  ↓
adjoint mode state
  ↓
transport entry
```

不能仅凭 `adjoint` 关键词或变量名判定功能存在。

### Q2 — 实际调用链是什么？

形成至少一条可核查的调用链，覆盖：

- 伴随模式进入输运；
- 粒子/伪粒子历史推进；
- 碰撞处理；
- 多群能群转换相关逻辑；
- 历史终止/边界处理。

每个关键节点尽量记录：

```text
file:function:line-range
```

### Q3 — 数学上的伴随算子如何落实？

必须从实际代码判断，而不是从函数名推断。

重点调查：

- 多群散射核/散射矩阵在伴随模式下如何处理；
- 是否存在与正向群间跃迁相对应的转置/反向索引逻辑；
- 能群采样概率、权重修正或等价实现；
- 角变量/方向处理是否存在伴随专用逻辑；
- 其他会影响伴随输运正确性的碰撞权重或采样处理。

注意：完整 Boltzmann 伴随算子是相空间散射核的伴随，不应仅以“矩阵转置”四个字作结论。若当前 RMC 多群实现采用简化条件，应明确写出适用假设和代码证据。

### Q4 — 当前实现是否真正可运行？

调查：

- 是否有现存输入卡、测试、算例或历史用例；
- 是否有明显废弃、未接通、条件编译或无法到达的代码；
- 注释中宣称支持但运行链未连接的情况。

第一轮以静态源码审查为主。如果静态证据不足以确认关键正确性：

- 不要自行宣称“正确”；
- 将相关项记为未验证；
- 给出最小运行/数值验证方案；
- 最终可分类为 **C — Verify**。

## 4. 明确不做的事情

本任务禁止：

- 修改 `RMC/` 任意源码；
- 修复发现的问题；
- 重构伴随模块；
- 设计 MLVR 最终接口/class/controller；
- 审查连续能量伴随；
- 把 F03/F04/F06/F07 合并成一次大审查；
- 更新任何 benchmark/reference output。

若发现明确缺陷，只记录 `file:function:line + 行为 + 为什么是问题`，留到 Stage 3 另立任务。

## 5. 输出格式

审查完成后直接在本 README 追加以下章节，不删除本任务定义。

### A. Environment Snapshot

RMC branch / commit / worktree 状态。

### B. Existing Implementation

入口、文件、类/函数、关键状态变量、调用链。

### C. Actual Behavior

用 `Input → Processing → Output` 解释实际程序行为。

### D. Physics Audit

逐项记录散射、能群、方向、采样/权重等伴随物理实现及证据。

### E. Requirement Gap

| 子需求 | 证据 | 状态 | 备注 |
|---|---|---|---|
| MG adjoint mode exists | | | |
| transport call chain reachable | | | |
| adjoint multigroup scattering behavior understood | | | |
| angular/collision treatment understood | | | |
| executable evidence exists | | | |

### F. Verification Evidence

已有测试/算例/运行证据；没有则明确写 `Not verified`。

### G. Final Classification

必须从以下选择一个主分类：

- A Ready
- B Extend
- C Verify
- D Integration issue
- E Defect
- F Missing

并用 3–8 句解释分类依据。

### H. Open Questions / Proposed Next Action

只提出下一步审查或最小验证，不进行源码修复。

## 6. 人工决策

2026-08-24：用户已批准 Stage 2 审查协议，并批准 F02 多群 Adjoint transport 作为第一项正式只读审查任务。

本次批准仅允许**只读调查与必要的非修改型验证建议**，不授权修改 RMC 源码。

## 7. 完成条件

只有同时满足以下条件，本任务才可提交用户复核：

- 记录 RMC branch + commit；
- 给出可追溯调用链；
- 解释实际多群伴随物理实现，而非只列符号；
- 明确已验证与未验证内容；
- 给出唯一 A–F 主分类；
- 未修改 RMC 源码。

用户确认 F02 结论后，才进入下一项 F03 审查。
