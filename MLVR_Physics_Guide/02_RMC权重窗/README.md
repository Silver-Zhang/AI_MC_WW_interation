# RMC 权重窗（Weight Window）

## 一句话结论

RMC 当前存在 cell-based、mesh-based、MCNP 格式 `WWINP`、roulette 和 splitting 等权重窗代码路径，但截至当前审计快照，不能把它们整体视为可直接复用的可靠基础能力。

F08 源码审查将当前状态暂定为：

- **E — Defect**：已发现若干代码级参数、索引、状态复制和并行数据布局问题；
- **D — Integration issue**：adjoint + WW 的组合边界没有明确支持契约或输入保护；
- **C — Verify**：cell WWE 首能群边界、`WWINP` 截断输入、track mesh 事件语义等仍需针对性复现。

这不是说所有正常输入都会失败，而是说“简单案例可以运行”不足以证明权重窗实现满足第一版 MLVR 的物理要求。

## 1. 权重窗改变什么，不能改变什么

在模拟中，粒子权重 $w$ 表示该粒子代表的物理粒子数或统计贡献。权重窗的目标是：

- 在重要区域增加粒子数、降低单粒子权重；
- 在不重要区域减少粒子数、提高存活粒子权重；
- 在不改变 tally 期望值的前提下改善方差。

因此，权重窗不能改变输运方程、材料截面、几何边界或响应的物理定义。它只能改变同一随机过程的抽样表示。

### 1.1 Roulette 的无偏关系

如果输入粒子权重低于下限，roulette 应满足

$$
P(\text{survive}) \times w_{\text{survive}} = w_{\text{in}}.
$$

RMC 的基本实现采用

$$
P(\text{survive}) = \frac{w_{\text{in}}}{w_{\text{survive}}},
$$

存活时把粒子权重提升为 $w_{\text{survive}}$，死亡时权重为零。只要概率在 $[0,1]$ 且存活权重为正，该变换在期望上是无偏的。

### 1.2 Splitting 的无偏关系

如果粒子权重高于上限，粒子被拆成 $n$ 个状态相同的后代，每个后代权重应满足

$$
\sum_{i=1}^{n} w_i = w_{\text{in}}.
$$

RMC 的 bank 设计是保留一个当前粒子，并把其余 $n-1$ 个复制体放入粒子 bank。因此，审查不能只看 bank 中新增了多少粒子，还必须检查：

- 当前粒子是否保留；
- bank 复制体是否完整；
- 所有副本的权重、位置、方向、能量、时间和物理属性是否一致；
- 后续取出 bank 粒子时是否仍位于正确的空间和能群。

## 2. RMC 当前执行链路

### 2.1 Cell WW

cell WW 的基本链路为：

1. 输入 `WWE`、`WWN`、`WWP`；
2. 为 cell 保存能量边界和 lower bound；
3. 根据 `WUPN`、`WSURVN` 构造 upper bound 和 survival weight；
4. 粒子穿越 cell 表面后查找新 cell 与当前能量区间；
5. 调用 roulette/splitting；
6. 将 split 副本放入固定源粒子 bank，继续输运当前粒子。

源码入口主要位于 [DoWeightWindow.cpp](../../RMC/src/DoWeightWindow.cpp)、[RayTracking.cpp](../../RMC/src/RayTracking.cpp) 和 [ReadWeightWindow.cpp](../../RMC/src/ReadWeightWindow.cpp)。

### 2.2 Mesh WW

mesh WW 通过空间 mesh index 和能量 bin 查找权窗参数。当前实现包括：

- point mesh：在粒子位置处查找 mesh；
- track mesh：将一段飞行轨迹切成多个 mesh segment；
- MCNP `WWINP`：读取外部网格和 lower bound；
- MPI shared mesh：把 mesh 参数展平后放入共享内存。

源码入口主要位于 [DoMeshWeightWindow.cpp](../../RMC/src/DoMeshWeightWindow.cpp)、[WeightWindows.cpp](../../RMC/src/WeightWindows.cpp)、[MeshFun.cpp](../../RMC/src/MeshFun.cpp) 和 [ReadMCNPWwinpFile.cpp](../../RMC/src/ReadMCNPWwinpFile.cpp)。

### 2.3 物理事件时序

权重窗操作发生在输运事件之间，而不是独立于输运过程的后处理：

- cell neutron WW 当前主要在穿面后处理；
- mesh track WW 在轨迹段处理中逐段处理；
- point mesh WW 按当前实现的空间位置和飞行切段处理；
- split 副本会进入后续历史队列，重新定位并继续输运。

因此，WW 的正确性不仅取决于 roulette/splitting 公式，也取决于“在什么位置、什么能量、什么物理事件之后”调用它。

### 2.4 本轮讨论沉淀：先理解 cell，再理解 mesh

本节记录对代码和物理算法的共同理解，作为后续 C 模式讨论的基础，不替代源码审计证据。

#### Point mesh 与 track mesh

两者都使用空间网格，但权重窗触发时机不同：

- **Point mesh**：粒子飞行到一个离散位置后，根据当前位置查找 mesh index 和能量 index，再执行一次 WW。当前 RMC 的 point mesh 路径在若干平均自由程切点检查，而不是保证每次穿过 mesh 几何边界都立即检查。
- **Track mesh**：先将一段飞行轨迹切成多个 mesh segment，对每个 segment 查找权窗并执行 WW，然后对该 segment 做 tally，最后把粒子移动到 segment 末端。

因此，point mesh 更像“在采样点控制权重”，track mesh 更像“沿轨迹段控制权重”。在屏蔽区进入探测器区的例子中，track mesh 可以在进入探测器 segment 时立即使用探测器权窗；point mesh 可能要等到下一个检查点才调整。这个差异首先影响方差控制发生的位置和 tally 的事件时序，不能仅凭两者都能运行就认为物理语义相同。

#### `DoWeightWindows()` 的统一执行逻辑

mesh 模块只负责把粒子的空间位置和能量映射为三个量：

$$
w_L=\text{lower},\qquad w_S=\text{survival},\qquad w_U=\text{upper}.
$$

随后统一进入 `DoWeightWindows()`：

```text
w_L = 0                    → 不做 WW
w < w_L                    → roulette
w_L ≤ w ≤ w_U              → 保持不变
w > w_U                    → splitting
```

roulette 分支使用

$$
w_T=\min(MXSPLN\,w_L,w_S),
\qquad P_{survive}=\frac{w}{w_T}.
$$

存活时权重变为 $w_T$，死亡时权重为零。若合法参数使 $MXSPLN\,w_L\ge w_S$，则 $w_T=w_S$，恢复通常的无偏 roulette 关系 $P_{survive}w_S=w$。因此，`MXSPLN` 在当前代码中不只是 splitting 数量上限，也参与 roulette 的实际存活权重计算；这正是为什么 `WWP` 参数生命周期必须单独审查。

splitting 分支先计算

$$
r=\frac{w}{w_S},
$$

再按小数部分随机取整得到总后代数 $n$。当 $n\le MXSPLN$ 时，当前粒子保留为一个后代，另外 $n-1$ 个后代进入 bank，每个权重为 $w_S$；当 $n>MXSPLN$ 时，总后代数被限制为 `MXSPLN`，每个后代权重改为 $w/MXSPLN$，从而保持总权重而牺牲部分粒子数。

例如探测器 mesh 中 $w_L=0.01,w_S=0.03,w_U=0.05$：

- $w=0.006$ 时，roulette 存活概率为 $0.006/0.03=0.2$；
- $w=0.20$ 时，理论 splitting 数约为 $0.20/0.03=6.67$，程序随机产生 6 或 7 个后代；
- 若 `MXSPLN=5`，则改为 5 个后代，每个权重 $0.04$，总权重仍为 $0.20$，但方差控制效果可能变差。

#### 当前修复理解顺序

当前决定先处理 **cell WW**，再处理 **mesh WW**。原因不是 cell 比 mesh 更重要，而是先固定以下共同语义：

```text
粒子进入空间区域
  → 能量定位
  → 读取 lower/survival/upper
  → roulette/splitting
  → 继续输运或进入 bank
```

cell 阶段先解决能量边界和粒子类型参数生命周期；mesh 阶段再加入空间坐标到 mesh index 的映射、point/track 事件时序、mesh 数据长度、边界 index 和 MPI shared layout。这样可以把核心权重变换问题与空间映射问题分开。

本轮讨论还明确：split bank 必须检查位置、方向、能量、时间、粒子类型及 `ParticleAttr` 等会影响后续输运的状态；但仅凭 bank 结构中存在默认 `particleAttr`，还不能直接量化当前 neutron/photon 路径对 tally 的实际偏差，仍需追踪 bank 取出和属性消费链。

## 3. 当前发现的问题及物理影响

下表区分**源码已经确认**和**仍需动态复现**的内容。

| 类别 | 当前发现 | 可能物理影响 | 当前证据 |
|---|---|---|---|
| 参数生命周期 | native `WEIGHTWINDOW` 的 `WWP:N/P/E` 曾使用公共局部变量，`MXSPLN` 未同步到执行参数数组；现已按粒子类型保存，构造与执行共用该参数源 | 修复前会改变 roulette/split 的控制策略和效率；修复后不同粒子类型参数不再串扰 | **E3，已修复：cell-WW 3/3 回归 + cross-particle 对照** |
| cell 能量索引 | neutron/photon/electron 的 WWE 查找都存在 `nErg-1` 路径；常规 $0<E\le E_1$ 映射到 bin 0，$E=0$、不合法能量或边界表异常仍需确认 | $E=0$ 等可达异常状态可能访问错误权窗或越界；常规首能群不应再表述为错位 | **E1，待最小复现** |
| mesh 数据长度 | native WWMESH lower-bound 数量曾未与 mesh 数、能量 bin 数等长检查；现强制 $N_{value}=N_sN_g$，不匹配输入在初始化期拒绝 | 避免参数不足时运行期访问不存在参数，以及参数多余时静默失去空间含义 | **E3，已修复：mesh-WW 3/3 回归 + 9/11 项拒绝对照** |
| mesh 最大边界 | 异构 mesh 坐标等于最大边界时，细网格 index 可能等于网格数量，而不是最后一个合法 index | 可能访问越界参数，导致错误分裂、错误 roulette 或崩溃 | **E1，待最小复现** |
| MPI shared offset | 多粒子类型共享 mesh 时，实际写入跨度和 offset 计算使用了不同的能群长度约定 | 某粒子类型可能读取另一类型或错误位置的权窗参数；并行结果可能与串行不一致 | **E1，源码确认候选** |
| split 状态复制 | 通用 split bank 路径没有完整复制 `ParticleAttr` | delay/capture 等物理属性可能变成默认属性，影响属性过滤的 tally 或后续物理处理 | **E1，源码确认** |
| WWINP 完整性 | 外部文件头、粒子数、能群数、网格数据长度和边界合法性检查不足 | 截断或不匹配文件可能部分读入并生成错误权窗，且不一定立即报错 | **E1，待输入复现** |
| 事件时序 | track mesh 在 tally/move 前执行 WW；point mesh 按当前切段策略处理，不等同于所有几何网格面事件 | 可能导致同一粒子在错误空间位置被调整权重，影响 tally 归属或 split 副本位置 | **E1，待事件级验证** |
| adjoint + WW | 未见明确的 adjoint + WW 支持契约、方向语义或拒绝机制 | 不能把 forward WW 的物理解释直接外推到伴随输运；可能出现未定义组合 | **D，边界未定义** |
| WWG | 源码头部明确记录历史 WWG 效率差、内存过大风险；当前 MLVR 不应依赖它作为首版生成器 | 影响实用性、内存和生成质量，不等同于 roulette 数学本身错误 | **E1，历史风险** |

## 4. 哪些问题会影响无偏性

需要区分“效率不好”和“物理估计可能错误”。

### 4.1 只改变效率的情况

如果所有参数都是合法正值，roulette 概率有效，split 后代状态完整，且空间/能群 index 正确，那么错误的 `MXSPLN` 或不理想的上下限比例通常首先表现为：

- 粒子数过多或过少；
- bank 膨胀；
- 方差降低效果差；
- 运行时间变长。

这类问题可能不立即造成期望值偏差，但仍会使 WW 不适合作为 MLVR 的稳定控制器。

### 4.2 可能改变物理估计的情况

以下问题可能直接影响结果，而不是单纯降低效率：

- 能量或空间 index 错误，读取了另一个 bin 的权窗；
- split 副本缺少物理属性，导致 tally 过滤条件改变；
- 副本位置、方向或 cell 定位错误，改变后续输运路径；
- MPI rank 读取了错误的共享参数；
- 在不支持的 adjoint 组合中使用了 forward 事件语义；
- 参数异常造成概率不在 $[0,1]$ 或发生除零，导致粒子被错误保留、杀死或产生。

这些问题不能用“总粒子数看起来正常”排除。需要检查粒子级状态、事件级调用顺序和响应级期望。

## 5. 对 MLVR 的直接影响

第一版 MLVR 需要把空间 × 能群的场转换成 WW，并在 forward/adjoint 迭代中重复使用。因此，WW 至少必须满足：

1. 空间网格和能群映射稳定且可追溯；
2. 每个粒子类型的参数互不污染；
3. split/roulette 在合法参数下保持期望权重；
4. bank 状态完整，尤其是位置、能量、时间和属性；
5. serial、MPI 和不同粒子路径不能静默使用不同的权窗；
6. forward 与 adjoint 的支持范围明确，不能由 forward 结果默认推出 adjoint 可用；
7. 错误输入应在初始化阶段拒绝，而不是运行中越界或静默截断。

因此，当前阶段不建议直接把 ML 生成的 WW 写入 RMC 并进入双向迭代。正确顺序应是：

```text
源码缺陷分类
  → Stage 3 最小修复
  → 针对性状态/索引/参数验证
  → forward WW 有界放行
  → 明确 adjoint + WW 契约
  → 再接入 MLVR WW 更新
```

## 6. 建议的 Stage 3 修复与验证顺序

### P0：先保证数据和状态不会错

1. 统一 native `WEIGHTWINDOW` 与 MCNP 路径的 WWP 参数存储；**已完成 native 路径，MCNP 原本按粒子类型存储**；
2. 对 `MXSPLN`、lower/survival/upper、能量边界和 mesh 数量做初始化期校验；
3. 修复 cell WWE 首边界索引；
4. 修复异构 mesh 最大边界夹取；
5. 修复 MPI shared mesh offset；
6. 复制 split bank 的完整粒子状态，包括 `ParticleAttr`。

### P1：再确认物理事件语义

1. 为 cell、point mesh、track mesh 画出粒子位置、cell、mesh、能量和权重的事件时序；
2. 明确 WW 是在穿面前、穿面后、轨迹段开始还是 tally 前生效；
3. 检查 split 副本重定位是否回到正确 cell/mesh；
4. 用粒子级 oracle 检查 roulette/splitting 的期望权重和状态守恒。

### P2：最后定义组合和工程边界

1. 明确 adjoint + WW 是否支持；
2. 若不支持，输入阶段明确拒绝；
3. 若支持，单独定义伴随权重窗的方向、能量、事件和响应语义；
4. 再评估 WWG 的性能和 ML 生成器接口；
5. 最后才进入 MLVR 迭代调度和 FOM 比较。

## 7. 当前结论与边界

当前 RMC WW 的正确物理关系是清楚的，核心 roulette/splitting 思路也不是整体错误；问题集中在参数生命周期、输入校验、索引边界、bank 状态、并行数据布局和组合契约。

因此当前最准确的结论是：

> **RMC WW 代码具备可复用的算法骨架，但还不是可以无条件信任的生产级 WW 接口。**

本专题不能推出：

- 所有 forward WW 输入都会产生偏差；
- 所有列出的问题都已经在运行时复现；
- photon/electron WW 与 adjoint+WW 的完整支持状态；
- Stage 3 修复后的行为；
- WWG 的实际效率损失数量级。

## 技术证据

- [F08 源码审计档案](../../MLVR_develop/2026-09/20260918_02_f08-weight-window-audit/README.md)
- [F08 任务总档案](../../MLVR_develop/2026-09/20260918_03_f08-ww-physics-guide/README.md)
- [RMC WW 头文件](../../RMC/src/WeightWindow.h)
- [RMC WW 执行逻辑](../../RMC/src/WeightWindows.cpp)
- [RMC cell WW](../../RMC/src/DoWeightWindow.cpp)
- [RMC mesh WW](../../RMC/src/DoMeshWeightWindow.cpp)
- [RMC native WW 输入](../../RMC/src/ReadWeightWindow.cpp)
- [RMC MCNP WW 输入](../../RMC/src/ReadMCNPWeightWindowCard.cpp)
- [RMC WWINP 读取](../../RMC/src/ReadMCNPWwinpFile.cpp)
- [Stage 2 功能矩阵](../../MLVR_Knowledge/02_RMC功能审查矩阵.md)
- [已知问题 W10](../../MLVR_Knowledge/06_已知问题与改进建议.md)

## 状态

- 证据等级：E1（源码审计为主）；native WWP 参数生命周期修复具 E3 针对性回归/对照证据
- RMC 状态：native WWP 参数生命周期已修复；其余 W10 问题未修改
- 适用范围：当前 RMC commit `b26a81a26f6d43aea405b1c744f0c4cdf4fd8bdf` 的 Linux 源码审查；native WWP 修复在 MPI-off cell-WW 回归范围验证
- 下一步：cell 粒子级 oracle、$E=0$ 可达性确认，以及 mesh WW 修复和针对性验证
