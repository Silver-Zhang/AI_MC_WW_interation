# Independent pre-implementation review criteria

**Independence boundary:** These criteria were written after checking the current RMC repository identity/diff and before reading Task 05's claimed Gate 1–7 conclusions or accepting any PASS summary. They define what current production code and independently traceable evidence must establish.

## Required production call relation

```text
one caller-owned model initialization
→ one prepared-series binding
→ for each RunSpec:
    validate without destroying previous completed result
    CLEAR prior run state
    SET role/source/NPS/RNG/WW
    REBUILD role-dependent state and derived WW bounds
    CHECK denominator, flags, banks and RNG segment
    ExecuteFixedSourcePrepared exactly once
    FinalizeFixedSourceRun exactly once
    return a receipt tied to this run
→ process-level Finish/OutputEnding only at actual process end
```

Required source facts:

- Stage 2 public APIs must be present and production-linked.
- The actual history/batch/descendant loop remains unique and is the Stage 1 core.
- `InitiateAll` / `InitiateMatAce` / `InitiateTally` do not run again for each half-run.
- No friend, placement-new, private bypass token, copied history loop or test-only transport algorithm is used.
- Ordinary `CalcFixedSource` remains behaviorally separate from the prepared series.

## Owner acceptance checklist

### KEEP

Geometry/material definitions, raw MGACE arrays, fixed mesh/tally definitions and registry identity, WW topology/energy/WWP, and canonical source definition remain stable across a prepared sequence. Raw data must not be mutated or reloaded after the one initialization.

### CLEAR

Before each new run, explicitly clear or reset fixed-source finish/batch/history/collision/miss/denominator state, every source/descendant bank and sentinel, tally Score/ScoreTemp/Sum1/Sum2/Sum3/Ave/RE plus activity/index state, StatisticsTester working arrays, particle transient/cache state, external-source working banks, prior WW derived runtime bounds, run timers and RNG cache/draw counters. Registry definition pointers must not be appended again.

### SET

Each run must set role, source identity and actual source, NPS, physical adjoint cutoff, effective Type2 seed/stride/offset, WW ON/OFF and lower bounds, and output/run identity. The persistent run must use the same input semantics as the fresh oracle.

### REBUILD

Forward/Adjoint ACE and particle flags, adjoint scatter/fission arrays (zero before every `+=` build), physical-to-MG cutoff, particle geometry/material/XS scratch, native WW lower/survival/upper, and owner-scoped RNG skip state must be rebuilt or explicitly checked.

## Physical/statistical acceptance criteria

- Every initial source history is checked exactly once for finite unit effective weight; zero-score and early-killed histories remain in the run count.
- Descendants created by WW or reactions never increment the initial-history denominator.
- `W0` is independently accumulated from sampled source weights; successful receipt proves completed NPS = actual ProcessTally denominator = W0 only for the restricted unit-weight profile.
- Any nonunit/nonfinite source weight rejects the prepared run before a successful receipt. Ordinary weighted/distribution-source behavior must remain available on the ordinary path.
- Each run has a non-overlapping Type2 source-history substream. Effective seed and final RNG position/draw counts are checked against an independent calculation, preserving full integer precision.
- Statistics FOM timing is either genuinely per prepared run from steady-clock intervals (`prepareSeconds`, `transportSeconds`, `tallyFinalizeSeconds`, `mcSeconds`) or explicitly labelled legacy/process-cumulative and excluded from per-run equivalence. A reset of FixedSource/Tally timers alone is insufficient because legacy StatisticsTester reads `OTimer[Total]`.

## Dynamic evidence required

For each gate, evidence must expose original raw artifacts, command/exitcode, input/program/data hashes, and per-run state—not only a README summary.

- **G0:** both executables actually compile/link; `main.cpp` is not duplicated; process globals have one owner; symbols, macros, flags and dependencies are auditable.
- **G1:** ordinary Forward/Adjoint/native-WW and six-mode/CTest/Type1/2/3 ordinary regression, including existing weighted-source behavior, remain valid.
- **G2 FF:** F0→F1 persistent equals separate fresh F0/F1 at source histories, descendants, RNG, raw scores/moments, Ave/RE, denominator and final state.
- **G3 FAF:** F→A→F each equals its own fresh oracle, including role/cutoff/particle and final F restoration.
- **G4 AA:** A→A does not repeat-accumulate derived arrays; H2O evidence is explicitly limited to zero-fission behavior.
- **G5 WW:** OFF→WW1→WW2→OFF and F/A/F with WW use actual changed lookup lower/survival/upper and real split, roulette and bank-drain events; OFF has no stale WW application.
- **G6 reuse:** raw initialization and tally registration each happen once; 20-run resources, file descriptors, registry and capacities are stable within declared bounds.
- **G7 negative:** invalid API state, role, NPS, source weight, WW, RNG range, profile and nonzero fission reject at the intended prepared validation stage; no success receipt or accidental input-parser failure substitutes for the guard.

## Comparison rules

Fresh runs must use legacy ordinary `RunCalculation`, not the new prepared API. Each oracle must match role, source, NPS, effective seed/stride/offset, WW, MGACE, input and binary identity. Raw Score/ScoreTemp/Sum1/Sum2/Sum3, Ave/RE, role-derived arrays, source/descendant/RNG events and WW lookup state require exact comparison in the declared supported profile. Only predeclared time-derived fields may differ; a negative comparator self-test must show a single changed physical statistic fails.

## Scope boundary

Any success conclusion is limited to Linux serial standard MGACE neutron fixed-source, Type2 prepared RNG, unit effective source weights, Cartesian Type1 track-length tally and native mesh WW, with nonzero fission production rejected. It cannot establish MPI/OpenMP, CE, coupled particles, restart/surface source, Python source, arbitrary weighted distributions, or nonzero-fission continuous F/A support.
