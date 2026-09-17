# f02-angular-density-asset-qualification

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-25 |
| 状态 | 已完成（发现 E；W9 后续已由任务 12 修复） |
| 任务类型 | 物理验证 / 验证资产资格化 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F02 |
| 涉及文件 | 任务侧 MGACE/HDF5、独立 oracle、PTRAC/响应 harness；只读 `RMC/` |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `6d2087518e0d9f23574d629f5fde361c79f519e4` |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：资格化 F02 有界 A 级验证所需的私有 MGACE 条件角分布和 density-mesh HDF5 资产，并动态确认 standard ASCII MGACE fixed-source neutron-adjoint 的负单变量角采样分支是否构成生产缺陷。

**范围**：只读 `RMC/` 和部署核数据；仅在本任务创建生成器、独立读回工具、私有数据、输入、日志和分析结果。运行范围限定 Linux x86_64 串行 Release、ASCII MGACE、`FIXEDSOURCE`、neutron adjoint、`ais=OFF`。不修改 `RMC/`，不更新部署核库、reference/benchmark，不覆盖 CE、光子/电子、显式 delayed、WW、GPT、MPI/OpenMP 或 Windows。

**验收标准**：

1. 私有 MGACE/HDF5 均有生成器、独立 readback oracle、schema/locator/shape/单位/理论支持域检查和 SHA256；RMC 实际加载与 oracle 一致。
2. MGACE 覆盖 isotropic、`ISANG=0,NLEG=1` 正/负单变量、equiprobable multi-bin 和 `ISANG=1` discrete-cosine。
3. density mesh 覆盖常数比 `0.5/1/2` 与两区互换，并验证 HDF5 schema、`[x][y][z]` 轴序和 gram-density ratio 语义。
4. 负单变量试验闭合“读回正确 → 标准调用链可达 → 碰撞方向可观测 → 支持域/矩/方向模与理论比较”；其余角表示为控制。
5. 只有 locator/readback 正确、标准路径到达且出现越界/错误矩或最终响应不互易，才判 **E — Defect**。若确认 E，立即停止 A formal，另立修复任务并等待 `RMC/` 改码拍板。
6. 原始输出、命令、种子、依赖、哈希和未覆盖范围完整归档；不挑 seed、删除失败或事后改判据。

**原始材料**：`logs/user_request.txt` 原样保存本轮请求；后续基线、生成、读回、构建、运行和分析输出均原样写入 `logs/`。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：W5/W6/W7 已提交为 `6d208751...`。既有 P0 非裂变、非均匀 cell-density、total-nubar oracle/bank reachability 和一个 NNUBAR=2 最终响应案例通过，但尚无已资格化的 density-mesh 与强条件角分布证据，F02 因此保持 C — Verify。

**可证伪局部假设**：`GetMgAdjNeuExitErgMu()` 的 `ISANG=0,NLEG=1,x<0` 分支可由标准路径到达，并因使用 `-1+2ξ(1-x)` 而产生超出正确前向支持域 `[-1,1+2x]`、甚至大于 1 的余弦。对 `x=-0.5`，正确支持域为 `[-1,0]`、均值为 `-0.5`，当前伴随公式的原始范围为 `[-1,2]`。早期曾误把表值 `x` 当作端点并写成 `[-1,x]`；前向动态对照否定后，已按“`x` 是均值”修正 oracle、分析器和本档案。

**证据链**：

| # | 位置 | 说明 |
|---|---|---|
| 1 | `RMC/src/GetMgExitErgMu.cpp:GetMgNeuExitErgMu` | 前向负单变量使用 `-1+2*Rand()*(1+x)`，支持域为 `[-1,1+2x]`、均值为 `x`。 |
| 2 | `RMC/src/GetMgExitErgMu.cpp:GetMgAdjNeuExitErgMu` | 伴随使用 `-1+2*Rand()*(1-x)`；`x=-0.5` 时范围为 `[-1,2]`。 |
| 3 | `RMC/src/GetExitState.cpp` | `MuLab` 进入方向旋转，是动态 reachability 和最终影响控制点。 |
| 4 | `RMC/src/GetLocationInfo.cpp:GetLocationDensRatio` | mesh gram density 除以 cell 基准 gram density得到局部比例。 |
| 5 | `RMC/src/Mesh/StructuredMesh/StructuredMesh.cpp`、`.h` | 定义 HDF5 geometry、dataset shape 和坐标 lookup。 |
| 6 | `RMC/tests/mesh/feedback.h5`、`inp` | 已有 `dens=-3` 与 density `MeshInfo` 格式先例。 |
| 7 | `RMC/tests/ptrac_grp/inp` | PTRAC 可输出碰撞事件与方向状态。 |

**影响面**：本任务只生产证据。若确认缺陷，影响可达的负单变量 neutron-adjoint 条件角散射；photon/secondary-adjoint 重复实现另行审查。私有数据不进入部署核库或基准体系。

**为什么之前没做/没发现**：部署 MGACE 的 `NLEG=0`，旧审查只能静态识别公式差异；先前也未定位 density HDF5 先例。现已由仓库 mesh/PTRAC 测试闭合格式和观测路径。

---

## 3. 方案选项（② 设计/定位 · Agent 填）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A：独立资产 + 动态闭环 | 生成最小私有数据、独立读回，先做 PTRAC 支持域/矩，再做最终响应。 | 成本较高，但可区分格式错误、不可达与生产缺陷。 | ★推荐 |
| B：仅静态 oracle | 直接以公式越界判 E。 | 不能证明数据可达和运行影响。 | 不采用 |
| C：跳过确认直接 formal | 只扩充可运行 P0 案例。 | 回避确定性风险，无法达到 A。 | 禁止 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A，先资格化资产，再动态闭合负单变量角采样证据。
- **决定人 / 日期**：用户，2026-08-25（“Start implementation”）。
- **理由与约束**：授权任务目录内生成器、私有 MGACE/HDF5、隔离构建和验证；不授权修改 `RMC/`，不更新部署核库、reference/benchmark，不 commit/push/切分支。确认缺陷后另立修复任务并再次等待拍板。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 建立任务档案 | `new_task.sh f02-angular-density-asset-qualification F02` | 已登记 INDEX。 |
| 2 | 冻结任务边界与原始请求 | 本 README、`logs/user_request.txt` | 任务侧实施已授权；RMC 改码门禁关闭。 |
| 3 | 生成并独立资格化 MGACE | `tools/generate_angular_mgace.py`、`verify_angular_mgace.py` | 五类一群纯自散射表的 NXS/JXS/XSS、locator、P0、支持域、矩和 SHA256 通过。 |
| 4 | 建立标准动态路径 | `generate_dynamic_cases.py`、`run_dynamic_cases.py` | 使用 `RMC inp -d <private-xsdir-dir>`；未修改部署核库。 |
| 5 | 修正观测方法 | `analyze_dynamic_angles.py` | PTRAC 不记录伴随 elastic，且 `UpdateNeuStateMg()` 会归一化方向；改用源射线/末段射线交会重建单碰撞余弦。 |
| 6 | 低光学厚度对照 | `runs/negative_low_optical_depth` | 100000 前向 + 100000 伴随历史，原子密度 `0.001×10^24 cm^-3`，seed 17。 |
| 7 | 缺陷分类 | `logs/low_optical_analysis_final.json` | 前向 `0/509` 越界；伴随 `161/330` 越界；多碰撞解释 Chernoff 上界 `<10^-175.52`，判 E。 |

**代码改动**：本任务不修改 RMC；任务侧工具与输入直接保存在本目录。归档时生成空的 `changes.diff` 并核对 RMC clean。

---

## 6. 验证 / 实验记录（④ · Agent 填）

| 验证项 | 命令 | 结果 |
|---|---|---|
| 工具语法 | `python3 -m py_compile tools/*.py` | 通过；Python 3.12.3。 |
| MGACE 独立读回 | `verify_angular_mgace.py ...` | `qualified_cases=5`；负单变量 `support=[-1,0] mean=-0.5`；报告 SHA256 `3ecdbec8...85c37f5`。 |
| 标准路径 pilot | 200-history negative adjoint | 退出码 0；私有 xsdir/ACE 被生产读取器加载。 |
| 高密度方法对照 | 1000 forward + 1000 adjoint | 暴露仅凭射线交会会混入多碰撞；未用于最终 E 分类。 |
| 低光学厚度正式判别 | 100000 forward + 100000 adjoint | 两运行均退出 0；前向碰撞直方图校准：510 条真实单碰撞，重建 509，假阳性 0、漏检 1。 |
| 支持域结果 | `low_optical_analysis_final.json` | 前向余弦范围 `[-0.996164,-0.001770]`、`0/509` 越界；伴随余弦范围 `[-0.988493,0.993678]`、`161/330` 越界。 |
| 多碰撞替代解释 | 同上 | 多碰撞历史期望上界 4.9627；出现至少 161 条的 Chernoff 概率上界 `10^-175.5227`。 |
| 基线完整性 | `logs/final_baseline.txt` | RMC clean at `6d208751...`；binary SHA256 `f3870bf4...1f0887`；未修改 RMC/reference/benchmark。 |

**实验设置**：seed 17；RNG type 2、stride 1000000；5 cm 球；一群总截面/P0 均为 1 barn、吸收 0；正式判别原子密度 `0.001×10^24 cm^-3`；每模式 100000 histories；Python 3.12.3；RMC binary SHA256 见 `final_baseline.txt`。生成、运行与分析完整命令保存在本节对应工具、manifest 和原始日志中。

正式低光学厚度实验可从任务目录重现：

```bash
python3 tools/generate_dynamic_cases.py --assets assets/mgace --root runs/negative_low_optical_depth --case one_variable_negative --mode forward --mode adjoint --population 100000 --seed 17 --density 0.001
python3 tools/run_dynamic_cases.py --root runs/negative_low_optical_depth --rmc /tmp/mlvr_f02_rmc_build/bin/RMC --output logs/low_optical_run.json
python3 tools/analyze_dynamic_angles.py --root runs/negative_low_optical_depth --output logs/low_optical_analysis_final.json
```

归档时删除了两份可再生成的正式 `inp.PTRAC`（31,533,437 与 31,451,104 bytes），因为单文件超过 10 MB；输入、manifest、运行报告、最终逐历史分析 JSON、摘要和 SHA256 均保留。清理后本任务无超过 10 MB 的单文件。

**未覆盖到的验证**：按预设停止规则，确认 E 后未继续 density-mesh HDF5 资格化、其他四类角表示的 RMC 动态矩、A formal 互易性矩阵、GPU/MPI/OpenMP/Windows/AIS/CE。未更新任何 reference、benchmark 或部署数据。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：标准 ASCII MGACE fixed-source neutron-adjoint 的负单变量角分支动态确认为 **E — Defect**。`x=-0.5` 的正确支持域 `[-1,0]` 在前向 `0/509` 越界，伴随却 `161/330` 越界并达到 `0.993678`；A formal 已停止，不能达到 A。
- **遗留问题 / 后续待办**：独立修复任务 `20260825_12_f02-adjoint-negative-one-variable-angular-fix` 后续已完成一行根因修复、三 seed 动态回归、CTest 与 oracle 验证；F02 恢复 C。density-HDF5、其余角表示和 A formal 仍待后续任务。
- **知识库同步**：新增 W9；同步 F02 物理导读、`AGENT_CONTEXT.md` 与 INDEX。
- **是否已提交**：未 commit/push/切分支。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-25 19:54 | 立项。 |
| 2026-08-25 | 用户要求开始实施；冻结资产资格化和动态确认范围。 |
| 2026-08-25 20:16 | 低光学厚度动态证据确认 W9；任务按停止规则归档为 E，并建立独立修复任务。 |
| 2026-08-25 | 后续任务 12 修复 W9 并验证通过；本任务保留修复前反例，当前 F02 状态见知识库。 |

---

## 9. 工作日志

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成任务目录、logs 和 INDEX 行。 |
| 2 | 检查基线与工作树 | Git 状态与历史 | RMC clean at `6d208751...`；保留根工作区既有改动。 |
| 3 | 读取代码、测试与格式先例 | angular、StructuredMesh、mesh/PTRAC tests | 局部假设和最小动态判别路径已确定。 |
| 4 | 首次 MGACE oracle | `verify_angular_mgace.py` | 固定 18 行下限误拒合法短表；改为 token/NXS 长度检查后五表通过。 |
| 5 | 首轮 PTRAC | pilot runs | 发现伴随不写 elastic，且状态更新归一化方向；否定“穿面方向模”观测法。 |
| 6 | 射线交会 pilot | 200/1000 histories | 高密度前向也出现旧支持域“越界”，促使纠正 NLEG=1 语义及多碰撞混淆。 |
| 7 | 修正理论 oracle | MGACE code + forward source | 确认 `x` 为均值；`x=-0.5` 正确支持域为 `[-1,0]`。 |
| 8 | 低光学厚度正式判别 | 100000 histories/mode | 前向校准无假阳性；伴随 161 条支持域违例，替代解释尾界 `<10^-175.52`。 |
| 9 | E 分类与停机 | 本档案、W9、任务 12 | 停止 A formal；未修改 RMC。 |
| 10 | 归档体积审查 | `find ... -size +10M` | 删除两份可再生成的 >10 MB PTRAC；复查无输出。 |
