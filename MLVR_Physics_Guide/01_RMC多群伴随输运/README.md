# RMC 多群伴随输运

## 一句话结论

在当前基线（RMC 3.5.0、`Neural_Network_WW_Iteration`、`6d208751...`、standard ACE、`ais=OFF`）下，RMC 的 fixed-source neutron adjoint 已闭合 W5/W6/W7 三项已知缺陷，当前为 **C — Verify**；仍不能等同于面向任意 MLVR 问题的完整放行。

## 适用范围

本专题只讨论 `MGACE + FIXEDSOURCE + ADJOINT ADJOINTCALCULATION=1` 的中子伴随路径。它不放行 continuous-energy、photon、耦合粒子、AIS/HDF5、GPT/sensitivity、伴随源语义、伴随场/RE、权重窗接口或 ML 控制器。

## 阅读地图

1. [功能逻辑与物理对象](01_功能逻辑与物理对象.md)：先理解程序正在追踪什么物理对象，以及每步怎样组织。
2. [流程图与时序图](02_流程图与时序图.md)：用六张图看初始化、单历史、银行、缺陷位置及修复逻辑。
3. [当前能力与验证结论](03_当前能力与验证结论.md)：区分已确认缺陷、局部正证据和未验证边界。
4. [三个已确认缺陷的物理解读](04_三个已确认缺陷的物理解读.md)：理解 W5/W6/W7 如何影响物理结果，以及当前如何修复。

## 当前状态

| 项目 | 状态 |
|---|---|
| P0 群间转置机制 | 静态可追溯；V4 在两个指定非裂变群对未检测到显著差异 |
| W5 局部密度权重 | 已修复；首碰撞权重恢复为 $1:1:1$，等体积双区域 1M 响应级互易性批次通过 |
| W6 双 nubar 裂变核 | 已修复；运行时与初始化统一使用 total 核，逐群核/概率差为 0，动态 bank 路径可达，单一裂变主导响应案例通过互易性判据 |
| W7 photon 群初始化 | 已修复并验证；neutron-only `c5g7td` 正常完成 10,000 个源历史 |
| 完整能力 | **C — Verify**；已有单一可裂变最终响应正证据，更多材料/群对/几何等扩展验证仍缺失 |

## 技术证据

- [F02-B 静态审查](../../MLVR_develop/20260824_05_f02-adjoint-physics-verification/README.md)
- [F02 数值验证](../../MLVR_develop/20260825_01_f02-adjoint-numerical-verification/README.md)
- [W5 修复与验证](../../MLVR_develop/20260825_05_f02-w5-local-density-adjoint-weight-fix/README.md)
- [W5 非均匀密度响应级验证](../../MLVR_develop/20260825_06_f02-w5-nonuniform-density-reciprocity-verification/README.md)
- [W7 修复与验证](../../MLVR_develop/20260825_04_f02-w7-neutron-only-adjoint-init-fix/README.md)
- [W6 修复与验证](../../MLVR_develop/20260825_07_f02-w6-double-nubar-kernel-consistency-fix/README.md)
- [可裂变响应级互易性验证](../../MLVR_develop/20260825_08_f02-fissile-response-reciprocity-verification/README.md)
- [功能审查矩阵](../../MLVR_Knowledge/02_RMC功能审查矩阵.md)
- [问题台账](../../MLVR_Knowledge/06_已知问题与改进建议.md)
