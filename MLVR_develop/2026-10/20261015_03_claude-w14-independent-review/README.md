# W14 — RMC 多群源速度初始化独立审核归档

| 项 | 内容 |
|---|---|
| 立项/归档日期 | 2026-10-15 |
| 状态 | 已完成（**CONFIRMED · P1 · E3，未修复**） |
| 任务类型 | 独立源码审核与限定动态验证 |
| 任务模式 | C — 深度物理研究与学习 |
| 审核人 | Claude（独立审核；形成判断前未阅读 Codex 本轮报告） |
| RMC 基线 | `Neural_Network_WW_Iteration` / `4810694b7a99dfc3ad7d27f7d443814f511f4829`；工作树 clean |
| 主要报告 | [Independent_W14_RMC_MG_Source_Velocity_Review.md](Independent_W14_RMC_MG_Source_Velocity_Review.md) |
| 测试证据 | 本地隔离目录 `/tmp/w14-claude-review/`；不入库，不与 Codex 测试共享 |

## 1. 目标与范围

独立判断普通 RMC 多群中子外源是否在源能量仍为物理 MeV 时，将其误作为内部群号传给 `GetNeuVelMg()`；检查是否越界、实际首次使用、Forward/Adjoint 共用范围及稳态结果推论边界；限定回顾 F02/F03/F04 的显式验收范围。

本轮只审核和验证，不实施修复、不改源代码/reference/核数据库/冻结设计，不进入 F11 Stage 3。

## 2. 做法与证据

直接阅读冻结 RMC HEAD 的源采样、MG映射、速度公式、history、移动、tally、bank及相关代码；并检查指定历史任务档案。动态 probe 使用隔离 `/tmp/w14-claude-review/`，从已有 Stage2 archived binary 进行 GDB 观察，并对当前冻结 RMC 源码副本单独配置 ASan/UBSan/float-cast-overflow binary。

| 验证 | 实际结果 | 限制 |
|---|---|---|
| 高能源 `16 MeV`，Forward/Adjoint GDB | 两模式 sample 与首次飞行速度均为 `4.9053375868571196 cm/shake`；映射 group 1，真实中心 16 MeV，正确速度 `54.6310903661`。 | ordinary binary banner 是 `330f091e`；相关源文件逐文件与 `4810694b` 相同，但不声称整 binary provenance 已匹配冻结 HEAD。 |
| 低能源 `0.2435 MeV`，Forward/Adjoint GDB | 两模式源采样速度均为 0；Adjoint 映射到 group 15 后首飞仍 v=0。Forward/Adjoint 首飞均观测到非零飞行距离。 | 未将 GDB 试图检查 post-flight 成员的输出作为证据。 |
| 低能源 `0.2435 MeV`，新建 sanitizer binary | ASan: `heap-buffer-overflow`, READ size 8, 0 bytes after 240-byte region；栈为 `GetNeuVelMg(GlobeFun.h:544) ← SampleParticle.cpp:82 ← SampleSourceParticle ← SampleFixSource`。 | sanitizer 路径还报告既有 Universe bool/enum 与 StrideRNG signed overflow UBSan 诊断；未将它们归于 W14。 |
| `0.6615 MeV` in-range sanitizer control | 退出0，无 ASan OOB；但该合法索引输入仍可能选错群中心速度。 | 不构成速度正确性证据。 |
| 普通 RMC run | 低能 adjoint/forward 小运行可退出0且有非零 collision count。 | 退出0不能排除 OOB/错误速度；不等同于物理正确。 |

关键动态记录、普通/插桩 binary SHA、输入 SHA、compiler/CMake 版本见主报告第2/7节；全部测试用例保存在 `/tmp/w14-claude-review/`。

**历史范围核对**：F02 将 source semantics 排除到 F03 处理；其数学核/稳态 response gates 未检查速度或时间。F03 检查过 `SampleParticle` 及后续群定位，因此速度表示问题静态上可见；但 acceptance gates 检查最终 group、source support/weight 和无时间项稳态 response，不检查速度/首飞/ASan。F04 检查 adjoint+native WW 及配对稳态 tally，不含 velocity oracle。不能因此否定原有有限范围的 F02/F03/F04 结果。

## 3. 决策记录

原请求授权独立验证与报告，明确禁止修复和修改共享 STATUS/INDEX/档案。本轮审核完成后，用户另行明确要求“需要进行归档记录”；经确认正式工作区归档并同步共享入口。该后续归档授权不包含生产修复、commit/push 或 Stage 3。

**变更卡**：只新增本 W14 独立审核报告和本 README，并同步 INDEX/STATUS/06 风险状态指针；不改 Codex 原始报告/证据、RMC、KB04、核数据库或 reference。回滚仅撤销本轮文件增量；不得覆盖其它既有修改。

## 4. 结论与边界

**CONFIRMED · P1 · E3（限定路径）**：普通 standard MGACE neutron fixed-source source sampler 在源能量为 MeV 时，用 `GetNeuVelMg` 按 group number 解释该值。对 `G=30, E=0.2435`，`int(E+0.5)=0`，`k=30`，而 vector 合法下标为 `0..29`；本次 ASan 真实确认越界。对其它 E，合法下标也可能取错群中心，Forward 与 Adjoint 均受影响，且初速未在首次自由飞行前重算。

源速度直接进入 `FlyByLength` 的时间推进 `t += L/v`；时间 bin、velocity estimator 等也直接依赖它。首段空间长度和 MG 截面在所查普通路径不直接依赖速度，所以本次**未证明普通稳态通量/反应率或既有 F02/F03/F04 paired response 必然错误**。这是源初态/时间/内存安全的已确认缺陷，不是对全部稳态物理结果的自动否定。

固定源 bank 出队还存在静态确认的反向表示风险：split bank 保存内部 group，`PopParticleOutofStack()` 却用 CE `GetNeuVel()` 把群号作为 MeV；本轮未动态验证 bank descendants。主报告详列证据等级、历史覆盖及其它未验证范围。

**最小通用修复方向**：在 `SampleParticle()` 的通用 MG neutron 初始化处根据物理 MeV 定位内部群/中心并计算速度，保持后续现有群映射合同；bank 恢复处按已存内部群号取得 MG 中心速度。不能仅在 Stage 3 TARGET 专用源层绕行。该修复须另行授权，本次不实施。建议将其作为 F11 Stage 3 相关生产实施前的 P1 blocker；既有稳态验收不需全矩阵重跑，但时间/速度相关结论与低群源首次状态须专项复核。

## 5. 过程记录

| 时间 | 操作 |
|---|---|
| 2026-10-15 | 直接按冻结 RMC 源码追踪物理MeV→MG group、源速度初始化、首次移动、时间/score和 bank 路径；未读 Codex W14 报告。 |
| 2026-10-15 | 在 `/tmp/w14-claude-review/` 执行限定 GDB probes 与独立 sanitizer build；低能 OOB 复现，高能 Forward/Adjoint 错速确认。 |
| 2026-10-15 | 独立回顾 F02/F03/F04 历史审核的目标、观测量及边界；完成技术报告。 |
| 2026-10-15 | 用户要求正式归档并授权同步；新增报告、README、INDEX/STATUS/知识库指针。 |

保护确认：没有修改 RMC、Codex W14 档案/证据、KB04、核数据、reference 或 Stage3设计；没有 commit/push/reset/checkout/clean；RMC仍为 `4810694b` 且 clean。未实施修复，未启动 Stage 3。
