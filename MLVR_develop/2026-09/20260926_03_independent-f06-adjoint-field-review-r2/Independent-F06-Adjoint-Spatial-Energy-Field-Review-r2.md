# Independent-F06 Adjoint Spatial-Energy Field Review — R2

## 1. Independent requirement definition

A first-version MLVR field must provide a deterministic scalar flux density indexed by spatial mesh cell and MG transport group:

\[
\phi^\dagger_{i,g} = \frac{1}{W_0V_i}E\left[\sum_{h}\sum_{\ell\in(i,g)}w_h\ell\right].
\]

Minimum conditions are: independently addressable spatial bins; one-to-one MG group bins; defined weight/track-length/volume/source normalization; same estimator for forward and adjoint; stable spatial/group indexing; and a deterministic machine- or text-readable output. `Energy=-1` is required for the exact MG group structure. Arbitrary physical energy boundaries may cut an MG group and produce a projected, not exact, group field.

## 2. Tally implementation chain

| Stage | Current evidence | Independent finding |
|---|---|---|
| Parser | `ReadMeshTallyCard.cpp:174-188,257-267` | Reads `Energy`, `Normalize`, mesh geometry and HDF5 flag. |
| MG setup | `SingleTally.cpp:875-890` | `Energy=-1` copies `p_vNeuMltErgBins`; allocates mesh × (energy bins + total). |
| Transport dispatch | `TallyByTL.cpp:24-54`, `RayTracking.cpp:250-275` | Fixed-source scoring calls mesh track-length tally before particle movement. |
| Track partition | `MeshFun.cpp:270-387` | A track is split among crossed Cartesian bins. |
| Score | `ScoreMeshTally.cpp:60-118`, `TallyType.cpp:46-49` | Score is current particle weight times each mesh subtrack; MG state is converted before energy lookup. |
| Accumulation | `TallyData.cpp:43-100`, `ProcessTally.cpp:360-394` | Per-history sums are accumulated and divided by fixed-source total source weight. |
| Output | `SingleTally.cpp:939-1004`, `MeshTallyHDF5.cpp:40-99` | Text emits spatial index/group/boundary/Ave/RE; HDF5 reshapes spatial values only. |

## 3. Mathematical meaning

`TallyFlux::score()` returns the passed flux unchanged. `ScoreMeshTallyByTL()` passes `p_dWgt` and multiplies it by each subtrack length. Therefore:

- `Normalize=0`:
  \[
  W_0^{-1}\sum w\ell,
  \]
  a source-normalized volume-integrated track-length score;
- `Normalize=1`: mesh track code divides each subtrack by cell volume, yielding:
  \[
  \phi^\dagger_{i,g}=W_0^{-1}V_i^{-1}\sum w\ell,
  \]
  the desired scalar flux density estimator.

The fixed-source divisor is `cFixedSource.p_dTotStartWgt` passed as `dM` to `CalcAveRe`. No additional volume factor is applied in text output.

The fresh corrected run used x widths 5 cm and 15 cm, y/z widths 100 cm. For adjoint mesh 1, raw/normalized ratios were approximately 49,999.24 and 150,000.0, directly confirming volume normalization.

## 4. Adjoint compatibility

The mesh scoring function contains no adjoint-specific branch. It always uses current `cParticleState.p_dWgt`; the adjoint collision path updates that same state before subsequent track scoring. No tally-local adjoint correction, forward-only skip, or second energy reinterpretation was found.

Within the declared F02 boundary, normalized Type=1 mesh scoring is therefore physically interpretable as the adjoint scalar track-length field \(\phi^\dagger_{i,g}\), provided the transport history is valid. WW ordering does not alter estimator meaning; separate WW unbiasedness is not re-audited here.

## 5. Spatial indexing

Current code supports Cartesian uniform, Cartesian nonuniform, and cylindrical nonuniform meshes. For Cartesian uniform mesh, the flat index is:

\[
I=zN_xN_y+yN_x+x,
\]

with x fastest. Track crossing emits one `(mesh index, subtrack length)` per crossed bin. Text output prints one-based `(x,y,z)`. The fresh two-bin case produced separate values for both spatial bins, not a duplicated total.

Boundary behavior is not uniformly clean: uniform mesh preliminary bounds allow equality at the upper edge before the calculated index is rejected, while heterogeneous mesh uses lower-inclusive/upper-exclusive bounds. The runtime cases also emitted many particle-location warnings, so production-quality boundary semantics remain unverified.

## 6. Energy/group mapping

`LocateMgErgGrp` stores a reverse-indexed internal group. `GetErgValue` maps it back through `GetMgNeuCentErg`, whose `G-g` reversal restores physical order. `ScoreMeshTallyByTL` uses this physical group-centre value with the `Energy=-1` library boundary vector.

Thus `Energy=-1` provides one output bin per MG transport group, with output rows in ascending physical-energy order, while the internal transport group order is reverse. The fresh adjoint text output populated physical rows 21–30 in both spatial bins, confirming multiple group bins are independently addressed.

A user-specified physical energy grid can cut a group. Its centre-based bin assignment is deterministic but not an exact unresolved within-group physical-energy result. For MLVR exact group fields, `Energy=-1` is the valid contract.

## 7. Output representation

### Text

Text `inp.Tally` is sufficient as a first serial interface. Each spatial block lists `(x,y,z)`, group number, physical energy boundary, `Ave`, `RE`, and a per-mesh `Tot` row. The final total is not a group.

### HDF5Mesh

Independent `HDF5Mesh=1` output had:

```text
/Geometry/BinNumber: (3)
/Geometry/Boundary: (7)
/Type1: (2, 1, 1)
```

The HDF5 writer only converts the spatial flat array with `OneToThree()` and does not iterate over energy bins. It has no energy-axis dataset. Therefore HDF5Mesh is **not** an F06 space×energy field output in the current implementation.

## 8. Independent runtime tests

### Test A — spatial indexing

Fresh 200,000-history MG adjoint input with two x bins (0–5 cm, 5–20 cm) and `Energy=-1` produced separate Type=1 rows. Normalized mesh totals were `1.3205E-05` and `6.4398E-05`; raw totals were `6.6024E-01` and `9.6597E+00`. Values are distinct and spatially indexed.

### Test B — energy indexing

The same run populated rows 21–30 in both bins. For example, raw scores were `(i=1,g=21)=5.6171E-02`, `(i=1,g=30)=6.7210E-02`, `(i=2,g=21)=4.4584E+00`, `(i=2,g=30)=3.8002E-01`. This verifies multiple energy rows and their spatial cross-product. It is not a clean direct single-group source oracle.

### Test C — spatial × energy cross-check

The four logical coordinates `(i=1,g=21)`, `(i=1,g=30)`, `(i=2,g=21)`, `(i=2,g=30)` are all nonzero and not copies. Their differences are physically plausible for the two spatial regions and group spectrum.

### Test D — forward vs adjoint mechanism

Forward and adjoint runs entered the same mesh Type=1 implementation and produced the same output shape. Static source evidence is stronger: `ScoreMeshTallyByTL` has no adjoint branch. The run is a mechanism check, not a revalidation of adjoint transport physics.

### Test E — volume semantics

The raw/normalized ratios match the two mesh volumes. This is targeted E3 confirmation of `Normalize=1` for the selected Cartesian path.

### Runtime limitation

The first narrow transverse geometry produced hundreds of thousands of location warnings and was discarded. The corrected wide geometry still produced 12,217 adjoint warnings and 24 forward warnings, plus source-above-MG-range warning behavior. The run proves reachability and targeted indexing/normalization, but not clean production geometry correctness.

## 9. F06 requirement comparison

| Requirement | Assessment |
|---|---|
| Distinct spatial bins | Met for Cartesian serial path |
| Distinct MG group bins | Met with `Energy=-1`; projected physical grids are not exact group fields |
| Scalar flux definition | Met only with `Normalize=1` |
| Adjoint weight inclusion | Supported within fixed-source MG adjoint boundary |
| Same forward/adjoint estimator | Met statically |
| Stable text index recovery | Met |
| Machine-readable space×energy output | Not met by HDF5Mesh |
| Per-bin RE | Present, but F07 owns reliability/statistics |

## 10. Comparison with Codex

The only F06 task archive available after the independent preliminary conclusion is an unfilled template. It contains no implementation, runtime claim, or classification. There is therefore no substantive Codex claim to confirm or contradict.

## 11. Remaining issues reserved for F07

- RE mathematics, zero-score bins, low-count reliability and history correlation;
- statistical acceptance of the field;
- MPI/OpenMP reduction and ordering;
- clean geometry boundary/warning resolution;
- energy-aware HDF5 or another machine-readable field contract;
- direct single-group/bin oracle.

## 12. Final classification

**C — Verify**, within standard MGACE fixed-source neutron adjoint, Type=1 Cartesian mesh, `Energy=-1`, `Normalize=1`, text `inp.Tally`, MPI-off/OpenMP-off serial.

The current code chain is physically appropriate for \(\phi^\dagger_{i,g}\) in this limited text-first scope. It is not A — Ready because HDF5 lacks energy dimension, runtime geometry warnings remain, the direct group oracle is incomplete, and F07 statistics are not reviewed.
