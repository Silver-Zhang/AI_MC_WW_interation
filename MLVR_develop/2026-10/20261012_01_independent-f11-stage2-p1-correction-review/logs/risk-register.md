# Risk Register

| Severity | Finding | Evidence | Disposition |
|---|---|---|---|
| P1 | Prepared WW reads `p_vEnergyBins[1]` before proving the outer vector includes neutron entry; native installer repeats that assumption. | `RMC/src/PrepareFixedSourceRun.cpp:286-288`; `RMC/src/WeightWindows.cpp:310-312` | Open. Blocks Stage 2 final acceptance, freeze and Stage 3. |
| P1 | Native WW lookup can use the final boundary as a window index: `GetIntpltPos` returns `max` for `erg == bins.back()`, while fallback corrects only `erg > bins.back()`. Energy boundaries are not validated finite/strictly increasing. | `RMC/src/GlobeFun.h:141-151`; `RMC/src/WeightWindows.cpp:45-66`; `RMC/src/ReadWeightWindow.cpp:56-82,419-427` | Open. Repair endpoint mapping or reject unsafe topology; add boundary-value negatives. |
| Verification limit | No negative test mutates malformed WW energy-bin outer/inner shape. | `tests/prepared_fixed_source_lifecycle/driver.cpp`; Task05 P1 negatives | Open. Must be added with the P1 repair. |
| Verification limit | Hexagonal Universe path is statically covered but not independently dynamically rerun in correction era. | Universe review | Documented limitation; not the acceptance blocker. |
| Governance | Correction delivery manifest has one `MLVR_develop/INDEX.md` hash mismatch; protected historical evidence validates 11,551/11,551 entries. | Task05 delivery/protected evidence manifests | Record only; do not overwrite historical manifest. Not a numerical-artifact mismatch. |
| Scope | Nonzero fission, parallel modes, CE, coupled particles, restart/source variants and arbitrary source distributions remain unsupported. | Prepared profile guard and Task05 §4 | Retained Stage 2 boundary. |

## REVIEW CONCLUSION

The P1 energy-bin topology defect is sufficient for `NEEDS CORRECTION`. No additional P0 was confirmed in the reviewed scope.
