# 任务总台账

> 一行一个任务。新增由 `new_task.sh` 自动追加，状态变化手工/由 Agent 更新。
> 状态词表见 [README.md](README.md)。

## 进行中 / 已处理

| 立项日期 | 任务 | 类型 | 状态 | 关联KB | 提交 |
| 2026-08-31 | [f02-parallel-statistical-gate-calibration](20260831_02_f02-parallel-statistical-gate-calibration/README.md) | 算法实验 / 统计判据校准 | 已完成 | F02 | `2×1/4×1/2×2/2×4` 共 160/160 结构运行；四配置均 8/8 aggregate 通过；仅 `4×1` seed 41/rank 3 isotropic forward/adjoint Holm 诊断拒绝，保留 strict failed，MPI/OpenMP 仍为 C — Verify |
| 2026-08-31 | [f02-parallel-angular-distribution-verification](20260831_01_f02-parallel-angular-distribution-verification/README.md) | 算法实验 / 并行正确性验证 | 已完成（strict failed） | F02 | 2×1 rank-aware angular strict 通过；4×1 的 seed 41/rank 3 isotropic mean $z=-3.15282$ 失败，按停止规则未运行混合矩阵；MPI/OpenMP 保持 C — Verify |
|---|---|---|---|---|---|
| 2026-08-31 | [f02-mpi4-angular-seed-replication](20260831_03_f02-mpi4-angular-seed-replication/README.md) | 算法实验 / 独立复现 | 已完成 | F02 | 新 seeds `101,103,107,109,113` 的 `4×1` 全角矩阵 40/40 结构通过；8/8 aggregate 通过、零 Holm 拒绝；不改判原 seed 41 strict failed，MPI/OpenMP 仍为 C — Verify |
| 2026-08-30 | [f02-parallel-mpi-openmp-verification](20260830_01_f02-parallel-mpi-openmp-verification/README.md) | 算法实验 / 并行正确性验证 | 已完成（条件性） | F02 | 六配置 runtime/CTest、density 与 fissile 统计、angular 40/配置输运结构通过；独立审计指出未做 multi-rank angular 分布探针，不能扩展 F02 A 的并行作用域 |
| 2026-08-28 | [f02-mpi-off-serial-provenance](20260828_01_f02-mpi-off-serial-provenance/README.md) | 验证基础设施 / 证据恢复 | 已完成 | F02 | 显式 MPI-off fresh build 上 angular 40/40、density 10/10 strict 通过，CTest 1/1、checksum 和独立审计 ACCEPT；严格 serial F02 恢复有界 A |
| 2026-08-27 | [f02-binary-source-identity](20260827_05_f02-binary-source-identity/README.md) | 验证基础设施 / 证据恢复 | 已完成（后续范围收紧） | F02 | 已闭合 source/binary；但该 fresh binary 是 MPI-enabled one-rank execution。task 01 已在严格 MPI-off serial 范围重跑并作为当前 A 证据 |
| 2026-08-27 | [f02-formal-evidence-recovery](20260827_04_f02-formal-evidence-recovery/README.md) | 物理验证 / 证据恢复 | 已完成（raw evidence 恢复） | F02 | 50 条 raw outputs 与 strict gates 均通过；但随后发现 binary banner/source snapshot 身份不闭合，不能单独恢复 A |
| 2026-08-27 | [f02-final-a-readiness-review](20260827_03_f02-final-a-readiness-review/README.md) | 物理审查 / 证据归并 | 已完成（后续证据恢复） | F02 | 原 binary provenance 问题已由 task 05 闭合；serial 定义由 task 01 的 MPI-off fresh matrix 进一步闭合，当前 F02 为有界 A |
| 2026-08-27 | [f02-nnubar-material-reciprocity](20260827_02_f02-nnubar-material-reciprocity/README.md) | 物理验证 / 输入数据资格化 | 已完成 | F02 | 部署 `10005` NNUBAR=1 及 NNUBAR=1 主导的 `10005/10001` 混合裂变材料，各五对 formal 共 20/20 clean；合并 $z=0.9563$ 与 $0.3748$；最终 A 复核已纳入 |
| 2026-08-27 | [f02-density-mesh-hdf5-readiness](20260827_01_f02-density-mesh-hdf5-readiness/README.md) | 物理验证 / 输入数据资格化 | 已完成 | F02 | 私有 HDF5 两区域 mesh 读回、位置依赖 pilot 与五 seed 10/10 clean formal 通过；合并互易性 $z=0.0984$；最终 A 复核已纳入 |
| 2026-08-26 | [f02-remaining-angular-representations](20260826_02_f02-remaining-angular-representations/README.md) | 物理验证 / 验证资产复用 | 已完成 | F02 | 四类 × 前向/伴随 × 五 seeds 的 40/40 clean formal 通过；40,000 样本支持域/矩/离散频数通过；最终 A 复核已纳入；RMC 只读且暂不同步 |
| 2026-08-26 | [f02-adjoint-photon-negative-angular-audit](20260826_01_f02-adjoint-photon-negative-angular-audit/README.md) | 缺陷修复 / 数值验证 | 已完成 | F02 / W9 | photon 与 photon→neutron 两处分支修复；两群 6/6 整程零 Warning/零 Error，三 seed 共 1800 样本零越界；配对/CTest/reference 通过；未 commit |
| 2026-08-25 | [f02-adjoint-negative-one-variable-angular-fix](20260825_12_f02-adjoint-negative-one-variable-angular-fix/README.md) | 缺陷修复 | 已完成 | F02 / W9 | 一行根因修复；三 seed 共 1438 对样本零越界且逐项一致；CTest/reference/oracle 通过；未 commit |
| 2026-08-25 | [f02-angular-density-asset-qualification](20260825_11_f02-angular-density-asset-qualification/README.md) | 物理验证 / 验证资产资格化 | 已完成（E — Defect） | F02 / W9 | 低光学厚度动态确认负单变量伴随角核越界；按停止规则未继续 HDF5/A formal |
| 2026-08-25 | [f02-extended-physics-readiness](20260825_10_f02-extended-physics-readiness/README.md) | 物理验证 | 已完成（C — Verify） | F02 | A 门禁 pilot 暴露 NNUBAR=1 有效响应、真实 density mesh 和强 P1/P2 验证缺口；未修改 RMC |
| 2026-08-25 | [f03-adjoint-source-definition-audit](20260825_09_f03-adjoint-source-definition-audit/README.md) | RMC 只读功能与语义审查 | 待设计 | F03 | 已进入 F03；初始定位为通用外源采样后标记伴随，尚不预判分类 |
| 2026-08-25 | [f02-fissile-response-reciprocity-verification](20260825_08_f02-fissile-response-reciprocity-verification/README.md) | 数值验证 | 已完成 | F02 | 正式 10/10 运行与 5/5 独立流通过；合并 $z=-0.703$；F02 阶段复核保持 C — Verify |
| 2026-08-25 | [f02-w6-double-nubar-kernel-consistency-fix](20260825_07_f02-w6-double-nubar-kernel-consistency-fix/README.md) | 缺陷修复 | 已完成 | W6 | total nubar 核统一；逐群差为 0，动态 bank 可达；已随 W5/W7 提交为 RMC `6d208751...` |
| 2026-08-25 | [f02-w5-nonuniform-density-reciprocity-verification](20260825_06_f02-w5-nonuniform-density-reciprocity-verification/README.md) | 算法实验 / 现有能力验证 | 已完成 | W5 | 200k 原批次严格门槛失败；1M 全量精度升级通过逐种子、分组与总体判据 |
| 2026-08-25 | [f02-w5-local-density-adjoint-weight-fix](20260825_05_f02-w5-local-density-adjoint-weight-fix/README.md) | 缺陷修复 | 已完成 | W5 | 两处权重分母使用局部总原子密度；三种密度权重恢复 $1:1:1$；已随 W6/W7 提交为 RMC `6d208751...` |
| 2026-08-25 | [f02-w7-neutron-only-adjoint-init-fix](20260825_04_f02-w7-neutron-only-adjoint-init-fix/README.md) | 缺陷修复 | 已完成 | W7 | 按粒子模式隔离伴随能群上限；崩溃输入和回归通过；已随 W5/W6 提交为 RMC `6d208751...` |
| 2026-08-25 | [physics-guide-topic-refactor](20260825_03_physics-guide-topic-refactor/README.md) | 文档 | 已完成（复核校正） | F02 / W5 / W6 / W7 | 按物理功能重构导读；校正 tally/银行/吸收语义；补充 W7 修复逻辑与门控图 |
| 2026-08-25 | [human-physics-guide](20260825_02_human-physics-guide/README.md) | 文档 | 已完成 | F02 / W5 / W6 / W7 | 建立 `MLVR_Physics_Guide/`，整理当前结论及三缺陷物理解读；未修改 RMC |
| 2026-08-25 | [f02-adjoint-numerical-verification](20260825_01_f02-adjoint-numerical-verification/README.md) | 算法实验 / 现有能力验证 | 已完成（第一阶段） | F02 / W5 / W6 / W7 | V0 通过；V2 数值确认 W5；V4 两群对互易性通过；V3 功效不足且被 W7 阻断；未修改 RMC/reference |
| 2026-08-24 | `20260824_01_workflow-baseline` | 工作流/知识库基线 | 已完成 | 00 / AGENT_CONTEXT / DECISIONS | GitHub history |
| 2026-08-24 | `20260824_02_stage1-framework-requirements` | 功能需求基线 | 已完成并确认 | 01 / 02 / DECISIONS | GitHub history |
| 2026-08-24 | `20260824_03_stage2-audit-protocol` | 审查规范 | 已完成 | 02 / 03 / DECISIONS | GitHub history |
| 2026-08-24 | `20260824_04_f02-mg-adjoint-transport-audit` | RMC只读功能审查（F02-A） | 已完成 | F02 / 03 | 未修改 RMC |
| 2026-08-24 | `20260824_05_f02-adjoint-physics-verification` | RMC只读物理正确性审查（F02-B） | 待决策 | F02 / W5 / W6 | 独立复核及 Claude 第二轮反驳再复核完成；成员/getter 数据流与已登记双 nubar 实表均维持 W5/W6，完整能力 E、受限子域 C；待人工复核；未修改 RMC |

## 待办储备（来自知识库 06 文档，尚未立项）

按优先级排列，处理时用 `./new_task.sh <短名> <KB编号>` 立项。

| KB编号 | 问题/想法 | 级别 | 优先级 |
|---|---|---|---|
|  |  |  |  |
