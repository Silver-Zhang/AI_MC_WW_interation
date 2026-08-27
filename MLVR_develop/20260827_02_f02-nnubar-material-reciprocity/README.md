# f02-nnubar-material-reciprocity

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-27 |
| 状态 | 已完成（NNUBAR/material formal 通过） |
| 任务类型 | 物理验证 / 输入数据资格化 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F02 |
| 涉及文件 | 例：`RMC/src/WeightWindow.h` ／ `AIMC_WWiteration/src/solver.py` |
| 分支 / 提交 | 例：`feat/mlvr-xxx` ／ `abc1234` |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：以部署的 C5G7 standard MGACE 数据实际验证 `NNUBAR=1` 裂变核及含 `NNUBAR=1`/`NNUBAR=2` 两种裂变核的混合材料，在 fixed-source neutron forward/adjoint 标量响应下均可形成有限、非零且统计相容的互易响应。

**范围**：仅写本任务档案、输入卡和分析脚本；只读 `RMC/` 与部署核数据。固定为 serial、`ais=OFF`、7 群 standard MGACE、真空 2 cm 均匀球、同一 cell 标量 track-length tally。不得修改 RMC、reference、benchmark 或核数据。

**验收标准**：pilot 的每个前向/伴随运行须 exit 0、恰有一次完整 source count、stderr 为空、stdout/stderr/inp.out 零 warning/error/NaN/Inf、目标 tally 有限且为正；仅当 pilot 全部通过后，才冻结五对独立 seeds 的 formal manifest。formal 还须每对及 inverse-variance 合并互易性均满足 $|z|\le3$。

**原始材料**：`logs/nnubar_data_audit.txt` 保存本任务对部署核表的只读解析，`logs/SHA256SUMS.txt` 冻结审计和 formal 摘要。原始 stdout/stderr/输入卡保留在任务私有 `pilot/` 与 `formal/`；`pilot_aborted_high_density/` 原样保留了因错误材料密度中止的首次运行。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：已完成的单核 `10001.01m`（NNUBAR locator count=2）`g6↔g1` formal 只证明一条 NNUBAR>1 路径；历史扩展任务中 `10005.01m` 的 `g6↔g1` 20k pilot 前向 RE=1、伴随为 0，因而不能替代本任务的有效群对筛选。密度 mesh 与所有剩余角表示已由独立任务完成，不在此任务重复。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `MLVR_develop/20260825_10_f02-extended-physics-readiness/logs/deployed_mgace_inventory.csv:2-9` | 部署 7 群表中 `10005.01m` 是 fissile 且 NNUBAR locator count=1；`10001.01m` 是 fissile 且 count=2。 |
| 2 | `logs/nnubar_data_audit.txt` | 与 RMC 一基 XSS 访问一致的只读解析显示：`10005` 的最大裂变迁移为 g4→g1，强度 $6.32308961777\times10^{-6}$；历史失败 g6→g1 仅 $8.62086251911\times10^{-7}$。 |
| 3 | `MLVR_develop/20260825_08_f02-fissile-response-reciprocity-verification/results/formal/summary.csv:2` | 单核 NNUBAR>1 先验 formal 的合并 $z=-0.7026348520546188$，不能代替混合材料和 NNUBAR=1 证据。 |

**影响面**：只影响 F02 的证据覆盖范围与分类建议；不涉及接口、基准结果或兼容性改动。该试验不覆盖 delayed、CE、photon、AIS、MPI/OpenMP、Windows 或完整 MLVR 工作流。

**为什么之前没做/没发现**：（可选，但对改进机制很有价值）

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A | 重新筛选 `10005` 最大有效裂变迁移 g4→g1；先做其纯材料及以 NNUBAR=1 为裂变主导的 `10005:10001=0.9999:0.0001` 混合材料 pilot，均通过后冻结两 case × 五独立对的 formal。 | NNUBAR=1 裂变截面远小于 `10001`，pilot 需较多 histories；微量 `10001` 用于使两类 nubar locator 都进入混合材料路径，同时避免其强裂变项掩盖 `10005`。 | ★推荐 |
| B | 仅重跑历史 g6→g1 或仅验证 NNUBAR>1。 | 已有反例/证据，不能覆盖目标。 | 不采用 |
| C（不做/最小改动） | 保持 F02 为 C。 | 不会增加 NNUBAR=1 与混合裂变材料证据。 | 备选 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：方案 A；先执行冻结的 pilot，只有全通过才生成 formal manifest 并执行。
- **决定人 / 日期**：用户 / 2026-08-27（用户确认后续持续按建议选择，直至 F02 的 A 门槛可诚实满足）。
- **理由与约束**：只读 RMC；不得更新核数据、reference 或 benchmark；不得删除失败产物、事后挑选 seeds/样本量/阈值；formal 仅使用 pilot 前写入脚本的固定 seeds 和 population；不 commit/push/切换 RMC 分支。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 读取上下文、台账和历史裂变验证 | `AGENT_CONTEXT.md`、`INDEX.md`、历史任务档案 | 确认本任务是 density mesh/角表示闭合后的下一条 F02 A 前置证据。 |
| 2 | 只读解析 C5G7 `10005`/`10001`/`10006` | 与 RMC 一基索引一致的既有 `screen_mgace_pairs.py` 解析器 | 选定 `10005` 的 g4→g1，而非历史无效 g6→g1；未改生产树或数据。 |
| 3 | 首次 pilot | `pilot_aborted_high_density/` | 初始任务侧材料密度误设为 `10000.0`，导致单条运行持续超过 8 分钟；已中止并原样保留，未将其计入任何结果。 |
| 4 | 修正密度后的 pilot | `generate_cases.py --stage pilot --population 200000` | 4/4 clean、响应有限非零；两个 case 的配对 $|z|$ 分别为 $0.1621$ 和 $1.1095$。 |
| 5 | frozen formal | `generate_cases.py --stage formal --population 1000000` | 20/20 clean；两种材料的全部五对与合并统计均通过。 |

**代码改动**：RMC/AIMC 无改动。任务侧新增 `generate_cases.py` 与 `run_and_analyze.py`；RMC 的 [changes.diff](changes.diff) 只包含既有 W9 未提交差异，不归属本任务。

生成方式：
```bash
git -C ../../RMC diff > changes.diff
# 改原型则：
git -C ../../AIMC_WWiteration diff > changes.diff
```

---

## 6. 验证 / 实验记录（④ · Agent 填，要贴真实输出）

| 验证项 | 命令 | 结果 |
|---|---|---|
| `10005` 裂变群对筛选 | `logs/nnubar_data_audit.txt` | g4→g1 是最大候选，裂变核强度 $6.32308961777\times10^{-6}$。 |
| pilot | `generate_cases.py --stage pilot --population 200000` + `run_and_analyze.py` | 4/4 exit 0、stderr 空、零 warning/error、完整 source count、响应有限非零。 |
| formal | `generate_cases.py --stage formal --population 1000000` + `run_and_analyze.py` | 20/20 clean；两 case 各五对独立流及合并 $|z|\le3$。 |

```
formal_manifest_sha256=60bd815b5ab0e8fd1b95159b95653f4ba356c337071e60f2b9293fd7175aeeac
formal_clean_runs=20/20
nnubar1_pure: R_F=1.4705632104745229e-05, R_A=1.1477480457459034e-05, z=0.9562519705792026
mixed_nnubar1_nnubar2: R_F=2.5991300561588e-05, R_A=2.4296708587753254e-05, z=0.3747657992876843
all_individual_abs_z_le_3=True
formal_statistics_pass=True
```

**实验设置（算法实验必填）**：
- 随机种子：pilot `1009/1013`；formal 五对 `2003/2011`、`2017/2027`、`2029/2039`、`2053/2063`、`2069/2081`；RNG type 2、stride `1000000`。
- 配置快照：7 群、2 cm 真空球、同 cell 标量 track-length tally、`10005` g4↔g1；纯 `10005.01m` 和 `10005:10001=0.9999:0.0001` 的双裂变核混合，材料密度 `1.0` atom/(barn·cm)。
- 依赖版本：Python 3.12.3；RMC 3.5.0 serial `ais=OFF`，binary SHA256 `8fff3f0f534d2a2a116e033a26cf4bb62005c5b6d62b29925423b97bb74f13c2`。
- 基准对比：非 FOM 实验；比较 source/response 能群互换的 forward/adjoint 响应。

**未覆盖到的验证**：仅覆盖 g4↔g1、均匀 2 cm 球和标量 cell tally；未覆盖更多裂变群对、空间非均匀混合、裂变与 density-mesh 组合、强各向异性、其他几何/边界、delayed、photon、CE、AIS、MPI/OpenMP、Windows 或完整 MLVR。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：部署 `10005.01m` 的 NNUBAR locator count=1 及以其为裂变主导的 `10005/10001` 混合材料，均在冻结的前向/伴随响应 formal 中通过。两 case 各 10 条、合计 20/20 clean；每条与合并 $|z|\le3$。
- **遗留问题 / 后续待办**：本任务关闭 NNUBAR=1/多材料裂变门槛，但不能验证更广群对、空间混合或裂变与 density mesh 的组合。最终复核 `20260827_03_f02-final-a-readiness-review` 已裁定开放式“更多几何/边界”不是冻结 F02 门槛，并将有界作用域改判 A；该结论仍不得外推至 photon、CE、AIS、并行环境或未测机制组合。
- **知识库同步**：待完成 F02 总体 A 门槛复核后统一更新 `02_RMC功能审查矩阵.md`、`06_已知问题与改进建议.md` 与 `AGENT_CONTEXT.md`。
- **是否已提交**：未提交、未推送；RMC 未修改。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-27 03:46 | 立项 |
| 2026-08-27 | 完成部署数据审计、冻结 pilot/formal 门禁并记录用户持续授权。 |
| 2026-08-27 | 修正首次 pilot 的任务侧材料密度后，4/4 pilot clean；冻结并完成 20/20 formal。 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 读取历史 NNUBAR/material 证据 | 历史 F02 任务 | 识别历史 NNUBAR=1 g6→g1 不可用，不能作为 formal 输入。 |
| 3 | 解析部署核表 | 既有一基 MGACE 解析器 | 找到更强的 `10005` g4→g1 裂变候选；待 task-local pilot 验证。 |
| 4 | 高密度反例处置 | `pilot_aborted_high_density/` | 发现任务侧 `MAT 1 10000.0` 不符合历史裂变 harness 的 `1.0` 密度；停止后保留，不删除。 |
| 5 | pilot/formal | task-local generator/analyzer | 修正为 `MAT 1 1.0` 后 pilot 通过；依照已冻结 seeds/population 运行 20 条 formal，全部通过。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
