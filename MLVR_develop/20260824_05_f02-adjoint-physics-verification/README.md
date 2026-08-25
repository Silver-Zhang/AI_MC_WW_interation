# F02-B Multigroup Adjoint Physics Verification Report

日期：2026-08-24

状态：Independent audit and second-round cross-review complete — awaiting human review

审查类型：Stage 2 RMC existing-capability audit（只读；Audit ≠ Repair）

## A. Scope

本报告审查 RMC 当前代码中**多群、中子、固定源伴随输运**的物理实现是否具备作为后续 MLVR 双向迟代权窗框架伴随求解基础的证据。本报告不是 F02-A 的“功能存在/调用链可达”复述，而是对其散射、碰撞、角变量和裂变核是否符合离散伴随关系的进一步审查。

### A.1 审查基线

```text
RMC repository path: /home/workspace/AI_MC_WW_interation/RMC
RMC branch: Neural_Network_WW_Iteration
RMC HEAD commit SHA: 4d3e1aac60f1c40062f05e5d532afb6c7eb6fb4b
RMC git status --short: clean（无输出）
审查日期: 2026-08-24
默认构建范围: standard ACE，ais=OFF
运行模式: MGACE + FIXEDSOURCE + ADJOINT ADJOINTCALCULATION=1
粒子范围: neutron adjoint
```

`CMakeLists.txt:77` 将 `ais` 默认设为 `OFF`。本报告中“RMC 当前实现”均指上述默认标准-ACE 构建路径；不能据此推断 AIS/HDF5 分支也满足同一结论。

### A.2 纳入与排除

纳入：

- 多群中子能群、散射、碰撞和权重；
- 多群伴随裂变、bank 与 nubar 数据定位；
- 现有固定源伴随测试资产及其覆盖边界；
- 达到伴随算子物理正确性所需的最小数值验证建议。

明确不审查：

- continuous-energy、photon、neutron–photon coupled adjoint；
- GPT/sensitivity 或临界计算的其它 adjoint 路径；
- AIS/HDF5 adjoint；
- adjoint source 语义（F03）、adjoint + WW（F04）、Field/RE（F06/F07）、MLVR controller 或接口设计；
- 任何 RMC 修复、重构、测试参考值更新或基准更新。

本次仅进行了源码与测试资产审查；**未构建、未运行 RMC，未修改任何 `RMC/` 文件，未更新 reference/benchmark 输出。** 若无法由静态证据证明正确，按 D017/D018 记录为 Verify，而不是默认通过。

### A.3 对现有草稿的独立复核摘要

本报告最初由 Claude 完成了一版审查草稿。本轮没有直接接受其判断，而是重新沿 MGACE locator、碰撞抽样、局部密度和裂变 bank 调用链逐项复核。复核结果如下：

| 草稿判断 | 独立复核结果 | 本版处理 |
|---|---|---|
| `minErgGrp` 可能使最小合法前驱群未参与扣减。 | 不成立。该值位于合法下界之前，是递减循环的哨兵；合法前驱群均在触发 `break` 前参与扣减。 | 删除该风险，并在 C.2 给出群范围推导。 |
| 未见显式 P1/P2 转置或 $(-1)^\ell$，因此一般角伴随未落实。 | 论证不充分。MGACE 保存的是选定群对的条件散射余弦分布；若伴随飞行方向解释为正向物理方向的反向，则同时反号前后方向不改变 $\mu$。 | 重写 E.2；不再把“未显式转置高阶矩”本身作为缺陷证据，但仍要求数值互易性验证。 |
| 碰撞权重比量纲闭合，混合材料只需后续数值验证。 | 仅在局部密度比例 $r=1$ 时成立。自由飞行总截面含 $r$，伴随产生量和权重归一化却使用基准材料密度，导致 $w'$ 多出 $1/r$。 | 在 D.3 记为标准路径可达的明确缺陷。 |
| `JXS[4]` 与 `GetMgNeuLNU()` 只是未闭合的数据语义风险。 | 当 `NNUBAR>1` 时，代码和本地 7 群裂变 MGACE 数据共同证明两者分别读取第一组 prompt nubar 与第二组 total nubar；初始化和运行时抽样确实不一致。 | 在 F.3 升级为明确缺陷。 |
| 30 群 `mgxsnp` 首块头中的 `4` 可作为 `NNUBAR>1` 证据。 | 不成立。该 `4` 是 `NXS[3]=NLEG`，`NXS[10]=NNUBAR` 实为 0。 | 删除误引；多 nubar 可达性只引用 `c5g7td` 首个 7 群裂变表。 |
| `nNLEG==1` 负余弦分支可能产生 $\mu>1$。 | 公式差异和越界可能性成立，但尚未完成部署数据 locator 级可达性证明。 | 保留为高优先级 Verify 风险，不升级为本次 E 分类依据。 |

本轮新证据改变了主分类：完整的标准 MGACE 固定源伴随能力存在两项可达的确定性错误，故主分类为 **E — Defect**。对不触发这两项错误的受限子域（局部密度比例 $r=1$ 且 `NNUBAR<=1`），仍只能给出 **C — Verify**，不能升级为 Ready。

### A.4 对 Claude 第二轮反驳的再复核（2026-08-25）

Claude 第二轮回复接受了 C.2 群边界和 E.2 角变量的修正，但提出两项反驳：一是 `p_dMacroTotCs / p_dMatAtomDen` 会以局部总原子密度抵消 $r$，故 D.3 应撤回；二是双 nubar 仅能记为未闭合风险，故主分类应退回 C。对实际成员访问、getter、核数据索引和部署数据重新复核后，两项反驳均不成立：

| 第二轮反驳 | 再复核证据 | 裁定 |
|---|---|---|
| `p_dMatAtomDen` 是包含局部缩放的总原子密度，能抵消宏观总截面中的 $r$。 | `MaterialFunctions.cpp:79-91` 明确区分 `GetMatAtomDen(m)` 与 `GetMatAtomDen(m,r)`；前者和材料成员 `p_dMatAtomDen` 都是基准密度。`SetCellGramDens.cpp:12-32` 只生成 cell 的 `p_dDensRatio`。`CalcMacroXS()` 通过三参数 `GetMatNucAtomDen(...,p_dDensRatio)` 让总截面乘 $r$，而 `GetExitState.cpp:186-189` 与 `SampleColliType.cpp:190-192` 直接读取未缩放成员。 | **反驳不成立。** 可用的局部密度 getter 不等于权重调用点实际使用了它；D.3 的 $1/r$ 数据流闭合，W5 保留。 |
| 本地双 nubar 数据语义和部署可达性尚未复核，因此只能记为潜在风险。 | 当前核库 `xsdir:263-270` 将多个 `.01m` 核素登记到 `multigroup/c5g7td`，并非孤立文件。首表 `10001.01m` 的 `NNUBAR=2`、`JXS[4]=29`、`JXS[5]=43`；两组 nubar 数值不同。standard getter 双表时读取第二组，HDF5 通用 getter 在 total 存在时也明确优先 total，而运行时伴随裂变抽样硬编码第一组。 | **反驳不成立。** 数据可达、两组核不同且调用点混用；W6 保留。即使暂不依赖 prompt/total 标签，仅“初始化阈值采用第二核、群扣减采用第一核且无重要性权重补偿”也已构成确定性错误。 |

对 `c5g7td` 首表按 locator 直接计算得到：

$$
\sum_g\Sigma_f(g)\nu_1(g)=0.71975438088,
\qquad
\sum_g\Sigma_f(g)\nu_2(g)=0.719776674648.
$$

运行时随机阈值由第二组总量选出裂变并除以 $\chi(h)$，随后却只按第一组逐群扣减；两者差额

$$
\Delta=2.22937680699\times10^{-5}
$$

没有权重补偿，并会因循环的末群退出条件落入最后一个群。该实际数据上的后果不取决于两组表的命名。因此，第二轮复核后仍维持：完整能力 **E — Defect**，受限子域 **C — Verify**；不撤回 D.3、F.3、W5 或 W6。

---

## B. Mathematical Adjoint Definition

### B.1 审查目标

目标离散伴随关系为：

$$
L^\dagger \psi^\dagger=q^\dagger,
\qquad
\langle\psi^\dagger,L\psi\rangle
=
\langle L^\dagger\psi^\dagger,\psi\rangle .
$$

对多群散射，若正向核写为 $\Sigma_s(g\to h)$，则群积分伴随核至少应满足：

$$
\Sigma_s^\dagger(h\to g)=\Sigma_s(g\to h).
$$

对可分离多群裂变核：

$$
F(g\to h)=\nu\Sigma_f(g)\chi(h),
$$

其群空间转置为：

$$
F^\dagger(h\to g)=\chi(h)\nu\Sigma_f(g).
$$

这些关系只描述能群离散部分。完整输运伴随还涉及空间、方向和测度约定；不能由“群矩阵已转置”自动推出完整相空间伴随正确。

### B.2 代码中可观察到的约定

| 项目 | 源码证据 | 可确认的行为 | 仍不能确认的部分 |
|---|---|---|---|
| 启用与状态传播 | `ReadFixedSourceBlock.cpp:209-235` → `InitiateAll.cpp:125-131` → `InitiateMatAce.cpp:65-67` | `ADJOINTCALCULATION=1` 使固定源伴随标志传给 ACE/材料初始化，并在 MG 条件下构造伴随产生截面。 | 这只证明实现入口及预处理，不证明数学伴随性。 |
| 伴随粒子 | `SampleNeutronSource.cpp:222`；`TrackHistory.cpp:226-275` | 外源中子被标记为 adjoint，进入固定源历史推进、碰撞和 bank 循环。 | 外源是否为目标响应对应的伴随源属于 F03。 |
| 空间与方向 | `ParticleState.h:474-492`；`ParticleStateFun.cpp:146-148`；`GlobeFun.h:463-504` | 几何飞行仍按 `position += direction × distance`；出射方向由当前方向和抽得的 $\mu$ 旋转得到。将伴随存储方向解释为正向物理方向的反向时，两方向同时反号而 $\mu$ 不变。 | 源码未明确文档化该方向约定，且没有强各向异性数值互易性测试。 |
| 能群 | `ParticleState.h:1345-1351`；`CheckMgAceBlock.cpp:38-60`；`GetMgCs.cpp:263-298` | 粒子群号为 1-based；容器通常 0-based。群号 1 对应高能，能量数组的存储/定位顺序经过反向映射。 | 群号反向本身不等同于散射核转置，仍需逐对验证。 |
| 权重 | `GetExitState.cpp:186-189`；`SampleColliType.cpp:190-192` | 伴随散射与裂变均乘以由伴随产生截面和正向总截面组成的比值。 | 当局部密度比例 $r\ne1$ 时，分母含 $r$ 而分子不含，形成已确认的 $1/r$ 偏差，见 D.3。 |

### B.3 可证实的伴随定义范围

RMC 没有在该固定源路径中显式声明一条完整的相空间伴随定义。源码能证实的是：它在普通几何飞行的粒子历史框架内，通过反向群对索引、伴随产生截面抽样及权重比，实现一个拟转置的 collision/production kernel。若伴随存储方向定义为正向物理方向的反向，则对方位对称且只依赖散射余弦的 MGACE 条件角核，交换方向并同时反号后 $\mu$ 不变；因此无需以“缺少显式方向反号或 $(-1)^\ell$”为由直接判错。该约定下的目标关系可写为

$$
K^\dagger(g,\Omega\to h,\Omega')
=K(h,-\Omega'\to g,-\Omega)
$$

或与其采用方向变量约定等价的关系。但代码没有用非对称源/响应和强各向异性核做数值检验；同时 D.3 和 F.3 已确认碰撞权重及裂变 nubar 存在错误。因此，本报告既不把未显式角矩转置本身定为缺陷，也不能把完整 $L^\dagger$ 的物理正确性视为已证明。

---

## C. Scattering Transpose Audit

### C.1 初始化阶段：P0 群产生截面

`CDAceData::treatAdjointMaterial()` 在 `InitiateMatAce()` 的多群伴随分支中被调用：

```text
ReadFixedSourceBlock()
  → CDFixedSource::InitiateAll()
  → CDMaterial::InitiateMatAce()
  → CDAceData::treatAdjointMaterial()
```

| 基线 | 文件：函数：行号 | 调用关系 / 实际逻辑 | 支持的结论 |
|---|---|---|---|
| `4d3e1...` | `RMC/src/TreatAdjointMaterial.cpp:34-59` — `CDAceData::treatAdjointMaterial()` | 外层 `jg` 遍历正向入射群，内层 `jh` 遍历正向出射群。每个可达 P0 项累加到 `p_vAdjointCrossSection[neutron][jh]`。 | 正向 $g\to h$ 的 P0 数据被计入伴随当前群 $h$ 的产生总量，构造与群转置一致的列和。 |
| `4d3e1...` | `RMC/src/CheckMgAceBlock.cpp:63-123` — MG P0 布局预处理 | 使用 up/down scatter 边界解码压缩 P0 行；正向每个群行的 P0 总量也在此构建。 | `TreatAdjointMaterial()` 扫描的是与正向 MGACE P0 布局相同的群对序列。 |
| `4d3e1...` | `RMC/src/GetMgExitErgMu.cpp:446-501` — `GetMgAdjNeuExitErgMu()` | 固定伴随当前群 `incidGrp=h`，遍历候选出射群 `exitGrp=g`，以压缩布局 locator 读取正向 $(g\to h)$ 数据，并将抽样结果写为 `p_dExitErg=g`。 | 运行时群选择也按反向群对进行，不是仅将能量数组倒序。 |

由此，P0 群核的静态证据与下式一致：

$$
\Sigma_{s,0}^\dagger(h\to g)=\Sigma_{s,0}(g\to h).
$$

### C.2 群号方向与索引风险

RMC 同时使用两种索引：粒子 `ErgGrp()` 为 1-based，向量访问通常以 `group - 1` 进行；且物理高能群为较小群号，而存储数组顺序被反向映射。`GetExitState.cpp:190-194` 对最大伴随能量的比较依赖这一约定。上述约定在代码中可追溯，因而不能仅因“群号递减/递增”判定错误。

对伴随当前群 $h$，正向前驱群 $g$ 必须满足正向 $g\to h$ 的 up/down-scatter 数据范围：

$$
g\in
\left[
  \max(1,h-NDS),
  \min(NGRP,h+NUS)
\right].
$$

`GetMgAdjNeuExitErgMu()`（`GetMgExitErgMu.cpp:446-461`）将：

```text
minErgGrp = max(0, h - NDS - 1)
exitGrp   = min(NGRP, h + NUS) + 1
```

循环每次先执行 `exitGrp -= 1`，再在 `exitGrp == minErgGrp` 时退出。因此，实际参与扣减的群依次为

$$
\min(NGRP,h+NUS),\ldots,\max(1,h-NDS),
$$

而 `minErgGrp` 恰好位于最小合法群之前。故该 `break` 是哨兵保护，不会漏掉边界群；原草稿将其列为风险属于 off-by-one 误判。非对称群矩阵试验仍有价值，但用途是验证整体转置和统计无偏性，不再用于判断该哨兵是否漏群。

### C.3 P1 与更高阶散射

未找到标准-ACE 固定源伴随路径中独立读取、存储或转置 P1/P2/... 群矩阵的实现，但这不能直接作为角伴随缺失的证据。`NLEG` 与 `ISANG` 在 `Nuclide.h:1943-1961` 中描述的是群对条件角分布的变量数和表示方式；前向路径与伴随路径都在选定群对后读取该群对的条件余弦分布，而不是在运行时使用独立的高阶群转移矩阵。

因此：

- **已证明（静态）**：P0 群积分产生/群抽样存在反向群对机制；
- **已论证（静态、带条件）**：若角核只依赖散射余弦且方位对称，则在反向方向变量下复用正向 $(g\to h)$ 群对的同一条件角分布与伴随 $(h\to g)$ 一致，见 E.2；
- **未证明（数值）**：强各向异性条件角分布下完整前向/伴随响应是否在统计误差内满足互易关系；
- **结论**：不能因未见显式 P1/P2 转置就判定缺陷，也不能只凭静态索引机制把一般相空间互易性升级为 Ready。

---

## D. Collision Sampling Audit

### D.1 实际抽样链

标准-ACE、`ais=OFF` 的固定源历史在 `TrackHistory.cpp:226-275` 中进入：

```text
SampleFreeFlyDist / CalcMacroXS
  → SampleColliNuc
  → CalcColliNucCs
  → TreatImpliCapt
  → SampleColliMT_FixedSrc
  → GetExitState
```

`SampleFreeFlyDist()` 使用当前群的正向宏观总截面抽样自由程：

$$
\ell=-\frac{\ln\xi}{\Sigma_{t,h}^{macro}}.
$$

证据为 `SampleFreeFlyDist.cpp:7-84` 和 `GetMgCs.cpp:6-11`。因此，伴随产生截面**不**用作自由程核；它用于随后伴随偏倚的核素/反应抽样。

### D.2 核素与反应概率

初始化中，对核素 $i$ 的伴随当前群 $h$，代码构造的产生量可概括为：

$$
P_{i,h}^\dagger
=
\sum_g\left[
  \Sigma_{s,i}(g\to h)
  +\chi_i(h)\nu_i(g)\Sigma_{f,i}(g)
\right].
$$

其中散射项与裂变项分别见 `TreatAdjointMaterial.cpp:37-59` 和 `TreatAdjointMaterial.cpp:40-51`。材料中使用基准材料原子份额 $f_i$ 组成：

$$
\bar P_h^\dagger=\sum_i f_iP_{i,h}^\dagger.
$$

`SampleFreeFlyDist.cpp:85-103` 计算该量；`SampleColliNuc.cpp:25-48` 使核素选择概率为：

$$
\Pr(i\mid h)=
\frac{f_iP_{i,h}^\dagger}{\sum_j f_jP_{j,h}^\dagger}.
$$

随后 `SampleColliMT_FixedSrc()`（`SampleColliType.cpp:156-197`）以该核素的伴随产生截面为抽样总量，先按伴随裂变项选择裂变；余量传入伴随散射群/角抽样。对标准路径，这与“核素/反应都按伴随产生 kernel 比例选择”的意图一致。

### D.3 权重修正与 implicit capture

设材料基准总原子密度为 $N_0$，当前栅元或密度网格给出的局部密度比例为 $r$。`CalcMacroXS()` 在多群分支通过 `GetMatNucAtomDen(material, nuclide, p_dDensRatio)` 计算宏观总截面（`SampleFreeFlyDist.cpp:65-83`），因此：

$$
\Sigma_{t,h}^{macro}=rN_0\bar\Sigma_{t,h}.
$$

另一方面，`adjointAccumulatedCrossSection` 使用 `GetMatNucAtomDenFract()` 组合各核素的微观伴随产生量（`SampleFreeFlyDist.cpp:85-103`），`SampleColliNuc()` 的伴随分支也只使用同一基准原子份额（`SampleColliNuc.cpp:25-48`）。公共密度比例在核素选择概率中本可消去，因此这两处不乘 $r$ 并非问题；但它意味着权重公式的分子是与 $r$ 无关的

$$
\bar P_h^\dagger=\sum_i f_iP_{i,h}^\dagger.
$$

散射与裂变分支实际均使用：

$$
w_{\mathrm{code}}'
=w\frac{\bar P_h^\dagger}
      {\Sigma_{t,h}^{macro}/N_0}
=w\frac{\bar P_h^\dagger}{r\bar\Sigma_{t,h}}.
$$

对应代码：

- 裂变：`SampleColliType.cpp:187-192`；
- 散射：`GetExitState.cpp:178-189`；
- 基准总原子密度与归一化份额：`ConvertMatNucDen.cpp:35-63`、`Material.h:33-43,302`。

正确的产生量/总截面比应使共同的局部密度缩放消去：

$$
w_{\mathrm{expected}}'
=w\frac{rN_0\bar P_h^\dagger}
         {rN_0\bar\Sigma_{t,h}}
=w\frac{\bar P_h^\dagger}{\bar\Sigma_{t,h}}.
$$

故 $r\ne1$ 时：

$$
w_{\mathrm{code}}'=\frac{1}{r}w_{\mathrm{expected}}'.
$$

这不是仅在特殊耦合功能中可达的假设。`SetCellGramDens.cpp:7-32` 允许栅元原子密度覆盖材料基准密度并生成非单位 `p_dDensRatio`；`GetLocationInfo.cpp:59-82` 也允许密度网格返回局部质量密度/材料基准质量密度；`FindNextCell.cpp:146-148,351-357` 将该比例写入粒子状态。普通 MG fixed-source adjoint 随后进入上述 `CalcMacroXS()` 和权重分支。

因此，该实现只在 $r=1$ 时退化为预期公式；对非单位局部密度存在标准路径可达、数学后果确定的权重偏差，构成 **E — Defect**。`TreatImpliCapt.cpp:6-12` 对 MG adjoint 直接返回可以避免重复施加正向 non-absorption 权重，但不能修正此 $1/r$ 因子。

### D.4 碰撞审查结论

已确认：标准路径用正向总截面推进飞行，用伴随产生截面选择核素/反应，并在散射和裂变两支应用同一修正比。核素/反应选择概率的结构与重要性抽样意图相容；在 $r=1$ 的受限条件下，权重比也退化为预期形式。

但对 $r\ne1$，代码将含局部比例的宏观总截面除以不含该比例的基准材料总原子密度，明确留下 $1/r$。这已超出“尚无数值证据”的范围，是可由执行链和公式直接确定的错误。即使限定 $r=1$，混合材料、非对称群核和所有碰撞分支的数值无偏性仍未由前向/伴随双线性统计验证证明。

---

## E. Angular Treatment Audit

### E.1 代码实际行为

当 `GetMgAdjNeuExitErgMu()` 已通过反向群对选得伴随出射群后，它用该正向 $(g\to h)$ 群对的角数据抽样 `MuLab`：

- 无角分布 locator 时，使用各向同性 $\mu=2\xi-1$：`GetMgExitErgMu.cpp:464-471`；
- 有数据时，使用 MGACE 的 equiprobable cosine bins 或 discrete cosines：`GetMgExitErgMu.cpp:472-496`；
- `GetExitState.cpp:178-189` 随后调用 `CDGlobeFun::RotateDirection(MuLab, oldDir, exitDir, ORNG)`；
- `RotateDirection()` 以 `MuLab` 作为相对于当前方向的夹角余弦，方位均匀：`GlobeFun.h:463-504`。

换言之，RMC 在群对转置后复用该正向群对的条件角分布，并直接围绕伴随粒子的当前飞行方向旋转。

### E.2 伴随角核是否已证明

RMC 让伴随粒子沿其存储方向做普通几何飞行。若把这一存储方向解释为对应正向物理方向的反向，即

$$
\widetilde\Omega=-\Omega,
$$

则伴随转置交换正向入射/出射方向后，两个物理方向同时反号。对 MGACE 此处使用的方位对称条件角核，散射余弦保持不变：

$$
\widetilde\Omega_{\mathrm{in}}\cdot
\widetilde\Omega_{\mathrm{out}}
=
(-\Omega_{\mathrm{out}})\cdot(-\Omega_{\mathrm{in}})
=
\Omega_{\mathrm{out}}\cdot\Omega_{\mathrm{in}}
=\mu.
$$

因此，在群对已经从正向 $(g\to h)$ 反向为伴随 $(h\to g)$ 后，复用该正向群对的条件 $\mu$ 分布并围绕当前伴随方向旋转，是与上述反向方向约定一致的；程序无需仅为此额外显式应用 $\Omega\mapsto-\Omega$ 或 Legendre $(-1)^\ell$。原草稿将“未见显式 parity 处理”作为一般风险，忽略了方向变量定义，判断过强。

但源码没有以数学文档显式声明该方向约定，也没有强各向异性、非对称源/响应几何的数值互易性测试。因此本节结论是：**角核机制在方位对称、仅依赖 $\mu$ 的 MGACE 表示下静态上自洽，但完整数值伴随性仍为 Verify**。各向同性 case 无法提供有区分力的通过证据。

### E.3 一变量负余弦分支的可疑不一致

前向与伴随的 `nNLEG == 1` 分支不相同：

```cpp
// forward, GetMgExitErgMu.cpp:139-143
// XSS[nPndLoc] < 0
dExitMu = -1 + 2 * Rand() * (1 + XSS[nPndLoc]);

// adjoint, GetMgExitErgMu.cpp:482-486
// XSS[lx] < 0
MuLab = -1 + 2 * Rand() * (1 - XSS[lx]);
```

若存储值为 $-0.5$，伴随表达式的输出范围是 $[-1,2]$，可产生 $\mu>1$；之后未见该函数在传入 `RotateDirection()` 前作 $[-1,1]$ 检查。该源码分支差异是确定的，但尚未确认：

1. 部署 MGACE 库是否会使该伴随分支可达；
2. 存储值的精确定义是否与表面符号解释一致；
3. 该值实际到达 `RotateDirection()` 时是否造成可观测数值错误。

因此将其记录为**高优先级可能问题（possible issue / Verify）**，不是本报告中的已证实 E — Defect。需要数据驱动的 reachability 与输出验证。

---

## F. Fission Treatment Audit

### F.1 转置裂变核与群选择

初始化时，`TreatAdjointMaterial.cpp:40-51` 对每个正向前驱群 $g$ 形成 $\nu(g)\Sigma_f(g)$，累加为伴随裂变总量，并对伴随当前群 $h$ 乘以 $\chi(h)$。`SampleColliMT_FixedSrc()` 再：

1. 以
   $$
   \chi(h)\sum_g\nu(g)\Sigma_f(g)
   $$
   从该核素的伴随产生量中选择裂变（`SampleColliType.cpp:164-167`）；
2. 以 $\nu(g)\Sigma_f(g)$ 从前驱群中选择 `exitGrp`（`SampleColliType.cpp:168-189`）。

在结构上，这对应：

$$
K_f^\dagger(h\to g)=\chi(h)\nu(g)\Sigma_f(g).
$$

这是静态源码支持的伴随裂变群核意图。

### F.2 后继粒子、能群与 bank

`GetExitState.cpp:169-177` 在伴随裂变后调用 `TreatFission()` 并终止母粒子。`CDFixedSource::GetFissionNeuState()` 中：

- 若粒子为伴随粒子，后继数被强制为 1（`GetFissionNeuState.cpp:550-572`）；
- 多群分支调用 `GetMgFisErgDir()` 取得裂变方向，但预先保存的伴随选择群会恢复，故前向 $\chi$ 能量抽样结果不覆盖已选 $\nu\Sigma_f$ 前驱群（`GetFissionNeuState.cpp:721-728`）；
- 一个携带当前修正权重的中子被压入 fixed-source bank（`GetFissionNeuState.cpp:735-736`）。

这与用一个加权后继粒子表示转置裂变产生核的做法在结构上相符；但尚未由可裂变算例验证群分布、权重和 bank 行为。

### F.3 `JXS[4]` 与 `GetMgNeuLNU()`

存在可追溯且在本地核数据中可达的 nubar 数据路径不一致：

| 位置 | nubar locator | 影响 |
|---|---|---|
| `TreatAdjointMaterial.cpp:40-46` | `GetMgNeuLNU(i)` | 初始化构造伴随裂变总产生量 $\sum_g\nu(g)\Sigma_f(g)$ 时使用。 |
| `GetMgCs.cpp:78-97` | `GetMgNeuLNU()` | 通用 `GetMgNucNubar()` 也使用这一 locator。 |
| `SampleColliType.cpp:168-176` | 直接 `JXS[4] + exitGrp` | 伴随裂变前驱群按 $\nu(g)\Sigma_f(g)$ 抽样时使用；相邻注释保留 `GetMgNeuLNU()` 替代式与 `todo`。 |
| `Nuclide.cpp:28-35` | `GetMgNeuLNU()` | 当 `NXS[10]=NNUBAR>1` 时返回 `JXS[4]+NGRP`，否则返回 `JXS[4]`。 |
| `CalcMXSTable.cpp:61,87-93` | MGACE 写出约定 | `NNUBAR=1` 被明确标注为 total nubar；`NNUBAR=2` 时 nubar block 长度为 `2*NGRP`。 |

`GetMgNeuLNU()` 在双表情况下有意跳过第一组，令通常的 nubar getter 和伴随初始化读取第二组 total nubar；运行时抽样则硬编码第一组 prompt nubar。两处实现的物理量因而分别为：

$$
P_{f,h}^{\dagger,\mathrm{init}}
=\chi(h)\sum_g\nu_{total}(g)\Sigma_f(g),
$$

和

$$
\Pr_{\mathrm{runtime}}(g\mid h,\mathrm{fission})
\propto\nu_{prompt}(g)\Sigma_f(g).
$$

这会使运行时群选择的归一化核与初始化时用于选择裂变、计算权重的总产生核不一致。只有在 `NNUBAR<=1`，或双表各群 prompt/total 比例恰为群无关常数时，群分布才可能偶然不受影响；一般情况下不成立。

可达性不只是格式上的假设。本地核库 `/home/silver/NucXS_Library/RMC_DATA/xsdir:263-270` 将 `10001.01m` 等多个核素登记到 `multigroup/c5g7td`，因此它是当前部署索引中的可选 MGACE 数据，而非孤立文件。该文件首张 7 群裂变表 `10001.01m` 明确给出 `NXS[10]=2`、`JXS[4]=29`、`JXS[5]=43=29+2*7`。其第一组 nubar 从 `2.34389` 开始，第二组从 `2.34542` 开始，数值不同且后者略大。RMC 的 standard getter 在双表时跳到第二组；独立的 HDF5 多群路径分别读取 `nu_prompt` 和 `nu_total`，且通用 getter 在 total 存在时明确优先 total（`ReadFissionNu.cpp:79-93`、`GetMgCs.cpp:27-35`），与第二组作为 total 的解释相互印证。该表同时具有非零 fission 与 $\chi$ block，能够进入 F.1 的标准 MGACE fixed-source adjoint 分支。

更重要的是，缺陷结论不必完全依赖 prompt/total 标签。对该实际表：

$$
S_1=\sum_g\Sigma_f(g)\nu_1(g)=0.71975438088,
\qquad
S_2=\sum_g\Sigma_f(g)\nu_2(g)=0.719776674648.
$$

初始化形成的裂变产生总量使用 $S_2$，运行时进入裂变分支后却按第一组核逐群从同一阈值扣减。由于 $S_2>S_1$，差额 $S_2-S_1=2.22937680699\times10^{-5}$ 无法由第一组核扣尽，并被循环末群退出条件归入末群；代码未对这种提议核/目标核差异施加重要性权重补偿。故即使把两张表暂记为“第一组”和“第二组”，初始化与运行时使用不同归一化核也已经足以判错。

因此该项满足：标准路径可达、读取位置确定、两张表数值不同、初始化与抽样所用核不同。它构成第二项 **E — Defect**，而非仅待格式负责人解释的 Verify 风险。本任务只记录缺陷，不授权将 `JXS[4]` 改为 `GetMgNeuLNU()` 或作任何其它源码修复。

### F.4 delayed 数据边界

上述结论针对 MGACE nubar 双表中 prompt/total 的选择不一致。标准 ACE 的显式 delayed nubar getter 由 `JXS[24]` 控制（`GetTotNu.cpp:100-119`），locator 为零时返回 0。尚未证明固定源 MG adjoint 路径对显式 delayed precursor/family 做了完整转置处理；但没有证据表明本次标准路径必然进入该分支，因此 delayed 处理保持为范围明确的 Verify 项，不作为本次 E 分类的额外依据。

---

## G. Existing Verification Evidence

### G.1 已有资产

与本路径直接相关的回归资产为：

| 资产 | 证据 | 能说明什么 | 不能说明什么 |
|---|---|---|---|
| 输入 | `RMC/tests/fixed_source_adjoint/inp:13-24` | 包含 H-1/O-16、`MGACE erggrp=30 12`、`FIXEDSOURCE`、`ADJOINT ADJOINTCALCULATION=1`，共 1,000,000 histories。 | 不含可裂变核素。 |
| 注册 | `RMC/tests/fixed_source_adjoint/CMakeLists.txt:1-9`；`RMC/tests/CMakeLists.txt:117`；`RMC/tests/configure.yaml:1516-1524` | 固定源多群伴随路径曾被登记为 serial/MPI/OpenMP、Linux/Windows 回归资产。 | 注册不等于当前 commit 的运行结果或数学正确性证明。 |
| 参考结果 | `RMC/tests/fixed_source_adjoint/reference_result:38` | 参考为 30 群 neutron cell track-length flux；总值 `2.1335E-01`，RE `8.2455E-03`。 | 参考输出不覆盖裂变、多 nubar、非对称散射互易性或各向异性方向互易性。 |

其它名称中含 `adjoint` 的测试（例如 `tests/fission_matrix_adjoint_flux/`）使用 `CRITICALITY` 中的 `MGAdjFisMatrix`，不是此处 `MGACE + FIXEDSOURCE + ADJOINTCALCULATION` 的直接验证，不计入本结论。

### G.2 本次已验证与未验证

**已验证（源码/资产层面）**：

- 默认 `ais=OFF` 下固定源多群伴随中子调用链可达；
- P0 群对反向索引、伴随产生核素选择、权重补偿和一个裂变 bank 后继的机制存在；`minErgGrp` 是合法群范围外的哨兵，不漏边界群；
- 当局部密度比例 $r\ne1$ 时，散射与裂变权重相对预期结果多出 $1/r$；
- 当 `NNUBAR>1` 时，伴随初始化读取第二组 total nubar，而运行时裂变前驱群抽样读取第一组 prompt nubar；本地 `c5g7td` 数据使该分支实际可达；
- 直接相关回归输入、注册与参考 tally 文件存在。

**未验证（当前 RMC SHA 的运行/物理层面）**：

- 当前 `4d3e1...` 是否可构建并通过现有固定源伴随回归；
- 非对称散射矩阵下的离散伴随内积关系；
- 一般各向异性条件角分布下的方向互易性；
- 裂变 $\chi\nu\Sigma_f$ 核、parent/child group、权重和 bank 行为；
- 显式 delayed nubar/precursor 路径的适用范围与完整伴随处理；
- 即使限定 $r=1$ 且 `NNUBAR<=1`，混合材料碰撞估计器的数值无偏性；
- AIS/HDF5 路径。

本次没有可执行 RMC 二进制可用于验证；故未运行 CTest、未产生运行日志，也未改写任何 reference result。

---

## H. Risk List

| 类别 | 风险 | 证据 | 当前判断 | 需要的最小证据 |
|---|---|---|---|---|
| **Confirmed defect** | 非单位局部密度下，伴随权重相对正确产生量/总截面比多出 $1/r$。 | `SampleFreeFlyDist.cpp:65-103`；`SampleColliNuc.cpp:25-48`；`GetExitState.cpp:186-189`；`SampleColliType.cpp:187-192`；`SetCellGramDens.cpp:7-32`；`GetLocationInfo.cpp:59-82` | 标准路径可达，代数后果确定；完整能力判为 E。 | Stage 3 另立修复任务；修复前用相同材料、不同 $r$ 的响应缩放测试固化复现。 |
| **Confirmed defect** | `NNUBAR>1` 时，初始化/权重核使用 total nubar，运行时裂变前驱群抽样使用 prompt nubar。 | `TreatAdjointMaterial.cpp:40-46`；`SampleColliType.cpp:168-176`；`Nuclide.cpp:28-35`；`CalcMXSTable.cpp:61,87-93`；本地 `c5g7td` | 双表 locator 与数值均不同，裂变表可达；完整能力判为 E。 | Stage 3 另立修复任务；修复前记录双表 case 的初始化核、抽样群频数和权重。 |
| Possible issue | 一变量、负余弦的伴随角抽样表达式与前向表达式不同，且可能给出 $\mu>1$。 | `GetMgExitErgMu.cpp:139-143` 对比 `:482-486` | 源码分支差异确定；其可达性和端到端物理后果未证实。 | 使用实际 MGACE 数据或最小构造数据验证分支可达性、$\mu$ 范围及方向统计。 |
| Unverified physics requirement | 在反向方向变量、方位对称且仅依赖 $\mu$ 的 MGACE 条件角核下，复用同一 $\mu$ 分布静态自洽；但没有数值互易性证明。 | `GetMgExitErgMu.cpp:462-501`；`GetExitState.cpp:178-189`；`GlobeFun.h:463-504` | 不能因未显式转置 P1/P2 判错，也不能默认一般各向异性响应已通过。 | 强各向异性、非对称源/响应几何的方向互易性测试。 |
| Unverified estimator requirement | 即使限定 $r=1$、`NNUBAR<=1`，碰撞估计器仍没有数值无偏性验证。 | `SampleFreeFlyDist.cpp:64-103`；`SampleColliNuc.cpp:25-48`；`GetExitState.cpp:186-189` | 受限子域静态上合理，数值上未证明。 | 单核素与混合材料的已知解/前向-伴随双线性比较。 |
| Scope / coverage gap | 显式 delayed nubar 由 `JXS[24]` 控制，但固定源 MG adjoint 的 delayed precursor/family 伴随处理未闭合。 | `GetTotNu.cpp:100-119`；F.4 | 尚未证明标准路径数据使其可达，不作为本次 E 的依据。 | 带显式 delayed 数据的可裂变 MGACE case 与调用链记录。 |
| Coverage gap | 现有回归为 H/O 非裂变，且未在当前 SHA 运行。 | `tests/fixed_source_adjoint/inp:13-24` | 测试资产不能替代实际运行或裂变/角核验证。 | 在记录基线下运行，保留原始输出，不更新 reference。 |

本表中的 “Possible issue” 与 “Open issue” 不授权在 F02-B 中修复。任何经后续验证确认的缺陷，都必须在人工审阅后按 Stage 3 另立修复任务处理。

---

## I. Final Classification

**E — Defect（完整标准 MGACE fixed-source adjoint 能力）**

默认 standard ACE、`ais=OFF` 的 RMC 固定源多群伴随中子路径不是空壳：P0 群对转置的构造与运行时反向选择均可由源码追溯；碰撞抽样使用伴随产生量；裂变代码也具有 $\chi(h)\nu\Sigma_f(g)$ 的转置结构、单一加权后继及 fixed-source bank 链。`minErgGrp` 不漏合法群，反向方向变量下复用同一条件 $\mu$ 分布也不能仅凭“无显式 P1/P2 转置”判错。

然而，本轮独立复核建立了两项确定性错误：

1. 对普通栅元密度覆盖或密度网格产生的 $r\ne1$，自由飞行总截面含 $r$，而权重归一化使用基准材料总原子密度，导致散射和裂变权重多出 $1/r$；
2. 对 `NNUBAR>1`，初始化和通用 getter 使用第二组 total nubar，运行时伴随裂变前驱群抽样却硬编码第一组 prompt nubar；本地裂变 MGACE 数据证明该分支可达且两组数值不同。

任一项都足以使完整能力不能被接受为物理正确，因此主分类必须为 **E — Defect**，不能因已有 H/O reference 或其余静态机制合理而保持 C。

对明确排除两个缺陷触发条件的受限子域——局部密度比例恒为 $r=1$ 且所有裂变核素 `NNUBAR<=1`——本报告不宣称已发现同等级确定性错误，但该子域仍为 **C — Verify**：当前 SHA 没有运行结果，现有 H/O 回归不覆盖裂变，没有非对称散射内积试验，也没有强各向异性方向互易性验证；负余弦分支仍待 reachability 检查。AIS/HDF5 不在本结论中放行。

因此，RMC 当前多群伴随输运**不能作为已被证明可信的 MLVR 伴随求解基础**。本结论只触发治理上的 Stage 3 缺陷立项要求；不授权在 F02-B 内修改源码、更新基准、开始 F03 或设计 WW 接口。

---

## J. Recommended Minimal Verification

以下建议只定义验证目标，不在本 F02-B 中执行、不修改 RMC 源码、也不更新任何 reference/benchmark。未来执行时须记录 RMC branch/SHA、构建配置、核数据版本、随机种子、完整命令、退出码、stdout/stderr、重要 tally 和未覆盖项；原始输出原样保存到本任务 `logs/` 目录。

### Test 1 — 当前基线的固定源回归冒烟

1. 在记录的 `4d3e1...` SHA 以默认 `ais=OFF` 构建；
2. 运行现有 `test_fixed_source_adjoint`；
3. 保存产物与 `reference_result` 的 diff、退出码和原始标准输出；
4. **不得**为了通过而更新 `reference_result`。

目的：仅证明当前基线的既有非裂变调用链可执行，不用作完整伴随物理正确性的判据。

### Test 2 — 两群非对称散射离散伴随内积

构造均匀两群材料，使：

$$
\Sigma_s(1\to2)\ne\Sigma_s(2\to1).
$$

选择可人工核算的前向源/响应与伴随源/响应，比较：

$$
\langle\psi^\dagger,L\psi\rangle
\approx
\langle L^\dagger\psi^\dagger,\psi\rangle
$$

是否在 Monte Carlo 统计误差内一致。除总量外，必须 tally 每个群转移或等价群响应，以验证 P0 转置和群号方向。`minErgGrp` 已由静态范围推导确认为哨兵，本测试不再承担判断该项是否漏群的任务。对称矩阵不可替代此试验，因为会掩盖转置错误。

### Test 3 — 各向异性角核互易性

选择明显非各向同性的群对角分布，以及不对称的空间源/响应几何。分别测量前向与伴随方向相关响应，检验采用的方向变量是否满足离散相空间互易性。若能得到一变量负余弦分支的数据，额外记录所有抽样 $\mu$ 的范围及对应方向统计，直接审查 E.3 的可能问题。各向同性 case 不构成通过证据。

### Test 4 — 伴随裂变与 nubar 路径

使用最小可裂变多群材料，至少覆盖：

1. 单一 nubar 表；
2. `NNUBAR > 1` 的本地 `c5g7td` 或等价双表数据。

逐项检查：裂变发生概率、伴随 parent/child group 分布、权重乘子、每次伴随裂变恰有一个 bank 后继、bank 后历史继续输运。对双表 case，分别按第一组 prompt 与第二组 total nubar 计算理论群分布，记录初始化读取 locator、运行时读取 locator 和抽样频数，固化 F.3 缺陷的数值复现。若数据还含显式 delayed 信息，另行记录 `JXS[24]` 和 precursor/family 路径，不与 prompt/total 缺陷混为一个判据。

### Test 5 — 局部密度比例不变性

构造材料组成和几何保持不变、仅局部密度比例分别为 $r=1$、$r=1/2$、$r=2$ 的最小固定源 MG adjoint case。保存每次碰撞前后的：

- `p_dDensRatio`；
- `p_dMacroTotCs` 与 `p_dMatAtomDen`；
- `adjointAccumulatedCrossSection[h]`；
- 散射/裂变权重乘子；
- 最终前向/伴随双线性响应。

代码现状预期权重乘子相对 $r=1$ 分别出现 $2$ 和 $1/2$ 的非物理缩放。该测试用于固化 D.3 缺陷复现和未来 Stage 3 修复后的回归判据，不用于在 F02-B 内试改源码或更新 reference。

### 验证后的流程边界

验证结果只能用于更新 F02-B 的证据、受限子域结论和未来修复验收标准。两项已确认缺陷必须经过人工决策后分别或合并另立 Stage 3 修复任务；不得在本任务中修改 `RMC/`、设计 MLVR 接口、开始 F03 或推进 WW 实现。
