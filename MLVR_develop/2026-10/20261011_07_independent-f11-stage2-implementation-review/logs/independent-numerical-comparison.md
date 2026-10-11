# Independent Numerical Comparison

## Method and provenance

This review independently read the archived raw artifacts under Task 05 `logs/gates-04/` and recomputed key invariants with standalone logic. It did not import or execute the Task 05 comparator and did not modify artifacts or run production binaries.

## Selected raw comparisons

| Sequence | Persistent/fresh result | Independent finding |
|---|---|---|
| FF | comparator exit 0, physical tolerance 0, errors empty; 54 declared time/FOM exceptions | Raw and semantic metadata matched for selected pairs; differences were confined to declared time/FOM members. |
| FAF | comparator exit 0, physical tolerance 0, errors empty | Persistent/fresh raw/final/derived/start/end metadata matched for all three runs inspected. |
| AA | comparator exit 0, physical tolerance 0, errors empty | Both A runs matched fresh artifacts; no observed repeated derived-array difference. This is restricted nonfissile evidence. |
| WW | comparator exit 0, physical tolerance 0, errors empty | OFF→WW1→WW2→OFF matched; WW traces show actual split/roulette/bank/query activity. |

The selected persistent/fresh `1-raw.json` artifacts had the same SHA-256 digest:

```text
d7f444dd98fe6f55e57245834681d1b4dfc4c15d0dcdd8c656d6f867bd4d742b
```

This held for the selected FF, FAF, AA and WW run pairs. Cross-process identity snapshots are not byte-equal because they contain addresses; the independent check treated addresses as ASLR-dependent and compared semantic identities instead.

## Receipt recomputation

A standalone read of the final `logs/gate-results.json` recomputed:

```text
rows=34 half_runs=34 histories=17500
all_N_D_W0=True
timing_scope_values=['legacy_mixed_not_per_run'] [False]
source_count_matches=True
finalize_once=True
roles=['A','F'] WW=['ww-0','ww-1','ww-2']
```

For every final row, requested histories, completed histories, normalization denominator and sampled source histories agreed; initial-weight sums agreed; min/max source weight was 1; nonunit count was 0; source event count equaled N; and `FINALIZE_ENTRY` equaled 1.

Selected independent receipt checks decoded the archived bit patterns:

```text
0000000000408f40 → 1000.0
0000000000709740 → 1500.0
0000000000409f40 → 2000.0
```

The corresponding final positions were N and final-position-pre was N−1 for the inspected runs.

## WW evidence

The raw trace summaries independently contained:

```text
WW1: SPLIT=2072, ROULETTE=3397, BANK=3975, WW_QUERY=42711
WW2: SPLIT=3313, ROULETTE=5675, BANK=7499, WW_QUERY=76808
```

The comparator also checked lower/survival/upper values against the configured WW parameters. This supports actual WW use in the audited cases, not just an enabled input flag.

## Limits of independent recomputation

- I did not rerun production binaries or regenerate the 34 half-runs.
- I did not independently recompare every HDF5 dataset or all 34 raw traces.
- I did not independently verify the complete ordinary 123/123 matrix; I verified its archived result and final command output.
- The evidence cannot test geometry mutation or malformed WW-parameter mutation unless those negative cases are explicitly present; those API integrity gaps remain open in the source review.
