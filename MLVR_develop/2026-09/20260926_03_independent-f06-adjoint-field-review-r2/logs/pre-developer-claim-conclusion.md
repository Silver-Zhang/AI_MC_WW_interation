# Pre-developer-claim independent conclusion — F06 R2

This second review was based on current RMC source, current RMC user documentation, current RMC tests, and a fresh serial build/run only. No F06 conclusion archive or prior F06 report was used to form this preliminary conclusion.

## Preliminary requirement

A usable first-version field must be a deterministic scalar flux density indexed by Cartesian mesh cell and MG transport group:

\[
\phi^\dagger_{i,g}=W_0^{-1}V_i^{-1}E\left[\sum w\ell\right]_{i,g}.
\]

`Energy=-1` is the only current input that can plausibly guarantee a one-to-one tally bin per MG library group; arbitrary physical energy boundaries can cut groups and should not be treated as an exact MG field.

## Preliminary source conclusion

- Type-1 mesh track-length scoring uses current particle weight times subtrack length.
- `Normalize=1` divides subtracks by spatial cell volume; fixed-source processing divides by total source weight.
- The scoring path has no adjoint-specific branch and uses the same current `p_dWgt` for forward and adjoint.
- MG tally lookup calls `GetErgValue`, mapping the internal reverse group coordinate to physical group-centre energy before selecting `Energy=-1` bins.
- Flat storage is mesh-major with x-fastest order and an extra total slot per mesh; text output exposes spatial index, group row, physical boundary and RE.
- HDF5Mesh output is spatial-only in the current implementation: its `/Type1` dataset has spatial shape and no energy axis.

## Preliminary classification

**C — Verify**, limited to standard MGACE fixed-source neutron adjoint, Type-1 Cartesian mesh, `Energy=-1`, `Normalize=1`, serial text output. Runtime cases reach the tally and show distinct spatial/group values, but the selected geometry still reports particle-location warnings, the HDF5 field is incomplete, and F07 statistical qualification is out of scope.
