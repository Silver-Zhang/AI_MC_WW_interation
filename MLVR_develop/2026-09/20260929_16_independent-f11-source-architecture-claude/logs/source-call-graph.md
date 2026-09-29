# Source call graph

## SOURCE FACT — current fixed-source entry

```text
main.cpp
  → CheckIOFile / OutputHeading
  → ReadInputBlocks
  → RunPlot / GenerateInpFile
  → CDCalMode::RunCalculation
      → CDCalMode::CalcFixedSource
          → CDFixedSource::InitiateAll
              → CDMaterial::InitiateMatAce
              → CDFixedSource::InitiateTrspt
              → CDTally::InitiateTally
          → outer batch loop: DistributeSource
              → source-history loop: SampleFixSource → transport / descendants / tally
              → PrcoessBatchEnd
          → FinalizeLoadBalanceChecker
          → CDTally::ProcessTally
          → OutputSummary / optional output
  → OutputEnding → MPI_Finalize
```

- `main` makes a single `RunCalculation` dispatch after parsing, at `RMC/src/main.cpp:123-166`.
- Fixed-source dispatch occurs at `RMC/src/RunCalculation.cpp:83-89`.
- `CalcFixedSource` combines initialization, the original history/batch loops, tally finalization and output tail at `RMC/src/CalcFixedSource.cpp:67-749`.
- The neutron loop pushes a sentinel bank then repeats while `p_nFinishCalculate < 2`, distributing a batch, simulating source histories and calling batch end at `RMC/src/CalcFixedSource.cpp:106-715`.

## Hierarchy

| Layer | Meaning in current source | F11 meaning |
|---|---|---|
| Bootstrap | not an RMC native iteration concept | one ordinary Forward half-run before formal loop; no formal FOM/result selection |
| Formal iteration k | no current object | orchestration pair: Adjoint half-run then Forward half-run |
| Half-run | one configured `CalcFixedSource` call | one prepared Adjoint or Forward calculation |
| RMC batch | source-population interval distributed by `DistributeSource`, then `PrcoessBatchEnd` | unchanged internal transport accounting; F11 should not add a batch parameter |
| Source history | one source sample plus transport of its descendants | remains RMC’s statistical unit |
| Descendants | split/secondary particles drained from banks during a source history | not independent source histories or F11 iterations |

**DESIGN RECOMMENDATION:** Do not introduce an F11 “batch” setting. Use existing `FIXEDSOURCE PARTICLE POPULATION` separately for bootstrap, adjoint and forward NPS. Keep F11 iteration outside the RMC batch loop.
