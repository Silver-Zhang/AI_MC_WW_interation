# f02-density-mesh-hdf5-readiness

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-27 |
| 状态 | 已完成（density-mesh formal 通过） |
| 任务类型 | 物理验证 / 输入数据资格化 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F02 |
| 涉及文件 | 只读 `RMC/src/ReadCellCard.cpp`、`GetLocationInfo.cpp`、`SetCellGramDens.cpp`、`ReadMeshBlock.cpp`、`MeshInfo.h` |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `6d2087518e0d9f23574d629f5fde361c79f519e4`；RMC 不修改、不提交、不推送 |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：建立任务私有 HDF5 density mesh 写入/读回 oracle，并验证 standard ASCII MGACE fixed-source neutron forward/adjoint 在位置相关质量密度下的实际读取、密度比例换算与响应级互易性。这是 F02 从 C — Verify 到 A — Ready 的剩余密度 mesh 门槛之一，不预设 A 结论。

**范围**：RMC 保持只读；仅在本任务和 `/tmp` 创建私有 HDF5、输入、oracle、运行和日志。限制为 Linux serial、`ais=OFF`、standard ASCII neutron MGACE、fixed source、neutron forward/adjoint。排除 photon、CE、AIS/HDF5 核数据、裂变、NNUBAR、多材料、WW、reference/benchmark 和任何 RMC 代码改动。

**验收标准**：
1. 私有 HDF5 的 geometry、dataset、轴序、值、单位和 SHA256 可由不依赖 RMC 输出的 readback oracle 验证。
2. `DENS=<负 mesh id>`、`MESHINFO TYPE=1 FILENAME=... DATASETNAME=...` 的 RMC 输入可加载该文件；运行日志无 Warning/Error。
3. 至少两个空间区取预先定义的质量密度比例，实际输运能进入 density-mesh 位置读取链路；前向/伴随响应级比较采用预冻结统计判据。
4. 运行结束执行 CTest/reference 完整性和 RMC 工作树边界检查；不更新 reference/benchmark。

**原始材料**：`logs/` 将保存本轮命令、HDF5/输入 manifest、oracle、原始运行输出和哈希；旧任务 10 的 `logs/coverage_feasibility.csv` 记录本门槛此前未具备可运行 harness。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：任务 10 已确认真实 density mesh 是 F02 A 门槛，但当时缺少任务私有 HDF5 写入器及可运行输入。角表示 formal 已完成，故此门槛成为下一项独立验证对象。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `RMC/src/ReadCellCard.cpp:225-235` | 负 `DENS` 被解释为 mesh 用户索引，并登记为 density mesh。 |
| 2 | `RMC/src/ReadMeshBlock.cpp:17-119` | `MESHINFO` 读取 `TYPE=1`、文件名和 dataset 名，并在输入阶段载入结构化 HDF5 mesh。 |
| 3 | `RMC/src/SetCellGramDens.cpp:11-29` | density mesh 的数值语义为质量密度；初始化保存材料基准质量密度。 |
| 4 | `RMC/src/GetLocationInfo.cpp:60-82` | 输运按粒子位置读取 dataset，并计算 $r=\rho_{mesh}/\rho_{material}$。 |
| 5 | `RMC/src/MeshInfo.h:51-90` | mesh 由 `StructuredMesh::ReadMesh()` 读取，RMC 维护用户索引、文件名和 dataset 名的映射。 |
| 6 | `20260825_10_f02-extended-physics-readiness/README.md` | 旧 A 门禁审计明确未找到任务私有 HDF5 writer 或可运行 density-mesh harness。 |

**影响面**：验证的是位置相关密度对宏观截面和 W5 已修复伴随权重归一化的组合路径。通过不能覆盖裂变、NNUBAR、混合材料、强各向异性或完整 F02；不影响基准、reference 或生产接口。

**为什么之前没做/没发现**：（可选，但对改进机制很有价值）

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A | 两区域 private HDF5 structured mesh：定义两固定质量密度比例，独立 oracle 读回后进行前向/伴随 pilot；pilot 全通过再冻结响应级 formal。 | 最小可验证真实 mesh 路径；仍不覆盖更多密度形状。 | ★推荐 |
| B | 三区域 mesh，直接冻结多比例 formal。 | 覆盖更广，但在无可运行 writer/oracle 的条件下跳过 pilot，风险高。 | 不推荐 |
| C（不做/最小改动） | 继续用 cell `DENS` 比例替代 mesh。 | 不会进入 HDF5/位置查询路径，不能关闭本 A 门槛。 | 不采用 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A — 私有两区域 HDF5 structured mesh、独立 readback、forward/adjoint pilot，pilot 全通过后再冻结 formal。
- **决定人 / 日期**：用户 / 2026-08-27（持续执行至 A 的授权）。
- **理由与约束**：RMC 保持只读，不提交、推送、同步、合并或重置；不更新 reference/benchmark。pilot 使用 5 cm 球内的左右两个 x 半球，材料基准质量密度为 1.0 g/cm³、mesh 密度为 0.5/2.0 g/cm³；先用 seed 17、300 histories、密度由 mesh 唯一指定。任一 HDF5 读回、输入解析、Warning/Error、结构性或生产路径门禁失败即停止并保留反例。
- **formal 冻结 / 日期**：用户已授权后续按推荐方案继续 / 2026-08-27。pilot 的 2/2 clean 与非零双向响应通过后，冻结 seeds `17,23,41,59,83`、每条 50,000 histories、forward/adjoint 共 10 条。每条必须 exit 0、Warning/Error 0、Finish 1、stderr 为空且响应有限非零；五 seed 合并前向/伴随响应以独立方差近似计算 $|z|\le3$。不替换种子、追加样本或改阈值。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 私有 HDF5 asset | `create_density_mesh.c` + `h5cc` | 创建 `Geometry/MeshType=1`、`Boundary`、`BinNumber` 和 `/density[2,1,1]=[0.5,2.0]`。 |
| 2 | mesh load / position pilot | `/tmp/mlvr_density_mesh_pilot_20260827` | RMC 读取 mesh；低密度侧 2.10、高密度侧 20.11 次碰撞/源，位置相关密度进入输运。 |
| 3 | response pilot | 左右等体积盒体、seed 17、5,000 histories | forward/adjoint 2/2 clean，目标 cell 响应均非零。 |
| 4 | frozen formal | 五 seeds、50,000 histories/条 | 10/10 clean；逐 seed 与合并前向—伴随响应均满足 $|z|\le3$，合并 $z=0.0984$。 |

**代码改动**：RMC 无改动。任务侧新增 HDF5 C 写入器与输入生成器。

生成方式：
```bash
git -C ../../RMC diff > changes.diff
# 改原型则：
git -C ../../AIMC_WWiteration diff > changes.diff
```

---

## 6. 验证 / 实验记录（④ · Agent 填，要贴真实输出）

| 验证项 | 命令 | 结果 |
|---|---|---|
| HDF5 readback | `h5dump -n/-d /density` | 验证 uniform structured schema 和两个密度值 0.5、2.0 g/cm³。 |
| 位置依赖 pilot | 两侧点源、forward/adjoint | 低密度侧 2.10、高密度侧 20.11 次碰撞/源；均 clean 完成。 |
| 响应 formal | 5 seeds × forward/adjoint | 10/10 exit 0、Warning/Error 0、Finish 1、stderr 空；合并互易性 $z=0.0984397473$。 |

```
formal_combined_z=0.09843974732241369
formal_pass=True
formal_manifest_sha256=f6f1ba1d070b57e57cde262c0dcd7b1339cd003aeaebd8a342601446716583a7
```

**实验设置（算法实验必填）**：
- 随机种子：RNG type 2，`17,23,41,59,83`，stride `1000000`。
- 配置快照：两等体积 $5\times5\times10$ cm³ 盒体；材料基准质量密度 1.0 g/cm³；mesh 两侧为 0.5/2.0 g/cm³；私有两群 isotropic MGACE。
- 依赖版本：Python 3.12.3、HDF5 C 工具链、RMC 3.5.0 binary SHA256 `8fff3f0f...f13c2`。
- 基准对比：交换左右空间源/响应的前向—伴随互易性。

**未覆盖到的验证**：裂变/NNUBAR、多材料、强各向异性、非等体积和非均匀 mesh、更多几何/边界、MPI/OpenMP 和 Windows。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：真实 HDF5 density mesh 已在 RMC 位置查询路径中运行，并在 0.5/2.0 g/cm³ 两个等体积区域的 nonfissile two-group 私有资产下通过冻结的前向—伴随响应级 formal。
- **遗留问题 / 后续待办**：该结果只闭合 F02 的 density-mesh 缺口；F02 仍需 NNUBAR=1/多材料裂变和更多几何/边界，不能据此升级为 A。
- **知识库同步**：待完整 F02 A 门槛闭合后统一更新分类；本任务不改变 F02 的 C — Verify。
- **是否已提交**：未提交/推送；RMC 未修改。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-27 01:29 | 立项 |
| 2026-08-27 | 用户授权两区域 mesh pilot；2/2 pilot 通过后冻结 10 条 formal。 |
| 2026-08-27 | formal 10/10 clean、合并互易性 $z=0.0984$；任务完成。 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 剩余门槛复核 | 知识库、任务 10、角表示 formal 档案 | 确认角表示已闭合；真实 density mesh 仍是独立 A 门槛。 |
| 3 | density mesh 调用链定位 | `ReadCellCard.cpp`、`ReadMeshBlock.cpp`、`SetCellGramDens.cpp`、`GetLocationInfo.cpp`、`MeshInfo.h` | 确认负 `DENS` → HDF5 structured mesh → 位置质量密度 → 密度比例的实际链路；尚未创建验证资产或运行。 |
| 4 | schema 定位与资产创建 | `StructuredMesh.cpp`、`BaseMesh.cpp`、`create_density_mesh.c` | 确认 `Geometry` 组、`MeshType` 属性、`Boundary`、`BinNumber` 和根 dataset schema；用本机 HDF5 C 工具链创建资产。 |
| 5 | pilot 与 formal | `/tmp/mlvr_density_mesh_*` | 点源、双向响应 pilot 通过；冻结后正式五种子矩阵通过。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
