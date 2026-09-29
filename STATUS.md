# 项目状态（人只看这一页）

> **最后更新：2026-09-29** ｜ 更新责任：Agent 在任务**归档（第 ⑤ 步）时同步本页**
> 详细任务清单（80 项）→ [`MLVR_develop/INDEX.md`](MLVR_develop/INDEX.md) ｜ 工作流规则 → [`MLVR_develop/README.md`](MLVR_develop/README.md) ｜ 一屏上下文 → [`MLVR_Knowledge/AGENT_CONTEXT.md`](MLVR_Knowledge/AGENT_CONTEXT.md)

## 1. 现在在哪个 Stage

```
Stage 0 ✅ ─► Stage 1 ✅ ─► Stage 2 🟡 收尾 ─► Stage 3/4 ⏭ 下一步 ─► Stage 5…8 ⬜
```

| Stage | 内容 | 状态 |
|---|---|---|
| 0 | 工作流与知识库建立 | ✅ 完成 |
| 1 | 双向迭代框架功能需求定义 | ✅ 第一版基线已冻结 |
| 2 | RMC 现有功能审查 | 🟡 **F02** 多群伴随输运 → 有界 A–Ready；**F03** 伴随源定义 → C–Verify（冻结子域，方案 A）；**F08** WW → E — Defect + D — Integration issue（源码审计） |
| **3 → 4** | **功能缺口修复与补充 → 功能接口分析与框架设计** | 🟡 F08 主要缺陷已修复并回归；F10 Field Reconstruction 数据边界 **design frozen，尚未实现**；F11 前置（持久执行能力）两份独立审查已完成（审查时未有动态复用证明），E0–E4 动态实验全部 PASS、独立复核 **ACCEPT WITH LIMITATIONS**（限定实验 lifecycle contract，正式 persistent API 未实现）；MLVR 已限定为 native track mesh，状态复制和 adjoint 组合仍待处理 |
| 5 → 8 | 分模块实现 → 双向迭代 WW 框架 → 场重构 → 高级 ML 方法 | ⬜ 未开始 |

一句话：**F08 主要确定性缺陷已修复并回归；F10 首版数据合同已冻结、无实现；F11 前置两份独立审查已归档（生产 session 接口尚未实现），E0–E4 动态实验全部 PASS、独立复核 ACCEPT WITH LIMITATIONS（限定实验 lifecycle contract）；其余框架与组合边界待后续任务。**

## 2. ⛔ 等你拍板（不拍板 Agent 不动）

| # | 事项 | 需要你决定什么 | 相关档案 |
|---|---|---|---|
| 1 | **启动 Stage 3/4** | 是否现在开新任务做「双向迭代 WW 框架接口设计」（F03 已拍板：MLVR 侧外部构造 response→源，RMC 只管执行） | [f03 审查](MLVR_develop/2026-08/20260825_09_f03-adjoint-source-definition-audit/README.md) |
| 2 | F04 扩展验证 | F04 的 MG native `WWE:N` 物理能量坐标契约已修复并在 serial 验证；是否扩展至 MPI/OpenMP、耦合粒子或多 mesh，取决于第一版实际问题需求 | [F04 修复](MLVR_develop/2026-09/20260923_01_f04c-mg-native-ww-energy-contract/README.md) |
| 3 | AIMC 正式实验 | Task 08B 正式矩阵（30 iterations × 400M histories）已就绪但**未运行**，需单独授权才能开跑 | [task08a 冻结](MLVR_develop/2026-09/20260905_03_task08a-experiment-freeze-harness/README.md) |
| 4 | RMC push 时机 | 分支 `Neural_Network_WW_Iteration` 现有 5 个本地提交未 push（含 MPI shared offset 与 MG `WWE:N` 修复，均本地验证/复核通过）；何时 push origin 由你决定 | [MG WW 修复](MLVR_develop/2026-09/20260923_01_f04c-mg-native-ww-energy-contract/README.md)、[MPI offset](MLVR_develop/2026-09/20260920_02_f08-mesh-ww-mpi-offset/README.md) |
| 5 | 台账遗留 | `20260824_05`（F02-B 物理验证）台账仍标「待决策」；其 W5/W6 缺陷已修复并复现——确认后可直接关闭 | [档案](MLVR_develop/2026-08/20260824_05_f02-adjoint-physics-verification/README.md) |
| 6 | MG WW 输入契约加固 | V2/V3 source-energy 注入错误已修正并重跑；已确认 0.4015 MeV 实际进入高群用例，但碰撞数仍是间接证据。群内 `WWE:N` 边界建议与 MG 群边界对齐；direct selected-bin oracle 尚未实现 | [修复与补测](MLVR_develop/2026-09/20260923_01_f04c-mg-native-ww-energy-contract/README.md)、[独立复核](MLVR_develop/2026-09/20260923_02_independent-mg-ww-repair-review/README.md) |
| 7 | F06 输出接口 | F06 已完成 C — Verify（含 R1/R2 两轮独立复核，结论一致）：`Energy=-1` + `Normalize=1` 的 Type=1 Cartesian mesh tally 在 serial text 输出中可解释为 $\phi^\dagger_{i,g}$；HDF5 无能群轴，F07 统计另审 | [F06 档案](MLVR_develop/2026-09/20260926_01_f06-adjoint-spatial-energy-field/README.md)、[R1 复核](MLVR_develop/2026-09/20260926_02_independent-f06-adjoint-field-review/README.md)、[R2 复核](MLVR_develop/2026-09/20260926_03_independent-f06-adjoint-field-review-r2/README.md) |
| 8 | **F07 RE 统计语义** | **已完成 C — Verify（限定 serial text-first Cartesian）**：source-history RE 与 WW bank-drain 归属已确认；独立复核完成一个 field bin 的 10-seed WW-on 校准（PTRAC-active，`Q=0.88769`）；zero-score `RE=0` 不是零不确定度，全部 bins 与非单位源权重等未覆盖 | [F07 档案](MLVR_develop/2026-09/20260927_01_f07-field-statistical-uncertainty/README.md)、[独立复核](MLVR_develop/2026-09/20260927_02_independent-f07-field-re-review/README.md) |
| 9 | **F01/F05 Forward Field** | **已完成 A — Ready（限定 serial text 子域）**：200k-history standard MGACE forward neutron fixed-source 正常结束；Cartesian Type=1、`Energy=-1`、`Normalize=1` 输出 2 spatial × 30 MG rows 的 `Ave/RE`，空间差异明显 | [合并档案](MLVR_develop/2026-09/20260927_03_f01-f05-forward-field-closure/README.md) |
| 10 | **F12 Bootstrap MC-side chain** | **已完成 A — Ready（限定首版）**：20k low-population、无 WW 的 standard MGACE forward 运行得到 2 spatial × 30 MG `phi0/Ave + RE0`；`stage=bootstrap` 与 formal iteration 分离；不含 Field Reconstruction 或 `WW_A^(1)` | [F12 档案](MLVR_develop/2026-09/20260927_04_f12-bootstrap-forward-chain/README.md) |
| 11 | **F09 Response + FOM information** | **已完成 A — Ready（限定第一版子域）**：200k formal Forward serial run 同一 scalar target 输出 `R`、`RE_R` 与 `Time in Fixed Source Calculation`；单-run FOM 可外部计算；不含 Bootstrap/FOM controller | [F09 档案](MLVR_develop/2026-09/20260927_05_f09-response-fom-closure/README.md) |
| 12 | **F10 Field 数据合同** | **design frozen（implementation not completed）**：三项 minor corrections 已按你批准写回设计；是否/何时另立 F10 实现任务（Adapter/parser → Reconstruction → WW Builder）由你决定；F11 按你指示未启动 | [设计](MLVR_develop/2026-09/20260927_06_f10-field-reconstruction-boundary/README.md)、[修订](MLVR_develop/2026-09/20260927_08_f10-minor-corrections-f07-sync/README.md) |
| 13 | **F11 前置审查** | 两份独立源码审查已归档（Codex：运行生命周期/复用能力；Claude：persistent execution；互不参阅）：当前 RMC 缺少经证明可重复调用的 fixed-source session；后续最小动态实验已完成（见 #14） | [Codex 报告](MLVR_develop/2026-09/20260929_09_f11-rmc-runtime-architecture-audit-codex/README.md)、[Claude 报告](MLVR_develop/2026-09/20260929_10_f11-rmc-persistent-execution-audit-claude/README.md) |
| 14 | **F11 架构设计启动** | E0–E4 动态实验全 PASS，独立复核 Task 14 结论 **ACCEPT WITH LIMITATIONS**（E1/E3/E4 证据可接受；E0/E2/归一化受模型边界限制；Task 13 manifest 哈希不一致已修复）。动态证据已足以进入受限 F11 架构设计；是否现在立项（或先补可裂变 E2 验证）由你决定 | [动态执行报告](MLVR_develop/2026-09/20260929_13_f11-persistent-session-e0-e4-execution/README.md)、[独立复核](MLVR_develop/2026-09/20260929_14_independent-f11-e0-e4-dynamic-review/README.md) |

## 3. 最近完成

| 日期 | 任务 | 结果 |
|---|---|---|
| 09-29 | independent-f11-e0-e4-dynamic-review | 独立复核 Task 13 动态证据：**ACCEPT WITH LIMITATIONS**——E1/E3/E4 合同证据可接受；E0/E2/归一化受模型边界限制；独立重跑 comparator 复现 PASS；指出 manifest 一处 README 哈希不一致（整理编辑所致，已修复）；RMC 未修改 |
| 09-29 | f11-persistent-session-e0-e4-execution | E0–E4 全部 PASS（限定 task-private lifecycle contract）；F/A gates、fresh exact oracle、真实 WW2 查窗、tally reset 与 G+1 已有动态证据；共享 RMC 未改；[报告](MLVR_develop/2026-09/20260929_13_f11-persistent-session-e0-e4-execution/README.md) |
| 09-29 | f11-persistent-session-minimal-experiments | F11 最小实验 E0–E4 协议冻结 + P0/P1 提案交付：全部 BLOCKED（未编译、未运行、无 fresh oracle）；当时待批准，后续授权执行见 Task 13；RMC 未修改 |
| 09-29 | independent-f11-persistent-experiment-review | 独立复核（先立验收标准后读结果）：E0–E4 INCONCLUSIVE（全部未运行、空测量）；建议批准前先补全可审查实验包；RMC 未修改 |
| 09-29 | f11-rmc-runtime-architecture-audit-codex | F11 前置独立源码审查（Codex）：生命周期/初始化复用/固定源重复执行/F-A 切换/全局状态与 IO 审计；无可直接重复调用的 fixed-source session 边界；未做实验、未决定架构；RMC/AIMC 只读 |
| 09-29 | f11-rmc-persistent-execution-audit-claude | F11 前置独立源码审查（Claude）：确认单次命令行生命周期；persistent session、F/A 转换、WW hot update、tally snapshot、输出隔离为缺口/未验证；列 E1–E6 最小实验（未执行）；RMC/AIMC 只读 |
| 09-27 | f10-minor-corrections-f07-sync | 用户批准的 F10 三项小修正已写回，**design frozen；implementation not completed**；F07 WW-on 校准状态已按独立复核更新；RMC 未修改 |
| 09-27 | f10-field-reconstruction-boundary | F10 第一版数据合同初稿完成；独立复核三项小修正已由后续 `20260927_08` 写回；没有 parser/算法/WW 实现，RMC 未修改 |
| 09-27 | independent-f10-field-boundary-review | 独立设计复核：**ACCEPT WITH MINOR CORRECTIONS**（拒绝负 `Ave`、记录 source-normalization identity、明确 flux-density unit）；无实现/运行证据；RMC 未修改 |
| 09-27 | f12-bootstrap-forward-chain | F12 MC-side 闭环完成：低粒子数无 WW Forward → Bootstrap `phi0[i,g]+RE0[i,g]`；分类 A — Ready（限定首版）；RMC 未修改 |
| 09-27 | f09-response-fom-closure | F09 formal Forward response/FOM 信息闭环完成：200k serial run 输出同一 scalar target 的 `R`、`RE_R`、fixed-source time；单-run FOM 外部计算成立；分类 A — Ready（限定第一版子域）；RMC 未修改 |
| 09-27 | f01-f05-forward-field-closure | 轻量闭环验证完成：F01/F05 均 A — Ready（限定 standard MGACE、fixed-source neutron、Cartesian Type=1、`Energy=-1`、`Normalize=1`、MPI/OMP-off serial text）；RMC 未修改 |
| 09-27 | f07-field-statistical-uncertainty | 只读审查 F07 RE 统计：source-history RE 公式与 WW bank-drain 归属确认；该任务未做 field-bin WW-on 校准，后续独立复核 `20260927_02` 已完成受限校准；RMC 未修改 |
| 09-27 | independent-f07-field-re-review | 独立复核（静态 E1、runtime E2/E3）：N scaling 1.975/1.993、analog Q=0.849、WW Q=0.888、Normalize RE 不变；结论 C — Verify（限定 serial）；RMC 未修改 |
| 09-26 | f06-adjoint-spatial-energy-field | 只读审查完成：fixed-source MG neutron adjoint、Cartesian、Type=1、`Energy=-1`、`Normalize=1`、serial text 输出可恢复 2 spatial × 30 group 场；HDF5 无 energy axis；分类 C — Verify；RMC 未修改 |
| 09-26 | independent-f06-adjoint-field-review | 独立复核：raw/normalized 体积比 49,999.24 / 150,000.0 cm³；确认 text-first 子域，HDF5 与 geometry warnings 为边界；RMC 未修改 |
| 09-26 | independent-f06-adjoint-field-review-r2 | R2 独立 source/docs/runtime 复核（静态 E1、runtime E2、行为 E3）：修正几何后 volume ratios 与文本 2×30 结构确认；HDF5 `/Type1` 无 energy 维；C — Verify（限定 serial）；RMC 未修改 |
| 09-23 | f04c-mg-native-ww-energy-contract | 修复 MG native `WWE:N` 坐标契约；补正 V2/V3 脚本后确认 0.2435/0.4015 MeV 均实际进入 forward/adjoint 用例。碰撞行为为间接 bin 证据；direct selected-bin oracle 仍缺。RMC commit `5cfb0f77`（未 push） |
| 09-23 | independent-mg-ww-repair-review | 独立审查：认可 native MG group→physical centre 修复，但群内 WWE boundary 无唯一物理含义、无 direct bin-ID oracle；结论 Repair is correct with explicit limitations；RMC 未修改 |
| 09-22 | f04b-static-ww-contract-audit | 静态契约审查（Confirmed mismatch）：MG `p_dErg` 离散群坐标直接查 literal `WWE:N`（解析/查找/文档证据链）；forward 与 adjoint 同链；RMC 未修改；修复决策待人工 |
| 09-22 | f04b-deep-penetration-ww-benchmark | 100 cm water deep-penetration MG adjoint benchmark（5×1M paired，MPI-off/OpenMP-off）：$z=0.29571$，FOM ratio=9.24161，PTRAC 6009 split/31449 roulette；仅 native single-interval track-mesh WW；RMC 未修改 |
| 09-22 | f04-independent-ww-verification | 独立实验验证（模式 C）：群坐标 `WWE:N` 下 WW on/off 无偏性通过（合并 $z=-1.16537$），FOM 比值 0.8522；独立确认 MG `p_dErg` 与 literal physical-MeV `WWE:N` 存在潜在失配；RMC 未修改；正式分类待人工决定 |
| 09-20 | independent-adjoint-ww-physics-review | 独立 E1 源码/测试输入审查：报告认为 MG `p_dErg` 组号与 native WW 物理能量边界的契约未证明一致，且未找到 combined input；结论待人工决定，RMC 未修改 |
| 09-20 | f08-mesh-ww-event-semantics | track 时序为段起点 WW→tally→移动；point 最终余段不触发；用户决定 MLVR 仅支持 native track mesh、跳过 point 修复；native mesh WW 3/3 回归通过；RMC 未修改 |
| 09-19 | f08-heter-mesh-max-boundary | 异构 Cartesian/cylindrical 最大边界统一为 mesh 外；RMC `41cf4559`，mesh WW 3/3 与异构 tally 1/1 回归通过；未 push |
| 09-19 | f08-mesh-ww-shape-validation | native `WWMESH` 现强制空间 mesh × 能群数等于 lower-bound 数量；RMC `5ec595e1`，MPI-off 构建成功、mesh WW 3/3 回归通过，9/11 项输入被拒绝；未 push |
| 09-19 | f08-cell-ww-core-repair | native `WWP:N/P/E` 参数生命周期已修复；MPI-off 构建成功、cell WW 3/3 回归通过，额外 `WWP:P` 不再影响 neutron tally；未 push |
| 09-18 | f08-weight-window-audit | 源码优先审计完成：E — Defect + D — Integration issue；未修改 RMC，Stage 3 修复候选已登记 W10 |
| 09-18 | f08-ww-physics-guide | 完成 `MLVR_Physics_Guide/02_RMC权重窗/README.md`；明确 WW 无偏关系、代码问题、物理影响和证据边界；未修改 RMC |
| 09-18 | workflow-simplification | 模板 10→5 节；模式 C 产物 6→3 内嵌；验证分场景；**保留 A/B/C**；新增本页 |
| 09-18 | f03-adjoint-source-definition-audit | 拍板方案 A；外部映射动态验证通过 → C–Verify（冻结子域） |
| 09-17 | 工作区治理 ×4 | 按月归档、多仓库卫生、遗留资产清理、工作流加固（新增两个自检脚本） |
| 09-05 | task08a（冻结 + R2 修复） | 实验冻结 harness 与阻塞修复完成（READY ≠ RUN） |
| 09-04 | task01–07（物理审查系列） | 网格 tally / 度量管线 / 前向-伴随互易 / WW 事件语义 / 迭代历史 / 场重构等审查归档 |

## 4. 下一步（Agent 建议，待你点头）

1. **后续 Stage 3/4 框架工作**：F10 数据边界已有首版设计合同，但尚无实现；F03 外部 response→source、F04 伴随+native WWMESH、F06 serial text-first 场输出与 F08 native WW 主路径为后续接口工作的已知边界。F11 正式调度尚未实现；授权的 E0–E4 已全部 PASS 且独立复核通过（ACCEPT WITH LIMITATIONS），受限 F11 架构设计是否启动待拍板，证据见 Task 13/14。
2. **F04 按需扩展**：仅当首版实际问题需要 MPI/OpenMP、耦合粒子或非单 mesh 时，另立任务扩展验证；不做无限矩阵。
3. **收尾治理**：关闭台账遗留项 `20260824_05`；知识库 W10 与变更记录已同步。

## 5. 维护方式（Agent 必读）

- 新建任务、状态变化、Stage 推进时回写本页第 1–3 节；**归档（第 ⑤ 步）必须同步本页**。
- 本页只放**看板信息**（阶段 / 待拍板 / 最近完成 / 下一步），细节一律写进任务档案；**保持一屏以内**。
- 多个 Agent 可能并行工作：本页与 `INDEX.md` 是共享文件，动手前先看 `git status`，不要把别人的未提交内容一起提交。
