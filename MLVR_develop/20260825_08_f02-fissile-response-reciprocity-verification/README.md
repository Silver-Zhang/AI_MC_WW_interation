# f02-fissile-response-reciprocity-verification

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-25 |
| 状态 | 已完成 |
| 任务类型 | 数值验证 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F02 |
| 涉及文件 | 任务侧输入生成、运行与响应分析脚本、原始日志和结果；不修改 RMC 生产代码 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `6d2087518e0d9f23574d629f5fde361c79f519e4` |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：在已提交 W5/W6/W7 修复的 RMC 上，建立至少一个明确由裂变耦合驱动的前向—伴随响应对，比较交换源群/响应群后的最终 track-length 响应，补足 F02-B 从确定性核一致性与 bank 可达性到响应级物理证据的缺口。

**范围**：仅在本任务目录新增可复现输入生成、批量运行和统计分析材料，并同步 F02 知识库/物理导读结论。不修改 RMC、核数据、reference/benchmark；只覆盖 standard MGACE、fixed-source、neutron、`ais=OFF`、单一均匀球、P0 标量 cell track-length 响应。

**验收标准**：

1. 使用部署 `10001.01m`（7 群、`NNUBAR=2`）和已提交 RMC `6d208751...`；核表与可执行文件哈希冻结，过程中不更新 reference/benchmark。
2. 主群对选择 ACE `g6→g1`：前向源为 `g6`、响应为 `g1`；伴随源/响应交换。只读核解析须证明 $\nu\Sigma_f(6)\chi(1)>0$ 且 P0 散射 `6→1`、`1→6` 均为 0，使跨群响应确实覆盖裂变耦合而非直接散射。设计期首选 `g7→g1`，但 pilot 发现 RMC 会对最低群源逐历史输出下界告警，故在正式批次冻结前改用次强 `g6→g1`。
3. pilot 只验证输入、tally 群映射、有限正响应与无异常，不进入正式判据。正式批次冻结后不按结果挑 seed 或局部追加：5 个前向 seed `1,3,5,7,9` 与 5 个伴随 seed `11,13,15,17,19`，每运行 1,000,000 histories。
4. 正式 10/10 运行退出 0、完成规定 histories、无未解释 warning/error/NaN/Inf；所有响应有限且正。主判据为五组独立流逐组及逆方差合并均满足 $|z|\le3$；报告响应、标准差、RE、$z$ 和哈希。
5. 若预冻结正式批次失败，原样保留并将 F02-B 维持 C 或降级，不通过挑 seed、只追加失败侧、更新 reference 或事后改变主判据掩盖结果。
6. 归档真实输出、复现命令、输入 manifest、随机种子、工具链和未覆盖边界；根据结果同步 F02-B 与物理导读，但单个代表案例不得直接把 F02 提升为 A — Ready。

**原始材料**：

- `logs/baseline.txt`：RMC 分支/提交、工具链、可执行文件、`xsdir` 和 `c5g7td` 哈希。
- `logs/fissile_pair_screen.txt`：7 群 total $\nu\Sigma_f$、$\chi$、P0 散射背景和裂变算子候选强度的只读解析输出。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：W5/W6/W7 已在 RMC commit `6d208751...` 中提交。W6 的生产 locator 与部署核数据 oracle 已证明初始化和运行时采用同一 total nubar 核，10,000-history 动态重放也覆盖了 2,487 条 bank 后继，但尚未比较可裂变问题的最终响应。既有 V4/W5 响应级测试使用 `NNUBAR=0` 的 H/O 数据，不能填补该缺口。

**可证伪局部假设**：若正向 `g6` 源到 `g1` 响应与伴随 `g1` 源到 `g6` 响应实现的是同一转置输运算子，则在相同均匀球、相同源/响应空间归一化和独立统计流下，两者应在联合不确定度内一致。廉价反证检查是部署核表的直接群耦合：若 `g6→g1` 可由 P0 散射直接产生，或裂变项为零，则该群对不能隔离裂变证据。解析结果为裂变项 `0.100120227799`，双向直接 P0 散射均为 0，支持该设计。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | W6 修复任务 | `GetMgNeuLNU()` locator 修复、逐群核差为 0、真实 bank 路径可达；但未覆盖最终响应。 |
| 2 | V4/W5 响应级任务 | 已有输入生成、tally 群映射和前向—伴随 $z$ 分析框架可复用；旧案例均为非裂变 H/O。 |
| 3 | `logs/fissile_pair_screen.txt` | `g6` 的 total $\nu\Sigma_f=0.170298562364$，`g1` 的 $\chi=0.58791$，乘积为 `0.100120227799`。 |
| 4 | 同上 | P0 `g6→g1=0` 且 `g1→g6=0`，直接群间信号由裂变项主导。 |
| 5 | `RMC/src/TreatAdjointMaterial.cpp` / `SampleColliType.cpp` | 初始化构造 $\chi(h)\sum_g\nu\Sigma_f(g)$，运行时按 total $\nu\Sigma_f(g)$ 抽样前驱群，正是本响应对覆盖的路径。 |

**统计与归一化设计**：使用与 V4 相同的单区域均匀体源和同区域积分 cell track-length tally，空间源/响应区域相同，因此只交换能群且体积归一化不变。RMC tally 输出群号按 `NGRP-ACE_group+1` 映射：前向读取 tally group 7（ACE g1），伴随读取 tally group 2（ACE g6）。前向与伴随使用不重叠 seed，避免沿用相同 RNG stream 后把未知协方差当独立误差。

**影响面**：这是任务侧数值实验，不改生产代码和接口。通过只能增强当前 representative standard MGACE 可裂变子域的正证据；不能外推到混合材料、非均匀密度、强各向异性、delayed、AIS/HDF5、continuous-energy 或完整 MLVR 工作流。

**为什么之前没做/没发现**：W7 修复前纯中子双表算例在输运前崩溃；W6 修复前群抽样核又确定性错误。两项闭合并提交后，响应级验证才具有解释价值。

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A：单一纯裂变主群对，pilot + 冻结正式批次 | 2 cm 均匀 `10001.01m` 球；正式采用 `g6↔g1`；pilot 不入判据，正式 5 组独立 RNG 流、每运行 1M histories；复用并收紧 V4 分析。 | 10 个正式运行，成本低；覆盖强 fission entry 且避开最低群源逐历史告警。仅一个群对/几何，仍不足以评 A。 | ★推荐 |
| B：两个裂变群对扩大覆盖 | 在 A 基础上增加 `g6↔g2`（裂变项 `0.070122136039`，双向直接散射也为 0），同样 5 组独立流。 | 正式运行翻倍；覆盖更广，但第二对信号较弱，可能需更高 histories。 | 可后续追加，但不得在看到 A 结果后冒充同一事前主检验 |
| C：只做 bank 群频数或不新增响应测试 | 延续 W6 的核 oracle/10k 可达性，不比较最终 tally。 | 成本最低，但不能填补 F02 当前最大证据缺口，也无法支持进入 F03 前的阶段复核。 | 不推荐 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A，单一 `g6↔g1` 裂变主导响应对，pilot + 预冻结 1M 正式批次。原设计的 `g7↔g1` 在 pilot 暴露最低群源逐历史告警，正式批次生成前按同一方案原则调整为 `g6↔g1`。
- **决定人 / 日期**：用户授权 GitHub Copilot 自主选择，2026-08-25。用户原请求要求完成该验证直至进入 F03；决策问询返回“Work autonomously and make good decisions”，据此采纳已在第 3 节推荐的 A。
- **理由与约束**：`g6→g1` 是避开最低群源告警后的次强裂变项，双向直接 P0 散射均为 0，以较低成本直接补 F02 最大证据缺口。只新增任务侧实验材料，不修改 RMC/核数据/输入接口，不更新 reference/benchmark；正式 seeds、1M histories 和判据在运行前冻结，不按结果挑 seed 或单侧追加；未覆盖范围不外推为 A — Ready。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 实现输入生成器 | `generate_cases.py` | 固定几何、材料、群对、独立 seed、population、tally 群映射和 manifest/input 哈希。 |
| 2 | 实现批量运行器 | `run_cases.py` | 每批先核对可执行文件 SHA256；逐运行保存 stdout/stderr、退出码与摘要。 |
| 3 | 实现响应分析器 | `analyze_reciprocity.py` | 解析 source count/tally/RE，检查异常并计算逐对及逆方差合并 $z$；修正首个 tally 群行可含 cell ID 的解析。 |
| 4 | 运行首轮 g7 pilot | `cases/pilot` | 响应有限且相容，但最低 ACE 群源逐历史输出下界 warning；未进入正式判据。 |
| 5 | 源码定位并调整主群对 | `RMC/src/GetMgCs.cpp`、`logs/fissile_pair_screen.txt` | `LocateMgErgGrp()` 对插值位置 0 无条件告警，无法用合法 g7 群内能量规避；正式冻结前改为 `g6↔g1`。 |
| 6 | 重跑 g6 pilot | `logs/pilot_*.log` | 2/2 退出 0、0 异常；$R_F=0.25084$、$R_A=0.24456$、$z=0.4773$。 |
| 7 | 冻结并运行正式批次 | `cases/formal/manifest.json`、`logs/formal_*.log` | manifest SHA256 `b7f1fa9a...7e732`；10/10 个 1M-history 运行退出 0。 |
| 8 | 分析正式响应 | `results/formal/` | 五组逐对与合并结果全部满足 $|z|\le3$，0 异常，正式判据通过。 |

**代码改动**：见 [changes.diff](changes.diff)。RMC 工作树在实验前后均为 clean，快照为空；本任务只新增任务侧生成、运行、分析与证据文件。

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
| Python 语法检查 | `python3 -m py_compile generate_cases.py run_cases.py analyze_reciprocity.py` | 退出 0。 |
| g6 pilot | `generate_cases.py --stage pilot` → `run_cases.py` → `analyze_reciprocity.py` | 2/2 运行退出 0；每个 20,000 histories；0 异常；$z=0.477347$；pilot 门槛通过。 |
| 正式 manifest 冻结 | `generate_cases.py --stage formal && sha256sum cases/formal/manifest.json` | 10 个运行，每个 1,000,000 histories；SHA256 `b7f1fa9a1ce2e7afe6bba61f323881d0c45f9a7f6f7e1c6e1bba3a1b8377e732`。 |
| 正式运行 | `run_cases.py --root cases/formal --executable /tmp/mlvr_f02_rmc_build/bin/RMC --expected-executable-sha256 f3870...1ba16` | 10/10 退出 0，stderr 均为空；run summary SHA256 `0d8d3f57...9e053`。 |
| 正式互易性分析 | `analyze_reciprocity.py --root cases/formal --results results/formal` | 10 个 source count 均为 1M，0 异常；5/5 逐对及合并 $|z|\le3$；正式判据通过。 |
| RMC 洁净性 | `git -C RMC status --short && git -C RMC rev-parse HEAD` | 无状态输出；HEAD `6d2087518e0d9f23574d629f5fde361c79f519e4`。 |

```text
run_count=10 paired_stream_count=5 anomaly_lines=0
pair z: -0.554265, 0.619398, -2.033117, 0.594154, -0.186475
combined R_F=0.24199811808304358 sigma_F=0.00036637027404590856
combined R_A=0.24255941171604797 sigma_A=0.0007098732314158964
combined z=-0.7026348520546188
criterion_pass=True
```

**实验设置（算法实验必填）**：
- 随机种子：pilot forward/adjoint `101/103`；formal forward `1,3,5,7,9`，adjoint `11,13,15,17,19`；`RNG TYPE=2 STRIDE=1000000`。
- 配置快照：`cases/{pilot,formal}/manifest.json`；均匀 2 cm 球、`10001.01m`、ACE `g6↔g1`、P0 cell track-length response；pilot 20k、formal 1M histories/运行。
- 依赖版本：RMC 3.5.0 源码 commit `6d208751...`；可执行 SHA256 `f3870...1ba16`；g++ 13.3.0；CMake 3.28.3；分析仅使用 Python 标准库。
- 核数据：`xsdir` SHA256 `970e85ad...f62b`；`c5g7td` SHA256 `cc6951ed...ed4c`。
- 基准对比：本任务不比较 ML/WW/FOM；比较同一线性响应的前向与伴随独立统计估计。

**未覆盖到的验证**：只覆盖单一 `10001.01m` 材料、`g6↔g1` 群对、均匀球、P0 标量 cell track-length 响应和串行本地运行；未覆盖其他裂变群对、混合材料、非均匀密度、强各向异性、delayed、AIS/HDF5、continuous-energy、MPI/OpenMP、Windows 或完整 MLVR 工作流。当前可执行文件由新 commit 前已配置的构建目录增量编译，运行 banner 内嵌 Git 标识仍为 `4d3e1aac...`；本任务以源码 HEAD、干净工作树和可执行 SHA256 三者冻结追溯，但后续新阶段宜重新 CMake configure/build 刷新 banner。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：预冻结的可裂变响应级互易性正式批次通过。该代表案例把 F02 的裂变证据从“total nubar 确定性核一致 + bank 路径可达”推进到最终响应统计相容；但单材料/单群对/单几何不足以评 A，F02 阶段复核结论保持 **C — Verify**。
- **遗留问题 / 后续待办**：其他裂变群对、混合材料、一般密度场、强各向异性与并行平台仍待扩展验证；最低 ACE 群源无条件 warning 仅作为输入/健壮性现象记录，不在本数值任务修改 RMC。按既定顺序进入 F03 Adjoint source 只读审查。
- **知识库同步**：更新 `AGENT_CONTEXT.md`、F02 审查矩阵、W6 台账；更新多群伴随输运专题及根物理导读，写明可裂变响应正证据和剩余边界。
- **是否已提交**：本任务未修改 RMC。实验基线为 RMC `Neural_Network_WW_Iteration` / `6d208751...`，未 push；根工作区文档待用户后续统一提交。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-25 18:50 | 立项 |
| 2026-08-25 18:51 | 冻结已提交 RMC 与核数据基线；完成 7 群裂变群对筛选，状态转为待决策 |
| 2026-08-25 | 用户授权自主决策，采纳方案 A，进入实施 |
| 2026-08-25 | g7 pilot 暴露最低群源逐历史告警；源码定位后在正式批次前调整为 g6↔g1 |
| 2026-08-25 | g6 pilot 无异常通过；冻结并完成 10 个 1M-history 正式运行，全部响应互易性判据通过 |
| 2026-08-25 | 完成 F02 阶段复核与知识库/物理导读同步，评级保持 C — Verify，任务归档 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 冻结实验基线 | `logs/baseline.txt` | RMC 为干净的 `6d208751...`；工具链、可执行文件和核数据哈希已记录。 |
| 3 | 复核既有响应框架 | V4/W5 生成与分析脚本 | 可复用 cell tally、ACE/tally 群映射和 $z$ 分析；需改为独立前向/伴随 RNG 流。 |
| 4 | 首次群对筛选 | 临时 Python 只读分析 | 因终端当前目录已在 `MLVR_develop/`，相对导入路径多一层而失败；未读写核数据。 |
| 5 | 重跑群对筛选并保存 | `logs/fissile_pair_screen.txt` | 改用绝对路径后通过；选出 strongest `g7→g1` 裂变项，双向直接 P0 散射均为 0。 |
| 6 | 人工门禁 | 用户请求与决策问询 | 用户授权自主选择；采纳推荐方案 A 并冻结统计与改动约束。 |
| 7 | 首轮 pilot 与输入修正 | `cases/pilot`、`GetMgCs.cpp:263-280` | RMC 运行和响应正常，但 g7 最低群源触发逐历史下界告警；源码确认插值位置 0 无条件告警。正式批次前改用次强且同样无直接散射的 `g6→g1`。 |
| 8 | g6 pilot 验证 | `logs/pilot_generate.log`、`pilot_run.log`、`pilot_analysis.log` | 2/2 退出 0，0 异常，响应有限正，$z=0.477347$。 |
| 9 | 冻结正式批次 | `cases/formal/manifest.json` | seeds、1M population、群对和判据按方案冻结；manifest SHA256 `b7f1fa9a...7e732`。 |
| 10 | 正式运行与分析 | `logs/formal_run.log`、`formal_analysis.log`、`results/formal/` | 10/10 退出 0；五组及合并均满足 $|z|\le3$，最大单组 $|z|=2.033117$、合并 $z=-0.702635$、0 异常。 |
| 11 | F02 阶段复核 | 本 README、知识库与物理导读 | 可裂变最终响应缺口已获得单代表案例正证据；一般适用域仍未充分验证，F02 保持 C — Verify 并进入 F03。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
