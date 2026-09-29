# Pre-result acceptance criteria — independent F11 E0–E4 review

**Independence boundary:** This note was completed before reading any result, patch, status, or log inside `20260929_11_f11-persistent-session-minimal-experiments/`. It uses only the two earlier F11 source audits and the frozen task request.

## Common criteria

- Every acceptance claim must identify the exact RMC revision, build configuration, input fixture, geometry, MG definition, source convention, mesh, tally, RNG seed/position policy, rank/thread settings, and output policy.
- A process exit code alone is never proof that a second calculation transported histories, reset statistics, or switched mode correctly.
- A fresh-process run with the same selected configuration is the primary numerical oracle. Snapshot values must be compared after the same reduction and normalization point.
- Unit source weights in a fixture may make history count numerically equal total source weight. This coincidence must not be used as a general normalization identity.
- A serial, neutron-only, standard-MGACE result cannot establish CE, coupled particle, MPI/OpenMP, burnup, restart, or arbitrary source/WW support.

## E0 — performance decomposition

### Should measure

Separate wall-clock intervals for external process/MPI startup, input/geometry setup, cross-section/MGACE load, mode-specific derived initialization, tally/bank preparation, history transport, final reduction/normalization, and output. The measurement must state whether each timer includes work from neighboring stages.

### PASS

At least repeated cold and warm trials with a documented cache protocol report mean and variation for each clearly bounded stage. The accepted claim is limited to a share of elapsed time for the named fixture and environment.

### Insufficient evidence

One timing, an unspecified timer, a total `CalcFixedSource` duration called transport, or an elapsed-time ratio without repetitions and cache disclosure.

### Most dangerous false positive

Treating the FixedSource timer as pure transport even though it includes initialization or final output, then extrapolating a small cached fixture result into a large-model performance argument.

## E1 — same-process Forward → Forward

### Should measure

Two truly sequential fixed-source Forward calculations in one process, plus fresh-process oracle runs. Capture second-run entry/exit, histories dispatched and normalized, `p_nFinishCalculate`, all relevant bank sizes/counts, source denominator/total start weight, RNG position, tally Sum1/Sum2/Ave/RE, touched/index registries, and post-reduction snapshots.

### PASS

Run 2 demonstrably enters and completes its transport loop, has independent source/history and normalization state, and matches a fresh Forward oracle within predetermined numerical/statistical tolerance. Run-2 raw and derived tally state must demonstrate no Run-1 contribution.

### Insufficient evidence

Exit zero, a text output file, equal-looking final mean alone, or history count alone. A matching mean can conceal inherited Sum1/Sum2 and denominator state.

### Most dangerous false positive

Run 2 reaches output but inherited Run-1 tally sums or normalizer produce a plausible Ave/RE.

## E2 — Forward → Adjoint → Forward

### Should measure

A same-process F/A/F sequence with fresh-process Forward and Adjoint oracles. At each transition observe ACE adjoint role/flags, particle role, mode-dependent cutoff/energy representation, source role, WW selection context, and sizes/values of derived adjoint arrays before/after rebuild. Detect whether `TreatAdjointMaterial` accumulates on retained arrays.

### PASS

All three runs execute. The adjoint run has evidence of actual adjoint state and source role. The final Forward run is shown to restore its forward representation and independently matches the fresh Forward oracle. Transition diagnostics rule out stale derived arrays, including repeated accumulation.

### Insufficient evidence

Only the terminal tally agrees, a bool flag changes, or the adjoint run exits normally. End-tally agreement cannot establish that the final Forward state was restored.

### Most dangerous false positive

Forward and final Forward tallies appear close while the third run retains adjoint-transformed cross sections, group cutoff, source role, or accumulated arrays in an insensitive test problem.

## E3 — WW hot update

### Should measure

A same-process run with fixed mesh/group and deliberately distinguishable WW1/WW2 bounds, plus a fresh WW2 oracle. Instrument or otherwise make observable selected spatial bin, selected energy group, lower, survival, and upper bounds used at actual lookup. Check rank-local copies when MPI is in scope.

### PASS

The actual lookup reads WW2 for selected bins/groups and all three bounds match the fresh WW2 path. The changed run agrees with a fresh WW2 run for predeclared diagnostics and no stale derived/replicated state is present.

### Insufficient evidence

Updated input/file/array, changed FOM, or changed collision count. None identifies the bound actually read by transport.

### Most dangerous false positive

WW2 is stored but lookup reads stale survival/upper bounds, an old geometry-linked copy, or a non-root MPI replica.

## E4 — tally reset and memory Field extraction

### Should measure

Two runs with intentionally distinguishable source/field values using one tally definition. Capture all tally families needed by the Field contract after `ProcessTally`, reduction, and normalization. Record Sum1, Sum2, Ave, RE, touched sets, registry/index mappings, source denominator, mesh dimensions, tally-group mapping, and in-memory snapshot timing.

### PASS

Run-2 snapshots contain no Run-1 contribution and match a fresh Run-2 oracle. Arrays are read only after reduction/normalization. The extraction proves value/RE plus ordering metadata rather than raw storage alone.

### Insufficient evidence

Only text/HDF5 output, only Ave, or a memory pointer read before final reduction/normalization. A reset of visible values without Sum1/Sum2/registries is incomplete.

### Most dangerous false positive

Run 2 has a different mean but retains Run-1 variance, touched indices, sum buffers, or denominator, yielding plausible but invalid RE and Field values.

## Energy-boundary acceptance criteria

If an experiment claims in-memory recovery of G+1 physical edges, it must record group count, tally group mapping, every centre and width, derived lower/upper edge relation, final upper edge, and ascending physical-energy order. It must explicitly distinguish internal MG group coordinates from physical energy. Centre/width information alone is insufficient unless the exact RMC convention and final-edge construction are demonstrated.

## Normalization acceptance criteria

Every run record must separately state dispatched/source-history count and the actual denominator used for tally normalization. A test with unit starting weights may report equality as fixture-specific evidence only. It must not establish `N histories == total starting source weight` as a general rule.

## Patch review criteria if experiments are blocked

A proposed experimental patch is acceptable only if it is test-gated or opt-in, exposes observations required above, leaves default production behavior unchanged, avoids transport-physics changes, avoids new MLVR/session architecture, and has a narrow reversible diff. Prefer test-only seams where practical. A proposal that resets state or adds a controller as part of the probe must be reviewed as an implementation design, not a minimal experiment patch.
