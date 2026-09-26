# Independent F07 Field Statistical Uncertainty Review

**Scope:** current RMC `5cfb0f771d0c5a2127c90d57e51ce672a4e3b616`; standard MGACE, ordinary fixed-source neutron, Cartesian Type=1 track-length mesh, `Energy=-1`, `Normalize=1`, MPI-off/OpenMP-off serial, text output. RMC source, tests, benchmarks, and reference results were not modified.

**Independence:** this review saved [`logs/pre-developer-claim-conclusion.md`](logs/pre-developer-claim-conclusion.md) before reading the F07 developer archive, F07 board entries, or Codex results.

## 1. Independent requirement definition

A field-bin RE is adequate only when each `(space, group)` entry has an individually accumulated uncertainty whose formula, statistical unit, normalization, and zero-score meaning are clear. The source family—not a track, collision, or WW offspring—must be the independent unit. For a nonzero field bin, the reported uncertainty scale must agree with independent-run scatter; scaling must be roughly \(N^{-1/2}\); and volume normalization must not change RE.

## 2. Statistics implementation chain

| Stage | Evidence | Finding |
|---|---|---|
| Mesh track score | [ScoreMeshTally.cpp:60-118](../../../RMC/src/ScoreMeshTally.cpp#L60-L118) | `p_vScore[mesh,energy] += p_dWgt × subtrack`; data index is per mesh × energy. |
| History termination | [CalcFixedSource.cpp:167-203](../../../RMC/src/CalcFixedSource.cpp#L167-L203) | A source family is transported, its neutron bank is drained, then exactly one `SumUpTally()` occurs. |
| First and second moments | [TallyData.cpp:43-51](../../../RMC/src/TallyData.cpp#L43-L51) | Adds current history score to `Sum1` and its square to `Sum2`, then clears it. |
| Final mean / RE | [TallyData.cpp:83-100](../../../RMC/src/TallyData.cpp#L83-L100), [ProcessTally.cpp:360-394](../../../RMC/src/ProcessTally.cpp#L360-L394) | Computes per-bin average and RE after fixed-source histories. |
| Output | [SingleTally.cpp:939-1004](../../../RMC/src/SingleTally.cpp#L939-L1004) | Each energy row prints its own `Ave, RE`; `Tot` is a separately accumulated all-energy bin. |

## 3. Exact RE formula

Let \(X_h(i,g)\) be the **complete tally contribution from external source history \(h\)** to field bin `(i,g)` after all split descendants finish. For the reviewed ordinary equal-weight source scope, \(N=p\_dTotStartWgt\) equals source population. Code accumulates

\[
S_1=\sum_{h=1}^{N}X_h,\qquad S_2=\sum_{h=1}^{N}X_h^2.
\]

For \(N>1\) and \(S_1\ne0\), `CalcAveRe()` gives

\[
\bar X=\frac{S_1}{N},
\]

\[
SE(\bar X)^2=
\frac{S_2-S_1^2/N}{N(N-1)},
\]

\[
RE=\frac{SE(\bar X)}{|\bar X|}
=\sqrt{\frac{NS_2/S_1^2-1}{N-1}}.
\]

This is the usual unbiased-sample-variance standard error of the mean divided by the mean. The source-total normalization applied to the tally mean is common to every observation and cancels in RE. The formula has no explicit negative-radicand clamp; very large \(N\), tiny variance, or cancellation therefore remains an untested numerical-stability risk.

For `N=1` the code sets RE to zero. For `S1=0` the code also sets RE to zero.

## 4. Independent statistical unit

The independent statistical observation is \(X_h(i,g)\), one external source family. `p_vScore` is a temporary current-history vector. At the end of the source family, `SumTallyBin()` creates `Sum1` and `Sum2` from that complete vector; it is not invoked per collision, track segment, or bank pop.

Fixed-source has operational batches (`PrcoessBatchEnd`), but the final estimator is history-level: the source loop invokes `SumUpTally()` after each family and `ProcessTally()` uses the history/source total. The reviewed RE is therefore not a batch estimator in this scope.

## 5. Weight-window correlation handling

WW splitting banks `n-1` copies with `calculateTime=splitNum-1` ([SaveSplitParticles.cpp:16-49](../../../RMC/src/SaveSplitParticles.cpp#L16-L49)). The controlling source-history loop repeatedly transports and pops bank members until no neutron bank member remains, **then** calls `SumUpTally()` ([CalcFixedSource.cpp:167-203](../../../RMC/src/CalcFixedSource.cpp#L167-L203)). Thus every split descendant contributes to the same current `p_vScore`, and their correlated contributions are squared only after aggregation into \(X_h\).

This is the required treatment: daughters are not falsely counted as independent observations. A dedicated ten-seed WW-on PTRAC run recorded a total **274,938 split** and **157,789 roulette/cutoff** events before its configured output caps, confirming this was an actual WW path.

## 6. Forward / Adjoint consistency

`ScoreMeshTallyByTL()` and `CalcAveRe()` contain no adjoint-specific statistical branch. Both forward and adjoint score current particle weight × track length into the same vectors and use the same history-based moments. Adjoint collision/importance sampling changes \(X_h\), not the definition of RE. Thus, in the declared scope, \(RE_F(i,g)\) and \(RE_A(i,g)\) have the same statistical definition.

## 7. Zero-score and rare-score semantics

An explicitly unreachable mesh field bin returned `Ave=0`, `RE=0`, and total RE zero. This follows from `p_vSum1[i] == 0 ? 0 : sqrt(...)`; **RE=0 is a guard/placeholder for an undefined relative uncertainty, not evidence of certainty.** A downstream MLVR consumer must not interpret it as high confidence.

The same reachable mesh had a nonzero, less frequently populated group 20 with `Ave=1.1505`, `RE=0.023248`, compared with group 1 `Ave=23.228`, `RE=0.0090991`. The code can express a larger finite uncertainty for a rarer nonzero bin. No NaN, Inf, or negative-variance output appeared in the tested ranges.

## 8. Normalize invariance

For ten independent N=10,000 runs, raw mesh score / normalized mesh score was approximately 200,000 cm³—the configured volume—and every `RE_raw - RE_norm` was exactly zero at printed precision. This is direct E3 evidence that mean and uncertainty are consistently scaled by volume:

\[
\frac{Ave_{raw}}{Ave_{norm}}=V,
\qquad RE_{raw}=RE_{norm}.
\]

## 9. N-scaling test

Five independent odd RNG seeds were run at each population:

| Histories | Mean RE | Seed SD of RE |
|---:|---:|---:|
| 2,500 | 0.0180424 | 0.0001120 |
| 10,000 | 0.00913662 | 0.0000678 |
| 40,000 | 0.00458392 | 0.0000041 |

\[
RE_{2500}/RE_{10000}=1.97473,
\qquad RE_{10000}/RE_{40000}=1.99319.
\]

Both are consistent with the expected factor of two for each fourfold increase in histories.

## 10. Reported RE vs empirical scatter

For ten independent N=10,000 analog runs of the selected normalized mesh/group bin:

\[
s_{emp}=8.94023\times10^{-7},
\qquad \sqrt{mean(\sigma_{reported,k}^2)}=1.05269\times10^{-6},
\]

\[
Q=\frac{s_{emp}}{\sqrt{mean(\sigma_{reported,k}^2)}}=0.84927.
\]

Ten repetitions are insufficient for a strict ratio=1 criterion, but the reported and empirical uncertainty scales agree within ordinary finite-repetition variation.

## 11. WW-on calibration

For ten independent N=10,000 WW-on runs of the same bin:

\[
s_{emp}=0.159123,
\qquad \sigma_{reported,RMS}=0.179255,
\qquad Q_{WW}=0.88769.
\]

PTRAC proves WW activation. Combined with static bank-drain evidence, this supports that WW-on RE remains calibrated at the source-family level in this small study. It does not establish every WW configuration, MPI behavior, or rare-field-bin distribution.

## 12. Per-bin indexing and output semantics

Each mesh × energy flattened entry has independent `p_vScore`, `p_vSum1`, `p_vSum2`, `p_vAve`, and `p_vRe`. `GetMeshErgPtr()` indexes a particular energy row; `GetMeshPtr()` indexes a separate total slot. In `inp.Tally`:

- **Group / Energy Bin / Ave / RE** refer to that one `(i,g)` field bin.
- **Tot** is an all-energy tally with independently accumulated moments and its own RE. It is **not** a group row and its RE must never be copied into the individual group field.

## 13. Comparison with Codex

The developer archive was read only after the pre-developer conclusion was written.

### Agreement

- history-level RE formula and source-family statistical unit;
- WW daughters drained before one history-level sum;
- RE zero-score output is not confidence;
- analog N-scaling and empirical calibration support C — Verify;
- serial text Cartesian scope is the correct boundary.

### Differences / corrections

1. The developer archive’s displayed intermediate quantity labelled \(s^2\) is actually \(SE(\bar X)^2\), because it includes an extra division by \(M\); its subsequent line `SE=s/sqrt(M)` would double-divide by \(\sqrt M\). Its final RE formula is nevertheless correct. This report gives the unambiguous sample-variance and SE formulas above.
2. The developer did not independently run a field-bin WW-on calibration. This review did: PTRAC confirms activation and ten WW-on seeds give \(Q_{WW}=0.88769\).
3. The developer’s Normalize runtime used unit volume, so it could not test scaling. This review used volume 200,000 cm³ and directly confirmed both mean scaling and RE invariance.
4. Both reviews correctly leave variable source weights, MPI/OpenMP, CE/coupled paths, and extreme numerical cancellation outside the conclusion.

## 14. Remaining limitations

- `RE=0` must have an explicit downstream invalid/zero-score policy; no mask is added here.
- Formula qualification assumes equally weighted ordinary source histories; weighted surface/fission/spontaneous source paths require separate review.
- No clamp guards a small negative radicand caused by cancellation.
- MPI/OpenMP, restart, source weighting, CE/coupled particles, other estimators, and all-field calibration remain unverified.
- The current F06 HDF5 output lacks an energy axis, so this only qualifies text field RE.

## 15. Final classification

**C — Verify** for standard MGACE fixed-source neutron forward/adjoint, Type=1 Cartesian track-length mesh, `Energy=-1`, `Normalize=1`, MPI-off/OpenMP-off serial, text `inp.Tally`, including native track-mesh WW with the reviewed source-family bank-drain control flow.

This is not A — Ready because zero-score RE has unsafe placeholder semantics, the equal-source-weight assumption bounds the formula, numerical cancellation is unguarded, and broad statistical/parallel coverage remains incomplete.
