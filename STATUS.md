# 项目状态（人只看这一页）

> **最后更新：2026-09-23** ｜ 更新责任：Agent 在任务**归档（第 ⑤ 步）时同步本页**
> 详细任务清单（47 项）→ [`MLVR_develop/INDEX.md`](MLVR_develop/INDEX.md) ｜ 工作流规则 → [`MLVR_develop/README.md`](MLVR_develop/README.md) ｜ 一屏上下文 → [`MLVR_Knowledge/AGENT_CONTEXT.md`](MLVR_Knowledge/AGENT_CONTEXT.md)

## 1. 现在在哪个 Stage

```
Stage 0 ✅ ─► Stage 1 ✅ ─► Stage 2 🟡 收尾 ─► Stage 3/4 ⏭ 下一步 ─► Stage 5…8 ⬜
```

| Stage | 内容 | 状态 |
|---|---|---|
| 0 | 工作流与知识库建立 | ✅ 完成 |
| 1 | 双向迭代框架功能需求定义 | ✅ 第一版基线已冻结 |
| 2 | RMC 现有功能审查 | 🟡 **F02** 多群伴随输运 → 有界 A–Ready；**F03** 伴随源定义 → C–Verify（冻结子域，方案 A）；**F08** WW → E — Defect + D — Integration issue（源码审计） |
| **3 → 4** | **功能缺口修复与补充 → 功能接口分析与框架设计** | 🟡 F08 native WWP、WWMESH 输入形状、异构最大边界与 MCNP `WWINP` MPI shared mesh 多粒子 offset 已修复并完成 MPI-off / MPI 2·10 rank 回归；MLVR 已限定为 native track mesh，状态复制和 adjoint 组合仍待处理 |
| 5 → 8 | 分模块实现 → 双向迭代 WW 框架 → 场重构 → 高级 ML 方法 | ⬜ 未开始 |

一句话：**F08 的主要确定性缺陷（WWP 生命周期、WWMESH 形状校验、异构最大边界、WWINP MPI shared offset）已修复并回归；下一步是状态复制/adjoint 组合边界与双向迭代框架设计。**

## 2. ⛔ 等你拍板（不拍板 Agent 不动）

| # | 事项 | 需要你决定什么 | 相关档案 |
|---|---|---|---|
| 1 | **启动 Stage 3/4** | 是否现在开新任务做「双向迭代 WW 框架接口设计」（F03 已拍板：MLVR 侧外部构造 response→源，RMC 只管执行） | [f03 审查](MLVR_develop/2026-08/20260825_09_f03-adjoint-source-definition-audit/README.md) |
| 2 | F04 扩展验证 | F04 的 MG native `WWE:N` 物理能量坐标契约已修复并在 serial 验证；是否扩展至 MPI/OpenMP、耦合粒子或多 mesh，取决于第一版实际问题需求 | [F04 修复](MLVR_develop/2026-09/20260923_01_f04c-mg-native-ww-energy-contract/README.md) |
| 3 | AIMC 正式实验 | Task 08B 正式矩阵（30 iterations × 400M histories）已就绪但**未运行**，需单独授权才能开跑 | [task08a 冻结](MLVR_develop/2026-09/20260905_03_task08a-experiment-freeze-harness/README.md) |
| 4 | RMC push 时机 | 分支 `Neural_Network_WW_Iteration` 现有 5 个本地提交未 push（含 MPI shared offset 与 MG `WWE:N` 修复，均本地验证/复核通过）；何时 push origin 由你决定 | [MG WW 修复](MLVR_develop/2026-09/20260923_01_f04c-mg-native-ww-energy-contract/README.md)、[MPI offset](MLVR_develop/2026-09/20260920_02_f08-mesh-ww-mpi-offset/README.md) |
| 5 | 台账遗留 | `20260824_05`（F02-B 物理验证）台账仍标「待决策」；其 W5/W6 缺陷已修复并复现——确认后可直接关闭 | [档案](MLVR_develop/2026-08/20260824_05_f02-adjoint-physics-verification/README.md) |
| 6 | MG WW 输入契约加固 | 修复已实施并经独立复核（“Repair is correct with explicit limitations”）：群内 `WWE:N` 边界无唯一物理含义；复核建议要求群对齐边界或在解析期转 group→bin 表，并补 deterministic bin-selection 测试——是否立项由你决定 | [修复](MLVR_develop/2026-09/20260923_01_f04c-mg-native-ww-energy-contract/README.md)、[复核](MLVR_develop/2026-09/20260923_02_independent-mg-ww-repair-review/README.md) |

## 3. 最近完成

| 日期 | 任务 | 结果 |
|---|---|---|
| 09-23 | f04c-mg-native-ww-energy-contract | 修复 MG native `WWE:N` 坐标契约：用户输入保持物理 MeV，MG 查窗转换为群中心物理能量；forward/adjoint bin oracle、native WW 6/6 与 energy-dependent 深穿透 5×1M 通过（$z=0.29571$、FOM 9.27935×）；RMC 本地 commit `5cfb0f77`（未 push） |
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

1. **启动 Stage 3/4 接口设计**：F03 外部 response→source 冻结子域、F04 伴随+native WWMESH C—Verify 子域与 F08 native WW 主路径已具备；是否现在立项「双向迭代 WW 框架接口设计」。
2. **F04 按需扩展**：仅当首版实际问题需要 MPI/OpenMP、耦合粒子或非单 mesh 时，另立任务扩展验证；不做无限矩阵。
3. **收尾治理**：关闭台账遗留项 `20260824_05`；知识库 W10 与变更记录已同步。

## 5. 维护方式（Agent 必读）

- 新建任务、状态变化、Stage 推进时回写本页第 1–3 节；**归档（第 ⑤ 步）必须同步本页**。
- 本页只放**看板信息**（阶段 / 待拍板 / 最近完成 / 下一步），细节一律写进任务档案；**保持一屏以内**。
- 多个 Agent 可能并行工作：本页与 `INDEX.md` 是共享文件，动手前先看 `git status`，不要把别人的未提交内容一起提交。
