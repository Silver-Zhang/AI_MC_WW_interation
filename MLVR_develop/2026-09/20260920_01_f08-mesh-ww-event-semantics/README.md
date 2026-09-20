# f08-mesh-ww-event-semantics

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-20 |
| 状态 | 已完成（限定支持范围） |
| 任务类型 | 物理语义审查 / mesh WW 事件时序 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | W10 |
| 涉及文件 | `RMC/src/ReadWeightWindow.cpp`、`WeightWindows.cpp`、`InitiateAll.cpp`、`TrackWithWeightWindow.cpp`、`DoMeshWeightWindow.cpp`、`MeshFun.cpp`、`SaveSplitParticles.cpp` |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / 审查快照 `41cf4559`；只读，未改 RMC |

---

## 1. 目标与范围（① 立项 · Agent 填）

**要做什么**：审查正向 fixed-source 中 native track mesh 与 MCNP `WWINP` point mesh 权重窗的查窗、roulette/split、tally 和移动时序。
**涉及什么**（仓库 / 模块 / 数据）：RMC `WWMESH:N/P`、`WWINP`、固定源中子/光子输运、track-length tally、split bank；电子专用路径仅记录为范围外。
**怎样算完成**：给出可复核事件链，区分已证实实现行为和未定义的物理契约；若存在修复选择，停在模式 C 人拍板关口。
**原始材料**（`logs/` 下有什么，原样保存）：`logs/20260920_mesh-ww-ctest.txt`（当前 RMC build 与 native mesh WW 回归真实输出）。

> **模式 C 追加 · 物理解释**：对于长度 $\ell$，进入该段前的 roulette/split 后，全部后代对 track-length score 的期望应保持 $w_{in}\ell$。因此 track mesh 必须在段起点处理，bank 副本也必须从相同起点继续。若产品将 point mesh 定义为“进入 mesh 即触发”，却只在部分自由程端点触发，则该契约不成立；反例是粒子跨进高重要性 mesh 后在下一检查点前碰撞或终止。

---

## 2. 做法与证据（② 设计 · ④ 实施 · Agent 填）

**设计 / 定位**（读了什么、查到什么；关键证据给 `文件:行号` 或数据位置）：

### 输入路径与实际可达模式

- `RMC/src/ReadWeightWindow.cpp` 的 native `WWMESH:N/P/E` 将 mode 设为数值 `3` 的 track mesh；现有 `var_reduce_wwmesh_n/p/e` 输入均走该路径。
- `RMC/src/InitiateAll.cpp` 只在 `p_bUseMCNPweightwindow` 时调用 `InitiateWeightWindow()`；`RMC/src/WeightWindows.cpp` 的该函数对已有 mesh 参数改为 point mesh。故 native `WWMESH` 实际走 **track**，而 `WWINP` 是当前 **point** 主入口，二者不是同一输入的可选实现。

### Track mesh：事件链和状态闭环

`RMC/src/TrackWithWeightWindow.cpp` 将该自由程交给 `DoTrackMeshWeightWindow()`；`RMC/src/DoMeshWeightWindow.cpp` 先以 `CalcUniversalMeshTrack()` 切为 `(mesh index, segment length)`，之后每段为：

```text
段起点 → 查该段 WW → roulette/split → 若存活则 TallyByTL(该段) → FlyByLength(该段)
```

- `RMC/src/MeshFun.cpp` 按轨迹顺序生成 Cartesian 均匀/异构段。权重窗 mesh 的 `p_bUseVol` 默认 `false`（`Mesh.h`），所以 tally 使用物理段长。
- `RMC/src/WeightWindows.cpp` 保留当前粒子并把额外 $n-1$ 副本放入 bank；`SaveSplitParticles.cpp` 保存执行 split 时的段起点，`SampleNeutronSource.cpp` 取出后重新定位。因此 split 后代会从同一段起点重走。就权重期望而言，$E[\sum_i w_i\ell]=w_{in}\ell$ 的段级关系闭合。
- 当前未发现 track path 存在“离开该段后才对该段执行 WW”的确定性时序错误。

### Point mesh：已证实的触发缺口

`RMC/src/TrackWithWeightWindow.cpp` 的 point 分支不按 mesh 面切段，而以

$$d_{avg}=1/\Sigma_t$$

切分完整子段。每个完整子段严格为 `TallyByTL(d_avg) → FlyByLength(d_avg) → DoPointMeshWeightWindow(端点)`；循环退出后的最终余段仅 tally 和移动，**没有** point-WW 调用。

```text
完整 d_avg 子段：tally → move → point WW
最终余段（碰撞/表面端点）：tally → move → 不触发 point WW
```

已由源码确认：

1. point WW 不保证在 WW mesh 几何面穿越时触发；
2. 若自由程 $d\le d_{avg}$，该次输运没有 point-WW 触发；
3. 最终碰撞/表面端点不会按该端点位置和可能更新后的能量再执行 point WW。

这不自动证明 tally 期望有偏：已发生的段仍按进入该段的权重 score，roulette/split 的守恒关系未被否定。但其语义与“进入空间 mesh 立即控制”不同，且与 track mesh 不可默认等价。源码/现有文档未定义点检查间距或端点遗漏的产品契约，故结论为 **C — Verify / 待决策**，不直接标为确定缺陷。

**方案选择**：本阶段只完成静态闭环与既有回归；不以 native track regression 代替 `WWINP` point 端点/跨 mesh 的粒子级验证。建议先明确 point 的目标触发集合。
**实施要点**（改了什么；改动快照见 `changes.diff`，无代码改动写“无”）：无 RMC 代码改动；新增本任务档案和回归原始输出。
**验证输出**（贴真实命令与输出；物理结论从严，工程/文档从简）：

```text
cmake --build /tmp/rmc-f08-cell-ww-build -j16 && ctest --test-dir /tmp/rmc-f08-cell-ww-build --output-on-failure -R '^test_var_reduce_wwmesh_[npe]$'

[100%] Built target RMC
test_var_reduce_wwmesh_e ... Passed
test_var_reduce_wwmesh_n ... Passed
test_var_reduce_wwmesh_p ... Passed
100% tests passed, 0 tests failed out of 3
Total Test time (real) = 9.28 sec
```

**未覆盖到的验证**（如实写；没有就写“无”）：没有专用 `WWINP` point-mesh 输入在“跨 mesh 后立即碰撞/终止”的动态 oracle；没有逐事件 PTRAC/测试替身核验 track split 后代的全部状态；未判定电子专用路径、TMS、MPI shared mesh、adjoint+WW。当前 3/3 regression 仅证明 native track mesh 未回归，不能验证 point 语义。

---

## 3. 决策记录（③ · **人拍板**）

- **决定**（采纳什么方案）：采纳方案 2：跳过 point mesh 修复。第一版 MLVR 框架只使用 native `WWMESH` 的 track mesh，不读取、不生成、也不承诺 MCNP `WWINP` point mesh 的事件语义。
- **决定人 / 日期**：用户 / 2026-09-20
- **约束**（能不能动接口 / 基准 / 算力预算…）：不改 `RMC/`；不更新 benchmark/reference；框架文档/接口不得笼统宣称支持所有 mesh WW，必须标明只支持 native track mesh。

**变更卡（B/C 模式，各一行）**：
| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| point WW 在最终余段、短自由程或 mesh 面穿越后不触发，语义与 track 不等价 | 本任务不改 `TrackWithWeightWindow.cpp`；MLVR 仅使用 native track mesh，不接入 `WWINP` point mesh | 框架设计阶段将输入/输出限定为 native `WWMESH`；若未来需要 MCNP 互操作，必须另立任务并建立 point-mesh oracle | 无 RMC 改动；撤销范围声明即可重新立项 |

> **模式 C 追加 · 人类理解确认**：用户确认框架将使用 track mesh，因此决定跳过 point mesh 修复。双方认可 native `WWMESH` 是 track 路径，而 `WWINP` 是 point 路径；第一版 MLVR 不把 point mesh 纳入已支持范围。

> 未拍板前，Agent 不得改动 `../RMC` 下的任何文件。



---

## 4. 结论与边界（⑤ 归档）

- **结论**：native `WWMESH` 的 neutron/photon 实际使用 track mesh，事件顺序为“段起点 WW → 该段 tally → 移动”，满足本框架所需的空间段级控制语义。`WWINP` point mesh 存在“完整平均自由程端点才触发、最终余段不触发”的已知非等价行为；用户决定不修复，第一版 MLVR 明确排除该路径。
- **不能推出什么**（边界）：native mesh WW 3/3 regression 不放行 point/WWINP、电子、TMS、MPI 或 adjoint 支持；本结论不将 point 行为断言为 tally 偏差，也不禁止 RMC 独立使用 point mesh。
- **遗留 / 下一步**：进入 W10 的下一项 track/框架相关工作：MPI shared mesh 多粒子类型 offset 审查与修复决策；`ParticleAttr` 状态复制和 adjoint+WW 仍保持独立范围。
- **提交状态**（分支 / commit / 谁 push）：RMC 无改动、无 commit；根工作区档案未归档、无 commit。

> **模式 C 追加 · 结果解释**：审查支持“track mesh 在空间段入口控制粒子表示”的假设，故它可作为 MLVR 的唯一 mesh WW 路径；审查未验证 point mesh，也不把 point 的触发延迟扩大解释为响应偏差。支持范围止于 native forward track mesh。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-20 15:07 | 立项 |
| 2026-09-20 | 阅读 native/MCNP 输入、初始化、neutron/photon 输运、mesh 分段、tally 和 split bank 链；确认 native=track、WWINP=point。 |
| 2026-09-20 | 静态确认 track 为段起点 WW→tally→移动；point 仅在完整平均自由程端点触发，最终余段无触发。 |
| 2026-09-20 | MPI-off build 成功；native mesh WW neutron/photon/electron CTest 3/3 通过，原始输出存入 `logs/`。 |
| 2026-09-20 | 进入模式 C 决策关口，等待确认 point 触发语义。 |
| 2026-09-20 | 用户决定跳过 point mesh 修复；第一版 MLVR 仅使用 native `WWMESH` track mesh，排除 `WWINP` point mesh。任务归档。 |

> 关键命令、误判与修正、未决分歧都写在这里；人机讨论较深时把要点并入本表，**不再单独建会话纪要文件**。原始聊天转储不要入仓（可能含凭据）。

**证据等级（可选）**：物理/审查结论可标 E0–E4；工程、文档、治理任务可省略。
