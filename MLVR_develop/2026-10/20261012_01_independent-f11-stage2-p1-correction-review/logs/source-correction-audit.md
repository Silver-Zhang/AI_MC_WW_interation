# Source Correction Audit

## SOURCE FACT

- `RMC/src/PrepareFixedSourceRun.cpp:47-61` serializes deterministic `CDUniverse` membership, resolved fill indices, neighbor adjacency, transformation enable flags/matrices/origin, lattice type/pitch/scope, hex derived terms, fill count and lattice fill maps.
- `RMC/src/PrepareFixedSourceRun.cpp:86-87` incorporates each Universe definition into the prepared fingerprint.
- `RMC/src/PrepareFixedSourceRun.cpp:132-136` rejects random/dispersion/CLS/PBS/RSA/ODR/DEM paths and lattice types outside rectangle/hexagon.
- `RMC/src/PrepareFixedSourceRun.cpp:63-75` safely validates WWP parameter-vector outer/inner shape before its own neutron indexing, then validates WUPN, WSURVN and MXSPLN.
- `RMC/src/PrepareFixedSourceRun.cpp:286` indexes `OWeightWindow.p_vEnergyBins[1]` before an outer-shape guard for that vector. Its later `bins.size() >= 2` check at lines 287-288 cannot guard the prior access.
- `RMC/src/WeightWindows.cpp:310-312` repeats the prepared-path neutron energy-bin index in `InstallPreparedNativeState`.

## REVIEW CONCLUSION

P1-01 is source-complete for the explicit deterministic prepared profile. P1-02 is source-incomplete: malformed caller-visible WW energy-bin topology can reach unchecked access instead of controlled prepared rejection.
