# f02-adjoint-photon-negative-angular-audit

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-26 |
| 状态 | 已完成 |
| 任务类型 | 缺陷审查 / 数值验证（确认后候选修复） |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F02 |
| 涉及文件 | `RMC/src/GetMgExitErgMu.cpp`、`RMC/src/ProcessMgPhotonCollision.cpp`、任务侧私有 MGACE 资产与验收器 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `6d2087518e0d9f23574d629f5fde361c79f519e4`；工作树含任务 12 的 neutron W9 一行与本任务两行，均未提交 |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：审查并动态确认 `GetMgAdjPhoExitErgMu()`（伴随 photon 散射）与 `GetMgAdjPhoNeuExitErgMu()`（伴随 photon→neutron 次级）在 `ISANG=0,NLEG=1,x<0` 时是否复现 W9 的错误区间宽度；若人工授权且动态确认缺陷，则做最小根因修复并完成支持域、理论矩、前/伴随一致性与既有回归验证。

**范围**：只涉及 standard ASCII multigroup ACE、fixed-source adjoint 的 photon 散射和 photon→neutron 次级条件角核，以及任务侧最小私有核数据/输入/分析器。默认不改输入格式、核数据库、reference/benchmark，不扩展到 CE、AIS、电子、其他角表示或无关代码。任务 12 的 neutron-adjoint W9 一行未提交改动保持原样且单独归属。

**验收标准**：两条候选路径分别具备独立数据 readback、生产调用可达证据和修复前/后动态对照。对 `x=-0.5`，修复后样本须全部位于 `[-1,0]`，均值与 `-0.5` 在预设统计阈值内，且同 RNG 前向/伴随样本一致；至少三 seed。最终整程主证据须逐运行同时满足退出码 0、0 Warning、0 Error 和恰好一个 `RMC Calculation Finish.`；现有 fixed-source adjoint CTest 通过，reference 哈希不变，RMC diff 能区分既有 W9 与本任务改动，未覆盖范围如实记录。

**原始材料**：`logs/request/user_request.txt` 原样保存用户启动请求，并注明其直接触发上下文。日志分类见 `logs/README.md`。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：任务 11/12 已确认并修复 standard neutron-adjoint 的同形 W9，但明确排除 photon/secondary。当前两个候选负分支仍使用 `-1+2*Rand()*(1-x)`。若表值 `x` 与同结构前向分支一样表示单变量近似的目标均值，则该式产生支持域 `[-1,1-2x]`、均值 `-x`；对 `x=-0.5` 为 `[-1,2]`、均值 `+0.5`，同时违反余弦范围与目标均值。正确均匀逆变换为 `-1+2*Rand()*(1+x)`，支持域 `[-1,1+2x]`、均值 `x`。

**可证伪局部假设**：两条候选生产路径均可由带 `x=-0.5` 私有表到达；未修复实现会产生 `mu>0`、甚至 `mu>1`，而对应前向条件角核只产生 `[-1,0]`。若任一路径的数据 locator 语义不同、不可由合法 MGACE 表表达，或运行未进入目标分支，则该路径的“W9 同类缺陷”假设被否定并停止修复。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `RMC/src/GetMgExitErgMu.cpp:246-264` | 前向 photon 从 `PNXS(3/9)` 与 `PXSS` 读取 `NLEG/ISANG`；负单变量使用 `(1+x)`。 |
| 2 | `RMC/src/GetMgExitErgMu.cpp:379-432` | photon→neutron 次级从 `JXS(14/15)` 指向的 secondary `ISANG/NLEG` 与 `XSS` 取值；负单变量使用 `(1-x)`。 |
| 3 | `RMC/src/GetMgExitErgMu.cpp:518-560` | 伴随 photon 从与前向相同的 `PNXS(3/9)` 与 `PXSS` 取值；负单变量使用 `(1-x)`。 |
| 4 | `RMC/src/ProcessMgPhotonCollision.cpp:16-52` | 伴随 photon 碰撞直接调用 `GetMgAdjPhoExitErgMu()`，是生产路径而非孤立 helper。 |
| 5 | `RMC/src/GetMgExitErgMu.cpp:570-596` | photon 散射能群搜索耗尽后进入 photon→neutron 次级 helper，并将 photon kill。 |
| 6 | `RMC/src/ReadAceData.cpp:617-676` | photon multigroup 数据由 xsdir gamma entry 独立读入 `PNXS/PJXS/PXSS`，需单独构造私有 gamma MGACE。 |
| 7 | `RMC/src/TreatAdjointMaterial.cpp:60-113` | 初始化伴随 photon 散射与 photon→neutron 产生截面，提供两条抽样路径的上游权重。 |
| 8 | 任务 11/12 | 已有 neutron 私有表、独立 readback、低光学厚度重建和三 seed 验收框架可复用，但不能替代本任务两条路径的动态证据。 |

**规范证据边界**：仓库注释二级引用 “MCNP manual vol. III, Table F.52”，工作区未保存手册原文，当前环境也未提供通用网页搜索。因此目前不能把代码一致性或自写 oracle 单独称为格式规范证明；实施时应补入可核验的官方原文/页码，若无法取得则在结论中保留该证据缺口。

**影响面**：候选影响 standard MGACE photon-adjoint 散射方向，以及 mixed neutron-photon adjoint 中 photon→neutron 次级方向，进而可能改变重要性场、响应与互易性。最小公式修复不改变输入或数据格式；不应更新 reference/benchmark。现有仓库测试仅看到 neutron fixed-source adjoint 输入，未发现针对这两条负单变量路径的专门回归。

**为什么之前没做/没发现**：任务 12 的授权和资产仅覆盖 neutron-adjoint；部署 MGACE 角数据主要为 `NLEG=0`，普通回归不会进入负单变量分支；方向旋转/归一化还可能掩盖原始 `mu>1`。此外 photon 与 secondary 使用两套 locator/数组，不能由 neutron 资产自动覆盖。

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A：双路径动态确认后最小修复 | 分别生成并独立读回一群 gamma 负单变量表、mixed neutron/gamma secondary 表；先保留旧式取得动态反例，再将两处 `(1-x)` 改为 `(1+x)`，做三 seed 前/伴随对照、理论矩、CTest、reference/hash 验收。若某路径不可达则不改该路径。 | 证据最完整；需开发两类私有表和观测器，成本高于 W9。 | ★推荐 |
| B：静态同形修复 | 依据前向同源数据和数学反证直接改两行，只做编译、单 seed smoke 与既有回归。 | 快，但不能证明合法数据可达、secondary locator 正确或生产影响，不满足“完全验证”。 | |
| C：仅登记风险 | 不修改 RMC，只把两个分支登记为候选缺陷并等待正式核数据/手册。 | 零代码风险，但确定性越界风险继续存在，F02 边界不闭合。 | |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A — 双路径动态确认后最小修复。
- **决定人 / 日期**：用户 / 2026-08-26。
- **理由与约束**：用户明确回复“我同意方案A，开始完成”。不更新 reference/benchmark，不 commit/push/切分支。动态确认是每个分支获准修改的前置条件；若无法取得官方 Table F.52 原文，必须明确保留格式规范证据缺口。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 资格化普通 photon 资产 | `generate_photon_mgace.py`、`verify_photon_mgace.py` | `10000.91g` 的 `ISANG=0,NLEG=1,x=-0.5` 独立回读通过；manifest SHA256 `2522d98c...7e84`。 |
| 2 | 确认普通伴随 photon 缺陷 | `sample_mulab_gdb.py` / `GetMgAdjPhoExitErgMu()` | 修复前 200 样本中 130 个超出 `[-1,0]`，范围 `[-0.974133,1.969432]`，均值 `0.432234`。 |
| 3 | 修复普通伴随 photon | `RMC/src/GetMgExitErgMu.cpp` | 仅把负分支 `(1-x)` 改为 `(1+x)`；同路径 200 样本变为 0 越界。 |
| 4 | 构造 mixed secondary 资产 | `generate_secondary_photon_mgace.py`、`verify_secondary_photon_mgace.py` | 独立确认 `NSEC=1`、secondary photon、`JXS(11-17)` locator、P0、`ISANG=0,NLEG=1,x=-0.5`；报告 SHA256 `d85f6a2c...0d5c`。 |
| 5 | 确认 photon→neutron 缺陷 | `GetMgAdjPhoNeuExitErgMu()` ABI 探针 | 修复前 200 样本中 144 个超出 `[-1,0]`，范围 `[-0.998296,1.996736]`。 |
| 6 | 修复 photon→neutron 次级 | `RMC/src/GetMgExitErgMu.cpp` | 仅把负分支 `(1-x)` 改为 `(1+x)`；同路径 200 样本变为 0 越界。 |
| 7 | 三种子动态验收 | seeds 17/23/41，各路径各 300 样本 | 两路径共 1800 样本零越界；每 seed 与合并均满足预设 `abs(z)<=3`。 |
| 8 | 正向/伴随逐样本对照 | 普通 photon 三 seed，各 300 对 | 每个 seed 的 packed-double 样本 SHA256 前/伴随完全相同。 |
| 9 | 工程回归 | 增量构建、CTest、reference/hash、`git diff --check` | 构建成功；CTest 1/1 passed；reference SHA256 不变；diff 与编辑器诊断无错误。 |
| 10 | 复核一群整程 warning | 旧两路径 × seeds 17/23/41 日志、`LocateMgErgGrp()` / `GetIntpltPos()` | 旧运行虽退出 0 并打印 Finish，但每个 400-history 输入有 401/402 条能群下界 warning；单群插值位置恒为 0，故旧日志不得称为无警告成功。 |
| 11 | 构造两群无警告资格资产 | `generate_two_group_photon_mgace.py`、`verify_two_group_photon_mgace.py` | ordinary/secondary 两套中心 `[3,1]` MeV、宽度 `[2,2]` MeV 的资产独立回读通过；3 MeV 源位于上群 `[2,4]`。 |
| 12 | 两群整程和生产采样复验 | `analyze_two_group_clean_validation.py` | 6/6 整程均 0 Warning、0 Error、一个 Finish；9/9 GDB 生产采样日志 0 Warning/0 Error；原三种子矩与配对结论复现。 |

**代码改动**：见 [changes.diff](changes.diff)，摘要：
- `RMC/src/GetMgExitErgMu.cpp:GetMgAdjPhoNeuExitErgMu()` —— photon→neutron 次级负单变量宽度由 `1-x` 改为 `1+x`。
- `RMC/src/GetMgExitErgMu.cpp:GetMgAdjPhoExitErgMu()` —— 普通伴随 photon 负单变量宽度由 `1-x` 改为 `1+x`。
- 快照中 `GetMgAdjNeuExitErgMu()` 的同形一行归属任务 12，不是本任务新增修改。`changes.diff` SHA256 为 `5eec92f9...c756`，共 3 个 hunk。

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
| 普通 photon 独立 readback | `verify_photon_mgace.py ...` | qualified；`x=-0.5`，理论支持域 `[-1,0]`；报告 SHA256 `31773942...1acb45`。 |
| secondary 独立 readback | `verify_secondary_photon_mgace.py ...` | qualified；secondary=photon，`ISANG=0,NLEG=1,x=-0.5`；报告 SHA256 `d85f6a2c...0d5c`。 |
| 修复前动态反例 | 两个生产函数各 200 样本 | 普通 photon `130/200` 越界；secondary `144/200` 越界；调用栈均闭合到 `TrackGmaHistory()`。 |
| 修复后三种子矩阵 | `analyze_mulab_matrix.py ...` | passed；普通 photon 合并 `n=900, mean=-0.500278, z=-0.288647`；secondary 合并 `n=900, mean=-0.482753, z=1.792340`；均 0 越界。 |
| 正向/伴随配对 | `analyze_photon_pairs.py ...` | seeds 17/23/41 各 300 对 packed-double SHA256 相同；报告 SHA256 `f1864e86...111c0`。 |
| 旧一群私有输入整程运行 | 两路径 × seeds 17/23/41 | 6/6 退出 0、0 Error 并打印 Finish，但每个 400-history 输入有 401/402 条能群下界 warning；仅保留为辅助证据，不计作干净整程成功。 |
| 两群资产独立 readback | ordinary / secondary | 两套资产均 qualified；下界 `[0,2]` MeV，3 MeV 源落在上群；报告 SHA256 分别为 `c5cf1363...e04e`、`b02f1538...60cc`。 |
| 两群私有输入整程运行 | 两路径 × seeds 17/23/41 | `6/6` clean：每个运行均 0 Warning、0 Error、恰好一个 `RMC Calculation Finish.`；整理后主报告 SHA256 `0ddc8f8a...43b7`。 |
| 两群生产函数复验 | 三函数 × seeds 17/23/41 | 9/9 GDB 日志 0 Warning/0 Error；两条伴随路径合计 1800 样本零越界；普通 photon 900 对前/伴随 SHA256 相同。 |
| 既有伴随回归 | `ctest --test-dir /tmp/mlvr_f02_rmc_build -R '^test_fixed_source_adjoint$' -V` | 1/1 passed，0 failed，0.73 s。 |
| reference 完整性 | `sha256sum RMC/tests/fixed_source_adjoint/reference_result` | `750be0255b972f0d4aa25dbd2a0c864e17b5b04058be4749109cb10290443faa`，未更新。 |
| 修复后二进制 | `sha256sum /tmp/mlvr_f02_rmc_build/bin/RMC` | `8fff3f0f534d2a2a116e033a26cf4bb62005c5b6d62b29925423b97bb74f13c2`。 |
| 源码完整性 | `git diff --check`、VS Code diagnostics | 均通过；RMC 仅 `src/GetMgExitErgMu.cpp` 修改。 |

```
status=passed
full_runs=6 clean=6
branch=ordinary_photon n=900 min=-0.998399106615 max=-0.00167109486623 mean=-0.500277750606 z=-0.288647 violations=0
branch=photon_to_neutron n=900 min=-0.999703838375 max=-0.00053755684732 mean=-0.482753202956 z=1.792340 violations=0
paired_seeds=3 equal=3

1/1 Test #62: test_fixed_source_adjoint ........ Passed 0.73 sec
100% tests passed, 0 tests failed out of 1
```

**实验设置（算法实验必填）**：
- 随机种子：17、23、41；RNG type 2，stride 1000000。
- 配置快照：5 cm 球，`x=-0.5`，原子密度 `1.0×10^24 cm^-3`；旧一群资产用于缺陷确认和 warning 根因复核；最终主证据使用两群中心 `[3,1]` MeV、宽度 `[2,2]` MeV、源能量 3 MeV。每个动态矩样本集 300，整程 400 histories。
- 依赖版本：Python 3.12.3、CMake 3.28.3、G++ 13.3.0、GDB 15.1；非 ML 任务，无 CUDA/PyTorch 配置。
- 基准对比：只读既有 reference；未更新 benchmark/reference。

**未覆盖到的验证**：未取得 MCNP manual vol. III Table F.52 官方原文，格式依据限于 RMC 读取逻辑、前向实现一致性和私有 readback；未覆盖其他角表示、真实生产多群 photon 核数据、响应级 photon/secondary 互易性、CE、AIS/HDF5、MPI/OpenMP、Windows、大规模生产算例。旧私有一群输入因 `LocateMgErgGrp()` 在单群时索引恒为 0，每个源历史都会输出“低于最小群下界”warning；另有旧 gdb 中止遗留 STATE warning，均已原样保留且明确排除在干净整程证据之外。新增两群资格资产只用于消除该验证构造的单群退化，不代表真实生产多群数据已覆盖。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：普通伴随 photon 与 photon→neutron 次级的负单变量角核均动态确认为 W9 同类缺陷，并完成两行根因修复。两条生产路径的修复前反例、修复后同路径对照、三种子支持域/理论矩、普通 photon 正向/伴随逐样本一致性、6/6 两群零警告整程、CTest 和 reference 完整性均闭合。旧一群整程有大量 warning，不作为干净成功证据。
- **遗留问题 / 后续待办**：官方格式原文和更广 photon/耦合粒子能力仍未验证；本任务只闭合两个条件角分支，不把 photon adjoint 或 F02 整体评为 A。F02 保持 C — Verify。
- **知识库同步**：更新 `MLVR_Knowledge/06_已知问题与改进建议.md`、`AGENT_CONTEXT.md` 与 `MLVR_Physics_Guide/` 的 W9 范围和证据入口。
- **是否已提交**：未 commit/push/切分支；RMC HEAD 仍为 `6d208751...`，reference/benchmark 未更新。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-26 00:15 | 立项 |
| 2026-08-26 | 完成源码调用链、数据 locator、现有测试与证据边界定位；形成 A/B/C 方案，进入待决策。 |
| 2026-08-26 | 已请求人工选择方案；决策界面返回用户暂不可用，未视为授权，RMC 修改门禁保持关闭。 |
| 2026-08-26 | 用户正式批准方案 A，RMC 修改门禁按“逐路径先动态确认”约束开启，进入实施。 |
| 2026-08-26 | 两条生产路径分别取得修复前动态反例后完成两行最小修复；三种子矩、配对、CTest、哈希和归档通过，任务完成。 |
| 2026-08-26 | 用户质疑旧一群整程 warning；复核确认质疑成立，旧日志降级为辅助证据。新增两群资产后，6/6 整程及 9/9 GDB 日志均零 Warning/零 Error，任务按更严格门槛重新闭合。 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 修复建档脚本首日空匹配 | `MLVR_develop/new_task.sh` | 原脚本在当天无目录时因 `pipefail` 退出 2；改用 `nullglob` 数组，`bash -n` 通过并成功建档。 |
| 3 | 锁定候选公式 | `GetMgExitErgMu.cpp` | 两个负单变量分支仍为 `(1-x)`；对应前向 photon 为 `(1+x)`。 |
| 4 | 追踪生产可达性 | `ProcessMgPhotonCollision.cpp`、`TreatAdjointMaterial.cpp` | 普通伴随 photon 有直接调用；secondary 由散射搜索耗尽后进入，均有上游截面构造。 |
| 5 | 核对数据装载 | `ReadAceData.cpp`、`Nuclide.h` | 普通 photon 使用独立 gamma ACE 的 `PXSS`；secondary 使用 neutron ACE secondary block 的 `XSS`。 |
| 6 | 核对既有验证资产 | 任务 11/12、RMC tests | W9 harness 可复用方法，但没有覆盖 photon/secondary 的现成动态资产。 |
| 7 | 冻结工作树 | `git -C RMC status --short --branch` | 分支领先 origin 1；仅 `src/GetMgExitErgMu.cpp` 修改，为任务 12 既有 W9 一行。 |
| 8 | 人工门禁 | 本 README 第 4 节 | 等待用户选择方案；尚未修改 RMC。 |
| 9 | 请求人工决策 | VS Code 问答 | 用户暂不可用；没有选择 A/B/C，不构成授权。 |
| 10 | 用户正式拍板 | 对话请求 / 本 README 第 4 节 | 方案 A 获批；允许先构建资产并逐路径动态确认，确认后做对应最小修复。 |
| 11 | 普通 photon 可观测性 | PTRAC、GDB | photon PTRAC 为空；Release 二进制无行表，改用函数入口 ABI 保存 `double& MuLab` 地址并在返回断点读取。 |
| 12 | 普通 photon 修复前/后 | `photon_*gdb_samples.txt` | `130/200` 越界降为 `0/200`，随后进入第二路径。 |
| 13 | mixed 表首次烟测 | `secondary_photon_probe_v1` | 输入沿用纯 photon 的 `ERGGRP=0 1`，RMC 正确拒绝 neutron 群数冲突；修正为 `1 1` 后 v2 退出 0。 |
| 14 | secondary 修复前/后 | `secondary_photon_*gdb_samples.txt` | `144/200` 越界降为 `0/200`。 |
| 15 | 三种子与配对 | matrix/pair analyzers | 两路径 1800 样本零越界；所有 z 判据通过；普通 photon 900 对逐样本一致。 |
| 16 | 回归与归档 | CTest、hash、diff、知识库、物理导读 | 1/1 CTest 通过，reference 不变，快照与证据边界完整记录。 |
| 17 | 复核用户指出的 warning | 六份旧整程日志、`LocateMgErgGrp()`、`GetIntpltPos()` | 旧运行确有 401/402 条 warning；退出 0 不能称为干净成功。根因是单群插值索引恒为 0。 |
| 18 | 两群资格资产 | two-group generators / verifiers | ordinary、secondary 两套独立 readback 通过；源能量 3 MeV 合法落入索引 1。 |
| 19 | 严格整程复验 | `analyze_two_group_clean_validation.py` | 6/6 整程、9/9 生产采样日志无 Warning/Error；矩、支持域及普通 photon 前/伴随配对全部通过。 |
| 20 | 归档整理 | `.gitignore` 既有规则、`logs/README.md` | 删除全开发区可重建的 `runs/`/`cases/` 与缓存；本任务 56 份原始记录按证据角色分层，内容和数量不变。 |

**可选**：若人机讨论较深入，另写一份 `会话纪要.md`
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
