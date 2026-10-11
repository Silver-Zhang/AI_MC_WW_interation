# Independent F11 Stage 2 Persistent-Lifecycle Review

> **Verdict: DESIGN REVIEW ONLY**  
> **Review status:** Completed as a source/design review. No Stage 2 production code, build, transport sequence, persistent/fresh comparison, or Stage 2 gate result exists to accept or reject dynamically.

## 1. Objective and scope

This independent Mode-C review asks whether current RMC can, after one complete model initialization, correctly execute multiple Forward/Adjoint fixed-source half-runs in one process while preserving per-run statistical independence and physical consistency.

The review was intentionally read-only:

- no `RMC` production source, Task 05 artifact, reference result, nuclear-data file, `STATUS.md`, `INDEX.md`, or knowledge-base file was modified;
- no commit, push, Stage 3 work, or repair was started;
- review records were written only in this archive;
- the acceptance criteria in [logs/pre-review-criteria.md](logs/pre-review-criteria.md) were written before Task 05's lifecycle design and evidence were read.

The inspected baseline is RMC `330f091eb0296e0d0124237ba7d9a22b81aee852` on branch `Neural_Network_WW_Iteration`.

**Physical interpretation.** A fixed-source estimator for each half-run must be formed from that run's source histories—including zero-score histories—and all their descendants, with that run's own starting-weight denominator. Changing Forward/Adjoint role changes transport operators and derived state; it is not a safe boolean-only transition. Consequently, a repeated-run claim requires verified clearing of statistical history and verified rebuilding of role-dependent state before transport, followed by exact comparison against fresh single-run oracles.

## 2. Independent source findings

### 2.1 Stage 1 interface extraction

**SOURCE FACT.** The ordinary path is now:

```text
CalcFixedSource
  → InitializeFixedSourceModel
  → ExecuteFixedSourcePrepared
  → FinalizeFixedSourceRun
  → existing ordinary output / process-facing tail
```

The wrapper maintains its timer, local `CBurnup`, ordinary output behavior, and by-value external-source semantics ([CalcFixedSource.cpp:67-112](../../../RMC/src/CalcFixedSource.cpp#L67-L112)). `InitializeFixedSourceModel` still performs complete existing initialization through `CDFixedSource::InitiateAll` ([CalcFixedSource.cpp:114-139](../../../RMC/src/CalcFixedSource.cpp#L114-L139)).

**SOURCE FACT.** The sole history/batch/descendant execution suite remains in `ExecuteFixedSourcePrepared` ([CalcFixedSource.cpp:141-770](../../../RMC/src/CalcFixedSource.cpp#L141-L770)), while `ProcessTally` is called once through `FinalizeFixedSourceRun` ([CalcFixedSource.cpp:772-775](../../../RMC/src/CalcFixedSource.cpp#L772-L775)). There is no duplicated transport loop and no hidden initialization-bypass token.

**SOURCE FACT.** These Stage 1 helpers are private members, not a public prepared-series API ([CalMode.h:172-247](../../../RMC/src/CalMode.h#L172-L247)). Their comments explicitly say that initialization is one-time rather than a repeated-run reset, and that execution requires externally prepared state.

**REVIEW CONCLUSION.** Stage 1 provides an appropriate single-core seam for Stage 2. It does **not** itself provide safe repeated execution.

### 2.2 Current source cannot safely repeat a prepared half-run

The following are source-backed blockers, not merely missing tests:

| Area | SOURCE FACT | Consequence without a formal reset/rebuild |
|---|---|---|
| Fixed-source completion, counters, banks and denominator | `InitiateTrspt` resets selected fields only ([InitiateTrspt.cpp:60-100](../../../RMC/src/InitiateTrspt.cpp#L60-L100)); the core adds a neutron-bank sentinel and runs until `p_nFinishCalculate` becomes terminal ([CalcFixedSource.cpp:156-259](../../../RMC/src/CalcFixedSource.cpp#L156-L259)). | A second direct call can retain terminal finish state, counter/bank state or an old normalization denominator. |
| Tally numerical and registry state | `SetZero` omits `Sum3` and activity/index structures ([TallyData.cpp:17-24](../../../RMC/src/TallyData.cpp#L17-L24)); full tally initialization registers pointers by repeated `push_back` ([InitiateTally.cpp:57-145](../../../RMC/src/InitiateTally.cpp#L57-L145)). | `SetZero` is not a sufficient per-run clear; rerunning full tally initialization is not a safe substitute. |
| Adjoint derived data and role | Initialization visibly sets ACE adjoint only in the true direction ([InitiateAll.cpp:125-131](../../../RMC/src/InitiateAll.cpp#L125-L131)); `treatAdjointMaterial` accumulates derived arrays with `+=` after `resize` ([TreatAdjointMaterial.cpp:23-100](../../../RMC/src/TreatAdjointMaterial.cpp#L23-L100)). | A→A can accumulate and A→F can retain stale role-derived data unless explicitly cleared/rebuilt. |
| Physical vs internal cutoffs | An adjoint maximum energy is overwritten with a multigroup index by `LocateMgErgGrp` ([InitiateAll.cpp:192-203](../../../RMC/src/InitiateAll.cpp#L192-L203)). | Reusing the stored value as a physical energy on a later run is unsafe. |
| Particle role/cache | Source sampling sets `p_bIsAdjointParticle=true` when ACE is adjoint ([SampleNeutronSource.cpp:180-222](../../../RMC/src/SampleNeutronSource.cpp#L180-L222)). | Switching ACE alone does not prove Forward particle state/cache restoration. |
| Working source state | External-source sampling mutates fixed-initial source-bank vectors/counts ([ExternalSource.cpp:46-153](../../../RMC/src/ExternalSource.cpp#L46-L153)); the ordinary wrapper passes source by value ([CalMode.h:223-227](../../../RMC/src/CalMode.h#L223-L227)). | A persistent API needs an immutable canonical definition and a clean per-run active source; neither exists today. |
| RNG state | Type2 `GetRandSeed` keeps skip parameters and seed in function-static state ([StrideRNG.cpp:85-100](../../../RMC/src/RNG/StrideRNG.cpp#L85-L100)). | A per-object seed/position reset alone cannot establish a complete repeat-run stream contract. |
| Native WW | Actual transport reads lower/survival/upper values from global `OWeightWindow` ([WeightWindows.cpp:45-69](../../../RMC/src/WeightWindows.cpp#L45-L69)); `ProcessWeightWindow` derives all three fields from lower bounds ([WeightWindows.cpp:79-100](../../../RMC/src/WeightWindows.cpp#L79-L100)). | Updating lower bounds alone can leave stale derived limits or policy across half-runs. |
| Timer/output/process lifetime | Output, timer and WW are globals ([main.cpp:28-33](../../../RMC/src/main.cpp#L28-L33)); process ending is called once from `main` ([main.cpp:162-166](../../../RMC/src/main.cpp#L162-L166)); `Timer::reset` does not clear `recordTime` ([Timer.h:94-99](../../../RMC/src/Utility/Timer.h#L94-L99)). | A per-run lifecycle must not perform process closing, and needs more explicit timer/output handling than current code exposes. |
| Value/reference boundary | `RunCalculation` passes several model/work objects by value but ACE/fixed source/RNG/external source by reference ([RunCalculation.cpp:6-13](../../../RMC/src/RunCalculation.cpp#L6-L13)). | Repeated `RunCalculation` calls are not a persistent-model API and cannot safely stand in for it. |

The complete owner matrix is recorded in [logs/state-ownership-audit.md](logs/state-ownership-audit.md), and the call topology in [logs/source-call-graph.md](logs/source-call-graph.md).

## 3. Review of Task 05 Stage 2 design

### Strengths

**DESIGN REVIEW.** Task 05 correctly treats Stage 1 as an execution seam rather than a completed session lifecycle. Its design:

1. proposes a stable-reference caller instead of repeated `RunCalculation` calls;
2. preserves one private production execution suite and one tally finalization;
3. identifies KEEP/CLEAR/SET/REBUILD ownership by class;
4. requires a zero base before rebuilding adjoint `+=` arrays and explicit Forward cleanup;
5. preserves raw MGACE and tally registry while resetting per-run state;
6. calls for a canonical source definition and clean active source copy;
7. addresses Type2's actual odd-seed period and its existing function-static cache;
8. requires native WW lower/survival/upper reinstallation and WW-OFF restoration;
9. proposes fresh-oracle gates for FF, FAF, AA, WW, model reuse, ordinary regression, and negative lifecycle cases; and
10. conservatively rejects nonzero fission production in the first supported profile.

These points agree with the independent pre-review criteria. The design's own static evidence reports 848 source files checked, no RMC source change, and no Stage 2 build or transport execution.

### Required design guardrails before implementation

The design is sufficiently detailed to submit for an implementation decision, but the following must remain non-negotiable implementation gates:

- The public API must bind and validate the exact objects it will transport; it must not rely on a caller-declared “initialized” token.
- A failed prepare after CLEAR must make the series unusable or return it to a defined safe state; it must never silently run with partial state.
- Reset must include terminal status, all live descendant/source banks, statistics tester state, all tally moments/index state, role flags, physical cutoff preservation, owner-scoped RNG cache state, WW derived fields, and per-run timer state.
- Normal RMC process finalization/output closure must remain outside every half-run.
- The test executable must call only implemented public production lifecycle APIs. It must not use a copied loop, friend access, placement-new, state injection, or a private bypass token.
- The test-target CMake design must explicitly solve production global ownership. The existing source glob includes `main.cpp`, which defines Output/WW/Timer/RNG/CalMode and other process globals. A driver must either share a factored production bootstrap/globals translation unit with `main`, or exclude exactly `main.cpp` and define each required extern once under matching feature macros; “create globals like main” is otherwise link-ambiguous.
- The currently proposed check for a denominator of exactly `N` is incomplete: a WEIGHT-variable distribution and probability/bias paths can alter source weights even if `SOURCE WEIGHT=1`. The restricted profile must reject all non-provably weight-neutral paths, or receipts and normalizations must use actual starting-weight sums.
- Resetting FixedSource/Tally timers does not isolate prepared-run statistics FOM: `CalcFlucInfluence` reads process-global `OTimer[Total]`, which runs from `OutputHeading` until `OutputEnding`. The design must add a prepared-run timing basis without altering ordinary behavior, or classify time/FOM as process-cumulative and exclude it from per-run lifecycle equivalence.
- A nonfissile H2O AA case validates only the zero-fission boundary. General fissile F→A→F→A remains unsupported until it has a separate approved dynamic gate with nonzero production contribution.

See [logs/risk-register.md](logs/risk-register.md) for the source-backed stop conditions.

## 4. Evidence review and dynamic-gate status

**SOURCE FACT.** An independent symbol search finds none of the Task 05 proposed Stage 2 methods in `RMC/src`:

```text
InitializePreparedFixedSourceRuns   absent
RunPreparedFixedSource              absent
FinishPreparedFixedSourceRuns       absent
PrepareFixedSourceRun               absent
ResetRunState / ResetRunScores      absent
ClearPreparedDerivedData            absent
ConfigurePreparedType2Substream     absent
ResetForPreparedRun                 absent
```

The `RMC` diff from `330f091e` to the inspected current `HEAD` is empty. Task 05's own recorded verification agrees: `changed_source_files: []`, `new_source_files: []`, `production_code_modified_by_stage2: false`, and `stage2_builds_and_transport_tests_executed: false`.

Therefore no dynamic evidence exists for the requested gates:

| Gate | Required result | Independent result |
|---|---|---|
| E1 | Forward → Forward vs two fresh references | Not implemented / not executed |
| E2 | Forward → Adjoint → Forward vs fresh references | Not implemented / not executed |
| E3 | Adjoint → Adjoint with derived-array control | Not implemented / not executed |
| E4 | WW ON with actual split/roulette and bank draining | Not implemented / not executed |
| E5 | One model initialization with stable model/registry identity | Not implemented / not executed |
| E6 | Ordinary fixed-source regression after Stage 2 | No Stage 2 modification exists to test |

Task 05's exact modular Type2 arithmetic is a valuable static design check, not an RMC execution result. Stage 1's ordinary one-shot regression is likewise not Stage 2 evidence: it validates the extraction under fresh ordinary calls, not persistent reuse or F/A transitions.

No numerical conclusion, deterministic equivalence claim, or independent transport recomputation is possible without inventing evidence. The exact comparison record is [logs/independent-comparison.md](logs/independent-comparison.md).

## 5. Verdict, boundary and decision point

### Final verdict

```text
DESIGN REVIEW ONLY
```

The Stage 2 proposal is source-aware and structurally consistent with the independently established lifecycle risks. It is appropriate to present for a human implementation decision. It is **not** an implemented persistent fixed-source lifecycle, and it provides no basis to claim that current RMC can already perform statistically independent same-process FF, FAF, AA, or dynamic-WW sequences.

### What this review supports

- Stage 1 has a single extracted production transport core with no duplicated history loop.
- Current source requires a formal Stage 2 reset/rebuild lifecycle before repeated prepared use can be considered safe.
- Task 05 names the principal source owners and proposes appropriate restricted-profile gates.
- Implementation should remain limited initially to the stated serial standard-MG neutron profile and must keep the listed guards.

### What this review does not support

- Acceptance (`ACCEPT` or `ACCEPT WITH LIMITATIONS`) of persistent execution.
- Any claim that `ExecuteFixedSourcePrepared` is directly reusable today.
- General fissile-material F/A cycling.
- CE, MPI/OpenMP, coupled particle modes, restart/surface source, burnup, Python source, TIME_REDUCE, or full F11 workflow support.
- Automatic transition to Stage 3.

### Next decision required from the user

If implementation is desired, the user must explicitly approve the concrete Stage 2 production file/interface scope in Task 05 §3 before any `RMC` modification. After implementation, the review must be reopened for fresh-oracle E1–E6 evidence. This review stops here.
