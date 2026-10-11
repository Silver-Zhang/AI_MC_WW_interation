# Task 05 Evidence and Design Review

## Evidence provenance

Task 05 identifies `RMC` baseline `330f091eb0296e0d0124237ba7d9a22b81aee852`. Its own `logs/design-verification.json` reports:

```json
{
  "source_files_checked": 848,
  "changed_source_files": [],
  "new_source_files": [],
  "production_code_modified_by_stage2": false,
  "stage2_builds_and_transport_tests_executed": false
}
```

Independent checks agree:

- Current `RMC` has no tracked or untracked diff after `330f091e`.
- No proposed Stage 2 symbol (`InitializePreparedFixedSourceRuns`, `RunPreparedFixedSource`, `PrepareFixedSourceRun`, reset/rebuild/substream methods) is present in `RMC/src`.
- Task 05 contains design documents and static-source artifacts only. It contains no Stage 2 driver, inputs, build output, transport output, receipt, persistent/fresh snapshots, comparator result, or `changes.diff` for Stage 2 production code.

## What can be credited

### SOURCE FACT

Stage 1 did extract the one ordinary execution suite and the one tally-finalization call. This review independently verified that the current code still has this shape; no duplicated transport loop or hidden initialization-bypass token was found.

### DESIGN REVIEW

Task 05 provides a technically informed, intentionally restricted proposal:

1. A stable-reference caller rather than repeated `RunCalculation` calls.
2. Private `Prepare` and public lifecycle calls distinct from Stage 1 helpers.
3. Explicit KEEP/CLEAR/SET/REBUILD ownership.
4. Explicit reset needs for tally activity state, statistics, banks, ACE-derived adjoint arrays, particle scratch, native WW state, timer state and RNG static cache.
5. Type2 period analysis with seed ranges checked against the actual `2^61` odd-seed period.
6. A strong planned oracle matrix: FF, FAF, AA, WW ON/OFF, model reuse, ordinary regression and negative gates.
7. A conservative nonzero-fission rejection boundary.

The proposal is aligned with the independent pre-review criteria in `logs/pre-review-criteria.md` and with source constraints described in `logs/source-call-graph.md` and `logs/state-ownership-audit.md`.

## What cannot be credited

None of the following exists as Stage 2 evidence:

| Requirement | Status | Why |
|---|---|---|
| E1 Forward → Forward | Not executed | No new production API/driver or persistent/fresh snapshots. |
| E2 Forward → Adjoint → Forward | Not executed | No role/cutoff/adjoint-array/cache comparison. |
| E3 Adjoint → Adjoint | Not executed | No runtime proof that `+=` arrays are zero-based per run. |
| E4 WW on, split/roulette, bank draining | Not executed | Stage 1 ordinary WW evidence cannot validate a repeated dynamic WW lifecycle. |
| E5 model reuse | Not executed | Static plan cannot prove one raw-load/tally registration/model initialization over a sequence. |
| E6 ordinary regression after Stage 2 | Not applicable / not executed | Stage 1 already supplied ordinary-refactor regression; no Stage 2 source change exists to regress. |
| negative lifecycle gates | Not executed | No lifecycle state machine or production errors exist. |

The archived modular-arithmetic result is a useful **E1 static mathematics check**, but it is neither a transport execution nor an RNG integration result. Likewise, Task 05's static source inspection cannot prove that the designed clear list is complete.

## REVIEW CONCLUSION

Task 05 is an implementation-ready **design proposal**, subject to normal source-review corrections discovered during implementation. It is not an implemented lifecycle and does not establish any repeated-run physical or statistical claim.
