# f01-f05-forward-field-closure

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-27 |
| 状态 | 已完成 |
| 任务类型 | 轻量功能验证 / F01 + F05 |
| 任务模式 | B — 工程协作 |
| RMC revision | `b7d8a946417eea091a30c09c233054aa077570ee` |
| executable | `/tmp/rmc-f08-cell-ww-build/bin/RMC`；banner `3.5.0`；MPI OFF；OMP OFF |
| RMC 改动 | 无 |

## 1. Goal

验证第一版限定子域的 Forward fixed-source MC → Forward spatial×energy field 输出链：standard MGACE、fixed-source neutron、Cartesian Type=1 track-length mesh、`Energy=-1`、`Normalize=1`、serial text `inp.Tally`。

不重新审查 F06/F07 数学，不修改 RMC、HDF5 或 Field 接口。

## 2. Test configuration

输入文件：[forward_field.inp](forward_field.inp)

- 水模型：`1001.50m` / `8016.50m`，`MGACE ERGGRP=30 12`
- 两个 Cartesian spatial bins：`SCOPE=1 1 2`，`BOUND=-20 20 -20 20 0 50`
- 固定源：neutron point source `(0,0,0)`，energy `0.6`，weight `1`
- `PARTICLE POPULATION=200000`
- `RNG TYPE=2 SEED=2701 STRIDE=1000000`
- `MESHTALLY TYPE=1 PARTICLE=1 ENERGY=-1 NORMALIZE=1`
- 运行命令：

```text
RMC_DATA_PATH=/home/silver/NucXS_Library/RMC_DATA \
  /tmp/rmc-f08-cell-ww-build/bin/RMC forward_field.inp
```

原始材料：`forward_field.stdout`、`forward_field.stderr`、`forward_field.inp.out`、`forward_field.inp.Tally`。

## 3. F01 result

**A — Ready（限定第一版子域）**。

- exit code：`0`
- calculation mode：`fixed-source`
- source：有效材料 cell 内的 neutron source，无 0-importance source warning
- histories：输入 `200000`；fixed-source 运行正常结束
- neutron transport：`Neutron collisions per source particle: 224.98`
- fixed-source runtime：`1.0194e+01 seconds`

## 4. F05 result

**A — Ready（限定第一版子域）**。

`forward_field.inp.Tally` 报告：

- `1 Mesh tally in total`
- `Particle = neutron, Type = flux, Estimator = track length`
- `2` 个空间 bin
- 每个空间 bin `30` 个 energy rows，符合 30-group MGACE
- 每行均包含 `Energy Bin`, `Ave`, `RE`
- `Tot` 是每个空间 bin 的总行，不作为独立 energy group

代表性输出：

```text
space (1,1,1), group 1,  energy 1.3900E-10, Ave 2.3070E+01, RE 1.9537E-03
space (1,1,1), group 18, energy 5.0000E-01, Ave 1.6537E+00, RE 3.7368E-03
space (1,1,1), Tot, Ave 3.1032E+01, RE 1.7721E-03

space (1,1,2), group 1,  energy 1.3900E-10, Ave 3.9633E-02, RE 2.8317E-02
space (1,1,2), group 18, energy 5.0000E-01, Ave 1.7960E-05, RE 1.0000E+00
space (1,1,2), Tot, Ave 3.9914E-02, RE 2.8314E-02
```

两个空间 bin 均有独立输出，均有多个非零能群；空间响应差异明显。输出形式与 F06 Adjoint 使用同一 mesh tally/text 数据结构。`Energy=-1` 与 MGACE 全能群结构一致；`Normalize=1` 的 flux-density 语义直接复用 F06 结论。F07 的 per-space×group `Ave/RE` 统计定义直接复用，不在本任务重复审查。

## 5. Final status

| Feature | Status | Scope |
|---|---|---|
| F01 Forward fixed-source MC | **A — Ready** | standard MGACE neutron fixed-source，serial |
| F05 Forward spatial-energy field | **A — Ready** | Cartesian Type=1、`Energy=-1`、`Normalize=1`、text `inp.Tally`，serial |

## 6. Scope / limitations

结论不外推至：continuous-energy、photon/coupled transport、MPI/OpenMP、HDF5 space×energy output、其他 tally estimator、其他 mesh 类型或未测试 source contract。

F06 已确认的 HDF5 energy-axis 限制仍然适用；本任务仅确认 text `inp.Tally` 可恢复 Forward `{phi(i,g), RE(i,g)}`。零分数 bin 的 `RE=0` 语义沿用 F07，不在本任务改变或设计 mask。

---

**提交状态**：RMC 未修改、无 commit/push；档案与运行证据（`forward_field.inp`、`.Tally`、`.stdout`/`.stderr`）随 2026-09-27 根工作区提交入库；原始 `.inp.out`/`.fissmul`/`.material`/`.rossialpha`/`.cumrossialpha` 与 `*.h5` 按体积规范不入库、仅保留本地。

