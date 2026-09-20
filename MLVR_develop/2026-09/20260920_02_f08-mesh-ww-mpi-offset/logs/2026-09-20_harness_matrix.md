# 测试矩阵（真实执行记录）

生成时间：2026-09-20（本机，OpenMPI 4.1.6，RMC_DATA_PATH=/home/silver/NucXS_Library/RMC_DATA）

| # | 用例 | 配置 | 命令要点 | 退出码 |
|---|---|---|---|---|
| 1 | MCNP_WeightWindow_MPI_multi_particle | MPI 10 rank | -n 10 | 0 |
| 2 | MCNP_WeightWindow_MPI_ShareMem_multi_particle | MPI 10 rank | -n 10 | 0 |
| 3 | MCNP_WeightWindow_MPI_multi_particle | MPI 2 rank | -n 2 | 0 |
| 4 | MCNP_WeightWindow_MPI_ShareMem_multi_particle | MPI 2 rank | -n 2 | 0 |
| 5 | MCNP_WeightWindow_MPI_multi_particle | serial (1 rank) |  | 0 |
| 6 | MCNP_WeightWindow_MPI_ShareMem_multi_particle | serial (1 rank) |  | 0 |
| 7 | MCNP_WeightWindow_MPI_multi_particle | MPI 10 rank + OpenMP 2 threads | -n 10 -s 2 | 0 |
| 8 | MCNP_WeightWindow_MPI_ShareMem_multi_particle | MPI 10 rank + OpenMP 2 threads | -n 10 -s 2 | 0 |
| 9 | MCNP_WeightWindow_MPI_ShareMem | MPI 10 rank（既有单粒子 shared 回归） | -n 10 | 0 |
| 10 | var_reduce_wwmesh_n | MPI-off serial（native track mesh WW） |  | 0 |
| 11 | var_reduce_wwmesh_p | MPI-off serial（native track mesh WW） |  | 0 |
| 12 | var_reduce_wwmesh_e | MPI-off serial（native track mesh WW） |  | 0 |
| 13 | MCNP_WeightWindow | MPI-off serial（MCNP WWINP 既有） |  | 0 |
| 14 | MCNP_WeightWindow_MPI_multi_particle | MPI-off serial（新用例，shared 预期为允许的 runtime error） |  | 0 |
| 15 | MCNP_WeightWindow_MPI_ShareMem_multi_particle | MPI-off serial（新用例，shared 预期为允许的 runtime error） |  | 0 |
