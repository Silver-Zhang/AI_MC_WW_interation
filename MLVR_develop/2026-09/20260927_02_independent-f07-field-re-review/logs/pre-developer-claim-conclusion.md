# Pre-developer-claim independent conclusion — F07

Written before reading any F07 archive, F07 STATUS/INDEX result, or Codex claim.

## Exact RE formula

For a fixed-source field bin, the independent observation is the **complete source-history family contribution** \(X_h\), including every split/banked descendant. The code accumulates

\[
S_1=\sum_{h=1}^N X_h,\qquad S_2=\sum_{h=1}^N X_h^2.
\]

For `dM=N>1`, it reports

\[
\bar X=S_1/N,\qquad
RE=\sqrt{\frac{NS_2/S_1^2-1}{N-1}}
=\frac{\sqrt{[S_2-S_1^2/N]/[N(N-1)]}}{|\bar X|}.
\]

Thus the numerator is the standard error of the mean and `RE` is its relative form. For fixed-source final normalization the common total-start-weight divisor does not change RE. With variable source weights, source-weight normalization and the history-variance formula need separate qualification; this review uses equal source weights.

## Independent sample unit and WW correlation

The outer fixed-source loop exhausts the split-particle bank before calling `SumUpTally`. The temporary field bin score is therefore the sum for the original source family, and only then are `p_vSum1` and `p_vSum2` incremented. Split offspring are not entered as independent variance observations in serial fixed source. Forward/adjoint share this machinery; adjoint changes field contributions through transport weights only.

## Zero and rare score

`p_vSum1==0` forces `RE=0`. This is an output/denominator guard, not evidence of high confidence. A rare nonzero field bin should instead retain a large finite RE, absent negative-radicand handling.

## Independent runtime observations

- 5-seed N scaling: mean REs 0.0180424 (N=2500), 0.00913662 (N=10000), 0.00458392 (N=40000); ratios 1.9747 and 1.9932, as \(N^{-1/2}\).
- 10-seed N=10000 empirical check: mean reported sigma \(1.05269\times10^{-6}\), observed SD \(8.94023\times10^{-7}\), \(Q=0.8493\), compatible in scale for 10 repetitions.
- Normalize check: raw/norm = 200,000 cm³; all ten RE differences are exactly zero.
- WW enabled test has lower RE but no activation event recording yet; it cannot be positive WW-calibration evidence without PTRAC confirmation.

## Preliminary classification

**C — Verify**, within standard MGACE fixed-source neutron forward/adjoint Type=1 Cartesian `Energy=-1` `Normalize=1` serial text field, subject to WW activation proof and variable-source-weight/parallel limits. No F07 developer record has been read at this point.

## WW activation/calibration completion

A separate 10-seed WW-on rerun with PTRAC emitted 273,? split and 155,? roulette events per seed (exact per-seed counts in `logs/ww-ptrac-events.json`; PTRAC output capped at 100,000 events per run). Thus WW definitely activates. Its field-bin calibration gives mean 22.9702, empirical SD 0.159123, RMS reported sigma 0.179255, and \(Q=0.88769\). This is compatible in scale for only 10 independent runs and supports, but does not prove, history-family RE calibration under WW.

The final preliminary classification remains **C — Verify**. The outstanding concern is that `CalcAveRe` uses total starting weight as `dM`, even though its derivation needs a count of equally weighted independent histories. The audited equal-unit-source scope has `dM=N`; non-unit or unequal source weights require separate qualification.
