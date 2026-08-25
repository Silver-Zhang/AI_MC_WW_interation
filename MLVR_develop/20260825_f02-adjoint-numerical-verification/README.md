# f02-adjoint-numerical-verification

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-25 |
| 状态 | 已完成（第一阶段验证归档） |
| 任务类型 | 算法实验 / 现有能力验证 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F02 / W5 / W6 / W7 |
| 涉及文件 | `RMC/tests/fixed_source_adjoint/`（只读）、任务目录下独立输入/脚本/日志 |
| 分支 / 提交 | `Neural_Network_WW_Iteration` / `4d3e1aac60f1c40062f05e5d532afb6c7eb6fb4b`；RMC 未切分支、未提交 |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：对 RMC standard MGACE、fixed-source neutron adjoint 的现状实施 Stage 2 L4 数值验证；分别取得回归可运行性、W5 缺陷数值复现、受限子域前向—伴随互易性，以及 W6 双 nubar 部署数据功效和动态覆盖边界的独立证据。

**范围**：

- RMC 基线：`Neural_Network_WW_Iteration`，预期 SHA `4d3e1aac60f1c40062f05e5d532afb6c7eb6fb4b`，standard ACE，`ais=OFF`；运行前重新核实。
- 第一阶段顺序：V0 现有回归 → V2 W5 密度复现 → V4 非对称散射互易性 → V3 W6 双 nubar 路径与功效分析。
- 只使用现有部署核库；若 V4 无合适的解析可控核，或 V3 统计功效不足，停止并提交专用 MGACE 核第二阶段方案。
- 不包含 W5/W6 修复、F03、WW、AIS/HDF5、continuous-energy、MPI/OpenMP 一致性和 Windows 验证。
- 所有研究性输入、解析脚本和结果均置于本任务目录或服务器独立任务目录；不修改 `RMC/` 下任何文件。

**验收标准**：

1. V0 保存构建/运行命令、环境、退出码、stdout/stderr 和既有 reference 的只读比较；通过仅表示 smoke pass。
2. V2 用 $r=0.5,1,2$ 独立输入和 PTRAC/等价事件证据检验首碰撞权重相对倍率 $2,1,0.5$；不得修改原回归输入或 reference。
3. V4 至少筛选并验证两个非对称群对；对前向/伴随配对报告 $R_F,R_A,\sigma_F,\sigma_A$ 和
	$$z=\frac{R_F-R_A}{\sqrt{\sigma_F^2+\sigma_A^2}},$$
	预注册判据为 $|z|\le3$；若现有核库无法形成有区分力的案例，明确记录阻塞证据而非伪造通过。
4. V3 证明双 nubar 路径可达，给出当前部署数据下的检验功效/样本量；可行时运行群频数检验，不可行时形成第二阶段专用核提案。
5. 记录所有随机种子、输入哈希、核数据哈希、依赖/工具链和真实输出；结构性失败条件包括崩溃、NaN/Inf、群越界、$|\mu|>1$ 和异常 bank 行为。
6. 最终确认 RMC 工作树和既有 reference 未被修改；完整能力在 W5/W6 未修复前保持 E。

**原始材料**：当前没有外部报错文件；用户要求为“先验证，再修复”，并于 2026-08-25 明确发出 “Start implementation”。脱敏决策与范围已写入本档案，不保存原始聊天转储。后续 `logs/` 保存命令输出、环境清单、输入副本、摘要 CSV/JSON 和关键小型原始结果。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：F02-B 静态审查确认完整能力为 E — Defect，受限子域（局部密度比 $r=1$ 且 `NNUBAR<=1`）为 C — Verify。W5 为局部密度下伴随碰撞权重多出 $1/r$；W6 为双 nubar 时初始化和运行时裂变群抽样混用不同数据块。既有 `fixed_source_adjoint` 只覆盖 H/O 非裂变 30 群场景，旧 reference 一致不能证明数学伴随性。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `MLVR_develop/20260824_f02-adjoint-physics-verification/README.md` D.3 | W5 的局部密度数据流与 $1/r$ 后果已由静态证据闭合。 |
| 2 | 同上 F.3 / A.4 | W6 在已登记 `c5g7td` 双 nubar 表上可达，两个核的累计裂变产生量不一致。 |
| 3 | `RMC/tests/fixed_source_adjoint/inp` | V0/V2 可复用的现有 30 群 H/O 非裂变基础输入；只读。 |
| 4 | `RMC/tests/ptrac_grp/inp`、`RMC/src/ParticleTrack.cpp` | PTRAC 具有群号、方向和权重输出能力；实际是否足够区分 bank child 需运行确认。 |
| 5 | `RMC/src/ReadCellCard.cpp` | cell `DENS` 能构造 $r=0.5,1,2$。 |
| 6 | `RMC/src/ReadFixedSourceBlock.cpp` | `PARTICLE FISSION=1 0` 可启用 fixed-source 中子裂变。 |

**影响面**：本任务不改生产代码和接口；结果将影响 F02 完整能力/受限子域的证据等级，并为后续 W5/W6 独立修复任务提供失败基线。既有 benchmark/reference 只读，禁止更新。

**为什么之前没做/没发现**：现有回归着重“可运行且输出稳定”，没有非单位局部密度、双 nubar 群频数或非对称源—响应前向/伴随双线性测试，因此不能暴露 W5/W6，也不能证实完整互易性。

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A：现状优先、分阶段 | 先用现有核库执行 V0/V2/V4/V3；只有证据表明核库或统计功效不足时再提交专用核方案。 | 第一阶段可能无法闭合 V4/V3 的强判别测试，但不会把核格式或额外改动混入验证。 | ★推荐/已采纳 |
| B：直接制作专用 MGACE 核 | 立即构造非对称 2–3 群散射核和放大双 nubar 核。 | 核格式、oracle 与部署路径本身需要额外审查，且超出当前第一阶段授权。 | 第二阶段候选 |
| C：只跑旧回归 | 仅执行 V0 并比较旧 reference。 | 成本低，但只能证明不崩溃，不能验证 W5/W6 或互易性。 | 不采纳 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A（现状优先、分阶段）；执行顺序 V0 → V2 → V4 → V3。
- **决定人 / 日期**：用户，2026-08-25（“先验证，再修复”；“专用核分两阶段决定”；“Start implementation”）。
- **理由与约束**：先建立当前缺陷的数值失败基线，再在后续独立任务修复；第一阶段只使用现有核库。不修改 RMC，不更新任何 reference/benchmark，不修复 W5/W6，不进入 F03。若 PTRAC 能力不足或需要 instrumentation，停止并提交最小诊断补丁方案，不能擅改源码。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 建立独立验证档案 | `MLVR_develop/new_task.sh f02-adjoint-numerical-verification F02` | 成功；任务状态进入实施中。 |
| 2 | 冻结构建、源码和核库基线 | `logs/environment.txt` | RMC 3.5.0，SHA `4d3e1...`；Release，AIS/MPI/OpenMP off，test on。 |
| 3 | 隔离构建并执行 V0 | `/tmp/mlvr_f02_rmc_build`；`ctest -R '^test_fixed_source_adjoint$' -V` | 1/1 passed；重建结果与 reference 字节一致。 |
| 4 | 构造 V2 三种局部密度输入并解析原生 source trace | `cases/v2_w5_density/` | 三组退出 0；显式固定 RNG 后二次运行的 source 哈希逐字节相同；W5 的 $1/r$ 缺陷数值复现。 |
| 5 | 按 RMC NXS/JXS/XSS 索引只读解析部署 MGACE | `cases/v4_reciprocity/screen_mgace_pairs.py` | H2O 筛得 359 个非对称群对候选。 |
| 6 | 生成、运行并分析 V4 | 两群对 × 五种子 × forward/adjoint | 20/20 退出 0；合并及逐种子均满足 $|z|\le3$。 |
| 7 | V3 双 nubar 核与功效分析 | `cases/v3_double_nubar/analyze_double_nubar.py` | 核差异重现；80% 近似功效需约 $7.33\times10^7$ 个已观测裂变子代。 |
| 8 | V3 动态可达性尝试 | `cases/v3_double_nubar/reachability/` | 双 nubar 伴随材料初始化已执行；随后 neutron-only 光子群定位访问空数组而 SIGSEGV，登记 W7；运行时裂变群抽样未覆盖。 |

**代码改动**：见 [changes.diff](changes.diff)，摘要：
- 无 RMC 代码改动；任务目录内只新增验证档案、独立输入/脚本和日志。

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
| V0 既有回归 | `ctest --test-dir /tmp/mlvr_f02_rmc_build -R '^test_fixed_source_adjoint$' -V` | 退出 0，1/1 passed；重建结果与 reference SHA256 均为 `750be025...43faa`，raw diff 为空。 |
| V2 W5 密度复现 | 三个目录分别运行 RMC，再执行 `analyze_source_trace.py` | 三组退出 0；RNG type 2、seed 1、stride 1,000,000；重复运行 source 哈希 diff 退出 0；首碰撞后权重相对倍率符合 $1/r$，最大相对误差 $2.9894\times10^{-5}$。 |
| V4 互易性 | 20 个 RMC 运行，再执行 `analyze_reciprocity.py` | 20/20 退出 0；两群对合并 $z=-0.258679,0.0829025$，全部逐种子 $|z|<1$。 |
| V3 功效 | `analyze_double_nubar.py --zaid 10001.01m` | 退出 0；$S_1=0.71975438087957$、$S_2=0.71977667464764$，80% 功效近似样本量 73,289,470 个子代。 |
| V3 动态尝试 | `/tmp/mlvr_f02_rmc_build/bin/RMC inp` | 退出 11；`LocateMgErgGrp()` 中 SIGSEGV，0 条 source state；不能作为 W6 频数检验。 |
| 最终分析复验 | `py_compile` 后重跑 V2/V3/V4 分析 | 脚本语法检查退出 0；V2 与 V4 判据再次通过，V3 样本量再次得到 73,289,470。 |
| 最终完整性 | `git -C RMC status/diff` + reference SHA256 | 分支/SHA 未变，RMC status 空，`changes.diff` 为 0 byte，reference SHA256 与立项值相同。 |

```
V0:
1/1 Test #62: test_fixed_source_adjoint ........ Passed 0.70 sec
100% tests passed, 0 tests failed out of 1

V2:
r0.5 mean_weight=1.3381 relative_to_r1=2.0000597881
r1   mean_weight=0.66903 relative_to_r1=1.0
r2   mean_weight=0.33452 relative_to_r1=0.5000074735
criterion: max relative error <= 5.0e-04; pass=True

V4 combined:
g14_to_g15 R_F=0.4372696694 sigma_F=0.0009925827 R_A=0.4376056804 sigma_A=0.0008378861 z=-0.2586787
g20_to_g22 R_F=0.4594500249 sigma_F=0.0008047237 R_A=0.4593570930 sigma_A=0.0007803925 z=0.0829025
criterion=all combined |z| <= 3; pass=True

V3 dynamic:
exit_code=11
source_records=0
Signal (No. 11) caught, processing...
stack: CDAceData::LocateMgErgGrp -> CDFixedSource::InitiateAll -> CalcFixedSource
```

**实验设置（RMC 数值验证）**：
- 随机种子 / RNG：V2 使用 RNG type 2、seed 1、stride `1,000,000`，128 粒子，冻结后重复运行三个 `.source` 哈希均相同；V4 使用 RNG type 2、种子 `1,3,5,7,9`、同一 stride，每次 200,000 粒子；V3 动态尝试使用 seed 1、同一 stride。
- V4 几何与群对：5 cm 均匀 H2O 球，群 14→15（$0.4015\to0.2435$ MeV）和群 20→22（$0.0022925\to0.0003105$ MeV）；同一 cell 体源/track-length flux 响应互换群。
- 输入配置：保存每个 RMC 输入卡原文及 SHA256；V4 manifest SHA256 为 `9785dabde2e3318d7fa5f5b3678a0d5020e0748f03336784a30b17e9a6c90f3d`；V3 动态输入为 `ecc35caf3f52ec38d5f9c393afef379e65644ad97a2e5224abe18fdd0fa08106`。
- 运行依赖：CMake 3.28.3、G++ 13.3.0、RMC 可执行文件 SHA256 `55a820e6...c62f9`；`xsdir`、`mgxsnp`、`c5g7td` SHA256 分别为 `970e85ad...9f62b`、`1d26fac6...7001`、`cc6951ed...0ed4c`；完整值见 `logs/environment.txt`。
- Python 边界：不需要独立 Python 环境；只允许系统 Python 运行仓库既有测试驱动或做可复核的文本/统计汇总，物理验证主体是 RMC 输入卡、原生 tally/PTRAC 与源码证据。
- 基准对比：V0 只读比较既有 reference；V2 对照解析 $1/r$；V4 对照前向—伴随配对响应；V3 对照两组 nubar 理论分布。

**已解释告警**：V0/V2/V4 的 adjoint 运行出现 `particle energy larger than maximum energy group upper bound`。源码表明 neutron-only 模式仍无条件转换 photon 上限；30+12 群 H/O 案例只产生告警。V3 的 neutron-only c5g7td 没有 photon 群数组，同一路径升级为 W7 SIGSEGV。

**未覆盖到的验证**：

- W6 运行时伴随裂变群频数、权重和 bank 子代统计；被 W7 启动崩溃、PTRAC bank 事件的存库前状态语义以及约 $7.33\times10^7$ 有效子代样本需求共同阻塞。
- 混合材料碰撞估计器、可裂变互易性、强各向异性方向核、负余弦疑点、显式 delayed precursor/family。
- AIS/HDF5、continuous-energy、MPI/OpenMP、Windows、GPU/服务器大规模验证。
- V4 之外的一般几何、边界条件、源/响应和多核素混合物。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：完整 standard MGACE fixed-source neutron adjoint 能力仍为 **E — Defect**。V0 smoke 通过；W5 的 $1/r$ 偏差已数值确认；V4 证明本次 $r=1$、`NNUBAR=0`、P0 H2O 均匀球代表子域的两个强非对称群对满足互易性，但不能外推到完整能力；W6 部署核差异与静态运行时分支仍成立，动态群频数未覆盖；另发现 W7 neutron-only MGACE 伴随初始化可因无条件光子群定位而崩溃。
- **遗留问题 / 后续待办**：W5、W6、W7 分别进入 Stage 3 独立任务并重新由用户拍板。W6 第二阶段应先明确 nubar 表语义/oracle，再决定最小 instrumentation 或专用非生产核；不得擅自修改生产核。
- **知识库同步**：更新 `02_RMC功能审查矩阵.md` 的 F02 L4 证据、`06_已知问题与改进建议.md` 的 W5/W6 状态并新增 W7、`AGENT_CONTEXT.md` 的当前阶段，以及任务台账。
- **是否已提交**：未对 RMC commit/push/切分支；未更新 reference/benchmark。工作区档案由用户决定何时提交。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-25 02:30 | 立项 |
| 2026-08-25 | 用户授权按方案 A 开始第一阶段实施，状态转为实施中。 |
| 2026-08-25 | V0 1/1 passed；V2 数值确认 W5。 |
| 2026-08-25 | V4 筛选 359 个群对，完成 20 个运行并通过预注册判据。 |
| 2026-08-25 | V3 完成功效分析；动态输入在 photon 群定位处 SIGSEGV，新增 W7 并归档第一阶段。 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 冻结设计与决策 | 本 README 第 1–4 节 | 记录 V0/V2/V4/V3、统计判据及不改 RMC/不更新 reference 边界。 |
| 3 | V0 | 隔离 Release 构建、CTest、原始结果重建 | 1/1 passed；reference 未改变。 |
| 4 | V2 | 三种 `DENS` + 显式固定 RNG + native source trace | 两次运行 source 哈希逐字节相同；W5 按 $1/r$ 缩放，数值确认。 |
| 5 | V4 | 核库解析、生成 20 输入、配对统计 | 两群对合并与逐种子均通过 $|z|\le3$。 |
| 6 | V3 | c5g7td 核解析、功效分析、最小动态输入 | 双核差异重现；动态被 W7 阻断，未伪报通过。 |
| 7 | 误判修正 | 解析脚本和输入 | V4 修正 `DATAPATH`/xsdir 字段和批量目录深度；V3 修正 Python JXS 索引错位和 RNG block 位置。首次错误 RNG block 的原始失败输出曾被后续运行覆盖，仅在本档案如实记录；最终 SIGSEGV 原始输出和栈证据已完整保留。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
