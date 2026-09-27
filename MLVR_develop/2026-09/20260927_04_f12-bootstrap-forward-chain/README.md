# f12-bootstrap-forward-chain

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-27 |
| 状态 | 已完成 |
| 任务类型 | 轻量功能验证 / Bootstrap MC-side chain |
| 任务模式 | B — 工程协作 |
| RMC revision | `b7d8a946417eea091a30c09c233054aa077570ee` |
| executable | `/tmp/rmc-f08-cell-ww-build/bin/RMC`；MPI OFF；OMP OFF |
| RMC 改动 | 无 |

## 1. Goal

闭合第一版 Bootstrap 的 RMC/MC 侧链：

```text
真实 Forward physical problem
    -> 低粒子数 direct/analog-like Forward MC
    -> BootstrapForwardField {phi0[i,g], RE0[i,g]}
```

本任务不实现 Field Reconstruction、不生成 `WW_A^(1)`、不实现 controller、不累计历史场。

## 2. Frozen Bootstrap rules

本次运行使用与 F01/F05 相同的真实水模型、真实 neutron source、Cartesian mesh 和 30-group MGACE；particle population 降为 `20000`。输入未启用任何 Weight Window、WWMESH、WWN 或 WWINP 配置，也未使用 density reduction 或 auxiliary problem。

Bootstrap 的外部工作流身份固定记录为：

```text
stage = bootstrap
iteration = none
formal_iteration = none
```

该身份不要求 RMC 增加 stage enum；本任务只在档案和 handoff 语义中记录。

## 3. Runtime configuration

输入：[bootstrap_forward.inp](bootstrap_forward.inp)

- standard MGACE：`ERGGRP=30 12`
- fixed-source neutron forward
- Cartesian Type=1 track-length mesh
- `Energy=-1`
- `Normalize=1`
- 2 spatial bins：`SCOPE=1 1 2`、`BOUND=-20 20 -20 20 0 50`
- `PARTICLE POPULATION=20000`
- RNG：`TYPE=2 SEED=2713 STRIDE=1000000`
- source：`(0,0,0)`、energy `0.6`、weight `1`
- MPI/OpenMP：OFF/OFF
- Weight Window：无

实际命令：

```text
RMC_DATA_PATH=/home/silver/NucXS_Library/RMC_DATA \
  /tmp/rmc-f08-cell-ww-build/bin/RMC bootstrap_forward.inp
```

首次运行使用偶数 seed `2712`，RMC 按输入规则拒绝；改为合法正奇数 `2713` 后正常完成。该输入修正未涉及 RMC 源码。

真实运行摘要：

```text
RMC_EXIT=0
Code version: 3.5.0
Git commit  : b7d8a946417eea091a30c09c233054aa077570ee
MPI parallel: OFF
OMP parallel: OFF
******** Calculation mode: fixed-source ********
Neutron collisions per source particle: 225.40
Time in Fixed Source Calculation = 1.1067e+00 seconds
WW_CARD_MATCHES=0
```

原始材料：[bootstrap_forward.stdout](bootstrap_forward.stdout)、[bootstrap_forward.stderr](bootstrap_forward.stderr)、`bootstrap_forward.inp.Tally`。

## 4. Bootstrap Field output

`bootstrap_forward.inp.Tally` 可直接恢复：

```text
BootstrapForwardField[i][g] = {Ave, RE}
```

输出含 2 个 spatial bins，每个含完整 30 个 MG energy rows；每个 row 均有 `Ave` 与 `RE`。代表值：

```text
space (1,1,1), group 1:  Ave=2.3243E+01, RE=6.1343E-03
space (1,1,1), group 18: Ave=1.6217E+00, RE=1.1786E-02
space (1,1,1), Tot:       Ave=3.1254E+01, RE=5.5604E-03

space (1,1,2), group 1:  Ave=3.7999E-02, RE=9.2770E-02
space (1,1,2), group 11: Ave=3.2466E-06, RE=1.0000E+00
space (1,1,2), group 18: Ave=0,          RE=0
space (1,1,2), Tot:       Ave=3.8498E-02, RE=9.2021E-02
```

两个空间 bins 均有独立输出；多个能群非零；空间数值差异明显。zero-score group 的 `RE=0` 保留原始 RMC 输出，沿用 F07 语义：不能解释为高可信度或零不确定度。

## 5. Bootstrap/formal shape consistency

Bootstrap 与已验证 formal Forward 输入 [F01/F05 input](../20260927_03_f01-f05-forward-field-closure/forward_field.inp) 的 field shape 一致：

```text
Bootstrap mesh  = formal mesh  = 2 Cartesian spatial bins
Bootstrap groups = formal groups = 30 MGACE groups
Bootstrap row   = formal row   = {Energy Bin, Ave, RE}
```

本任务不做 mapping；当前两者输入定义相同，因而没有连接所需的额外 mapping。Bootstrap `Ave` 对应 `phi0[i,g]`，`RE` 对应 `RE0[i,g]`。

## 6. Lifecycle boundary

Bootstrap 是独立初始化阶段，不属于正式 iteration 1：

```text
stage = bootstrap
iteration = none
```

Bootstrap 输出不进入正式 Forward FOM、不进入正式 iteration 编号、不参与历史场累计，也不作为最终物理结果。RMC 输入本身不包含 iteration controller 语义；这些字段属于后续外部工作流记录。

## 7. Handoff requirements

后续 F10 Field Reconstruction 至少需要能够接收以下信息：

- Bootstrap stage marker：`stage=bootstrap`
- source/run identity：RMC revision、executable identity、input identity、RNG seed/stride
- source/model identity：geometry、material、source configuration reference
- particle population：`20000`
- spatial mesh definition：bounds、scope、Cartesian ordering
- MG group definition：30-group physical energy boundaries
- `phi0[i,g]` / `RE0[i,g]`，每个 space×group 一条

这些是 handoff 的最小信息集合；本任务不决定 JSON/HDF5/C++ class，也不实现 Field Reconstruction 或 WW generation。

## 8. Classification

**F12 = A — Ready（限定首版 Bootstrap MC-side chain）**。

该 A 仅表示：

```text
low-population direct/analog-like Forward MC -> Bootstrap Field + RE
```

已完成。它不表示 Field Reconstruction 或 `WW_A^(1)` generation 已完成。

## 9. Limitations

结论限定于 standard MGACE、fixed-source neutron forward、Cartesian Type=1、`Energy=-1`、`Normalize=1`、MPI/OpenMP-off serial、text `inp.Tally`。不外推至 CE、photon/coupled transport、并行、HDF5 field output、其他 mesh/estimator、formal iteration controller 或 F10 handoff implementation。

---

**提交状态**：RMC 未修改、无 commit/push；档案与运行证据（`bootstrap_forward.inp`、`.Tally`、`.stdout`/`.stderr`）随 2026-09-27 根工作区提交入库；原始 `.inp.out`/`.fissmul`/`.material`/`.rossialpha`/`.cumrossialpha` 与 `*.h5` 按体积规范不入库、仅保留本地。
