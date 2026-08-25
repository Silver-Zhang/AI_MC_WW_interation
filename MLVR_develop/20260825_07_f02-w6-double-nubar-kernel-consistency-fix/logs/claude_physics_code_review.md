# Claude 物理正确性与代码开发独立审核原文

> 收到日期：2026-08-25
> 保存说明：以下内容为用户提供的 Claude 审核结果，按原结论归档；未作为 RMC 修改授权。

## 1. Findings

**未发现阻止 W6 标记为“已修复”的问题。** 本次修复位于实际控制 standard MGACE fixed-source neutron adjoint 裂变前驱群抽样的位置，并使它与初始化、通用 nubar getter 采用同一 locator。以下仍有验证缺口，但不阻断 W6 根因关闭。

| 严重度 | 发现 | 证据与影响 | 建议 |
|---|---|---|---|
| 高（已修复） | 修复前的 W6 确为同一伴随裂变过程混用两套核。修复后该直接不一致已消除。 | `SampleColliType.cpp:164-174` 的裂变阈值来自初始化构造的总产生量；现在逐群扣减使用 `GetMgNeuLNU(nNuc)`。初始化在 `TreatAdjointMaterial.cpp:40-46` 也使用该 getter；通用 getter 在 `GetMgCs.cpp:85-90` 同样使用它。 | 可以关闭 W6；保留可裂变响应级验证为后续工作。 |
| 中（验证缺口） | `verify_kernel_consistency.py` 证明 locator 与解析公式一致，但“runtime_kernel”是脚本按同一 getter 重新计算的，不是从执行轨迹提取。 | 脚本在第 61–65 行同时把 `expected_kernel` 和 `runtime_kernel` 填为 `sigma_f * nubar`；它主要是**源码表达式存在性 + 核数据 oracle**，不是独立动态频数证明。 | 保留为确定性代码/数据一致性验证；不要将其表述为对运行时群频数的直接测量。 |
| 中（残余风险） | 修复没有新增防护来处理异常 MGACE 数据中的零/负 `χ`、`νΣ_f` 或累计残差。 | `SampleColliType.cpp:168-174` 从 `sampleFission / χ(h)` 开始逐群扣减；若 `χ(h)=0` 而裂变仍被选中，会有除零风险。正常数据流应使 `sampleFission=0`，但代码没有显式 guard。 | 不属于 W6 回归；在核数据健壮性或可裂变扩展验证时单独覆盖。 |
| 低（文案边界） | “10,000 histories / 2,487 bank 后继”不能证明概率分布正确。 | 动态重放仅证实修复后双表裂变路径可初始化、发生 bank 后继并正常结束；部署数据的效应量很小，低统计频数不具备分布检验能力。 | 保持当前档案的表述：它是可达性/稳定性证据，不是 W6 分布误差量化。 |

### 代码范围检查

- 当前工作树有三个未提交 RMC 文件：
  - `src/GetExitState.cpp`：W5 密度权重修复；
  - `src/InitiateAll.cpp`：W7 photon 群初始化保护；
  - `src/SampleColliType.cpp`：W6 locator 修复，以及同一文件内的 W5 权重修复。
- W6 本身的生产改动只有：

```cpp
XSS[GetMgNeuLNU(nNuc) + exitGrp]
```

替换旧的：

```cpp
XSS[JXS[4] + exitGrp]
```

- 全部 standard MGACE neutron-adjoint 相关 `JXS[4]` / `GetMgNeuLNU` 搜索后，未发现第二处仍用 `JXS[4]` 进行 fixed-source adjoint 裂变前驱群抽样的路径。
- 正向多群路径位于 `p_bIsAdjointParticle == false` 的独立分支，不经过本修复位置。

---

## 2. Physical derivation

令正向多群裂变核为：

$$
F(g\to h)=\nu(g)\Sigma_f(g)\chi(h).
$$

其群空间伴随应为：

$$
F^\dagger(h\to g)=\chi(h)\nu(g)\Sigma_f(g).
$$

对当前伴随群 $h$，定义：

$$
S_\nu=\sum_g \nu(g)\Sigma_f(g).
$$

则初始化阶段应构造：

$$
P_f^\dagger(h)=\chi(h)S_\nu.
$$

这正是 `TreatAdjointMaterial.cpp:40-51` 的结构：

1. 对每个前驱群 $g$，形成 $\nu(g)\Sigma_f(g)$；
2. 求和得到 `p_vAdjointFissionCrossSection`；
3. 对每个当前伴随群 $h$，乘以 $\chi(h)$ 并加入伴随产生截面。

运行时：

1. 从该核素的伴随产生截面中选择反应；
2. 裂变概率由 $P_f^\dagger(h)$ 决定；
3. 条件于裂变，前驱群应按

$$
p(g\mid h,\mathrm{fission})=
\frac{\nu(g)\Sigma_f(g)}{\sum_{g'}\nu(g')\Sigma_f(g')}
$$

抽样；
4. 裂变后继保留这个前驱群，并以一个加权粒子加入 fixed-source bank。

修复后，初始化和运行时均使用：

$$
\nu(g)=\nu_{\mathrm{getter}}(g),
$$

即 `GetMgNeuLNU()` 的 nubar block。

### total nubar 语义

在 RMC 当前 standard MGACE 约定中：

- `Nuclide.cpp:28-35` 表明：
  - `NNUBAR <= 1`：getter 返回 `JXS[4]`；
  - `NNUBAR > 1`：getter 返回 `JXS[4] + NGRP`，即第二个 nubar block。
- RMC 的 MGACE 写出逻辑将单表 `NNUBAR=1` 标为 total nubar。
- HDF5 getter 也在 total 存在时优先选择 total，只在 total 缺失时退回 prompt。

因此，在当前 RMC 的 standard MGACE 语义下，修复统一采用 **total nubar** 是内部一致的。

### 逐群索引与末群残差

RMC 的 `XSS` 是 1-based 填充：读取时数据从 `XSS[1]` 写起，见 `ReadAceData.cpp:485-511`。

运行时 `exitGrp` 从 0 开始，读取：

$$
\Sigma_f(g)\nu(g)
\quad\leftrightarrow\quad
\texttt{XSS[LFIS + exitGrp] × XSS[LNU + exitGrp]}.
$$

修复前，随机阈值来自 second/total block，而逐群扣减来自 first/prompt block；两者总和不相等时，残余会落到最后一群。修复后两处使用同一 total block，因此在正常正截面数据上累计量与阈值来自同一核，旧的“最后群吸收不匹配残余”问题消失。

### 权重与银行

- W6 修复未改变裂变权重公式，只使群选择核与该公式所依赖的初始化核一致。
- 当前 W5 修复已让分母使用当前位置总原子密度，因此局部密度因子在裂变权重比中抵消。
- `GetFissionNeuState.cpp:550-736` 对伴随裂变固定一个后继，保持此前选定群，并将当前权重带入 fixed-source bank。W6 修改不改变这段行为。

### `NNUBAR=1`

行为保持不变：

$$
\texttt{GetMgNeuLNU()}=\texttt{JXS[4]}.
$$

因此单表数据仍读取完全相同位置。任务 oracle 的显式检查也得到 `single_table_locator=29 unchanged=True`。

---

## 3. Validation assessment

| 验证 | 审核判断 | 说明 |
|---|---|---|
| 构建 | 有效 | 记录显示 RMC target 成功构建。 |
| 原 fixed-source regression | 有效但范围有限 | 1/1 通过、reference SHA256 未变；该回归是 H/O 非裂变，不能直接覆盖 W6。 |
| 修复后核 oracle | 有效的静态确定性检查 | `10001.01m`、`NNUBAR=2`、first locator 29、getter locator 36；七个群的 total kernel 和运行时应使用 kernel 差均为 0。它正确确认源码定位表达式和核数据解析的一致性。 |
| Python ACE 解析 | 正确 | 解析器明确使用 1-based `xss_at()`；RMC 也从 `XSS[1]` 读取。对 `JXS[4]` 的 Python tuple 映射为零基 `jxs[3]`，与 RMC 语义相符。 |
| pre/post CSV | 支持 W6 修复 | pre CSV 保留修复前 first/second 不一致和末群残余效应；post CSV 显示 total 核逐群一致。注意：post CSV 是 deterministic oracle 输出，不是动态样本统计。 |
| 10,000 histories / 2,487 bank successors | 有效的可达性与稳定性证据 | 证明修复后真双表、可裂变、neutron-only 路径能完成，且确实产生 bank 后继；不证明其群频数在统计上匹配目标分布。 |
| reference、核数据与基线 | 保持不变 | reference SHA256 与任务记录一致；`c5g7td` SHA256 与任务记录一致；分支和 SHA 保持原基线。 |
| W6 动态分布误差 | 未验证 | 原因合理：效应极小，V3 仅给出约 $7.33\times10^7$ 后继的正态近似功效量级。未见把此数字误称为精确保证。 |

---

## 4. Classification

### W6

> **建议：已修复。**

理由：

- 根因已定位在真正控制 fixed-source MGACE adjoint 裂变前驱群抽样的位置；
- 修复使初始化、通用 getter 和运行时抽样使用同一 total nubar locator；
- `NNUBAR=1` 保持原行为；
- 逐群 kernel / probability oracle 为零差；
- 真双表裂变 bank 路径已动态完成并正常退出；
- 没有发现残留的同类 standard MGACE adjoint 前驱群 `JXS[4]` 直接读取。

### F02-B

> **建议：C — Verify。**

从 **E — Defect** 调整为 **C — Verify** 合理：W5/W6/W7 的已确认根因均已处理并有针对性证据，但尚未覆盖完整物理适用域。

达到 **A — Ready** 前至少还需要：

1. 可裂变材料上的最终响应或前向—伴随响应级验证；
2. 混合材料碰撞估计器验证；
3. 一般非均匀密度 mesh 验证；
4. 强各向异性角核与非对称空间源/响应验证；
5. 更多几何、群对和边界条件；
6. delayed、AIS/HDF5、continuous-energy 等明确的独立范围审查。

---

## 5. Open questions / residual risks

- **Delayed / precursor：未验证。** total nubar 的选择不自动证明显式 delayed family 或 precursor 的伴随转置已正确。
- **Prompt-only 模型：未实现为可选语义。** 当前 RMC 内部语义统一到 total；若未来要提供 prompt-only 物理模型，需要让初始化、概率、群抽样、权重和 delayed 处理成套一致，不可只改单点。
- **AIS/HDF5：未受本 W6 standard ACE 改动影响，但仍需单独审查。** HDF5 已有 total 优先 getter 不等于其完整伴随裂变路径已验证。
- **Continuous energy：不受本修复覆盖。**
- **异常核数据健壮性：未验证。** 零/负 $\chi$、负 $\nu\Sigma_f$、不规范 nubar block、或浮点累计残差缺少专用保护和测试。
- **可裂变最终响应：未验证。** 当前动态运行只确认 bank 可达、无崩溃和无明显 NaN/Inf，不替代物理响应验证。
- **文档状态：审核范围内未发现过度表述。** 知识库和物理导读均将 W6 写为已修复，同时保留“动态频数未测”“可裂变最终响应未验证”“整体 C 而非 A”的边界；该表述合理。
