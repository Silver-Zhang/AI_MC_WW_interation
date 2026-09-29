# Pre-Task 13 independent review criteria

**Independence boundary:** Written after reading only prior F11 source audits and Task 12’s pre-result criteria. No Task 13 report, verdict, harness source, raw result, manifest, or status was read before this note.

## Common acceptance conditions

- A positive result requires task-private provenance tied to RMC `5cfb0f771d0c5a2127c90d57e51ce672a4e3b616`, reproducible build identity, declared serial configuration, and proof that shared RMC remained unchanged.
- A fresh-process oracle must execute the full intended initialization and original transport loop under the same fixture/seed/source/WW/tally configuration. An equal result from a simplified harness is not sufficient.
- A same-process PASS must show the second run actually enters transport and must compare pre-reset, pre-transport and post-`ProcessTally` state. Exit code, output existence, or final Ave alone never suffices.
- P1 is a lifecycle-control experiment, not passive observation. A PASS can support only the explicit test contract. It cannot demonstrate that the default production entry point is persistent-session safe.
- A serial standard-MGACE neutron result cannot generalize to CE, coupled particles, MPI, OpenMP, burnup/restart, arbitrary source distributions, or arbitrary WW topology.

## E0 requirements

- Separate timing boundaries must be stated and non-overlapping at the accounting level.
- Warmups must be excluded from statistics. Measured repetitions, raw values, cache policy, mean, sample standard deviation, closure and probe-overhead evidence must be inspectable.
- Forward and adjoint populations and configuration must be recorded. A result may state only the stage share for the named small warm-cache fixture.
- False positive: interpreting a total FixedSource timer as pure transport or inferring production speedup from one cached model.

## E1 requirements

- Fresh F1/F2 and same-process F1→F2 must compare Run-2 requested/completed histories, `p_nFinishCalculate`, source denominator/starting weight, banks, RNG sequence/state, Score, ScoreTemp, Sum1, Sum2, Ave, RE, touched/index sets, registry and statistical-tester state.
- Reset must be visible before Run 2, and the tally owner/definition must remain retained rather than be rebuilt to imitate reuse.
- At least one zero-score and one nonzero bin must be independently checked from raw snapshots.
- False positive: a plausible Run-2 mean normalized with Run-1 moments or denominator.

## E2 requirements

- F→A→F must have fresh F/A/F references and state snapshots for fixed-source, ACE and particle roles, physical and internal cutoffs, source role, WW context, particle caches and derived adjoint arrays.
- The `TreatAdjointMaterial` accumulation path must be shown to begin from an explicit zero/rebuild base. Final Forward must restore forward interpretation and match fresh Forward.
- A non-fissile fixture cannot establish a nonzero adjoint-fission-array result.
- False positive: insensitive final tally agreement despite stale adjoint data, cutoff or cache.

## E3 requirements

- Raw transport events must show mesh index, physical energy, transport/internal group, selected WW energy bin, lower, survival and upper bounds. WW2 must be distinct and compared with a fresh WW2 sequence.
- Event count or hash alone is insufficient. At least representative raw events must be inspectable, including selected spatial/source-group coverage.
- False positive: update stored array but transport reads old derived or replicated bounds.

## E4 requirements

- The same tally definition and owner must be retained. Reset must demonstrate zero Score, ScoreTemp, Sum1, Sum2, Ave, initial RE state, touched sets/statistics state, plus unchanged registry/index configuration.
- Field arrays must be read after reduction and `ProcessTally`, then compared against both fresh values and text output with clear ordering metadata.
- False positive: raw or pre-normalized in-memory arrays, or a new tally object hiding residual state.

## Energy / normalization requirements

- G+1 extraction must provide group count, centres, widths, all physical edges, final upper edge, strict physical ordering and explicit tally-to-physical group mapping. It proves RMC memory availability, not `.Tally` self-description.
- Every run must separately record requested/completed histories, actual normalization denominator, initial source weight and component probability. Equality of denominator and N is only a unit-weight fixture property.

## Archive / evidence requirements

- Large excluded assets must have paths, sizes and SHA256 records. Verify locally available assets rather than trusting a report summary.
- Re-run only analyzers, comparators and hash checks against preserved evidence. Do not execute RMC transport.
