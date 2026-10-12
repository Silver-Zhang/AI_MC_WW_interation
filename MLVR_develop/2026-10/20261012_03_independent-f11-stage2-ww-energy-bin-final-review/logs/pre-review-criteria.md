# Independent WW Energy-Bin Final Review Criteria

**Independence boundary:** Written before accepting Task02's READY/PASS summary. The criteria derive from the current native WW source, Task08's unresolved findings, and the frozen Stage2 contract.

## Container contract

- WW-OFF must remain valid without requiring a neutron energy-bin entry.
- Any prepared path that will access `p_vEnergyBins[Neutron]` must first verify the outer particle vector contains that entry.
- The neutron entry must contain at least two boundaries; lower-bound storage must match `mesh_count * (boundary_count - 1)`.
- Boundaries must obey the actual RMC sentinel contract: determine the real `INFINITY_ENERGY` definition from source, then require the permitted first/last endpoint and reject malformed values, duplicates and descending order.
- Any NaN/Inf boundary must be accepted or rejected according to the explicit sentinel contract, never by accidental floating-point behavior.

## Endpoint contract

With B boundaries, valid WW interval indices are exactly `0 ... B-2`.

- below/at first boundary: first interval rule;
- internal equality: preserve existing native interval semantics;
- internal values: existing interval selection;
- exactly last boundary: final valid interval, never index B-1;
- above last boundary: defined clamp or controlled rejection;
- non-finite particle energy: controlled rejection before lookup.

`GetIntpltPos()` and `setMeshWeightWindowBound()` must be reviewed together; a caller must not be able to reach an invalid interval index.

## Ownership and validation order

Independently verify the responsibilities of:

1. `InitializePreparedFixedSourceRuns`;
2. `RunPreparedFixedSource` pre-CLEAR validation;
3. `InstallPreparedNativeState` before every neutron energy-bin and WWP access;
4. shared/native lookup code used by ordinary and prepared WW.

Run validation cannot be treated as proof that a separately callable installer is safe.

## Negative and regression criteria

Binding-time and post-successful-run malformed-container cases must reach the production guard, not parser rejection or only the old definition fingerprint. Post-run failures must occur before CLEAR and preserve the first receipt, tally, denominator and RNG state.

Required malformed cases: outer empty/short, neutron inner empty/one-boundary, duplicate, descending, non-finite interior/terminal, missing/incorrect sentinel, lower shape mismatch, first/internal/last endpoint equality and above-terminal energy.

Legal native WW must preserve existing split/roulette/RNG semantics and ordinary fixed-source output. FF, FAF, AA, WW OFF→WW1→WW2→OFF, and FAF+WW require fresh-process comparison where evidence is claimed.

A final `ACCEPT WITH LIMITATIONS` requires both remaining P1s closed with source and dynamic evidence. Otherwise classify `NEEDS CORRECTION`, `INCONCLUSIVE`, or `BLOCKED`.
