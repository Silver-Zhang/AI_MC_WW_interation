# RMC 功能审查规范（Stage 2 Audit Protocol）

## 1. 目的

本规范用于统一 Stage 2 的 RMC 现有功能审查方法，确保不同 Agent 在不同时间接手时采用一致的证据标准、结论格式和任务边界。

Stage 2 只回答：

> RMC 当前实际具备什么能力、这些能力是否满足双向迭代 WW 基础框架需求、哪些点需要后续扩展/验证/修复。

Stage 2 不负责修改 RMC 源码，也不提前设计最终接口。

---

## 2. 核心原则

审查按以下链路进行：

```text
Requirement
   ↓
Existence
   ↓
Actual Behavior
   ↓
Requirement Match
   ↓
Integration Compatibility
   ↓
Targeted Verification（按风险需要）
   ↓
Classification
```

执行原则：

1. **Audit ≠ Repair**：发现缺口、缺陷或兼容性问题后停止于记录和分类，不在同一审查任务中顺手修改源码。
2. **Evidence first**：结论必须由源码、已有测试/算例、运行结果或可靠文档支撑；不能仅根据函数名、注释或关键词猜测。
3. **Risk-based verification**：成熟常用功能不重复做大规模正确性验证；低频、关键物理功能和组合功能提高审查深度。
4. **One logical capability per task**：每次只审一个逻辑功能。可记录相邻功能的关联证据，但最终分类分别登记。
5. **No premature interface design**：Stage 2 只识别事实、能力边界和缺口，接口/类/文件组织留到 Stage 4。

---

## 3. 四层审查深度

### L1 — 功能存在性（Existence）

确认功能是否真实存在于当前 RMC 代码链中。至少定位：

- 输入/启用入口；
- 核心状态变量或数据结构；
- 关键类/函数；
- 实际执行位置；
- 输出或下游消费位置。

必须尽量形成调用链，而不是只给关键词搜索结果。

### L2 — 需求匹配性（Requirement Match）

将 RMC 实际能力与 `01_双向迭代基础框架_方法与功能需求.md` 中冻结需求逐项对照。

例如“存在 Adjoint 模式”不等价于“满足第一版多群 Adjoint + 空间–能群 Field + RE + WW 组合需求”。

### L3 — 组合兼容性（Integration Compatibility）

检查两个单独可用的功能在组合使用时是否仍然成立。例如：

- Adjoint transport + Weight Window；
- Adjoint transport + spatial-energy tally；
- WW + multigroup field tally；
- Bootstrap Analog Forward + field/RE 输出。

不得由“功能 A 存在、功能 B 存在”直接推断“A+B 可用”。

### L4 — 针对性正确性验证（Targeted Verification）

仅在必要时进行。适用情形包括：

- 功能使用频率低或长期未维护；
- 实现涉及关键物理变换；
- 文档与源码行为不一致或不明确；
- 组合使用缺少既有测试；
- 静态代码不足以判断正确性。

可采用：已有回归测试、已有算例、最小运行验证、数值对照等。若当前无法验证，必须明确写“未验证”，不得以推测替代。

---

## 4. 证据要求

每个源码结论至少记录：

```text
RMC branch / commit
file path
class / function / symbol
line range（以本次审查 checkout 为准）
调用关系
该证据支持的具体结论
```

优先使用 `file:function:line` 形式。

对关键物理结论，不能只引用注释；需要追踪实际执行逻辑。若行号会随版本变化，必须同时记录审查时的 RMC commit SHA。

运行验证必须记录：

- 输入算例/路径；
- 运行命令；
- RMC commit；
- 关键输出原文；
- 未覆盖的验证范围。

---

## 5. 单项审查统一输出模板

每个功能审查任务的 README 至少包含以下内容。

### A. Requirement

原样说明本框架需要什么，不由 Agent 自行重定义需求。

### B. Existing Implementation

记录输入入口、关键文件/函数/数据结构和调用链。

### C. Actual Behavior

按 `Input → Processing → Output` 解释程序真正做了什么。

### D. Requirement Gap

逐项列出满足、部分满足、未知或不满足的子需求。

### E. Verification Evidence

列出静态源码、已有测试、已有算例和必要的运行证据，并明确哪些未验证。

### F. Final Classification

按第 6 节分类给出唯一主分类；如存在多个问题，可在备注中记录次级风险。

### G. Open Questions / Next Action

只给出下一步需要调查、验证或进入 Stage 3 的事项；不得在 Stage 2 内直接修复。

---

## 6. 统一分类标准

- **A — Ready**：已有且满足第一版框架需求，可直接复用。
- **B — Extend**：主体能力已有，但需要有限扩展才能满足需求。
- **C — Verify**：看起来具备所需能力，但关键正确性或行为尚缺充分证据。
- **D — Integration issue**：单项功能存在，但与所需上下游功能组合时存在不兼容或明显障碍。
- **E — Defect**：已有实现存在明确错误、失效逻辑或与理论/预期行为不符。
- **F — Missing**：所需能力不存在，需要新增实现。

Stage 2 只给分类和证据。B/E/F 以及需要代码改动的 D，进入 Stage 3 后另立任务，由用户再次拍板。

---

## 7. 第一版建议审查顺序

按框架依赖关系和风险排序：

1. **F02 — 多群 Adjoint transport**：先确认伴随输运本体和关键物理实现。
2. **F03 — Adjoint source**：确认目标响应驱动的伴随源定义能力。
3. **F06 + F07 — Adjoint spatial-energy field / RE**：确认伴随场及统计误差获取链路；最终仍分别分类。
4. **F04 — Adjoint + WW**：重点检查组合兼容性。
5. **F08 — WW 输入与应用链路**：确认给定空间–能量 WW 后的 splitting / roulette 链路。
6. **F05 + F07 + F12 — Forward field / RE / Bootstrap 组合**：确认低粒子数 Analog Forward 能否输出第一版 Bootstrap 所需场。
7. **F09 — Response 与 FOM 所需信息**：确认响应、RE 与计时信息来源；FOM 公式本身可属于框架层。
8. **F10 — Field Reconstruction 数据边界**：确认现有输入/输出能力是否足以支撑方法无关场处理边界。
9. **F11 — 固定次数双向迭代调度基础**：确认可复用的运行/调度能力及缺口。
10. **F01 — Forward fixed-source MC**：作为成熟基础能力记录事实，不做无必要的全面正确性重验。

审查过程中允许因源码依赖调整读取顺序，但不得改变各功能的独立结论和分类。

---

## 8. 第一项正式审查

Stage 2 第一项任务固定为：

> **F02 — Multigroup Adjoint Transport Audit**

任务档案：`MLVR_develop/20260824_04_f02-mg-adjoint-transport-audit/`

第一轮以只读源码审查为主。若静态证据不足以确认关键物理正确性，应记录为 C — Verify，并提出最小验证方案，而不是在未验证情况下直接判定正确。

---

## 变更记录

- 2026-08-24 · 建立 Stage 2 统一审查协议与 A–F 分类体系 · 关联 `MLVR_develop/20260824_03_stage2-audit-protocol/`
