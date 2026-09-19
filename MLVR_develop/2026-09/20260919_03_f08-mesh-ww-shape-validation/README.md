# f08-mesh-ww-shape-validation

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-19 |
| 状态 | 已完成（native WWMESH 输入形状校验） |
| 任务类型 | 缺陷修复 / 输入物理契约 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | W10 |
| 涉及文件 | `RMC/src/ReadWeightWindow.cpp`、`RMC/src/WeightWindows.cpp`、`RMC/src/MeshFun.cpp`、`RMC/tests/var_reduce_wwmesh_n/`；不处理 point/track 时序、MPI、异构最大边界或 adjoint+WW |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `341c0238`；尚未修改 |

---

## 1. 目标与范围（① 立项 · Agent 填）

**要做什么**：为 native `WEIGHTWINDOW` 的 `WWMESH:N/P/E` 建立严格的输入形状校验：lower-bound 数量必须等于权窗几何总 mesh 数乘能群数，不能由整数除法猜测空间数。
**涉及什么**（仓库 / 模块 / 数据）：`WEIGHTWINDOWMESH` 的均匀/异构 mesh 定义、`WWE:*` 能量边界、`WWMESH:*` lower-bound 数组和 `ProcessWeightWindow()` 的参数重排。仅处理 native mesh WW 初始化期校验；不改 roulette/splitting、point/track 调用时序、MPI shared mesh、`WWINP`、adjoint+WW 或 reference/benchmark。
**怎样算完成**：用户批准后，合法 $N_s\times N_g$ 输入保持既有行为；少于或多于该数量的输入在初始化期明确报错并停止，绝不进入运行期数组访问。生成最小合法/少一项/多一项输入验证与 `changes.diff`。
**原始材料**（`logs/` 下有什么，原样保存）：`var_reduce_wwmesh_n` 现有 10×1 输入、源码定位、后续构建和拒绝输入的真实输出。

> **模式 C 追加 · 物理解释**：mesh WW 的物理对象是 $w_L(m,g)$：每个空间 mesh $m$ 与能群 $g$ 有唯一 lower bound，并由 $w_S=WSURVN\,w_L$、$w_U=WUPN\,w_L$ 派生。因而输入数组必须满足 $N_{value}=N_sN_g$。少一项时某个真实空间—能群位置没有权窗，运行期可能访问不存在的参数；多一项时存在没有物理位置的权窗，不能静默接受。当前 neutron 回归的 `ScopeX=10,ScopeY=1,ScopeZ=1` 且无 `WWE:N`，所以 $N_s=10,N_g=1$，恰需 10 个 `WWMESH:N` 值。

---

## 2. 做法与证据（② 设计 · ④ 实施 · Agent 填）

**设计 / 定位**（读了什么、查到什么；关键证据给 `文件:行号` 或数据位置）：

1. `ReadWeightWindowBlock()` 先读取 `WWMESH:*` 到 `vTemporaryWeightWindowPara[particleType]`，再在同一 block 结束后调用 `ProcessWeightWindow()`；`WEIGHTWINDOWMESH` 在此之前/之后出现不影响最终处理，因为处理发生在整个 block 读取完成后。
2. `ReadWeightWindowMeshBlock()` 调用 `CheckMeshPara()` 或 `CheckHeterMeshPara()`，将均匀 mesh 的 $N_s$ 写入 `p_nTotMeshNum`，或将异构 mesh 的三个方向细网格乘积写入同一成员。
3. 现有 `ProcessWeightWindow()` 以 `totalWeightWindowParaNum / ergBinNum` 计算 `spatialNum`，没有确认余数为零，也没有与 `p_OWeightWindowMesh.GetTotMeshNum()` 比较。`ReadVaryVec()` 对 native `WWMESH:*` 读取到行末，不从 mesh 定义推导或限制该数量。运行时 `setMeshWeightWindowBound()` 按真实 `meshIndex` 直接访问 `p_vMeshInformation[particleType][meshIndex][ergPos]`。
4. 静态结论：数组不匹配可以由合法语法但数量错误的外部输入直接造成。例如当前 $N_s=10,N_g=1$ 的输入若只有 9 项，`spatialNum=9`，粒子进入 index 9 的真实 mesh 时会访问不存在的第 10 个参数；若有 11 项，则初始化 11 个空间位置，但物理 mesh 只有 10 个，最后一项静默失去空间含义。
5. 因此校验应在调用 `ProcessWeightWindow()` 前或其中执行，使用已完成初始化的 $N_s$ 与 `ErgBins.size()-1` 的 $N_g$，不需要在每个粒子输运步骤新增任何索引或检查。

**方案选择**（选了什么、放弃了什么、为什么）：用户批准初始化期严格相等检查：$N_{value}=N_sN_g$，不满足立即报输入错误；不采用整数除法截断、补零、重复最后一项或运行期边界回退，因为它们都会把外部重要性场映射成另一个物理对象。
**实施要点**（改了什么；改动快照见 `changes.diff`，无代码改动写“无”）：在 `RMC/src/WeightWindows.cpp` 的 `ProcessWeightWindow()` 中，以 `p_OWeightWindowMesh.GetTotMeshNum()` 取得真实空间 mesh 数，强制 `WeightWindowParameter.size()==meshCount*ergBinNum`。不匹配时输出实际/期望数量和能群数，使用输入错误等级停止；不再用整数除法推断 `spatialNum`。改动快照：`changes.diff`（19 行）。
**验证输出**（贴真实命令与输出；物理结论从严，工程/文档从简）：

```text
cmake --build /tmp/rmc-f08-cell-ww-build -j16
[100%] Built target RMC

ctest --test-dir /tmp/rmc-f08-cell-ww-build --output-on-failure -R '^test_var_reduce_wwmesh_[npe]$'
1/3 test_var_reduce_wwmesh_e ... Passed
2/3 test_var_reduce_wwmesh_n ... Passed
3/3 test_var_reduce_wwmesh_p ... Passed
100% tests passed, 0 tests failed out of 3

临时 native WWMESH:N 输入（10×1 mesh）
9 项：exit 1
Error: WWMESH parameter count (9) does not match mesh count (10) times energy-bin count (1).
11 项：exit 1
Error: WWMESH parameter count (11) does not match mesh count (10) times energy-bin count (1).
```

**未覆盖到的验证**（如实写；没有就写“无”）：未构造多能群、异构/圆柱 mesh、point/track 事件时序、MPI shared mesh、WWINP、split bank 或 adjoint+WW 验证；本任务只验证 native 均匀 mesh 的初始化形状契约。

---

## 3. 决策记录（③ · **人拍板**）

- **决定**（采纳什么方案）：用户确认 $N_{value}=N_sN_g$ 是 native WWMESH 的必要物理输入契约；数量不匹配必须输出错误并拒绝运行。
- **决定人 / 日期**：用户 / 2026-09-19
- **约束**（能不能动接口 / 基准 / 算力预算…）：不改变合法输入格式、WWP 语义或运行期 WW 算法；不改 MCNP/WWINP、MPI、reference、benchmark；仅在本任务范围内修改 `RMC/`。

**变更卡（B/C 模式，各一行）**：
| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| 外部生成的 lower-bound 数组与 RMC mesh/energy 形状不一致，导致错误或越界映射 | 只在 native WWMESH 初始化处检查数组形状；不改运行期 point/track 语义及其他 WW 路径 | 10×1 合法输入回归保持通过；9/11 项输入均在初始化期拒绝；若无法获得正确总 mesh 数则停止 | 还原本任务 RMC diff |

> **模式 C 追加 · 人类理解确认**：用户确认不匹配输入应报错并停止，而非仅给警告后继续；接受空间×能群形状完全一致是 ML/外部重要性场进入 RMC 的必要条件。

> 未拍板前，Agent 不得改动 `../RMC` 下的任何文件。



---

## 4. 结论与边界（⑤ 归档）

- **结论**：native WWMESH lower-bound 数组现在必须与真实空间 mesh 数×能群数严格一致。合法 10×1 输入保持三粒子 mesh WW 回归通过；9/11 项输入均在初始化期拒绝，消除了整数除法截断导致的运行期无定义映射。
- **不能推出什么**（边界）：不证明 mesh WW 的 point/track 事件时序、异构最大边界、MPI、WWINP、split bank、adjoint+WW 或完整方差改善正确；多能群/异构 mesh 的同一检查逻辑未单独动态运行。
- **遗留 / 下一步**：处理异构 mesh 最大边界 index；之后再审查 point/track mesh 事件时序与 MPI shared offset。
- **提交状态**（分支 / commit / 谁 push）：RMC `Neural_Network_WW_Iteration`，本地提交 `5ec595e1`；根工作区档案待同步提交；未 push。

> **模式 C 追加 · 结果解释**：合法输入回归通过说明该检查不改变已支持的 mesh WW 映射；9/11 项输入被拒绝说明 RMC 不再把没有明确 $w_L(m,g)$ 含义的外部数组带入输运。该结果不外推到未测的多能群、异构、并行或事件时序问题。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-19 19:59 | 立项 |
| 2026-09-19 | 完成 native WWMESH 输入数组 → 空间×能群形状 → 运行期访问的数据链审计；用户确认不匹配输入应报错停止 |
| 2026-09-19 | 实施初始化期 shape check；MPI-off 16 核构建、合法 mesh WW 3/3 回归、9/11 项拒绝输入均通过 |

> 关键命令、误判与修正、未决分歧都写在这里；人机讨论较深时把要点并入本表，**不再单独建会话纪要文件**。原始聊天转储不要入仓（可能含凭据）。

**证据等级（可选）**：物理/审查结论可标 E0–E4；工程、文档、治理任务可省略。
