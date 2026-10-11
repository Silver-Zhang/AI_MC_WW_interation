# Gate Verification — Independent Review

## Gate status matrix

| Gate | Codex self-report | Independently verified in this review | Final status |
|---|---|---|---|
| G0 build/link/global ownership | PASS | **PASS** for Linux serial: current CMake/test target, untracked `globals.cpp`, linkage result, source list and test-OFF/OΝ evidence agree. One main and one singleton definition per executable were recorded. | **PASS** |
| Gate 1 ordinary regression | PASS | **PASS** as artifact verification: `ordinary-comparison-final-03/results.json` reports 123/123, physical tolerance 0; final CTest command exited 0 with 10/10 tests including existing ordinary cases and source-weight self-test. I did not rebuild or rerun the full ordinary matrix. | **PASS** |
| Gate 2 FF | PASS | **PASS**: independent raw-artifact agent compared FF persistent/fresh final/raw data; no non-time differences, physical tolerance 0. Receipts independently satisfy N/D/W0 and seed/offset checks. | **PASS** |
| Gate 3 FAF | PASS | **PASS**: independent final/raw snapshot and role/cutoff checks for all three runs; exact artifact equality and no comparator errors. | **PASS** |
| Gate 4 AA | PASS | **PASS**: independent final/raw snapshot checks for both A runs; exact equality and no comparator errors. This verifies the restricted nonfissile derived-array behavior, not general fissile production. | **PASS with scope limitation** |
| Gate 5 native WW | PASS | **PASS**: independent evidence contains WW1/WW2 split, roulette, bank and query counts; lower/survival/upper traces and OFF behavior were checked by the final comparator. FAF+WW also passed. | **PASS** |
| Gate 6 model/resource reuse | PASS | **PASS**: final gate summary records 34 half-runs, 20-run reuse, one initialization/registry identity, FD count 19 and RSS growth 84 KiB versus 4 MiB limit. Full raw resource remeasurement was not repeated here. | **PASS** |
| Gate 7 negative/failure handling | PASS | **PASS** as artifact verification: final negative results report expected nonzero exits/no false receipts/state preservation; source-weight owner self-test reports 7/7; stride runtime and profile/fission negatives are retained. I did not rerun all 66 child processes. | **PASS** |

## Independent receipt recomputation

A standalone read of `logs/gate-results.json` recomputed:

```text
rows=34 half_runs=34 histories=17500
all_N_D_W0=True
timing_scope_values=['legacy_mixed_not_per_run'] [False]
source_count_matches=True
finalize_once=True
roles=['A','F'] WW=['ww-0','ww-1','ww-2']
```

This check did not import Task 05 comparator code.

## Independent raw snapshot comparison

An independent evidence agent read the selected final artifacts under `logs/gates-04/`:

- FF, FAF, AA and WW comparator commands all exited 0.
- Physical tolerance was 0 and errors were empty for all four selected scenarios.
- Persistent/fresh `1-raw.json` SHA-256 was the same selected-run digest for all inspected pairs.
- FAF, AA and WW final snapshots were exact; FF differences were restricted to declared time/FOM fields.
- FF had 54 listed time exceptions across the two runs; no non-time physical mismatch was reported.
- WW1/WW2 had actual nonzero split/roulette/bank/query events.

The independent check did not rerun production binaries, regenerate artifacts, compare all 34 half-runs itself, or independently inspect every HDF5 dataset. Those limitations remain explicit.

## Comparator audit

The comparator source uses a closed set of seven statistics time/FOM member names and does not wildcard the whole StatisticsTester. It checks shape, type, numeric category and declared domains for the exception fields; comparator self-test reports all listed mutations behaving as expected. Raw `Sum3`, RE, PDF, largest-score, VoV and other non-time fields were included in negative self-tests.

## Timing interpretation

This review does **not** treat legacy StatisticsTester time/FOM as an isolated prepared-run metric. The implementation and receipts explicitly say:

```text
statisticsTimingScope = legacy_mixed_not_per_run
statisticsFomIsRunMetric = false
```

The new receipt's `prepareSeconds + transportSeconds + tallyFinalizeSeconds == mcSeconds` contract is separately checked by the comparator. This resolves the earlier design ambiguity by narrowing the contract rather than pretending that `OTimer[Total]` was reset per half-run.
