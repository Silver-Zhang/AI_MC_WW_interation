# RMC功能审查矩阵

## 目的

记录双向迭代WW框架所需功能与RMC现有能力之间的对应关系。

## 分类标准

- A：已有且满足需求
- B：已有但需要扩展
- C：已有但正确性需要核查
- D：功能存在但组合使用存在问题
- E：功能缺失

## 当前状态

| ID | 功能需求 | RMC状态 | 备注 |
|---|---|---|---|
| F01 | Forward fixed-source MC | 待审查 | |
| F02 | 多群 Adjoint transport | 待审查 | |
| F03 | Adjoint source定义 | 待审查 | |
| F04 | Adjoint + WW兼容性 | 待审查 | |
| F05 | Forward field tally | 待审查 | |
| F06 | Adjoint field tally | 待审查 | |
| F07 | Field统计与RE输出 | 待审查 | |
| F08 | WW输入与应用链路 | 待审查 | |
| F09 | Response统计与FOM | 待审查 | |

## 说明

功能审查阶段只关注与新框架相关的能力，不重复验证成熟且无关功能。
