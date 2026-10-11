# Independent Review — F11 Stage 0 Field Volume Normalization

> **Verdict: ACCEPT WITH LIMITATIONS.**  
> The archived Stage 0 evidence supports the F11 v1 conversion table for the tested serial standard-MGACE, neutron fixed-source, Cartesian Type=1 track-length mesh cases. It does not establish a general result for other estimators, meshes, source-weight conventions or parallel modes.

## 1. Scope and independent method

This review checked `20261011_02_f11-field-volume-normalization` without modifying it, RMC, the nuclear database, reference data or frozen design. Before reading that task’s report/results, I froze an independent source-level judgment and acceptance criteria in [pre-codex-source-judgment.md](logs/pre-codex-source-judgment.md).

I then read the current scorer, mesh parsing and fixed-source normalization paths; independently parsed every archived source/segment trace and `.Tally`; and recomputed the reference using my own three-dimensional ray/box clip implementation. The independent script imports no task-under-review analysis module. Its output is [independent-calculation.txt](logs/independent-calculation.txt).

No RMC transport was rerun.

## 2. SOURCE FACT — meaning of `Ave`

For mesh track-length scoring, the tally stores `weight × returned_mesh_segment_length` at [ScoreMeshTally.cpp:60-117](../../../RMC/src/ScoreMeshTally.cpp#L60-L117).

- Uniform Cartesian uses `CalcMeshTrck` ([ScoreMeshTally.cpp:39-45](../../../RMC/src/ScoreMeshTally.cpp#L39-L45)), which returns physical segment lengths and does not apply `p_bUseVol`.
- Heterogeneous Cartesian uses `CalcHeterMeshTrck` ([ScoreMeshTally.cpp:43-45](../../../RMC/src/ScoreMeshTally.cpp#L43-L45)). When `p_bUseVol` is true, that function divides each returned segment by its bin volume ([MeshFun.cpp:474-485](../../../RMC/src/MeshFun.cpp#L474-L485)).
- Fixed-source finalization uses `M = p_dTotStartWgt`, `Div = 1` ([ProcessTally.cpp:360-365](../../../RMC/src/ProcessTally.cpp#L360-L365)); `CalcAveRe` then divides the accumulated first moment only by `M × Div` ([TallyData.cpp:83-100](../../../RMC/src/TallyData.cpp#L83-L100)).

Thus no later volume correction compensates a uniform path. The source-level and dynamic conclusions agree:

| Cartesian TL path | `NORMALIZE` | `Ave` physical meaning | F11 Field conversion |
|---|---:|---|---|
| uniform | 0 | source-normalized weighted path length | `value = Ave / V` |
| uniform | 1 | source-normalized weighted path length | `value = Ave / V` |
| heter | 0 | source-normalized weighted path length | `value = Ave / V` |
| heter | 1 | source-normalized volume-average scalar-flux density | `value = Ave` |

RE is unchanged by a deterministic positive volume scaling. `value=0, RE=0` remains a zero-score result, not a proof of exact physical zero or zero uncertainty.

## 3. Uniform/heter physical and code-path equivalence

**Accepted.** The four inputs differ only in the intended mesh representation and `NORMALIZE` value.

- Uniform uses `SCOPE=2 1 1`, `BOUND=0 4 0 2 0 2`.
- Heter uses `SCOPEX=1 1`, `SCOPEY=1`, `SCOPEZ=1`, `BOUNDX=0 2 4`, `BOUNDY=0 2`, `BOUNDZ=0 2`.

Both describe two physical bins `[0,2]×[0,2]×[0,2]` and `[2,4]×[0,2]×[0,2]`, each 8 cm³. Inputs, source, material, 30-group MGACE, N=200, seed, source weight, estimator, `Energy=-1`, MPI/OMP state and print precision otherwise match.

The GDB trace records only `CalcMeshTrck` for uniform and only `CalcHeterMeshTrck` for heter, one call per source history. It records `usevol=0/1` and `heterflag=0/1` for each formal case. The normal and traced `.Tally` files are byte-identical per case, so debugger acquisition did not change the printed result.

The test only proves equivalent **equal-volume** bins. It does not dynamically test non-equal heter bins, oblique rays, three-dimensional flattening or cylindrical geometry.

## 4. Independent reference calculation

**Accepted.** My independent calculation uses raw archived `SOURCE` and `SEGMENT` lines, not `Ave`, `Sum1`, the target task’s `analyze.py`, or a mesh implementation.

For all four configurations, the archived trace has the same SHA-256:

```text
53936bd102ec7f9ba84a1c212cd8733cce5d17edd8dc530ee86032c90c1c20b5
```

It contains 200 source histories and 200 pre-mesh segments. The independent 3D clipping finds, for each of the two bins:

| Quantity | Value |
|---|---:|
| histories | 200 |
| histories with a 2 cm bin segment | 93 |
| zero-contribution histories | 107 |
| `Σ wL` | 186 cm |
| source denominator | 200 |
| volume | 8 cm³ |
| independent `L_ref = ΣwL/N` | 0.93 cm per unit starting source weight |
| independent `phi_ref = ΣwL/(N V)` | 0.11625 cm⁻² per unit starting source weight |
| independent RE | 0.0760368078814928 |

Zero-contribution histories remain in both the mean denominator and second-moment RE calculation. This avoids the false positive of conditioning on hit histories.

## 5. Results and accepted conversions

The independently parsed text results and independently recomputed reference agree for all 248 checked rows.

| Case | Path / Normalize | nonzero text-group `Ave` | RE | converted density |
|---|---|---:|---:|---:|
| uniform_n0 | uniform / 0 | 0.93 | 0.0760368079 | 0.11625 |
| uniform_n1 | uniform / 1 | 0.93 | 0.0760368079 | 0.11625 |
| heter_n0 | heter / 0 | 0.93 | 0.0760368079 | 0.11625 |
| heter_n1 | heter / 1 | 0.11625 | 0.0760368079 | 0.11625 |

The source has no collisions, scattering or group changes in the tally region. 0.6 MeV is located in internal MG group 13 and printed physical-energy group 18. The test correctly accounts for this reversal rather than using the internal group as the external Field index.

The task analyzer’s tolerance accommodates text formatting. My calculation uses the same printed precision and independently reproduces the values. The raw source/segment evidence makes the conversion result non-circular.

## 6. Normalization, source weight and `Normalize`

**Accepted with limitation.** Formal and GDB outputs show `Source Number=200`, denominator `M=200`, `Div=1`, and source components have weight one. The result therefore uses `N = starting-weight denominator` in this fixture.

This must not become a general F11 rule. The next validation that varies source-component weights/probabilities remains required before treating NPS as a universal Field denominator. The currently accepted rule is only the direct production value: use actual `p_dTotStartWgt` / recorded normalization denominator, not history count by assumption.

`NORMALIZE=1` is not globally equivalent to “density.” It controls heter mesh segment division but is not honored by the uniform splitter. Stage 0 correctly establishes that the adapter must inspect the actual scorer path and apply one central conversion coefficient.

## 7. Analysis-script audit

The target task’s `analyze.py` is materially sound for this fixture:

- it verifies formal/trace input and `.Tally` byte equality;
- it requires every history ID from 1 to 200;
- it includes all zero-score histories in both `sum1/N` and RE;
- it computes geometry using an independent slab-clipping method;
- it computes RE from raw per-history scores;
- it parses text and accepts differences only through frozen tolerances;
- it explicitly maps internal group to ascending physical text-group order.

My independent script reproduced the same results without importing it. No double volume divide was found. The target script does use target-task configuration values for N, G and volume. That is reasonable for a frozen experiment, but a reusable production verifier should derive/validate geometry metadata from the input or field file instead of trusting a parallel configuration record.

## 8. Outstanding issues and minimal gaps

1. **Non-equal heter bin volumes.** The current two bins both have volume 8 cm³. A minimal next test needs unequal Cartesian heter volumes to exercise per-bin `c_i` dynamically.
2. **Transport complexity.** This is a vacuum-path source test. It does not cover collisions, scattering, fission, WW descendants, adjoint, or material-dependent path variation.
3. **Source normalization generality.** Only unit weights and equal component probabilities were exercised.
4. **Zero-score semantics.** The output convention was checked, but a production Field writer must emit an explicit zero-score status instead of letting `RE=0` be interpreted as exact certainty.
5. **Archive portability.** The source snapshot and binary remain under `/tmp`; archives contain hashes and raw outputs, but a different machine needs the separately reproduced source/build environment for full execution replication.

These limitations do not invalidate Stage 0’s narrow conversion result.

## 9. Stage 0 readiness

**Ready for user acceptance and for the planned Stage 1 entry, with explicit scope controls.**

The required Stage 0 criterion in KB04 §14 is satisfied: nonunit volume, same physical grid under uniform and heter representations, distinct expected code paths, independent trajectory-length/volume reference, and no scorer/reference modification.

Stage 1 must treat this as an adapter contract, not a license to alter the common scorer. It must implement one central conversion function for Field export and target history score using `c_i`; preserve original `Ave`, `Sum1` and `Sum2`; attach a score-status flag; and reject unsupported paths rather than silently assuming `Normalize=1` means density.

## 10. Final assessment

| Question | Answer |
|---|---|
| Independent verdict | **ACCEPT WITH LIMITATIONS** |
| Accepted conversion table | the four-row Cartesian TL table in §2 |
| Evidence independent of `Ave` | **yes**, raw 200-history GDB source/segment records plus independent 3D clip arithmetic |
| Stage 0 ready for user acceptance | **yes**, within stated scope |
| Stage 1 may begin | **yes**, provided the Stage 0 conversion contract and open tests are retained |

The principal accepted fact is not that every RMC mesh tally is volume-normalized. It is that the current scorer distinguishes uniform and heter Cartesian paths, and F11 v1 must preserve that distinction through one explicit Field/response conversion policy.
