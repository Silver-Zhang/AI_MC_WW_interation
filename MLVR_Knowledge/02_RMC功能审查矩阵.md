# RMC功能审查矩阵

## 目的

记录双向迭代WW基础框架所需功能与RMC现有能力之间的对应关系。

Stage 2 依据本矩阵逐项进行只读审查。审查不直接修复代码。统一方法见 `03_RMC功能审查规范.md`。

## 分类标准

- A — Ready：已有且满足第一版框架需求，可直接复用。
- B — Extend：主体能力已有，但需要有限扩展。
- C — Verify：功能或实现机制存在，但关键正确性/适用范围仍需验证。
- D — Integration issue：单项功能存在，但组合使用存在问题。
- E — Defect：已有实现存在明确错误。
- F — Missing：所需能力不存在。

## 当前状态

| ID | 功能需求 | 当前状态 | 审查重点 | 任务 |
|---|---|---|---|---|
| F01 | Forward fixed-source MC | 待审查 | Bootstrap与正式Forward基础能力 | — |
| F02-A | 多群Adjoint transport功能存在性 | 已完成 | 入口、调用链、实际行为 | `20260824_f02-mg-adjoint-transport-audit` |
| F02-B | 多群Adjoint物理正确性审查 | 进行中 | 算子转置、碰撞抽样、角处理、裂变、数值验证 | `20260824_f02-adjoint-physics-verification` |
| F03 | Adjoint source定义 | 待审查 | 目标响应驱动伴随源 | — |
| F04 | Adjoint + WW兼容性 | 待审查 | 组合功能正确性 | — |
| F05 | Forward spatial-energy field tally | 待审查 | 输出空间×能群场 | — |
| F06 | Adjoint spatial-energy field tally | 待审查 | 输出伴随空间×能群场 | — |
| F07 | Field统计与RE输出 | 待审查 | 统计误差定义与输出 | — |
| F08 | WW输入与应用链路 | 待审查 | splitting/roulette接口 | — |
| F09 | Response统计与FOM | 待审查 | 响应、RE、时间统计 | — |
| F10 | Field Reconstruction数据边界 | 待审查 | RMC与外部重构接口 | — |
| F11 | 固定次数双向迭代调度基础 | 待审查 | 多阶段运行组织 | — |
| F12 | Bootstrap直接模拟链路 | 待审查 | Analog Forward→field+RE→WW_A(1) | — |

## F02当前结论

F02-A 已确认默认标准 ACE 多群路径存在固定源伴随输运链。

F02-B 继续审查伴随输运物理正确性。在完成以下内容前，不将 F02 标记为 Ready：

- 多群散射转置关系；
- 伴随碰撞抽样与权重修正；
- 角变量处理；
- 伴随裂变处理；
- 最小离散伴随互易性验证。

## Stage 2原则

- Audit 与 Repair 分离。
- 代码证据优先于函数名称和注释。
- 发现疑点只记录，不在审查任务中修改源码。
- 物理正确性不足时采用 Verify，而不是推测通过。

## 变更记录

- 2026-08-24：新增 F02-B 伴随物理正确性审查阶段，F02-A 与 F02-B 分离。
