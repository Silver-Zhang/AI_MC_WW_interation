# ML-VR 物理导读

> 面向理解中子输运、伴随方程和减方差的读者；不要求了解 RMC 的 C++ 实现或开发流程。

## 如何组织

这里按**物理功能**而不是开发任务分类。每个专题独立说明：物理原理、RMC 实际计算流程、验证状态、已知风险和技术证据入口。开发档案负责保存完整源码审查与原始运行材料；本目录负责把稳定结论翻译成物理语言。

## 当前专题

| 专题 | 内容 | 当前状态 |
|---|---|---|
| [01 RMC 多群伴随输运](01_RMC多群伴随输运/README.md) | standard MGACE fixed-source neutron adjoint 的物理对象、流程、验证和缺陷修复 | **C — Verify** |
| 正向输运 | 后续专题：正向固定源与场统计 | 待建立 |
| 权重窗迭代 | 后续专题：重要性场到 split/roulette 的物理链路 | 待建立 |
| ML 代理模型 | 后续专题：重构模型与物理约束 | 待建立 |
| 无偏性验证 | 后续专题：估计器、权重与统计检验 | 待建立 |

## 当前一句话结论

RMC 当前 standard ASCII MGACE fixed-source neutron adjoint 为 **C — Verify**：W5/W6/W7/W9 均已修复，四类条件角表示、真实 density mesh、NNUBAR=1 与双裂变核混合材料均有强正向 formal 汇总。独立审核发现 angular/density 的逐运行原始输运输出未归档、angular checker 未强制逐 seed 门槛，因此不能将这些汇总独立验收为 A 级证据；正启动证据恢复任务。

该结论不代表完整 photon adjoint、CE、AIS/HDF5 核数据、delayed、并行环境、Windows、反射边界或相邻 F03/F04/F06/F07 能力已验证。W9 的 photon/secondary 两条同形分支虽已修复，但仍只是局部证据。

## 阅读与维护原则

1. 先解释物理对象、正确关系和物理后果，再解释计算步骤。
2. 明确区分物理模型选择、核数据事实、数值抽样、实现错误和未验证风险。
3. 回归通过或单个统计检验通过，不等于完整能力正确。
4. 需要复核时，通过每篇文末的技术证据进入审查档案、脚本和原始日志。
5. 审查、修复或验证改变物理结论时，同步更新对应专题并保留变更记录。

## 证据入口

- [F02 静态物理复核](../MLVR_develop/20260824_05_f02-adjoint-physics-verification/README.md)
- [F02 第一阶段数值验证](../MLVR_develop/20260825_01_f02-adjoint-numerical-verification/README.md)
- [W5 非均匀密度响应级验证](../MLVR_develop/20260825_06_f02-w5-nonuniform-density-reciprocity-verification/README.md)
- [W6 双 nubar 核一致性修复](../MLVR_develop/20260825_07_f02-w6-double-nubar-kernel-consistency-fix/README.md)
- [可裂变响应级互易性验证](../MLVR_develop/20260825_08_f02-fissile-response-reciprocity-verification/README.md)
- [W9 私有角资产与动态确认](../MLVR_develop/20260825_11_f02-angular-density-asset-qualification/README.md)
- [W9 修复与验证](../MLVR_develop/20260825_12_f02-adjoint-negative-one-variable-angular-fix/README.md)
- [W9 photon/secondary 修复与验证](../MLVR_develop/20260826_01_f02-adjoint-photon-negative-angular-audit/README.md)
- [其余条件角表示 formal](../MLVR_develop/20260826_02_f02-remaining-angular-representations/README.md)
- [真实 density mesh formal](../MLVR_develop/20260827_01_f02-density-mesh-hdf5-readiness/README.md)
- [NNUBAR=1/混合材料 formal](../MLVR_develop/20260827_02_f02-nnubar-material-reciprocity/README.md)
- [F02 最终 A 复核](../MLVR_develop/20260827_03_f02-final-a-readiness-review/README.md)
- [RMC 功能审查矩阵](../MLVR_Knowledge/02_RMC功能审查矩阵.md)
- [已知问题与改进建议](../MLVR_Knowledge/06_已知问题与改进建议.md)

## 变更记录

- 2026-08-25：从平铺结论文档重构为按物理功能组织的专题目录；建立首个“RMC 多群伴随输运”专题。
- 2026-08-25：W7 已按粒子模式隔离 neutron/photon 能群上限初始化；纯中子 `c5g7td` 算例恢复运行，完整能力仍因 W5/W6 保持 E。
- 2026-08-25：W5 修复后完成等体积双区域响应级互易性验证；1M 全量批次通过，完整能力仍因 W6 保持 E。
- 2026-08-25：W6 已统一采用 total nubar 核；确定性逐群核/概率差为 0，10,000 历史动态重放覆盖 2,487 条 bank 后继。F02 转为 C — Verify，不宣称 A。
- 2026-08-25：`g6↔g1` 可裂变最终响应正式批次通过五组独立流及合并互易性判据；单代表案例不改变 C — Verify 的完整能力评级。
- 2026-08-25：私有 MGACE 独立 readback 与低光学厚度动态路径确认 W9 负单变量伴随角核支持域越界；完整能力改判 E，停止 density-HDF5 与 A formal。
- 2026-08-25：W9 负单变量公式修正为 `(1+x)`；三 seed 共 1438 对样本零越界且前/伴随逐项一致，CTest/reference/oracle 通过。完整能力恢复 C — Verify，A 门禁不变。
- 2026-08-26：W9 的普通 photon 与 photon→neutron 次级同形分支也经生产动态反例确认并修正为 `(1+x)`；两路径三 seed 各 900 样本零越界，普通 photon 900 对逐项一致。该局部结论不放行完整 photon adjoint。
- 2026-08-27：其余四类条件角表示、真实 density mesh、NNUBAR=1/混合裂变材料的冻结 formal 全部完成；最终风险复核将 standard ASCII MGACE fixed-source neutron adjoint 改判为有界 A — Ready。
- 2026-08-27：Claude 独立审核发现 angular/density formal 的原始逐运行证据和逐 seed 强制接受门槛不足；未发现新的物理 defect，但 F02 下调为 C — Verify，等待证据恢复后重新评估。
