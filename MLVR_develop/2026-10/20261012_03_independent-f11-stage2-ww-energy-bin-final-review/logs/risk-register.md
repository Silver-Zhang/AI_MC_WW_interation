# 风险登记

| ID | Level | Finding | Evidence | Minimum closure |
|---|---|---|---|---|
| P1-WW-01 | P1 | MG raw NaN/Inf energy converts to integer before lookup finite guard | `RMC/src/DoMeshWeightWindow.cpp:17-18,42-43`; `RMC/src/WeightWindows.cpp:84-90`; `RMC/src/GetMgCs.cpp:247-253` | Validate raw energy before conversion or make converter reject safely; transport-path NaN/±Inf production + sanitizer evidence. |
| P1-WW-02 | P1 | Public independent installer accepts malformed lower values | `RMC/src/WeightWindows.cpp:354-370`; lower validation only in `RMC/src/PrepareFixedSourceRun.cpp:269-285` | Shared non-mutating lower/derived/split validation in Run and Install; direct Install negatives prove no mutation. |
| P2-WW-03 | P2 / out of prepared profile | MPI shared lookup branch lacks serial mesh-index/shape checks | `RMC/src/WeightWindows.cpp:62-70` vs `:72-78` | Separate MPI scope decision and MPI test task; not a reason to reinterpret serial prepared evidence. |
| L1 | Limitation | Task02 dynamic proof is reviewed archive evidence, not an independent rerun | `logs/independent-comparison.md` | A later authorized clean reproduction if required for higher evidence level. |
