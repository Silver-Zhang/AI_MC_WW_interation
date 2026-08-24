# Task: stage1-framework-requirements

日期：2026-08-24

## 1. 任务目标

把网页端已经逐轮讨论并由用户确认的第一版双向迭代 WW 基础框架功能需求整理为可追溯的 Stage 1 需求基线，为下一阶段 RMC 现有功能审查提供唯一需求依据。

## 2. 本次范围

仅修改项目知识与开发档案，不修改 RMC 或 AIMC_WWiteration 源码。

本次重点：

- 完整定义第一版双向迭代算法链；
- 定义 Field 的最小数据语义；
- 定义 Bootstrap Stage；
- 定义固定 iteration 调度边界；
- 更新设计决策记录；
- 对齐下一阶段 RMC 功能审查矩阵。

明确不做：

- RMC 源码审查；
- RMC 源码修改；
- C++ 类/函数/文件设计；
- Field Reconstruction 具体算法设计；
- DNN/PINN/GNN/FNO 开发；
- 连续能量伴随输运；
- 跨 iteration 历史场累计。

## 3. 用户已拍板的 Stage 1 决策

1. 第一版从多群 Adjoint transport 开始，不考虑连续能量伴随输运。
2. Field 数据至少包含 MC mean field 与对应 RE。
3. 第一版 Field 只考虑空间网格 × 能群，不包含角度、时间或机器学习特征。
4. Forward 与 Adjoint Field 采用统一数据规范，但物理语义和生命周期严格区分。
5. 第一版暂不做跨 iteration 历史场累计。
6. 第一版使用固定 iteration 次数，不做自动收敛停止。
7. 正式 iteration 前设置独立 Bootstrap Stage。
8. Bootstrap 第一版采用真实物理问题下的低粒子数 Analog Forward MC。
9. Bootstrap 产生 field + RE，经 Field Reconstruction 后生成 `WW_A(1)`。
10. Bootstrap 不属于正式 iteration，不参与正式 FOM、跨 iteration 历史累计或最终物理结果。
11. Bootstrap 与正式 iteration 使用相同 Field mesh 和能群结构。
12. Bootstrap 后续保留降密度、辅助减方差、外部场、多阶段初始化等扩展空间，但第一版不实现。
13. Field Reconstruction 保持方法无关，第一版后续优先采用简单回归/插值等低复杂度方法验证基础框架。

## 4. 本次落库结果

更新：

- `MLVR_Knowledge/01_双向迭代基础框架_方法与功能需求.md`
- `MLVR_Knowledge/02_RMC功能审查矩阵.md`
- `MLVR_Knowledge/DECISIONS.md`
- `MLVR_Knowledge/00_开发总纲与阶段路线.md`

新增：

- `MLVR_develop/20260824_stage1-framework-requirements/README.md`

## 5. Stage 1 结论

第一版功能需求基线已经形成。当前基础框架的逻辑起点为：

```text
Bootstrap Analog Forward
  ↓
Bootstrap Forward Field + RE
  ↓
Field Reconstruction
  ↓
WW_A(1)
  ↓
Adjoint(1)
  ↓
Adjoint Field + RE
  ↓
Field Reconstruction
  ↓
WW_F(1)
  ↓
Forward(1)
  ↓
Forward Field + RE
  ↓
Field Reconstruction
  ↓
WW_A(2)
  ↓
...
```

第一版固定执行用户指定的 K 轮 iteration。

## 6. 下一步

待用户确认 Stage 1 需求基线后进入 Stage 2：RMC 现有功能审查。

Stage 2 应严格依据 `MLVR_Knowledge/02_RMC功能审查矩阵.md` 逐项推进，优先只读调查并保留源码证据，不修改 RMC。

建议第一轮 Stage 2 先讨论并确定“审查顺序与单项审查记录模板”，再把具体只读审查任务交给本地 Agent。
