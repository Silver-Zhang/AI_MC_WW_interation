# Evidence check

## Reviewed materials

- Task 11 main report, frozen protocol, E0–E4 status JSON, preparation check, fixture provenance, proposed patch and declaration-only hook draft.
- Current RMC source at `5cfb0f771d0c5a2127c90d57e51ce672a4e3b616`, limited to lifecycle, mode, WW, tally and MG-energy paths needed to assess claims.

## Execution-status verification

Every E0–E4 status file records `result: BLOCKED`, `executed: false`, zero RMC runs, zero fresh-oracle runs, null measurements/comparisons, and no runtime evidence. The Task 11 report repeats this at `F11_Persistent_Session_Minimal_Experiments.md:3-5,87-96`.

No binary, input fixture, stdout/stderr, transport trace, timing sample, fresh-oracle output, field array artifact or compiled test driver is present in the Task 11 verification tree. The preparation check is static only: patch context/base hash/default-off text checks passed, compilation and transport did not run.

## Frozen-plan strengths

The plan explicitly requires fresh-process references, exact same-binary comparisons, history/RNG/bank/denominator/tally checks, test-only CLEAR/REBUILD, actual WW lookup evidence, post-`ProcessTally` extraction, and physical G+1 boundaries. It does not mistake unit-weight fixture arithmetic for a general source normalization identity. These are appropriate acceptance criteria, not evidence that any criterion is met.

## Proposed patch review

- `git -C RMC apply --check` succeeds against current RMC. This only proves textual patch applicability.
- P0 observability is targeted at phase timing, the fixed-source lifecycle, history events and native mesh WW lookup. The lookup hook is placed after the code has selected `ergPos` and copied lower/survival/upper bounds, so if implemented correctly it can support E3's primary proof.
- The patch is not an executable test harness. The hook header declares callbacks only. No callback definition, input generator, build system, driver, reset implementation, comparison program, or dynamic output exists.
- P1 changes control flow by skipping `InitiateAll` when a token is consumed. It is not observation-only. The unspecified driver must recreate enough preparation state to make the original history loop meaningful. Therefore P1 is an experimental session seam and cannot be approved merely as an instrumentation patch.
- The frozen plan requires rich snapshots, but the proposed hook interface exposes only opaque whole-object arguments. The patch text does not explicitly establish serialization of starting-weight denominator, all banks/counters, tally Score/ScoreTemp/Sum1/Sum2/Ave/RE, touched/index sets, role/cutoff, derived adjoint arrays, registry, or physical G+1 boundaries. The later driver could implement them, but it has not been provided for review.

## Source cross-checks

- `CalcFixedSource` starts the FixedSource timer before `InitiateAll`, then runs finalization, `ProcessTally`, summary/output, and stops it. It is not pure history-loop timing. `RMC/src/CalcFixedSource.cpp:67-80,719-749`.
- `InitiateAll` sets `CDAceData::p_bIsAdjoint` only when the fixed-source flag is true, invokes material/ACE initialization, and converts adjoint energy cutoffs in place for MG. `RMC/src/InitiateAll.cpp:125-203`.
- `treatAdjointMaterial` resizes then accumulates derived arrays using `+=`. `RMC/src/TreatAdjointMaterial.cpp:21-105`.
- Native mesh lookup determines the actual energy-bin position then copies lower/survival/upper bounds. `RMC/src/WeightWindows.cpp:45-69`.
- `CDTallyData::SetZero` clears numerical arrays while per-history index sets are cleared elsewhere. `RMC/src/TallyData.cpp:17-80`.
- `ProcessTally` is called before output summary. `RMC/src/CalcFixedSource.cpp:719-742`.
- MGACE stores physical-lower-bound and center arrays in ascending physical-energy order, while transport mapping reverses group index. The highest edge is inferred from center/lower in the checked path. `RMC/src/CheckMgAceBlock.cpp:38-60`; `RMC/src/GetMgCs.cpp:231-278`.

## Review boundaries

This document makes no claim about whether an unimplemented driver would compile, reset all required state, or produce correct physics. It makes no final F11 architecture recommendation.
