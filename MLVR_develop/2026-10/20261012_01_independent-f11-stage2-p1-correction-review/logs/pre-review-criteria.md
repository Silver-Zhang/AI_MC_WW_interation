# Independent P1 Correction Review Criteria

**Independence boundary:** Written before accepting Task 05's P1-correction PASS/READY conclusion. The criteria are based on Task 07's two findings, current production source, and the frozen F11 contract.

## P1-01 Universe fingerprint

A prepared-model definition fingerprint must be a deterministic semantic serialization of every geometry/Universe field that can change particle location, cell membership, material assignment, surface crossing, transform/fill behavior, or transport-relevant geometry interpretation within the supported profile.

It must:

- include Universe contents, not only `p_vUniverse.size()`;
- include relevant nested fill/transform/index/reference data actually consumed by geometry location;
- exclude transient caches, current particle location, allocator addresses, padding and run-mutated scratch state;
- remain stable over two valid runs without false rejection;
- be checked before CLEAR and before any new history starts;
- reject a mutation of an actually transport-relevant Universe field while preserving the previous run's tally, denominator, RNG and successful receipt state.

A negative test that changes only the Universe vector size is insufficient because the previous implementation already checked that size. A negative test that changes an unused field is also insufficient.

## P1-02 Native WW parameter validation

For the actual parameter types in the current RMC classes, prepared validation must safely reject malformed WW state before indexing malformed vectors or clearing prior state. It must validate:

- outer particle/energy-bin shape before accessing neutron entries;
- WUPN, WSURVN and MXSPLN as finite and contract-valid values;
- lower values and derived survival/upper values;
- any range/relationship constraints required by the existing native WW implementation;
- no new arbitrary restrictions that reject previously valid ordinary RMC native WW behavior.

Separate negative evidence must distinguish:

1. initial malformed WW model/parameter rejection;
2. a valid prepared model followed by a deliberate WW-parameter mutation;
3. wrong shape/empty model rejection.

The observed error must come from the intended prepared WW guard, not ordinary parser rejection or the model-definition fingerprint. For a post-run mutation, rejection must occur before CLEAR and preserve the previous run's state where the API contract requires it.

## Required regression evidence

The P1 patch must preserve:

- G0 ordinary/prepared build and singleton linkage;
- ordinary fixed-source regression and CTest;
- FF, FAF, AA and WW persistent/fresh comparisons at zero physical tolerance;
- actual WW split/roulette/bank behavior and OFF restoration;
- the existing restricted nonfissile/serial MGACE scope;
- Task 05's explicit legacy StatisticsTester FOM limitation.

New evidence must bind input, source patch, binary/build identity, command, exit code and snapshots. Historical `gates-04` evidence may be reused only when the correction cannot affect that behavior and the new evidence demonstrates the relevant unchanged behavior; corrected runs must not be silently relabeled as the old batch.

## Evidence labels

Every conclusion in the final review will be labeled one of:

- **SOURCE FACT** — directly verified in current RMC source;
- **DYNAMIC EVIDENCE** — directly verified from a correction-era command/result/snapshot;
- **INFERENCE** — derived from source and evidence;
- **REVIEW CONCLUSION** — final acceptance judgment.

## Final acceptance rule

Both P1s must be fully closed with production guard coverage and correction-era negative evidence. If either guard is incomplete, tests hit the wrong rejection path, or correction-era identity/evidence is insufficient, the result is `NEEDS CORRECTION` or `INCONCLUSIVE`, not acceptance. Even if accepted, scope remains restricted to Linux serial standard-MGACE neutron fixed source with nonzero fission rejected; Stage 3 is not started by this review.
