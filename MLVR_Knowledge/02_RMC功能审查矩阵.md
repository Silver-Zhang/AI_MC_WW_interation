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
| F02-B | 多群Adjoint物理正确性审查 | 待人工复核（E — Defect；L4 第一阶段已完成） | W5 数值确认；V4 非裂变代表子域互易性通过；W6 动态频数未覆盖；新增 W7 初始化崩溃 | `20260824_f02-adjoint-physics-verification`；`20260825_f02-adjoint-numerical-verification` |
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

对局部密度比例恒为 $r=1$ 且所有裂变核素 `NNUBAR<=1` 的受限子域，当前结论仍为 **C — Verify**。第一阶段 L4 已补齐当前 SHA 的既有回归，并在 H2O 均匀球中验证两个强非对称散射群对；但这只是非裂变 P0 代表案例，尚缺混合材料碰撞估计器、一般几何/源响应、强各向异性方向互易性和可裂变 bank/权重数值验证。F02-B 等待人工复核；在复核和 Stage 3 另立任务前，不修复 RMC、不进入 F03。

2026-08-25 对 Claude 第二轮反驳完成再复核，结论不变：`p_dMatAtomDen` 是未乘局部比例的材料基准成员，权重调用点没有使用带比例 getter；当前核库 `xsdir` 已登记双表 `c5g7td`，且首表两组 $\nu\Sigma_f$ 加权总量不同。即使不依赖 prompt/total 标签，初始化阈值与运行时逐群扣减混用两个不同核且无重要性权重补偿，也构成确定性错误。因此不撤回 W5/W6，完整能力保持 E，受限子域保持 C。

2026-08-25 第一阶段 L4 数值验证补充以下证据：

- 当前 `4d3e1...` 的既有 `fixed_source_adjoint` 回归 1/1 passed，重建结果与 reference 字节一致；这仍只属于 smoke。
- W5 已由 $r=0.5,1,2$ 三个 native source trace 数值复现，首碰撞后权重相对倍率符合 $1/r$，最大相对误差 $2.99\times10^{-5}$。
- 在 $r=1$、`NNUBAR=0` 的 30 群 H2O 均匀球中，两个单向散射群对（14→15、20→22）各用五种子做前向—伴随配对；合并 $z=-0.2587$ 与 $0.0829$，全部逐种子也满足 $|z|\le3$。因此该**代表性非裂变 P0 子域**获得数值正证据，但不足以把整个受限子域改判 A，也不抵消 W5/W6。
- 部署 `10001.01m` 双 nubar 核的群概率最大差仅 $3.10\times10^{-5}$；Pearson 效应量 $w^2=1.07\times10^{-7}$，80% 功效近似需要 73,289,470 个已观测伴随裂变子代。最小动态算例在运行前被新发现的 W7 阻断，故 W6 运行时群频数仍明确标为未覆盖。
- W7：neutron-only MGACE adjoint 初始化仍无条件调用 photon `LocateMgErgGrp()`。30+12 群 H/O 表只出现无关上限告警；没有 photon 群数据的 c5g7td 则访问空数组并 SIGSEGV。该独立缺陷进一步支持完整能力维持 E。

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
- 2026-08-25：完成第一阶段 L4 数值验证：V0 smoke 通过、V2 数值确认 W5、V4 两个非裂变强非对称群对通过互易性判据；V3 量化部署双 nubar 数据功效并发现 W7 neutron-only MGACE 初始化崩溃。完整能力保持 E，受限子域仍不整体放行为 A。
