# Agent 快速上下文卡片

> 后续 Agent 接手时先读本页；需要细节再翻对应专题文档。

## 当前项目目标

本工作区用于 RMC 双向迭代权重窗（Bidirectional Adaptive Weight Window）基础框架开发。

当前核心目标不是立即接入 DNN/PINN 等高级机器学习方法，而是首先建立：

```text
RMC Monte Carlo capability
        ↓
Field statistics
        ↓
Field processing boundary
        ↓
Weight Window update
        ↓
Forward–Adjoint iterative framework
```

## 当前开发原则

1. RMC 是成熟蒙特卡罗软件，优先复用已有功能。
2. 不提前修改 RMC 架构，先完成需求分析和功能审查。
3. 先确认算法需求，再检查 RMC 是否满足。
4. 功能确认后，再分析接口并逐步连接。
5. 一次只处理一个逻辑功能，并进行记录和验证。
6. 方案由用户逐阶段拍板，Agent 不得自行跨阶段扩展设计。
7. Stage 2 严格执行 `Audit ≠ Repair`：发现问题只记录证据和分类，不修改 RMC 源码。

## 第一版方法边界（已冻结）

- 第一版采用多群 Adjoint transport。
- 暂不考虑连续能量伴随输运。
- Field = 空间网格 × 能群上的 mean field + relative error (RE)。
- Forward/Adjoint Field 数据规范尽量统一，但物理语义和生命周期严格区分。
- 第一版暂不进行跨 iteration 历史场累计。
- Field Reconstruction 保持方法无关，不绑定具体 ML 模型。
- 第一版采用用户给定的固定 iteration 次数，不做自动收敛终止。

## Bootstrap Stage（已冻结）

正式 iteration 前设置独立 Bootstrap Stage：

```text
Low-particle Analog Forward MC
        ↓
Bootstrap Forward Field + RE
        ↓
Field Reconstruction
        ↓
WW_A(1)
```

第一版 Bootstrap：

- 使用真实物理问题；
- 不使用 WW；
- 不修改材料密度；
- 与正式 iteration 使用相同 Field mesh 和能群结构；
- 不属于正式 iteration；
- 不参与正式 FOM 比较；
- 不进入跨 iteration 历史统计；
- 不作为最终物理结果。

后续可研究 reduced-density / auxiliary-VR / external-field / multi-stage Bootstrap，但第一版不实现。

## 第一版正式双向迭代

```text
WW_A(k)
  ↓
Adjoint MC
  ↓
Adjoint Field + RE
  ↓
Field Reconstruction
  ↓
WW_F(k)
  ↓
Forward MC
  ↓
Forward Field + RE
  ↓
Field Reconstruction
  ↓
WW_A(k+1)
```

正式 iteration 从 `k = 1` 开始。

## Stage 2 审查规则

当前已进入 **Stage 2 — RMC Existing Capability Audit**。

统一协议：`MLVR_Knowledge/03_RMC功能审查规范.md`。

审查链：

```text
Requirement → Existence → Actual Behavior → Requirement Match
→ Integration Compatibility → Targeted Verification → Classification
```

分类：

- A Ready
- B Extend
- C Verify
- D Integration issue
- E Defect
- F Missing

源码证据必须尽量记录 `RMC commit + file:function:line`。不得仅凭函数名、注释或关键词宣称功能正确。

## 当前正式任务

**F02 — Multigroup Adjoint Transport Audit** 的静态审查、第一阶段 L4 数值验证和 W5/W6/W7/W9 Stage 3 修复均已完成；W9 已补全普通 photon 与 photon→neutron 次级同形分支。

任务档案：

- `MLVR_develop/20260824_04_f02-mg-adjoint-transport-audit/`：存在性审查；
- `MLVR_develop/20260824_05_f02-adjoint-physics-verification/`：物理静态复核；
- `MLVR_develop/20260825_01_f02-adjoint-numerical-verification/`：V0/V2/V4/V3 数值验证。
- `MLVR_develop/20260825_05_f02-w5-local-density-adjoint-weight-fix/`：W5 修复与密度不变性验证。
- `MLVR_develop/20260825_06_f02-w5-nonuniform-density-reciprocity-verification/`：W5 等体积双区域响应级互易性验证。
- `MLVR_develop/20260825_04_f02-w7-neutron-only-adjoint-init-fix/`：W7 修复与回归验证。
- `MLVR_develop/20260825_07_f02-w6-double-nubar-kernel-consistency-fix/`：W6 total nubar 核一致性修复与验证。
- `MLVR_develop/20260825_11_f02-angular-density-asset-qualification/`：私有 MGACE 资格化与 W9 低光学厚度动态确认。
- `MLVR_develop/20260825_12_f02-adjoint-negative-one-variable-angular-fix/`：W9 一行根因修复与三种子动态验证，已完成。
- `MLVR_develop/20260826_01_f02-adjoint-photon-negative-angular-audit/`：W9 photon/secondary 两行根因修复、生产 ABI 探针与三种子动态验证，已完成。

当前结论：审查范围内的 standard MGACE fixed-source neutron adjoint 为 **C — Verify**，不是 A。W9 已把 neutron、普通 photon 和 photon→neutron 次级的负单变量伴随分支由 `(1-x)` 修正为 `(1+x)`。neutron 三 seed 共 1438 对逐项一致；新增两条 photon 路径三 seed 各 900 样本零越界，合并 $z=-0.289$ 与 $1.792$，普通 photon 900 对前/伴随逐项一致。既有 CTest 1/1 和 reference 完整性通过。

W5/W6/W7 已提交为 RMC `6d2087518e0d9f23574d629f5fde361c79f519e4`（未 push）。W9 三行修改当前尚未 commit，均在 `src/GetMgExitErgMu.cpp`：neutron 一行归属任务 12，photon/secondary 两行归属任务 20260826_01；修复后二进制 SHA256 `8fff3f0f...f13c2`。不更新 reference/benchmark；官方 Table F.52 原文与完整 photon/耦合粒子能力仍未验证，不能据此评为 A。

F03 已立项为 `MLVR_develop/20260825_09_f03-adjoint-source-definition-audit/`，当前待设计。初始只读定位显示 `ADJOINT` 卡负责启用模式/最大能量，`SampleFixSource()` 复用通用外源采样后标记伴随粒子；是否存在足够的目标响应到源表达能力仍须完整审查，不得提前评为 Ready。

面向物理读者的解释已按物理专题整理到 `MLVR_Physics_Guide/`；首个专题为 `01_RMC多群伴随输运/`。后续若修复改变 W5/W6/W7/W9 的状态、物理影响或适用边界，除更新技术证据文档外，还必须同步更新该专题。

## 开发流程

所有任务遵循：

```text
需求分析
 ↓
设计/定位
 ↓
用户决策冻结
 ↓
实施/审查
 ↓
测试与记录
 ↓
归档
```

详细规则见：

- `AGENTS.md`
- `MLVR_Knowledge/00_开发总纲与阶段路线.md`
- `MLVR_Knowledge/01_双向迭代基础框架_方法与功能需求.md`
- `MLVR_Knowledge/02_RMC功能审查矩阵.md`
- `MLVR_Knowledge/03_RMC功能审查规范.md`
- `MLVR_Knowledge/DECISIONS.md`

## 当前阶段

- Stage 0：基础工作流已建立。
- Stage 1：第一版框架功能需求基线已冻结。
- **Stage 3：W5/W6/W7/W9 已修复并验证，W9 photon/secondary 同形分支已补全；F02 评级保持 C — Verify。**

W5/W6/W7 已 commit、未 push；W9 三行已修改但未 commit；reference/benchmark 未更新。A formal 仍缺其余角表示、density mesh、裂变/材料矩阵和冻结统计验证，完整 photon adjoint 也未获放行。
