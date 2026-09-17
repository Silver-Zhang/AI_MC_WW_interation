# task07-field-reconstruction-audit

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-05 |
| 状态 | 已完成（A — field semantics and importance mapping repaired/verified） |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | Claude Opus 5 |
| 涉及文件 | `src/learning.py`, `src/utils.py`, `src/solver.py`, focused tests, primary report/assets |
| 分支 / 提交 | `develop` / `956f951f4fe34f29863eab547603530e6ef1fa84` |

## 0. 人类阅读摘要

Task 07 verifies the historical MC field → statistical target → DNN/PINN/U-Net → positive field → multigroup WW chain. The current field is a per-history cell-integrated track-length score; scalar flux differs by the common cell volume, so the normalized-field claim is restricted to the current equal-volume mesh.

Confirmed and repaired: PINN adjoint residual normalization used forward scatter orientation in its denominator; multigroup WW generation independently normalized each group and erased cross-group importance amplitudes. Coordinate/group/prediction orientation and prior residual identity were verified. The PINN is an interior 2-D diffusion regularizer, not a full boundary-value Boltzmann solver.

## 1. Design and causal chain

```text
historical unbiased MC field (G,Z,Y,X)
  -> log10 target + RE-derived confidence
  -> model output (log flux or prior residual)
  -> positive predicted importance/flux
  -> W_g(r)=C/I_g(r)
  -> next transport WW
```

Forward adjoint field is the response importance used to construct forward WW; forward flux is the dual input used to construct adjoint WW. Current raw, historical cumulative, and AI fields remain distinct.

## 2. Confirmed findings

- Grid storage `(G,Z,Y,X)`, point coordinates `(x,y,z)`, and U-Net `(Z,C/G,Y,X)` conversions passed asymmetric coordinate/group sentinels.
- `FluxAccumulator` output is the actual training input; zero scores are retained in the accumulator and zero/high-RE cells are masked as “no information”.
- `Var(log10 Phi) ≈ RE²/ln(10)²` justifies inverse-RE-squared weighting only in the small-RE delta-method regime; high-RE Jensen/truncation limitations remain documented.
- `log10 Phi = log10 Phi_prior + delta` passed numpy/Torch and fitted prior identity checks in both modes.
- Forward PINN scatter is `S[h,g]`; adjoint is `S[g,h]`. The adjoint normalization denominator now follows the same transpose orientation.
- Source term is disabled by default and source-enabled collocation can exclude the source region; no physical boundary residual is implemented.
- Pre-repair WW used `I_g(r_ref)/I_g(r)`, forcing every group’s reference WW to 1. For `I=[1,10]`, this loses the expected reference ratio 10.
- Repair: optional `normalization_spectrum` selects one common harmonic reference scalar `C=1/sum(p_g/I_g(r_ref))`; solver passes forward and adjoint spectra. This preserves cross-group amplitude ratios while keeping global scale invariance, spatial inverse ratios, clipping, and log relaxation.

## 3. Verification outputs

```text
field semantics: SUMMARY: 11 PASS, 0 FAIL
PINN operator: SUMMARY: 7 PASS, 0 FAIL
importance-to-WW: SUMMARY: 8 PASS, 0 FAIL
Task 05 regression: SUMMARY: 9 PASS, 0 FAIL
mesh: 5 PASS 0 FAIL
final metrics: 9 PASS, 0 FAIL
adjoint: 12 PASS, 0 FAIL
reciprocity: 10 PASS, 0 FAIL
accumulator history: 7 PASS, 0 FAIL
iteration dataflow: 19 PASS, 0 FAIL
smoke: 89 PASS 0 FAIL
lightweight solver compatibility: exit=0
```

## 4. Classification

| Item | Pre | Post |
|---|---|---|
| P1 field semantics | B | B, equal-volume restriction |
| P2 coordinate/grid | A | A |
| P3 historical wiring | A | A |
| P4 log statistics | B | B, approximation stated |
| P5 RE weighting | A/B | A/B |
| P6 zero masking | A | A |
| P7 prior residual | A | A |
| P8 forward PINN | A | A |
| P9 adjoint PINN | A | A |
| P10 normalization | B | A/B, orientation repaired |
| P11 source/collocation | B restriction | B restriction |
| P12 boundary/dimension | B restriction | B restriction |
| P13 prediction | A | A |
| P14 inversion | A | A |
| P15 multigroup normalization | D | A |
| P16 relaxation | A | A |
| P17 U-Net extension | B restriction | B restriction |

Overall pre-repair: **D** (importance-mapping fidelity defect). Overall post-repair: **A within stated scope**.

## 5. Gate matrix

`G1–G10 PASS`; `G11–G15 PASS` (adjoint transpose and manufactured derivatives/normalization); `G16–G17 PASS with source/BC restrictions`; `G18–G24 PASS`; `G25 PASS as post-conference extension restriction`; `G26 PASS`; `G27 PASS after committed primary report and assets`.

## 6. Reproducibility and restrictions

Environment: conda `torch`, Python 3.11, existing NumPy/Numba/PyTorch/h5py/matplotlib; deterministic tests use explicit seeds where sampling is involved. No benchmark/reference/HDF5 result was updated.

The task does not establish model quality, FOM improvement, full 3-D PDE validity, full boundary conditions, arbitrary variable-volume support, or exact log-space unbiasedness at high RE. U-Net evidence is post-conference interface evidence only. Task 08 corrected experiments, ablations and journal tables were not started.

## 7. Archive and commit

Primary report and assets are committed under `docs/journal_revision/task_07_field_reconstruction_claude/`; this archive contains the work log and raw outputs. Production snapshot is in the primary asset `production_diff.txt`.
