# f02-w6-double-nubar-kernel-consistency-fix

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-25 |
| 状态 | 已完成 |
| 任务类型 | 缺陷修复 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | W6 |
| 涉及文件 | `RMC/src/SampleColliType.cpp`；任务侧验证脚本/输入/日志；W6 知识库与物理导读 |
| 分支 / 提交 | `Neural_Network_WW_Iteration` / `4d3e1aac60f1c40062f05e5d532afb6c7eb6fb4b`；工作树已有未提交 W5/W7 修改 |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：修复 standard MGACE fixed-source neutron adjoint 在 `NNUBAR>1` 时初始化/权重核与运行时裂变前驱群抽样使用不同 nubar block 的 W6 缺陷，使裂变反应概率、群抽样和权重对应同一个物理核。

**范围**：拟修改 `RMC/src/SampleColliType.cpp` 的多群伴随裂变群抽样 locator；不改变正向输运、连续能量、HDF5/AIS、显式 delayed precursor、输入卡格式、核数据或既有 reference/benchmark。任务侧新增只读核数据 oracle 与运行日志，并同步 W6 知识库和物理导读。

**验收标准**：

1. 运行时伴随裂变前驱群抽样与 `treatAdjointMaterial()`、`GetMgNucNubar()` 使用同一个 nubar locator；`NNUBAR=1` 行为保持不变，`NNUBAR>1` 不再直接硬编码第一 block。
2. 代码构建通过；既有 `test_fixed_source_adjoint` 通过且 reference SHA256 仍为 `750be025...43faa`，不更新任何参考结果。
3. 部署 `10001.01m` 双表数据的确定性 oracle 表明生产源码选取的运行时群核逐群等于第二套 total $\nu\Sigma_f$ 核；最大逐群概率差在双精度容差内为 0。该 oracle 不是动态频数测量；修复前真实结果 `3.09731738402652e-05` 原样保留。
4. W7 修复后的 neutron-only `c5g7td` 输入重放退出 0、完成 10,000 个源历史并产生 bank 后继；无崩溃、NaN/Inf 或未解释 error。因部署核差异极小，该运行只作可达性/稳定性验证，不用低统计频数冒充分布证明。
5. `git diff --check` 通过；`changes.diff` 仅包含任务开始时已有 W5/W7 改动和本任务获批后的 W6 最小改动；核库、reference、分支与 commit 均不变。

**原始材料**：

- `logs/baseline.txt`：任务开始时 RMC 分支/SHA/工作树、编译器及可执行文件、reference、`xsdir`、`c5g7td` 和 V3 输入哈希原始输出。
- `logs/pre_fix_kernel_analysis.txt`：部署双 nubar 数据修复前只读分析的完整 stdout。
- `logs/pre_fix_kernel.csv`：7 群两套 $\nu\Sigma_f$ 核、当前精确运行时分布和差值。
- `logs/claude_physics_code_review.md`：Claude 对修复后的物理正确性、代码范围、验证强度和 F02-B 分级所做的独立只读审核原文。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：伴随裂变核应使用同一套 $\nu(g)\Sigma_f(g)$ 同时构造总产生量、选择裂变反应并抽样前驱群。当前初始化与通用 getter 在双表时选择第二套 total nubar，运行时却从第一套 prompt nubar 扣减同一个由 total 核形成的抽样阈值，最后一群吸收剩余概率且没有重要性补偿，因此实现的群分布不是任一归一化物理核。

**可证伪局部假设**：W6 由 `SampleColliMT_FixedSrc()` 内唯一的 `JXS[4]` 直接访问造成，改为既有 total locator 即可闭合 standard MGACE 伴随裂变核，而不影响正向路径。廉价反证检查是全仓搜索 `GetMgNeuLNU()`/`JXS[4]`：若发现其他 standard MGACE 伴随裂变群抽样仍读取第一 block，或该访问被正向路径共享，则单点方案作废。搜索结果未发现第二处；该代码位于 `p_bIsAdjointParticle` 分支，正向分支独立。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `RMC/src/TreatAdjointMaterial.cpp:40-46` | 初始化用 `GetMgNeuLNU()` 形成 $\nu\Sigma_f$ 并累加伴随裂变总产生量。 |
| 2 | `RMC/src/Nuclide.cpp:28-35` | `NNUBAR>1` 时 `GetMgNeuLNU()` 返回 `JXS[4]+NGRP`，即第二套 nubar；单表返回 `JXS[4]`。 |
| 3 | `RMC/src/GetMgCs.cpp:85-90` | 通用 `GetMgNucNubar()` 也经 `GetMgNeuLNU()` 读取同一套数据。 |
| 4 | `RMC/src/SampleColliType.cpp:164-179` | 伴随裂变反应阈值来自初始化 total 核，但前驱群扣减直接读取 `JXS[4]+exitGrp`；相邻 TODO 已指出 getter 替代式。 |
| 5 | `RMC/src/CalcMXSTable.cpp:61,87-93` | RMC 自身 MGACE 写出约定：单表为 total；双表 block 长度为 `2*NGRP`。 |
| 6 | `RMC/src/GetMgCs.cpp:25-35` | HDF5 通用 getter 在 total 可用时明确优先 total，只在 total 缺失时回退 prompt。 |
| 7 | `logs/pre_fix_kernel_analysis.txt` | `10001.01m`：`NNUBAR=2`，第一/第二核总量不同；当前最大群概率偏差 $3.0973\times10^{-5}$，80% 功效约需 73,289,470 个后继。 |
| 8 | W7 修复任务 | 同一 `c5g7td` 输入修复 W7 后退出 0，10,000 个源历史产生 12,487 条初始/后继状态，证明 W6 运行路径可达。 |

**影响面**：仅 standard MGACE、多群、fixed-source、伴随粒子、裂变核素且 `NNUBAR>1` 时产生数值变化；`NNUBAR=1` 的 locator 相同，既有 H/O 非裂变回归不触发裂变。正向、连续能量和 HDF5/AIS 不进入该分支。双表伴随输出发生物理修正是预期行为，但不允许借机更新任何既有 reference。

**为什么之前没做/没发现**：既有 `fixed_source_adjoint` 使用非裂变 H/O 数据；部署双表 `c5g7td` 的 prompt/total 差异很小，低统计运行难以发现。W7 修复前该 neutron-only 输入又在首历史前崩溃，阻断了动态可达性。

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A：统一为既有 total getter | 将运行时 `JXS[4]+exitGrp` 改为 `GetMgNeuLNU(nNuc)+exitGrp`，删除过时 TODO；初始化、通用 getter和群抽样统一采用 total。 | 最小一处生产代码改动；符合 standard/HDF5 现有语义。部署双表差异太小，动态频数只能记可达性，确定性正确性由核解析 oracle 证明。 | ★推荐 |
| B：新增 prompt/total 模型选项 | 新增输入卡/配置，让初始化、反应概率、权重和群抽样统一选择 prompt 或 total。 | 需定义用户物理语义，修改接口、解析、standard/HDF5 两路径并新增成套测试；远超 W6 根因修复。可另立功能任务。 | 不推荐本任务 |
| C：保留 prompt 抽样并加权补偿 | 继续从第一核提议群，按 total/prompt 核比修正后继权重，使期望对应 total。 | 增加方差、零概率支持风险和复杂权重证明；既然 total 数据可直接抽样，没有必要。 | 不采纳 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A，将 standard MGACE 伴随裂变运行时前驱群抽样统一为既有 total nubar getter。
- **决定人 / 日期**：用户，2026-08-25（“请完成修复”）。
- **理由与约束**：沿用 RMC standard/HDF5 已有的 total 优先语义，以最小改动消除初始化、反应概率、权重和群抽样之间的不一致。不改输入格式、核数据、reference/benchmark，不进入 W6 之外的 delayed/AIS/HDF5 重构，不 commit/push/切分支。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh f02-w6-double-nubar-kernel-consistency-fix W6` | 建立 `20260825_07_...` 任务和 logs，台账入口校验通过。 |
| 2 | 复核直接控制路径 | `SampleColliType.cpp`、`TreatAdjointMaterial.cpp`、`Nuclide.cpp`、`GetMgCs.cpp` | 确认 standard MGACE 伴随裂变只有运行时群抽样直接读取第一 block。 |
| 3 | 冻结修复前基线 | `logs/baseline.txt` | RMC SHA、既有 W5/W7 工作树、可执行文件、reference、核库和输入哈希已记录。 |
| 4 | 重放双表数据 oracle | `logs/pre_fix_kernel_analysis.txt` / `.csv` | 重现最大群概率偏差 `3.09731738402652e-05` 与约 7330 万后继的功效边界。 |
| 5 | 记录人工决策 | 本档第 4 节、`INDEX.md` | 用户“请完成修复”记为采纳方案 A；任务进入实施。 |
| 6 | 实施最小生产修复 | `RMC/src/SampleColliType.cpp` | 将运行时裂变前驱群 nubar locator 从 `JXS[4]` 改为 `GetMgNeuLNU(nNuc)`，删除过时 TODO。 |
| 7 | 构建与既有回归 | `/tmp/mlvr_f02_rmc_build`、`logs/ctest_fixed_source_adjoint.txt` | RMC 构建通过；定向 CTest 1/1 通过。 |
| 8 | 运行修复后 oracle | `verify_kernel_consistency.py`、`logs/post_fix_kernel_*` | 双表逐群核/概率最大差均为 0；单表 locator 保持不变。 |
| 9 | 重放真实双表分支 | `cases/neutron_only_c5g7td/` | seed 1、10,000 历史退出 0，产生 2,487 条 bank 后继，无 error/NaN/Inf/信号。 |
| 10 | 同步并归档 | 知识库、物理导读、`changes.diff` | W6 标记已修复；F02-B 从 E 保守调整为 C — Verify；快照与完整性证据已保存。 |
| 11 | Claude 独立审核 | `logs/claude_physics_code_review.md` | 未发现阻止 W6 标记已修复的问题；认可 F02-B 为 C — Verify，并重申 oracle/动态重放的证据边界。 |

**代码改动**：见 [changes.diff](changes.diff)，摘要：
- `RMC/src/SampleColliType.cpp:171-172` —— 运行时伴随裂变前驱群抽样改用既有 total nubar getter，使反应概率、群抽样和权重对应同一 total 核。
- 快照同时包含任务开始前已有且必须保留的 W5 `GetExitState.cpp`/`SampleColliType.cpp` 与 W7 `InitiateAll.cpp` 未提交修改。

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
| 人工门禁 | 任务/INDEX 断言 | `w6 human decision gate: PASS`。 |
| 构建 | `cmake --build /tmp/mlvr_f02_rmc_build --target RMC -j2` | `[100%] Built target RMC`。 |
| 定向回归 | `ctest --test-dir /tmp/mlvr_f02_rmc_build -R '^test_fixed_source_adjoint$' -V` | `1/1` 通过，0 失败，0.73 s。 |
| 双表核 oracle | `python3 verify_kernel_consistency.py ... --zaid 10001.01m` | `NNUBAR=2`，first/getter locator=`29/36`；total 核和归一化概率最大差均为 `0`。 |
| 单表兼容 | 同一 oracle 的显式 `NNUBAR=1` locator 检查 | locator=`29`，`unchanged=True`。 |
| 动态可达性/稳定性 | 在 `cases/neutron_only_c5g7td/` 运行修复后 `RMC inp` | exit 0；10,000 源历史；12,487 条总粒子记录、2,487 条 bank 后继；0 条 error/NaN/Inf/信号。 |
| 完整性 | `git -C RMC diff --check`、哈希和文件集合检查 | 通过；仅 3 个预期共享文件；分支/SHA、reference、核表不变。 |
| Claude 独立审核 | 只读复核物理推导、生产调用链、oracle、动态证据与评级 | “未发现阻止 W6 标记为已修复的问题”；认可 C — Verify，不认可将低统计重放表述为动态分布证明。 |

```
zaid=10001.01M NGRP=7 NNUBAR=2 first_nubar=29 getter_nubar=36
single_table_locator=29 unchanged=True
expected_total_kernel_sum=0.71977667464764
runtime_kernel_sum=0.71977667464764
max_kernel_difference=0
max_probability_difference=0
criterion=runtime kernel equals initialized total kernel group-by-group; pass=True

exit_code=0
source_number=10000
particle_records=12487
bank_successor_records=2487
warning_lines=1
error_nan_inf_signal_lines=0

reference_result sha256=750be0255b972f0d4aa25dbd2a0c864e17b5b04058be4749109cb10290443faa
c5g7td sha256=cc6951edc9cd2fc8045d6b6ab163fea2394d995749ec85da7ae40ed40540ed4c
```

**实验设置（算法实验必填）**：
- 随机种子：动态重放 `RNG TYPE=2 SEED=1 STRIDE=1000000`；10,000 source histories。
- 配置快照：任务输入卡 `cases/neutron_only_c5g7td/inp`，SHA256 `e08475fd...131cd9`；非 ML 训练任务，无 `src/config.py`。
- 依赖版本：G++ 13.3.0；CMake 3.28.3；RMC 3.5.0，commit `4d3e1aac...`。
- 基准对比：修复前最大群概率偏差 `3.09731738402652e-05`；修复后确定性差为 0。未运行 ML/WW 的 RE、FOM 对比。

**已解释告警**：动态卡片沿用 W7 可达性输入，将 `MAXADJOINTENERGY` 设为 16，高于 `c5g7td` 群上边界，产生 1 条已知上限 warning；群定位后计算正常完成。该告警与 W6 locator 无关。

**未覆盖到的验证**：未执行约 7330 万已观测后继的动态群频数检验，因为部署 prompt/total 差异太小且源码 locator/核解析 oracle 已直接验证修复；该 oracle 重新计算源码应选 kernel，不是执行轨迹频数测量。未测量可裂变最终响应或响应级互易性；未覆盖异常核数据中的零/负 $\chi$、$\nu\Sigma_f$ 与累计残差防护、delayed precursor、AIS/HDF5、continuous-energy、MPI/OpenMP、Windows、大规模生产算例，也未更新任何 reference/benchmark。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：W6 根因已修复。standard MGACE 双 nubar 伴随裂变初始化、通用 getter 与运行时前驱群抽样现在统一使用 total nubar 核；确定性逐群核/概率差为 0，真实动态 bank 路径稳定可达。W5/W6/W7 三项已知缺陷均已闭合，F02-B 从 E 调整为 **C — Verify**，不宣称 A — Ready。
- **遗留问题 / 后续待办**：为可裂变最终响应、混合材料、一般密度场、强各向异性和更多几何/群对补充代表性验证；异常 MGACE 数据中的零/负 $\chi$、$\nu\Sigma_f$ 及累计残差健壮性另行审查；delayed/AIS/HDF5 等另立任务审查。
- **知识库同步**：更新 `AGENT_CONTEXT.md`、`02_RMC功能审查矩阵.md`、`06_已知问题与改进建议.md`、知识库 README，以及物理导读总览和多群伴随输运专题 01-04。
- **是否已提交**：已由 GitHub Copilot 提交到 RMC `Neural_Network_WW_Iteration`，commit `6d2087518e0d9f23574d629f5fde361c79f519e4`；未 push、未切分支。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-25 18:06 | 立项 |
| 2026-08-25 18:07 | 完成代码定位、修复前核 oracle 与三方案设计，状态转为待决策 |
| 2026-08-25 | 用户拍板方案 A，进入实施 |
| 2026-08-25 18:18 | 完成最小修复、构建、回归、确定性 oracle、动态重放、文档同步和快照归档 |
| 2026-08-25 | Claude 独立审核确认无 W6 阻断问题并认可 C — Verify；审核原文归档 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 校验建档 | README、logs、INDEX | 初次因终端已在 `MLVR_develop/` 而重复路径失败；修正相对路径后通过，档案内容无异常。 |
| 3 | 追踪 nubar 数据流 | 生产代码与 F02 旧档案 | 确认初始化/通用 getter/运行时群抽样的 locator 差异及分支边界。 |
| 4 | 检查测试能力 | `RMC/tests/`、V3/W7 档案 | 现有 CTest 不覆盖裂变；部署核动态频数低功效，需确定性 oracle + 可达性分层验证。 |
| 5 | 保存基线与修复前结果 | `logs/` | 哈希、工具链、双表核和功效结果已原样归档。 |
| 6 | 记录用户决策并实施 | 任务第 4 节、`SampleColliType.cpp` | 采纳方案 A；只替换 W6 locator，保留共享文件内 W5 修改。 |
| 7 | 首轮验证 | RMC build、CTest | 编译成功，定向回归 1/1 通过。 |
| 8 | 新增确定性 oracle | `verify_kernel_consistency.py` | 读取生产源码和部署数据，验证双表 total 核逐群一致及单表 locator 不变。 |
| 9 | 动态重放与证据汇总 | `cases/neutron_only_c5g7td/` | RMC 正常完成；首次摘要命令因 `grep` 零匹配返回 1 而中止，改用零匹配安全的 `awk` 后得到 0 异常与完整哈希。RMC 运行本身未失败。 |
| 10 | 文档一致性检查 | 知识库、物理导读 | 首轮断言发现两处导读仍把 W6 写成当前限制；修正后 7 个关键文档状态检查通过，历史时间线保留修复前 E 结论。 |
| 11 | 最终完整性与归档 | `changes.diff`、`logs/final_integrity_check.txt` | `diff --check` 通过；3 个预期 RMC 文件，分支/SHA/reference/核表均未漂移。 |
| 12 | 归档 Claude 独立审核 | `logs/claude_physics_code_review.md` | 审核支持 W6 已修复与 F02-B C — Verify；明确 oracle 非动态频数测量，并提出异常核数据健壮性后续项。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
