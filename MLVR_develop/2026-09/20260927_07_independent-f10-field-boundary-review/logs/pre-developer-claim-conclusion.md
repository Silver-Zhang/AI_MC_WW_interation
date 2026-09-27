# Pre-developer-claim independent conclusion — F10

Written before opening the Codex F10 design or any F10 result description.

## Minimum first-version contract

The boundary has three deliberately separate transformations:

\[
\text{RMC output}\xrightarrow{\text{adapter}}\text{StatisticalField}
\xrightarrow{\text{reconstruction}}\text{ReconstructedField}
\xrightarrow{\text{WW builder}}\text{WW input}.
\]

### StatisticalField

The minimum canonical raw field is immutable data:

- `value[i,g]`: nonnegative source-normalized scalar flux-density tally value;
- `re[i,g]`: raw tally relative error only where a score exists;
- `statistical_status[i,g]`: exactly `VALID` or `ZERO_SCORE` for v1; `ZERO_SCORE` means no observed tally contribution and makes its displayed `re=0` non-evidentiary;
- `mesh`: Cartesian dimensions, physical boundaries and declared flattening order sufficient to map `i ↔ (ix,iy,iz)` uniquely;
- `energy_groups`: physical MeV boundary vector in ascending order plus declared external group ordering. No RMC internal reverse group coordinate may cross this boundary;
- `field_role`: `BOOTSTRAP_FORWARD`, `FORWARD`, or `ADJOINT`;
- `stage`: `BOOTSTRAP` or `FORMAL`;
- `iteration`: absent for bootstrap, nonnegative explicit formal iteration otherwise;
- minimal provenance metadata: source/adapter identity, tally definition (`Type=1`, `Energy=-1`, `Normalize=1`) and run identity/config hash. Geometry/material are not field axes.

Shape must be explicit: `value.shape == re.shape == status.shape == (n_cells,n_groups)` with one documented ordering. `Tot` rows never enter the group axis.

### ReconstructedField

A reconstructed field holds `value[i,g]`, the same mesh/energy/role/stage/iteration/provenance contract, and the reconstruction method/version. It must not silently retain raw MC `RE`: the reconstructed value is no longer a raw tally. Algorithm uncertainty belongs only after an explicit defined method exists.

### Boundary rules

- Adapter is parsing/mapping only: text RMC tally → canonical raw field; it derives neither role nor workflow state from tally text.
- Reconstruction is pure: `StatisticalField → ReconstructedField`; it owns neither response source definition, RMC invocation, WW construction, nor iteration scheduling.
- WW builder is separate and policy-aware: bootstrap forward → `WW_A(1)`; formal adjoint at `k` → `WW_F(k)`; formal forward at `k` → `WW_A(k+1)`.
- `ResponseDefinition` is an external shared contract between the F03 adjoint source and F09 target response. It must not be stored as a field dimension or embedded in each `StatisticalField` payload.

## Preliminary design verdict

A design meeting the contract above should be **ACCEPT WITH MINOR CORRECTIONS** only if it explicitly fixes two semantic hazards: `ZERO_SCORE != zero uncertainty`, and all energy coordinates outside RMC are physical ascending boundaries/external order. Any v1 design that introduces group-map machinery, adaptive mesh, persistent store, plugin class tree, time/angle axes, HDF5 schema commitment, or ML feature tensors is over-design unless separately justified.
