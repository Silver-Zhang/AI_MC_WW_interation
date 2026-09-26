# Independent F06 Adjoint Spatial-Energy Field Review

**Scope reviewed:** current RMC `5cfb0f771d0c5a2127c90d57e51ce672a4e3b616`; standard MGACE fixed-source neutron adjoint; scalar track-length mesh tally; Cartesian mesh; MPI-off/OpenMP-off serial. No RMC source, test, benchmark, or reference file was changed.

**Independence record:** the source-only preliminary conclusion was saved in [`logs/pre-developer-claim-conclusion.md`](logs/pre-developer-claim-conclusion.md) before opening the only F06 archive. That archive was an empty template, so it contains no Codex implementation claim or result to compare.

## 1. Independent requirement definition

A first-version MLVR adjoint field must provide a stable, recoverable \(\phi^\dagger_{i,g}\) with all of the following:

1. a distinct spatial bin \(i\) and an unambiguous index/coordinate mapping;
2. a distinct physical MG group \(g\), without mixing physical MeV and internal group coordinate;
3. a defined estimator and normalization—specifically, scalar track-length flux density requires \(\sum w\ell/V_i\) per source weight;
4. the actual current transported particle weight, including adjoint collision corrections but no tally-side duplicate correction;
5. one tally mechanism for forward and adjoint histories, with mode differences arising only from transport state/weight;
6. deterministic text or machine-readable output capable of reconstructing space × group, including the energy coordinate and mesh geometry; and
7. per-bin RE when available, while reserving reliability/statistics analysis for F07.

## 2. Tally implementation chain

| Stage | Evidence | Finding |
|---|---|---|
| Input parser | [ReadMeshTallyCard.cpp:174-188](../../../RMC/src/ReadMeshTallyCard.cpp#L174-L188), [257-267](../../../RMC/src/ReadMeshTallyCard.cpp#L257-L267) | Reads physical MeV energy boundaries and `NORMALIZE`; `Energy=-1` is accepted specially. |
| MG energy initialization | [SingleTally.cpp:875-890](../../../RMC/src/SingleTally.cpp#L875-L890) | `Energy=-1` copies `cAceData.p_vNeuMltErgBins`; allocates `N_mesh*(N_energy+1)`. |
| Transport dispatch | [TallyByTL.cpp:24-54](../../../RMC/src/TallyByTL.cpp#L24-L54), [RayTracking.cpp:250-275](../../../RMC/src/RayTracking.cpp#L250-L275) | Fixed-source path calls mesh track-length scoring before moving the particle. |
| Track partition | [MeshFun.cpp:270-387](../../../RMC/src/MeshFun.cpp#L270-L387) | Divides a track among crossed Cartesian mesh cells, x-fastest flattening. |
| Score | [ScoreMeshTally.cpp:60-118](../../../RMC/src/ScoreMeshTally.cpp#L60-L118) | Scores current weight × each mesh subtrack; maps MG state to physical group-centre energy before bin lookup. |
| Accumulation | [SumUpTally.cpp:112-133](../../../RMC/src/SumUpTally.cpp#L112-L133), [TallyData.cpp:43-100](../../../RMC/src/TallyData.cpp#L43-L100) | History sums, means, and RE are per flattened score entry. |
| Fixed-source normalization | [ProcessTally.cpp:360-394](../../../RMC/src/ProcessTally.cpp#L360-L394) | Divides mesh data by `p_dTotStartWgt`, the source total weight. |
| Text output | [SingleTally.cpp:939-1004](../../../RMC/src/SingleTally.cpp#L939-L1004) | Emits each `(x,y,z), group, energy-boundary, Ave, RE`, plus per-mesh total. |
| HDF5 output | [MeshTallyHDF5.cpp:82-99](../../../RMC/src/MeshTallyHDF5.cpp#L82-L99) | Reshapes only spatial data and exports no energy-axis loop. |

## 3. Mathematical meaning

For Type=1 flux, `TallyFlux::score()` returns its flux argument unchanged ([TallyType.cpp:46-52](../../../RMC/src/TallyType.cpp#L46-L52)). `ScoreMeshTallyByTL()` sets that argument to the current `p_dWgt`, then multiplies the result by each mesh subtrack length ([ScoreMeshTally.cpp:61-85](../../../RMC/src/ScoreMeshTally.cpp#L61-L85)).

Therefore, with `NORMALIZE=0`, the output score is

\[
\frac{1}{W_0}\sum_{h}\sum_{\ell\in(i,g)}w_h\ell,
\]

a source-normalized **volume-integrated track-length scalar flux**, not flux density.

With `NORMALIZE=1`, the mesh track constructors divide each subtrack by its cell volume ([MeshFun.cpp:474-546](../../../RMC/src/MeshFun.cpp#L474-L546)). The estimator becomes

\[
\phi_{i,g} = \frac{1}{W_0 V_i}\sum_{h}\sum_{\ell\in(i,g)}w_h\ell.
\]

This is the desired scalar track-length flux density per unit source weight. The fixed-source divisor \(W_0\) is explicitly applied by `CalcAveRe(dM,1)` with `dM=cFixedSource.p_dTotStartWgt`.

### Runtime volume check

The independent adjoint case uses x bins of widths 5 and 15 cm and y/z widths 100 cm, so volumes are 50,000 and 150,000 cm³. For the first bin, `raw/normalized = 49,999.24`; for the second, it is `150,000.0`. This confirms `NORMALIZE=1` implements volume normalization in the selected Cartesian path.

## 4. Adjoint compatibility

`ScoreMeshTallyByTL()` has no `p_bIsAdjointParticle` branch. It reads `cParticleState.p_dWgt` directly. Fixed-source MG adjoint transport marks the source as adjoint and updates this same state weight during its collision processing; the next track is scored by the generic tally before movement. No tally-local adjoint correction, forward-only skip, or energy reinterpretation was found.

Accordingly, **within the frozen MG fixed-source adjoint transport scope**, the normalized Type=1 score can be interpreted as \(\phi^\dagger_{i,g}\): it is the scalar track-length field of the simulated adjoint history, including its current importance-sampling weight.

Native track-mesh WW acts before per-segment tallying; its splitting/roulette preserves expected weight. Thus WW changes variance/population but does not redefine the expected tally score. This audit does not separately re-validate WW unbiasedness.

## 5. Spatial indexing

- Supported tally meshes: Cartesian uniform, Cartesian nonuniform, and cylindrical nonuniform ([ScoreMeshTally.cpp:39-50](../../../RMC/src/ScoreMeshTally.cpp#L39-L50)).
- First-version Cartesian field is structurally complete. Flattening is `z*Nx*Ny + y*Nx + x` ([MeshFun.cpp:151-184](../../../RMC/src/MeshFun.cpp#L151-L184)); text output uses corresponding one-based `(x,y,z)` rows.
- Uniform Cartesian bounds use a non-exclusive upper-bound preliminary check, but the calculated bin index at the upper outer boundary becomes `N`, then the range guard returns `-1`; heterogeneous meshes use lower-inclusive/upper-exclusive checks. Exact outer-boundary ownership is consequently not uniformly expressed across mesh kinds. The source’s usual boundary nudge/tracking may avoid practical ambiguity, but it is an E1 edge-case limitation.
- Each crossed mesh receives its own subtrack contribution. The independent two-bin case demonstrated distinctly different values for both space positions and every nonzero energy group.
- With `NORMALIZE=1`, different Cartesian cell sizes have a common flux-density meaning, as confirmed by the runtime volume ratio above.

## 6. Energy/group mapping

MG source physical energy is localized to an internal reverse group coordinate by `LocateMgErgGrp()` ([GetMgCs.cpp:263-297](../../../RMC/src/GetMgCs.cpp#L263-L297)). In scoring, the mesh tally calls `GetErgValue()` ([ScoreMeshTally.cpp:87-101](../../../RMC/src/ScoreMeshTally.cpp#L87-L101)), which maps the internal group to its physical centre after reversing the index ([GetMgCs.cpp:231-260](../../../RMC/src/GetMgCs.cpp#L231-L260)). It then searches the physical-energy tally boundaries.

For `Energy=-1`, those boundaries are exactly the library’s physical group boundaries. Since a group centre lies strictly inside its own group, each transport group maps one-to-one to the intended tally bin. The printed output order is ascending physical-energy boundary order, not RMC’s reverse internal group numbering: row 1 is the lowest physical group and row 30 is the highest.

This is unlike the earlier native-WW mismatch: the mesh tally explicitly converts back to physical energy before comparing with physical bins.

**User-defined bins:** Physical `Energy` boundaries may cut an MG group. Then group-centre classification provides a deterministic bin but does not resolve the group internally. For MLVR’s desired exact MG field, use **`Energy=-1` only**. A user-defined field energy grid is a separate projected field, not necessarily one transport group per output bin.

## 7. Output representation

### Text

`inp.Tally` is sufficient for a first-version, serial space×MG field interface: each mesh block prints one-based spatial index, one-based group row, physical lower boundary, average, and RE. The data layout is recoverable from `[mesh][group]`, and the final row per mesh is the total—not an additional group.

### HDF5Mesh limitation

The independent `HDF5Mesh=1` run produced `MeshTally1.h5` with `/Type1` shape `(2,1,1)`, despite 30 energy groups. It contains spatial-only values (in this input those happened to be zero because the exporter receives the start of the flattened energy-containing block). There is no energy coordinate dataset. Consequently, **HDF5Mesh cannot be used as the F06 space×energy field output in the reviewed implementation.**

Text output is stable enough for a first serial interface, but a future machine-readable field consumer should parse text conservatively or add a dedicated energy-aware HDF5 output in a separately approved task.

## 8. Independent runtime tests

### Test A — spatial indexing

A 20 cm water slab was split into 0–5 cm and 5–20 cm mesh bins. Adjoint Type=1 `Energy=-1` output contained separately printed `(1,1,1)` and `(2,1,1)` field rows with markedly different values: totals `6.6024E-01` and `9.6597E+00` before volume normalization, respectively. Thus bins are independently accumulated rather than repeated/collapsed.

### Test B — energy indexing

The same adjoint output populated physical rows 21–30 (lower boundaries 1.738–15 MeV) in both spatial bins. The source maps to the high-energy transport group and the scattered/transposed history populates the physical high-group field rows. The table labels them in ascending physical-energy order; this confirms output coordinate order rather than internal reverse index. It is not a direct single-group source oracle, but it verifies the actual MG state→physical boundary scoring path for multiple active groups.

### Test C — spatial × energy cross check

For rows 21 and 30, both mesh cells had nonzero but different values. For example, raw adjoint scores were:

| Field coordinate | Score |
|---|---:|
| `(i=1,g=21)` | `5.6171E-02` |
| `(i=1,g=30)` | `6.7210E-02` |
| `(i=2,g=21)` | `4.4584E+00` |
| `(i=2,g=30)` | `3.8002E-01` |

This demonstrates an actual 2D field, not a spatial-only or energy-only duplicate.

### Test D — forward/adjoint mechanism

The same input was run forward and adjoint. Both invoke the same Type=1 mesh tally implementation and both output two spatial bins × 30 group rows. Differences in values and collision rate derive from transport state, not from a tally mode switch. Static inspection supplies the stronger proof because the estimator has no adjoint branch.

### Test E — volume semantics

The paired `NORMALIZE=0` and `NORMALIZE=1` mesh tallies produced raw-to-normalized ratios matching 50,000 cm³ and 150,000 cm³. This is targeted E3 confirmation of flux-density semantics for Cartesian mesh.

### Runtime limitation

The initial narrow-y/z run produced many geometry-location warnings and was discarded. The corrected wide transverse mesh still reports boundary-location warnings (12,217 adjoint; 24 forward) and source-above-MG-range warnings. The scored fields are nonzero and volume ratios exact, but this reduces the test from a clean high-confidence geometry oracle to targeted structural evidence. Raw/summary logs are retained.

## 9. F06 requirement comparison

| Requirement | Status | Evidence |
|---|---|---|
| Distinct Cartesian space bins | Met | E1 indexing + E3 two-bin output |
| Distinct MG groups | Met with `Energy=-1` | E1 group mapping + E3 nonzero rows |
| Scalar flux physical definition | Met only with `Normalize=1` | E1 estimator + E3 volume ratio |
| Adjoint current weight included | Met within F02 boundary | E1 generic `p_dWgt` use and no branch |
| Forward/adjoint same tally mechanism | Met | E1 no adjoint branch + E2 runs |
| Stable recoverable indices | Met for text | E1 flattening/output rows |
| Machine-readable space×energy field | Not met by HDF5Mesh | E3 HDF5 shape only spatial |
| Per-bin RE output | Present | text `Ave, RE` per group/mesh |

## 10. Comparison with Codex

Only [`f06-adjoint-spatial-energy-field`](../20260926_01_f06-adjoint-spatial-energy-field/README.md) existed when this comparison was permitted. It is an unfilled task template with no design, claim, code change, or result. Therefore there is no substantive Codex conclusion to affirm, reject, or identify as overclaimed.

## 11. Remaining issues reserved for F07

- RE estimator correctness, zero-score and low-count bins, correlation, and statistical acceptability;
- field uncertainty export/consumer contract;
- HDF5 energy-aware output design;
- geometry-boundary warning root cause and its effect on production field completeness;
- MPI/OpenMP tally reduction and ordering;
- additional physical response/tally validation.

## 12. Final classification

**C — Verify** within **standard MGACE fixed-source neutron adjoint, Type=1 Cartesian mesh tally, `Energy=-1`, `Normalize=1`, text `inp.Tally`, and MPI-off/OpenMP-off serial**.

The underlying track-length field chain is physically and structurally appropriate for \(\phi^\dagger_{i,g}\). The classification remains C rather than A because the production-quality runtime evidence is limited by persistent geometry-location warnings, no clean direct group-label oracle, lack of an energy-aware machine-readable output, and unreviewed F07 statistics. `Normalize=0` is explicitly not the required scalar-flux-density field.
