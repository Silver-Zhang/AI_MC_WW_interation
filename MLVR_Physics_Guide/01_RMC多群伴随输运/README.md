# RMC 多群伴随输运

## 一句话结论

在当前冻结快照（RMC 3.5.0、`Neural_Network_WW_Iteration`、base `6d208751...` 加 W9 三行 diff `5eec92f9...c756`、binary `8fff3f0f...f13c2`、standard ASCII MGACE、Linux serial、`ais=OFF`）下，RMC 的 fixed-source neutron adjoint 为 **C — Verify**：没有新增的已证实物理 defect，但 angular/density formal 的原始逐运行证据与逐 seed 接受门槛尚未独立闭合。

## 适用范围

本专题主体只讨论 `MGACE + FIXEDSOURCE + ADJOINT ADJOINTCALCULATION=1` 的中子伴随路径。W9 条目额外记录了普通 photon 与 photon→neutron 次级的同形条件角核验证，但这不放行完整 photon/耦合粒子能力；continuous-energy、AIS/HDF5、GPT/sensitivity、伴随源语义、伴随场/RE、权重窗接口或 ML 控制器也不在放行范围。

## 阅读地图

1. [功能逻辑与物理对象](01_功能逻辑与物理对象.md)：先理解程序正在追踪什么物理对象，以及每步怎样组织。
2. [流程图与时序图](02_流程图与时序图.md)：用六张图看初始化、单历史、银行、缺陷位置及修复逻辑。
3. [当前能力与验证结论](03_当前能力与验证结论.md)：区分已确认缺陷、局部正证据和未验证边界。
4. [已确认缺陷的物理解读](04_三个已确认缺陷的物理解读.md)：理解 W5/W6/W7/W9 如何影响物理结果，以及修复状态。

## 当前状态

| 项目 | 状态 |
|---|---|
| P0 群间转置机制 | 静态可追溯；V4 在两个指定非裂变群对未检测到显著差异 |
| W5 局部密度权重 | 已修复；首碰撞权重恢复为 $1:1:1$，等体积双区域 1M 响应级互易性批次通过 |
| W6 双 nubar 裂变核 | 已修复；运行时与初始化统一使用 total 核，逐群核/概率差为 0，动态 bank 路径可达，单一裂变主导响应案例通过互易性判据 |
| W7 photon 群初始化 | 已修复并验证；neutron-only `c5g7td` 正常完成 10,000 个源历史 |
| W9 负单变量角核 | neutron、普通 photon、photon→neutron 次级均已修复；neutron 1438 对、普通 photon 900 对逐项一致，两条 photon 路径各 900 样本零越界 |
| 其余条件角表示 | 四类 × forward/adjoint × 五 seeds，40/40 clean；40,000 个生产样本通过支持域、矩、方差/Pearson 门槛 |
| HDF5 density mesh | 两区域读回、位置依赖和 10/10 clean formal 通过，合并 $z=0.0984$ |
| NNUBAR=1/混合裂变材料 | 20/20 clean formal 通过，合并 $z=0.9563/0.3748$ |
| 完整能力 | **C — Verify**；任务 `20260827_04_f02-formal-evidence-recovery` 完成独立 raw-evidence formal 前不得升级 A |

## 技术证据

- [F02-B 静态审查](../../MLVR_develop/20260824_05_f02-adjoint-physics-verification/README.md)
- [F02 数值验证](../../MLVR_develop/20260825_01_f02-adjoint-numerical-verification/README.md)
- [W5 修复与验证](../../MLVR_develop/20260825_05_f02-w5-local-density-adjoint-weight-fix/README.md)
- [W5 非均匀密度响应级验证](../../MLVR_develop/20260825_06_f02-w5-nonuniform-density-reciprocity-verification/README.md)
- [W7 修复与验证](../../MLVR_develop/20260825_04_f02-w7-neutron-only-adjoint-init-fix/README.md)
- [W6 修复与验证](../../MLVR_develop/20260825_07_f02-w6-double-nubar-kernel-consistency-fix/README.md)
- [可裂变响应级互易性验证](../../MLVR_develop/20260825_08_f02-fissile-response-reciprocity-verification/README.md)
- [W9 私有角资产与动态确认](../../MLVR_develop/20260825_11_f02-angular-density-asset-qualification/README.md)
- [W9 修复与验证](../../MLVR_develop/20260825_12_f02-adjoint-negative-one-variable-angular-fix/README.md)
- [W9 photon/secondary 修复与验证](../../MLVR_develop/20260826_01_f02-adjoint-photon-negative-angular-audit/README.md)
- [其余条件角表示 formal](../../MLVR_develop/20260826_02_f02-remaining-angular-representations/README.md)
- [真实 density mesh formal](../../MLVR_develop/20260827_01_f02-density-mesh-hdf5-readiness/README.md)
- [NNUBAR=1/混合材料 formal](../../MLVR_develop/20260827_02_f02-nnubar-material-reciprocity/README.md)
- [最终 A 复核](../../MLVR_develop/20260827_03_f02-final-a-readiness-review/README.md)
- [功能审查矩阵](../../MLVR_Knowledge/02_RMC功能审查矩阵.md)
- [问题台账](../../MLVR_Knowledge/06_已知问题与改进建议.md)
