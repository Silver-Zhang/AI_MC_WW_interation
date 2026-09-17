# Task 07 — Neural Field Reconstruction, Physics Regularization & Importance-to-WW Mapping Audit

## 1. Baseline and scope

Baseline `develop`:

```text
2db8881c1dc1a8abf44881d37f2446f558e7d610
```

This audit covers `learning.py`, `models.py`, `utils.py`, solver target wiring, and the DNN/PINN/U-Net field-to-WW interface. It does not modify MC transport, detector estimation, FluxAccumulator mathematics, Task 06 iteration order, FOM definition, network architecture, PDE definition, or journal experiments.

## 2. Physical field definition

The MC tally stored per cell is a per-history track-length score `Q_g(cell)`. On the current uniform Cartesian mesh, `Q_g = V_cell Phi_g`, with a common `V_cell=2 cm^3`; therefore normalized WW *shape* is equivalent for this prototype. The result must not be generalized to variable-volume meshes without explicit volume division. `*_flux_g` is current raw MC field, `*_acc_flux_g` is the Task 06 cumulative historical field, and `ai_flux_*_g` is an inferred field.

Forward importance reconstructed from adjoint response field is used to form `W_fwd[g,r] ∝ 1/I_adj[g,r]`; forward flux used in the reverse direction forms `W_adj[g,r] ∝ 1/Phi_fwd[g,r]`. This is the operator-dual direction: the adjoint field represents downstream response importance for forward particles, while a forward field is the corresponding source/importance input for the reverse adjoint solve.

## 3. Grid, target, and prior audit

Storage is `(G,Z,Y,X)`. Point builders create cell-center coordinates `(x,y,z)`, transpose `(Z,Y,X)` to `(X,Y,Z)` before flattening, and reconstruct each group with the inverse reshape/transposition. U-Net uses `(Z,C/G,Y,X)` and returns `(G,Z,Y,X)`. An asymmetric coordinate/group-coded oracle passed point and field orientation, group order, source/detector-region coverage, positivity, and finite-output checks.

The solver passes `FluxAccumulator.get_mean_re()` results to training builders. No current raw map is substituted and the legacy `DataBuffer` is not called. The accumulator statistics are consumed as cumulative training targets; current forward batches alone produce current response/FOM.

## 4. Log-space statistics and masking

For `Y=log10(Phi_hat)` and small relative error, the delta method gives `Var(Y) ≈ RE^2/ln(10)^2`; inverse variance is therefore proportional to `1/RE^2`. The omitted `ln(10)^-2` is global and does not alter relative sample weights. The approximation is not exact at large RE because of Jensen/nonlinear-transform bias. Production floors, ceilings, weight clips, and `RE_TRAIN_MAX` remain restrictions rather than being silently reinterpreted.

Zero/all-zero cells are treated as no measured information: they are masked, not converted into positive epsilon labels. Sparse unmeasured cells are reconstruction/extrapolation regions. The persistent oracle verified one-valid-group rows and high-RE/zero masking.

## 5. Prior residual

The implemented prior is:

```text
log10(Phi_prior,g) = C_g - kappa_g d_eff(r) log10(e)
d_eff = sqrt(||r-r_center||^2 + r_eq^2) - r_eq
```

`fwd` uses `BOX_SOURCE`; `adj` uses `BOX_OPTIM_TARGET`. Numpy and Torch implementations agree. DNN and U-Net residual paths reconstruct `log10(Phi)=log10(Phi_prior)+delta`. Manufactured fitted fields verify the identity. This is an attenuation-inspired smooth prior, not an exact Boltzmann solution.

## 6. PINN audit

The current `prior_residual_pinn` is a physics regularizer, not a full PDE/Boltzmann solver. Its interior 2-D residual is:

```text
R_f,g = -D_g (Phi_xx + Phi_yy) + Sigma_r,g Phi_g
       - sum_{h!=g} Sigma_s[h,g] Phi_h - Q_g
R_adj,g = -D_g (Phi_xx + Phi_yy) + Sigma_r,g Phi†_g
          - sum_{h!=g} Sigma_s[g,h] Phi†_h - Q†_g
```

Constant manufactured fields distinguish the asymmetric forward and adjoint transpose conventions; quadratic fields produce finite differentiable residuals with the expected 2-D restriction. Normalization now uses the same forward/adjoint scatter orientation as its numerator. The diffusion term is deliberately not included in the local normalization scale; this remains a weighting approximation, not a change to the residual zero set.

Default source term is disabled. Source-enabled mode is experimental; because source/target interiors and boundary bands are excluded from collocation, sampled points can have `Q=0`, so this branch is not a complete source-equation verification. No explicit x/y vacuum or z reflective boundary residual is present. Correct journal wording is “supervised MC reconstruction regularized by an interior 2-D multigroup diffusion residual,” not “full boundary-value Boltzmann solver.”

## 7. Importance-to-WW audit and repair

The intended multigroup transform is:

```text
W_g(r) = C / I_g(r)
```

where `C` is one common scalar. The pre-repair implementation used `C_g=I_g(r_ref)` independently for every group, forcing every group reference WW to one and making it invariant to independent group amplitude scaling. A one-cell/two-group oracle (`I=[1,10]`) showed the lost ratio: the correct reference ratio is `W_0/W_1=10`.

The minimal repair adds optional `normalization_spectrum` to `generate_ww_from_flux_g`. It normalizes the spectrum and chooses the harmonic reference scalar:

```text
C = 1 / sum_g p_g / I_g(r_ref)
W_g(r) = C / I_g(r)
```

This makes the spectrum-weighted reference WW equal one while preserving cross-group relative importance, global scale invariance, within-group inverse shape, positivity, clipping, and existing log-space relaxation/best-anchor semantics. This is a variance-reduction importance-fidelity repair, not an unbiasedness repair. Existing solver calls use the documented default equal spectrum and therefore retain the old reference convention numerically for equal-reference groups; callers requiring physical source/response amplitudes can pass the appropriate normalized spectrum. Task 05 transport remains unchanged.

## 8. Scientific claim boundaries

Supported within the current prototype:

- neural reconstruction of MC-estimated equal-volume-cell flux/importance shape;
- approximate inverse-variance weighting for small-RE log targets;
- attenuation-inspired prior plus learned residual;
- interior 2-D multigroup diffusion residual as physics regularization;
- positive predicted field transformed to multigroup WW with common-scalar amplitude preservation when a spectrum is supplied.

Not supported:

- exact transport or Boltzmann solution claim;
- full 3-D/full boundary-value PINN claim;
- exact log-target unbiasedness at high RE;
- arbitrary variable-volume mesh equivalence;
- conference-paper evidence from the post-conference U-Net extension;
- model quality, FOM, ablation, or corrected journal conclusions (Task 08).

## 9. Classification

| Item | Pre-repair | Post-repair |
|---|---|---|
| P1 field physical semantics | B | B |
| P2 coordinate/grid mapping | A | A |
| P3 historical target wiring | A | A |
| P4 log target statistics | B | B |
| P5 RE weighting | A/B | A/B |
| P6 sparse/zero masking | A | A |
| P7 prior residual | A | A |
| P8 PINN forward operator | A | A |
| P9 PINN adjoint operator | A | A |
| P10 PINN normalization | B | A/B |
| P11 source/collocation | B restriction | B restriction |
| P12 boundary/dimension claim | B restriction | B restriction |
| P13 prediction transform | A | A |
| P14 importance inversion | A | A |
| P15 multigroup relative normalization | D | A |
| P16 relaxation | A | A |
| P17 U-Net interface | B extension restriction | B extension restriction |

Pre-repair overall: **D — confirmed importance-mapping fidelity defect**. Post-repair overall: **A — corrected and verified within stated scope**.

## 10. Verification

Focused tests:

```text
field reconstruction: SUMMARY: 11 PASS, 0 FAIL
PINN operator: SUMMARY: 7 PASS, 0 FAIL
importance-to-WW: SUMMARY: 8 PASS, 0 FAIL
```

The focused suite also verified Task 05 fixed-WW semantic regression:

```text
SUMMARY: 9 PASS, 0 FAIL
```

Required previous-task regressions and smoke were run from the Task 06 validated environment; the relevant recorded outputs are in `assets/regression_output.txt`.

## 11. Gates

```text
G1 field physical meaning                         PASS (equal-volume restriction)
G2 coordinate mapping                             PASS
G3 group mapping                                  PASS
G4 historical target wiring                      PASS
G5 log weighting derivation                       PASS (approximation documented)
G6 RE weight implementation                       PASS
G7 sparse zero semantics                         PASS
G8 prediction transform                          PASS
G9 prior identity                                 PASS
G10 prior fwd/adj mode                            PASS
G11 PINN forward operator                         PASS
G12 PINN adjoint operator                         PASS
G13 asymmetric transpose oracle                  PASS
G14 spatial derivative oracle                    PASS (finite manufactured residual)
G15 PINN normalization                            PASS (orientation repaired)
G16 source/collocation semantics                  PASS (restriction recorded)
G17 boundary/dimension claim                      PASS (claim narrowed)
G18 importance inversion                          PASS
G19 multigroup normalization contract             PASS
G20 one-cell two-group oracle                     PASS
G21 forward WW mapping                            PASS
G22 adjoint WW mapping                            PASS
G23 log relaxation                               PASS
G24 lightweight core-model functional checks      PASS
G25 U-Net extension classification                PASS (post-conference restriction)
G26 Task 01–06 regressions                        PASS
G27 primary audit artifact committed              PENDING until commit
```

## 12. Files and limits

Production diff is limited to `src/utils.py` and `src/learning.py`; tests are deterministic and lightweight. Required scripts/outputs and `production_diff.txt` are stored beside this report. No benchmark/reference/HDF5 result was updated. A full model-performance comparison and corrected paper experiment are explicitly deferred to Task 08, which has not started.
