# Finding

**Potential mismatch** — in multigroup neutron transport, `CDParticleState::p_dErg` is converted from physical energy to a discrete group number before native `WWMESH` lookup. Native WW lookup compares that group-number coordinate directly against the numbers supplied through `WWE:N`; it does not convert a physical-energy WW boundary into a group number.

Therefore, a `WWE:N` card written as physical energies is not compatible with the post-source MG value in `p_dErg`. The working contract is numerical group-coordinate boundaries, not physical MeV boundaries, unless a separate conversion layer is added outside the current code path.

# Evidence

## Source-state coordinate

- `RMC/src/SampleNeutronSource.cpp:268` overwrites `cParticleState.p_dErg` with `cAceData.LocateMgErgGrp(...)` whenever the ACE data are multigroup.
- `RMC/src/GetMgCs.cpp:263-296`, `CDAceData::LocateMgErgGrp`, finds a physical-energy-bin position and returns `p_nNeuMltGrpNum - nErgGrp`: an integer transport group coordinate.
- `RMC/src/GetMgCs.cpp:245-260`, `GetErgValue`, independently confirms the convention: in MG mode it treats `dParticleErg` as a group number and maps it to the group-centre physical energy only when physical energy is required.

For the independent experiment source, physical $E=0.2435\ \mathrm{MeV}$ is in the source group represented in transport by the numerical coordinate 16; it is not retained in `p_dErg` as 0.2435.

## Native WW coordinate

- `RMC/src/ReadWeightWindow.cpp:55-91` appends the literal numeric values from `WWE:N` to `OWeightWindow.p_vEnergyBins[Neutron]`; no MG conversion is performed.
- `RMC/src/ReadWeightWindow.cpp:485-516` reads literal `WWMESH:N` values and constructs the mesh WW parameter table.
- `RMC/src/WeightWindows.cpp:45-65`, `setMeshWeightWindowBound`, passes the current `erg` directly to `CDGlobeFun::GetIntpltPos` over `p_vEnergyBins`.
- `RMC/src/GlobeFun.h:141-153`, `GetIntpltPos`, is a normal numerical ordered-boundary lookup. It has no MG-aware conversion.

Thus the actual lookup is:

```text
physical source energy 0.2435 MeV
  -> LocateMgErgGrp
  -> p_dErg = 16
  -> setMeshWeightWindowBound(..., erg=16)
  -> numeric search through literal WWE:N values
```

## Dynamic discriminator

`verification/cases/energy-contract/inp` uses a physical-energy-style `WWE:N 0.2 0.3` and distinct WW lower bounds. It executes normally (`exit 0`, 1,000 source histories; raw log: `logs/2026-09-22_energy-contract-discriminator.log`). Successful execution does not establish correct physical-bin selection: source evidence shows its lookup value is the group coordinate 16, which lies numerically beyond 0.3 and is clamped to the terminal WW bin rather than selecting the physical 0.2–0.3 interval.

# Conclusion

**Potential mismatch.**

For MG native `WWMESH`, physical MeV values in `WWE:N` are not interpreted in the same coordinate system as the MG particle state used at lookup. This is an interface-contract risk. It does not by itself prove that all existing MG WW inputs are wrong: callers may intentionally provide group-number coordinates. It does prove that a physical-energy `WWE:N` convention needs explicit conversion or explicit documentation before it can be relied on.

No RMC source, benchmark, reference result, or formal capability classification was changed by this verification.
