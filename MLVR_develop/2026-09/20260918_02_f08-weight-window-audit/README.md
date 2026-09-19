# f08-weight-window-audit

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-18 |
| 状态 | 已完成（E — Defect；D — Integration issue） |
| 任务类型 | RMC 只读功能与物理语义审查 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F08 |
| 涉及文件 | `RMC/src/WeightWindow.h`、`ReadWeightWindow.cpp`、`WeightWindows.cpp`、`DoWeightWindow.cpp`、`DoMeshWeightWindow.cpp`、`RayTracking.cpp`、`GmaGeoTracking.cpp`、fixed-source 输入/测试资产 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `b26a81a26f6d43aea405b1c744f0c4cdf4fd8bdf`；只读审查，暂不改 RMC |

---

## 1. 目标与范围（① 立项 · Agent 填）

**要做什么**：确认 RMC 正向 fixed-source 权重窗是否真实可用、是否保持 split/roulette 无偏、输入参数和空间/能群查找是否正确，并明确其与第一版 MLVR 正向输运及 adjoint 的组合边界。
**涉及什么**（仓库 / 模块 / 数据）：RMC cell-based 与 mesh-based weight window；neutron 优先，必要时记录 photon/电子边界；不修改 RMC、reference 或 benchmark。
**怎样算完成**：完成 WW 全部关键调用链和数据生命周期审计，逐项检查参数、边界、权重守恒、事件时序、粒子 bank、cell/mesh/MCNP 输入与 adjoint 组合；动态测试只作为复现/确认工具，不作为“简单案例通过即可”的正确性证明。发现确定性问题则记录为 E/D 候选，不在本任务修复。
**原始材料**（`logs/` 下有什么，原样保存）：静态源码 inventory、已有 WW 任务/输入定位、运行命令与 stdout/stderr/exit code（如运行）。

> **模式 C 追加 · 物理解释**：权重窗改变粒子数与单粒子权重，但应保持任意 tally 的期望不变。高于上限时分裂后各后代权重总和应等于原权重；低于下限时 roulette 的存活概率与权重提升应满足 $E[w_{out}]=w_{in}$。若固定 WW 改变零假设响应的期望、丢失状态/能群，或同一配置在 adjoint 路径失去支持，则否定当前实现满足首版需求。

---

## 2. 做法与证据（② 设计 · ④ 实施 · Agent 填）

**设计 / 定位**（读了什么、查到什么；关键证据给 `文件:行号` 或数据位置）：
- `RMC/src/ReadWeightWindow.cpp`：读取 `WWE/WWN/WWP/WWMESH` 并按粒子类型、空间和能量建立权窗参数。
- `RMC/src/WeightWindows.cpp:45-119`：mesh 能群定位、上下限构造和 `DoWeightWindows()` 的 roulette/splitting 数学。
- `RMC/src/DoWeightWindow.cpp:9-116`：cell neutron/photon 权窗选择与输运入口。
- `RMC/src/RayTracking.cpp:230-260`、`GmaGeoTracking.cpp:75-180`：正向 neutron/photon 穿面、飞行段和碰撞前后的调用时序。
- `RMC/src/WeightWindow.h:27-153`：参数语义、支持粒子类型和当前实现声明。
- `RMC/src/SaveSplitParticles.cpp:7-39`、`SampleNeutronSource.cpp:294-345`：split bank 只存 `n-1` 个复制体，当前粒子保留在输运态；需要同时审计复制体是否完整继承粒子状态，而不只检查总权重。
- `RMC/src/InitiateAll.cpp:181-202`：WW 初始化只在 `p_bUseMCNPweightwindow` 分支调用；原生 `WEIGHTWINDOW` 与 `MCNPWEIGHTWINDOW` 的参数生命周期不同。
- `RMC/src/ReadMCNPWeightWindowCard.cpp:126-146,220-350`：MCNP 风格路径按粒子保存 `WWP`，检查 `WWE` 与 `WWN` 数量匹配，并支持 `WWINP`。
- `RMC/src/ReadWeightWindow.cpp:281-306,361-401`：原生 `WEIGHTWINDOW` 的 `WWP:N/P/E` 共用局部 `WUPN/WSURVN/MXSPLN`，且没有同步写入 `p_vWeightWindowPara`；最终 cell/mesh 上下限统一使用最后一次读到的参数，而 `DoWeightWindows()` 的 roulette/cap 又从 `p_vWeightWindowPara[*][MXSPLN]` 读取最大分裂数。这是一个已定位的跨输入路径参数不一致候选。
- `RMC/src/DoWeightWindow.cpp:18-39`：cell WWE 查找从 `nErg=0` 开始，但命中第一个正能量上界时读取 `nErg-1`；需要用最小案例确认低于首界/等于零能量是否会访问 `[-1]`。超过最高边界则直接跳过 WW，与 mesh 路径的最高能量夹取行为也不一致。
- `RMC/src/TrackWithWeightWindow.cpp:17-35`、`DoMeshWeightWindow.cpp:29-57`：track mesh 在每个轨迹段处理 WW 后才 tally/move；point mesh 按平均自由程切段，而不是按几何网格面切段。需要继续核对 WW 发生点与 tally 的物理定义，不能由简单 forward smoke 证明其正确。
- `RMC/src/DoWeightWindow.cpp:9-116`、`RayTracking.cpp:230-260`：cell WW 只在 neutron 的穿面后调用，未见 `p_bIsAdjointParticle` 或 fixed-source forward 限制；若首版 adjoint/WW 同时开启，需明确这是禁用组合还是未防护组合。
- `RMC/src/WeightWindows.cpp:45-59`、`GlobeFun.h:141-155`：mesh 能量定位将 `GetIntpltPos()` 的末端位置再映射到 `size-2`，低于首界则保留为 0；输入能量边界非严格递增、空能量表、`erg=NaN` 和负/零下限均没有在该层防护。
- `RMC/src/ReadWeightWindow.cpp:408-415`：`p_vMeshInputLowBound` 在当前读取路径中未见填充，但其派生 upper/survival 数组仍被构造；需要判断这是遗留无效路径还是实际影响某种 mesh 输入。
- `RMC/src/DoMeshWeightWindow.cpp:29-57`：track mesh 对每个 `CDMeshTrack` 先执行 WW，再 tally 和移动；同一轨迹段若进入多个 mesh，分裂 bank 中的副本位置仍取分裂前粒子状态，后续 bank 重定位依赖旧坐标与方向，需审计边界处重复/遗漏风险。
- `RMC/src/ReadMCNPWeightWindowCard.cpp:120-146`、`WeightWindows.cpp:117-145`：MCNP 路径把 `MXSPLN` 存入粒子类型参数并用于 cap；原生 `WEIGHTWINDOW` 路径只更新局部变量，未更新同一参数数组，导致原生路径仍使用构造函数默认 `MXSPLN=5`。这不是“简单案例必失败”，但属于已由代码闭环确认的配置语义缺陷候选。
- `RMC/src/ReadWeightWindow.cpp:281-306`：原生 `WWP:N/P/E` 每次只覆盖公共局部变量，且没有按粒子类型独立保存；定义多个粒子类型时，最终 cell/mesh 参数来自最后一个 `WWP`。若用户为不同粒子配置不同 WWP，结果确定性错误。
- `RMC/src/DoWeightWindow.cpp:18-39`、`DoWeightWindow.cpp:108-139`、`DoWeightWindow.cpp:200-231`：neutron/photon/electron 三套 cell 查找完全复制同一 `nErg-1` 逻辑；能量恰好低于/等于首个 WWE 上界时会使用索引 `-1`，属于潜在越界；能量高于末界则跳过 WW，而 mesh 路径采用末 bin 夹取，语义不一致。
- `RMC/src/ReadWeightWindow.cpp:408-415`、`WeightWindow.h:145-153`：原生 `WWMESH` 读取到 `vTemporaryWeightWindowPara` 后直接调用 `ProcessWeightWindow()`，但 `p_vMeshInputLowBound` 在当前路径未填充；末尾又基于该空向量生成数组，说明存在遗留字段/无效派生路径，需确认不会被其他输入模式依赖。
- `RMC/src/ReadMCNPWwinpFile.cpp:105-125,300-345`：wwinp 文件读入主要依赖 `getline`/流状态和 `stoi`/`stod`，缺少文件头粒子数、能群数、网格数据完整性及 `nwg`/能量边界合法性校验；截断或不匹配文件可能静默产生部分参数。
- `RMC/src/DoWeightWindow.cpp:9-116`、`RayTracking.cpp:235-260`：WW 只在普通 neutron ray tracking 的穿面后处理；固定源 adjoint 粒子复用同一 `RayTracking` 但没有 WW 方向/模式保护。当前首版若不支持 adjoint+WW，应属于缺少输入组合防护，而不是可默认认为正确。
- `RMC/src/ReadWeightWindow.cpp:281-306`、`ReadMCNPWeightWindowCard.cpp:120-146`：`WWP` 只检查 `WUPN>1`、`1<WSURVN<WUPN`，没有检查 `MXSPLN>1`、整数性、有限性，也没有检查 lower/survival/upper 为正；输入 `MXSPLN<=0` 或负/非有限权窗参数可能在 `DoWeightWindows()` 中触发除零或无意义分裂。
- `RMC/docs/source-en/usersguide/VarianceReduction.rst:43-46,103-113` 与上述实现不一致：文档要求 `WUPN>2`，代码接受 `WUPN>1`；这属于输入契约未统一，需在审查结论中单列，不能仅以正常参数测试覆盖。
- `RMC/src/WeightWindows.cpp:180-183,246-269`：MPI shared mesh 的扁平数组实际按 `p_vMeshInformation[*][*].size() = p_vEnergyBins[*].size()-1` 写入，但 `p_vParticleTypeMeshDisplc` 按 `p_vEnergyBins[*].size()` 计算前一粒子类型的跨度；当同一 WWINP 包含多个粒子类型时，后续粒子类型的共享内存偏移会多出“每个 mesh 一个能群”的长度，可能读错或越界。
- `RMC/src/MeshFun.cpp:184-216`：`GetHeterMeshIndex()` 和 `GetHeterCylinMeshIndex()` 在坐标恰好等于最大边界时，细网格下标会等于该方向网格数；函数只输出 warning，不将最终 `nIndex` 变为 `-1`，随后 `DoPointMeshWeightWindow()` 可能用非法 mesh index 访问 `p_vMeshInformation`。
- `RMC/src/SaveSplitParticles.cpp:26-39`：通用 neutron/photon split bank 没有复制 `cParticleState.attr()`，`CDFixBank::particleAttr` 保持默认 `prompt`；delay/capture 等粒子属性在 split 后代中会丢失。电子 split 的多个手写 bank 路径也需单独核对属性复制。
- `RMC/src/ReadWeightWindow.cpp:314-351,404-410`、`WeightWindows.cpp:71-85`：原生 `WWMESH` lower-bound 个数没有与实际 mesh 数和能量 bin 数做等长检查，`ProcessWeightWindow()` 使用整数除法得到 `spatialNum`，不足时运行期 mesh 查找可能越界，多余值则静默丢弃。
**方案选择**：采用“源码审计优先、动态案例只用于确认根因”的方案；不以简单案例通过作为结论，不重复大规模统计，不在本任务修复源码，也不把 AIMC 的 WW 结果直接当作 RMC 结论。
**实施要点**（改了什么；改动快照见 `changes.diff`，无代码改动写“无”）：当前无 RMC 代码改动。
**验证输出**（贴真实命令与输出；物理结论从严，工程/文档从简）：

```text
当前阶段完成了关键源码闭环审计，未修改 RMC、未运行动态案例。
已确认：原生 WEIGHTWINDOW 的 WWP 参数不按粒子类型保存，且 DoWeightWindows 的 MXSPLN 读取的是另一套默认参数数组；不同粒子使用不同 WWP 时配置语义会失真。
已确认候选：原生 WWMESH 长度无校验、MPI 多粒子类型 shared offset 不一致、异构 mesh 最大边界非法 index、split bank 粒子属性丢失。
待确认：cell WWE 首能群边界、wwinp 截断输入、track mesh 分裂位置/事件时序、adjoint+WW 组合边界及 WWG 数组边界。
```

**未覆盖到的验证**（如实写；没有就写“无”）：当前尚未完成所有候选的调用者级闭环、输入最小复现、MPI shared-memory 生命周期、WWG 生成器和复杂 mesh 边界审计；这些不能以一个正常 forward 案例替代。

---

## 3. 决策记录（③ · **人拍板**）

- **决定**（采纳什么方案）：用户批准继续按“源码审计优先、动态案例只用于确认根因”的方案完成 F08；本任务只读审查，不修改 RMC。
- **决定人 / 日期**：用户 / 2026-09-18
- **约束**（能不能动接口 / 基准 / 算力预算…）：不改 RMC、不更新 reference/benchmark、不提交或 push；失败即分类，不通过调参掩盖。

**变更卡（B/C 模式，各一行）**：
| WW 事件顺序、split/roulette 或查找边界可能导致偏倚或不可用 | 只读 RMC + 新增 F08 证据；不改 RMC/reference | 已发现确定性参数、mesh index、shared offset 与粒子属性风险；停止于 E/D 分类，后续修复另立 Stage 3 任务 | 无 RMC 改动 |

> **模式 C 追加 · 人类理解确认**：用户指出正向输运 WW 可能不好用，要求优先完成 F08；已确认先验证 RMC 现有 WW 的正确性与可用边界，不提前进入框架接口或修改实现。

> 未拍板前，Agent 不得改动 `../RMC` 下的任何文件。



---

## 4. 结论与边界（⑤ 归档）

- **结论**：当前不能将 RMC WW 评为 A — Ready。源码审计已发现多项确定性缺陷候选：原生 `WWP` 参数生命周期错误、原生 `WWMESH` 输入长度缺少校验、MPI shared mesh 多粒子类型偏移计算不一致、异构 mesh 最大边界可能产生非法 index、split bank 可能丢失粒子属性。cell WWE 能群首边界、WWINP 截断文件、track mesh 事件语义和 adjoint+WW 组合仍需进一步闭环。阶段分类建议为 **E — Defect（已确认代码缺陷，待 Stage 3 修复）+ D — Integration issue（未定义/未防护的 adjoint 组合）**，不建议继续把验证重点放在普通 happy-path smoke。
- **不能推出什么**（边界）：尚不能据此断言所有 WW 输入都会错误，也不能量化每个缺陷对某个具体 tally 的偏差；未完成动态复现的候选仍不能写成已观察到的运行时崩溃。结论只针对当前 RMC commit `b26a81a26f6d43aea405b1c744f0c4cdf4fd8bdf`、Linux 源码审查和上述代码路径，不外推到其他分支或修复后版本。
- **遗留 / 下一步**：将确定性缺陷整理成 Stage 3 修复候选，优先顺序为：① 原生/MCNP WWP 参数统一；② lower-bound 与 mesh/energy 数量校验；③ shared-memory offset；④ mesh 最大边界夹取；⑤ split bank 完整复制 `ParticleAttr`；⑥ 决定并防护 adjoint+WW 支持边界。动态最小复现应服务于各缺陷修复，不作为本次“功能正确”放行依据。
- **提交状态**（分支 / commit / 谁 push）：

> **模式 C 追加 · 结果解释**：结果支持或否定了哪个假设；通过/失败在物理上说明什么；不可外推的边界在哪。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-18 17:05 | 立项 |
| 2026-09-18 | 用户确认以源码缺陷审计为主，不以简单 forward smoke 作为正确性证明 |
| 2026-09-18 | 完成 cell/mesh/MCNP WW、split bank、WWG、MPI shared mesh 与 adjoint 组合的关键路径审计；未修改 RMC |
| 2026-09-18 | 结论归档：E — Defect + D — Integration issue；Stage 3 修复候选另立任务 |

> 关键命令、误判与修正、未决分歧都写在这里；人机讨论较深时把要点并入本表，**不再单独建会话纪要文件**。原始聊天转储不要入仓（可能含凭据）。

**证据等级（可选）**：物理/审查结论可标 E0–E4；工程、文档、治理任务可省略。
