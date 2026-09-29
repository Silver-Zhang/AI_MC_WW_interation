# Independent F11 Production v1 Architecture Design — Claude

> This is a design proposal based on current-source audit. It is not implementation authorization.

## 1. Design objective

Implement the frozen v1 flow without copying transport logic:

```text
Bootstrap Forward
  → field.h5 → external reconstruction/mapping → ww_A_1.h5
for k = 1..K:
  Adjoint(ww_A_k) → field_A_k.h5 → external → ww_F_k.h5
  Forward(ww_F_k) → field_F_k.h5 + response/RE/FOM → external → ww_A_{k+1}.h5
```

The scope is standard MGACE, neutron fixed source, serial, Cartesian Type=1 mesh field, `Energy=-1`, `Normalize=1` and native track-mesh WW.

## 2. Architecture choice

### Workflow owner

**DESIGN RECOMMENDATION:** `CDCalMode` owns the F11 workflow because it owns calculation-mode dispatch today. Add `CDCalMode::CalcMLVR(...)`, dispatched when an active `MLVR` configuration is present within fixed-source mode.

Do not use `RMC::Control`: it is geometry/hash configuration, not calculation orchestration. Do not put the whole loop in `CDFixedSource`: it owns transport counters/banks, not external commands, input config or research workflow.

### Configuration owner

Add a compact `CDF11Config` value object as `CDCalMode::p_OMLVR`. It stores K, three NPS values, target mesh/bin/group/weight definition, base-seed policy, command and workdir. It owns no transport data.

### Repeated-run preparation owner

`CDCalMode::PrepareMLVRHalfRun(...)` performs an explicit `CLEAR / SET / REBUILD / KEEP` contract. It accepts reference-owned RMC objects and returns success only after state preconditions validate.

### Transport execution owner

Refactor `CalcFixedSource` so the original history/batch loop exists once in private `ExecuteFixedSourcePrepared(...)`. Ordinary fixed source does full init then calls core. F11 preparation then calls the same core.

### Field / WW owners

`CDOutput::OutputMLVRField(...)` writes field HDF5 after tally finalization. `CDWeightWindow::ImportMLVRLowerBounds(...)` validates and updates runtime bounds through `ProcessWeightWindow`.

## 3. Exact proposed call graph

```text
main
  → CDInput::ReadInputBlocks(...)
      → CDInput::ReadMLVRBlock(cCalMode.p_OMLVR)
  → CDInput::CheckInpBlock(...)
      → CDCalMode::CheckMLVRConfig(...)
  → CDOutput::GenerateInpFile(...)
  → CDCalMode::RunCalculation(...)
      → CDCalMode::CalcMLVR(...)
          → PrepareMLVRBootstrapForward(...)
          → ExecuteFixedSourcePrepared(...)
          → CDTally::ProcessTally(...)
          → CDOutput::OutputMLVRField(stage=bootstrap)
          → RunMLVRExternalCommand(field.h5, ww_A_1.h5)
          → CDWeightWindow::ImportMLVRLowerBounds(...)
          → for k = 1..K
              → PrepareMLVRHalfRun(role=adjoint, NPS=adjoint)
              → PrepareMLVRAdjointSource(target)
              → ExecuteFixedSourcePrepared(...)
              → CDTally::ProcessTally(...)
              → CDOutput::OutputMLVRField(stage=adjoint,k)
              → RunMLVRExternalCommand(... ww_F_k.h5)
              → CDWeightWindow::ImportMLVRLowerBounds(...)
              → PrepareMLVRHalfRun(role=forward, NPS=forward)
              → PrepareMLVRForwardSource(original source)
              → ExecuteFixedSourcePrepared(...)
              → CDTally::ProcessTally(...)
              → CDOutput::OutputMLVRField(stage=forward,k)
              → CalcMLVRResponseAndFOM(...)
              → RunMLVRExternalCommand(... ww_A_{k+1}.h5)
              → CDWeightWindow::ImportMLVRLowerBounds(...)
```

The ordinary path remains:

```text
RunCalculation → CalcFixedSource → InitiateAll → ExecuteFixedSourcePrepared
```

## 4. Half-run preparation contract

| Category | Action | owner |
|---|---|---|
| geometry/material/raw MGACE | KEEP | session/main problem objects |
| tally mesh definition, registry, statistics index definition | KEEP | `CDTally` |
| WW mesh topology, physical energy grid, WWP parameters | KEEP | `OWeightWindow` |
| counters, terminal status, batches, banks, descendants, denominator | CLEAR | `PrepareMLVRHalfRun` |
| NPS, source component definitions, RNG seed/position | SET | `PrepareMLVRHalfRun` |
| role flags, physical/internal cutoffs, particle scratch, adjoint arrays | REBUILD | `PrepareMLVRHalfRun` |
| tally score/moments/Ave/RE/touched sets/statistical samples | CLEAR | dedicated `CDTally::ResetForFixedSourceRun` |
| lower WW values | SET, then original `ProcessWeightWindow` rebuild | `CDWeightWindow` |
| output paths and HDF5 handles | close/reopen per half-run | `CDOutput` |

A production `ResetForFixedSourceRun` must be a named source method with test coverage. Do not encode all fields in `CalcMLVR.cpp`; that would merely turn the Task 13 experimental driver into hidden production debt.

## 5. Target source design

`PrepareMLVRAdjointSource` uses existing `CDExternalSource` and `CDSource` containers. It builds target components over selected Cartesian target bins and physical MG groups.

For each selected `(space bin i, physical group g)`, form a component probability:

```text
q(i,g) = target_weight(i,g) × bin_volume(i) × group_weight(g) / Σ target_weight × volume × group_weight
```

Every component uses equal initial source weight. It uniformly samples position in its Cartesian bin and uses the selected group representation required by MG source sampling. Existing source selection then handles fraction sampling. This is a response-source construction helper, not a new generic source sampler.

Reject a zero denominator, nonpositive/nonfinite weights, invalid mesh/group, unsupported geometry, or incompatible source probability normalization before transport.

## 6. File layout

### Existing files to modify

| File | Why | Risk |
|---|---|---|
| `src/CalMode.h`, `src/RunCalculation.cpp` | hold config and dispatch `CalcMLVR` | medium: preserve ordinary dispatch |
| `src/CalcFixedSource.cpp` | extract a single reusable prepared execution core | high: history-loop regression |
| `src/FixedSource.h` and reset implementation | formal fixed-source run reset contract | high: omitted mutable field |
| `src/Input.h`, `src/ReadInputBlocks.cpp` | MLVR block declaration/dispatch | low |
| `src/CheckInpBlock.cpp` | cross-block scope and conflict validation | medium |
| `src/GenerateInputFile.cpp` | normalized MLVR input output | low |
| `src/WeightWindow.h`, `src/WeightWindows.cpp` | validated dynamic lower import | medium |
| `src/Output.h` | output field writer declaration | low |
| `src/ExternalSource.*` or `src/Source.*` | reusable target-component construction helper | medium |

### New files justified

| New file | Why existing code cannot naturally own it |
|---|---|
| `src/MLVR.h` | compact configuration, stage metadata and HDF5 schema types shared across input/calculation/output without making `CalMode.h` a large protocol header |
| `src/ReadMLVRBlock.cpp` | follows current input-block convention and keeps parser logic out of generic input dispatch |
| `src/CalcMLVR.cpp` | multi-owner bootstrap/formal orchestration and external command lifecycle do not fit fixed-source transport code |
| `src/MLVRRunPreparation.cpp` | makes CLEAR/SET/REBUILD contract auditable and testable rather than embedding it in orchestration |
| `src/OutputMLVRField.cpp` | focused field exchange writer built on existing HDF5 support without altering legacy MeshTally HDF5 schema |
| `src/ReadMLVRWeightWindow.cpp` | focused HDF5 import/validation; calls existing WW processing rather than reimplementing it |

No `src/MLVR/` tree is recommended for v1. These focused root-level files match the current source layout and avoid a parallel subsystem.

## 7. `MLVR` input block

The block owns iteration and integration policy. Existing blocks keep their native semantics.

| Configuration | owner / rule |
|---|---|
| K, three NPS values, base seed, command/workdir | `MLVR` |
| regular Forward source | existing `EXTERNALSOURCE` |
| fixed-source cutoffs/load options | existing `FIXEDSOURCE` |
| target mesh and Field | existing `TALLY`, referenced by `MLVR TARGET` |
| WW topology / WWP | existing native `WEIGHTWINDOW` definition, treated as immutable topology/parameter template |
| half-run roles | F11 workflow only; static `FIXEDSOURCE ADJOINT` conflicts and is rejected |

Require `FIXEDSOURCE PARTICLE POPULATION == BOOTSTRAP_NPS`. The dynamic NPS values become authoritative only inside F11. Require one compatible neutron native WWMESH + WWP and reject concurrent static WW application in formal runs.

## 8. Field and WW HDF5 contracts

### `field.h5`

Required metadata: schema version, stage, formal iteration, role, run ID, tally ID, Cartesian spatial bounds/order, G+1 physical MeV edges, group order, value, RE, score status, denominator, requested/completed histories, RNG metadata and source normalization metadata.

`ZERO_SCORE` is an explicit status derived from raw score/sum state. Existing `RE=0` remains a numerical RMC value and is not recast as a certainty claim.

### `ww.h5`

Required metadata: schema version, expected next role, source stage/iteration, neutron particle type, Cartesian mesh bounds/order, G+1 physical edges, WWP factors, exact lower-bound shape and values. Import rejects any mismatch, NaN/Inf or nonpositive lower bound.

## 9. Fail-fast boundary

| Failure | owner | action |
|---|---|---|
| bad `MLVR` card / incompatible legacy card | parser/checker | error before calculation |
| invalid target / zero target total | config checker | error before bootstrap |
| state preparation invariant fails | `PrepareMLVRHalfRun` | error before transport core |
| field write failure | `OutputMLVRField` | stop before command |
| external command nonzero/signal | `RunMLVRExternalCommand` | stop |
| missing/stale/malformed `ww.h5` | WW importer | stop |
| wrong iteration/role/mesh/edge/shape | WW importer | stop |
| nonfinite or nonpositive lower | WW importer | stop |
| ordinary RMC error | existing RMC fail-fast behavior | process terminates |

No recovery/retry/auto-fallback in v1.

## 10. Metrics and history

RMC should emit per-half-run field and raw transport metrics. It should compute Forward target response, response RE and transport-time FOM because these are direct execution outcomes. External policy owns reconstruction model choice, convergence/best-iteration selection, allocation strategy and scientific result selection.

Store all field files, all imported WWs, response/FOM records, run metadata and final `WW_A(K+1)` in unique work directories. Never overwrite a previous iteration artifact.

## 11. Minimal implementation phases

| Phase | Goal | main files | acceptance gate |
|---|---|---|---|
| 1 | extract prepared core without changing ordinary behavior | `CalcFixedSource.cpp` | ordinary fixed-source regression exactly matches baseline |
| 2 | formal reset API and Forward→Forward session test | fixed source/tally reset files | F→F fresh exact lifecycle gate |
| 3 | role prep and target source | MLVR prep, external source helper | F→A→F plus required fissile lifecycle gate |
| 4 | field HDF5 export | output field file, tally integration | field value/RE/G+1 contract matches finalized tally/text |
| 5 | WW HDF5 import | WW import/process files | actual lookup uses imported lower/survival/upper |
| 6 | external command fail-fast | `CalcMLVR.cpp` | exit, missing file and malformed HDF5 failure tests |
| 7 | bootstrap and one formal iteration | input/config/orchestration | Bootstrap → A → F file sequence and response/FOM record |
| 8 | K=3 | orchestration/history output | correct alternating roles, unique artifacts and final WW_A(K+1) |

The fissile lifecycle gate is mandatory before generalizing E2 beyond the current nonfissile experimental evidence.

## 12. Final recommendation

**Recommended architecture:** `CDCalMode`-owned MLVR orchestration over a single extracted fixed-source execution core, with an explicit production preparation contract and focused root-level integration files.

**Architecture fit:** **ACCEPTABLE.** Current RMC has suitable data owners but not the reusable lifecycle boundary. The proposed split is the minimum structural correction.

**Ready to freeze:** **YES WITH CORRECTIONS.** Freeze this design only if the team explicitly accepts:

- no new generic `src/MLVR/` subsystem;
- a real reference-only prepared execution core;
- formal reset and F/A rebuild APIs rather than a bypass token;
- one HDF5 exchange schema and fail-fast external command contract;
- serial MGACE/native track mesh scope plus a fissile F/A validation gate.
