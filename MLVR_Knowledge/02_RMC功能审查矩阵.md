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
| F02-B | 多群Adjoint物理正确性审查 | 待人工复核（E — Defect） | 两项确定性缺陷；受限子域仍为 C — Verify | `20260824_f02-adjoint-physics-verification` |
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

F02-B 已完成源码层独立复核，完整 standard ACE、`ais=OFF`、MGACE fixed-source neutron adjoint 能力主分类为 **E — Defect**：

1. 局部密度比例 $r\ne1$ 时，散射与裂变权重相对正确值多出 $1/r$；
2. `NNUBAR>1` 时，伴随初始化使用 total nubar，运行时裂变前驱群抽样使用 prompt nubar，本地裂变 MGACE 数据证明路径可达。

同时纠正两项原草稿判断：`minErgGrp` 是合法群范围外的递减哨兵，不漏边界群；在伴随方向解释为正向物理方向反向时，方位对称且仅依赖 $\mu$ 的条件角核交换方向后 $\mu$ 不变，不能仅因未显式转置 P1/P2 或应用 $(-1)^\ell$ 判错。

对局部密度比例恒为 $r=1$ 且所有裂变核素 `NNUBAR<=1` 的受限子域，当前结论仍为 **C — Verify**，因为尚缺当前 SHA 的实际回归、非对称散射离散内积、强各向异性方向互易性和可裂变 bank/权重数值验证。F02-B 等待人工复核；在复核和 Stage 3 另立任务前，不修复 RMC、不进入 F03。

2026-08-25 对 Claude 第二轮反驳完成再复核，结论不变：`p_dMatAtomDen` 是未乘局部比例的材料基准成员，权重调用点没有使用带比例 getter；当前核库 `xsdir` 已登记双表 `c5g7td`，且首表两组 $\nu\Sigma_f$ 加权总量不同。即使不依赖 prompt/total 标签，初始化阈值与运行时逐群扣减混用两个不同核且无重要性权重补偿，也构成确定性错误。因此不撤回 W5/W6，完整能力保持 E，受限子域保持 C。

## Stage 2原则

- Audit 与 Repair 分离。
- 代码证据优先于函数名称和注释。
- 发现疑点只记录，不在审查任务中修改源码。
- 物理正确性不足时采用 Verify，而不是推测通过。
- 标准路径可达且数学后果确定的错误采用 Defect；Audit 结论不自动授权 Repair。

## 变更记录

- 2026-08-24：新增 F02-B 伴随物理正确性审查阶段，F02-A 与 F02-B 分离。
- 2026-08-24：F02-B 独立复核完成，确认非单位局部密度权重与双 nubar 裂变核两项 E 级缺陷；受限子域保持 C — Verify，状态转为待人工复核。
- 2026-08-25：完成 Claude 第二轮反驳再复核；由成员/getter 数据流、`xsdir` 登记和双 nubar 实表核差异确认原 E/C 分层结论不变。
