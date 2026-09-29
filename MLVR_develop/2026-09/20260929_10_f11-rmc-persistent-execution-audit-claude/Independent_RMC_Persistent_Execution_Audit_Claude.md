# Independent Audit — F11 前置：RMC 多轮同进程执行与内部集成风险审查（Claude）

> **审查性质**：独立静态源码审查，不是实现方案，也不构成 F11 架构选型。  
> **独立性协议**：先形成 `logs/preliminary-independent-architecture-view.md`，再读取允许的 F02–F10 归档作交叉核验；全程未读取 `20260929_09_f11-rmc-runtime-architecture-audit-codex/`。  
> **结论标签**：**SOURCE CONFIRMED** 为当前源码直接证实，**ARCHIVE SUPPORTED** 为允许归档的交叉支持，**INFERENCE** 为尚无运行实证的工程推论，**UNKNOWN** 为当前检查不足以判断。

## 1. Executive summary

1. **当前 RMC 是一输入、一初始化、一计算、一输出、进程退出的命令行生命周期，不是可复用 calculation session。** `main` 一次构造局部问题对象、一次读 input、一次 `RunCalculation`，然后执行结束处理和 `MPI_Finalize`。这是 **SOURCE CONFIRMED**，见 `RMC/src/main.cpp:57-166`。
2. **同一进程的第二次 fixed-source run 不能被认定为安全。** `CDFixedSource` 持有计数器和多个粒子 bank；现行启动路径只重置其中一部分。特别是 fixed-source 外层输运由 `p_nFinishCalculate` 控制，但普通外源分发路径没有通用的第二轮复位。对“第二轮一定会失败”的断言仍是 **INFERENCE**，但“没有完整显式 reset 生命周期”的阻碍是 **SOURCE CONFIRMED**。
3. **Forward → Adjoint → Forward 不具备可声明的同进程安全性。** fixed-source adjoint 标志会在初始化阶段驱动 MG 伴随材料处理，并影响源粒子标志。已检查路径没有提供受支持的 forward/adjoint toggle 加清理加反向变换 API。最安全的当前执行边界是新的进程与新 input。这是 **SOURCE CONFIRMED** 加 **INFERENCE** 的组合结论，不是运行实证。
4. **可以识别可复用的“稳定执行资源”，但不能把它们直接当成现有内嵌接口。** geometry 拓扑、已加载核数据库和 MPI communicator 具有 process-lifetime 候选资格；每轮 source、bank、RNG position、tally statistics、WW 数值、计时器、输出 handle 则必须显式设定或重建。是否可复用取决于补齐 lifecycle contract，而非对象目前存在于内存中。
5. **WW 与 tally 的运行时数据均可定位，但现有入口不是热更新 API。** native WW lookup 直接读 `OWeightWindow` 的 bounds 和 mesh；tally 初始化会重新配置/清零大量数组，HDF5 可输出 `Mean` 与 `Re`。这支持未来提取接口的可行性，却不证明“替换 array 即安全”。
6. **AIMC 当前承担迭代、采样预算、源采样、DNN/PINN 重构、WW 构造、FOM、候选选择和 HDF5 记录。** 活跃原型中未找到 RMC launcher 或 RMC output parser。因此其 RMC 耦合目前不是一个已实现、可审查的进程内集成点。

### 总体边界

本报告**不建议最终架构**。它只说明：若要走“更多内部集成”，最先需要定义且用实验验证的是 run session 的输入/输出所有权、全量 reset、mode rebuild、WW update、tally snapshot 与输出隔离。若不实现这些能力，外部进程耦合仍是当前源代码支持最明确的执行方式。

## 2. Source revision

| 项目 | 记录 |
|---|---|
| RMC branch | `Neural_Network_WW_Iteration` |
| RMC HEAD | `5cfb0f771d0c5a2127c90d57e51ce672a4e3b616` |
| RMC working tree | clean at audit start |
| AIMC branch | `feature/3d-two-group` |
| AIMC HEAD | `9d749291d5f5070a00b9f88603428e686938cb7f` |
| AIMC working tree | pre-existing untracked conference PDF only; not touched |
| `Neural_Network_WW_Iteration` top-level path | **UNKNOWN/absent in this workspace**. `RMC/` itself is on a branch of that name. |

未切 branch、未 reset、未修改 RMC/AIMC、未运行计算、未 commit 或 push。

## 3. Process lifecycle

| 阶段 | 入口与对象 | lifetime | 证据与判断 |
|---|---|---|---|
| Process globals | `Output`、`OWeightWindow`、`ORNG`、`OStatus`、`OTimer`、`OMeshInfo`、controller、logger、MPI `OParallel` | process | **SOURCE CONFIRMED** `RMC/src/main.cpp:27-55`。这些全局对象天然跨 calculation 存活。 |
| Problem objects | `main` 的 input、geometry、material、ACE、tally、fixed source、external source、transport 等局部对象 | main/process | **SOURCE CONFIRMED** `main.cpp:57-89`。它们直至 `main` return 才析构。 |
| MPI setup | `MPI_Init` 后 `OParallel.InitiateParallel` | process | **SOURCE CONFIRMED** `main.cpp:90-94`。不是每个 fixed-source run 初始化。 |
| Problem loading | `CheckIOFile` → `ReadInputBlocks` → plot → generated input | problem | **SOURCE CONFIRMED** `main.cpp:123-152`。读取和 output name 建立在单一 input 上。 |
| Calculation | `OCalMode.RunCalculation(...)` | one dispatch | **SOURCE CONFIRMED** `main.cpp:154-159`。`RunCalculation` 以值传递多类 transport/geometry/material/tally 对象，但 `CDFixedSource`、RNG、ACE、output globals 仍跨调用共享，见 `RunCalculation.cpp:6-13`。 |
| Fixed source | dispatcher 一次进入 `CalcFixedSource`，`InitiateAll` 后进行 neutron/photon/electron batch loops，完成后 process tally/output | calculation | **SOURCE CONFIRMED** `RunCalculation.cpp:83-89`，`CalcFixedSource.cpp:67-82,105-209,719-750`。 |
| Shutdown | `OutputEnding` 后 `MPI_Finalize` | process end | **SOURCE CONFIRMED** `main.cpp:161-166`。现有 `main` 不含第二次 dispatch loop。 |

**生命周期结论：** source history 的局部粒子状态可在输运中反复产生和消耗，calculation state 在 `CDFixedSource`/tally/output/global objects 中持续，problem state 在 `main` 的局部对象和全局配置中持续，process state 覆盖 MPI、logger、global WW/RNG。当前代码没有把这四层显式建模为可独立重入的 session API。

## 4. State ownership and lifetime

| 状态类别 | 所有者/代表字段 | 当前可长期保留？ | 第二轮要求 | 标签 |
|---|---|---|---|---|
| 解析 input 与 block bookkeeping | `CDInput`、`BlockDefined`、input filename set | 不应默认复用 | REBUILD 或新对象 | **SOURCE CONFIRMED** input 是一次读取；无通用 clear 路径在本审计范围内定位。安全影响是 **INFERENCE**。 |
| Geometry topology | `CDGeometry` | 候选可保留 | NO RESET 仅限无 burnup/temperature/surface mutation | **INFERENCE**，因为 material initialization 可能更新 cell density/temperature。 |
| Material / ACE | `CDMaterial`、`CDAceData` | 候选但 mode-sensitive | Forward/Adjoint 之间 REBUILD/clear | **SOURCE CONFIRMED** `InitiateMatAce.cpp:8-126` 会载入、填充并更新 material/data；`TreatAdjointMaterial.cpp:9-105` 分配并累加 adjoint cross-section arrays。 |
| Fixed-source counters/banks | `CDFixedSource` fields and vectors | 否 | CLEAR/REINITIALIZE | **SOURCE CONFIRMED** `FixedSource.h:192-214,287-308,341-418`。 |
| RNG | `CDRNG` | RNG engine 可保留 | 显式 SetSeed/SetPosition | **SOURCE CONFIRMED** setters 位于 `RNG/RNG.h:405-552`。正确重现策略是 **INFERENCE**。 |
| WW mesh/bounds | global `OWeightWindow` | mesh topology 候选保留 | bounds update + derived-state validation | **SOURCE CONFIRMED** WW runtime lookup uses arrays, `WeightWindows.cpp:45-163`。足够性仍为 **UNKNOWN**。 |
| Tally definitions/buffers | `CDTally` / tally data | definitions 候选保留 | SetZero 或 `InitiateTally` | **SOURCE CONFIRMED** `InitiateTally.cpp:8-245` and `TallyData.cpp:17-80`。完整子类覆盖为 **UNKNOWN**。 |
| Output files/HDF5 | global `Output` raw handles and names | 否 | close/rotate/reopen per calculation | **SOURCE CONFIRMED** `OutputHeading.cpp:22-23`, `OpenFilePtrs.cpp:27-274`, `CheckIOFile.cpp:135-170`。 |
| MPI/OpenMP runtime | MPI global / implicit OMP runtime | MPI process-lifetime only | do not finalize between runs | **SOURCE CONFIRMED** `main.cpp:90-94,164-166`; repeated collectives after a completed run are structurally possible but not an end-to-end guarantee. |

## 5. Second-run safety

### 5.1 反向问题：为什么第二次可能不安全

| 项目 | 现有证据 | 第二轮分类 | 风险结论 |
|---|---|---|---|
| Completion state | neutron and coupled loops use `while (p_nFinishCalculate < 2)`; terminal paths assign completion values. | CLEAR | **SOURCE CONFIRMED** control mechanism at `CalcFixedSource.cpp:105-108` and `InitialBatchSource.cpp:334-336`; ordinary external-source distribution does not provide a general reset of this value. A second run may skip is **INFERENCE** from that mechanism. |
| Fixed source count and total starting weight | `InitiateTrspt` sets `p_dTotStartWgt` and `p_nFixedSrcCount`; it does not reset all bank counters/bank vectors. | CLEAR/REINITIALIZE | **SOURCE CONFIRMED** `InitiateTrspt.cpp:60-100`; commented legacy reset at `ResetTrspt.cpp:24-32`. |
| Particle banks | `p_vFixedParticleSrcBank`, photon/electron banks and fixed-source banks are mutable vectors/stacks. | CLEAR | **SOURCE CONFIRMED** ownership `FixedSource.h:287-308`; residual nonempty state after a normal run is **UNKNOWN** without experiment. |
| Per-history particle vectors | source sampling clears selected particle-level paths. | CLEAR per history only | **SOURCE CONFIRMED** `SampleNeutronSource.cpp:180-283`. This is not a global run reset. |
| Tally score/sum/re | `CDTallyData::SetZero` clears score/sum/average/re and `InitiateTally` initializes buffers. | REINITIALIZE preferred | **SOURCE CONFIRMED** `TallyData.cpp:17-24`, `InitiateTally.cpp:8-245`. Whether every tally mode/state is reset by a minimal shared call is **UNKNOWN**. |
| Source statistics / batch counters | batch distribution updates current batch, total histories and normalization. | CLEAR | **SOURCE CONFIRMED** `InitialBatchSource.cpp:199-344`. |
| RNG sequence | source distribution advances RNG position. | explicit SET | **SOURCE CONFIRMED** RNG setters exist, `RNG/RNG.h:446-552`; policy for rank-independent replay is **UNKNOWN**. |
| Time / diagnostics | timer and process-wide output/logging persist. | CLEAR/rotate | **SOURCE CONFIRMED** timer/output global declarations `main.cpp:27-55`; precise all-diagnostic reset coverage is **UNKNOWN**. |
| Output stream pointers | main opens output once, auxiliary files opened with truncating modes, and close path does not null all pointers. | close/reopen | **SOURCE CONFIRMED** `OutputHeading.cpp:22-23`, `OpenFilePtrs.cpp:27-274`, `CloseFilePtrs.cpp:27-74`. |

### 5.2 Assessment

**Second Forward run safety: LOW.** The current driver is not evidence of a supported repeated-run contract. A call to `InitiateAll` does reinitialize important tally/transport state, but the checked implementation does not reset all fixed-source bank/counter/output/input/global state. The only defensible current claim is that a fresh process is the established lifecycle. A same-process Forward → Forward run must remain **UNKNOWN** until E1 validates it.

## 6. Forward ↔ Adjoint switching

### 6.1 Source-confirmed mode dependence

- The fixed-source input parser records `ADJOINT` on `CDFixedSource`, `RMC/src/ReadFixedSourceBlock.cpp:209-236`.
- Initialization transfers this choice to ACE mode, `RMC/src/InitiateAll.cpp:125-131`.
- Fixed-source sampling tags sampled particles as adjoint when the ACE flag is set, `RMC/src/SampleNeutronSource.cpp:222`.
- In multigroup adjoint mode, material setup calls the adjoint material treatment, `RMC/src/InitiateMatAce.cpp:65-67`.
- `TreatAdjointMaterial` allocates and accumulates adjoint cross-section/fission-cross-section structures, `RMC/src/TreatAdjointMaterial.cpp:9-105`.
- Forward and adjoint currently use a common native WW lookup contract. **ARCHIVE SUPPORTED**: F04 recorded that the MG physical-energy lookup is shared by forward and adjoint, while its verification scope did not cover runtime mode switching. See `MLVR_develop/2026-09/20260923_01_f04c-mg-native-ww-energy-contract/README.md:55,72`.

### 6.2 Safety assessment

| Sequence | Assessment | Reason |
|---|---|---|
| Forward → Adjoint | **LOW** | Changing a bool is insufficient because material/ACE mode transformation happens in initialization and no public mode-transition lifecycle was found. **SOURCE CONFIRMED** initialization mutation; safety conclusion is **INFERENCE**. |
| Adjoint → Forward | **LOWER / UNKNOWN** | The inspected path exposes creation/accumulation of adjoint arrays but no inverse transformation or documented cleanup that restores forward-only state. This creates a stale-state risk. Exact numerical failure mode is **UNKNOWN**. |
| Fresh process with adjoint input → fresh process with forward input | current supported baseline | It follows `main`’s actual one-run lifecycle. It is not a performance recommendation. |

**Do not infer safety from `p_bIsAdjoint`.** It is both a run configuration and an initialization-time data transformation trigger. The current code provides no source-confirmed hot source/mode toggle API.

## 7. Nuclear-data persistence

`CDMaterial::InitiateMatAce` builds nuclide lists, initializes/resizes ACE state, loads ACE/HDF5 data, applies burnup-related material/surface variations and handles OTF/Doppler metadata, `RMC/src/InitiateMatAce.cpp:8-126`. `CDAceData::ClearData` clears nuclides during dedicated paths, `RMC/src/InitiateAndClear.cpp:11-119`. The adjoint treatment explicitly allocates and accumulates derived arrays, `RMC/src/TreatAdjointMaterial.cpp:9-105`.

| Question | Result |
|---|---|
| Are loaded cross-section arrays read-only during ordinary transport? | **UNKNOWN in full generality.** Transport visibly reads ACE tables extensively, but this audit did not prove all transport paths are immutable. |
| Is initialization mode-neutral? | **No. SOURCE CONFIRMED.** MG adjoint invokes material transformation. |
| Is Forward → Adjoint → Forward shared-ACE reuse naturally safe? | **No safe claim.** Rebuild/clear is required by prudent lifecycle design. Exact stale-data failure is **INFERENCE/UNKNOWN**. |
| May ACE be a long-lived resource in a new architecture? | **Potentially yes, but only behind an explicit immutable-base plus per-mode-derived-state separation. INFERENCE.** |

## 8. Geometry and material persistence

Geometry is passed by value into `RunCalculation`, while material is also copied at that dispatch boundary, `RMC/src/RunCalculation.cpp:6-13`. This limits some mutation leakage inside the driver but does not make object copying a documented reset mechanism, and mutable globals remain external. Material initialization calls `VaryMat`, `VarySurf`, cell gram-density and temperature setup, `RMC/src/InitiateMatAce.cpp:59-76`.

**Assessment:** static geometry topology could be a persistent model resource only in a frozen non-burnup/non-temperature-changing subdomain. Material density/temperature/derived maps must be treated as problem or calculation state unless an explicit snapshot/restore contract is added. This is **SOURCE CONFIRMED** for mutations and **INFERENCE** for the proposed lifetime split.

## 9. Source replacement

| Parameter | Parsed/stored | Mutable representation | Current hot-update assessment |
|---|---|---|---|
| External source distribution | input → `CDExternalSource` | object fields and source-bank data | **No source-confirmed setter/reload API found.** `SampleFixSource` calls existing source sampling, `SampleNeutronSource.cpp:191-203`. |
| Fixed-source population | input → `CDFixedSource` counters/population fields | mutable fields | **Technically mutable but not proven safe.** Batch counts, normalizations and source statistics are coupled. |
| RNG seed/position | `CDRNG` | `SetSeed`, `SetPosition`, `SetPositionPre` | **SOURCE CONFIRMED setter capability**, but distributed seeding/replay semantics require E5. |
| Adjoint source | fixed-source flag plus source configuration | initialization-dependent | **No hot update contract found.** Mode change requires derived data review. |

`SampleFixSource` clears selected particle vectors, samples external/defined source, maps MG energy and conditionally marks an adjoint particle, `SampleNeutronSource.cpp:180-283`. It is a per-history routine, not a whole-run source replacement/reset facility.

## 10. WW hot update

### What exists

- WW definitions include lower/survival/upper bounds, per-particle parameters, generated windows and mesh state, `RMC/src/WeightWindow.h:32-170,337`.
- Initialization builds/loads bounds into the global `OWeightWindow`; runtime native mesh WW gets the mesh index and then calls `setMeshWeightWindowBound` before split/roulette, `RMC/src/DoMeshWeightWindow.cpp:12-180`.
- WW initialization mutates survival/upper-bound and geometry-linked WW state, `RMC/src/WeightWindows.cpp:45-210`.
- MPI broadcast occurs in the initialization path, `RMC/src/WeightWindows.cpp:220-240`.

### Static definition versus calculation values

| Component | Classification | Update condition |
|---|---|---|
| Mesh topology and spatial coordinate contract | static definition | REBUILD if changed |
| Energy grid/group contract | static definition | REBUILD if changed |
| Lower-bound values | per-run value candidate | requires synchronized replacement and invariant checks |
| Survival/upper bounds | derived state | must recompute if parameterization derives them from lower bounds |
| Geometry-linked WW fields / MPI replicas | derived/shared state | must reinitialize or explicitly synchronize |

**Answer to “fixed mesh/group, replacing only lower-bound array enough?”:** **UNKNOWN as an existing capability.** It may be theoretically sufficient only if all derived survival/upper bounds, geometry-linked fields, device/shared-memory copies and MPI-rank replicas are either direct views or rebuilt. Current source has initialization-time mutation and MPI broadcast, so “array assignment only” cannot be declared safe.

**ARCHIVE SUPPORTED constraint:** F04 confirms native MG WW now interprets `WWE:N` on a physical-energy contract and shares forward/adjoint lookup behavior. It does not verify hot updates, MPI/OpenMP, or real MLVR generation chains, `20260923_01_f04c-mg-native-ww-energy-contract/README.md:72,97-99`.

## 11. Tally reset and extraction

### Reset

`CDTally::InitiateTally` allocates/resizes and initializes many tally data arrays, `RMC/src/InitiateTally.cpp:8-245`. `CDTallyData::SetZero` clears score, sum, average and relative error, and `SumTallyBin` clears per-history score/index sets, `RMC/src/TallyData.cpp:17-80`.

**Assessment:** there is clear evidence for reset primitives and initialization, but no single source-confirmed universal “reset all tally kinds for next external run” API was located. Use **REINITIALIZE** rather than assuming a generic `SetZero` covers all active tally families.

### Structured export

`OutputTallyh5` writes hierarchical HDF5 datasets including `Mean` and `Re` for Cell/Surface/Point/Mesh/Material paths, `RMC/src/OutputTallyh5.cpp:7-240`. `MeshTallyHDF5` writes mesh geometry and `Type<type>` datasets, `RMC/src/MeshTallyHDF5.cpp:12-100`. Thus structured scalar values and relative errors are **SOURCE CONFIRMED** output capabilities.

They are not yet an MLVR field API. **ARCHIVE SUPPORTED:** F06 and F10 found that the existing HDF5 mesh path does not produce a fully machine-readable space×energy field axis, and `.Tally` lacks a self-contained authoritative G+1 group-boundary representation. See F06 `README.md:126,166,181-182` and F10 `README.md:30,38`. Complete physical group boundaries must therefore be supplied from authoritative MG definition or a run-sidecar in any later interface.

## 12. Runtime parameter mutability

| Parameter | Parsed where | Stored where | Mutable after initialization? | Safe now? | Evidence |
|---|---|---|---|---|---|
| particle population | fixed-source input parser | `CDFixedSource` population/count fields | field-level yes | **UNKNOWN** | distribution/normalization coupled to batch logic, `InitialBatchSource.cpp:199-344` |
| seed | input/RNG setup | `CDRNG` | yes | setter exists, sequence policy **UNKNOWN** | `RNG/RNG.h:446-552` |
| RNG stride/position | RNG setup/distribution | `CDRNG` and MPI bookkeeping | yes | **UNKNOWN** in MPI | same setters; rank state needs test |
| forward/adjoint | fixed-source parser | fixed-source/ACE flags plus derived material data | flag yes | **LOW / not safe claim** | `ReadFixedSourceBlock.cpp:209-236`, `InitiateAll.cpp:125-131`, `InitiateMatAce.cpp:65-67` |
| source | source parser | external/fixed-source objects | object fields mutable | no supported hot-update API found | `SampleNeutronSource.cpp:191-203` |
| WW | WW parser/init | global `OWeightWindow` | arrays mutable | **UNKNOWN** pending rebuild/sync | `WeightWindows.cpp:45-240` |
| tally accumulation | tally parser/init | `CDTally` data | buffers mutable | reinitialize preferred | `InitiateTally.cpp:8-245` |
| output filename | command-line I/O | global `Output` | mutable character arrays | unsafe without handle lifecycle | `CheckIOFile.cpp:135-170` |
| iteration identity | no MLVR loop found in RMC | none identified | no first-class field found | external/controller responsibility today | **SOURCE CONFIRMED absence in inspected fixed-source path** |

## 13. MPI and OpenMP lifecycle

- **MPI:** `main` calls `MPI_Init` once and `MPI_Finalize` once, `RMC/src/main.cpp:90-94,164-166`. `InitiateParallel` creates parallel state and custom datatypes, `RMC/src/InitiateParallel.cpp:16-142`. This supports repeated collectives before finalization in principle, but no test or session loop demonstrates multi-calculation state reset. Calling another calculation after `MPI_Finalize` is not a valid path.
- **Fixed-source collective completion:** fixed-source uses nonblocking collectives and waits at finalization, `RMC/src/CalcFixedSource.cpp:11-63,719`. This is evidence of per-run completion synchronization, not session re-entry.
- **OpenMP:** no explicit OpenMP initialization or finalization was found. Thread runtime settings are process-wide. The audit did not establish a fixed-source repeated-run thread-local reset contract.

**Assessment:** MPI job persistence is technically plausible only before `MPI_Finalize`, but the complete calculation state is not lifecycle-safe today. MPI/OpenMP repeated-run safety remains **UNKNOWN** until E1–E5 have serial success and then parallel coverage.

## 14. Existing RMC precedents

| Precedent | What it shows | What it does not show |
|---|---|---|
| Criticality cycles / burnup substeps | RMC has repeated physics work inside dedicated modes. | It does not expose a generic fixed-source session or Forward/Adjoint mode toggle. |
| Burnup succession/restart | existing code has persistent state and restart file patterns. | It intentionally mutates material/geometry and is not a clean repeated fixed-source baseline. |
| Sampling loops in `RunCalculation` | the dispatcher can invoke mode-specific calculation more than once within its own designed branch. | It does not prove `CDFixedSource` repeated-call cleanup. |
| Tests | test harness invokes standalone executables for cases. | No discovered C++ test loop calls `RunCalculation`/`CalcFixedSource` twice in the same process. |

The closest relevant design lesson is not “reuse these mechanisms unchanged.” It is that RMC’s existing repeated physics modes own their own specialized lifecycle. A generic MLVR session would need an equally explicit lifecycle.

## 15. Output and filesystem coupling

Fixed-source output is coupled to one input/output prefix. `CheckIOFile` derives names and opens HDF5 output objects, `RMC/src/CheckIOFile.cpp:135-170`. `OutputHeading` opens the main text output with `w`, `RMC/src/OutputHeading.cpp:22-23`; `OpenFilePtrs` opens many auxiliary files with `w`, `RMC/src/OpenFilePtrs.cpp:27-274`; `OutputEnding` calls close handling, `RMC/src/OutputEnding.cpp:7-80`.

**Confirmed blockers/risk factors:**

- Re-opening the same output identity overwrites rather than naturally creates iteration namespaces.
- File handles have raw-pointer lifecycle; `CloseFilePtrs` closes a subset and does not null every pointer, `RMC/src/CloseFilePtrs.cpp:27-74`.
- HDF5 result objects are constructed during input/I/O setup, not exposed as per-iteration result channels.
- fatal error paths call `MPI_Finalize`, `MPI_Abort`, or `exit`, preventing a controller from recovering in process.

A persistent run facility therefore needs an output policy: explicit `disabled`, `per-iteration namespace`, or structured in-memory result collector. This is a design requirement, not a final architecture recommendation.

## 16. AIMC responsibilities

| Function | Currently AIMC | Currently RMC | Research-variable or stable mechanism? | Evidence |
|---|---|---|---|---|
| iteration loop | yes | no MLVR loop found | research/controller | `AIMC_WWiteration/src/solver.py:394-409` |
| K / training and final particle budgets | yes | fixed-source executes configured histories | allocation policy is research-variable | `src/config.py:81-109`, `src/mc.py:370-414` |
| source construction | yes | RMC has independent source system | source semantics are research-variable | `src/mc.py:253-264`, `src/config.py:44,71` |
| particle transport / splitting | prototype implementation | yes, production transport | stable executor candidate | `src/mc.py:217-367` |
| reconstruction/model training | yes, DNN/PINN | no active external RMC reconstruction path found | research-variable | `src/solver.py:443-540,708-778`, `src/learning.py:162-275` |
| WW calculation/mapping | yes | native RMC lookup/split-roulette | builder research-variable; executor stable | `src/solver.py:541-587,778-814`, `src/utils.py:405-530` |
| RMC launch / output parse | no active implementation found | n/a | integration not yet implemented | **SOURCE CONFIRMED absence in inspected AIMC active `src/`** |
| response / relative error | yes | RMC tally outputs data | response semantics are research-variable | `src/utils.py:536-616` |
| FOM | yes | RMC supplies execution time/data | metric policy research-variable | `src/solver.py:650-657,1182-1222` |
| best iteration / history | yes | no MLVR candidate selector found | research/controller | `src/solver.py:668-681,996-1068,822-968` |
| final validation/output | yes | one fixed-source output path | split between controller and executor | `src/solver.py:1077-1275` |

**Important correction of scope:** active AIMC reconstruction is its DNN/PINN model prediction, not an RMC reconstruction launcher/parser. Any implication that a current AIMC loop already drives RMC internally would be unsupported.

## 17. Candidate internalization stability matrix

Technical stability means feasibility of making a robust capability with bounded coupling. It does **not** mean it should be integrated.

| Candidate | Technical stability | Reason / evidence | Coupling introduced | Future variability |
|---|---|---|---|---|
| 1. load geometry/material/MGACE once | MEDIUM | expensive resources are identifiable, but material/adjoint initialization mutates derived state | model snapshot and derived-state ownership | medium |
| 2. continuous fixed-source runs | LOW | no complete reset/session contract; `CDFixedSource` state persists | all calculation-lifetime state | low for mechanism, high initial repair |
| 3. dynamic particle population | MEDIUM | mutable fields exist but batch/normalization coupling must be made explicit | source scheduler and tally normalization | high policy variability |
| 4. per-run RNG reset | MEDIUM | direct seed/position setters exist | MPI rank stream convention | medium |
| 5. WW hot update | MEDIUM-LOW | bounds are identifiable but derived and MPI state exist | WW builder to executor contract | high builder variability, lower executor variability |
| 6. tally reset | MEDIUM | initialization/zeroing exists but universal coverage is unproven | tally-family lifecycle | low-to-medium |
| 7. runtime Forward/Adjoint switch | LOW | mode transforms material/ACE data; no inverse/reset API | transport kernel/data representation | medium physics variability, high safety burden |
| 8. adjoint source hot update | LOW | no source setter or source/mode transactional update | source, mode, normalization | high |
| 9. field in-memory export | MEDIUM | tallies retain values/RE; HDF5 already exports structured scalar data | data contract, group boundary ownership | medium |
| 10. iteration counter / K loop | HIGH as controller-only | no need to alter transport if external orchestration retained | controller/result schema | high research variability |

## 18. Confirmed blockers

1. **No supported multi-run session boundary.** Main calls the dispatcher once and exits. `main.cpp:141-166`.
2. **Fixed-source reset is partial.** `InitiateTrspt` resets selected counts but not all banks/counters, while a fuller legacy reset is commented. `InitiateTrspt.cpp:60-100`; `ResetTrspt.cpp:24-32`.
3. **Mode is initialization-sensitive.** MG adjoint invokes material transformation without a located reverse lifecycle. `InitiateMatAce.cpp:65-67`; `TreatAdjointMaterial.cpp:9-105`.
4. **Output identity/handles assume one calculation.** initialization opens truncating files and HDF5 output objects; close is incomplete for a clean session boundary. `CheckIOFile.cpp:135-170`; `OpenFilePtrs.cpp:27-274`; `CloseFilePtrs.cpp:27-74`.
5. **No current RMC in-memory field contract matches MLVR’s complete space×energy/group-boundary needs.** Structured `Mean`/`Re` exists, but energy-axis/boundary limitations remain. Source and allowed archive evidence cited in §11.

## 19. Risks

| Risk | Basis | Mitigation experiment/design need |
|---|---|---|
| stale bank or termination state causes second run skip/contamination | partial reset **SOURCE CONFIRMED** | E1 with deterministic counts and separate-process oracle |
| Forward/Adjoint conversion leaks derived cross-section state | initialization mutation **SOURCE CONFIRMED** | E2 plus explicit clear/rebuild instrumentation |
| updated WW reaches only some ranks/derived bounds | initialization and MPI broadcast **SOURCE CONFIRMED** | E3 serial then MPI value oracle |
| stale tally statistics or zero-score semantics enter reconstruction | reset primitives are partial at aggregate level; F07/F10 boundaries | E4 plus snapshot contract |
| output overwrite or dangling handle corrupts iteration records | files/HDF5 are single-run coupled **SOURCE CONFIRMED** | isolated per-run namespace or output-disabled E1 |
| model integration freezes scientific choices | AIMC currently owns reconstruction, response, FOM, history | keep scientific policy outside executor contract |

## 20. Unknowns

- Whether a normal fixed-source completion always drains every particle bank.
- Whether any uninspected CE, coupled-particle, plugin, GPU, or OpenMP code caches mode-dependent data.
- Whether ACE/multigroup transport arrays are wholly read-only after initialization.
- Exact deep/shallow copy semantics at the `RunCalculation` value-passing boundary.
- Whether repeated HDF5 object construction on identical output files is tolerated or corrupts/leaks.
- Whether all tally types can be safely reset with one invocation and retain correct RE after reuse.
- MPI rank-local RNG/reset and WW replication behavior under a second calculation.
- Runtime cost and numerical equivalence of rebuild versus fresh process.

None of these may be promoted to an architecture decision without the experiments below.

## 21. Required experiments

| ID | Question | Minimal setup | Pass condition | Proves | Does not prove |
|---|---|---|---|---|---|
| E1 | Same-process Forward → Forward safe? | small serial fixed-source MG case; call intended session API twice with identical input/seed | each run matches a fresh-process oracle in response, RE, history count, and bank-empty diagnostics | baseline reset lifecycle for this frozen case | adjoint, MPI, other tallies, performance |
| E2 | Forward → Adjoint → Forward safe? | same frozen geometry/group mesh; fresh-process triplet oracle | each stage matches corresponding fresh process; material/ACE mode state is checked before/after | mode rebuild/clear correctness in frozen MG case | CE/coupled particles/other responses |
| E3 | Same model plus new WW values works? | fixed mesh/group, two lower-bound fields with deterministic selected-bin instrumentation | all ranks choose intended bounds; each run matches fresh input run | WW update/rebuild contract | ML-generated field quality or bias for arbitrary windows |
| E4 | Same tally definition plus reset exports correct field? | two runs with intentionally different source strengths/spatial shapes | second snapshot has no contribution from first; value/RE match fresh run | tally clear/snapshot semantics | all tally estimators and zero-score inference |
| E5 | population and RNG changes are isolated? | sequential runs with two populations/seeds; serial then small MPI | expected history/normalization and independent reproducible streams | scheduler/RNG contract in tested ranks | all cluster thread counts or large scale |
| E6 | output isolation is valid? | E1 with output enabled and distinct iteration namespaces | no overwrite, closed handles, readable independent HDF5/text artifacts | output lifecycle for the selected policy | every optional output module |

Run E1–E4 before treating any internal controller as production-ready. These experiments must record commands, seeds, configuration, raw output and untested dimensions in their own task archive.

## 22. Questions the human must decide

1. **What is the permitted first integration boundary?** The choices materially differ: external fresh-process runs only, a hybrid executor with file-based request/result boundaries, or an internal session requiring the lifecycle work identified above.
2. **Which frozen physics subdomain must the first proof cover?** A defensible minimum is standard MGACE, fixed-source neutron, native Cartesian track mesh, serial, and a defined source/response. Expanding to CE, coupled particles, MPI/OpenMP, burnup, or user-defined energy grids changes the required contract.
3. **What output policy is acceptable for iterative execution?** Options are no RMC per-iteration files, isolated per-iteration output namespaces, or a new structured in-memory result API. The answer determines whether output lifecycle work is in scope.

---

## Evidence and boundary note

The preliminary view, source map and audit notes are retained under `logs/`. The report performed no runtime experiments and does not change F02–F10 conclusions. Permitted archive cross-checks are marked **ARCHIVE SUPPORTED**; all claims about existing RMC behavior rely on cited current source. No final architecture verdict is made.
