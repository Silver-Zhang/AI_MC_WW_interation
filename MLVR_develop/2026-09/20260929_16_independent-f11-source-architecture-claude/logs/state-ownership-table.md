# State ownership table

| State | Owner / current evidence | Forward | Adjoint | F→A action | A→F action | v1 recommendation |
|---|---|---|---|---|---|---|
| model geometry | `CDGeometry`, `main.cpp:62`, setup may vary cells in material init | retained | retained | KEEP | KEEP | immutable base in session |
| material/raw MGACE | `CDMaterial` / `CDAceData`, `InitiateMatAce.cpp:8-126` | base tables | base plus derived adjoint tables | KEEP raw, rebuild derived | KEEP raw, clear derived | split base and derived ownership explicitly |
| fixed-source role | `CDFixedSource::p_bIsAdjoint`, `ReadFixedSourceBlock.cpp:209-236` | false | true | SET | SET false | session prep owns it |
| ACE role | `CDAceData::p_bIsAdjoint`, `InitiateAll.cpp:130` | false | true | SET/rebuild | SET false | do not rely on one-way init flag |
| particle role/cache | `CDParticleState`, `SampleNeutronSource.cpp:222`, init cache setup | forward cache | adjoint particle/cache | REBUILD | REBUILD | per-half-run scratch object or explicit reset |
| adjoint XS/fission XS | nuclide arrays, `TreatAdjointMaterial.cpp:21-105` | absent/unused | built by accumulation | CLEAR then REBUILD | CLEAR | never reuse accumulated arrays |
| cutoff | fixed-source physical card and in-place group conversion, `InitiateAll.cpp:192-203` | forward cutoff | adjoint group cutoff | SET from preserved physical value | restore forward semantic | retain physical config separately |
| source definition | `CDExternalSource`, sampled by `SampleFixSource` | regular source | target-derived source | SET | SET | persistent owner, component data replaced per half-run |
| WW topology | global `OWeightWindow`, `main.cpp:31`, `WeightWindow.h:160,234,242` | fixed | fixed | KEEP | KEEP | validate against F11 field mesh/group |
| WW bounds | `p_vMeshInformation`, `WeightWindows.cpp:79-100` | forward values | adjoint values | SET lower + REBUILD upper/survival | same | use `ProcessWeightWindow`, not direct three-array writes |
| tally definition/registry | `CDTally`, `InitiateTally.cpp:57-69` | retained | retained | KEEP | KEEP | initialize once; do not append registry per run |
| tally statistics | `CDTallyData`, `TallyData.cpp:17-80` | run values | run values | CLEAR | CLEAR | dedicated reset method must cover arrays, indices, statistics tester |
| banks/counters/denominator | `CDFixedSource`, `FixedSource.h:254-418`, batch code | run values | run values | CLEAR | CLEAR | session prep owns complete reset |
| RNG | `CDRNG`, setters in `RNG/RNG.h:446-552` | run stream | run stream | SET per policy | SET per policy | explicit seed/position contract |
| output handles | global `Output`, `main.cpp:28`, `OutputHeading.cpp:22`, `CloseFilePtrs.cpp:27-74` | per-half-run files | per-half-run files | REOPEN/close | REOPEN/close | isolated run directories / names |
