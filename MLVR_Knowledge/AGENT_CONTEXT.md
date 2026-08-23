# Agent 快速上下文卡片

> 后续 Agent 接手时先读本页；需要细节再翻对应专题文档。

## 当前项目目标

本工作区用于 RMC 双向迭代权重窗（Bidirectional Adaptive Weight Window）基础框架开发。

当前阶段的核心目标不是立即接入 DNN/PINN 等高级机器学习方法，而是首先建立：

```
RMC Monte Carlo capability
        ↓
Field statistics
        ↓
Field processing interface
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

## 当前方法边界（已冻结）

- 第一版采用多群伴随输运。
- 暂不考虑连续能量伴随输运。
- 场数据至少包含：
  - flux field
  - relative error (RE)
- 第一版暂不进行跨 iteration 历史场累计。
- Field Reconstruction 保持方法无关，不绑定具体 ML 模型。
- 第一阶段目标是基础框架，而非最终 AI 算法。

## 开发流程

所有任务遵循：

```
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
- `MLVR_Knowledge/DECISIONS.md`

## 当前阶段

Stage 0: Workflow and Knowledge Baseline

下一阶段：

Stage 1: Framework Functional Requirement Analysis

后续才进入：

- RMC 功能审查
- 接口设计
- 模块连接
- 基础框架实现
- 简单场重构方法验证
