# Task: F02 — Multigroup Adjoint Transport Audit

日期：2026-08-24

状态：Audit complete — awaiting human review

关联知识库：

- `MLVR_Knowledge/01_双向迭代基础框架_方法与功能需求.md`
- `MLVR_Knowledge/02_RMC功能审查矩阵.md`
- `MLVR_Knowledge/03_RMC功能审查规范.md`
- `MLVR_Knowledge/DECISIONS.md`

## 1. Requirement

本任务只审查 F02：**RMC 是否真实具备第一版框架所需的多群 Adjoint transport，以及其实际物理实现是否能够被后续双向迭代框架依赖。**

第一版需求边界：

- 仅考虑 multigroup adjoint，不审查 continuous-energy adjoint；
- 本任务重点是伴随输运本体；
- Adjoint source 的完整语义归 F03；
- Adjoint field/RE 的完整能力归 F06/F07；
- Adjoint + WW 兼容性归 F04；
- 可记录这些相邻功能的交叉证据，但不得在本任务中替代其独立审查结论。

## 2. 审查前必须记录

本地 Agent 开始前先记录：

```text
RMC repository path:
RMC branch:
RMC HEAD commit SHA:
git status --short:
审查日期:
Agent/模型:
```

若 RMC 工作区存在未提交修改，只读审查可以继续，但必须记录状态，不能覆盖、整理或修改这些内容。

## 3. 本任务必须回答的问题

### Q1 — 如何启用多群 Adjoint transport？

追踪从输入/配置到运行时状态的完整入口：

```text
input / option
  ↓
parser / initialization
  ↓
adjoint mode state
  ↓
transport entry
```

不能仅凭 `adjoint` 关键词或变量名判定功能存在。

### Q2 — 实际调用链是什么？

形成至少一条可核查的调用链，覆盖：

- 伴随模式进入输运；
- 粒子/伪粒子历史推进；
- 碰撞处理；
- 多群能群转换相关逻辑；
- 历史终止/边界处理。

每个关键节点尽量记录：

```text
file:function:line-range
```

### Q3 — 数学上的伴随算子如何落实？

必须从实际代码判断，而不是从函数名推断。

重点调查：

- 多群散射核/散射矩阵在伴随模式下如何处理；
- 是否存在与正向群间跃迁相对应的转置/反向索引逻辑；
- 能群采样概率、权重修正或等价实现；
- 角变量/方向处理是否存在伴随专用逻辑；
- 其他会影响伴随输运正确性的碰撞权重或采样处理。

注意：完整 Boltzmann 伴随算子是相空间散射核的伴随，不应仅以“矩阵转置”四个字作结论。若当前 RMC 多群实现采用简化条件，应明确写出适用假设和代码证据。

### Q4 — 当前实现是否真正可运行？

调查：

- 是否有现存输入卡、测试、算例或历史用例；
- 是否有明显废弃、未接通、条件编译或无法到达的代码；
- 注释中宣称支持但运行链未连接的情况。

第一轮以静态源码审查为主。如果静态证据不足以确认关键正确性：

- 不要自行宣称“正确”；
- 将相关项记为未验证；
- 给出最小运行/数值验证方案；
- 最终可分类为 **C — Verify**。

## 4. 明确不做的事情

本任务禁止：

- 修改 `RMC/` 任意源码；
- 修复发现的问题；
- 重构伴随模块；
- 设计 MLVR 最终接口/class/controller；
- 审查连续能量伴随；
- 把 F03/F04/F06/F07 合并成一次大审查；
- 更新任何 benchmark/reference output。

若发现明确缺陷，只记录 `file:function:line + 行为 + 为什么是问题`，留到 Stage 3 另立任务。

## 5. 输出格式

审查完成后直接在本 README 追加以下章节，不删除本任务定义。

### A. Environment Snapshot

RMC branch / commit / worktree 状态。

### B. Existing Implementation

入口、文件、类/函数、关键状态变量、调用链。

### C. Actual Behavior

用 `Input → Processing → Output` 解释实际程序行为。

### D. Physics Audit

逐项记录散射、能群、方向、采样/权重等伴随物理实现及证据。

### E. Requirement Gap

| 子需求 | 证据 | 状态 | 备注 |
|---|---|---|---|
| MG adjoint mode exists | | | |
| transport call chain reachable | | | |
| adjoint multigroup scattering behavior understood | | | |
| angular/collision treatment understood | | | |
| executable evidence exists | | | |

### F. Verification Evidence

已有测试/算例/运行证据；没有则明确写 `Not verified`。

### G. Final Classification

必须从以下选择一个主分类：

- A Ready
- B Extend
- C Verify
- D Integration issue
- E Defect
- F Missing

并用 3–8 句解释分类依据。

### H. Open Questions / Proposed Next Action

只提出下一步审查或最小验证，不进行源码修复。

## 6. 人工决策

2026-08-24：用户已批准 Stage 2 审查协议，并批准 F02 多群 Adjoint transport 作为第一项正式只读审查任务。

本次批准仅允许**只读调查与必要的非修改型验证建议**，不授权修改 RMC 源码。

## 7. 完成条件

只有同时满足以下条件，本任务才可提交用户复核：

- 记录 RMC branch + commit；
- 给出可追溯调用链；
- 解释实际多群伴随物理实现，而非只列符号；
- 明确已验证与未验证内容；
- 给出唯一 A–F 主分类；
- 未修改 RMC 源码。

用户确认 F02 结论后，才进入下一项 F03 审查。

## A. Environment Snapshot

```text
RMC repository path: /home/workspace/AI_MC_WW_interation/RMC
RMC branch: Neural_Network_WW_Iteration
RMC HEAD commit SHA: 4d3e1aac60f1c40062f05e5d532afb6c7eb6fb4b
git status --short: clean（0 条）
审查日期: 2026-08-24
Agent/模型: GitHub Copilot / gpt-5.6-sol (xhigh) · REAL GPT
OS: Linux
RMC_DATA_PATH: /home/silver/NucXS_Library/RMC_DATA（目录存在）
本仓库可执行文件: 未发现
```

本次只读审查未修改 `RMC/`。以下行号均以该 commit 为准。

## B. Existing Implementation

### B.1 启用入口与状态传递

多群伴随不是由单独的“Adjoint 求解器”入口启动，而是由多群核数据库模式与固定源伴随卡共同启用：

```text
MATERIAL / MGACE
FIXEDSOURCE
  PARTICLE ... [FISSION=<neutron> <photon>]
  ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=<neutron> <photon>
```

证据链：

1. `ReadInputBlocks()` 遇到 `FIXEDSOURCE` 时设置 `FixedSourceMode`，再调用 `ReadFixedSourceBlock()`：`RMC/src/ReadInputBlocks.cpp:137-150`。
2. `ReadFixedSourceBlock()` 将 `ADJOINTCALCULATION=1` 写入 `CDFixedSource::p_bIsAdjoint`，并读取中子/光子两个最大伴随能量：`RMC/src/ReadFixedSourceBlock.cpp:207-242`。
3. `RunCalculation()` 将 `FixedSourceMode` 分派至 `CalcFixedSource()`：`RMC/src/RunCalculation.cpp:81-89`。
4. `CDFixedSource::InitiateAll()` 将固定源伴随状态传给 `CDAceData::p_bIsAdjoint`；材料读库完成后把最大伴随能量映射为群号：`RMC/src/InitiateAll.cpp:125-132,191-195`。
5. `CDMaterial::InitiateMatAce()` 只在 `p_bIsMultiGroup && p_bIsAdjoint` 时调用 `treatAdjointMaterial()`：`RMC/src/InitiateMatAce.cpp:8-66`。
6. `SampleFixSource()` 把外源实际能量映射为群号，并把源粒子标为 `p_bIsAdjointParticle=true`：`RMC/src/SampleNeutronSource.cpp:180-268`。

因此，可达的 F02 入口是 **MGACE 多群 + FIXEDSOURCE/ADJOINT**。本任务没有把临界计算中的 `CDAdjoint`/GPT 敏感性路径视为该功能的入口。

### B.2 固定源伴随输运调用链

主路径（中子、默认标准 ACE 构建）如下：

```text
main()
  → ReadInputBlocks()
    → ReadFixedSourceBlock()
  → RunCalculation()
    → CalcFixedSource()
      → CDFixedSource::InitiateAll()
        → CDMaterial::InitiateMatAce()
          → CDAceData::treatAdjointMaterial()
      → CDFixedSource::SampleFixSource()
      → CDFixedSource::TrackHistory()
        → CDFixedSource::RayTracking()
          → GetNextTrackCalFlyDistance()
            → SampleFreeFlyDist() / CalcMacroXS()
          → 几何边界迁移、边界 tally、escape/kill
        → SampleColliNuc()
        → CalcColliNucCs()
        → TreatImpliCapt()（MG adjoint 直接返回）
        → SampleColliMT_FixedSrc()
        → GetExitState()
          ├─ scatter → GetMgAdjNeuExitErgMu() → RotateDirection()
          └─ fission → TreatFission() → GetFissionNeuState() → fixed-source bank
        → UpdateNeuStateMg()
      → 若 bank 非空：SampleFromParticleBank() → 再次 TrackHistory()
```

关键位置：

- 固定源初始化与历史循环：`RMC/src/CalcFixedSource.cpp:67-169`。
- 历史推进、碰撞处理、出射状态、状态更新：`RMC/src/TrackHistory.cpp:163-301`。
- 几何边界、自由程、跨面、逃逸/终止：`RMC/src/RayTracking.cpp:204-303`。
- 伴随核素抽样：`RMC/src/SampleColliNuc.cpp:9-49`。
- 标准 ACE 伴随反应类型抽样：`RMC/src/SampleColliType.cpp:146-198`。
- 伴随散射出射群/角度：`RMC/src/GetMgExitErgMu.cpp:446-519`。
- 伴随散射/裂变状态应用与能量上限终止：`RMC/src/GetExitState.cpp:162-207`。
- 多群状态更新：`RMC/src/ParticleStateFun.cpp:130-141`。
- 伴随裂变固定为一个后继粒子并入固定源 bank：`RMC/src/GetFissionNeuState.cpp:550-734`。

没有发现独立的“伪粒子伴随输运”参与该固定源 F02 主路径；`clearPseudoParicles()` 在历史末尾清理的是固定源公共基础设施。临界 GPT 的 pseudo-particle 路径属于另一套功能，不作为 F02 存在性证据。

### B.3 条件编译范围

- `CMakeLists.txt:77` 的 `ais` 默认值为 `OFF`，故标准 ACE 分支是默认构建路径。
- 标准 ACE 分支中的 `SampleColliMT_FixedSrc()` 包含伴随散射和伴随裂变抽样。
- 当以 `ais=ON` 构建时，`SampleColliType_FixedSrc()` 的 MG adjoint 分支只固定返回 `N_ELASTIC`，并有显式 `todo`：`RMC/src/SampleColliType.cpp:308-324`。因此 **AIS/HDF5 多群伴随碰撞链不能视为完整实现**。

## C. Actual Behavior

### C.1 Input

1. `MGACE` 选择多群核数据并定义中子/光子群数。
2. `FIXEDSOURCE` 选择固定源模式。
3. `ADJOINTCALCULATION=1` 开启固定源伴随状态；`MAXADJOINTENERGY` 的两个值分别用于中子和光子上限。
4. `PARTICLE ... FISSION=<n> <p>` 可控制中子/光子固定源裂变；若未给该选项，`CDNeutronTransport::p_bTreatFission` 默认是 `true`：`RMC/src/NeutronTransport.h:43-56`、`RMC/src/ReadFixedSourceBlock.cpp:35-63`。
5. 外源本身仍由 `EXTERNALSOURCE` 提供。该源是否满足目标响应驱动的伴随源语义留给 F03。

### C.2 Processing

初始化时，RMC 从正向多群数据预计算每种核素、每个伴随当前群的总“伴随产生截面”，包含散射前驱群贡献和裂变前驱群贡献。运行时：

1. 粒子几何飞行仍按当前群的**正向物理宏观总截面** $\Sigma_t(h)$ 抽样。
2. 同时为材料计算伴随产生截面 $\Sigma_{\mathrm{prod}}^\dagger(h)$ 的原子份额加权混合值。
3. 碰撞后按该伴随产生截面选择核素，再在该核素内选择散射或裂变及前驱群。
4. 通过碰撞权重乘子补偿“按正向 $\Sigma_t$ 飞行、按伴随产生核抽样”的偏倚。
5. 散射后更新能群与方向；裂变时终止母粒子，并把一个伴随后继粒子压入固定源 bank；bank 粒子随后按同一历史循环继续输运。
6. 越界、逃逸、能量上限、几何定位失败、表面穿越过多或裂变终止等沿固定源公共终止路径处理。

### C.3 Output

F02 本体没有专用“伴随场”输出对象；伴随粒子使用固定源 tally 基础设施产生 tally 结果。现有回归用例输出按 30 群分箱的 neutron cell track-length flux。空间–能群 Adjoint Field 和逐 bin RE 是否满足框架要求，仍须在 F06/F07 独立审查。

## D. Physics Audit

### D.1 能群约定

多群内部群号从 1 开始，且**群号越小、能量越高**。`LocateMgErgGrp()` 从按低到高存储的群边界定位后执行 `group_count - interpolation_position`；`GetMgNeuCentErg()` 做相反索引映射：`RMC/src/GetMgCs.cpp:221-230,263-301`。这解释了 `GetExitState()` 中“出射群号小于最大允许群号则终止”的上限判断。

### D.2 伴随散射群核

设正向散射核中 $g$ 为正向入射群、$h$ 为正向出射群。`treatAdjointMaterial()` 以 `jg` 遍历正向入射群、以 `jh` 遍历正向出射群，把对应 P0 产生截面累加到伴随当前群 `jh`：`RMC/src/TreatAdjointMaterial.cpp:34-63`。因此其群积分形式意图为

$$
\Sigma_s^\dagger(h\rightarrow g)=\Sigma_s(g\rightarrow h).
$$

运行时 `GetMgAdjNeuExitErgMu()` 固定伴随入射群 `incidGrp=h`，遍历候选 `exitGrp=g`，并通过 `ixcos` 读取正向 `(g\rightarrow h)` 对应的群转移值和角分布位置：`RMC/src/GetMgExitErgMu.cpp:446-519`。这不是仅靠函数名推断，而是实际反向索引抽样。

### D.3 裂变群核

初始化时，对每个正向前驱群 $g$ 计算 $\nu\Sigma_f(g)$，再按当前伴随群 $h$ 的 $\chi(h)$ 累加：`RMC/src/TreatAdjointMaterial.cpp:38-52`。其意图对应可分离多群裂变核

$$
K_f^\dagger(h\rightarrow g)=\chi(h)\,\nu\Sigma_f(g).
$$

`SampleColliMT_FixedSrc()` 先按 $\chi(h)\sum_g\nu\Sigma_f(g)$ 选择伴随裂变，再按 $\nu\Sigma_f(g)$ 选择前驱群：`RMC/src/SampleColliType.cpp:164-187`。`GetFissionNeuState()` 将伴随裂变后继数强制为 1，保留已选群、仅调用多群裂变函数取得方向并压入固定源 bank：`RMC/src/GetFissionNeuState.cpp:550-575,700-734`。

需要验证的索引风险：初始化统一使用 `GetMgNeuLNU()`；但运行时前驱群抽样直接使用 `JXS[4]`，旁边保留了改用 `GetMgNeuLNU()` 的 `todo`：`RMC/src/SampleColliType.cpp:168-172`。`GetMgNeuLNU()` 在 `NNUBAR>1` 时会返回 `JXS[4]+group_count`：`RMC/src/Nuclide.cpp:28-35`。因此单一 nubar 数据表时两者等价；多个 nubar 数据表时选择的是哪一套 $\nu$ 数据，静态证据不足，列为 **Verify**，不在本 Audit 中判为已证实缺陷。

### D.4 碰撞抽样与权重修正

`CalcMacroXS()` 用正向微观 $\Sigma_t$ 与绝对原子密度计算 $\Sigma_t^{macro}$，自由程为

$$
\ell=-\frac{\ln\xi}{\Sigma_t^{macro}(h)}.
$$

同时，伴随分支计算

$$
\bar\Sigma_{\mathrm{prod}}^\dagger(h)
=\sum_i f_i\Sigma_{\mathrm{prod},i}^\dagger(h),
$$

其中 $f_i=N_i/N_{tot}$ 是材料核素原子份额：`RMC/src/SampleFreeFlyDist.cpp:52-103`、`RMC/src/Material.h:41-43,302`。`SampleColliNuc()` 再按 $f_i\Sigma_{\mathrm{prod},i}^\dagger(h)$ 选择核素：`RMC/src/SampleColliNuc.cpp:22-49`。

散射和裂变分支都应用同一权重乘子：

$$
w' = w\,
\frac{\bar\Sigma_{\mathrm{prod}}^\dagger(h)}
{\Sigma_t^{macro}(h)/N_{tot}}
=w\,\frac{\Sigma_{\mathrm{prod}}^{\dagger,macro}(h)}
{\Sigma_t^{macro}(h)}.
$$

代码位置为 `RMC/src/GetExitState.cpp:182-197` 和 `RMC/src/SampleColliType.cpp:188-192`。材料总原子密度单位和核素份额定义见 `RMC/src/Material.h:33-43,302`；绝对核素原子密度由总密度乘归一化份额得到：`RMC/src/ConvertMatNucDen.cpp:35-63`。该量纲链闭合。

`TreatImpliCapt()` 对 MG adjoint 直接返回：`RMC/src/TreatImpliCapt.cpp:7-11`。这避免再按正向吸收概率削减权重；吸收/非产生损失已经由上述产生核与总截面的权重比隐式处理。

### D.5 角变量与方向

对某一对转置后的群 `(h→g)`，代码使用正向 `(g→h)` 对应的角分布数据抽样 `MuLab`，随后调用公共 `RotateDirection(MuLab, old_dir, new_dir)`：`RMC/src/GetMgExitErgMu.cpp:462-505`、`RMC/src/GetExitState.cpp:182-186`。若没有角分布则各向同性抽样。

这表明 RMC 不只是转置群积分矩阵，还尝试复用转置群对的角核。然而源码没有显式写出或验证完整相空间恒等式

$$
K^\dagger(g,\Omega\rightarrow h,\Omega')
=K(h,-\Omega'\rightarrow g,-\Omega)
$$

（具体符号取决于采用的伴随方向约定）。当前实现直接围绕伴随粒子的当前飞行方向旋转，而没有可见的方向反号/互易性说明。对仅依赖散射夹角、方位对称、静止介质且群常数角核满足相应互易约定的模型，这可能是等价实现；但静态源码不足以证明一般各向异性角核的完整伴随性。因此“角处理代码机制已识别”，而“完整相空间伴随正确性”仍为 **Not verified**。

### D.6 适用边界

本审查可静态确认的主体范围是：

- 固定源、多群、中子；
- 默认 `ais=OFF` 的标准 ACE 多群数据路径；
- 以 P0 群产生截面构造群抽样概率，并按所选群对读取已有角分布；
- 可分离的多群裂变表示 $\chi(h)\nu\Sigma_f(g)$。

本审查不宣称：

- 连续能量伴随可用；
- AIS/HDF5 多群伴随碰撞链完整；
- 光子或中子–光子耦合伴随已正确验证；
- 一般各向异性相空间核已满足数值伴随互易性；
- 伴随裂变（特别是多套 nubar 数据）已由当前测试覆盖；
- 伴随源、WW 组合、Field/RE 输出已通过 F02 一并确认。

## E. Requirement Gap

| 子需求 | 证据 | 状态 | 备注 |
|---|---|---|---|
| MG adjoint mode exists | `ReadFixedSourceBlock.cpp:207-242`; `InitiateAll.cpp:125-132`; `InitiateMatAce.cpp:60-66` | 满足（默认标准 ACE 范围） | `MGACE + FIXEDSOURCE/ADJOINT` 可达；AIS/HDF5 除外。 |
| transport call chain reachable | `RunCalculation.cpp:81-89`; `CalcFixedSource.cpp:67-169`; `TrackHistory.cpp:163-301`; `RayTracking.cpp:204-303` | 满足（静态） | 覆盖源抽样、飞行、碰撞、边界、bank 和终止。 |
| adjoint multigroup scattering behavior understood | `TreatAdjointMaterial.cpp:34-63`; `GetMgExitErgMu.cpp:446-519` | 部分满足 / Verify | 群对转置与抽样机制明确；缺少非对称矩阵的数值内积验证。 |
| angular/collision treatment understood | `SampleFreeFlyDist.cpp:52-103`; `SampleColliNuc.cpp:22-49`; `GetExitState.cpp:182-197` | 部分满足 / Verify | 碰撞偏倚与权重比量纲闭合；一般各向异性方向约定未验证。 |
| adjoint fission treatment understood | `TreatAdjointMaterial.cpp:38-52`; `SampleColliType.cpp:164-192`; `GetFissionNeuState.cpp:550-734` | 部分满足 / Verify | 结构对应 $\chi\nu\Sigma_f$；现有测试无裂变材料，且多 nubar 索引有待核对。 |
| executable evidence exists | `tests/fixed_source_adjoint/*`; `tests/CMakeLists.txt:117`; `tests/configure.yaml:1516-1524` | 有资产，当前 SHA 未验证 | 回归覆盖 H/O 30 群非裂变 case；本地无 RMC executable，未实跑。 |
| default build path complete | `CMakeLists.txt:77`; `SampleColliType.cpp:146-198` | 满足（静态） | `ais=OFF` 时进入包含完整反应抽样的标准 ACE 分支。 |
| AIS/HDF5 build path complete | `SampleColliType.cpp:308-324` | 不满足 / 范围限制 | MG adjoint 分支固定返回散射并有显式 TODO。 |

## F. Verification Evidence

### F.1 已有测试资产

- 输入：`RMC/tests/fixed_source_adjoint/inp`。
- 注册：`RMC/tests/fixed_source_adjoint/CMakeLists.txt:1-9`，并由 `RMC/tests/CMakeLists.txt:117` 加入总测试集。
- 平台配置：`RMC/tests/configure.yaml:1516-1524` 将 Linux/Windows 的 serial、MPI、OpenMP 均登记为正常测试。
- 参考输出：`RMC/tests/fixed_source_adjoint/reference_result`，包含 30 群 cell track-length neutron flux，总值 `2.1335E-01`、RE `8.2455E-03`。
- 资产历史：该用例随 2023-06-09 的 `feat(adjoint fixedsource)` 提交进入仓库。

该输入使用 H/O 水材料，没有裂变核素；因此它只能覆盖非裂变的多群伴随历史执行与 tally 输出意图，不能覆盖伴随裂变。参考文件存在也不等于当前 commit 已运行通过。

### F.2 本次运行状态

**Not verified on current SHA.** 仓库四层深度内未发现已构建的 `RMC` 可执行文件，因此本次没有运行 CTest，也没有生成或更新任何 reference output。环境中的 `RMC_DATA_PATH` 存在，但仅凭数据目录不能替代可执行验证。

### F.3 最小验证方案

建议在不更新 reference 的前提下依次执行：

1. **现有回归冒烟**：默认 `ais=OFF` 构建当前 SHA，运行 `test_fixed_source_adjoint`，保存退出码、stdout、tally diff；确认 serial 至少通过。
2. **两群非对称散射内积测试**：构造可人工核算且 $\Sigma_s(1\to2)\neq\Sigma_s(2\to1)$ 的两群均匀介质，分别计算正向/伴随双线性量，检查
   $$
   \langle \psi^\dagger,L\psi\rangle
   \approx\langle L^\dagger\psi^\dagger,\psi\rangle
   $$
   是否在 MC 统计误差内一致。此测试必须避免对称矩阵掩盖索引错误。
3. **各向异性角核测试**：使用非对称空间源/响应和明显非各向同性群对角分布，检验方向约定与完整相空间互易性；各向同性 case 不足以完成该验证。
4. **伴随裂变测试**：使用最小可裂变多群材料，分别覆盖单一 nubar 与 `NNUBAR>1` 数据，核对裂变发生概率、前驱群分布、权重和 bank 中后继粒子数。
5. **AIS 单独处理**：若第一版部署明确需要 `ais=ON`，应另立 Stage 3 任务；当前源码已显示该分支不完整，不应只靠运行现有非裂变用例放行。

## G. Final Classification

**C — Verify**

当前 RMC 在默认标准 ACE 构建下确有可达的固定源多群伴随中子输运链，不是仅存在未接通的符号。散射群核采用正向群转移的反向索引，裂变结构意图为 $\chi(h)\nu\Sigma_f(g)$，按正向总截面飞行时也存在一致量纲的碰撞权重补偿。现有仓库还包含已注册的多群伴随回归输入和参考 tally，说明该功能曾被作为可执行能力维护。然而当前 commit 没有本地可执行验证，现有 H/O 用例不覆盖伴随裂变、非对称群矩阵内积互易性或一般各向异性角核。伴随裂变在多套 nubar 数据下还存在直接 `JXS[4]` 与 `GetMgNeuLNU()` 不一致的待核对风险；AIS/HDF5 分支则有显式未完成 TODO。故证据不足以判为 A Ready，主分类为 C Verify；若部署强制要求 AIS/HDF5，则该构建变体本身应按缺口另立任务处理。

## H. Open Questions / Proposed Next Action

1. 由人工确认本次 F02 的范围是否以默认 `ais=OFF` 标准 ACE 为第一版部署基线；若要求 AIS/HDF5，需将其显式缺口登记为后续扩展/缺陷任务。
2. 在具备可执行文件的受控环境执行 F.3 的最小验证，优先完成“现有回归 + 两群非对称散射内积 + 可裂变 case”。原始输出应原样保存到本任务 `logs/`，不得更新现有 reference。
3. 由多群核数据格式负责人确认 `NNUBAR>1` 时，伴随裂变前驱群应使用 `JXS[4]` 还是 `GetMgNeuLNU()` 所选数据；确认前保持 Verify。
4. 在 F02 由用户复核并明确接受结论前，停止于本任务，不进入 F03，不实施任何 RMC 修复。
