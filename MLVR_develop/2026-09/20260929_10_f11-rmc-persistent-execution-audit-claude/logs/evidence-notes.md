# Evidence notes

## Source revision and worktree state

| Repository | Branch | HEAD | Working tree at audit start |
|---|---|---|---|
| `RMC` | `Neural_Network_WW_Iteration` | `5cfb0f771d0c5a2127c90d57e51ce672a4e3b616` | clean |
| `AIMC_WWiteration` | `feature/3d-two-group` | `9d749291d5f5070a00b9f88603428e686938cb7f` | one pre-existing untracked PDF under `article/成都会议/` |

No branch switch, reset, source modification, commit, or push was performed.

## Evidence discipline

- **SOURCE CONFIRMED** means the cited current source explicitly performs the behavior.
- **ARCHIVE SUPPORTED** is reserved for later cross-checks against allowed F02–F10 records and does not replace source evidence.
- **INFERENCE** is an engineering implication that source inspection does not directly prove with a repeated-run test.
- **UNKNOWN** means the inspected source does not establish the claim.

## Initial source-confirmed anchors

- `src/main.cpp:57-168` constructs problem objects, initializes MPI once when enabled, reads one input, then invokes `CDCalMode::RunCalculation`.
- `src/main.cpp:27-55` defines process-global objects including the weight-window object, RNG, status, timers, mesh information, controller, loggers, and MPI parallel object.
- The exact reset coverage and mode transition behavior will be derived from the implementation paths recorded in `source-map.md` and final report citations.
