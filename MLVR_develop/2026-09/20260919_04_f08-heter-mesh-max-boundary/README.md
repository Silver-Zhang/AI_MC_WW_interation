# f08-heter-mesh-max-boundary

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-19 |
| 状态 | 已完成（异构 mesh 最大边界） |
| 任务类型 | 缺陷修复 / mesh 边界语义 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | W10 |
| 涉及文件 | `RMC/src/MeshFun.cpp`、`RMC/src/DoMeshWeightWindow.cpp`、`RMC/src/WeightWindow.h`；不处理数组形状、point/track 时序、MPI 或 adjoint+WW |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `5ec595e1`；尚未修改 |

---

## 1. 目标与范围（① 立项 · Agent 填）

**要做什么**：确定并修复异构 Cartesian/cylindrical mesh 在坐标恰好等于全局最大边界时产生非法 mesh index 的问题，且使其边界语义与均匀 mesh 保持一致。
**涉及什么**（仓库 / 模块 / 数据）：`GetHeterMeshIndex()`、`GetHeterCylinMeshIndex()`、`GetUniversalMeshIndex()` 和 point mesh WW 的索引消费。只处理“最大外边界”等于的状态；不改内部 mesh 分界面归属、数组形状、track 时序、MPI、WWINP 或 reference/benchmark。
**怎样算完成**：用户确认全局最大边界的物理归属规则后，以最小改动让该规则在异构 mesh 中成立；构造最大边界点的最小验证，确保不发生 `p_vMeshInformation[meshIndex]` 越界；生成 `changes.diff`。
**原始材料**（`logs/` 下有什么，原样保存）：F08 审计、`MeshFun.cpp`/`GlobeFun.h`/`DoMeshWeightWindow.cpp` 静态调用链，以及后续最小输入和输出。

> **模式 C 追加 · 物理解释**：空间 mesh 是离散重要性场 $w_L(m,g)$ 的空间分区，外边界点必须有明确语义：归入最后一个 mesh，或视为 mesh 外。RMC 的均匀 `GetMeshIndex()` 在坐标等于全局最大边界时最终返回 `-1`，即采用半开区间 $[x_{min},x_{max})$ 的“mesh 外”语义。异构路径却先允许 `pos==max`，随后 `GetIntpltPos()` 返回最后 coarse index，细网格 index 计算为总细网格数，产生非法正 index；point mesh 只检查 `<0`，会将该非法 index 用于参数访问。

---

## 2. 做法与证据（② 设计 · ④ 实施 · Agent 填）

**设计 / 定位**（读了什么、查到什么；关键证据给 `文件:行号` 或数据位置）：

1. `GetIntpltPos()` 对 `val>=max` 返回 `nPos=max`。异构函数只拒绝 `pos>max`，因此 `pos==max` 进入计算。
2. 对最后方向 coarse bin，`p_vCumMeshNum[last]` 等于此前 coarse bins 的细网格总数；`p_vMeshDelta[last]` 是最后宽度。于是 $\lfloor(x_{max}-x_{max})/\Delta\rfloor=0$，每个命中最大边界的方向得到该方向总细网格数，而非最后合法 index $N_i-1$。
3. 合成 `nIndex` 后，`GetHeterMeshIndex()` 和 `GetHeterCylinMeshIndex()` 仅在 `bCheckScope=true` 时输出 warning，但仍返回非法正 index。`DoPointMeshWeightWindow()` 调用时传 `false`，只检查 `nMeshIndex<0`，随后直接访问 `p_vMeshInformation[particleType][meshIndex]`。
4. 均匀 `GetMeshIndex()` 在同一最大边界得到 index 等于 `p_nTotMeshNum`，其无条件范围检查会返回 `-1`。当前候选修复应让异构路径采用同一“最大边界为 mesh 外”的语义，而不是把它夹入最后一个 mesh；这样不会改变现有均匀行为或把边界外的粒子误归属到重要性场。

**方案选择**（选了什么、放弃了什么、为什么）：用户确认采用与均匀 mesh 一致的半开区间语义：异构 Cartesian/cylindrical 的任一有限方向全局最大边界视为 mesh 外并返回 `-1`；不夹取到最后一个 mesh。
**实施要点**（改了什么；改动快照见 `changes.diff`，无代码改动写“无”）：将 `GetHeterMeshIndex()` 与 `GetHeterCylinMeshIndex()` 的上界判断由 `pos > max` 改为 `pos >= max`。全局最大边界现在立即返回 `-1`，不进入 coarse/fine index 计算。内部边界、最小边界、track 算法和 point/track WW 调用时序均未改动。改动快照：`changes.diff`（15 行）。
**验证输出**（贴真实命令与输出；物理结论从严，工程/文档从简）：

```text
cmake --build /tmp/rmc-f08-cell-ww-build -j16
[100%] Built target RMC

ctest --test-dir /tmp/rmc-f08-cell-ww-build --output-on-failure -R '^test_var_reduce_wwmesh_[npe]$'
1/3 test_var_reduce_wwmesh_e ... Passed
2/3 test_var_reduce_wwmesh_n ... Passed
3/3 test_var_reduce_wwmesh_p ... Passed
100% tests passed, 0 tests failed out of 3

ctest --test-dir /tmp/rmc-f08-cell-ww-build --output-on-failure -R '^test_heter_meshtally$'
1/1 test_heter_meshtally ... Passed
100% tests passed, 0 tests failed out of 1
```

**未覆盖到的验证**（如实写；没有就写“无”）：未为 `GetHeterMeshIndex()`/`GetHeterCylinMeshIndex()` 直接构造 exact-max boundary 单元测试；当前证据为静态 index 推导、编译和代表性异构 mesh tally 回归。内部边界、浮点容差、圆柱 phi 周期、track 分段、MPI、WWINP、split bank 与 adjoint+WW 仍未覆盖。

---

## 3. 决策记录（③ · **人拍板**）

- **决定**（采纳什么方案）：
- **决定人 / 日期**：
- **约束**（能不能动接口 / 基准 / 算力预算…）：

**变更卡（B/C 模式，各一行）**：
| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| | | | |

> **模式 C 追加 · 人类理解确认**：把“人现在理解了哪些关系、批准了什么范围”留下来——问答原文或一两句转述均可。

> 未拍板前，Agent 不得改动 `../RMC` 下的任何文件。



---

## 4. 结论与边界（⑤ 归档）

- **结论**：异构 Cartesian/cylindrical mesh 的最大边界现与均匀 mesh 一致，按半开区间 $[x_{min},x_{max})$ 视为 mesh 外并返回 `-1`；消除了非法正 index 流入 point mesh WW 参数访问的路径。现有三条 mesh WW 回归与一条异构 mesh tally 回归均通过。
- **不能推出什么**（边界）：不证明精确最大边界动态输入已被独立执行，也不证明内部边界、浮点容差、track 分段、圆柱 phi 周期、MPI、WWINP、split bank 或 adjoint+WW 正确。
- **遗留 / 下一步**：优先审查 point/track mesh 的事件时序与 MPI shared mesh offset；再处理 split bank `ParticleAttr` 和 adjoint+WW 组合边界。
- **提交状态**（分支 / commit / 谁 push）：RMC `Neural_Network_WW_Iteration`，本地提交 `41cf4559`（中文提交信息）；根工作区档案待同步提交；未 push。

> **模式 C 追加 · 结果解释**：四条现有回归通过说明统一边界语义没有破坏已覆盖 mesh 输运；代码推导说明 exact-max 状态不再构造非法正 index。该结果仅闭合最大外边界的索引安全性，不外推到未构造的动态边界点或其他 mesh 机制。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-19 20:59 | 立项 |
| 2026-09-19 | 完成静态调用链，用户确认最大边界视为 mesh 外；实施 Cartesian/cylindrical 统一上界判断 |
| 2026-09-19 | MPI-off 16 核构建、mesh WW 3/3 与异构 mesh tally 1/1 回归通过；生成 changes.diff |

> 关键命令、误判与修正、未决分歧都写在这里；人机讨论较深时把要点并入本表，**不再单独建会话纪要文件**。原始聊天转储不要入仓（可能含凭据）。

**证据等级（可选）**：物理/审查结论可标 E0–E4；工程、文档、治理任务可省略。
