# Pre-developer-claim independent conclusion

Written before opening any F06 task archive or F06 result summary.

## Static finding

1. A type-1 mesh tally scores `dScore * track.p_dTrackLen`, where flux type returns `dScore = particle.p_dWgt` (`ScoreMeshTally.cpp` and `TallyType.cpp`). Without `Normalize=1`, the tally is therefore per-source-history, energy-bin, mesh-cell **volume-integrated track length** \(\sum w\ell\), not scalar flux density.
2. With `Normalize=1`, the mesh tracker divides each subtrack by that mesh cell's volume before it is scored. Thus the score is \(\sum w\ell/V_i\), i.e. the scalar track-length flux estimator, subject to the fixed-source source-normalization applied in `CalcAveRe`.
3. `Energy=-1` makes the mesh energy boundary vector equal the MG library's physical-energy boundaries. At scoring, `GetErgValue` maps stored MG group coordinate back to group-centre physical energy before energy-bin lookup. This avoids the direct group-coordinate/MeV mismatch found in native WW.
4. Data layout is deterministic: flat index is `data_start + mesh_index*(N_energy+1)+energy_bin`, and the last per-mesh slot is the total. Mesh index is x-fastest, then y, then z. Text output includes `(x,y,z)` and group/energy boundary. HDF5Mesh appears spatial-only: the HDF5 exporter receives a single flat pointer and reshapes only x/y/z, without an energy loop. Therefore text supports a 2D spatial-energy field; current HDF5Mesh cannot yet be asserted to expose \(\phi[i,g]\).
5. There is no visible adjoint-specific mesh-score branch. The tally uses current `p_dWgt`; in the fixed-source adjoint path collision code updates that same weight before future tracks, so the track-length estimator should tally the adjoint history weight without a second correction.

## Preliminary classification

**C — Verify**, pending runtime confirmation of spatial indexing, MG energy mapping, volume normalization, fixed-source normalization, and output behavior. The likely usable first-version scope is fixed-source MG neutron adjoint, Cartesian mesh, serial, Type=1, `Energy=-1`, `Normalize=1`, text output. Any claim that the existing HDF5 mesh file alone is a machine-readable space×energy field is unverified.
