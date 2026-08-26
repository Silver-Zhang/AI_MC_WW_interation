# f02-remaining-angular-representations

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-26 |
| 状态 | 实施中（formal 已冻结） |
| 任务类型 | 物理验证 / 验证资产复用 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F02 |
| 涉及文件 | 只读 `RMC/src/GetMgExitErgMu.cpp`；复用任务 11 的私有 MGACE、独立 oracle 与任务侧验证工具 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `6d2087518e0d9f23574d629f5fde361c79f519e4`；RMC 工作树有未同步 W9 三行改动，本任务不修改、不提交或推送 RMC |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：对 W9 负单变量分支之外的四类 standard ASCII MGACE neutron 条件角表示，执行独立 readback、生产调用路径可达性和动态分布矩验证。对象为：各向同性、`ISANG=0,NLEG=1,x=+0.5` 正单变量、`ISANG=0,NLEG=4` 等概率多 bin，以及 `ISANG=1,NLEG=5` 离散余弦。目标是补足 F02 从 C — Verify 迈向 A formal 前的角表示证据；不预设 A 结论。

**范围**：只读 `RMC/`，在任务目录和 `/tmp` 创建输入、运行产物、分析脚本及日志；Linux x86_64、串行、standard ASCII MGACE、fixed-source neutron、`ais=OFF`。复用任务 11 已资格化的私有一群自散射资产。排除 photon/secondary、density-mesh HDF5、裂变、材料混合、CE、AIS/HDF5、MPI/OpenMP、Windows、reference/benchmark 和任何 RMC 代码改动。

**验收标准**：

1. 四类资产均由独立 oracle 再次验证 NXS/JXS/XSS locator、SHA256、理论支持域、均值与方差（离散余弦还验证各点概率）。
2. 每类均在前向和伴随生产路径取得可识别样本；记录函数调用栈、输入/资产/二进制哈希、退出码，并排除 warning/error/signal。
3. 对连续表示，以预冻结的支持域零越界、均值 $|z|\le3$ 和方差统计门槛判断；对离散表示，以预冻结的逐点频数 goodness-of-fit 判据判断。样本数、种子、容差和检验方法须在正式运行前冻结，不能因结果挑选或局部追加。
4. 前向/伴随在相同私有资产和随机流下的分布与理论矩均相容；若发现支持域、矩、离散概率或生产可达性异常，保留原始反例并停止，不擅自改 RMC。
5. 运行结束后执行 CTest/reference 完整性、`git diff --check` 和 RMC 工作树边界检查；不更新 reference/benchmark。

**原始材料**：`logs/user_request.txt` 保存本轮授权和 RMC 不同步约束。任务 11 的 `assets/mgace/manifest.json`、`logs/mgace_qualification_corrected.json` 与 README 是既有资产/理论证据；任务 12、任务 26-01 是已修复负单变量的边界证据。本任务后续的命令、环境、readback、运行和分析真实输出均原样保存在 `logs/`。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：任务 11 已生成并独立资格化五类一群私有角资产，但在负单变量缺陷被动态确认后按停止规则，未执行另外四类的生产动态矩验证。W9 后续修复已覆盖 neutron、ordinary photon 与 photon→neutron 次级的负单变量公式；这不自动证明其他表示正确。现有资产的 readback 理论值为：各向同性 $[-1,1]$、均值 $0$；正单变量 $[0,1]$、均值 $0.5$；等概率多 bin $[-1,1]$、均值 $-1/12$；离散余弦支持 $[-0.8,0.9]$、均值 $0.11$。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `MLVR_Knowledge/02_RMC功能审查矩阵.md` F02-B | 明确列出其余四类角表示动态矩为 F02 A formal 前缺口。 |
| 2 | `20260825_11.../assets/mgace/manifest.json` | 已冻结四类资产的 `ISANG/NLEG`、角数据、表路径和 SHA256。 |
| 3 | `20260825_11.../tools/verify_angular_mgace.py` | 独立读回 oracle 给出支持域和理论均值；须扩展到方差/离散质量检验。 |
| 4 | `RMC/src/GetMgExitErgMu.cpp:GetMgNeuExitErgMu()` | 前向与伴随均含 isotropic、单变量、等概率多 bin 与离散余弦分支。 |
| 5 | `20260825_11.../tools/generate_dynamic_cases.py`、`run_dynamic_cases.py` | 已有不修改部署核库的标准路径输入/运行骨架，但 PTRAC 射线重建不适合所有伴随表示，需先评估观测器。 |
| 6 | `20260825_12.../README.md`、`20260826_01.../README.md` | W9 修复后的 ABI/GDB 生产采样方法可作为候选观测器；当前仅保存返回值，不能替代逐样本公式审计。 |

**影响面**：不改生产代码、接口、部署核库、reference 或 benchmark。通过只能增强 standard ASCII MGACE、neutron、串行、固定源的代表性角表示证据；不能覆盖 density mesh、裂变、混合材料、photon 全范围、AIS/HDF5 或 F02 完整能力。

**为什么之前没做/没发现**：任务 11 的预设停止规则要求在确认 W9 缺陷后停止剩余控制案例，以免将修复前后逻辑和 A formal 证据混淆。W9 修复归档及仓库同步后，才适合把它们作为独立验证任务继续。

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A：先观测器 pilot，再冻结正式动态矩 | 复用四类资产和 readback；用 `/tmp` 小样本比较 ABI/GDB 采样与 PTRAC 观测能力，确认每类前向/伴随都进入目标函数且返回值可捕获后，冻结多 seed/样本数/统计判据并运行正式矩阵。 | 证据最强且避免把不适用的 PTRAC 几何重建当作所有表示的 oracle；需先定义离散频数检验。 | ★推荐 |
| B：直接复用任务 11 PTRAC 射线交会方法 | 对四类资产直接做低光学厚度 PTRAC 分析。 | 伴随 elastic 记录不完整，且几何重建曾受多碰撞混淆；可能无法区分观测器缺陷与生产行为。 | 不推荐 |
| C：只做静态/readback 复核 | 重新运行资产 oracle，不运行 RMC。 | 不能证明生产路径可达，不填补知识库列出的动态矩缺口。 | 不采用 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A — 先观测器 pilot，再冻结正式动态矩。
- **决定人 / 日期**：用户 / 2026-08-26（“按照你的计划进行完成”）。
- **理由与约束**：先同步非 RMC 仓库；RMC 暂不与远端同步。本任务只读 RMC，不得修改、提交、推送或合并 RMC；不更新 reference/benchmark。pilot 成功是冻结正式矩阵的前置条件；任一表示不可达或统计异常时停止并保留反例。

- **formal 授权 / 日期**：用户 / 2026-08-27（“请执行你的计划”）。
- **冻结范围**：仅 private two-group standard ASCII neutron MGACE、fixed source、neutron forward/adjoint、Linux serial、`ais=OFF`、当前二进制 SHA256 `8fff3f0f534d2a2a116e033a26cf4bb62005c5b6d62b29925423b97bb74f13c2`。
- **冻结资产**：`two_group_locator_oracle_v5` 资产 manifest SHA256 `f1cbaacc5112b1e58bb09bcfeca85c7cdce0b3a6711b26bbfba301459f5fc283`；四类表示 × forward/adjoint × seeds `17,23,41,59,83`，共 40 条；每条 50,000 histories、密度 1.0、RNG type 2、stride 1,000,000。
- **冻结观测与结构门禁**：每条以生产 `MuLab` return-boundary GDB probe 取得至少 1,000 样本；exit 0、Warning 0、Error 0、Finish 1、stderr 为空、无 GDB signal、哈希匹配。任何结构门禁失败立即停止并保留反例。
- **冻结统计规则**：连续表示严格支持域；合并样本为主检验，均值 $|z|\le3$；方差采用对应理论分布的预冻结 parametric-bootstrap 双侧 99% 接受区间。离散表示严格支持点，合并样本 Pearson $\chi^2<9.210$（$df=2$、$\alpha=0.01$）。逐 seed 结果仅作诊断，不单独决定通过/失败。统计异常不追加、换 seed、补样或调阈值；完成已冻结矩阵后统一报告。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 一群资产 readback 复验 | 复用任务 11 `verify_angular_mgace.py` | 五类资产重新 qualified；报告 SHA256 `3ecdbec8...85c37f5`。 |
| 2 | 一群生产路径 / ABI-GDB pilot | 四类 × 前向/伴随、seed 17、300 histories、密度 1.0 | 8/8 退出 0；在目标函数返回边界各取得 100 个样本。前/伴随的范围和均值逐类一致：isotropic `[-0.982322,0.988632]` / `0.021543`，正单变量 `[0.010066,0.994039]` / `0.501992`，多 bin `[-0.977628,0.987211]` / `-0.050946`，离散余弦仅取 `{-0.8,0,0.9}`、均值 `0.057`。 |
| 3 | 一群整程日志门禁 | 同一八条 pilot 输入 | 均退出 0、一个 Finish，但存在每 history 一条最低群下界 warning（前向 300、伴随 301）；与此前一群退化告警一致，不能作为 clean formal 整程。 |
| 4 | 首轮两群无告警资产 pilot | 早期 `generate_two_group_angular_mgace.py`，四类 × 前向/伴随、seed 17 | isotropic、正单变量和离散余弦 6/8 整程为零 Warning/零 Error；multi-bin 前向出现 3,035 条 `exit mu out of range` warning，按门禁停止 formal。 |
| 5 | 两群 locator/oracle 闭合 | `verify_two_group_angular_mgace.py` | 按 RMC 的一基 `JXS/XSS` 与两级 `JXS(16)→LXPN→LPND`、`JXS(17)→LPN→PN` 解引用独立读回四资产；验证两群 `[3,1]` MeV 中心、`[2,2]` MeV 宽度、P0、两个 PND/PN 块、多 bin 均值 $-1/12$/方差 $17/48$，以及离散 CDF/概率、均值 $0.11$、方差 $0.3589$。 |
| 6 | 修正后两群 clean pilot | 新资产、四类 × forward/adjoint、seed 17、300 histories、密度 1.0 | 8/8 真实进程 exit 0，`Warning=0`、`Error=0`、`Finish=1`、stderr 0 bytes；multi-bin forward 不再出现越界 warning。证据见 `logs/two_group_locator_oracle_v5/`。 |
| 7 | formal 门禁 | 本 README 第 1、3、4 节冻结门禁 | pilot 前置条件已满足。 |
| 8 | formal 冻结 | README 第 4 节 | 用户授权 40 条、50,000 histories/条、五固定 seeds、1,000 个 GDB 返回样本/条及预冻结的结构/统计门禁。 |

**代码改动**：RMC 无改动。任务侧新增两群资产/输入生成器和 GDB 返回值 probe；当前两群 multi-bin 生成器仅为失败 pilot 的可复核材料，未作为正式资产。

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
| 资产 readback | `verify_angular_mgace.py` | 五类资产 qualified；四类目标表示的静态支持域/理论均值与任务 11 记录一致。 |
| 一群 ABI-GDB pilot | 四类 × forward/adjoint | 8/8 取得 100 个函数返回样本，GDB 日志无 Warning/Error/signal；前向与伴随逐类统计一致。 |
| 一群整程 | 四类 × forward/adjoint | 8/8 exit 0、一个 Finish；但每条 history 均有最低群下界 warning，不能满足 formal 的 clean-run 门槛。 |
| 两群 locator/readback | `verify_two_group_angular_mgace.py --root /tmp/mlvr_two_group_locator_oracle_20260826_v5/assets` | 4/4 qualified；报告 SHA256 `160d7e09...ff9a`。 |
| 修正后两群整程 pilot | `generate_two_group_angular_mgace.py` + `generate_cases.py` + 8 条运行 | 8/8 exit 0、零 Warning、零 Error、恰好一个 Finish、stderr 0 bytes；包括 multi-bin forward。汇总 SHA256 `695e0c03...c74f7`。 |

```
pilot_asset_report_sha256=3ecdbec876af3008a9c0fc23926f5bb17c09df4e6ff3b8f8e3dd304ae85c37f5
one_group_manifest_sha256=3e501e7d8c50b02329896541cc3a2774cc3b4ac5070cf8f5e6b71171937bc3de
two_group_locator_asset_manifest_sha256=f1cbaacc5112b1e58bb09bcfeca85c7cdce0b3a6711b26bbfba301459f5fc283
two_group_locator_oracle_report_sha256=160d7e09faf956428c61510d2cd92dd26fbd1c2de28642b62e4457703399ff9a
two_group_locator_run_manifest_sha256=1a2fefc79d55ff2596543edfd5fdc86810c05935908ee32e1cb8846998cf74aa
two_group_locator_clean_report_sha256=695e0c03b6762c5b3509a4a3639eac3ba66b7728d55c81df3f441a864c0c74f7
two_group_multi_bin_forward_warnings=0
formal_manifest=not_created
```

**实验设置（算法实验必填）**：
- 随机种子：pilot 为 `17`；RNG type 2、stride `1000000`。
- 配置快照：任务 11 原始一群资产（5 cm 球、300 histories、密度 `1.0×10^24 cm^-3`）；两群 pilot 使用中心 `[3,1]` MeV、宽度 `[2,2]` MeV、3 MeV source。
- 依赖版本：Python 3.12.3、GDB 15.1、RMC binary SHA256 `8fff3f0f...f13c2`；串行、`ais=OFF`。
- 基准对比：不是 RE/FOM 实验；对照为任务 11 独立资产 oracle 的理论分布矩。

**未覆盖到的验证**：四类表示的 warning-free 正式动态矩、方差/离散频率的正式统计检验、density-mesh HDF5、`NNUBAR=1`、多材料、更多群对和预冻结响应级 formal 矩阵均未覆盖。两群 multi-bin 的 locator/格式语义现已独立闭合；首轮 warning 是私有资产 locator 布局错误，不构成 RMC 新缺陷证据。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：一群私有资产下，四类表示在已采到的前向/伴随函数返回样本中与静态理论分布相容，说明生产路径和 ABI-GDB 观测器可达；一群整程仍有已知能群告警。两群 P0/XPN/PN locator 经独立 oracle 闭合后，四类 × 前向/伴随 8 条 dense clean pilot 全部通过；multi-bin forward 的首轮越界来自私有资产 locator 布局错误，修正后为 0。
- **遗留问题 / 后续待办**：用户需冻结正式矩阵的多 seed、每条 histories、连续分布支持域/均值/方差门槛、离散余弦频数 goodness-of-fit 判据及失败停止规则。该用户决策前不得运行或宣称 formal 统计结论。
- **知识库同步**：未同步评级；F02 仍为 C — Verify。
- **是否已提交**：RMC 未提交、未推送、未合并；任务档案尚未提交。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-26 11:01 | 立项 |
| 2026-08-26 | 用户授权方案 A；冻结 RMC 只读、不与远端同步。 |
| 2026-08-26 | 一群 ABI-GDB pilot 取得四类前向/伴随生产样本；一群整程因已知下界 warning 不可作 clean formal。 |
| 2026-08-26 | 两群 multi-bin 前向发生 3,035 条越界 warning；按门禁停止，formal 未冻结。 |
| 2026-08-26 | 建立独立 two-group neutron P0/XPN/PN readback oracle；修正私有资产 locator 布局后，四类 × 前向/伴随 8/8 clean pilot 通过。 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 用户拍板 | README 第 4 节 | 采用方案 A；RMC 只读且暂不同步。 |
| 3 | 资产复验与一群运行 | 任务 11 工具、`/tmp` | readback 通过；8/8 exit 0，但一群整程含已知 warning。 |
| 4 | ABI-GDB 采样 | `sample_mulab_gdb.py` | 校正 x86_64 ABI 参数寄存器后，四类前/伴随函数返回值逐类一致。 |
| 5 | 两群 clean-run 尝试 | 任务侧两群生成器、`/tmp` | multi-bin 前向越界 warning；停止，不改 RMC。 |
| 6 | locator 语义定位 | `RMC/src/ReadAceData.cpp`、`CheckMgAceBlock.cpp`、`GetMgExitErgMu.cpp`、`Nuclide.h` | 确认表在内存中一基读取；P0 行 locator 由 `NUS/NDS` 预计算；前向路径经 `JXS(16)→LXPN→PND` 和 `JXS(17)→LPN→PN` 两级解引用。 |
| 7 | 两群独立 oracle | `verify_two_group_angular_mgace.py`、`logs/two_group_locator_oracle_v5/` | 4/4 readback qualified；复核连续/离散理论矩与 CDF。 |
| 8 | 最新两群 clean pilot | 新 `/tmp/mlvr_two_group_locator_oracle_20260826_v5` | 四类 × forward/adjoint、seed 17、300 histories、密度 1.0 均 exit 0、Warning/Error 0、Finish 1、stderr 0；formal 尚待用户冻结。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
