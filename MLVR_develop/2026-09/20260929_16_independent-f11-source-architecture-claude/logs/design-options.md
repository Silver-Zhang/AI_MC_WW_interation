# Design options

## Option A — independent `src/MLVR/`

**INFERENCE:** A full parallel subsystem would duplicate RMC ownership and create a second source/tally/WW vocabulary. Current code already concentrates calculation dispatch in `CDCalMode`, source in `CDExternalSource`, statistics in `CDTally`, and WW in `CDWeightWindow`. This option is excessive for production v1.

## Option B — extend only existing large files

**INFERENCE:** Adding all orchestration, HDF5 schema, external process and run preparation to `CalcFixedSource.cpp` would fuse unrelated responsibilities into an already broad function and heighten ordinary fixed-source regression risk.

## Option C — existing owners plus focused root-level F11 files

**DESIGN RECOMMENDATION: choose C.**

- Extend `CDCalMode` as the workflow owner because it already selects calculation mode and invokes `CalcFixedSource`.
- Extend `CDInput` for parsing and `CDOutput` for generated-input/history output.
- Add focused root-level files for cross-owner behavior: `ReadMLVRBlock.cpp`, `CalcMLVR.cpp`, `MLVRRunPreparation.cpp`, `OutputMLVRField.cpp`, `ReadMLVRWeightWindow.cpp`, and a small `MLVR.h` configuration/value header.
- Keep target source construction in existing external-source sampling machinery with a focused source helper, rather than a new generic subsystem.

This creates no artificial directory while preventing a single 500+ line orchestration change inside `CalcFixedSource.cpp`.
