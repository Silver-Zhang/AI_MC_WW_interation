# f04-adjoint-weight-window

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-20 |
| 状态 | 已完成（C — Verify，冻结 neutron native-WWMESH 子域） |
| 任务类型 | 组合功能审查 / 物理兼容性验证 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F04 |
| 涉及文件 | 预期只读：`RMC/src/{WeightWindows.cpp,DoPointMeshWeightWindow.cpp,DoWeightWindow.cpp,TrackWithWeightWindow.cpp,CalMode.h}`、伴随输运调用链、`RMC/tests/var_reduce_wwmesh_*/` 与伴随测试资产 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / 当前 `b7d8a946`；本轮先只读审查，未改 RMC |

---

## 1. 目标与范围（① 立项 · Agent 填）

**要做什么**：审查并以最小可观测量验证 RMC 多群 fixed-source adjoint transport 与**第一版允许的 native `WEIGHTWINDOW` / `WWMESH` track mesh**能否正确组合。先确定完整调用链、WW 发生的粒子状态/事件、伴随语义下应保持的无偏关系及潜在冲突；再给出 C 模式的验伪设计与分类，不提前修复。

**涉及什么**（仓库 / 模块 / 数据）：RMC standard ASCII MGACE、fixed-source neutron adjoint、native cell/track-mesh WW；参考 F02 的有界 A-ready 子域、F03 的外部 response→source 冻结契约、F08 已完成的 native WW 可靠性修复。明确排除 MCNP `WWINP` point mesh、连续能量、完整 photon/耦合粒子、跨节点、Windows、历史场累计、WW 生成算法和生产基准更新。

**怎样算完成**：

1. 静态证据闭合“adjoint 标志 → 粒子输运 → WW 查询/roulette/split → bank/统计”的实际组合链；
2. 写清物理不变量、可观测量与会推翻假设的结果；
3. 完成一项不更新基准的最小 targeted smoke/oracle 设计，并根据真实证据给出 A–F 分类或有界 C；
4. 若发现 E/D，记录最小修复方案和停止条件，**停在第 3 节等用户拍板**，不修改 RMC。

**原始材料**（`logs/` 下有什么，原样保存）：立项时无失败运行材料。已知前序证据在 F02/F03/F08 档案；本任务后续运行日志、输入快照和原始 tally 将原样存入本目录 `logs/`。

> **模式 C 追加 · 物理解释**：
>
> 对带权历史，WW 的 roulette/splitting 仅改变粒子数和单粒子权重，条件期望必须保持：
>
> $$E\left[\sum_{i\in\mathrm{offspring}} w_i\middle|w\right]=w.$$
>
> 在伴随 Monte Carlo 中，输运的是定义于伴随相空间的带权粒子；WW 可用于降低方差，但不能改变已冻结的伴随输运算子、外部 source→source 的 F03 契约或目标响应估计的期望值。第一版要观察的是：开启 native WW 后组合路径是否真实可达、权重/particle bank 是否满足守恒关系、且 paired forward–adjoint 可观测量是否在预定义统计范围内一致。若发生类型/能群/位置错配、bank 属性丢失、权重守恒破坏、确定性崩溃，或统计门槛拒绝，则推翻“可直接组合”假设。

---

## 2. 做法与证据（② 设计 · ④ 实施 · Agent 填）

**设计 / 定位**（E1 静态 + E2 smoke；源码基线 RMC `b7d8a946`）：

### 组合调用链

1. `FIXEDSOURCE/ADJOINT` 置 `CDFixedSource::p_bIsAdjoint=true`（`ReadFixedSourceBlock.cpp:228`）；`CDFixedSource::InitiateAll()` 把该状态传为 `CDAceData::p_bIsAdjoint=true`（`InitiateAll.cpp:130`）。
2. 初始外源在 `SampleNeutronSource.cpp:222` 读取该标志，设 `CDParticleState::p_bIsAdjointParticle=true`；WW 分裂出的 bank 再取出时，`PopParticleOutofStack()` 也依据全局 `p_bIsAdjoint` 重设该标志（`SampleNeutronSource.cpp:304-306`）。因此 neutron WW 子代不会因 bank 缺少独立 boolean 字段而退化成 forward 粒子。
3. `ReadWeightWindow.cpp:500-524` 的 native `WWMESH:N` 设置 `TrackMeshWeightWindow`。`CDFixedSource::RayTracking()` 把该模式传入 `TransportParticleAndDoMeshWeightWindow()`（`RayTracking.cpp:257-260`）；后者进入 `DoTrackMeshWeightWindow()`（`TrackWithWeightWindow.cpp:9-20`）。这条调用链**没有**按 adjoint 标志绕开 native track mesh WW。
4. `DoTrackMeshWeightWindow()` 对每段 mesh track 先查当前粒子类型/能群的 WW，再调用统一 `DoWeightWindows()`，随后才 tally/移动（`DoMeshWeightWindow.cpp:21-58`）。统一原语对中子/光子根据当前 `p_eParticleType` 选择 bank；roulette 保留权重 `w/p`、split 令子代总期望权重为原权重（`WeightWindows.cpp:95-151`）。
5. `pushSplitParticles()` 复制位置、方向、能群、权重、时间及历史信息（`SaveSplitParticles.cpp:20-48`）。`CDFixBank` 存有 `ParticleAttr`，但这一路尚未把 `cParticleState.attr()` 写入 `tempParticle.particleAttr`（`FixedSource.h:28-94`；`SaveSplitParticles.cpp:20-48`）。对当前 F04 冻结的 fixed-source neutron adjoint smoke，伴随标志由第 2 步全局开关恢复，故尚未证明该遗漏改变结果；但它是与 W10 split-attribute 候选相同的**待验证风险**，不能忽略。

### 最小动态 smoke（E2）

使用 `logs/f04-adjoint-native-wwmesh-smoke.inp`：复用 `fixed_source_adjoint` 的 standard ASCII 30-group MGACE、neutron fixed-source adjoint 输入，在单个覆盖几何的 native `WWMESH:N=0.1` + `WWP:N 5 3 5` 下运行。初始 source weight 为 `1.3636364`，高于 WW upper $0.5$，所以会触发 split 分支，而非仅测试“WW 卡被接受”。

```text
command: RMC_DATA_PATH=/home/silver/NucXS_Library/RMC_DATA \
         /tmp/rmc-f08-cell-ww-build/bin/RMC
exit: 0
Warning: particle energy larger than maximum energy group upper bound.
Source Number : 100000.
RMC Calculation Finish.
Tally total: 2.1767E-01, RE: 1.6299E-02
```

原始输入、stdout、`inp.out`、`inp.Tally` 与命令元数据均存入 `logs/`。该证据证明：**当前 native WWMESH + fixed-source neutron adjoint 路径可初始化、运行、产生非零多群 tally 并正常结束**。它不证明无偏性；上述能量 warning 也要求正式 oracle 改用已资格化、无 warning 的 F02 输入/源配置。

**方案选择**：采用用户批准的方案 A。正式 oracle 使用与 F02 已资格化输入相同的 standard ASCII 30-group H2O、fixed-source neutron adjoint、Linux MPI-off serial；固定五个独立 RNG seed `(101, 103, 107, 109, 113)`，每个开/关分支各 200,000 histories，共 10 次 RMC 运行、2,000,000 histories。源能量 `0.2435 MeV` 的可观测非零 tally 为输出 group 16（首轮误取 group 15，均为零导致 `0/0`；已记录为 oracle 映射修正，未混入正式结果）。

WW-on 使用一个覆盖整个球的 native `WWMESH:N=0.1`，配套 `WWP:N 5 3 5`；source weight 为 1，而 upper bound 为 0.5，因而每个源历史在第一个 track mesh 段确定触发 split。WW-off 与 WW-on 的唯一输入差异是这一 `WEIGHTWINDOW` block。采用逐 seed 及逆方差合并 $|z|\le3$ 作为预冻结接受条件。

放弃 PTRAC 作为子代状态的动态证明：RMC neutron fixed-source `TrackHistory()` 只初始化 PTRAC buffer（`TrackHistory.cpp:168-172`），没有在历史完成处调用 `checkEventsAndWrite()`；本轮 `SRC+BNK` probe 退出 0 但 `inp.PTRAC` 为 0 B。因此空 PTRAC 不能解释为“没有 split”。子代伴随状态的证据仍是 E1：`PopParticleOutofStack()` 在 `p_bIsAdjoint` 时显式设置 `p_bIsAdjointParticle=true`（`SampleNeutronSource.cpp:304-306`）；动态 WW-on 的 RE 从约 $0.00285$ 降至约 $0.00188$，也与 source 处确定 split 的预期一致，但不把 RE 改善单独当作状态证明。

**实施要点**（改了什么；改动快照见 `changes.diff`，无代码改动写“无”）：未修改 `RMC/`、基准、reference 或模型。新增本任务局部 `run_paired_oracle.py`、PTRAC probe 输入及原始 paired run 目录 `runs/`；`probe_split_adjoint_state.py` 仅是未执行的局部变异测试草案，**未运行且未修改 RMC**，不作为证据。

**验证输出**（E3，正式 paired oracle；完整原始输入/stdout/stderr/`inp.Tally` 位于 `runs/`，汇总在 `logs/2026-09-20_paired-oracle-results.{json,csv}`）：

```text
population per branch/run = 200000
seeds = 101, 103, 107, 109, 113
response tally = cell 1, group 16

seed   WW off ± sigma          WW on ± sigma           z(on-off)
101    1.4419 ± 0.0028388       1.4450 ± 0.0018812       +0.9103
103    1.4420 ± 0.0028285       1.4483 ± 0.0018854       +1.8533
107    1.4485 ± 0.0028486       1.4467 ± 0.0018810       -0.5273
109    1.4499 ± 0.0028527       1.4452 ± 0.0018790       -1.3759
113    1.4482 ± 0.0028540       1.4473 ± 0.0018819       -0.2633

inverse-variance aggregate:
WW off = 1.4460788 ± 0.0012721
WW on  = 1.4464977 ± 0.0008415
z = +0.27465
criterion: all per-seed and aggregate |z| <= 3 → PASS
run count = 10; each exit 0; each Source Number = 200000
```

该结果支持当前冻结子域内的无偏假设：在观测的不确定度下，WW-on 与 WW-off 估计一致，同时 WW-on 的统计误差更小。最小 PTRAC probe（1000 histories）也正常结束，但输出文件为空，见上方限制说明。

**未覆盖到的验证**（如实写）：`ParticleAttr` 的动态 end-to-end probe；多 cell/multi-mesh、多个 source/response 群、MPI/OpenMP、photon/耦合粒子、electron、MCNP point mesh、continuous energy、圆柱网格、反射边界和跨节点。

---

## 3. 决策记录（③ · **人拍板**）

- **决定**（采纳什么方案）：用户于 2026-09-20 指示“请继续完成后续工作”，批准按方案 A 执行：在已冻结的首版范围内，开展 native `WWMESH` 开/关 paired fixed-source neutron-adjoint oracle 与 split bank 观测；不以仅 smoke 成功作为通过依据。
- **决定人 / 日期**：用户 / 2026-09-20
- **约束**：本阶段只读、可新建任务局部测试输入/脚本和保存原始输出；不改 `RMC/`、不更新 baseline/reference/model，不改 F03 冻结的外部 response→source 契约；MPI/OpenMP 扩展仅在方案 A 首轮结果通过后再单独决定。

**变更卡（B/C 模式，各一行）**：
| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| native WW 与 fixed-source adjoint 的组合可能保持表面可运行却改变伴随 tally 期望，或 WW split 子代丢失伴随状态/属性 | 首轮只新增 F04 局部 oracle 输入、运行/分析脚本与日志；不改 RMC、基准、F02/F03 契约、WW 生成算法和 `WWINP` point mesh | 预冻结 seeds 的 WW off/on 差异与联合不确定度兼容；确认 split 被触发且子代仍为 adjoint；任一失败立即停止并归为 D/E，不以加大 histories 掩盖 | 删除任务局部输入/脚本即可；RMC 无改动，无需代码回滚 |

> **模式 C 追加 · 人类理解确认**：用户在已看到“组合路径存在但尚未证明无偏”的说明后，指示继续完成后续工作；据此确认首轮范围、方案 A 的 paired oracle 和“统计不兼容或子代状态/属性不保留即停止”的验伪规则。`WWINP` point mesh、photon/电子、MPI/OpenMP 继续排除本轮。

> 未拍板前，Agent 不得改动 `../RMC` 下的任何文件。



---

## 4. 结论与边界（⑤ 归档）

- **结论**：**F04 = C — Verify（冻结的首版子域）**。RMC 已有 fixed-source neutron adjoint + native `WWMESH` track-mesh WW 的实际组合路径；E1 证明伴随标志不会绕开 WW，且 split bank 出队时会恢复伴随标志；E2 smoke 与 E3 五独立种子 paired WW off/on oracle 均正常。正式观测中，所有逐 seed 与合并差异均满足 $|z|\le3$（合并 $z=0.27465$），没有观察到 native WW 改变该伴随 tally 的期望值；WW-on 的 RE 降低。
- **不能推出什么**（边界）：这不是“所有伴随+WW 组合 A-ready”的证明；仅覆盖 Linux、MPI-off、standard ASCII 30-group H2O、fixed-source neutron adjoint、单 cell/单覆盖 Cartesian mesh、source group 对应的输出 group 16。PTRAC 在 neutron fixed-source 路径不落盘，故没有动态逐子代属性证据；`ParticleAttr` 未被 split helper 显式复制的风险仍归 W10，未在本任务裁定为当前物理 defect。不得外推到 point mesh、CE、photon/electron、MPI/OpenMP、圆柱/多 mesh、反射/跨节点或 F03 以外的 source→response 契约。
- **遗留 / 下一步**：若第一版实际案例使用当前冻结范围，F04 组合可作为有界 C 复用；需要扩展粒子/并行/mesh 或把 C 提升为 A 时另立任务。`ParticleAttr` 的 split-bank 保存语义与 `MCNPWeightWindow` 解析顺序加固保持 F08/W10 后续项。
- **提交状态**（分支 / commit / 谁 push）：RMC 无改动、无 commit；本任务仅有根工作区档案/局部 oracle 资产，是否提交由用户决定。

> **模式 C 追加 · 结果解释**：统计通过说明当前检验未发现 WW 对冻结伴随 observable 的系统偏移，且较小 RE 符合分裂增加有效历史数的预期；它不证明任意 response、任意核数据和任意并行环境的无偏性。若将来观测到 $|z|>3$、错误群/状态或崩溃，物理含义是当前组合不能被视作纯方差变换，应停止使用并回到根因/修复审查。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-20 20:49 | 立项 |
| 2026-09-20 | 读取 Stage 1 F04 需求、Stage 2 协议、F02 有界 A、F03 冻结子域和 F08 修复档案；用户指定 C 模式。 |
| 2026-09-20 | E1 定位：伴随标志在 source 与 WW split bank 重取时恢复；native `WWMESH` track path 不按 adjoint 绕过，统一 WW roulette/split 原语不区分伴随状态。记录 `ParticleAttr` 未被 neutron/photon WW split bank 写入的相邻风险。 |
| 2026-09-20 | E2 最小 smoke：标准 30-group fixed-source neutron adjoint + native `WWMESH:N`，100,000 histories exit 0、非零多群 tally；发现 source energy warning，正式 oracle 必须换用无 warning 的已资格化配置。原始输出归档至 `logs/`。 |
| 2026-09-20 | 完成 C 模式问题定式、验伪设计和变更卡；停在第 3 节等待人类理解确认与方案 A/B 拍板。 |

> 关键命令、误判与修正、未决分歧都写在这里；人机讨论较深时把要点并入本表，**不再单独建会话纪要文件**。原始聊天转储不要入仓（可能含凭据）。

**证据等级（可选）**：物理/审查结论可标 E0–E4；工程、文档、治理任务可省略。
