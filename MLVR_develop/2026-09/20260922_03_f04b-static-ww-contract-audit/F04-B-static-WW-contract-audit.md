# F04-B Static WW Contract Audit

## 1. Scope

Static-only audit of RMC commit `b7d8a946417eea091a30c09c233054aa077570ee` on branch `Neural_Network_WW_Iteration`.

Reviewed scope:

```text
standard MGACE
fixed-source neutron
native WEIGHTWINDOW / WWMESH
neutron adjoint-compatible fixed-source path
```

Excluded: continuous energy, photon, ML/AI, WW generation algorithm, dynamic experiments, and source modifications.

## 2. Particle Energy Representation

**Answer to Q1: B — MG `p_dErg` stores a discrete group coordinate after source initialization.**

`SampleNeutronSource.cpp:268` overwrites sampled source energy with:

```cpp
cParticleState.p_dErg = cAceData.LocateMgErgGrp(
    cParticleState.p_dErg, cParticleState.p_eParticleType);
```

`CDAceData::LocateMgErgGrp` in `GetMgCs.cpp:263-296` searches physical MG boundaries, then returns a reversed integer group coordinate (`p_nNeuMltGrpNum - nErgGrp`).

The inverse convention is explicit in `GetMgCs.cpp:245-260`: `GetErgValue` converts `dParticleErg` back to a physical group-centre energy only when physical energy is needed. Therefore `p_dErg` is not retained as MeV for MG transport.

Post-collision MG state update follows the same MG representation: `TrackHistory.cpp:292` invokes `UpdateNeuStateMg`.

## 3. WW Input Representation

Native parser behaviour:

- `ReadWeightWindow.cpp:55-91` reads literal numeric `WWE:N` values and appends them to `OWeightWindow.p_vEnergyBins[Neutron]`.
- No call to `LocateMgErgGrp`, `GetErgValue`, or another MG conversion appears in this parsing path.
- `ReadWeightWindow.cpp:485-516` reads literal `WWMESH:N` lower bounds and enables `TrackMeshWeightWindow`.

Documentation describes `WWE:N` as an **energy grid** (`docs/source-en/usersguide/VarianceReduction.rst:88-101`) and gives a MeV example (`:176`). It does not disclose a different MG group-coordinate convention.

## 4. WW Lookup Chain

```text
physical source energy
  -> SampleNeutronSource.cpp:268 / LocateMgErgGrp
  -> p_dErg = discrete MG group coordinate
  -> RayTracking.cpp:257-260 / TrackWithWeightWindow.cpp:9-20
  -> DoTrackMeshWeightWindow
  -> WeightWindows.cpp:45-65 / setMeshWeightWindowBound
  -> GetIntpltPos(literal p_vEnergyBins, erg=p_dErg)
  -> DoWeightWindows
  -> roulette or split bank
```

`setMeshWeightWindowBound` passes `erg` directly to `GetIntpltPos` over the literal `WWE:N` vector (`WeightWindows.cpp:45-65`). `GetIntpltPos` is a numerical ordered-boundary search only (`GlobeFun.h:141-153`); it has no MG-specific conversion.

Thus MG group index can be treated as a physical-energy-like number whenever `WWE:N` is supplied in MeV. The reverse conversion (physical energy to MG group) is not performed by native WW lookup.

## 5. Forward/Adjoint Consistency

Fixed-source adjoint is activated by `ReadFixedSourceBlock.cpp:228` and propagated to ACE data by `InitiateAll.cpp:130`.

The native track-mesh WW lookup is selected by variance-reduction mode and invokes `setMeshWeightWindowBound` with `cParticleState.p_dErg` (`DoMeshWeightWindow.cpp:42-44`). This call has no branch on the adjoint flag.

Therefore forward MG and fixed-source neutron adjoint use the same `p_dErg -> literal WWE:N` lookup coordinate. The inconsistency is not an adjoint-only divergence; adjoint reproduces the same native MG WW contract.

## 6. Evidence Table

| Question | Evidence | Conclusion |
|---|---|---|
| MG `p_dErg` representation | `SampleNeutronSource.cpp:268`; `GetMgCs.cpp:263-296`; `GetMgCs.cpp:245-260` | Discrete group coordinate after source conversion |
| `WWE:N` parser semantics | `ReadWeightWindow.cpp:55-91` | Literal numeric boundaries stored without MG conversion |
| WW lookup semantics | `WeightWindows.cpp:45-65`; `GlobeFun.h:141-153` | Direct numeric search using current `p_dErg` |
| Native track-mesh entry | `ReadWeightWindow.cpp:485-516`; `TrackWithWeightWindow.cpp:9-20`; `DoMeshWeightWindow.cpp:42-44` | Lookup receives the MG state directly |
| Forward/adjoint distinction | `ReadFixedSourceBlock.cpp:228`; `InitiateAll.cpp:130`; `DoMeshWeightWindow.cpp:42-44` | Same WW lookup coordinate is used for both |
| User documentation | `docs/source-en/usersguide/VarianceReduction.rst:88-101,176` | Documents an energy grid/MeV example, not MG group-coordinate input |

## 7. Final Assessment

**Confirmed mismatch.**

For MG native `WWMESH`, transport state uses a discrete group coordinate while `WWE:N` is documented as an energy grid and stored/queried as literal numeric boundaries without conversion. A physical-MeV `WWE:N` grid is therefore not in the same coordinate system as `p_dErg` at lookup.

This is a static code-contract conclusion. It does not determine how all existing user inputs choose their numeric `WWE:N` values, nor does it provide a repair. No RMC code, benchmark, reference result, or patch was created.
