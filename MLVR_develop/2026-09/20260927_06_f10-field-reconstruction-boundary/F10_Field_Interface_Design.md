# F10 — Field Reconstruction 数据边界（第一版设计冻结）

> 状态：**design frozen；implementation not completed**。本文件定义接口语义，不是 RMC 能力新增、parser 或算法实现。原始任务见 `logs/user_task_original.txt`；结论与证据边界见同目录 `README.md` §4。

## 1. Purpose

将已审查的 RMC 空间×多群统计 tally 交给独立的场重构，再将重构结果交给未来的 WW Builder。第一版限定 standard MGACE fixed-source neutron、Cartesian Type=1 track-length mesh tally、`Energy=-1`、`Normalize=1`、MPI/OpenMP-off serial text `inp.Tally`。Bootstrap 是无 WW、低粒子数 Forward run；formal Forward / Adjoint 是不同物理身份。数据形状统一，物理身份不得混同。

本设计只冻结边界和必须拒绝的不一致输入。它不声称现有 RMC 已输出 `StatisticalField`，也不声称 Field Adapter 或 Reconstruction 已存在。

## 2. Architecture

```text
RMC inp.Tally + run metadata + authoritative mesh/MG definition
    → Field Adapter
    → StatisticalField
    → Field Reconstruction
    → ReconstructedField
    → WW Builder (later task)
```

Adapter 负责解释 RMC 格式和坐标；Reconstruction 只处理/补全场；WW Builder 才把重构场用于权重窗。Reconstruction 不生成 WW。response-to-adjoint-source 与 Forward target 另由独立的 `ResponseDefinition` 关联：F03 的 adjoint source 定义和 F09 的 formal Forward response 将来必须引用同一个定义身份；response 值和 FOM 不属于 Field。

## 3. StatisticalField definition

| 成员 | 冻结语义 |
|---|---|
| `value[i,g]` | RMC `Ave`：空间 bin `i`、物理能群数组索引 `g` 的 source-normalized Type=1 scalar track-length flux density mean。几何单位为 cm 时，其几何量纲为 **cm⁻² per unit starting source weight**；这是经过源权重分母与 mesh 体积归一化的通量密度，不是原始 `Σwℓ`。`FORWARD` 为 φ(i,g)，`ADJOINT` 为 φ†(i,g)，`BOOTSTRAP_FORWARD` 为 φ₀(i,g)。合格数值原样传递，不在 Adapter 中平滑或补零。 |
| `RE[i,g]` | 对应同一 tally 行的 RMC relative statistical uncertainty；保留原值。非零得分时按 F07 的 source-history mean 相对标准误差理解；零得分时 `RE=0` 是输出占位，不能解释为零不确定度。是否及如何利用 RE 由具体 Reconstruction 算法决定。 |
| `statistical_status[i,g]` | 仅 `VALID`、`ZERO_SCORE` 两态；定义见 §7。它是统计得分状态，不是物理有效性或质量评级。 |
| `mesh` | 物理坐标、Cartesian 空间分箱及唯一 flatten 规则；见 §5。 |
| `energy_groups` | G 个物理群的边界、MeV 单位、顺序及数组索引；见 §6。 |
| `field_role` | `BOOTSTRAP_FORWARD` / `FORWARD` / `ADJOINT`，显式表明物理身份。 |
| `stage` | `BOOTSTRAP` / `FORMAL`。 |
| `iteration` | Bootstrap 为 `none`；Formal 为正整数 `k∈{1,…,K}`；这是一次 Field 的标签，不是数据轴。 |
| `metadata` | 最小来源记录；见 §8。 |

第一版数组逻辑形状固定为 `[Nspace, Ngroup]`，`Nspace=Nx·Ny·Nz`。没有 angle、time 或 history 轴。名称 `value[i,g]` 固定外部逻辑索引；不强制任何语言的内存布局。

## 4. ReconstructedField definition

| 成员 | 冻结语义 |
|---|---|
| `value[i,g]` | Reconstruction 输出的完整处理场，仍对应相同空间 bin 与物理能群。它不是直接 MC tally。 |
| `mesh`, `energy_groups` | 与输入 **同一定义**；不得改变空间/能群分箱或索引。 |
| `field_role`, `stage`, `iteration` | 与输入完全相同，保持物理身份与生命周期。 |
| `metadata` | 保留输入来源身份并增加处理来源（例如 reconstruction 方法/版本身份）；不冒充 RMC 原始统计数据。 |

`ReconstructedField` 第一版没有 MC `RE` 或 `statistical_status` 成员。把输入 RE 直接复制到处理后场会错误声称它仍是输出场的 MC 相对误差。未来方法若提供不确定度，需要独立定义其量、估计方法与名称。

“完整”指每个规定的 `[i,g]` 都有可交付的数值，且通过接口基本数值检查；它不保证数值的物理质量、WW 适用性或统计置信度。这些判断归具体算法与后续 WW 契约。

## 5. Mesh contract

仅 Cartesian mesh。`mesh` 保存 `Nx,Ny,Nz` 和按物理坐标严格递增的 `x/y/z` boundary vectors，长度分别为 `Nx+1, Ny+1, Nz+1`；包括单位和定义身份。可以是等宽或非等宽 Cartesian 分箱，不引入新的空间离散。

外部 Field 使用 **零基** `ix∈[0,Nx)`, `iy∈[0,Ny)`, `iz∈[0,Nz)`：

```text
i = ix + Nx*iy + Nx*Ny*iz    (x fastest)
ix = i % Nx
iy = (i // Nx) % Ny
iz = i // (Nx*Ny)
```

RMC text 的 `(x,y,z)` 是一基；Adapter 各减 1 后按上述规则放入数组，不能仅靠行出现顺序定位。定义相等要求各轴分箱数、**全边界值及单位**、坐标方向和 flatten 规则一致；只有形状相同不够。Bootstrap、所有 formal Forward / Adjoint 输入以及对应 ReconstructedField 必须使用同一 mesh 定义。不做 mesh mapping。边界点归属的 RMC 几何运行时行为不由本数据边界重新规定。

## 6. Energy-group contract

`energy_groups` 保存 `number_of_groups=G`、MeV 单位下长度 `G+1` 的严格递增物理边界 `E[0..G]`、`physical_energy_ascending` 顺序约定和定义身份。外部零基 `g∈[0,G)` 对应物理区间 `[E[g],E[g+1])`（最高端点的运行时归属以 RMC 为准），`value[i,g]` 与 `RE[i,g]` 同址。此处的区间是数据标识，不宣称群内有连续能量分辨率。`g=0` 是最低物理能量群；`inp.Tally` 的 Group `g+1` 映射到它。RMC transport 内部 reverse group index 不暴露给 Reconstruction。

**完整边界的来源必须可追溯**。当前 `inp.Tally` 的 `Energy Bin` 每群只打印一个下界，而且格式化为 `5.4E`；它没有最后一群上界。Adapter 必须从本次运行对应的 authoritative MGACE group definition 或事先固化、可核验的 run-sidecar 取得完整精度的 `G+1` 边界。MGACE group-centre/width 定义可给出最后上界；不可用文本最后一个下界猜测上界，也不可把格式化的打印数当成完整精度的定义。Adapter 对文本的 Group 行数、顺序和所打印下界做显示精度允许的核验；定义无法取得或核验不符时拒绝构造 Field。只允许 `Energy=-1` 的 exact transport-group tally；自定义切群 energy grid 不在首版。

Bootstrap、formal Forward、formal Adjoint 和 ReconstructedField 必须使用相同 `G`、物理边界、单位与顺序。不能通过裸群号或仅凭 `G` 判定相等；不做 energy-group mapping。

## 7. statistical_status semantics

| 状态 | 判定与含义 |
|---|---|
| `VALID` | 冻结的 Type=1 标量通量行满足 **`Ave>0`**，且 `RE` 为有限非负数；其 `RE` 按 F07 限定语义传递。`VALID` 不表示 RE 小、估计充分或物理可靠。 |
| `ZERO_SCORE` | 原始 RMC 行为 `Ave=0, RE=0`；无非零统计得分的可用证据。`RE=0` 不代表零不确定度，也不证明真实场为零。 |

Adapter 对 **`Ave<0`**、非有限数字、负 RE、缺行、重复行、`Ave=0` 但 `RE≠0` 等不符合两态合同的输入报错，不默默映射成 `VALID` 或 `ZERO_SCORE`。第一版 Type=1 标量通量只接受 `Ave>0 → VALID` 与 `Ave=0, RE=0 → ZERO_SCORE`。首版不增加 `LOW_STATISTICS`、`OUTLIER`、`INTERPOLATED`、`INVALID_PHYSICS` 等状态。

## 8. role, stage, iteration, metadata

合法组合只有：

| `field_role` | `stage` | `iteration` | 数值身份 |
|---|---|---|---|
| `BOOTSTRAP_FORWARD` | `BOOTSTRAP` | `none` | φ₀ |
| `FORWARD` | `FORMAL` | `k≥1` | φₖ |
| `ADJOINT` | `FORMAL` | `k≥1` | φ†ₖ |

Adapter 必须从受控的 run metadata 绑定这些标签，并校验它们与运行模式一致；不能从文件名猜测。一次 Field 只表示一个 run、一个角色和一个 iteration，不存跨 iteration history。

最小 `metadata`：RMC revision（能识别执行版本）、唯一 run identity、source/run identifier、particle population（实际 source-history 计数及其口径）、**本次 tally 实际使用的 source-normalization denominator / total starting source weight 及其来源身份**（单独于 history 数量记录，不能默认二者相等）、RNG identity（例如 type/seed/stride 或可复核的等价身份）、tally definition identity（含 particle, Type=1, estimator, `Energy=-1`, `Normalize=1`）、mesh definition identity、energy-group definition identity，以及输入 `.Tally` 与定义材料的来源标识。分母必须是可核验的有限正数；来源身份应能关联本次 run。身份记录允许 URI/路径、hash 或受控 ID；不规定序列化字段名。ReconstructedField 另记录处理来源。材料、几何、距离和 ML features 不进入 Field 数组定义；若某方法未来需要，作为单独 feature input 另立合同。

## 9. Field Adapter contract

概念输入是 **RMC text `inp.Tally` + run metadata + authoritative mesh/MG definitions**；概念输出是一个 `StatisticalField`。调用形式和实现语言不冻结。

Adapter 应：选择 metadata 指明的唯一 neutron Type=1 Cartesian mesh tally；核对 track-length、`Energy=-1`、`Normalize=1`、serial frozen 子域及实际 source-normalization denominator；解析文本的一基 spatial tuple、Group、Energy Bin、Ave、RE，并按 §7 拒绝负 `Ave`；显式排除每个 mesh bin 的 `Tot` 行；依据 §5/§6 的物理定义恢复 `[Nspace,G]`；验证空间×能群笛卡尔积恰好各一行；建立两态 status；绑定 role/stage/iteration 与最小 metadata。`Tot` 可用于后续 response 路径，但不进入 Field 能群数组。输入缺乏必要定义、出现重复/缺失行、索引越界、能量顺序/边界不符或标签矛盾时，Adapter 必须拒绝输出，不得补造值。

F05/F06/F07/F12 提供的先验只覆盖上述限定子域。此处规定的是未来 Adapter 行为，并没有交付 parser 或可执行的转换。

## 10. Reconstruction contract

```text
ReconstructedField reconstruct(const StatisticalField& input)
```

这是概念签名，不锁定 C++ 类、ABI 或函数调用风格。输入符合 §3/§5–§8；输出符合 §4/§13。具体方法可选择插值、回归、平滑或未来 DNN/PINN/GNN/FNO；是否使用 RE、如何处理 `ZERO_SCORE`、如何补全场均由方法定义。处理不得改角色、stage、iteration、mesh 或能群。Reconstruction 不读取 RMC 文本、不解释内部群号，也不生成 WW。若方法需要额外 feature，未来通过独立输入合同扩展，不把它隐式塞入 MC Field。

## 11. WW Builder boundary

WW Builder 的输入是 `ReconstructedField`，由其 `field_role` 和 `iteration` 选择后续目的：

| 重构场 | 后续用途 |
|---|---|
| `BOOTSTRAP_FORWARD`, `BOOTSTRAP` | `WW_A(1)` |
| `ADJOINT`, `FORMAL`, `k` | `WW_F(k)` |
| `FORWARD`, `FORMAL`, `k` | `WW_A(k+1)` |

这仅是 handoff 身份合同。WW Builder 自己负责生成合法 Weight Window 及其后续输入；本任务不设计公式、参数或调度实现。

## 12. Bootstrap / Adjoint / Forward examples

| 路径 | Adapter 输出 | Reconstruction 输出 | 后续 handoff |
|---|---|---|---|
| Bootstrap analog Forward | `{φ₀[i,g], RE₀[i,g], status₀[i,g]}`, `role=BOOTSTRAP_FORWARD`, `stage=BOOTSTRAP`, `iteration=none` | 同 mesh/group 的 `ReconstructedField(φ̂₀)`；无 MC RE | later `WW_A(1)` |
| Formal Adjoint `k` | `{φ†ₖ[i,g], RE†ₖ[i,g], status†ₖ[i,g]}`, `role=ADJOINT`, `stage=FORMAL`, `iteration=k` | 同 mesh/group 的 `ReconstructedField(φ̂†ₖ)` | later `WW_F(k)` |
| Formal Forward `k` | `{φₖ[i,g], REₖ[i,g], statusₖ[i,g]}`, `role=FORWARD`, `stage=FORMAL`, `iteration=k` | 同 mesh/group 的 `ReconstructedField(φ̂ₖ)` | later `WW_A(k+1)` |

三条路径共享相同类型与二维形状，标签区分物理用途；Bootstrap 不进入 formal FOM 或最终物理结果。

## 13. Invariants

```text
StatisticalField.value.shape
  = StatisticalField.RE.shape
  = StatisticalField.statistical_status.shape
  = [Nx*Ny*Nz, G]
ReconstructedField.value.shape = [Nx*Ny*Nz, G]
ReconstructedField.mesh == StatisticalField.mesh
ReconstructedField.energy_groups == StatisticalField.energy_groups
ReconstructedField.field_role/stage/iteration == input's corresponding labels
```

这里 `==` 是物理定义与索引合同相等，不是对象指针相等。所有指定数组单元必须存在。Bootstrap / Forward / Adjoint 的 mesh 与 energy-group definition identities 还应对应同一实际定义；不接受只在形状上相同的不同网格。

## 14. Explicitly excluded features

没有 angle/time/history 轴、跨 iteration 历史、mesh/group mapping、response/FOM 数值、geometry/material/distance/ML feature 数组、复杂统计状态、ReconstructedField 的 MC RE、具体 Reconstruction/WW 算法、parser、C++ Field 类、F11 scheduler 或 ML 模型。HDF5 mesh tally、continuous-energy、耦合粒子、MPI/OpenMP 输出、非 Cartesian mesh、其他 tally 类型均不在首版数据入口。

## 15. Open issues for implementation

1. 确定 authoritative MGACE 完整 `G+1` 边界的读取/sidecar 形式和 provenance 校验；当前 `.Tally` 仅打印 `G` 个经舍入的下界，最后上界必须来自同一次群定义。此项在 Adapter 实现前必须解决。
2. 确定 metadata 的实际承载形式、唯一 run/tally 身份及数值单位序列化；本文仅冻结必有信息。
3. 未来 Adapter 需用代表性 `2 spatial × 30 MG` 证据检查空间索引、Group/下界、`Tot` 排除、零得分、重复/缺失行与非法 role 组合；本任务没有运行这些检查。
4. 具体 Reconstruction 方法需自行定义输出场的数值接受条件和处理 provenance；若报告处理后不确定度，应单独建立语义和验证。
5. WW Builder、ResponseDefinition 共享身份、F11 调度和更多运行配置均另立实现/验证任务。

## Evidence pointers

- F05 Forward text 输出：`../20260927_03_f01-f05-forward-field-closure/README.md` §2、其 `forward_field.inp.Tally`；F12 Bootstrap：`../20260927_04_f12-bootstrap-forward-chain/README.md` §5–§6。
- F06 空间/能群映射：`../20260926_01_f06-adjoint-spatial-energy-field/README.md` §10.4–§10.5，R2 独立复核 `../20260926_03_independent-f06-adjoint-field-review-r2/Independent-F06-Adjoint-Spatial-Energy-Field-Review-r2.md` §5–§7。
- F07 zero-score / RE：`../20260927_01_f07-field-statistical-uncertainty/README.md` §2.1–§2.7。
- RMC 只读证据：`RMC/src/SingleTally.cpp` 的 `SetupMeshTally` / text output；`RMC/src/InitiateAndClear.cpp` 的 MG bin vector 长度；`RMC/src/CheckMgAceBlock.cpp` 的 centre/width→lower bound；没有本任务代码修改。
