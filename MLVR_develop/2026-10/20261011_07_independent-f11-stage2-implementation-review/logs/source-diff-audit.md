# Source Diff and Repository Audit

## Repository identity

**SOURCE FACT — current workspace:**

```text
RMC branch: Neural_Network_WW_Iteration
RMC HEAD:   330f091eb0296e0d0124237ba7d9a22b81aee852
RMC base:   330f091e
RMC status: 24 modified tracked files + 5 untracked approved files
```

The Stage 2 implementation is present as uncommitted working-tree changes. It is not appropriate to use `git diff` alone: the five untracked files are material production/test inputs and were included in this audit.

## Actual file-set result

Task 05 declares 29 approved files: 24 tracked modifications and 5 new files. Independent inventory matches:

**Tracked modifications (24):**

```text
CMakeLists.txt
src/AceData.h
src/CalMode.h
src/CalcFixedSource.cpp
src/ExternalSource.cpp
src/ExternalSource.h
src/FixedSource.h
src/InitiateTally.cpp
src/InitiateTrspt.cpp
src/NeutronTransport.h
src/ParticleState.h
src/ParticleStateFun.cpp
src/RNG/RNG.h
src/RNG/StrideRNG.cpp
src/SampleNeutronSource.cpp
src/StatisticsFunc.cpp
src/StatisticsTester.h
src/Tally.h
src/TallyData.cpp
src/TallyData.h
src/TreatAdjointMaterial.cpp
src/Utility/Timer.h
src/WeightWindow.h
src/WeightWindows.cpp
```

**New files (5):**

```text
src/FixedSourceRunSpec.h
src/PrepareFixedSourceRun.cpp
tests/prepared_fixed_source_lifecycle/CMakeLists.txt
tests/prepared_fixed_source_lifecycle/driver.cpp
tests/prepared_fixed_source_lifecycle/globals.cpp
```

Task 05's `logs/implementation/actual-files.json` reports `count: 29` and `within_approved_scope: true`; the actual working-tree inventory matches that list. No extra Stage 2 source file was found.

## Implementation source facts

- Public methods are declared in [CalMode.h:42-55](../../../../RMC/src/CalMode.h#L42-L55): `InitializePreparedFixedSourceRuns`, `RunPreparedFixedSource`, and `FinishPreparedFixedSourceRuns`.
- Coordination is in the new [PrepareFixedSourceRun.cpp](../../../../RMC/src/PrepareFixedSourceRun.cpp). The coordinator calls the existing Stage 1 `ExecuteFixedSourcePrepared` and `FinalizeFixedSourceRun`; it does not contain a second history loop ([PrepareFixedSourceRun.cpp:257-275](../../../../RMC/src/PrepareFixedSourceRun.cpp#L257-L275)).
- Ordinary `CalcFixedSource` receives only an owner-conflict check in the Stage 2 diff; its existing wrapper/core/finalizer structure remains ([CalcFixedSource.cpp:67-112](../../../../RMC/src/CalcFixedSource.cpp#L67-L112)).
- `CDFixedSource::ResetRunState` clears terminal state, counters, banks, denominator, multiplicity and audit state ([InitiateTrspt.cpp:107-127](../../../../RMC/src/InitiateTrspt.cpp#L107-L127)).
- Tally reset traverses the persistent registry and invokes `CDTallyData::ResetForRun`; that reset clears numerical moments, `Sum3`, activity lists and StatisticsTester ([InitiateTally.cpp:262-265](../../../../RMC/src/InitiateTally.cpp#L262-L265), [TallyData.cpp:112-117](../../../../RMC/src/TallyData.cpp#L112-L117)).
- A role preparation first clears derived arrays and then invokes the original adjoint builder on a zero base ([TreatAdjointMaterial.cpp:111-124](../../../../RMC/src/TreatAdjointMaterial.cpp#L111-L124)).
- The source-weight hook is after ordinary source sampling and before possible alive/geometry termination ([SampleNeutronSource.cpp:191-208](../../../../RMC/src/SampleNeutronSource.cpp#L191-L208)). It is guarded off for ordinary runs.
- Native WW installation/clearing and Type2 substream setup occur in the new Prepare path before the one execution core ([PrepareFixedSourceRun.cpp:186-203](../../../../RMC/src/PrepareFixedSourceRun.cpp#L186-L203)).
- Receipt timing uses local `std::chrono::steady_clock` intervals ([PrepareFixedSourceRun.cpp:212-287](../../../../RMC/src/PrepareFixedSourceRun.cpp#L212-L287)). It labels legacy StatisticsTester timing as `legacy_mixed_not_per_run` and `statisticsFomIsRunMetric=false`; it does not claim old FOM is the new run metric.

## G0 source/CMake audit

Task 05's test CMake obtains the existing RMC source list, verifies exactly one `main.cpp`, removes only that source from the test target, and adds exactly `driver.cpp` and `globals.cpp`. The recorded linkage result reports 694 common production translation units, one ordinary-only `main.cpp`, two harness-only files, identical compile options and one definition for each listed singleton in each executable (`logs/linkage/result.json`). Test OFF/ON evidence reports the prepared target absent/present as expected (`logs/linkage/test-off.json`).

**Independent assessment:** the three singleton/linkage corrections identified in the earlier Task 06 review are implemented in the current source/CMake and have corresponding linkage evidence. This verifies build/linkage behavior for the serial Linux configuration, not all unsupported macro configurations.
