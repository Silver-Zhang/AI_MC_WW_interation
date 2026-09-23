# f04b-deep-penetration-ww-benchmark

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-22 |
| 状态 | 已完成 |
| 任务类型 | 算法实验 / 物理验证 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | Claude |
| 关联知识库条目 | F04 |
| 涉及文件 | 仅在本档案创建输入与运行产物；只读 `RMC/` 源码；不修改 RMC |
| RMC 基线 | `b7d8a946417eea091a30c09c233054aa077570ee` |
| 分支 / 提交 | 根工作区 `main`；随本档提交（2026-09-23）；RMC 未修改（`b7d8a946`） |

---

## 1. 目标与范围

**要做什么**：以真实 100 cm 水屏蔽 slab 深穿透问题，独立运行固定源多群中子伴随计算的 WW-off 与 native track-mesh WW-on 配对实验，检验响应无偏性、FOM 与 WW 实际激活。

**涉及什么**：RMC 当前源码的独立 MPI-off/OpenMP-off 构建；从 `RMC/tests/var_reduce_wwmesh_n/inp` 借用其 100 cm 水屏蔽几何尺度和 native `WWMESH:N` 形式；从 `RMC/tests/fixed_source_adjoint/inp` 借用 MGACE + fixed-source adjoint 输入形式。运行输入、命令、原始标准输出、tally/PTRAC 文件和解析脚本只存本任务目录。

**不涉及什么**：不修改 `RMC/` 任何源码、测试、基准或参考结果；不更新核数据库；不评价此前任何审查结论；不外推至连续能量、光子、耦合输运、point mesh 或并行路径。

**怎样算完成**：

1. 以同一几何、材料、伴随源、tally、history 数和一组预声明 seeds，完成 WW-off 与 WW-on；
2. 对合并响应计算 \(z=(R_{WW}-R_A)/\sqrt{\sigma_{WW}^2+\sigma_A^2}\)；
3. 从真实输出记录 runtime、RE、FOM、FOM ratio，并从 PTRAC/bank 证据确认 split/roulette/weight 行为；
4. 在本档案写出 `F04-B-deep-penetration-WW-benchmark.md`，并明确不足或未覆盖项。

**原始材料**：`logs/` 将保存 RMC revision/build 配置、每运行 stdout/stderr、输入 SHA256、Tally/PTRAC 原件和汇总脚本输出；不存编译目录或核数据副本。

> **模式 C · 物理解释**：物理正问题为源（x=0 侧）→100 cm 水屏蔽→探测器（x=100 侧）。对应的伴随计算从响应端注入伴随中子、反向穿越水层，并在正源端的小 cell tally 响应。若 WW 正确且激活，WW-on 与 WW-off 的均值应统计相容，而在相同 runtime 定义下可降低 RE 或提升 FOM。若 \(|z|\ge3\)，或 split/roulette 没有实际发生，则不能直接归因为源码偏差，须区分 window 标度、穿透深度、能群坐标和统计功效。

## 2. 做法与证据

**设计 / 定位**：

- 候选几何 `RMC/tests/var_reduce_wwmesh_n/inp`：10 个 x 向各 10 cm 的水段，x=0–100 cm，源/mesh tally形式均为固定源中子；是现有自动测试中最接近 source–shield–detector 的 100 cm 水屏蔽基线。
- 多群伴随输入语法依据 `RMC/tests/fixed_source_adjoint/inp`：`MGACE erggrp=30 12` 与 `FIXEDSOURCE / ADJOINT ADJOINTCALCULATION=1`。
- native mesh WW 的运行时作用位置和 energy lookup 仅以当前源码为准；本实验将固定一个**显式群坐标** `WWE:N`/`WWMESH:N` 合约，并在报告中同时打印物理能量、映射群号与输入 boundaries，避免将接口含义预设为物理 MeV。
- 当前 `RMC/` checkout 无同 revision 可执行文件。已有外部二进制的版本分别为 `e6e0907f` 与 `2831feff`，均不匹配本任务 revision，故不使用；将从当前 checkout 做独立 out-of-tree serial build。

**方案选择**：

- **几何**：x=0–100 cm、横向 \(100\times100\) cm 水 slab；物理正源端 x=0–10 cm 为 tally region，物理探测端 x=90–100 cm 为伴随 source region；其余为连续水屏蔽。
- **伴随 source**：x=97.5 cm、2 MeV neutron、全局 fixed-source adjoint；为使穿透方向可诊断，优先采用沿 \(-x\) 的 pencil/cone source。若 RMC source parser 不支持该严格定向形式，将记录并使用经 parser 验证的替代定向分布，而不是静默转为各向同性。
- **响应**：x=0–10 cm water cell 的 neutron track-length flux total；深穿透指标由先导 run 的 analog RE 和零分数决定。
- **WW**：仅 native track mesh，10 个空间 bin；WW-off 不含 `WEIGHTWINDOW` block，WW-on 使用同一 mesh 和预定义的单调窗口。窗口按伴随行进方向设置，使低 importance 端权窗较低、触发 split；参数固定为 `WWP:N 5 3 5`。所有其他输入相同。
- **统计设计**：先导 run 用 1 seed / 100k histories 检查非零响应和 WW event；正式 run 至少 5 个独立 seed，二案例逐 seed 相同 history 数，统计合并采用 batch/sample means；各 run 的 wall time 以 `/usr/bin/time -p` 记录。history 数由先导结果决定，但不得修改两个 case 间的任一物理输入。
- **停止条件**：若 source/binary identity 无法闭合、response 在合理 pilot 成本下全零、WW 无 split/roulette evidence、或运行故障，则如实判为 Inconclusive 并停止，不修改源码“修复”。

**实施要点**：已在本档案 `cases/` 建立可复现输入生成/运行/分析脚本；从 current checkout 完成 out-of-tree MPI-off/OpenMP-off build；RMC 源码、测试、基准和参考结果均未修改。生成的 build/run 目录在归档前清理；原始 stdout/stderr/tally、PTRAC、hash manifest 与脚本保留。无 `changes.diff`，因为 RMC 无代码改动。

**验证输出**：正式结果见 `F04-B-deep-penetration-WW-benchmark.md` §3–§7 与 `logs/formal-analysis.md`。五 seed × WW off/on × 1,000,000 histories：合并 $z=0.29571$、$FOM_{WW}/FOM_A=9.24161$；PTRAC activation pilot 记录 6,009 split 和 31,449 roulette/cutoff events。

**未覆盖到的验证**：MPI/OpenMP、continuous-energy、photon/耦合粒子、delayed-neutron adjoint、point mesh、动态 WW 生成、MLVR 生成 window、其他几何/材料、event-by-event bank-weight distribution、独立核数据实现均未覆盖。

## 3. 决策记录

- **决定**：批准按 §2 的 100 cm 水屏蔽设计实施：current checkout 的独立 serial build、100k histories/seed pilot；若响应非零且 WW 激活，则升至 1M histories/seed、至少五个独立 seed 的正式配对运行。
- **决定人 / 日期**：用户 / 2026-09-22。
- **约束**：不修改 RMC 源码/测试/基准/参考结果；输出只写任务档案；采用 current checkout revision 的独立 serial build。

**变更卡**：
| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| 伴随+WW 可能偏差或无效 | 仅新建档案内 benchmark inputs/runs/scripts；不改 `RMC/` | 五 seed paired comparison；\(|z|<3\) 为无偏门槛；记录 FOM 和 event evidence；响应全零、WW不激活或 source/binary不闭合则 Inconclusive | 删除本档案可再生产物；RMC 不需回滚 |

> **模式 C · 人类理解确认**：用户批准的范围仅为“固定输入的 native track-mesh WW 在该 MG adjoint slab 上是否无偏且有效”；不因此证明普遍的伴随输运、MLVR 生成权窗或其他几何/并行路径。

## 4. 结论与边界

- **结论**：**WW unbiased and effective**（限所测范围）。五 seed × 1M paired：合并 $|z|=0.29571<3$ 通过预声明无偏判据；WW 确有激活（PTRAC pilot 记录 6,009 次 split、31,449 次 roulette/cutoff）；合并 FOM 比 9.24161（WW-on 有利），合并 RE 降为约 $1/2.42$。9.24× 是所选窗口/机器的实测效率，不是最优窗口结论。
- **不能推出什么**（边界）：仅支持当前 RMC 修订 `b7d8a946`、MPI-off/OpenMP-off serial、30 群 MGACE、100 cm 水板、单一 2 MeV 伴随点源、源端 track-length flux 计数与 native 单区间 track-mesh WW；不覆盖 continuous-energy、photon/耦合输运、delayed-neutron adjoint、point mesh、WW 生成算法、其他几何/材料、能量依赖 WW、MPI/OpenMP 与 MLVR 生成窗口。**本实验刻意不使用 `WWE:N` 物理能量边界**（native 路径为 default 单区间），不能回答物理能量型 WW 输入在其他配置下是否被一致映射到 MG 群坐标；2 MeV→顶群 source 警告亦为已声明边界。
- **遗留 / 下一步**：`WWE:N` 坐标契约问题由静态审查（`20260922_03`）与 STATUS 待拍板 #6 继续跟踪；如需逐事件权重级诊断需另加 instrument。
- **提交状态**：RMC 无改动（`b7d8a946`）；报告、logs 摘要与 `cases/` 复现脚本/输入随本档入库；大体积 PTRAC 原件（`logs/pilot-ww-ptrac.txt`，7.4 MB）按归档体积规范不入库、仅保留本地。

> **模式 C · 结果解释**：$|z|<3$ 表明在统计功效范围内未观察到 WW 导致的响应偏移；9.24× FOM 是所选 water-slab/window 组合的实际效率提升。该结果不能排除较小偏差，也不能证明其它 input contract 或扩展物理路径。

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-22 | 立项，模式 C。 |
| 2026-09-22 | 仅读取当前 RMC 源码/test inputs，选择 100 cm water shielding 候选；确认本 checkout 无同 revision executable，外部二进制版本不匹配，计划独立 serial build。 |
| 2026-09-22 | 完成设计，等待用户按 §3 拍板；尚未创建 benchmark input、编译或运行。 |
| 2026-09-22 | 用户批准：serial build；100k histories/seed pilot，满足非零响应与 WW 激活条件后升至 1M histories/seed，至少五 seeds。 |
| 2026-09-22 | MPI-off/OpenMP-off current-revision build 成功；SHA-256 记录于 `logs/reproducibility-manifest.md`。 |
| 2026-09-22 | 100k pilot：WW off/on 均非零；WW-on RE=5.2142E-02（off=1.2350E-01）。首次 `WWE:N 0` 因 native parser 将其解释为两 energy bins，触发形状校验被拒绝；只改任务输入为无 `WWE:N` 的单 default interval 后成功，未修改 RMC。 |
| 2026-09-22 | 100k PTRAC activation pilot：记录 6,009 splitting 与 31,449 roulette/cutoff events；原件在 `logs/pilot-ww-ptrac.txt`。 |
| 2026-09-22 | 正式 5 seed × 1M off/on 完成；$z=0.29571$，FOM ratio=9.24161；报告已归档。 |

**证据等级**：当前 E1（测试输入与构建环境定位）；动态运行后按实际证据更新。
