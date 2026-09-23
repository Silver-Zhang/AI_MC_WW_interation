# F04-B Deep Penetration Benchmark

## 1. Environment

| Item | Value |
|---|---|
| RMC source revision | `b7d8a946417eea091a30c09c233054aa077570ee` |
| Executable identity | RMC 3.5.0, `v3.5.0-alpha.0-310-gb7d8a946` |
| Executable SHA-256 | `f5720d8229c6d011bee5788ae787f80afbad2ab0dd1dafec34eab5ab4841a6d6` |
| Build | clean, out-of-tree `cmake -Dmpi=off -Dopenmp=off -DO2=on`; Release |
| Parallelism | MPI off; OpenMP off |
| Nuclear data | configured `RMC_DATA_PATH=/home/silver/NucXS_Library/RMC_DATA`; MGACE 30-group neutron library, `1001.50M`/`8016.50M` |
| Runs | five independent seeds: 101, 103, 107, 109, 113; 1,000,000 source histories per case/seed |
| Timing | `/usr/bin/time -p` wall-clock `real`; FOM recomputed as \(1/(RE^2T)\) from the reported total-tally RE and wall time |

A build warning from unrelated burnup code was emitted by the compiler; the build completed and the target executable was produced. Every simulation issued the same one-time warning that the 2 MeV source energy exceeds the MG library maximum group boundary. RMC clamps this energy into its highest group. Since this is identical in each paired case, it does not invalidate the WW-on/off comparison, but it limits interpretation to this source-to-top-group mapping.

The source revision, executable identity, input/script hashes, and raw formal outputs are recorded in [`logs/reproducibility-manifest.md`](logs/reproducibility-manifest.md). The full configuration/build logs and individual tally/stdout/stderr files are retained under [`logs/`](logs/).

## 2. Problem Description

### Geometry and physical correspondence

The benchmark is a genuine source–shield–detector configuration: a 100 cm long water slab, with transverse dimensions \(100\times100\) cm. It has ten 10 cm x-direction cells, each filled with 1.0 g/cm³ water (H-1/O-16). Leakage through the transverse and axial exterior is killed.

The physical forward interpretation is a source near \(x=0\), shield traversal through water, and a response region at \(x=90\)–100 cm. RMC is run in fixed-source multigroup neutron adjoint mode, so the computational source is a 2 MeV neutron point at \((97.5,0,0)\), while the score is total neutron track-length flux in cell 1 \((0<x<10\ \mathrm{cm})\). A nonzero source-to-tally adjoint response requires traversal of the full 100 cm water depth in the reverse physical direction.

### Case control

All items below are identical between cases: geometry, material, MGACE library, adjoint source, source weight, tally, population, RNG type, seed values, build, execution platform, and tally estimator.

| Difference | Case A | Case B |
|---|---|---|
| Native WW | absent | `WEIGHTWINDOW` with a 10×1×1 track mesh from x=0 to 100 cm |
| Lower bounds, x=0→100 cm | n/a | \(9.765625\times10^{-4},\ldots,0.5\) geometric progression |
| WW parameters | n/a | `WWP:N 5 3 5` |

No `WWE:N` card was supplied for Case B. This deliberately uses the native parser’s one default interval rather than treating physical-MeV boundaries as MG group labels. Thus this benchmark validates only the native single-interval/spatial WW configuration; it does not qualify a physical-energy `WWE:N` interface in multigroup adjoint mode.

The pilot at 100,000 histories produced nonzero total responses and showed substantially lower WW-on RE. It therefore met the predeclared escalation condition for the formal five-seed runs.

## 3. Case A Analog Result

| Seed | Response | RE | \(\sigma=R\,RE\) | Wall time (s) | FOM |
|---:|---:|---:|---:|---:|---:|
| 101 | 5.322700E-04 | 3.939900E-02 | 2.097091E-05 | 2.530 | 2.546297E+02 |
| 103 | 5.116500E-04 | 4.052200E-02 | 2.073308E-05 | 2.550 | 2.388241E+02 |
| 107 | 4.871500E-04 | 3.833500E-02 | 1.867490E-05 | 2.540 | 2.679016E+02 |
| 109 | 5.047600E-04 | 4.285600E-02 | 2.163199E-05 | 2.530 | 2.152069E+02 |
| 113 | 5.287900E-04 | 4.127800E-02 | 2.182739E-05 | 2.540 | 2.310622E+02 |

Independent-seed mean: \(R_A=5.129240\times10^{-4}\). Combining the independent within-run standard errors in quadrature yields \(\sigma_A=9.301117\times10^{-6}\), \(RE_A=1.813352\times10^{-2}\), mean wall time \(T_A=2.538\) s, and \(FOM_A=1.198241\times10^3\).

The seed-to-seed standard error of the five sample means is \(8.241877\times10^{-6}\); it independently supports the same comparison scale.

## 4. Case B WW Result

| Seed | Response | RE | \(\sigma=R\,RE\) | Wall time (s) | FOM |
|---:|---:|---:|---:|---:|---:|
| 101 | 5.163100E-04 | 1.662300E-02 | 8.582621E-06 | 1.590 | 2.276062E+03 |
| 103 | 4.977800E-04 | 1.699500E-02 | 8.459771E-06 | 1.610 | 2.150462E+03 |
| 107 | 5.329700E-04 | 1.654400E-02 | 8.817456E-06 | 1.620 | 2.255298E+03 |
| 109 | 5.204300E-04 | 1.663300E-02 | 8.656312E-06 | 1.620 | 2.231227E+03 |
| 113 | 5.120200E-04 | 1.689600E-02 | 8.651090E-06 | 1.620 | 2.162306E+03 |

Independent-seed mean: \(R_{WW}=5.159020\times10^{-4}\). Combining independent within-run standard errors gives \(\sigma_{WW}=3.861346\times10^{-6}\), \(RE_{WW}=7.484649\times10^{-3}\), mean wall time \(T_{WW}=1.612\) s, and \(FOM_{WW}=1.107368\times10^4\).

The seed-to-seed standard error of the five sample means is \(5.724782\times10^{-6}\).

## 5. Statistical Comparison

Using the required paired-case comparison with independently accumulated within-run standard errors:

\[
z=\frac{R_{WW}-R_A}{\sqrt{\sigma_{WW}^2+\sigma_A^2}}
 =\frac{5.159020\times10^{-4}-5.129240\times10^{-4}}
 {\sqrt{(3.861346\times10^{-6})^2+(9.301117\times10^{-6})^2}}
 =0.29571.
\]

Therefore \(|z|=0.29571<3\). The WW-on and WW-off response estimates are statistically consistent for this benchmark.

As an independent robustness calculation that uses the sample variability of the five seed means rather than RMC’s within-run reported RE values, \(z_{seed}=0.29676\). It leads to the same conclusion.

## 6. Efficiency Comparison

\[
FOM=\frac{1}{RE^2T}.
\]

| Case | Combined RE | Mean wall time (s) | FOM |
|---|---:|---:|---:|
| A: WW off | 1.813352E-02 | 2.538 | 1.198241E+03 |
| B: WW on | 7.484649E-03 | 1.612 | 1.107368E+04 |

\[
\frac{FOM_{WW}}{FOM_A}=9.24161.
\]

The WW case reduced the combined RE by a factor of 2.42 and had a lower mean wall time in this serial run. The measured FOM gain is approximately 9.24×. This is an observed performance result for the selected windows and machine; it is not an optimum-window claim.

## 7. WW Activation Evidence

A dedicated 100,000-history WW-on pilot with PTRAC recording enabled produced these true event counts before the configured PTRAC maximum-output limit:

| Event | Count |
|---|---:|
| `Neutron: Bank_from_Weight_Splitting` | 6,009 |
| `Neutron: Weight_Cut_off` | 31,449 |
| `Neutron: Escape` | 15,546 |
| `Neutron: Source Event` | 46,996 |

The raw event record is [`logs/pilot-ww-ptrac.txt`](logs/pilot-ww-ptrac.txt); its full event summary is [`logs/pilot-ww-ptrac-event-counts.txt`](logs/pilot-ww-ptrac-event-counts.txt). These events demonstrate both branches of the native WW mechanism: splitting into the lower-bound direction and roulette/cutoff of overrepresented low-importance trajectories. The pilot’s reported collision count also changed from 5.86 per source particle (off) to 2.69 (on), consistent with aggressive roulette/splitting reshaping path populations.

PTRAC output reports event positions but not particle weights in the selected format, so an event-by-event empirical weight histogram cannot be recovered from this run. The specified lower-bound ladder and `WWP:N 5 3 5`, the split/roulette events, the response RE reduction, and the statistical comparison provide the available activation evidence. **Cannot verify from current evidence** the complete realized bank-weight distribution without adding a separate diagnostic output capability or modifying instrumentation, which is outside this no-source-change task.

## 8. Conclusion

**WW unbiased and effective** — within the explicitly tested scope.

- The five-seed MG fixed-source adjoint water-shielding benchmark passes the predeclared unbiasedness criterion: \(|z|=0.29571<3\).
- Native track-mesh WW actually ran: 6,009 recorded splitting events and 31,449 roulette/cutoff events occurred in the activation pilot.
- The observed combined FOM ratio is 9.24161 in favor of WW-on.

### Boundary of this conclusion

This result supports only current RMC revision `b7d8a946`, serial MPI-off/OpenMP-off execution, 30-group neutron MGACE, the stated 100 cm water slab, one fixed 2 MeV adjoint point source, one source-end track-length flux tally, and the native one-interval track-mesh WW input. It does **not** prove correctness for continuous energy, photon/coupled transport, delayed-neutron adjoint treatment, point mesh, WW generation, other materials/geometries, other energy-dependent WW definitions, MPI/OpenMP, or MLVR-generated windows.

In particular, this test intentionally avoids `WWE:N` physical-energy boundaries because the tested native path uses a default single interval. It cannot resolve whether a physical-energy WW input is consistently mapped to the MG group coordinate in other configurations. The repeated 2 MeV-to-top-group source warning is also a declared source-energy boundary.
