# Task: F02-B — Multigroup Adjoint Physics Verification

日期：2026-08-24

状态：Prepared — awaiting local agent execution

## 目标

在 F02-A 确认 RMC 存在多群伴随输运链的基础上，进一步审查其物理实现是否满足 MLVR 双向迭代框架的依赖要求。

本任务不修改源码，只进行物理正确性审查。

## 审查重点

### 1. 数学伴随定义

确认 RMC 当前实现对应的伴随算子定义，包括方向约定、群约定和权重定义。

### 2. 多群散射转置

检查：

$$
\Sigma_s^\dagger(g'\rightarrow g)=\Sigma_s(g\rightarrow g')
$$

是否真实落实到：

- 初始化数据结构；
- 群索引；
- 抽样概率；
- 权重修正。

### 3. 碰撞抽样与权重

检查：

- total cross section 与 adjoint production cross section关系；
- nuclide sampling；
- reaction sampling；
- implicit capture处理。

### 4. 角变量处理

确认各向异性散射情况下伴随角核处理是否满足对应互易关系。

### 5. 伴随裂变

检查：

- \(\chi\nu\Sigma_f\) 转置关系；
- parent/child group；
- bank生成；
- nubar数据处理。

### 6. 数值验证建议

提出最小验证方案：

- 非对称两群散射内积验证；
- 各向异性角核验证；
- 裂变伴随验证。

## 输出格式

最终报告包含：

A. Mathematical definition

B. Scattering transpose audit

C. Collision and weight audit

D. Angular treatment audit

E. Fission treatment audit

F. Verification requirement

G. Final classification

分类：A Ready / C Verify / E Defect

## 约束

- 不修改RMC源码；
- 不进入WW、Field、Source审查；
- 不替代F03/F04/F06/F07任务。
