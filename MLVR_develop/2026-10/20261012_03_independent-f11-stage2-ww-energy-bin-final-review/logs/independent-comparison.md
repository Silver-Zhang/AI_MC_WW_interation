# 证据等级与独立性说明

| Claim type | This review's status |
|---|---|
| Current RMC definition/lookup/lifecycle source | **SOURCE VERIFIED** by read-only inspection of the live shared working tree, branch `Neural_Network_WW_Iteration`, HEAD `330f091e`; Stage2 remains local uncommitted work. |
| Task02 command output, JSON outcomes, GDB stacks, binary/source identities and manifest assertions | **ARTIFACT VERIFIED** where represented in the refined archive. |
| 78 malformed cases and 38 pairing decomposition | **INDEPENDENTLY RECOMPUTED** from archived JSON grouping. |
| Build, CTest, ordinary runs, prepared runs and sanitizer | **NOT INDEPENDENTLY RERUN** by this review. |
| MPI/OMP, ordinary malformed parser, ordinary MCNP WW, full program/leaks, physical 1e22 source and Stage3 | **NOT VERIFIED**. |

Task02's `evidence-manifest.json` declares the selected raw corpus retained locally: 20,351 files / 8,692,116,673 bytes, including commands, logs, snapshots, GDB, inputs and source/binary hashes. The repository archive deliberately retains only 16 refined files. This supports traceability but does not turn saved Task02 execution into a new independent rerun.
