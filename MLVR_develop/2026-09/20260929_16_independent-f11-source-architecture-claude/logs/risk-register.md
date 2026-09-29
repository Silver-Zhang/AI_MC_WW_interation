# Risk register

| Severity | Risk | Source evidence | Mitigation |
|---|---|---|---|
| High | `RunCalculation` mixes value and reference ownership | `RMC/src/RunCalculation.cpp:6-13` | F11 bypasses repeated by-value dispatcher and uses a session-level fixed-source execution core with explicit reference ownership. |
| High | F/A mode transforms state and uses accumulating derived arrays | `InitiateAll.cpp:130,192-203`; `TreatAdjointMaterial.cpp:21-105` | preserve physical config, clear derived vectors, rebuild role/cache, validate before transport; fissile gate. |
| High | Fixed-source state lacks complete native reset | `InitiateTrspt.cpp:60-100`; commented fixed reset in `ResetTrspt.cpp:24-32` | production reset contract with exhaustive fields and tests, not ad hoc caller writes. |
| High | output is one-process / raw-handle oriented | `OutputHeading.cpp:22-23`; `OpenFilePtrs.cpp:27-274`; `CloseFilePtrs.cpp:27-74` | scoped per-half-run output names, explicit close/null lifecycle, fail-fast file handling. |
| Medium | tally registry may be re-appended by full initialization | `InitiateTally.cpp:57-69`; `SetStatisticsIndex.cpp:9-43` | initialize definition once; reset samples without re-registering. |
| Medium | RNG has state/position semantics beyond a seed | `RMC/src/RNG/RNG.h:446-552` | record and set type, seed0, stride, position and pre-position per run. |
| Medium | global WW and MPI branches complicate later extension | `main.cpp:31`; `WeightWindows.cpp:220-290` | v1 serial only; topology invariant check; defer MPI sharing lifecycle. |
| Medium | parser state and generated input assume one input | `Input.h:51-71`; `ReadInputBlocks.cpp:23-364` | parse F11 once; no repeated full parsing within formal loop. |
| Medium | RMC error routines can exit/abort | `PrintFile.cpp:5-15,51-58` | external command and field/WW validation must fail before transport; document fail-fast process termination. |
