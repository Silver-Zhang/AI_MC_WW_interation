# Independent Stage 2 review criteria

**Independence boundary:** Written before reading the Stage 2 task design, implementation plan, proposed lifecycle state matrix, or claimed test results. It is based only on AGENTS, STATUS, AGENT_CONTEXT, KB04 Stage 2 requirements, the Stage 1 interface names and current RMC source.

## Fixed-source half-run lifecycle that must be preserved

A normal half-run must remain ordered as:

```text
model initialization
→ transport preparation
→ source batch distribution
→ source-history sampling
→ primary history and all descendants
→ per-history tally aggregation
→ batch end / finish determination
→ final tally reduction and Ave/RE
→ ordinary optional output tail
```

The production history/batch loop must exist exactly once. A prepared entry may skip model initialization only after a complete, checked preparation contract. It must not skip transport preparation, history/batch accounting, tally finalization, or required per-run output state.

## State classification expected from source

### KEEP

Geometry topology, material definition, raw MGACE tables, fixed mesh/tally definitions, tally registry ownership, WW topology/energy grid/WWP configuration and physical source definition are candidate persistent state. Each candidate requires identity/content checks because process globals and value/reference boundaries can create aliases.

### CLEAR

Fixed-source completion/batch/history counters, starting-weight denominator, source/bank/descendant storage, external source temporary banks, tally Score/ScoreTemp/Sum1/Sum2/Sum3/Ave/RE, touched indices, run statistics samples, timer run state and per-run output handles need explicit clearing or recreation. `SetZero` alone is insufficient until indices/statistics are included.

### SET

NPS, source selection/location, role, WW enablement/bounds, RNG type/seed0/seed/stride/position/position_pre and output identity must be configured before each half-run.

### REBUILD

Forward/adjoint flags, physical-to-internal cutoff representation, adjoint cross sections/fission arrays, particle geometry/material/nuclear scratch cache, and derived WW survival/upper bounds must be rebuilt or explicitly revalidated. Existing `+=` in adjoint preparation requires a zero base.

## Failure modes the review must disprove

1. A second half-run terminates without transport because `p_nFinishCalculate` remains terminal.
2. Tally results retain earlier Sum1/Sum2, denominator, touched indices, registry side effects or statistical tester samples.
3. F→A or A→F leaves ACE/particle role/cutoff or derived adjoint arrays stale.
4. A helper operates on a copy while the transport loop uses a different original/global object.
5. Same named RNG objects refer to different local/global streams or RNG static fast-path state survives an incomplete reset.
6. WW-enabled descendants contaminate later source histories or the updated WW bounds do not reach actual lookup.
7. Per-run calls invoke process-wide output finalization, close needed handles or re-register MPI/process state.

## Required dynamic evidence if Stage 2 is implemented

- **E1 F→F:** fresh F1/F2 versus same-process F1→F2. Run 2 must show the requested/completed histories, reset finish state/denominator/banks/RNG, full tally state and fresh exact endpoint equality.
- **E2 F→A→F:** fresh references for all three runs, role/cutoff/adjoint-array/cache snapshots before transport and after finalization, plus final F exact equality.
- **E3 A→A:** nonzero-derived-array evidence or an explicitly limited nonfissile result. A second A must not double `+=` generated arrays.
- **E4 WW-on:** actual splitting/roulette plus lookup lower/survival/upper and bank-drain evidence.
- **E5 model reuse:** geometry/material/raw MGACE/tally definition identities or content stable; no input/ACE/tally initialization more than once.
- **E6 ordinary regression:** current ordinary fixed-source must retain its pre-Stage-2 behavior.

Fresh-oracle results, output exit code or final `.Tally` alone are insufficient. Any test-only access token, special driver or copied loop proves only that harness contract, not production capability.

## Scope boundary

A nonfissile H2O F/A result cannot validate nonzero adjoint-fission rebuild. MPI/OpenMP, CE, coupled particles, restart, burnup, nonunit/multiple source weights and dynamic external F11 workflow remain outside a serial MG neutron Stage 2 conclusion.
