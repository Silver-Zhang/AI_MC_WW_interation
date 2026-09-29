# Independent RMC F11 Source Audit — Claude

> **Scope:** Current RMC source only, with Task 09–14 cited only as bounded prior evidence.  
> **Labels:** **SOURCE FACT** is directly visible in the cited current source. **INFERENCE** is a design implication. **DESIGN RECOMMENDATION** is the independent v1 proposal, not implemented code.

## 1. Executive source findings

1. **SOURCE FACT:** normal RMC is a one-parse, one-dispatch program. `main` creates problem objects, reads input once, invokes `RunCalculation` once, performs ending output and finalizes MPI at [main.cpp:57-166](../../RMC/src/main.cpp#L57-L166).
2. **SOURCE FACT:** `CalcFixedSource` is not a reusable run core today. It combines `InitiateAll`, transport preparation, the source-history/batch loops, `ProcessTally` and output tail in one function at [CalcFixedSource.cpp:67-749](../../RMC/src/CalcFixedSource.cpp#L67-L749).
3. **SOURCE FACT:** the existing `RMC::Control` class controls geometry-location numerical parameters and hash selection. It is not an input-driven workflow controller. See [Control.h:15-70](../../RMC/src/Control/Control.h#L15-L70) and [Control.cpp:10-28](../../RMC/src/Control/Control.cpp#L10-L28).
4. **SOURCE FACT:** fixed-source repeated execution needs more than `InitiateTrspt`; its active reset only restores selected counters, while banks, terminal state and other state remain outside a complete reset API. See [InitiateTrspt.cpp:59-99](../../RMC/src/InitiateTrspt.cpp#L59-L99) and the commented fixed-source reset in [ResetTrspt.cpp:23-31](../../RMC/src/ResetTrspt.cpp#L23-L31).
5. **SOURCE FACT:** forward/adjoint role selection is initialization-sensitive. It affects fixed source, ACE, particle roles, cutoffs and derived adjoint cross sections. [InitiateAll.cpp:125-203](../../RMC/src/InitiateAll.cpp#L125-L203) and [TreatAdjointMaterial.cpp:21-105](../../RMC/src/TreatAdjointMaterial.cpp#L21-L105).
6. **SOURCE FACT:** mesh tally values/RE, MG lower edges/centres and runtime WW lower/survival/upper arrays all have identifiable current owners. They can support focused v1 interfaces without a new parallel physics subsystem.

## 2. Program-level ownership

### 2.1 Process and problem lifetime

| Object category | Current owner | lifetime | Evidence |
|---|---|---|---|
| process globals | `Output`, `OWeightWindow`, `OTimer`, `ORNG`, `OCalMode`, `OController`, mesh/status/tracker objects | process | [main.cpp:27-55](../../RMC/src/main.cpp#L27-L55) |
| problem objects | input, geometry, material, ACE, tally, fixed source, external source, transport, particle state, adjoint, sampling | `main` locals | one process invocation | [main.cpp:57-89](../../RMC/src/main.cpp#L57-L89) |
| calculation dispatch | `CDCalMode::RunCalculation` | one selected mode invocation | source declaration | [RunCalculation.cpp:6-24](../../RMC/src/RunCalculation.cpp#L6-L24) |
| fixed-source calculation state | `CDFixedSource`, banks, tally moments, particle scratch, output handles | current half-run but persistent in memory | fixed-source loop | [FixedSource.h:254-418](../../RMC/src/FixedSource.h#L254-L418) |

`RunCalculation` passes neutron transport, geometry, criticality, material, particle state, convergence, tally, burnup and sampling by value, while ACE, fixed source, RNG, photon/electron transport, adjoint and external source are references, [RunCalculation.cpp:6-13](../../RMC/src/RunCalculation.cpp#L6-L13). **INFERENCE:** this mixed boundary is unsuitable as the repeated-call F11 API because copy semantics obscure retained versus reset state. The F11 workflow should stay inside a reference-owned calculation session rather than loop over `RunCalculation`.

### 2.2 Existing Control architecture

`OController` is a global `RMC::Control`, [main.cpp:35-38](../../RMC/src/main.cpp#L35-L38). Its header contains hash function selection and geometry location tolerances, [Control.h:18-49](../../RMC/src/Control/Control.h#L18-L49). `CDInput::ReadControlBlock` exists but accepts only the `HASH` card and writes into `OController`, [ReadControlBlock.cpp:7-42](../../RMC/src/ReadControlBlock.cpp#L7-L42); top-level parsing dispatches CONTROL at [ReadInputBlocks.cpp:341-347](../../RMC/src/ReadInputBlocks.cpp#L341-L347).

**DESIGN RECOMMENDATION:** do not reuse `Control` for F11 orchestration. `CDCalMode` is the natural workflow owner because it already selects `FixedSourceMode` and invokes `CalcFixedSource`, [CalMode.h:43-50](../../RMC/src/CalMode.h#L43-L50) and [RunCalculation.cpp:83-89](../../RMC/src/RunCalculation.cpp#L83-L89).

## 3. Input parser architecture

`CDInput::ReadInputBlocks` dispatches top-level blocks by keyword. It already dispatches WEIGHTWINDOW, FIXEDSOURCE, EXTERNALSOURCE and TALLY at [ReadInputBlocks.cpp:96-199](../../RMC/src/ReadInputBlocks.cpp#L96-L199). `CDInput` retains block-definition bookkeeping, [Input.h:51-71](../../RMC/src/Input.h#L51-L71), and existing blocks receive dedicated `Read...Block` methods declared there.

**SOURCE FACT:** FIXEDSOURCE parses population, RNG, cutoff and ADJOINT cards through [ReadFixedSourceBlock.cpp:6-236](../../RMC/src/ReadFixedSourceBlock.cpp#L6-L236). EXTERNALSOURCE parses sources and distributions through [ReadExternalSourceBlock.cpp:6-72](../../RMC/src/ReadExternalSourceBlock.cpp#L6-L72). WEIGHTWINDOW parses topology, energy boundaries, lower bounds and WWP through [ReadWeightWindow.cpp:6-424](../../RMC/src/ReadWeightWindow.cpp#L6-L424).

**DESIGN RECOMMENDATION:** add a top-level `MLVR` block parsed by `CDInput::ReadMLVRBlock(CDCalMode&, ...)`, with configuration stored in `CDCalMode::p_OMLVR`. It contains a small configuration value type, not an independent transport owner. Validation occurs after all blocks are parsed because TARGET needs both TALLY and MGACE/WW information.

`GenerateInpFile` should emit the new block so the normalized input documents actual F11 configuration. It should not emit per-iteration mutable source/WW values, which belong in per-run records.

## 4. Fixed-source lifecycle and hierarchy

### 4.1 Actual source flow

`CalcFixedSource` starts timers, calls `InitiateAll`, initializes particle scratch arrays, then enters the particle-mode branch, [CalcFixedSource.cpp:67-106](../../RMC/src/CalcFixedSource.cpp#L67-L106). In neutron mode it pushes a bank sentinel, loops while `p_nFinishCalculate < 2`, distributes a source batch, samples each source history, transports/drains descendants, and calls `PrcoessBatchEnd`, [CalcFixedSource.cpp:106-715](../../RMC/src/CalcFixedSource.cpp#L106-L715). It then calls `ProcessTally`, WW-generator output if active, summary output and timer stop, [CalcFixedSource.cpp:719-749](../../RMC/src/CalcFixedSource.cpp#L719-L749).

`DistributeSource` advances the current batch and delegates ordinary or surface-source distribution, [InitialBatchSource.cpp:29-37](../../RMC/src/InitialBatchSource.cpp#L29-L37). Batch end updates particle interval, tally normalization and termination state, [InitialBatchSource.cpp:198-344](../../RMC/src/InitialBatchSource.cpp#L198-L344). `SampleFixSource` initializes a source particle and sets adjoint particle role from ACE state, [SampleNeutronSource.cpp:180-283](../../RMC/src/SampleNeutronSource.cpp#L180-L283).

### 4.2 F11 nesting

```text
F11 Bootstrap
  = ordinary Forward half-run, before formal iteration
F11 formal iteration k
  = one Adjoint half-run using WW_A(k)
  + one Forward half-run using WW_F(k)
RMC half-run
  = one prepared reusable fixed-source execution
RMC batch
  = source-population interval / restart / time chunk
RMC source history
  = sampled primary plus descendant-bank draining
```

**DESIGN RECOMMENDATION:** F11 must not add an RMC batch parameter. It supplies half-run NPS; existing fixed-source batch mechanics retain their meaning and are not exposed as an F11 control axis.

## 5. `CalcFixedSource` design decision

### Alternatives

| Alternative | assessment |
|---|---|
| A. leave `CalcFixedSource` whole and loop in wrapper | **Poor.** It always calls full initialization, so it cannot preserve model base safely. |
| B. extract reusable execution core | **Recommended.** Keep exactly one history/batch loop in a private core and layer full-init or prepared-run entry around it. |
| C. add public mode flags to existing function | **Risky.** Boolean entry modes tend to hide prerequisites and make ordinary behavior regressions likely. |

**DESIGN RECOMMENDATION:** split `CDCalMode::CalcFixedSource` into:

1. a normal wrapper retaining the current public behavior: full `InitiateAll` then execution;
2. one private reference-only `ExecuteFixedSourcePrepared(...)` that retains the original transport/history/batch/finalization sequence exactly once;
3. an F11-only session path that runs `PrepareMLVRHalfRun(...)`, validates all preconditions, then calls that same core.

The production history loop must be moved, not copied. Normal fixed-source calls remain wrapper → full init → core. F11 calls session prep → core. This is safer than the Task 13 token seam because preconditions become an explicit production API rather than a hidden bypass.

## 6. Forward / Adjoint state

| State | SOURCE FACT | v1 action |
|---|---|---|
| fixed-source adjoint flag | parser sets `p_bIsAdjoint`, [ReadFixedSourceBlock.cpp:209-236](../../RMC/src/ReadFixedSourceBlock.cpp#L209-L236) | SET each half-run |
| ACE adjoint flag | full init only sets true when source is adjoint, [InitiateAll.cpp:130](../../RMC/src/InitiateAll.cpp#L130) | SET both true and false explicitly |
| particle role | source sampling copies ACE role to source particle, [SampleNeutronSource.cpp:222](../../RMC/src/SampleNeutronSource.cpp#L222) | REBUILD particle scratch each half-run |
| adjoint cutoff | physical configured cutoff is converted to MG group in place, [InitiateAll.cpp:191-203](../../RMC/src/InitiateAll.cpp#L191-L203) | KEEP physical config separately; SET internal cutoff per role |
| derived adjoint XS | `TreatAdjointMaterial` resizes then uses `+=`, [TreatAdjointMaterial.cpp:21-105](../../RMC/src/TreatAdjointMaterial.cpp#L21-L105) | CLEAR then REBUILD for A; CLEAR/unuse for F |
| material/raw ACE | `InitiateMatAce` loads and prepares base data, [InitiateMatAce.cpp:8-126](../../RMC/src/InitiateMatAce.cpp#L8-L126) | KEEP immutable base only in frozen v1 |
| source | external source sampled through `CDExternalSource`, [ExternalSource.cpp:46-115](../../RMC/src/ExternalSource.cpp#L46-L115) | SET components per half-run |
| WW | global bound lookup reads mesh/energy arrays, [WeightWindows.cpp:45-69](../../RMC/src/WeightWindows.cpp#L45-L69) | KEEP topology; SET lower; REBUILD survival/upper |
| tally | final means/RE derive from source denominator, [ProcessTally.cpp:330-393](../../RMC/src/ProcessTally.cpp#L330-L393) | KEEP definition; CLEAR run statistics |
| banks/denominator/RNG | source/batch objects retain mutable state | CLEAR then SET before every half-run |

**INFERENCE:** production F11 must make `PrepareMLVRHalfRun` a first-class checked operation. A simple role flag toggle is insufficient.

## 7. TARGET to adjoint source

`CDExternalSource` owns source components, fractions and distributions, [ExternalSource.h:39-167](../../RMC/src/ExternalSource.h#L39-L167). `CDSource` already supports particle, fraction, weight, spatial variables and distribution-based sampling, [Source.h:36-175](../../RMC/src/Source.h#L36-L175). `CDExternalSource::SampleSourceParticle` selects and samples those components, [ExternalSource.cpp:46-115](../../RMC/src/ExternalSource.cpp#L46-L115).

### Options

| option | assessment |
|---|---|
| construct temporary existing `CDExternalSource` components | **Recommended.** Reuses source selection and particle initialization. |
| new MLVR-specific source sampler | unnecessary v1 duplicate of source machinery |
| new general `SourceDistribution` type | too broad; target is an orchestration input, not a reusable user distribution primitive |

**DESIGN RECOMMENDATION:** `PrepareMLVRAdjointSource` builds a temporary `CDExternalSource` using one ordinary `CDSource` component for each selected Cartesian bin × physical MG group. Each component samples uniformly in that target bin, selects its MG group through the established MG particle energy representation, uses isotropic direction under the fixed adjoint-source convention, and has identical initial source weight. Component fraction is normalized from the declared nonnegative target weight multiplied by target-cell volume and group weight. The response convention must state whether it represents volume-integrated scalar flux; v1 rejects zero total target weight, invalid mesh/group IDs, non-Cartesian targets and empty selection.

This preserves equal initial history weights and makes the denominator remain the actual sum of starting weights. It does not create a second particle sampler.

## 8. Tally / Field export

`CDTally` owns mesh definitions and `p_OMeshTallyData`, [Tally.h:964-1030](../../RMC/src/Tally.h#L964-L1030). Mesh tally setup registers its data pointer, [InitiateTally.cpp:60-69](../../RMC/src/InitiateTally.cpp#L60-L69). Track scoring writes score/index state in [ScoreMeshTally.cpp:101-117](../../RMC/src/ScoreMeshTally.cpp#L101-L117), then fixed-source `ProcessTally` computes Ave/RE after final gathering and denominator processing, [ProcessTally.cpp:330-393](../../RMC/src/ProcessTally.cpp#L330-L393).

**DESIGN RECOMMENDATION:** export field after `ProcessTally` and before normal summary output. Use the retained mesh tally definition and `p_OMeshTallyData.p_vAve/p_vRe`. Derive a field status `ZERO_SCORE` in the MLVR writer whenever score/sum are zero; do not equate existing `RE=0` to zero uncertainty because [TallyData.cpp:83-100](../../RMC/src/TallyData.cpp#L83-L100) assigns zero RE for zero sum.

MGACE stores physical lower edges and centres in ascending physical order, [CheckMgAceBlock.cpp:38-60](../../RMC/src/CheckMgAceBlock.cpp#L38-L60). The highest edge follows `2*lastCentre-lastLower`, [GetMgCs.cpp:263-278](../../RMC/src/GetMgCs.cpp#L263-L278). Write all G+1 edges, mesh bounds, ordering, unit, role, denominator, values and RE in `field.h5`.

Existing HDF5 tally output writes scalar Mean/Re bins, [OutputTallyh5.cpp:52-84](../../RMC/src/OutputTallyh5.cpp#L52-L84), while mesh HDF5 reshapes only spatial data, [MeshTallyHDF5.cpp:40-100](../../RMC/src/MeshTallyHDF5.cpp#L40-L100). **DESIGN RECOMMENDATION:** add a focused `CDOutput::OutputMLVRField(...)` writer using the existing HDF5 infrastructure, not a new general IO subsystem and not an extension that silently changes legacy mesh-HDF5 semantics.

## 9. Dynamic WW

`OWeightWindow` is a global process object, [main.cpp:27-38](../../RMC/src/main.cpp#L27-L38). The parser constructs topology/energy grids and calls `ProcessWeightWindow`, [ReadWeightWindow.cpp:350-424](../../RMC/src/ReadWeightWindow.cpp#L350-L424). `ProcessWeightWindow` stores lower bounds and derives upper/survival values, [WeightWindows.cpp:79-100](../../RMC/src/WeightWindows.cpp#L79-L100). Track WW obtains the actual spatial segment and calls the same lookup, [DoMeshWeightWindow.cpp:21-72](../../RMC/src/DoMeshWeightWindow.cpp#L21-L72).

**DESIGN RECOMMENDATION:** `CDWeightWindow::ImportMLVRLowerBounds(...)` reads `ww.h5`, validates neutron particle type, exact Cartesian topology, mesh bounds, G and physical edge contract, then sends validated lower values through existing `ProcessWeightWindow`. Never write lower alone and leave stale survival/upper values. v1 keeps topology, energy bins and WWP immutable; only lower values vary.

When MLVR is active, require exactly one compatible native neutron WWMESH/WWP topology declaration. Reject WWG, MCNP WW input, cell WW, second WWMESH or non-neutron WW selection in the F11 calculation. Bootstrap explicitly disables WW application. Formal half-runs use imported MLVR bounds only, eliminating simultaneous static and dynamic WW behavior.

## 10. External command and failures

No current `system`, `fork`, `execve`, `popen`, `waitpid` or `CreateProcess` use was found in `RMC/src` during this audit. Existing Python source support is source-subroutine lifecycle, not a generic external reconstruction launcher.

**DESIGN RECOMMENDATION:** a small `RunMLVRExternalCommand` in `CalcMLVR.cpp` owns v1 invocation. Linux v1 may use `fork` + `chdir(workdir)` + `/bin/sh -c COMMAND` + `waitpid`. It deletes or uniquely namespaces expected `ww.h5` before launch, writes `field.h5` first, waits synchronously, rejects nonzero/signal exit, missing output, malformed HDF5, role/iteration mismatch, mesh/edge mismatch, nonfinite/lower≤0 values, and stale output identity. No timeout or recovery in v1; document that a hung command requires operator termination.

Existing RMC errors may call `MPI_Finalize`/`exit` or `MPI_Abort`, [PrintFile.cpp:5-15](../../RMC/src/PrintFile.cpp#L5-L15) and [PrintFile.cpp:51-58](../../RMC/src/PrintFile.cpp#L51-L58). All F11 validation must therefore happen before entering the next transport core.

## 11. Input-card review

**DESIGN RECOMMENDATION:** use one top-level block:

```text
MLVR
  ITERATION K = <positive integer>
  BOOTSTRAP_NPS = <positive integer>
  ADJOINT_NPS = <positive integer>
  FORWARD_NPS = <positive integer>
  TARGET MESH = <mesh tally id> BINS = ... GROUPS = ... [WEIGHTS = ...]
  SEED BASE = <positive integer>
  COMMAND = <quoted command>
  WORKDIR = <path>
ENDMLVR
```

| Item | v1 rule |
|---|---|
| `FIXEDSOURCE` | required for source/physical options; its `PARTICLE POPULATION` must equal `BOOTSTRAP_NPS` to avoid two authoritative bootstrap NPS values |
| `TALLY` | required target mesh must be neutron Cartesian Type=1, `Energy=-1`, `Normalize=1`; no implicit mesh creation |
| `WWP:N`, `WWMESH:N` | required static topology/parameters, but parsed lower values are never active in formal runs; dynamic import replaces values before every formal half-run |
| `ADJOINTCALCULATION` | forbidden as a static user setting when MLVR is active; F11 owns half-run role |
| `ITERATION` | belongs only inside `MLVR`; do not introduce a generic top-level ITERATION block |
| `COMMAND`, `WORKDIR` | v1 required; reject relative ambiguity or unwritable workdir |
| target zero/invalid | fail parse/validation, not a silent zero-response calculation |

## 12. Metrics and output history

`ProcessTally` owns Field statistics. A simple nonnegative scalar-flux target response, response RE and a transport-time FOM can be calculated by the MLVR workflow after each Forward finalized Field.

**DESIGN RECOMMENDATION:** RMC records raw response, response RE, run time, phase, seed, NPS, field file hash and WW file hash for each half-run. It records formal forward FOM but does not make model selection or reconstruction quality decisions. External research policy owns reconstruction, convergence, best iteration, alternative allocation and final scientific interpretation. RMC archives every imported/exported WW and leaves final `WW_A(K+1)` as an artifact, not an automatically selected “best” window.

## 13. Source confidence and risks

The detailed risks are retained in [risk-register.md](logs/risk-register.md). The three highest risks are:

1. Explicit Forward/Adjoint state reconstruction, especially `+=` derived adjoint arrays and in-place cutoff conversion.
2. Correct production reset of fixed-source/tally/output/RNG state without copying the Task 13 experimental harness verbatim.
3. Output and file-handle lifecycle across many half-runs, including external command files and HDF5 ownership.

## 14. Final source verdict

| Decision | Verdict |
|---|---|
| Source understanding confidence | **HIGH** for frozen serial MG neutron fixed source; **MEDIUM** outside it |
| Recommended architecture | `CDCalMode` owns MLVR workflow; a reference-only fixed-source execution core is shared by normal and F11 paths; small focused root-level MLVR files own config, prep, field I/O, WW import and command execution. |
| Architecture fit with current RMC | **ACCEPTABLE**. Existing ownership points are usable but `CalcFixedSource` needs a controlled split and reset lifecycle. |
| Ready to freeze F11 architecture? | **YES WITH CORRECTIONS**. Freeze only after explicitly adopting the lifecycle split, source/WW contracts, field schema and fail-fast boundaries in the companion design. |

The source supports a bounded production design. It does not support claiming that the current default fixed-source entry is already reusable.
