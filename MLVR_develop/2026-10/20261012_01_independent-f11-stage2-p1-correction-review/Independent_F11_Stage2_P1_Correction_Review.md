# Independent F11 Stage 2 P1 Correction Review

## Classification

```text
NEEDS CORRECTION
```

## Decision table

| Review item | Classification | Basis |
|---|---|---|
| P1-01 Universe semantic fingerprint | PASS, restricted profile | Current source serializes deterministic membership, adjacency, transform and rectangle/hex lattice definition; correction-era mutations reject before a second CLEAR. |
| P1-02 native WW validation | FAIL | Energy-bin outer container is indexed before outer-shape validation; the installer repeats the assumption. |
| Scalar/derived WW constraints | PASS | WUPN/WSURVN/MXSPLN plus derived and integer-representation constraints are checked at binding and per-run boundaries. |
| Intended negative-guard paths | PARTIAL PASS | Scalar/derived and Universe guards are exercised; malformed energy-bin topology has no guard test. |
| Ordinary fixed-source non-regression | PASS, reviewed scope | 123/123 correction-era ordinary comparisons and 10/10 CTest are recorded. |
| Persistent/fresh equivalence | PASS, reviewed scope | 36/36 raw snapshots and decompressed trace payloads match under zero physical tolerance. |
| Stage 2 final technical acceptance | FAIL | Both P1s must close; P1-02 remains open. |
| Freeze / submit / Stage 3 | Not approved | Requires a separately authorized correction and independent re-review. |

## P1-01 basis

**SOURCE FACT.** `RMC/src/PrepareFixedSourceRun.cpp:47-61` serializes the supported deterministic `CDUniverse` state, and `:86-87` incorporates it into the prepared definition. Location/transport consumes those fields through `CheckParticleLocation.cpp`, `TranCoord.cpp`, `FindLatIndex.cpp`, `MonveToOriginLat.cpp`, and `FindNeighborCell.cpp`. Unsupported random/stochastic/DEM modes are rejected at `PrepareFixedSourceRun.cpp:132-136`.

**DYNAMIC EVIDENCE.** Task05 correction artifacts show Universe origin, rotation, membership and lattice-fill mutations rejecting prior to a second run reset while preserving first-run state.

**REVIEW CONCLUSION.** The original P1-01 finding is closed only for deterministic CSG, Type-1 rectangle and Type-2 hexagon paths; it is not a claim about rejected stochastic modes.

## P1-02 basis

**SOURCE FACT.** `checkNativeParameters()` at `RMC/src/PrepareFixedSourceRun.cpp:63-75` correctly checks WWP parameter-vector shape and scalar contracts. However, `RunPreparedFixedSource()` accesses `OWeightWindow.p_vEnergyBins[1]` at `:286` before validating the outer vector contains that element; only then does `:287-288` check the inner length. `RMC/src/WeightWindows.cpp:310-312` independently assumes the same neutron entry exists during prepared installation. Separately, `GetIntpltPos()` returns the final boundary position when energy equals the final boundary (`RMC/src/GlobeFun.h:141-151`), but `setMeshWeightWindowBound()` backs off only for energy greater than that boundary (`RMC/src/WeightWindows.cpp:45-66`). The prepared path does not require finite, strictly increasing WW energy boundaries or prove that terminal endpoint lookup selects a legal interval.

**DYNAMIC EVIDENCE.** 51 scalar/derived P1 negatives exercise the intended WUPN/WSURVN/MXSPLN or derived-bound guards. No negative mutates an empty/short energy-bin outer vector or a neutron entry of size zero/one.

**REVIEW CONCLUSION.** The original P1-02 finding is only partially repaired. A caller-visible malformed WW energy-bin container can reach unchecked indexing, which violates the predeclared P1 safety criterion. This is a P1 blocker.

## Required future correction

Before any prepared neutron energy-bin indexing:

1. validate `p_vEnergyBins` contains `CDParticleState::Neutron`;
2. validate the neutron entry has at least two finite, strictly increasing boundaries;
3. correct terminal endpoint lookup so it maps to the final legal WW interval (or reject a topology that cannot guarantee this);
4. centralize the shape validation so `RunPreparedFixedSource()` and `InstallPreparedNativeState()` cannot diverge;
5. add binding-time and post-successful-run negative cases for short outer vector, empty/one-boundary neutron vector, duplicate/descending/non-finite boundaries and terminal-equality lookup;
6. prove post-run rejection occurs before CLEAR while retaining the prior successful receipt, tally, denominator and RNG state.

No RMC code was modified by this review.
