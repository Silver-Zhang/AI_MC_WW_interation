# f08-cell-ww-core-repair

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-19 |
| 状态 | 待决策 |
| 任务类型 | 缺陷修复 / 物理正确性验证 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | W10 |
| 涉及文件 | `RMC/src/ReadWeightWindow.cpp`、`RMC/src/WeightWindows.cpp`、`RMC/src/DoWeightWindow.cpp`、`RMC/src/RayTracking.cpp`；不处理 mesh/MPI/adjoint+WW |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `b26a81a26f6d43aea405b1c744f0c4cdf4fd8bdf`；尚未修改 |

---

## 1. 目标与范围（① 立项 · Agent 填）

**要做什么**：先在 native `WEIGHTWINDOW` 的 cell neutron WW 子域修复并验证已确认的 `WWP:N/P/E` 参数生命周期问题：`WUPN`、`WSURVN`、`MXSPLN` 必须按粒子类型保存，且 cell/mesh 构造与 `DoWeightWindows()` 必须使用同一套参数。同步厘清 cell WWE 的首能群边界：确认常规 $0<E\le E_1$ 已映射到第一个权窗 bin；仅将 $E=0$ 的 `nErg-1` 访问作为待判定的防护问题，而不预设为已确认的常规能群映射缺陷。
**涉及什么**（仓库 / 模块 / 数据）：`WEIGHTWINDOW`（非 `MCNPWEIGHTWINDOW`）输入，cell-based fixed-source neutron WW；输入读取、cell 权窗构造、穿面后 WW 调用、通用 roulette/splitting 执行。暂不改变 mesh WW、MPI shared mesh、split bank `ParticleAttr`、photon/electron 路径、adjoint+WW 或 benchmark/reference。
**怎样算完成**：在用户批准后，以最小改动使每种粒子类型的 WWP 参数独立且可达；完成针对性输入/粒子级验证，证明 $E[w_{out}]=w_{in}$（roulette）和 $E[\sum_iw_i]=w_{in}$（splitting），并确认正确 WWP 参数被使用。`E=0` 仅在确认它是可达且需要防护的状态后才改动。生成 RMC `changes.diff`。不以普通 smoke 单独宣称 WW 整体放行。
**原始材料**（`logs/` 下有什么，原样保存）：F08 静态审计档案、`ReadWeightWindow.cpp`/`DoWeightWindow.cpp`/`WeightWindows.cpp`/`RayTracking.cpp` 源码定位，以及后续最小输入、构建和运行原始输出。

> **模式 C 追加 · 物理解释**：cell WW 在粒子穿过几何 cell 边界后，按目标 cell 与能群选择 $w_L,w_S,w_U$。roulette 必须满足 $P_{survive}w_T=w_{in}$，其中当前代码 $w_T=\min(MXSPLN\,w_L,w_S)$；splitting 必须满足 $E[\sum_iw_i]=w_{in}$。因此，跨粒子类型的 WWP 串扰会让 $w_S,w_U,MXSPLN$ 不再代表输入所定义的粒子统计策略。对能量边界，输入约定是 `bound[0]=0`、第一个 lower bound 对应 $[0,E_1]$；当前循环对常规 $0<E\le E_1$ 得到 `nErg=1` 并访问 bin 0。$E=0$ 时才会访问 bin `-1`，其可达性和是否需要防护须由最小输入确认。

---

## 2. 做法与证据（② 设计 · ④ 实施 · Agent 填）

**设计 / 定位**（读了什么、查到什么；关键证据给 `文件:行号` 或数据位置）：

1. 原生输入路径在 `ReadInputBlocks.cpp` 进入 `ReadWeightWindowBlock()`；`WWE:N` 为每个 cell 先写入能量下界 0，再追加用户上界，`WWN:N` 按能群×cell 写入 lower bound。用户文档定义第一个 bin 为 $[0,E_1]$。
2. `ReadWeightWindow.cpp` 以一个公共 `WUPN/WSURVN/MXSPLN` 局部三元组读取全部 `WWP:N/P/E`，随后用最终值构造 cell upper/survival；但 `DoWeightWindows()` 又从 `p_vWeightWindowPara[particleType][MXSPLN]` 读取执行上限。原生路径没有把已读取参数按粒子类型同步到该数组，导致构造和执行状态不一致。
3. `RayTracking.cpp` 在 neutron 穿面并定位新 cell 后调用 `DoWeightWindow()`；该函数对多能群从 boundary index 0 开始查找 `energy <= bound[nErg]`，之后访问 `[nErg-1]`。因 `bound[0]=0`，常规 $0<E\le E_1$ 会命中 `nErg=1` 并读取第一个权窗 bin，符合文档的 $[0,E_1]$ 定义。$E=0$、不合法能量、边界表异常及其可达性仍需用最小输入精确确认；photon/electron 有同构代码但不在本任务修复范围。
4. `DoWeightWindows()` 的 roulette 使用 $w_T=\min(MXSPLN\,w_L,w_S)$，splitting 在未触发上限时按 $w/w_S$ 随机取整生成后代；故 WWP 参数不仅影响性能，还决定实际权重变换。

**方案选择**（选了什么、放弃了什么、为什么）：拟采用最小范围方案：只为 native `WEIGHTWINDOW` 的三种粒子类型分别保存 `WUPN/WSURVN/MXSPLN`，统一 cell/mesh 构造和 `DoWeightWindows()` 的读取来源；只修正 neutron cell 的首能群定位并以文档规定的 $[0,E_1]$ 约定验证。暂不把 cell 任务扩展到 mesh/MPI/adjoint，也不因代码相似性未经复现修改 photon/electron。
**实施要点**（改了什么；改动快照见 `changes.diff`，无代码改动写“无”）：尚未实施，等待用户对物理问题定式、因果链及验伪条件确认。
**验证输出**（贴真实命令与输出；物理结论从严，工程/文档从简）：

```text
尚未运行；未获实施拍板。
```

**未覆盖到的验证**（如实写；没有就写“无”）：mesh WW、MPI shared mesh、photon/electron cell WW、split bank 属性完整性、adjoint+WW、WWINP，以及修复后完整响应/FOM 评估均不在本任务范围。

---

## 3. 决策记录（③ · **人拍板**）

- **决定**（采纳什么方案）：待物理讨论与用户拍板。当前已确认的实施候选是：保持输入格式不变，将 native `WWP:N/P/E` 写入既有的每粒子类型参数数组；cell/mesh 构造和 `DoWeightWindows()` 都从该数组读取。`E=0` 首边界仅在确认它是可达或输入可构造的状态后，作为独立防护修复纳入。
- **决定人 / 日期**：待用户确认 / 2026-09-19
- **约束**（能不能动接口 / 基准 / 算力预算…）：不改输入格式、MCNP 路径、mesh/MPI/adjoint 路径、reference 或 benchmark；未经本节记录的用户拍板，不修改 `RMC/`。

**变更卡（B/C 模式，各一行）**：
| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| WWP 读取、构造和执行使用不同参数源，导致输入定义的统计策略失真 | 仅 native `WEIGHTWINDOW` 的 WWP 参数保存和 cell neutron 最小验证；不改输入格式、MCNP、mesh/MPI/adjoint | custom `MXSPLN` 与多粒子不同 WWP 必须到达预期执行点；roulette/splitting 权重期望满足关系；若无法闭合参数来源则停止扩大修复 | 还原本任务 RMC diff |

> **模式 C 追加 · 人类理解确认**：待讨论。当前共同已厘清：对常规 $0<E\le E_1$，cell 查找读取 bin 0；首边界问题应缩小为 $E=0$/异常边界的可达性与防护，而不能再表述为常规能群错位。待确认：用户定义的 WWP 是否应对每个粒子类型独立生效，以及是否接受“先修参数生命周期、仅对可达的零能量状态追加防护”的物理范围。

> 未拍板前，Agent 不得改动 `../RMC` 下的任何文件。



---

## 4. 结论与边界（⑤ 归档）

- **结论**：
- **不能推出什么**（边界）：
- **遗留 / 下一步**：
- **提交状态**（分支 / commit / 谁 push）：

> **模式 C 追加 · 结果解释**：结果支持或否定了哪个假设；通过/失败在物理上说明什么；不可外推的边界在哪。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-19 18:30 | 立项 |

> 关键命令、误判与修正、未决分歧都写在这里；人机讨论较深时把要点并入本表，**不再单独建会话纪要文件**。原始聊天转储不要入仓（可能含凭据）。

**证据等级（可选）**：物理/审查结论可标 E0–E4；工程、文档、治理任务可省略。
