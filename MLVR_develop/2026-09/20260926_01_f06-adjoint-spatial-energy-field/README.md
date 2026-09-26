# f06-adjoint-spatial-energy-field

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-26 |
| 状态 | 已完成（C — Verify，serial text-first Cartesian 子域） |
| 任务类型 | 只读功能审查 / MG fixed-source adjoint 空间×能群场 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F06 |
| 涉及文件 | 只读 RMC tally/adjoint/mesh/output 路径；任务目录内输入与运行证据 |
| 分支 / 提交 | 根工作区 `main`；随本档提交（2026-09-26）；RMC 未修改 |

---

## 1. 目标与范围（① 立项 · Agent 填）

**要做什么**：只读审查 current RMC 能否在冻结子域（standard MGACE、fixed-source neutron、adjoint、Cartesian mesh、Type=1、`Energy=-1`、serial）输出 MLVR 第一版所需的空间×能群伴随标量通量场 $\phi^\dagger_{i,g}$。
**涉及什么**（仓库 / 模块 / 数据）：只读 RMC tally/adjoint/mesh/output 路径；任务目录内最小输入与运行证据；不重开 F02/F03/F04，不审查 F07 统计。
**怎样算完成**：完成执行链静态审查 + 最小运行验证（2 spatial × 30 group 可恢复），给出 F06 要求对比表与分类；详细结果见 §10。
**原始材料**（`logs/` 下有什么，原样保存）：`f06_minimal_adjoint_meshtally.inp` 及其运行输出（`.stdout`/`.Tally`）；其余 `.inp.*` 产品与 `.h5` 原件仅保留本地。

> **模式 C 追加 · 物理解释**：合格字段是每个空间 bin × 每个 MG transport group 的 source-normalized 标量通量密度；若 group 映射、体积归一化或文本输出维度任一处不成立，该假设被推翻。

---

## 2. 做法与证据（② 设计 · ④ 实施 · Agent 填）

**设计 / 定位**（读了什么、查到什么；关键证据给 `文件:行号` 或数据位置）：见 §10.2–§10.5（执行链、索引、输出表示）与 §10.7（F06 要求对比）；关键证据：`ReadMeshTallyCard.cpp:174-188,257-267`、`SingleTally.cpp:875-890,913-1004`、`TallyByTL.cpp:8-54`、`ScoreMeshTally.cpp:9-118`、`GetMgCs.cpp:231-260`。
**方案选择**（选了什么、放弃了什么、为什么）：最小输入（2 空间 bin）验证可达性；HDF5 与用户自定义跨群边界明确排除；不做 RMC 修改。
**实施要点**（改了什么；改动快照见 `changes.diff`，无代码改动写“无”）：无 RMC 改动；新增任务目录输入与运行证据。
**验证输出**（贴真实命令与输出；物理结论从严，工程/文档从简）：见 §10.6；摘要如下：

```text
RMC_EXIT=0；MPI/OMP OFF；collisions/source = 0.67
mesh (1,1,1): group 18 = 3.3037E-01; total = 1.1071E+00
mesh (1,1,2): group 18 = 1.7222E+01; total = 1.8036E+01
```

**未覆盖到的验证**（如实写；没有就写“无”）：见 §10.8——MPI/OpenMP、无 warning 几何、HDF5 energy axis、CE/耦合粒子、direct single-group oracle、field consumer、F07 统计。

---

## 3. 决策记录（③ · **人拍板**）

- **决定**（采纳什么方案）：按用户任务书执行只读功能审查（范围与停止条件见 §10.1/§10.8）；只读 RMC，不改测试/基准。
- **决定人 / 日期**：用户 / 2026-09-26。
- **约束**（能不能动接口 / 基准 / 算力预算…）：不修改 `RMC/`；不重开 F02/F03/F04；F07 统计另立任务。

**变更卡（B/C 模式，各一行）**：
| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| 把“有输出”误判为可用 field | 只读源码 + 任务目录最小运行；不改 RMC | 执行链闭合 + 2 空间 × 30 group 可恢复即停止；HDF5/边界保留为限制 | 删除任务目录生成物；无 RMC 回滚 |

> **模式 C 追加 · 人类理解确认**：立项时确认范围：只读、不修改 RMC、不审 F07；结论边界见 §10.8。

> 未拍板前，Agent 不得改动 `../RMC` 下的任何文件。



---

## 4. 结论与边界（⑤ 归档）

- **结论**：C — Verify（冻结子域：serial text-first Cartesian field）。见 §11 摘要与 §10.8。
- **不能推出什么**（边界）：HDF5Mesh 不是 space×energy 机器可读场；不外推 MPI/OpenMP、CE、耦合粒子、其他 estimator、跨群自定义边界与 F07 统计有效性。
- **遗留 / 下一步**：接受 text-first 接口则可关闭 F06 限定审查；机器可读场另立扩展任务；F07 单独审查 RE。
- **提交状态**：RMC 未修改、无 commit/push；档案随 2026-09-26 根工作区提交入库；`*.h5` 与原始 `.inp.out/.fissmul/.material/.rossialpha/.cumrossialpha` 按归档体积规范不入库、仅保留本地。

> **模式 C 追加 · 结果解释**：结果支持“限定配置下 RMC 可提供可解析的伴随标量轨长通量场”；不说明 HDF5 可直接消费、不说明所有 mesh/并行等价，也不说明 RE 已统计可靠。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-26 01:10 | 立项 |
| 2026-09-26 | 建立任务档案，完成静态执行链审查。 |
| 2026-09-26 | 首次最小输入因显式 `END` 不被 TALLY block 接受而失败；删除 `END` 后 exit 0。 |
| 2026-09-26 | 完成 adjoint 两空间 bin × 30 MG rows 运行；同步读取独立复核的 volume normalization、HDF5 limitation 与分类。 |

> 关键命令、误判与修正、未决分歧都写在这里；人机讨论较深时把要点并入本表，**不再单独建会话纪要文件**。原始聊天转储不要入仓（可能含凭据）。

**证据等级（可选）**：物理/审查结论可标 E0–E4；工程、文档、治理任务可省略。

## 10. 审查结果

### 10.1 范围与目标

检查范围冻结为 standard MGACE、fixed-source neutron、adjoint、Cartesian mesh、Type=1 scalar flux、`Energy=-1`。不重新打开 F02/F03/F04，不审查 F07 的 RE 公式或统计有效性。

第一版目标是可恢复的

\[
\phi^\dagger_{i,g}=\frac{1}{W_0 V_i}\sum_h\sum_{\ell\in(i,g)} w_h^\dagger\ell,
\]

其中 $W_0$ 为 fixed-source 总初始权重；这是标量轨长通量密度，不是每个 mesh bin 的体积分通量。

### 10.2 Tally 执行链

`MESHTALLY` 由 `ReadTallyBlock()` 调用 `ReadMeshTallyCard()` 读取；`TYPE=1` 对应 `TallyFlux`，`ESTIMATOR` 缺省为 track-length。`Energy=-1` 在 `SetupMeshTally()` 中替换为 `CDAceData::p_vNeuMltErgBins`，数据长度为 `N_mesh*(N_energy+1)`。

fixed-source transport 在 `RayTracking.cpp` 中调用 `TallyByTL()`；`TallyByTL()` 调用 `ScoreMeshTallyByTL()`。后者对每个穿越的 mesh 子段累加 `p_dWgt * track_length`，并以 `GetErgValue()` 将 MG 内部群坐标映射到群中心物理能量后选 energy bin。`NORMALIZE=1` 时 mesh track 构造器将子段除以该 mesh 体积。`ProcessTally()`/`CalcAveRe()` 再做 fixed-source 总权重归一化与均值计算。

关键证据：`RMC/src/ReadMeshTallyCard.cpp:174-188,257-267`；`RMC/src/SingleTally.cpp:875-890,913-1004`；`RMC/src/TallyByTL.cpp:8-54`；`RMC/src/ScoreMeshTally.cpp:9-118`；`RMC/src/GetMgCs.cpp:231-260`；`RMC/src/TallyData.cpp:83-101`；`RMC/src/OutputTally.cpp:245-275`。

### 10.3 实际统计量

- `TYPE=1` + track-length：$\sum w\ell$。
- `NORMALIZE=0`：每源权重归一化的 volume-integrated track length。
- `NORMALIZE=1`：每源权重归一化的 volume-averaged scalar flux，即 $\sum w\ell/V_i$。
- fixed-source adjoint 下 tally 直接读取当前 `p_dWgt`；没有 `p_bIsAdjointParticle` 专用 tally 分支。adjoint 权重修正发生在 transport collision/free-flight 代码中，下一段轨迹由同一通用 mesh tally 计数。因此在限定范围内可解释为 $\phi^\dagger_{i,g}$。

### 10.4 空间与能群索引

支持 uniform Cartesian、heterogeneous Cartesian 和 cylindrical mesh；第一版 Cartesian 足够。uniform Cartesian flattening 为 x-fastest：`mesh_index = z*Nx*Ny + y*Nx + x`。文本输出用 one-based `(x,y,z)`，每个空间 bin 独立输出。

`Energy=-1` 使 tally 边界使用 MGACE physical group boundaries；输出行按物理能量升序排列，而 RMC 内部群编号是 reverse order。因群中心落在自身 group 内，`transport group -> GetErgValue() -> one physical energy bin -> output row` 在 `Energy=-1` 下是一一对应关系。用户自定义 energy boundaries 可能切过 MG group，此时只按群中心投影，不能解释为群内连续能量场；本任务不采用这种输入。

### 10.5 输出表示

文本输出文件为 `<input>.Tally`，每个 mesh 块逐行输出 `(x,y,z)`、Group、Energy Bin、Ave、RE，并额外输出 per-mesh total；total 不是额外能群。该文本结构可恢复 space×group。

`HDF5Mesh=1` 的现有输出只按空间 reshape，没有 energy axis loop，不能作为 F06 space×energy machine-readable field；该问题不在本任务修复。

### 10.6 最小运行验证

实际命令：

```text
RMC_DATA_PATH=/home/silver/NucXS_Library/RMC_DATA /tmp/rmc-f08-cell-ww-build/bin/RMC f06_minimal_adjoint_meshtally.inp
```

真实结果：

```text
RMC_EXIT=0
MPI parallel: OFF
OMP parallel: OFF
Neutron collisions per source particle: 0.67
```

输出 `f06_minimal_adjoint_meshtally.inp.Tally` 含 2 个空间 bin：`(1,1,1)` 与 `(1,1,2)`；每个 bin 含 30 个 MG group 行。非零结果出现在多个能群，例如 group 18–30；两空间 bin 数值不同：

```text
mesh (1,1,1): group 18 = 3.3037E-01; total = 1.1071E+00
mesh (1,1,2): group 18 = 1.7222E+01; total = 1.8036E+01
```

这证明当前链路能在 adjoint 运行中输出独立的空间×能群文本数据。该最小运行使用了较宽 transverse mesh，仍有 source/geometry warning；warnings 已记录，不能视为干净的物理基准验证。

独立复核任务另完成了 raw/normalized 两空间不等体积测试：raw-to-normalized ratios 为 `49,999.24` 与 `150,000.0 cm3`，与 mesh 体积一致；独立记录见 `20260926_02_independent-f06-adjoint-field-review/`。

### 10.7 F06 要求对比

| Requirement | 判定 | 证据/边界 |
|---|---|---|
| fixed-source MG neutron adjoint 可运行 | 满足（限定 serial） | 最小运行 exit 0 |
| 独立空间 bin | 满足 | 文本输出 `(x,y,z)`；2 个 bin 数值不同 |
| 独立 MG energy group | 满足（`Energy=-1`） | 30 rows；`GetErgValue` physical-centre mapping |
| scalar adjoint flux physical definition | 满足（`TYPE=1, Normalize=1`） | $\sum w^\dagger\ell/V_i/W_0$ |
| adjoint current weight | 满足（F02 scope） | generic `p_dWgt`，无 tally-side adjoint branch |
| stable text reconstruction | 满足 | x-fastest flattening + one-based rows + physical group boundary |
| machine-readable space×energy file | 不满足 | current `HDF5Mesh` lacks energy axis |
| RE/statistical validity | 留给 F07 | 只记录输出存在，不审查公式 |

### 10.8 分类、边界与下一步

**Classification: C — Verify（冻结子域：serial text-first Cartesian field）。**

当前结论不是 A：HDF5 不是 space×energy field；运行仍有 geometry/source warnings；MPI/OpenMP、clean boundary ownership、CE/coupled particle、direct single-group oracle 和 field consumer 未覆盖。当前结论也不是 E/F：在限定子域内没有发现 tally 不执行、adjoint 权重丢失或 group index 断裂的代码缺陷。

F07 只需另行审查 RE/statistical validity。若第一版需要机器可读的 space×energy 资产，另立 F06 扩展任务审查/实现 energy-aware HDF5 或其他输出，不在本任务中修改。

> **模式 C 结果解释**：通过说明 RMC 当前能在限定配置下提供一个可解析的伴随标量轨长通量场；不说明 HDF5 可直接消费、不说明所有 mesh 类型/并行配置等价，也不说明 RE 已经统计可靠。

## 11. 结论与边界（归档摘要）

- **结论**：F06 在 `standard MGACE + fixed-source neutron adjoint + Cartesian + Type=1 + Energy=-1 + Normalize=1 + serial text output` 子域满足第一版空间×能群伴随标量通量场需求。
- **不能推出什么**：不能把当前 HDF5Mesh 当作 space×energy 机器可读场；不能外推到 MPI/OpenMP、CE、耦合粒子、其他 estimator、用户自定义跨群边界或 F07 统计有效性。
- **遗留/下一步**：若接受 text-first 接口，可关闭 F06 的限定审查并进入后续主线；若需要机器可读场，另立 F06 扩展任务。F07 单独审查 RE。
- **提交状态**：未修改 RMC、无 RMC commit/push；任务目录含输入、stdout/stderr、Tally 和审查记录；档案随 2026-09-26 提交入库（`*.h5` 与原始 `.inp.*` 非保留项仅本地）。

## 12. 过程记录补充

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-26 | 建立任务档案，完成静态执行链审查。 |
| 2026-09-26 | 首次最小输入因显式 `END` 不被 TALLY block 接受而失败；删除 `END` 后 exit 0。 |
| 2026-09-26 | 完成 adjoint 两空间 bin × 30 MG rows 运行；同步读取独立复核的 volume normalization、HDF5 limitation 与分类。 |
