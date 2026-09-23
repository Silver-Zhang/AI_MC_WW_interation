# f04c-mg-native-ww-energy-contract

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-23 |
| 状态 | 已完成（物理 `WWE:N` 语义修复，待本地审核） |
| 任务类型 | 缺陷修复 / MG native WW 能量坐标契约 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F04 |
| 涉及文件 | `RMC/src/{WeightWindow.h,WeightWindows.cpp,DoMeshWeightWindow.cpp,DoWeightWindow.cpp,TrackWithWeightWindow.cpp,RayTracking.cpp,GmaGeoTracking.cpp}`；新增任务局部 V2–V5 输入/脚本/日志 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / 修复 commit `5cfb0f77`（未 push；基线 `b7d8a946`） |

---

## 1. 目标与范围（① 立项 · Agent 填）

**要做什么**：修复 standard MGACE 中 native `WEIGHTWINDOW` 的 `WWE:N` 物理能量网格与内部 `p_dErg` 群坐标不一致问题。对用户，`WWE:N` 始终保持物理能量网格（MeV）语义；RMC 在查窗时负责转换。

**涉及什么**（仓库 / 模块 / 数据）：fixed-source neutron forward/adjoint、native cell WW、native track/point mesh WW。排除 `WWINP`、continuous-energy 算法、split/roulette 数学、adjoint collision sampling、benchmark/reference 更新及其他 W10 问题。

**怎样算完成**：

1. 所有本任务范围内 native neutron WW lookup 在 MG 下使用当前群的物理群中心能量，在 CE 下继续直接使用 `p_dErg`；
2. forward/adjoint 共用同一转换逻辑；
3. 完成 V1–V5，且不更新 reference 让测试通过；
4. 生成 `changes.diff` 和真实验证日志，停在本地审核状态，不 push RMC。

**原始材料**（`logs/` 下有什么，原样保存）：前序独立静态审查见 `20260922_03_f04b-static-ww-contract-audit`；深穿透基线见 `20260922_02_f04b-deep-penetration-ww-benchmark`。本任务运行输入、命令、输出与分析结果存 `logs/`。

> **模式 C 追加 · 物理解释**：用户输入的 `WWE:N` 是物理能量分界。MG 输运内部用群编号提高效率，但查 WW 前必须将群编号恢复为该群的代表物理能量，才能在同一能量轴上选 bin。CE 状态本来就是物理能量，不应改变。若两能群 oracle 中两个已知物理能量群没有选到对应的不同 WW lower bound，或 WW-on/off 的深穿透 response 不再统计相容，则该修复假设被推翻。

---

## 2. 做法与证据（② 设计 · ④ 实施 · Agent 填）

**设计 / 定位**：

```text
MG particle p_dErg (group coordinate)
  -> native cell WW or track/point mesh WW entry
  -> GetWeightWindowEnergy(cAceData, particle)
  -> GetErgValue(p_dErg, particle type) = current group-centre physical energy
  -> WWE physical-energy bin lookup
  -> selected lower/survival/upper WW bounds
```

查窗路径：cell neutron `RayTracking.cpp -> DoWeightWindow()`；cell photon `GmaGeoTracking.cpp -> DoGmaWeightWindow()`；track/point mesh `TrackWithWeightWindow.cpp -> DoTrackMeshWeightWindow()/DoPointMeshWeightWindow() -> setMeshWeightWindowBound()`。它们当前都直接使用 `p_dErg`。CE 的 `GetErgValue` 原样返回 `p_dErg`，因此统一 helper 对 CE 无行为变化。电子不属于当前 MG `GetErgValue` 支持范围，维持其既有路径且不在本修复范围。

**方案选择**：采用单一 `CDWeightWindow` helper，复用 `CDAceData::GetErgValue()`，不复制群边界/index 算法、不建立 adjoint-only 分支。MG group-centre 是 RMC 既有 group→physical-energy 定义；群内没有连续能量状态，故使用其代表值是与现有模型一致的最小选择。cell 与 mesh API 增加只读 `CDAceData` 参数以使用同一 helper。

**实施要点**：

1. 在 `CDWeightWindow` 增加 `GetWeightWindowEnergy(CDAceData&, const CDParticleState&)`；复用 `CDAceData::GetErgValue()`。MG 将 `p_dErg` 群坐标映射为当前群中心物理能量；CE 由 `GetErgValue()` 原样返回 `p_dErg`。
2. native neutron cell WW (`DoWeightWindow`)、native photon cell WW (`DoGmaWeightWindow`)、native point mesh 与 track mesh WW 均通过这一 helper 查窗；forward/adjoint 没有专用分支，因此共用同一 contract。
3. `p_bUseMCNPweightwindow` 时 helper 保留 `p_dErg`，明确不改变本任务排除的 MCNP `WWINP` point-mesh 路径。
4. 更新中英文 native WW 用户手册：`WWE:N` 为物理 MeV 上界；MG 查窗使用群中心物理能量。
5. 改动快照：`changes.diff`。

**验证输出**：

| 验证 | 真实结果 |
|---|---|
| Build | `/tmp/rmc-f08-cell-ww-build`，MPI-off/OpenMP-off，exit 0；最终 binary SHA256 见 `logs/2026-09-23_final-binary-sha256.txt` |
| V1 / V4 native 回归 | `var_reduce_wwmesh_{e,n,p}`、`var_reduce_wwn_{n,p}`：5/5 passed；既有 `fixed_source_adjoint`：1/1 passed；未更新 reference |
| V2 MG forward oracle | 同一 0.2435 MeV source group，`WWE:N=0.3` 选低 bin (0.1)、`WWE:N=0.2` 选高 bin (0.4)；低/高每源碰撞比 1.09253 > 1.05，exit 0 |
| V3 MG adjoint oracle | 同一输入/物理边界，低/高每源碰撞比 2.03153 > 1.05，exit 0；共用 forward helper，无 adjoint-only 分支 |
| V5 100 cm water slab | 5 seed × 1M histories，energy-dependent `WWE:N=1 MeV`；$R_A=5.12924\times10^{-4}\pm9.30112\times10^{-6}$，$R_{WW}=5.15902\times10^{-4}\pm3.86135\times10^{-6}$，$z=0.29571$，通过统计相容；FOM ratio=9.27935 |

V2/V3 原始 JSON/日志见 `logs/2026-09-23_v2-v3-bin-oracle.{json,log}`；V5 原始 JSON/日志及 10 个 run 输入、stdout/stderr/tally 见 `logs/2026-09-23_v5-deep-energy-dependent.{json,log}` 与 `runs_v5/`。V1/V4 真实 CTest 输出见 `logs/2026-09-23_v1-v4-native-ww-ctest.log`、`logs/2026-09-23_fixed-source-adjoint-ctest.log`。

**未覆盖到的验证**：MPI/OpenMP、连续能量（设计上由 identity branch 保持）、electron、MG photon、MCNP `WWINP`、cylindrical mesh、多群内不同物理能量的边界敏感性、真实 MLVR window 生成链。

---

## 3. 决策记录（③ · **人拍板**）

- **决定**（采纳什么方案）：用户于 2026-09-23 明确决定：`WWE:N` 对用户始终保持物理能量网格语义；MG 内部必须转换当前 transport group 为物理能量后查窗；CE 直接使用 `p_dErg`；forward/adjoint 共用统一逻辑。批准在限定范围内实施并执行 V1–V5。
- **决定人 / 日期**：用户 / 2026-09-23
- **约束**：不改变 `WWE:N` 用户语义；不要求群编号输入；不改 adjoint collision、split/roulette、benchmark/reference 或其他 W10；完成本地构建/验证后停止，RMC 不自动 push。

**变更卡（B/C 模式，各一行）**：
| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| MG group coordinate 被误作物理 MeV 查 WW，导致错误 bin/VR 行为 | 仅 native cell/track/point mesh WW 的 lookup-energy helper 和直接调用者；不改 parser 语义、WW 数学或 `WWINP` | V2/V3 两群 oracle 必须证明 forward/adjoint 各群选对物理 `WWE:N` bin；V4 回归不得更新 reference；V5 response 必须统计相容；任何失败停止 | 恢复本任务 RMC diff；任务输入/脚本可删除 |

> **模式 C 追加 · 人类理解确认**：用户已明确理解并批准“`WWE:N` 始终为物理能量网格，RMC 负责 MG 群坐标→物理能量转换”的接口原则；接受 group-centre 作为 MG 群的既有代表物理能量，并要求 forward 与 adjoint 同逻辑。

> 未拍板前，Agent 不得改动 `../RMC` 下的任何文件。



---

## 4. 结论与边界（⑤ 归档）

- **结论**：已修复 MG native WW 的能量坐标契约。`WWE:N` 现在统一表示物理 MeV 能量网格；MG forward/adjoint 在 native cell/track/point mesh 查窗前使用当前群中心物理能量；CE 行为保持原样。V2/V3 表明物理边界可使同一 MG source group 切换预期 WW bin；V5 energy-dependent 深穿透伴随 WW-on/off 合并 $z=0.29571$，未观察到修复引入 bias，并取得 9.27935× FOM。
- **不能推出什么**（边界）：群中心是 MG 群的代表能量，不等同于群内连续谱；本任务不验证 MG photon/electron、MCNP `WWINP`、MPI/OpenMP、cylindrical mesh 或真实 MLVR 生成 window；CE 未改变仅由现有回归和 `GetErgValue` identity 分支支持。
- **遗留 / 下一步**：若第一版需要 MG photon、MPI 或 `WWINP`，另立验证任务；`WWE:N=0` 仍会被 parser 作为显式上界而形成额外 bin，输入需省略 `WWE:N` 以表示默认单 interval，这一既有 parser 行为不在本任务修复范围。
- **提交状态**：RMC 修复已本地 commit `5cfb0f77`（未 push，待 push 时机）；根工作区档案随 2026-09-23 提交入库；`runs/`、`runs_v5/` 运行目录按归档体积规范不入库、仅保留本地。

> **模式 C 追加 · 结果解释**：修复前，MeV 边界与群编号在数值轴上混用；修复后，两者先回到同一物理能量轴再做 bin 选择。V5 的统计相容支持“本修复只纠正 WW 的选择，不改变伴随响应的期望”；FOM 增益说明所选深穿透 window 在该问题上有效，但不能推广为所有 window 的收益。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-23 18:22 | 立项 |
| 2026-09-23 | 用户给出 Stage 3 修复授权与物理能量网格接口原则。 |
| 2026-09-23 | 读取 cell/track/point WW、MG conversion 和 CE fallback：确认统一 helper 可覆盖 neutron cell/mesh lookup，CE fallback 是恒等映射；电子暂不纳入 MG helper。 |
| 2026-09-23 | 设计 V1–V5 与最小统一 helper，记录 group-centre 的边界语义和停止条件；进入实施。 |
| 2026-09-23 | 实现单一 native WW lookup-energy helper，并收紧范围：`WWINP` point mesh 保持既有群坐标行为。首次 build 因 `GetErgValue` 非 const 接口失败，改为非 const ACE 引用后成功；没有修改 MG 算法或 WW 数学。 |
| 2026-09-23 | V2/V3 oracle 首轮使用不同物理源能量，不能严格隔离 bin 选择；已改为同一 0.2435 MeV group、仅切换 `WWE:N` 物理边界，forward/adjoint 都显示预期低/高 bin 的可观测碰撞数差异。 |
| 2026-09-23 | 完成 V1–V5；更新中英文手册；生成 `changes.diff` 与真实 logs。按授权停止在本地审核状态，未 commit/push RMC。 |

> 关键命令、误判与修正、未决分歧都写在这里；人机讨论较深时把要点并入本表，**不再单独建会话纪要文件**。原始聊天转储不要入仓（可能含凭据）。

**证据等级（可选）**：物理/审查结论可标 E0–E4；工程、文档、治理任务可省略。
