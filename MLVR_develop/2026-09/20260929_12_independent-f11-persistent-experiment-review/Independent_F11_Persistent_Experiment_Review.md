# Independent Review — F11 Persistent Session E0–E4 Experiments

> **Review object:** Task 11’s frozen protocol, status records, report and proposed experimental patch.  
> **Evidence status:** no E0–E4 runtime experiment has run. Every experiment is **BLOCKED**, not failed and not passed.  
> **Review rule:** planned checks and static patch validation are assessed as preparation evidence only. They cannot establish transport, reset, mode-switch, WW lookup, field extraction or performance results.

## 1. Scope

This is an independent evidence-sufficiency review of E0 performance decomposition, E1 same-process Forward→Forward, E2 Forward→Adjoint→Forward, E3 WW hot update and E4 tally reset plus in-memory Field extraction.

The review first wrote its acceptance criteria in [pre-result-acceptance-criteria.md](logs/pre-result-acceptance-criteria.md), before reading Task 11. It then read Task 11 and cross-checked only the required current RMC paths. No RMC/AIMC file, Task 11 file, shared status/index/knowledge-base file, benchmark or reference result was modified. No experiment was run.

**Mode C physical boundary:** a second run must represent an independent Monte Carlo sample. A plausible final tally is inadequate when source denominator, score moments, relative error, particle bank, or Forward/Adjoint material role can retain prior-run state.

## 2. Independent criteria

The pre-result criteria required the following before accepting an experimental conclusion:

- **E0:** repeated warm-cache trials, documented timer boundaries, raw timings, mean and sample standard deviation, observer-overhead check, and no claim beyond the tested model.
- **E1:** evidence that Run 2 enters transport, has its own histories, source denominator, RNG and banks, and matches a corresponding fresh process after the same tally finalization.
- **E2:** direct state evidence for ACE role, particle role, cutoff representation, source and derived adjoint arrays before and after both transitions, not merely terminal tally agreement.
- **E3:** the actual transport lookup must expose selected mesh bin, energy bin, and lower/survival/upper bounds, and must match a fresh WW2 run.
- **E4:** snapshots after `ProcessTally` must cover score moments, averages, RE, touched/index/registry state, denominator and Field ordering, then compare Run 2 to a fresh Run-2 oracle.

The complete criteria and anticipated false positives are retained in [pre-result-acceptance-criteria.md](logs/pre-result-acceptance-criteria.md).

## 3. E0 review — performance decomposition

**Classification: INCONCLUSIVE.**

### What is accepted

- Task 11 correctly refuses to treat the existing FixedSource timer as pure transport. It starts before `InitiateAll` and stops after final tally processing and output work. **SOURCE CONFIRMED:** [CalcFixedSource.cpp:67-80](../../RMC/src/CalcFixedSource.cpp#L67-L80) and [CalcFixedSource.cpp:719-749](../../RMC/src/CalcFixedSource.cpp#L719-L749).
- The frozen protocol has a reasonable narrow plan: one warm-up plus seven measured runs per role, warm filesystem cache, monotonic timing, sample standard deviation, closure checks and a probe-overhead gate. Task 11 protocol lines 61–86.
- The Task 11 report makes no numerical speedup or startup-share claim. It labels all cells unmeasured. Task 11 report lines 26–44.

### What is not accepted

No timing sample exists. The status record explicitly has zero runs, null timings and null startup fraction. No cache condition was executed, no warmup occurred, and no mean/std is available. E0 therefore cannot support even the limited statement that a named phase occupies an approximate share of time for this model.

### Dangerous false positive avoided

Calling the FixedSource timer “transport” would include initialization and tail work. Task 11 avoids that claim, but the proposed timing instrumentation itself remains uncompiled and unexecuted.

## 4. E1 review — same-process Forward→Forward

**Classification: INCONCLUSIVE.**

### What is accepted

- The frozen acceptance conditions are materially stronger than exit-code checks. They require two fresh-process references, Run-2 history/RNG/bank/denominator checks, all score/moment/Ave/RE arrays, registry state and same-process model-load counts. Task 11 protocol lines 42–59 and 88–99.
- The report correctly identifies the actual blocker. `CalcFixedSource` unconditionally calls `InitiateAll`, so two ordinary calls do not test reuse without an explicitly different entry path. **SOURCE CONFIRMED:** [CalcFixedSource.cpp:67-82](../../RMC/src/CalcFixedSource.cpp#L67-L82).
- The report does not claim that a second forward calculation worked. Task 11 report lines 46–52.

### What is not accepted

Neither fresh oracle nor same-process sequence exists. There is no Run-2 trace, finish-state observation, history count, bank snapshot, source denominator, RNG record, raw tally moment, registry result or output comparison. Thus no state is dynamically confirmed reusable or reset-safe.

### Evidence gap in the proposed patch

The protocol demands snapshots of `Score`, `ScoreTemp`, `Sum1`, `Sum2`, `Ave`, `RE`, all relevant counters/banks and tally registry/index state. The hook draft only declares one opaque `snapshot(...)` callback. The submitted patch does not itself specify or serialize those required fields. The later driver might do so, but it has not been supplied, compiled or reviewed. Therefore the proposal is not yet sufficient to prove E1 after implementation without a concrete snapshot schema.

## 5. E2 review — Forward→Adjoint→Forward

**Classification: INCONCLUSIVE.**

### What is accepted

- The frozen protocol correctly identifies that a test-only role contract must preserve the physical cutoff separately, rebuild adjoint arrays from zero, restore Forward state, and compare every stage to fresh references. Task 11 protocol lines 101–109.
- The report properly isolates four source-level hazards without mislabeling them as runtime failures:
  - `InitiateAll` only sets ACE adjoint state when the fixed-source flag is true.
  - MG adjoint cutoff handling converts configured physical energy in place to a group representation.
  - `treatAdjointMaterial` resizes then accumulates derived values with `+=`.
  - particle cache resizing alone does not demonstrate reset.

  These are **SOURCE CONFIRMED** at [InitiateAll.cpp:125-203](../../RMC/src/InitiateAll.cpp#L125-L203) and [TreatAdjointMaterial.cpp:21-105](../../RMC/src/TreatAdjointMaterial.cpp#L21-L105).
- The report preserves an important boundary. The frozen H2O case has no nonzero fission-adjoint contribution, so it cannot validate rebuild correctness for a fissile model. Task 11 report lines 54–67.

### What is not accepted

No Forward, Adjoint or final Forward transport run exists. No data show ACE/particle role, source role, cutoff restoration, WW context, derived-array contents, or an absence of repeated `+=` accumulation. Final-tally agreement would not be enough even if it existed.

### Evidence gap in the proposed patch

The patch times `treatAdjointMaterial`, but its declared callback API has no explicit record format for `p_bIsAdjoint`, max-adjoint energy values, particle role, `p_vAdjointCrossSection`, `p_vAdjointFissionCrossSection`, or their before/after hashes. The task driver is supposed to fill this gap, but it is absent. Approval must require a reviewable state schema and a predeclared fission limitation before interpreting E2.

## 6. E3 review — WW hot update

**Classification: INCONCLUSIVE.**

### What is accepted

- The frozen plan rejects array/file updates, collision counts and FOM changes as sufficient proof. It requires actual transport events, selected spatial and energy bin, and all three bounds. Task 11 protocol lines 29–40.
- The proposed P0 lookup placement is directionally correct. `setMeshWeightWindowBound` computes `ergPos`, then reads lower/survival/upper bounds; the hook is inserted after those reads. If compiled and correctly paired with particle context, it can observe the values actually supplied to splitting/roulette. **SOURCE CONFIRMED:** [WeightWindows.cpp:45-69](../../RMC/src/WeightWindows.cpp#L45-L69). The patch’s intended insertion is Task 11 patch lines 210–221.
- The plan also demands a fresh WW2 oracle and natural transport coverage of each selected spatial bin. This prevents a manual lookup from masquerading as transport evidence.

### What is not accepted

No WW2 run, event trace, selected-bin record, event hash, fresh WW2 comparison, or rank-local observation exists. The current serial-only scope also cannot establish MPI replica or shared-memory consistency.

### Patch boundary

P0 is an observability seam. P1 is not. The prepared-state token skips `InitiateAll` when consumed, so it deliberately changes control flow. It may be reasonable as a test-only seam, but it cannot be described as a no-risk logging patch or as proof of an existing hot-update capability.

## 7. E4 review — tally reset and memory Field extraction

**Classification: INCONCLUSIVE.**

### What is accepted

- The proposed reading point is correct in ordering: `ProcessTally` is called before summary output, so a snapshot immediately after it can observe final reduced/normalized tally data while the owner is alive. **SOURCE CONFIRMED:** [CalcFixedSource.cpp:719-742](../../RMC/src/CalcFixedSource.cpp#L719-L742).
- The plan appropriately distinguishes numerical resets from touched/index/registry state and requires a source-discriminating second field. Task 11 protocol lines 111–119.
- The report does not misrepresent the existing data path as a completed F10 Field API. Task 11 report lines 77–85.

### What is not accepted

There is no Run-1 or Run-2 snapshot, no fresh oracle, no memory Field array, no text comparison, no registry/touched-set result and no G+1 edge artifact. No conclusion can be drawn about tally reset completeness or in-memory extraction correctness.

### Source caution

`CDTallyData::SetZero` clears numerical score/sum/average/RE vectors, while per-history index sets are cleared by tally accumulation methods. **SOURCE CONFIRMED:** [TallyData.cpp:17-80](../../RMC/src/TallyData.cpp#L17-L80). This reinforces the protocol’s requirement to observe more than visible `Ave`/`RE`, but it does not prove the stated driver will correctly reset every tally family.

## 8. Energy-boundary review

**Classification: INCONCLUSIVE for E4, with a sound planned method.**

Task 11 correctly separates native WW’s `0`/infinity lookup sentinels from physical MGACE G+1 field boundaries. Its proposed physical ordering and reverse transport mapping are consistent with the checked source:

- MGACE stores center energy and lower bound in physically ascending order. [CheckMgAceBlock.cpp:38-60](../../RMC/src/CheckMgAceBlock.cpp#L38-L60)
- The source calculates the highest upper edge as `2*lastCenter - lastLower` for its upper-bound check. [GetMgCs.cpp:263-278](../../RMC/src/GetMgCs.cpp#L263-L278)
- `GetErgValue` maps internal MG transport state to physical center energy. [GetMgCs.cpp:241-261](../../RMC/src/GetMgCs.cpp#L241-L261)

The plan’s requested output of group count, centres, widths, 31 physical edges, monotonicity and tally-row mapping would be adequate for this frozen MGACE scope. However, it has not generated any value or mapping artifact. It cannot yet establish complete G+1 recovery.

## 9. Normalization review

**Classification: INCONCLUSIVE for runtime behavior, with correct protocol discipline.**

The plan separately records requested/completed histories and starting-weight denominator. It limits the expected equality to this unit-weight fixture. This is correct and avoids turning a fixture property into a general source-normalization rule. Task 11 protocol lines 48–53 and 88–99.

No sequence has recorded actual source weights or denominators. Therefore there is no evidence that the proposed driver will reset or use the correct denominator on Run 2.

## 10. Evidence gaps

1. **No dynamic evidence exists.** E0–E4 have zero RMC runs, zero fresh oracles, no compiled harness and no numerical, timing or event outputs.
2. **No concrete driver exists.** The driver is where P1’s reset, source update, RNG reset, output isolation, role transition and result comparison would occur. It cannot presently be audited.
3. **No callback implementation or schema exists.** The declaration-only probe header does not show which scalar/vector/index members will be emitted, hashed or compared.
4. **No exact input/build artifact exists.** The two-bin derived fixture, binary, compiler flags, run commands and input hashes remain planned rather than frozen executable artifacts.
5. **No nonzero-fission E2 coverage exists.** The declared H2O model cannot test an adjoint fission-array rebuild with nonzero content.
6. **No parallel coverage exists.** Any positive serial result would not settle MPI/shared WW or OpenMP lifecycle behavior.

## 11. Accepted facts

- **Task 11 accurately reports BLOCKED rather than PASS.** Its status records show `executed=false`, zero completed RMC and fresh-oracle runs, null measurements/comparisons and no runtime evidence.
- **The frozen criteria are substantively strong.** They target the most dangerous false positives for E0–E4 and preserve fresh-process comparisons.
- **The proposal is textually applicable to the current RMC baseline.** `git apply --check` succeeds against RMC `5cfb0f771d0c5a2127c90d57e51ce672a4e3b616`.
- **The proposed patch is isolated in intent.** It affects eight RMC source files only inside a not-yet-created task-private snapshot, leaves default production compilation conditionally unchanged, and introduces neither a production Session class nor a stated transport-physics algorithm change.
- **The patch has not been compiled or linked.** Textual applicability and default-off textual comparison do not establish build correctness or observer noninterference.

## 12. Rejected claims

The following claims would be unsupported by the present evidence and must not be made:

- E0 measured any startup, initialization, transport or persistent-session speed benefit.
- E1 showed that a same-process Forward→Forward sequence executes independently or resets statistics.
- E2 showed that Forward→Adjoint→Forward restores forward physics, avoids stale ACE state, or avoids derived-array accumulation.
- E3 showed transport reads WW2, including its survival and upper bounds.
- E4 showed tally reset correctness, post-normalization in-memory Field extraction, G+1 physical-boundary recovery or source-normalization behavior.
- Any persistent-session architecture is preferable, or impossible, based on E0–E4.

## 13. Remaining experiments

The existing E0–E4 protocol remains a credible outline, but a reviewable implementation package must precede execution:

1. **P0 implementation package:** callback definitions, thread-safe event/output schema, field list, observer-overhead plan and build linkage.
2. **P1 driver package:** exact field-by-field CLEAR/REBUILD sequence, armed-token lifecycle, source/WW/RNG updates, output policy, ownership assumptions and failure behavior.
3. **Fresh fixture package:** exact input files, source/card generator, binary/configuration hashes, dependency/compiler flags and fresh-process single-run equivalence gate.
4. **Comparator package:** lossless snapshots and a deterministic comparison that includes all protocol-required values, registry/index state and first-divergence output.
5. **E2 limitation record:** preserve the non-fissile H2O boundary. Do not claim fission-array rebuild validation without a separately approved fissile fixture.
6. **After serial evidence:** decide separately whether MPI/OpenMP coverage is warranted. Do not silently broaden this task.

## 14. Information sufficient for F11 design?

**No, not for selecting an execution architecture.**

The available information is sufficient only to design a bounded experiment harness and its evidence contract. It is not enough to select external process coupling, hybrid execution, or a persistent in-process RMC session. This remains true even if the proposed patch is judged a reasonable starting point.

The current source audits and Task 11 planning do support one limited design constraint: any internal experiment must model immutable/base state, per-run reset state, mode-derived state, output state and observation state explicitly. That is a test-design requirement, not an approved production architecture.

## 15. Questions for human decision

1. **Should a revised experimental package be authorized?** My recommendation is **not to approve P1 as currently reviewable**. It needs a concrete task-private driver, callback implementation and snapshot schema first. P0’s narrow instrumentation intent is reasonable, but it should be approved together with those implementation artifacts because it cannot currently compile or emit the planned evidence alone.
2. **Is the limited H2O E2 boundary acceptable?** It can test state transition mechanics but not nonzero fission-adjoint rebuild. Keeping it is appropriate for a first experiment if the report retains that limitation.
3. **What is the desired authorization granularity?** A staged approval can first permit a task-private, default-off P0/P1 implementation plus build/smoke checks, with a second decision before executing the frozen E0–E4 matrix. This does not authorize production RMC changes or F11 architecture work.

---

## Review conclusion

E0–E4 are all **INCONCLUSIVE** because none executed. The preparation work is careful about false positives and appropriately refuses to convert static preparation into runtime conclusions. The proposed patch is a plausible test-only starting point, but P1 is a control seam rather than passive instrumentation and its essential driver/reset/snapshot implementation is still absent. The present evidence supports refining and reviewing that experimental package, not claiming a persistent RMC capability or choosing F11 architecture.
