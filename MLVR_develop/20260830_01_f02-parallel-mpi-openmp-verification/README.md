# f02-parallel-mpi-openmp-verification

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-30 |
| 状态 | 已完成（条件性并行运行证据） |
| 任务类型 | 算法实验 / 并行正确性验证 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F02 |
| 涉及文件 | 仅任务侧构建、运行器、原始证据与文档；`RMC/` 源码只读 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `b26a81a2...`；不改源码、不更新 reference/benchmark |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：验证 standard ASCII MGACE `FIXEDSOURCE` neutron adjoint 在 MPI 多 rank 与 MPI+OpenMP 混合并行下的运行可靠性、前向—伴随统计相容性及并行配置间统计相容性，消除双向迭代框架进入并行运行前的 F02 并行证据缺口。

**范围**：仅 Linux x86_64、本机 Open MPI、RMC 多群 fixed-source neutron adjoint；复用已冻结的条件角、density mesh 和裂变/银行资产。覆盖 MPI 1/2/4 ranks 和 MPI+OpenMP `1×2`、`2×2`、`2×4`（rank × threads）。不修改 `RMC/` 源码、核数据、reference/benchmark；不把结论外推到 CE、AIS/HDF5 核数据、photon/耦合粒子、delayed、GPT、反射边界、Windows 或任意机制组合。

**验收标准**：每个配置均由 banner 证明实际 MPI/OMP 设置；所有运行退出 0、无 NaN/signal/deadlock；逐 seed 的前向—伴随互易性与已冻结 strict gates 通过；同一统计量的串行—并行差异满足预注册的 $|z|\le3$；至少一个有裂变银行产生的案例在各配置下通过；MPI 与 MPI+OMP 构建各自的 `test_fixed_source_adjoint` CTest 通过；保留 raw reports、命令、配置、binary/source hash 与 checksum。

**原始材料**：后续 `logs/` 保存 configure/build/banner、每个配置的输入/stdout/stderr/exit code、raw/strict reports、CTest、hash manifest 和失败产物；本次设计依据为 `RMC/CMakeLists.txt`、`src/CalcFixedSource.cpp`、`tests/execute.py` 与已完成的 MPI-off task 01。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：F02 已在显式 MPI-off、OpenMP-off 的冻结范围取得 A — Ready（有界），但并行范围明确未覆盖。RMC 支持 MPI 和 MPI+OpenMP 构建，OpenMP-only 被 CMake 禁止。固定源主循环具有 MPI 历史分配、全局进度和负载均衡归约路径；伴随粒子仍复用该 fixed-source 主循环，因此必须用统计而非逐位 RNG 相同来检验。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `RMC/CMakeLists.txt:157-211` | `-Dmpi=ON` 定义 `USE_MPI`；`-Dopenmp=ON` 定义 `USE_OMP`；OpenMP 需要 MPI。 |
| 2 | `RMC/src/CalcFixedSource.cpp:13-58,111-157` | fixed-source 使用 MPI 非阻塞全局归约和每 rank 历史分配；伴随模式进入同一固定源循环。 |
| 3 | `RMC/src/OutputHeading.cpp:38-57` | runtime banner 输出 MPI process 数及 OMP thread 数，可作为实际配置证据。 |
| 4 | `RMC/tests/execute.py:112-155` | 回归运行器支持 `mpiexec -n` 与 `RMC -s <threads>`。 |
| 5 | `RMC/tests/CMakeLists.txt:34-50,117` | fixed-source adjoint CTest 存在；多线程条件下有部分测试排除，故需专项验证。 |
| 6 | `20260828_01_f02-mpi-off-serial-provenance` | 串行已闭合 40 条 angular、10 条 density、strict gates、CTest 与 checksum，可作为统计基线与资产来源。 |
| 7 | 本机环境 | `mpiexec` 为 Open MPI 4.1.6，`mpicxx` 可用，逻辑 CPU 为 32，可执行预定的最大 `2×4` 矩阵。 |

**影响面**：只影响 F02 并行范围的分类证据与未来双向迭代的并行准入；不改变输入格式、程序行为或基准结果。重点风险是 MPI tally/银行归约、随机数流按 rank/thread 的切分及 mixed-mode 共享状态；验证不要求逐历史可复现，而要求预注册统计门槛成立。

**为什么之前没做/没发现**：（可选，但对改进机制很有价值）

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A：分层全矩阵专项验证 | 新建 MPI-only 与 MPI+OMP fresh builds；先在 1×1、2×1、4×1 和 1×2、2×2、2×4 上跑 CTest、banner、smoke；再对每配置跑 angular 40、density 10 和裂变银行案例，逐 seed/aggregate 及跨配置统计检查。 | 计算量大，但直接覆盖双向迭代所需 MPI 与混合并行路径。 | ★推荐 |
| B：缩减矩阵 | 仅 2 ranks 与 2×2 跑代表性案例。 | 成本较低，但不能排除规模/配置相关问题，不能将 MPI/OMP 范围升为 A。 | 不推荐 |
| C（维持现状） | 保持 MPI/OpenMP 为 C — Verify。 | 无成本，但不能作为并行双向迭代的物理输运依据。 | 不采用 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A — 分层全矩阵专项验证。
- **决定人 / 日期**：用户 / 2026-08-30。
- **理由与约束**：保持 RMC 源码、核数据与 reference/benchmark 不变；正式运行使用冻结 seeds `17,23,41,59,83`、RNG type 2/stride `1000000`、50,000 histories/run。任何失败、死锁、统计门槛失败或非零退出均原样保留，不以更换 seed 掩盖。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh f02-parallel-mpi-openmp-verification F02` | 已建立档案。 |
| 2 | 只读定位并行构建与 fixed-source 主循环 | CMake、`CalcFixedSource.cpp`、`OutputHeading.cpp`、tests | 识别 MPI 归约/历史分配、OMP 构建约束、banner 证据和可复用 CTest。 |
| 3 | fresh MPI-only 与 MPI+OpenMP 构建 | `/tmp/mlvr_f02_mpi_build`、`/tmp/mlvr_f02_mpi_omp_build` | 均绑定 RMC `b26a81a2...`；SHA256 分别为 `60ecf80d...3fe`、`40e7818a...74db`。 |
| 4 | 六配置 banner/smoke | `logs/banner_smoke/` | `1×1`、`2×1`、`4×1` 为 MPI ON/OMP OFF；`1×2`、`2×2`、`2×4` 的 MPI/OMP banner 均与实际配置一致，且有效固定源伴随输入均 exit 0、Finish 1。 |
| 5 | density formal | `logs/density_formal/*_retry1/` | 每配置 10/10 个 50,000-history 运行通过结构门禁及逐 seed/aggregate 互易性；均相对 MPI-off 基线逐 seed $|z|=0$。 |
| 6 | angular formal transport | `logs/angular_formal/*_retry1/` | 每配置 40/40 个 50,000-history 前/伴随输运通过结构门禁。未在多 rank 下重复 GDB 返回值分布探针。 |
| 7 | fissile formal | `logs/fissile_formal/` | 每配置 10/10 个裂变主导 `g6↔g1` 运行通过结构与互易性；例如 `2×1` 合并 $z=-0.432283$、最大单对 $|z|=1.481133$。 |
| 8 | 回归、完整性与独立审计 | `logs/parallel_ctest.txt`、`SHA256SUMS.txt`、`independent_audit.txt` | MPI 与 MPI+OMP 的 fixed-source adjoint CTest 各 1/1 通过；扩展 checksum 清单通过；独立审计为 CONDITIONAL。 |

**代码改动**：见 [changes.diff](changes.diff)，摘要：
- `RMC/` 无改动；任务侧新增并行运行器与跨配置检查器，用于保留命令、banner、输出、退出码和统计报告。

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
| MPI-only 构建 + CTest | `-Dmpi=ON -Dopenmp=OFF`；`RMC_MPI_TEST=2 ctest ... -R '^test_fixed_source_adjoint$'` | 1/1 passed，0.98 s。 |
| MPI+OpenMP 构建 + CTest | `-Dmpi=ON -Dopenmp=ON`；`RMC_MPI_TEST=2 RMC_OMP_TEST=2 ctest ... -R '^test_fixed_source_adjoint$'` | 1/1 passed，1.00 s。 |
| 六配置运行时证据 | `logs/banner_smoke/*/stdout_ctest_input.log` | 全部 banner 显示预期 MPI rank；混合配置显示预期 OMP threads；六组均 exit 0、Finish 1。 |
| density 正式矩阵 | 六配置 × 10 runs，50,000 histories/run | 60/60 structural pass；每配置逐 seed/aggregate reciprocity passed；相对 MPI-off 基线逐 seed $|z|=0$。 |
| angular 正式输运矩阵 | 六配置 × 40 runs，50,000 histories/run | 240/240 structural pass；此项仅证明并行输运结构完整，不构成并行 `MuLab` 分布验证。 |
| fissile 正式矩阵 | 六配置 × 10 runs，50,000 histories/run | 60/60 execution/runtime-config pass；每配置 5 对及合并互易性均 $|z|\le3$，0 个分析异常。 |
| 完整性 | `sha256sum -c logs/SHA256SUMS.txt` | 两 binary、脚本、六组正式 raw/strict/summary、CTest 和审计材料均 OK。 |

```
独立审计结论为 **CONDITIONAL**：六配置的并行运行、density/fissile 响应统计及 angular 输运结构门禁通过；但没有在多 rank 下重复 angular GDB/PTRAC 分布探针，故不得声称并行 angular 支持域、矩或离散频数已完成验证。
```

**实验设置（算法实验必填）**：
- 随机种子：计划 `17,23,41,59,83`
- 配置快照：RMC `FIXEDSOURCE + ADJOINT ADJOINTCALCULATION=1`；standard ASCII MGACE；`ais=OFF`
- 依赖版本：Open MPI 4.1.6、g++ 13.3.0、CMake 3.28.3、32 logical CPU
- 基准对比：MPI-off strict serial formal；按 $|z|\le3$ 比较同一响应及跨配置统计量

**未覆盖到的验证**：并行 multi-rank `MuLab` 分布探针、超过 4 ranks 或 4 threads/rank、跨节点、异构 MPI、Windows、完整 photon/耦合粒子、CE、AIS/HDF5 核数据、delayed、GPT、反射边界或任意机制组合。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：六个指定配置的运行时配置、fixed-source regression、density formal 互易性/串行相容性、裂变主导响应互易性及 angular 全输运结构门禁均通过。独立审计为 **CONDITIONAL**：并行 angular 物理分布探针尚未完成，因此不将 MPI/OpenMP 作用域提升为 F02-B 的 A — Ready。
- **遗留问题 / 后续待办**：如双向迭代依赖并行条件角采样的分布级结论，应另立任务实现可审计的 rank-aware `MuLab` 观测，再验证支持域、矩和离散频数。
- **知识库同步**：已同步“有限运行/响应级正证据，分布级并行 angular 未验证”的边界；F02-B 的 A 仍严格限 MPI-off serial。
- **是否已提交**：未提交；RMC 未修改。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-30 11:26 | 立项 |
| 2026-08-30 | 用户批准方案 A；完成两套 fresh build、六配置 smoke、density/angular/fissile formal、CTest 与独立审计。 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 读取串行 F02 证据边界 | `20260828_01.../README.md` | 确认 MPI/OpenMP 未覆盖，不得复用 serial A。 |
| 3 | 读取并行构建规则 | `RMC/CMakeLists.txt:157-211` | MPI 可构建；OpenMP 必须与 MPI 同时构建。 |
| 4 | 定位 fixed-source MPI 路径 | `RMC/src/CalcFixedSource.cpp` | 确认固定源主循环的 MPI 历史分配、进度和非阻塞负载均衡归约。 |
| 5 | 定位 banner 与测试运行器 | `OutputHeading.cpp`、`tests/execute.py` | banner 可证明实际 rank/thread；运行器可传递 `mpiexec -n` 和 `-s`。 |
| 6 | 检查本机资源 | `mpiexec --version`、`mpicxx --version`、`getconf` | Open MPI 4.1.6、g++ 13.3.0、32 logical CPU 可用。 |
| 7 | 两套 fresh build + CTest | `/tmp/mlvr_f02_mpi_build`、`/tmp/mlvr_f02_mpi_omp_build` | MPI 与 MPI+OMP `test_fixed_source_adjoint` 各 1/1 passed。 |
| 8 | 六配置 smoke | `logs/banner_smoke/` | 先使用不含核素的 banner probe，随后改用既有 CTest 输入；后者六组均 exit 0、Finish 1。 |
| 9 | density 首次尝试 | `logs/density_formal/mpi_1x1/` | 旧默认核库不含私有 `10006.93m`，MPI_ABORT 16；完整失败输出保留，未作为正式结果。 |
| 10 | density 正式重跑 | `logs/density_formal/*_retry1/` | 改用已资格化私有索引，六配置 60/60 structural pass、strict reciprocity passed。 |
| 11 | angular 首次尝试 | `logs/angular_formal/mpi_1x1/` | 一群旧资产与两群输入不匹配，`10006.93m` 缺失；失败输出保留。 |
| 12 | angular 正式重跑 | `logs/angular_formal/*_retry1/` | 使用既资格化的两群资产；六配置 240/240 transport structural pass。 |
| 13 | fissile formal + cross-config | `logs/fissile_formal/`、`density_cross_configuration.json` | 六配置裂变 60/60 通过；density 相对 MPI-off 基线逐 seed $|z|=0$。 |
| 14 | 独立审计与封存 | `logs/independent_audit.txt`、`SHA256SUMS.txt` | 审计为 CONDITIONAL；补齐二进制、正式报告、脚本、CTest 与审计材料的 checksum 清单。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
