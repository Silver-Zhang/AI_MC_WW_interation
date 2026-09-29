# F11 Persistent Session E0–E4 Dynamic Execution

2026-09-29 · 模式 **C** · **已完成：E0–E4 全部 PASS under experimental lifecycle contract**。

## 1. 目标与范围

将 Task 11 的最小实验协议转为动态证据：E0性能分解、E1 F→F、E2 F→A→F、E3 WW热更新、E4 tally reset/内存Field/RE/G+1。

冻结物理域：H2O、30-group standard MGACE、中子固定源、Cartesian Type=1/Energy=-1/Normalize=1、native track-mesh WW、Linux串行。没有扩大到CE/photon/MPI/OpenMP/burnup/非单位源权重。

**物理解释**：保留模型/核数据库时，每轮仍应代表独立source histories；前轮统计、归一化和伴随缓存不得污染新轮。用同配置fresh结果、状态快照和真实WW查窗共同判断。PASS只对显式实验合同和此模型成立。

## 2. 做法与证据

主要入口：[动态实验报告](F11_E0_E4_Dynamic_Experiment_Report.md)、[机器可读汇总](logs/experiment-summary.json)、[字段级reset合同](logs/run-reset-contract.md)、[私有源码diff](changes.diff)。

- 基线RMC `5cfb0f771d0c5a2127c90d57e51ce672a4e3b616`，共享树始终clean；root起点`f4730fdb036ea8530faab228b2e8c38e81482f6b`。
- task-private源码在`verification/RMC-snapshot/`；[P0/P1 callbacks](verification/harness/probes.cpp)、[driver](verification/harness/driver_main.cpp)、[比较器](verification/harness/compare.py)均已实现和编译。
- [gates原始结果](logs/p0-noninterference.txt)：F/A fresh driver与原CLI exact，P0开关不改变物理结果和RNG端点。
- [E0](verification/E0/README.md)、[E1](verification/E1/README.md)、[E2](verification/E2/README.md)、[E3](verification/E3/README.md)、[E4](verification/E4/README.md)：每项完整判据及raw证据入口。
- [build info](logs/build-info.txt)、[binary hashes](logs/binary-sha256.txt)、[source base hashes](logs/snapshot-base-sha256.txt)、[current snapshot hashes](logs/snapshot-current-sha256.txt)、[最终自检](logs/final-verification.txt)。

实验配置及N/seed/WW：[fixture manifest](verification/fixtures/manifest.json)；输入来自Task11的冻结H2O派生模型。每次`execution.json`保存真实argv/env/cwd/binary hash/exit和parent timing；`.Tally/.out/stdout/stderr/snapshots/history/WW trace`全部保留。

**版本区分**：E1–E4使用已封存v1 binary；E0 v1计时通过但未保存逐run归一化标量，保留为初步记录。补充共用结束点只读collector后，v2 gates与E0均通过，最终E0只采用v2。没有修改reset合同或放宽阈值。[补测说明](logs/endpoint-metadata-amendment.md)。

## 3. 决策

用户本轮[原始任务](logs/user_task_original.txt)明确批准P0/P1、driver/comparator、构建、fresh oracle和E0–E4运行，不需重复审批。只在私有snapshot改动；完成后按第20节同步STATUS/INDEX。

| 变更卡 | 内容 |
|---|---|
| 问题与风险 | 原入口重复全初始化；同进程必须显式处理run/mode/RNG/输出状态 |
| 改动对象 | 私有9个src文件的probes/gate/条件friend access，私有build支持，任务内driver/分析脚本 |
| 不改什么 | 共享RMC、物理算法、基准、F10合同、F02–F09原结论、正式F11 API |
| 因果链 | 清理每轮状态与重建派生数据→原production loop→fresh exact/state/lookup对照 |
| 验证 | 两类baseline gate + 固定E0–E4判据；真实失败输出保留；未现场修复RMC |
| 回滚/隔离 | 实验源/构建/输出全部任务私有；共享RMC无须回滚 |

**人类理解确认（模式C）**：用户任务已经明确限定“PASS under experimental lifecycle contract不能自动推出production persistent支持”，本报告遵守该边界。最终架构没有选择。

## 4. 结论与边界

**结论**：E0/E1/E2/E3/E4全部PASS。正式9轮同进程结果及状态与对应fresh精确一致；模型/XS只初始化一次；E3真实读取WW2；E4得到独立2×30 Field/RE和31个物理edge。

**证据**：最终证据集51进程/56次calculation/705000 histories；包含保留初步记录的全档案为89进程/94次calculation/1360000 histories，所有exit=0，正确性仍由完整判据确定。[inventory](logs/execution-inventory.json)、[真实分析输出](logs/analysis-output.txt)。

**结果解释**：该合同能在冻结子域中复用模型并保持每轮独立性。warm-cache启动/初始化占比为F约2.96%、A约36.88%；不等于实测persistent加速，也不能直接决定架构。

**边界 / 未覆盖到的验证**：H2O无非零裂变项，E2不能证明非零adjoint-fission完整重建；CE/photon/coupled/MPI/OpenMP/burnup/任意源权重/复杂几何/长期多轮内存增长均未验证。没有正式Session/Controller/Field/WW Builder等实现，没有production缺陷修复。

## 5. 过程

1. 立项：采用C模式，原文原样保存；确认指定revision及clean状态。固定任务目录手工建档，避免建档脚本提前改公共台账。
2. 设计：继承Task11阈值和fixture，读取两份审查及Task12复核；在首次数值运行前固定字段级合同、输入与hash。
3. 人拍板：本轮任务已明确授权全部实验步骤；没有重复询问。
4. 实施+自验：私有P0/P1和driver构建；F/A baseline gates；E1–E4 fresh/sequence；E0初步运行，补齐只读metadata后完成最终gates/E0；保留各版本及全部原始证据。编译问题仅涉及实验接入/构建，不修改物理算法。
5. 归档：本任务报告及证据完成；仅同步STATUS/INDEX的实际verdict/入口。共享RMC和KB/Physics Guide/F10合同不变，未commit/push。到此停止，后续独立复核/架构设计由用户决定。
6. 入库（2026-09-29 整理）：档案随根工作区提交入库；`*.ww.tsv`（1.36 GB）、`verification/RMC-snapshot/`（124 MB）与 E1–E4 histories/snapshots trace 留本地，完整性见 `logs/artifact-manifest.sha256`（`sha256sum --check` 校验）。
