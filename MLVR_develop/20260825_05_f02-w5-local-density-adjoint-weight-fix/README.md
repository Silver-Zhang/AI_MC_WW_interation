# f02-w5-local-density-adjoint-weight-fix

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-25 |
| 状态 | 已完成 |
| 任务类型 | 缺陷修复 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | W5 |
| 涉及文件 | `RMC/src/GetExitState.cpp`、`RMC/src/SampleColliType.cpp`；W5 验证输入、知识库与物理导读 |
| 分支 / 提交 | `Neural_Network_WW_Iteration` / `4d3e1aac60f1c40062f05e5d532afb6c7eb6fb4b`（修复前基线） |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：修复 standard MGACE fixed-source neutron adjoint 在非单位 cell/密度网格比例 $r$ 下，散射与裂变碰撞权重相对正确产生量/总截面比多出 $1/r$ 的 W5 缺陷，使同一材料组成下的共同局部密度缩放在该权重比中正确抵消。

**范围**：只修正 MGACE 伴随散射和伴随裂变的权重归一化密度；复用现有 `CDMaterial::GetMatAtomDen(material, density_ratio)`，不修改输入卡、核数据格式、能群/角分布、正向输运、W6、reference 或 benchmark。同步 W5 任务档案、知识库和面向物理读者的导读。

**验收标准**：

1. 修复前 V2 的 $r=0.5,1,2$ 固定种子输入继续全部退出 0；首碰撞后平均权重相对 $r=1$ 从约 $2:1:0.5$ 变为 $1:1:1$，每组相对偏差不超过 $5\times10^{-4}$。
2. 散射与裂变两个伴随权重调用点都使用当前位置的局部总原子密度；$r=1$ 时公式与修复前完全等价。
3. RMC 增量编译通过；既有 `test_fixed_source_adjoint` 1/1 通过，reference SHA256 保持 `750be0255b972f0d4aa25dbd2a0c864e17b5b04058be4749109cb10290443faa`。
4. 不破坏已修复的 W7 neutron-only `c5g7td` 可达性；原输入仍退出 0。
5. `git diff --check` 通过，RMC 改动仅包含已存在的 W7 `InitiateAll.cpp` 和本任务批准的 W5 文件；生成仅含 W5 增量的 `changes.diff`。

**原始材料**：修复前数值证据原样保存在 `../20260825_01_f02-adjoint-numerical-verification/cases/v2_w5_density/` 及该任务 `logs/v2_evidence.txt`；关键结果为 $r=0.5,1,2$ 的首碰撞后平均权重 `1.3381, 0.66903, 0.33452`。本任务不改写历史证据，实施时把重放输入、修复后原生 `.source`、退出码和分析结果保存到本任务目录。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：材料基准总原子密度记为 $N_0$，当前位置 cell 覆盖或密度网格给出的比例为 $r$。自由飞行宏观总截面已经按各核素局部密度 $N_i r$ 计算，故 $\Sigma_t^{macro}=N_0r\,\bar\sigma_t$。伴随累计产生截面按材料原子份额形成微观平均量 $\bar\sigma_{prod}^\dagger$，本身不含 $N_0r$。

当前散射和裂变权重均以基准密度 $N_0$ 归一化宏观总截面：

$$
w'_{old}=w\frac{\bar\sigma_{prod}^\dagger}{\Sigma_t^{macro}/N_0}
=\frac{1}{r}w\frac{\bar\sigma_{prod}^\dagger}{\bar\sigma_t}.
$$

现有 `GetMatAtomDen(m, r)` 返回 $N_0r$。若权重分母使用该局部总原子密度，则

$$
w'_{fixed}=w\frac{\bar\sigma_{prod}^\dagger}{\Sigma_t^{macro}/(N_0r)}
=w\frac{\bar\sigma_{prod}^\dagger}{\bar\sigma_t},
$$

共同密度因子正确抵消，同时保留密度对平均自由程和碰撞位置的物理影响。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `RMC/src/SampleFreeFlyDist.cpp:65-83` | `CalcMacroXS()` 用 `GetMatNucAtomDen(..., p_dDensRatio)` 形成含 $r$ 的宏观总截面。 |
| 2 | `RMC/src/MaterialFunctions.cpp:79-91`、`Material.h:493-514` | 现有双参数 `GetMatAtomDen(m, r)` 明确定义为局部总原子密度 $N_0r$。 |
| 3 | `RMC/src/GetExitState.cpp:186-189` | 伴随散射权重当前直接读取未缩放成员 `p_dMatAtomDen`。 |
| 4 | `RMC/src/SampleColliType.cpp:187-192` | 伴随裂变权重使用同一未缩放分母。 |
| 5 | `RMC/src/GetLocationInfo.cpp:59-82` | `p_dDensRatio` 来源覆盖 cell 预计算密度比例和位置相关密度网格。 |
| 6 | `20260825_01_f02-adjoint-numerical-verification` V2 | 固定 RNG、128 粒子原生 source trace 得到约 $2:1:0.5$，相对 $1/r$ 最大误差 $2.9894\times10^{-5}$。 |

**局部假设与反证检查**：若 W5 仅由权重分母遗漏当前位置比例造成，则两个调用点改用 `GetMatAtomDen(p_nMAT, p_dDensRatio)` 后，原 V2 三组首碰撞后平均权重应在 $5\times10^{-4}$ 内相等；若仍保持 $1/r$、出现新的密度趋势或 $r=1$ 回归改变，则假设被否定并停止扩大修改。

**影响面**：仅 `p_bIsAdjointParticle && p_bIsMultiGroup` 下的 neutron 散射/裂变权重。密度仍影响宏观总截面、自由程、碰撞位置和 tally；只移除碰撞后权重中的人工 $1/r$。正向 MG/CE 路径、材料数据结构和公开接口不变。当前 RMC 工作树已有独立 W7 的 `src/InitiateAll.cpp` 改动，本任务不得覆盖或归因该改动。

**为什么之前没做/没发现**：既有伴随回归使用 $r=1$，此时基准密度与局部密度相同，错误因子退化为 1；只有显式比较相同材料组成的多种局部密度才会暴露。

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A：两处使用局部密度 getter | 在散射、裂变权重分母中把基准成员替换为 `cMaterial.GetMatAtomDen(p_nMAT, p_dDensRatio)`。 | 两行语义修复；复用现有接口，$r=1$ 等价，影响最窄。 | ★推荐 |
| B：伴随产生量改存宏观量 | 在 `CalcMacroXS()` 中把伴随累计产生截面乘局部总密度，权重改为宏观产生量/宏观总截面。 | 量纲直观，但改变共享状态字段语义和所有读取者，回归面更大。 | 不推荐 |
| C：新增公共权重 helper | 抽取函数统一散射/裂变公式，并在 helper 内使用局部密度。 | 可消除两处重复，但为两行修复新增抽象和接口，超出最小范围。 | 可选 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A，两处伴随权重分母使用现有局部总原子密度 getter。
- **决定人 / 日期**：用户授权、GitHub Copilot 代选，2026-08-25。用户本轮明确要求“完成 W5 的修复以及相关文档的补充和撰写”；方案选择询问返回“用户暂不可响应，请自主工作并作出合理决定”，据此采用已论证的推荐方案 A。
- **理由与约束**：方案 A 直接恢复共同密度因子抵消，复用已有接口且 $r=1$ 严格等价，影响面最小。不更新 reference/benchmark，不修改 W6，不 commit/push/切分支；保留当前独立 W7 改动。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 冻结用户决策 | 第 4 节 | 采用方案 A；不修改 W6/reference/benchmark。 |
| 2 | 修正伴随散射权重 | `RMC/src/GetExitState.cpp` | 分母改用当前位置总原子密度 `GetMatAtomDen(mat, ratio)`。 |
| 3 | 修正伴随裂变权重 | `RMC/src/SampleColliType.cpp` | 使用同一局部密度归一化，散射/裂变公式一致。 |
| 4 | 增量编译 | `/tmp/mlvr_f02_rmc_build` | `[100%] Built target RMC`。 |
| 5 | 重放 V2 三种密度 | `cases/v2_density_invariance/` | 三组退出 0；128 个首碰撞状态；权重相对比 $1:1:1$。 |
| 6 | 回归与兼容性 | CTest、`cases/w7_neutron_only_regression/` | 既有伴随回归 1/1 通过；W7 输入退出 0。 |
| 7 | 同步文档 | 知识库、物理导读、INDEX | W5 标记已修复；完整能力因 W6 保持 E。 |

**代码改动**：见 [changes.diff](changes.diff)，摘要：
- `RMC/src/GetExitState.cpp` —— 伴随散射权重以局部总原子密度归一化宏观总截面。
- `RMC/src/SampleColliType.cpp` —— 伴随裂变权重采用相同修正。

生成方式：
```bash
git -C ../../RMC diff -- src/GetExitState.cpp src/SampleColliType.cpp > changes.diff
```

采用路径限定是因为 RMC 工作树已含独立 W7 任务的 `src/InitiateAll.cpp`；W5 快照不得把该改动重复归档。

---

## 6. 验证 / 实验记录（④ · Agent 填，要贴真实输出）

| 验证项 | 命令 | 结果 |
|---|---|---|
| 增量编译 | `cmake --build /tmp/mlvr_f02_rmc_build --parallel 2` | 退出 0；`[100%] Built target RMC`。 |
| V2 密度不变性 | 三个目录运行 RMC 后执行 `analyze_density_invariance.py` | 三组退出 0；各 128 个首碰撞状态；平均/最小/最大权重均为 `0.66903`，相对比 $1:1:1$，判据通过。 |
| $r=1$ 逐事件等价 | `sha256sum` + `cmp` 修复前后 `.source` | SHA256 均为 `7effc2428b2d030ac60d5acc193c21da94592231d6eeb3ac71200a2b5627691d`；`cmp` 退出 0。 |
| 既有伴随回归 | `ctest --test-dir /tmp/mlvr_f02_rmc_build -R '^test_fixed_source_adjoint$' -V` | 1/1 passed，0 failed。 |
| W7 兼容性 | 在本任务 `cases/w7_neutron_only_regression/` 重放 RMC | 退出 0；12,487 条 `Particle:`；0 条崩溃信号。 |
| reference 完整性 | `sha256sum RMC/tests/fixed_source_adjoint/reference_result` | `750be0255b972f0d4aa25dbd2a0c864e17b5b04058be4749109cb10290443faa`，未变。 |
| 补丁与范围 | `git -C RMC diff --check`、`diff --name-only` | 格式通过；当前三文件为 W5 两文件加既有 W7 `InitiateAll.cpp`。 |
| 编辑器诊断 | `get_errors` | Python/Markdown 无诊断；两份 C++ 因编辑器 includePath 未配置 `hdf5.h` 报环境诊断，实际 CMake 编译成功。 |

```
V2 after W5 fix:
r0.5 exit_code=0 sample_count=128 mean=0.66903 relative_to_r1=1.0
r1   exit_code=0 sample_count=128 mean=0.66903 relative_to_r1=1.0
r2   exit_code=0 sample_count=128 mean=0.66903 relative_to_r1=1.0
criterion: max relative error <= 5.0e-04; pass=True

Regression:
1/1 Test #62: test_fixed_source_adjoint ........ Passed 0.77 sec
100% tests passed, 0 tests failed out of 1

W7 compatibility:
exit_code=0
particle_records=12487
signal_lines=0
```

**实验设置**：
- RMC：3.5.0，基线 `4d3e1aac60f1c40062f05e5d532afb6c7eb6fb4b`，standard ACE，AIS/MPI/OpenMP off。
- V2：30 群 H/O，cell `DENS` 对应 $r=0.5,1,2$；每组 128 粒子；RNG type 2、seed 1、stride 1,000,000；相同输入与修复前 V2 一致。
- W7 回归：7 群 neutron-only `c5g7td`，10,000 粒子；同一 RNG 设置。
- 工具链：G++ 13.3.0、CMake 3.28.3；见 `logs/baseline.txt`。
- 基准对比：修复前 V2 平均权重 `1.3381, 0.66903, 0.33452`，修复后均为 `0.66903`；不更新 reference。

**未覆盖到的验证**：V2 动态判据直接覆盖非裂变散射首碰撞；裂变调用点使用相同修正公式并通过编译及 neutron-only 裂变算例可达性检查，但未把 W5 从 W6 双 nubar 不一致中隔离出来做独立裂变权重统计。未覆盖一般密度网格、跨区非均匀场互易性、混合材料、AIS/HDF5、continuous-energy、MPI/OpenMP 或 Windows。未做浏览器级 Mermaid 渲染，只检查图块结构。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：W5 根因已修复。MGACE 伴随散射和裂变权重均用当前位置总原子密度 $N_0r$ 归一化宏观总截面；共同密度因子正确抵消。V2 从 $2:1:0.5$ 恢复为 $1:1:1$，$r=1$ 逐事件不变，既有回归和 W7 兼容性通过。
- **遗留问题 / 后续待办**：W6 双 nubar 核不一致仍未修复，完整 standard MGACE fixed-source neutron adjoint 保持 E — Defect。一般非均匀密度场互易性和混合材料仍需后续验证。
- **知识库同步**：更新 `06_已知问题与改进建议.md`、`02_RMC功能审查矩阵.md`、`AGENT_CONTEXT.md`；物理导读补充 W5 修复公式、边界、第六张密度数据流图及当前能力状态。
- **是否已提交**：未 commit、未 push、未切分支；由用户决定。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-25 16:40 | 立项 |
| 2026-08-25 | 完成根因复核与三方案设计；用户授权自主选择后采用方案 A。 |
| 2026-08-25 | 完成两处源码修复、V2 密度不变性、既有回归和 W7 兼容性验证。 |
| 2026-08-25 | 同步知识库、物理导读和任务台账，归档真实输出。 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 复核 W5 数据流 | `SampleFreeFlyDist.cpp`、`GetExitState.cpp`、`SampleColliType.cpp`、`MaterialFunctions.cpp` | 确认宏观总截面含 $r$，两处权重分母只使用 $N_0$。 |
| 3 | 冻结局部假设与验证判据 | V2 历史证据、现有 getter | 推荐两处改用 $N_0r$；修复后判据为三组相对权重 $1:1:1$。 |
| 4 | 人工决策询问 | VS Code 选择题 | 用户暂不可响应并授权自主决定；采用推荐方案 A，写入第 4 节后才修改 RMC。 |
| 5 | 实施 W5 | `GetExitState.cpp`、`SampleColliType.cpp` | 两处改用局部总原子密度 getter。 |
| 6 | 首个聚焦验证 | 增量编译 | 构建成功，假设未被接口/类型检查否定。 |
| 7 | 行为验证 | 独立 V2 case + 新分析器 | 三组权重严格 $1:1:1$；$r=1$ source 逐字节不变。 |
| 8 | 回归与归档 | CTest、W7 case、文档与快照 | 回归通过；W7 可达；知识库与物理导读同步。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
