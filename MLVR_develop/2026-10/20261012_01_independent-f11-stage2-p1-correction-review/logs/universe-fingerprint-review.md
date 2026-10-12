# Universe Fingerprint Review

## SOURCE FACT

The current deterministic prepared profile uses these `CDUniverse` categories in particle location and boundary crossing:

- contained cell count and resolved contained-cell map;
- neighbor-cell adjacency;
- origin, rotation matrix and transform enable flags;
- lattice status/type, pitch, scope and filled lattice map/count;
- hexagon angle, sine, cosine and height.

They are serialized in `RMC/src/PrepareFixedSourceRun.cpp:47-61`; the comparison occurs at `:265-266`, before `PrepareFixedSourceRun()` begins its CLEAR/reset sequence at `:228-232`.

Transport consumption was checked at:

- `RMC/src/CheckParticleLocation.cpp:16-76`;
- `RMC/src/TranCoord.cpp:13-20`;
- `RMC/src/FindLatIndex.cpp:7-123`;
- `RMC/src/MonveToOriginLat.cpp:6-31`;
- `RMC/src/FindNeighborCell.cpp:145-150`.

Stochastic/random/DEM fields omitted from serialization are outside the admitted profile and are rejected on every prepared run by `PrepareFixedSourceRun.cpp:132-136`.

## DYNAMIC EVIDENCE

Task05 correction evidence mutates Universe origin, rotation, cell membership and lattice fill after a successful first run without changing the Universe vector size. Each case rejects before a second CLEAR/execute/source and logs `state_unchanged=1`; random-Universe enablement is explicitly rejected by the profile guard.

## REVIEW CONCLUSION

`PASS` for deterministic CSG, Type-1 rectangular lattice and Type-2 hexagonal lattice within the declared prepared profile. Type-2 dynamic numerical behavior was not independently rerun in this review.
