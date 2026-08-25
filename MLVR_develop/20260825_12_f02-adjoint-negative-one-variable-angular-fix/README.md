# f02-adjoint-negative-one-variable-angular-fix

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-25 |
| 状态 | 已完成（W9 已修复；F02 恢复 C — Verify） |
| 任务类型 | 缺陷修复 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F02 / W9 |
| 涉及文件 | `RMC/src/GetMgExitErgMu.cpp`；任务侧 `tools/validate_w9_fix.py` 与验证资产 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / 基线 `6d2087518e0d9f23574d629f5fde361c79f519e4`；未 commit/push |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：修复 standard ASCII MGACE fixed-source neutron-adjoint 在 `ISANG=0,NLEG=1,x<0` 时使用错误区间宽度、产生越界散射余弦的问题，并用任务 11 的私有资产闭合前向/伴随支持域回归。

**范围**：候选修改仅限 `RMC/src/GetMgExitErgMu.cpp:GetMgAdjNeuExitErgMu()` 的负单变量分支及最小测试资产；不修改输入格式、核数据、reference/benchmark，不扩展到 photon/secondary、AIS、CE 或其他角表示，除非人工另行授权。

**验收标准**：`x=-0.5` 的伴随重建样本全部位于 `[-1,0]`，前向/伴随一阶矩与支持域相容；五类私有 MGACE oracle 继续通过；现有 fixed-source adjoint 回归通过且 reference 不变；RMC diff、真实输出和未覆盖范围完整归档。

**原始材料**：`logs/evidence_pointer.txt` 冻结任务 11 最终报告、SHA256、低光学厚度结果和用户授权边界；任务 11 保留输入、manifest、关键逐历史分析、摘要、哈希和重现命令，可再生成的 >10 MB PTRAC 已按归档规范删除。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：任务 11 已在未修改的 RMC `6d208751...` 对私有一群表完成独立 readback 和标准动态路径验证。对 `x=-0.5`，前向公式 `-1+2ξ(1+x)` 给出正确支持域 `[-1,0]`；伴随公式误用 `-1+2ξ(1-x)`，原始范围为 `[-1,2]`。低光学厚度 100000-history 对照中，前向 `0/509` 越界，伴随 `161/330` 越界；多碰撞解释的 Chernoff 上界小于 `10^-175.52`。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `RMC/src/GetMgExitErgMu.cpp:GetMgNeuExitErgMu` | 前向负单变量使用 `(1+x)`，区间均值为表值 `x`。 |
| 2 | `RMC/src/GetMgExitErgMu.cpp:GetMgAdjNeuExitErgMu` | 伴随负单变量使用 `(1-x)`；`x=-0.5` 时原始余弦范围为 `[-1,2]`。 |
| 3 | 任务 11 `mgace_qualification_corrected.json` | locator、P0、表值、支持域和 SHA256 独立读回通过。 |
| 4 | 任务 11 `low_optical_analysis_final.json` | 前向重建器假阳性 0、漏检 1；伴随 161 条支持域违例。 |

**影响面**：确认影响 standard ASCII MGACE neutron-adjoint 的负单变量条件角核；可能影响最终重要性场与互易性。相似 photon/secondary 实现尚未动态确认，不纳入本次默认改动。无需改变输入兼容性或基准数据。

**为什么之前没做/没发现**：部署 MGACE 主要为 `NLEG=0`；PTRAC 的伴随分支不记录 elastic 事件，且 `UpdateNeuStateMg()` 会归一化非法方向，普通方向模检查会隐藏问题。任务 11 用私有强角表和低光学厚度射线交会才动态闭合。

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A：最小根因修复 | 将伴随负分支 `(1-x)` 改为与前向一致的 `(1+x)`；复用任务 11 做支持域回归。 | 最小影响；仍保留前/伴随重复实现。 | ★推荐 |
| B：共享角采样实现 | 抽取前/伴随共用的单变量/多变量余弦采样 helper。 | 可防后续漂移，但扩大本次 blast radius 和回归面。 | |
| C：仅越界回退 | 保留错误公式，遇到 `|mu|>1` 时回退各向同性或截断。 | 掩盖错误矩，不能恢复 `[-1,0]` 分布。 | 不采用 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A — 最小根因修复，将伴随中子负单变量分支 `(1-x)` 改为 `(1+x)`。
- **决定人 / 日期**：用户 / 2026-08-25。
- **理由与约束**：用户明确要求“进行 W9 的修复工作，并且完全的验证”。只修改 W9 根因及必要测试/档案；不更新 reference/benchmark，不扩展到 photon/secondary、AIS、CE，不 commit/push/切分支。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 立项与证据冻结 | `new_task.sh`、`logs/evidence_pointer.txt` | 完成；RMC 改码门禁关闭。 |
| 2 | 人工拍板 | 本 README 第 4 节 | 方案 A 获批，进入实施。 |
| 3 | 最小根因修复 | `RMC/src/GetMgExitErgMu.cpp` | 伴随中子负单变量分支 `(1-x)` 改为 `(1+x)`；其他分支不变。 |
| 4 | 增量构建 | `cmake --build /tmp/mlvr_f02_rmc_build -j2` | 目标源重新编译，RMC 100% 链接成功。 |
| 5 | 三种子动态回归 | seeds 17/23/41，100000 histories/mode | 6/6 运行退出 0；前/伴随共 1438 对样本逐项相等，0 越界。 |
| 6 | 自动判据 | `tools/validate_w9_fix.py` | 三 seed 与合并均值均满足 `|z|≤3`；合并 `z=0.367210`。 |
| 7 | 既有回归与资产 | CTest、MGACE oracle | CTest 1/1 passed；五类 MGACE 5/5 qualified；reference 不变。 |
| 8 | 快照与体积清理 | `changes.diff`、`find ... -size +10M` | 快照仅一行；删除可再生成运行输出，复查无 >10 MB 文件。 |

**代码改动**：见 [changes.diff](changes.diff)，摘要：
- `GetMgAdjNeuExitErgMu()` 的 `NLEG=1,x<0` 分支将区间宽度由 `1-x` 修正为 `1+x`。
- 新增任务侧自动验收器，强制检查支持域、零越界、前/伴随逐样本一致和理论均值 `|z|≤3`。

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
| 设计前基线 | 任务 11 final baseline | RMC clean at `6d208751...`；binary SHA256 `f3870bf4...1f0887`。 |
| 增量编译 | `cmake --build /tmp/mlvr_f02_rmc_build -j2` | `Building ... GetMgExitErgMu.cpp.o`；`[100%] Built target RMC`。 |
| seed 17 动态 | 100000 forward + 100000 adjoint | 两运行退出 0；前/伴随均 509 样本、`0/509` 越界，逐样本完全一致。 |
| seed 23 动态 | 同规格 | 两运行退出 0；前/伴随均 462 样本、`0/462` 越界，逐样本完全一致。 |
| seed 41 动态 | 同规格 | 两运行退出 0；前/伴随均 467 样本、`0/467` 越界，逐样本完全一致。 |
| 理论矩自动判据 | `tools/validate_w9_fix.py` | 单 seed `z=0.829509,-0.061866,-0.160103`；合并 1438 样本、均值 `-0.497204593289`、`z=0.367210`，passed。 |
| 修复前后对照 | `logs/pre_post_comparison.json` | 伴随由 `161/330` 越界变为 `0/509`；前向 PTRAC SHA256 `ad4723d4...088e16` 修复前后不变。 |
| 五类 MGACE oracle | `verify_angular_mgace.py` | `qualified_cases=5`；报告 SHA256 `3ecdbec8...85c37f5`，与修复前一致。 |
| 既有伴随回归 | `ctest --test-dir /tmp/mlvr_f02_rmc_build -R '^test_fixed_source_adjoint$' -V` | 1/1 passed，0 failed，0.71 s。 |
| reference 完整性 | `sha256sum .../reference_result` | `750be025...90443faa`，未更新。 |
| 修复后二进制 | `sha256sum /tmp/mlvr_f02_rmc_build/bin/RMC` | `fd9bd9bd...ca25db`。 |
| 源码诊断与 diff | VS Code diagnostics；`git diff --check` | 无诊断；无 whitespace 错误；RMC 仅目标文件 `1 insertion, 1 deletion`。 |

**实验设置（算法实验必填）**：
- 随机种子：17、23、41；每 seed 前向/伴随共用 RNG 标识，`RNG TYPE=2 STRIDE=1000000`。
- 配置快照：5 cm 球；一群纯自散射；总截面/P0=1 barn、吸收 0；原子密度 `0.001×10^24 cm^-3`；100000 histories/mode。
- 依赖版本：Python 3.12.3；CMake 3.28.3；GCC 13.3.0；RMC 基线和二进制哈希见 `logs/final_integrity.txt`。
- 基准对比：同一 seed 17 修复前伴随 `161/330` 越界；修复后 `0/509`，前向轨迹哈希不变。

**未覆盖到的验证**：本任务完整闭合 W9 的 standard ASCII MGACE fixed-source neutron-adjoint 负单变量分支。未将其他四类角表示做 RMC 动态矩验证，未覆盖 density-mesh HDF5、NNUBAR=1 formal、多材料/多几何 A 矩阵、photon/secondary、AIS、CE、MPI/OpenMP、Windows；这些是 F02 从 C 升 A 的后续门禁，不影响 W9 标记已修复。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：W9 已按方案 A 修复并通过源码、构建、三种子动态支持域/矩、五类资产 oracle、既有 CTest 和 reference 完整性验证。当前没有 W9 失败证据。
- **遗留问题 / 后续待办**：完整 F02 从 E 恢复为 **C — Verify**，不是 A；继续任务 10/11 未完成的角表示、density mesh、裂变和 formal 矩阵。
- **知识库同步**：W9 标记已修复；F02 矩阵、Agent 快速上下文和物理导读恢复 C 并保留 A 门禁。
- **是否已提交**：未 commit/push/切分支；RMC 工作树仅有本任务一行修改，由用户决定提交。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-25 20:16 | 立项 |
| 2026-08-25 20:17 | 完成根因定位与方案，进入待决策。 |
| 2026-08-25 | 已提交方案 A/B/C 请求人工拍板；用户暂不可用，未形成第 4 节决策，RMC 门禁保持关闭。 |
| 2026-08-25 | 用户明确授权 W9 修复与完整验证；采纳方案 A，RMC 门禁开启。 |
| 2026-08-25 | 最小修复、三种子动态回归、CTest、oracle、哈希与归档完成；W9 闭合。 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 导入触发证据 | 任务 11 最终报告与基线 | E 分类成立；未修改 RMC。 |
| 3 | 形成修复选项 | 本 README 第 3 节 | 推荐最小根因修复，等待用户拍板。 |
| 4 | 请求人工决策 | VS Code 问答 | 用户暂不可用；不视为授权，状态保持待决策。 |
| 5 | 用户正式拍板 | 对话请求 | 方案 A 获批；允许开始最小 RMC 修改。 |
| 6 | 修改并增量构建 | `GetMgExitErgMu.cpp`、CMake | 一行修复，构建通过。 |
| 7 | seed 17 直接反证检查 | 任务 11 harness | 伴随由 161 条越界降为 0；前/伴随样本完全一致。 |
| 8 | seeds 23/41 重复 | 同规格独立运行 | 0 越界；逐样本一致，排除单 seed 偶然性。 |
| 9 | 自动验收与回归 | validator、CTest、oracle | 理论矩、支持域、资产和既有回归全部通过。 |
| 10 | 证据冻结与清理 | hashes、`changes.diff`、体积检查 | 真实输出已归档；可再生成大文件已删除。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
