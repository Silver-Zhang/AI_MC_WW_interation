# RMC功能审查矩阵

## 目的

记录双向迭代WW基础框架所需功能与RMC现有能力之间的对应关系。

Stage 2 将依据本矩阵逐项进行只读审查；当前文件只定义审查对象，不预判 RMC 实现状态。统一审查方法见 `03_RMC功能审查规范.md`。

## 分类标准

- **A — Ready**：已有且满足第一版框架需求，可直接复用。
- **B — Extend**：主体能力已有，但需要有限扩展。
- **C — Verify**：看起来已有，但关键正确性或行为仍缺充分证据。
- **D — Integration issue**：单项功能存在，但组合使用存在问题。
- **E — Defect**：已有实现存在明确错误或失效逻辑。
- **F — Missing**：所需能力不存在，需要新增实现。

Stage 2 只分类和留证据，不在审查任务中直接修复。

## 当前状态

| ID | 功能需求 | RMC状态 | 审查重点/备注 | 任务档案 |
|---|---|---|---|---|
| F01 | Forward fixed-source MC | 待审查 | Bootstrap 与正式 Forward iteration 的成熟基础能力；仅记录事实，不做无必要的全面重验 | — |
| F02 | 多群 Adjoint transport | **已立项，待本地只读审查** | 重点核查实际物理实现、调用链和可用状态 | `MLVR_develop/20260824_f02-mg-adjoint-transport-audit/` |
| F03 | Adjoint source定义 | 待审查 | 是否能按目标响应定义第一版所需伴随源 | — |
| F04 | Adjoint + WW兼容性 | 待审查 | 重点检查两个低频/组合功能是否真正兼容 | — |
| F05 | Forward spatial-energy field tally | 待审查 | 是否可输出与第一版 Field 定义一致的空间网格×能群场 | — |
| F06 | Adjoint spatial-energy field tally | 待审查 | 是否可输出伴随空间网格×能群场 | — |
| F07 | Field统计与RE输出 | 待审查 | Forward/Adjoint 每个空间–能群位置是否能获得 RE | — |
| F08 | WW输入与应用链路 | 待审查 | 给定空间–能量 WW 后能否进入 splitting / roulette 输运链路 | — |
| F09 | Response统计与FOM所需信息 | 待审查 | 正式 Forward iteration 的目标响应、RE及计时/评价信息 | — |
| F10 | Field Reconstruction数据边界 | 待审查 | RMC 现有数据输出/输入能力能否支撑后续方法无关场处理边界 | — |
| F11 | 固定次数双向迭代调度基础 | 待审查 | 当前 RMC 是否已有可复用的多阶段调度/重复运行机制；若无则后续新增 | — |
| F12 | Bootstrap所需直接模拟与场输出链路 | 待审查 | Analog Forward → field+RE → WW_A(1) 所需现成功能组合 | — |

## Stage 1 已冻结的第一版约束

- Field = 空间网格 × 能群上的 mean field + RE。
- Forward/Adjoint Field 数据规范尽量统一，但物理语义严格区分。
- 第一版只做多群 Adjoint。
- 第一版固定 iteration 次数，不做自动收敛终止。
- 正式 iteration 前存在独立 Bootstrap Stage。
- Bootstrap 第一版为低粒子数 Analog Forward MC。
- Bootstrap 与正式 iteration 使用相同 Field mesh 和能群结构。
- 第一版不做跨 iteration 历史场累计。
- 第一版不绑定高级机器学习算法。

## Stage 2 审查顺序

第一版按风险和依赖关系推进：

`F02 → F03 → F06/F07 → F04 → F08 → F05/F07/F12 → F09 → F10 → F11 → F01`

若一次审查中发现相邻功能证据，可记录交叉引用，但每个功能必须独立给出最终状态和分类。

## 说明

功能审查阶段只关注与新框架直接相关的能力，不重复验证 RMC 已成熟且与本框架无关的功能。

对 RMC 中不常用、理论上需要特别确认或组合后可能失效的功能（尤其多群 Adjoint、Adjoint + WW、Adjoint field tally），应提供更强的源码与必要数值证据。

## 变更记录

- 2026-08-24 · Stage 2 采用 A–F 六类审查体系，F02 作为首项正式审查立项 · 关联 `MLVR_develop/20260824_stage2-audit-protocol/`
