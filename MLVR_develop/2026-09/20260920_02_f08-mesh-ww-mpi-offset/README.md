# f08-mesh-ww-mpi-offset

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-20 |
| 状态 | 已完成（修复 + 双粒子 MPI 回归；红测→绿测闭环） |
| 任务类型 | 缺陷修复 / MPI shared mesh 参数布局 |
| 任务模式 | B — 工程协作（默认） |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | W10 |
| 涉及文件 | `RMC/src/WeightWindows.cpp`（修复）；`RMC/tests/MCNP_WeightWindow_MPI_multi_particle/`、`RMC/tests/MCNP_WeightWindow_MPI_ShareMem_multi_particle/`（新增回归）；`RMC/tests/{CMakeLists.txt,configure.yaml}`（注册）；本档案 `changes.diff`、`changes-new-files.diff`、`logs/` |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / 基线 `41cf4559`；修复已在工作区完成，**未 commit**（硬规则 5：是否提交由用户决定） |

---

## 1. 目标与范围（① 立项 · Agent 填）

**要做什么**：审查 MCNP `WWINP` 的 `MPISHAREWEIGHTWINDOW` 在多粒子类型、不同能群数时，shared-memory 扁平数组的写入和读取 offset 是否一致；给出最小修复和定向 MPI 验证方案。
**涉及什么**（仓库 / 模块 / 数据）：仅 MCNP `WWINP` point-mesh 的单节点 MPI shared-memory 优化；不涉及 native `WWMESH` track mesh、point mesh 时序、roulette/split 数学或 adjoint。
**怎样算完成**：确认实际数组布局与 offset 公式，量化错位条件；提出不改变输入格式的最小修复、两粒子类型异能群 oracle 和回滚方式，等待人拍板后再改 RMC。
**原始材料**（`logs/` 下有什么，原样保存）：

- `2026-09-20_prefix-fail_shared_mpi_2rank.log`：修复前二进制跑新 shared 回归的失败输出（harness 报 `results do not agree`，仅 photon tally 行不同）。
- `2026-09-20_prefix-fail_shared_mpi_2rank_error_result.txt` / `..._tally.txt`：修复前的错误输出与原始 tally。
- `2026-09-20_final_MCNP_WeightWindow_MPI_{multi_particle,ShareMem_multi_particle}_mpi2.md` / `..._tally.txt`：修复后 2 rank 直接运行原始输出与 tally。
- `2026-09-20_harness_matrix.md`：16 行真实测试矩阵（命令 + 退出码，含 MPI 2/10 rank、MPI+OpenMP、MPI-off serial、native mesh WW）。

> **模式 C 追加 · 物理解释**：物理对象与正确关系是什么；假设成立应观察到什么；什么结果会推翻它。（几句话即可，不必成表。）

---

## 2. 做法与证据（② 设计 · ④ 实施 · Agent 填）

**设计 / 定位**（读了什么、查到什么；关键证据给 `文件:行号` 或数据位置）：

### 范围与可达性

- `MPISHAREWEIGHTWINDOW` 仅由 `RMC/src/ReadMCNPWeightWindowCard.cpp:305-310` 识别；用户手册 `RMC/docs/source/usersguide/减方差.rst:102-105` 也明确它只对 `WWINP` 的 MCNP 格式权窗有效、仅限单节点。因此它**不影响**第一版 MLVR 已冻结的 native `WWMESH` track-mesh 主路径。
- `WWINP` 读入 `p_nMaxParicleType=ni`、各粒子独立能群边界和 `p_vMeshInformation[particle][mesh][energy-bin]`（`ReadMCNPWwinpFile.cpp:239-276`）。现有 shared-memory 回归仅有 neutron：输入 source/tally 都是 particle 1，`WeightWindowRead` 的 `ni=1, ne(1)=1`，故不能覆盖多粒子 offset。

### 已确认的数组错位

设共同空间 mesh 数为 $M$，粒子 $q$ 的能群数为 $G_q=|E_q|-1$。

- 主进程在 `WeightWindows.cpp:251-268` 分配并连续写入每个粒子的 $M\times G_q$ 个 `CDWeightWindowParameter`：

	$$\text{writeOffset}(q)=\sum_{r<q}M G_r.$$ 

- 每次查窗在 `WeightWindows.cpp:54-61` 使用：

	$$\text{readOffset}(q,m,g)=D_q+M G_q\,m+g,$$

	其中段内索引正确，问题在 $D_q$。
- `WeightWindows.cpp:187-191` 当前计算：

	$$D_q=D_{q-1}+M\,|E_q|=D_{q-1}+M(G_q+1).$$

	它错误地使用了**当前粒子**的能量边界数，并且多算一个边界；应当累加**前一粒子**的实际写入长度 $M G_{q-1}$。

例如 neutron 有 $G_1=2$、photon 有 $G_2=3$、$M=10$：主进程先写 20 个 neutron 参数，photon 正确起点应为 20；当前公式给出 $D_2=10\times(3+1)=40$。photon 的第一项会读取 shared window 中第 40 项，即自身第三个 mesh 的第一能群值；读到最后会访问 60 之后的未分配位置（总长度仅 50）。这是确定的越界/错误参数读取路径，证据等级 **E1**。

### 现有保护与缺口

- 共享窗口总长度、主进程写入循环和非主进程 `MPI_Win_shared_query()` 都与实际 $\sum M G_q$ 布局一致（`WeightWindows.cpp:251-275`）；错误集中在 per-particle displacement。
- 代码只在 master 计算 `p_vParticleTypeMeshDisplc`，却没有将该向量广播；非 master 构造函数将它初始化为全零（`WeightWindow.h:80-84`）。所以即使修正 master 公式，非主 rank 仍会把 photon/electron 读取为 window 起点，除非显式广播/重建 displacement。这是同一数据布局问题的第二个确定错误路径。
- 如果 `ni=1`，默认 displacement 0 正确，故现有 test 能通过；如果多个粒子恰好不用 WW 或不被输运，也不会暴露。不能据此放行多粒子共享模式。

**方案选择**：建议以一个统一的 prefix-sum 在所有 rank 上按已广播的 `p_vEnergyBins` 重建 `p_vParticleTypeMeshDisplc`：

```text
offset = 0
for particle = neutron .. p_nMaxParicleType:
		displacement[particle] = offset
		offset += mesh_count * (energy_bins[particle].size() - 1)
```

这直接与 shared window 的分配/写入顺序同源，去除“前/当前粒子”和“边界/bin 数”混淆；不需要广播 displacement。另加初始化前 shape 检查，避免 `p_vMeshInformation[type][0]` 在 malformed/空粒子数据下被解引用。放弃只把 `size()` 改成 `size()-1` 的一行修补，因为它仍使用当前粒子的维度，并遗漏非主 rank。
**实施要点**（改了什么；改动快照见 `changes.diff`，新增文件见 `changes-new-files.diff`）：

1. 删除 master-only 的错误 displacement 公式（原 `D_q = D_{q-1} + M·|E_q|`）。
2. 在 mesh 广播之后、**所有 rank 上**用统一 prefix-sum 重建位移（与实际共享窗口写入顺序同源）：

   ```cpp
   int displacement = 0;
   for (int particleType = CDParticleState::Neutron; particleType <= p_nMaxParicleType; particleType++) {
     p_vParticleTypeMeshDisplc[particleType] = displacement;
     displacement += p_OWeightWindowMesh.GetTotMeshNum() * (int(p_vEnergyBins[particleType].size()) - 1);
   }
   ```

3. worker 在重建前先调用 `p_OWeightWindowMesh.CheckHeterMeshPara()` 得到 mesh 总数；删除原先位于函数末尾（共享窗口之后）的延迟 worker 调用。
4. 顺带修正广播数据类型：`p_vMeshNum` 是 `vector<int>`，原先按 `MPI_DOUBLE` 广播（cuboid/cylinder 两处），会以 8 字节/元素写入 4 字节缓冲区；现改为 `MPI_INT`。
5. 新增两个回归用例并注册（`tests/CMakeLists.txt`、`tests/configure.yaml`）、生成参考结果。

**验证输出**（真实命令 + 退出码；完整矩阵见 `logs/2026-09-20_harness_matrix.md`）：

| 场景 | 结果 |
|---|---|
| 修复前二进制（`git HEAD` 源码），新 shared 用例 `-n 2` | **失败**：`Error: results do not agree`，仅 photon tally 10 行全部不同、neutron 完全一致（`logs/2026-09-20_prefix-fail_shared_mpi_2rank.log`） |
| 修复后，新非共享用例 MPI 2 / 10 rank | 退出码 0 |
| 修复后，新 shared 用例 MPI 2 / 10 rank | 退出码 0 |
| 修复后，两用例 serial（1 rank，MPI 构建） | 退出码 0 |
| 修复后，两用例 MPI 10 rank + OpenMP 2 线程（MPI+OpenMP 构建） | 退出码 0 |
| 既有单粒子 shared 回归 `MCNP_WeightWindow_MPI_ShareMem`，`-n 10` | 退出码 0（无回归） |
| MPI-off serial：`MCNP_WeightWindow`、native `var_reduce_wwmesh_{n,p,e}` | 退出码全 0 |
| MPI-off serial：两个新用例 | 退出码 0（shared 用例为允许的 runtime error：`MPISHAREWEIGHTWINDOW must be used with MPI on.`） |

关键等价性：两个新用例的 `reference_result` 逐字节相同（`diff` 无输出），即 shared 窗口读取与各 rank 直读数组给出完全一致的 WW 参数（相同随机数流下 tally 逐位一致）。

```text
diff MCNP_WeightWindow_MPI_multi_particle/reference_result \
     MCNP_WeightWindow_MPI_ShareMem_multi_particle/reference_result
(无输出 → 两文件一致)

修复前失败对比（节选）：
  --------- ID = 2, Particle = photon ... --------------
  -1   6.2255E+00  5.5886E-02      ← 修复后 / 非共享基线
  +1   6.1630E+00  5.6022E-02      ← 修复前 shared（offset 错位）
  （neutron tally 两侧完全一致）
```

**测试资产要点**：`WWINP` `ni=2`（neutron G=2、photon G=3、mesh 10、两粒子下界可区分）；`inp` 中 `WWINP` 必须写在 `WWP` 之前——解析器在第二张 `WWP` 后会误判块结束（实测踩到，已补记入知识库 06 文档）。

**未覆盖到的验证**（如实写）：跨节点 MPI（`MPISHAREWEIGHTWINDOW` 本身仅限单节点）；Windows 侧；`WWINP` `nr=16` 圆柱网格 + shared 组合；electron 作为第三粒子类型；大规模算例/大 mesh 下的性能与内存；CI（GitLab）端尚未实际触发。

---

## 3. 决策记录（③ · **人拍板**）

- **决定**（采纳什么方案）：用户于 2026-09-20 明确指示“开始修复”。批准按 `$M\times G_q$` 的 prefix-sum 在所有 rank 重建 shared-memory displacement，并新增两粒子、异能群 `WWINP` MPI oracle。
- **决定人 / 日期**：用户 / 2026-09-20
- **约束**（能不能动接口 / 基准 / 算力预算…）：只修改 `RMC/src/WeightWindows.cpp` 和新增专用测试资产；不改 native track mesh、WWINP 文件格式、reference/benchmark、roulette/split 或跨节点语义。

**变更卡（B/C 模式，各一行）**：
| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| 多粒子 `WWINP` 共享窗口错位或越界，造成部分粒子读取其他粒子/错误 mesh 的 WW | 统一在 `InitiateWeightWindow()` 内重建 displacement；增加两粒子异能群 MPI test；不改 native `WWMESH`、point 时序、物理采样公式 | MPI 2 ranks 下新 oracle 应与非共享 MPI 基线在统计容差内一致，且 sanitizer/边界断言不报错；保留现有 single-neutron regression | 恢复旧 offset 逻辑并移除新增测试；不改参考结果 |

> **模式 C 追加 · 人类理解确认**：把“人现在理解了哪些关系、批准了什么范围”留下来——问答原文或一两句转述均可。

> 未拍板前，Agent 不得改动 `../RMC` 下的任何文件。

**执行结果**：已在授权范围内实施；未改 native track mesh、未改 WWINP 文件格式、未改任何基准/参考结果。所有验证通过（见第 2 节矩阵），修复前对照（红测）确认新回归可判别原缺陷。



---

## 4. 结论与边界（⑤ 归档）

- **结论**：多粒子 `WWINP + MPISHAREWEIGHTWINDOW` 的 shared-memory 位移已修复：
  1. 所有 rank 上用实际写入长度 $\sum_{r<q} M G_r$ 的 prefix-sum 重建 `p_vParticleTypeMeshDisplc`（替代 master-only 的 $M(G_q+1)$ 错误公式）；
  2. worker 在重建前完成 mesh 元数据初始化；
  3. 顺带修正 `p_vMeshNum` 的广播数据类型（`vector<int>` 误用 `MPI_DOUBLE`）。

  工程验证：修复前新回归报 `results do not agree`（仅 photon tally 偏移），修复后 shared 与非共享参考逐位一致；MPI 2/10 rank、MPI+OpenMP、serial、MPI-off serial 全部通过；既有单粒子 shared 回归与 native `WWMESH` 3/3 无回归。
- **不能推出什么**（边界）：
  - 本修复不影响 MLVR 第一版 native track mesh 主路径（该路径已回归且未改）；
  - 不能外推到跨节点共享窗口、`WWINP` `nr=16` 圆柱网格 + shared 组合、electron 第三粒子类型；
  - 实测 tally 一致性依赖“相同随机数流 + 相同 WW 参数”，不是统计等价性声明；
  - 修复前失败表现为 photon 参数错位（数值偏差而非崩溃）——越界读取未在本用例触发崩溃，不代表其他输入不会。
- **遗留 / 下一步**：RMC 提交由用户决定（当前工作区改动未 commit）；可选的 CI 端确认；随后处理 W10 split `ParticleAttr`。
- **物理导读同步**：本次为被 MLVR 第一版排除的 `WWINP` point mesh 路径上的工程修复，未改变物理结论、适用范围或风险描述，`MLVR_Physics_Guide/` 无需更新。
- **提交状态**（分支 / commit / 谁 push）：RMC `Neural_Network_WW_Iteration` 工作区改动，**未 commit / 未 push**（硬规则 5）；改动快照 `changes.diff`（跟踪文件）+ `changes-new-files.diff`（新增测试文件）；根工作区档案待提交。

> **模式 C 追加 · 结果解释**：结果支持或否定了哪个假设；通过/失败在物理上说明什么；不可外推的边界在哪。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-20 15:55 | 立项 |
| 2026-09-20 | 阅读 W10、工作流、shared-memory reader/initiation/lookup/cleanup 链和现有 MPI test；确认本任务为 B 模式工程修复审查。 |
| 2026-09-20 | 静态推导 shared-window 写入长度为 $M\times G$，现有 displacement 却以当前 `$|E|` 计算；同时确认 non-master 不接收 displacement。 |
| 2026-09-20 | 现有 MPI shared-memory test 被确认仅为 single-neutron (`ni=1, ne=1`)；进入待决策关口。 |
| 2026-09-20 | 用户明确批准“开始修复”：可在约束范围内修改 RMC 并新增定向 MPI 回归。 |
| 2026-09-20 | 实施 prefix-sum 修复；新增两粒子、异能群 `WWINP`（neutron G=2 / photon G=3）非共享基线与 shared 目标用例，并注册到 CMake/configure。 |
| 2026-09-20 | MPI 构建成功；首次 shared 运行报 `MPI_Win_free: invalid window`。排查：补 `MPI_INT` 广播修正后仍复现；加临时诊断（已移除）后发现 `p_bUseMCNPweightwindow=0`——输入里 `WWINP` 写在第二张 `WWP` 之后，解析器误判块结束。将 `WWINP` 提前后，shared 窗口 `size=50` 正常分配/释放。 |
| 2026-09-20 | 生成 10 rank 参考结果；shared 与非共享参考逐位一致。 |
| 2026-09-20 | 修复前对照（临时回退 `WeightWindows.cpp`，仅增量重编译）：新 shared 用例失败，仅 photon tally 偏移 → 回归判别力确认；随后恢复补丁并重建。 |
| 2026-09-20 | 完成 MPI 2/10 rank、MPI+OpenMP(2 线程)、serial、MPI-off serial、native mesh WW 3/3、既有单粒子 shared 回归全矩阵验证；生成 `changes.diff` / `changes-new-files.diff` 与 `logs/` 证据。 |

> 关键命令、误判与修正、未决分歧都写在这里；人机讨论较深时把要点并入本表，**不再单独建会话纪要文件**。原始聊天转储不要入仓（可能含凭据）。

**证据等级（可选）**：物理/审查结论可标 E0–E4；工程、文档、治理任务可省略。
