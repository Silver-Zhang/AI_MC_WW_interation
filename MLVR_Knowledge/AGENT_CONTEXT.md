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
5. 一次只实现一个小功能，并进行记录和验证。
6. 方案由用户逐阶段拍板，Agent 不得自行跨阶段扩展设计。

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

## 开发流程

所有任务遵循：

```text
需求分析
 ↓
设计/定位
 ↓
用户决策冻结
 ↓
实施
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
- `MLVR_Knowledge/DECISIONS.md`

## 当前阶段

Stage 0：工作流与知识库基础已建立。

Stage 1：第一版双向迭代框架功能需求基线已形成，等待用户最终确认后进入 Stage 2。

下一阶段：

Stage 2：RMC 现有功能审查。

Stage 2 开始时应先确定审查顺序和单项审查记录模板，然后由本地 Agent 对 RMC 进行只读调查；在用户拍板前不得修改 RMC 源码。
