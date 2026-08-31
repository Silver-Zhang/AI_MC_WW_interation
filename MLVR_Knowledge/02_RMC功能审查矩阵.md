# RMC功能审查矩阵

## 目的

记录双向迭代WW基础框架所需功能与RMC现有能力之间的对应关系。

Stage 2 依据本矩阵逐项进行只读审查。审查不直接修复代码。统一方法见 `03_RMC功能审查规范.md`。

## 分类标准

- A — Ready：已有且满足第一版框架需求，可直接复用。
- B — Extend：主体能力已有，但需要有限扩展。
- C — Verify：功能或实现机制存在，但关键正确性/适用范围仍需验证。
- D — Integration issue：单项功能存在，但组合使用存在问题。
- E — Defect：已有实现存在明确错误。
- F — Missing：所需能力不存在。

## 当前状态

| ID | 功能需求 | 当前状态 | 审查重点 | 任务 |
|---|---|---|---|---|
| F01 | Forward fixed-source MC | 待审查 | Bootstrap与正式Forward基础能力 | — |
| F02-A | 多群Adjoint transport功能存在性 | 已完成 | 入口、调用链、实际行为 | `20260824_04_f02-mg-adjoint-transport-audit` |
| F02-B | 多群Adjoint物理正确性审查 | A — Ready（有界） | MPI-off serial 与已验证本机 MPI/MPI+OpenMP 配置；raw formal、统计门禁、CTest 与 checksum 已绑定至冻结快照 | `20260828_01_f02-mpi-off-serial-provenance`；`20260830_01`、`20260831_01~03` |
| F03 | Adjoint source定义 | 已立项（待设计） | 目标响应驱动伴随源；区分通用外源执行与响应到源构造 | `20260825_09_f03-adjoint-source-definition-audit` |
| F04 | Adjoint + WW兼容性 | 待审查 | 组合功能正确性 | — |
| F05 | Forward spatial-energy field tally | 待审查 | 输出空间×能群场 | — |
| F06 | Adjoint spatial-energy field tally | 待审查 | 输出伴随空间×能群场 | — |
| F07 | Field统计与RE输出 | 待审查 | 统计误差定义与输出 | — |
| F08 | WW输入与应用链路 | 待审查 | splitting/roulette接口 | — |
| F09 | Response统计与FOM | 待审查 | 响应、RE、时间统计 | — |
| F10 | Field Reconstruction数据边界 | 待审查 | RMC与外部重构接口 | — |
| F11 | 固定次数双向迭代调度基础 | 待审查 | 多阶段运行组织 | — |
| F12 | Bootstrap直接模拟链路 | 待审查 | Analog Forward→field+RE→WW_A(1) | — |

## F02当前结论

F02-A 已确认默认标准 ACE 多群路径存在固定源伴随输运链。

F02-B 源码层独立复核确认的 W5/W6/W7/W9 均已完成独立修复和针对性验证。当前冻结作用域为 Linux x86_64、`ais=OFF`、standard ASCII MGACE、fixed-source neutron adjoint，以及两类已验证执行配置：MPI-off serial build（OpenMP off）与本机 Open MPI 4.1.6 的 MPI `2×1/4×1`、MPI+OpenMP `2×2/2×4`。该范围为 **A — Ready（有界）**：source—binary provenance、formal raw evidence、响应级验证、条件角 aggregate 主检验、CTest 与 checksum 均已闭合。

1. W5 修复前，局部密度比例 $r\ne1$ 时散射与裂变权重相对正确值多出 $1/r$；当前已改用局部总原子密度并通过 V2 密度不变性验证。
2. W6 修复前在 `NNUBAR>1` 时混用 total/prompt nubar；当前运行时前驱群抽样已统一使用 total locator。部署双表数据的逐群核与概率差为 0，动态输入完成 10,000 个源历史和 2,487 条 bank 后继。
3. W9 修复前，负单变量 `NLEG=1,x<0` 的 neutron、photon 与 photon→neutron 次级伴随公式误用 `(1-x)`；现已改为 `(1+x)`。neutron 三 seed 共 1438 对逐项一致；新增两条 photon 路径各 900 样本零越界且理论矩通过，普通 photon 900 对前/伴随逐项一致；既有 CTest 与 reference 不变。

同时纠正两项原草稿判断：`minErgGrp` 是合法群范围外的递减哨兵，不漏边界群；在伴随方向解释为正向物理方向反向时，方位对称且仅依赖 $\mu$ 的条件角核交换方向后 $\mu$ 不变，不能仅因未显式转置 P1/P2 或应用 $(-1)^\ell$ 判错。

W9 局部修复之后，原 C 门槛已由三个独立任务全部闭合：

1. 四类其余 MGACE 条件角表示（isotropic、正单变量、等概率 multi-bin、discrete-cosine）完成 40/40 clean formal 和 40,000 个生产样本的支持域/矩/频数检验。历史“强 P1/P2”措辞不准确；`NLEG/ISANG` 在本路径表示群对条件余弦分布，不等同于传统 Legendre P1/P2 矩输运。
2. 私有 HDF5 position-dependent density mesh 完成独立 readback、位置依赖观测和 10/10 clean 响应 formal，合并 $z=0.0984$。
3. 部署 `10005.01m` 的 NNUBAR=1 纯材料和 `10005:10001=0.9999:0.0001` 的 NNUBAR=1 主导双裂变核混合材料完成 20/20 clean formal，合并 $z=0.9563$ 与 $0.3748$。

最终复核按冻结 F02 需求裁定：“更多几何/边界”不是无限枚举门槛。现有球、内球/外壳和双盒证据覆盖了泄漏、曲面/平面穿越、材料与密度界面等已识别风险；没有证据要求任意几何数量才能评 A。反射边界等未测机制仍明确排除，若第一版实际问题需要则另行审查。

**独立审核后的证据恢复**：原审核正确指出角表示 40 条和 density-mesh 10 条 formal 缺少逐运行原始输出，且 angular analyzer 只强制 aggregate。任务 `20260827_04_f02-formal-evidence-recovery` 已在同一冻结快照下重跑并保留每条 `inp`、stdout、stderr、`inp.out`、exit-code（density 还保留 `inp.Tally`）；独立 strict checker 强制 angular 每 seed + aggregate 和 density 每对 + aggregate。四份 raw/strict report 均由严格 `SHA256SUMS.txt` 经 `sha256sum -c` 验证；独立复核接受恢复 A。

**身份与 serial 闭环**：任务 `20260827_05_f02-binary-source-identity` 的 MPI-enabled one-rank build 已闭合 source—binary 身份，但不再作为严格 serial 标签的唯一证据。任务 `20260828_01_f02-mpi-off-serial-provenance` 从 HEAD `6d208751...` 与 W9 diff SHA256 `5eec...` 用显式 `-Dmpi=OFF` 全新 configure/build；configure 与 runtime banner 都显示 MPI OFF。binary SHA256 `f7354ed9...` 执行 angular 40/40 和 density 10/10 formal；全部 raw reports、strict reports、diff 和 binary 经六项 `SHA256SUMS.txt` 验证，fresh `test_fixed_source_adjoint` 1/1 passed，独立审计 ACCEPT。

**A 的能力边界**：并行 A 仅覆盖上述本机、Open MPI 4.1.6 与 `2×1/4×1/2×2/2×4` 配置；不覆盖更多 rank/thread、跨节点、异构 MPI、Windows。整体也不覆盖完整 photon/耦合粒子、continuous-energy、AIS/HDF5 核数据、delayed、GPT、反射边界、任意机制组合，且不替代 F03 伴随源、F04 adjoint+WW 或 F06/F07 field/RE 的独立分类。原 MPI `4×1` seed 41/rank 3 isotropic Holm 诊断拒绝保留为风险记录，不推翻 aggregate 主检验或该有界 A 决策。

2026-08-25 对 Claude 第二轮反驳的再复核仍是有效的修复前证据：当时 `p_dMatAtomDen` 确为未乘局部比例的基准成员，两个权重调用点也未使用带比例 getter；双 nubar 运行时也确实直读第一 block。当前 W5/W6 修复分别替换了这些控制点，故不再把修复前缺陷当作当前 E 的依据。

2026-08-25 第一阶段 L4 数值验证补充以下证据：

- 当前 `4d3e1...` 的既有 `fixed_source_adjoint` 回归 1/1 passed，重建结果与 reference 字节一致；这仍只属于 smoke。
- W5 修复前已由 $r=0.5,1,2$ 三个 native source trace 数值复现，首碰撞后权重相对倍率符合 $1/r$，最大相对误差 $2.99\times10^{-5}$；修复后三组平均/最小/最大权重均为 `0.66903`，相对比 $1:1:1$，$r=1$ 轨迹哈希不变。
- 在 $r=1$、`NNUBAR=0` 的 30 群 H2O 均匀球中，两个单向散射群对（14→15、20→22）各用五种子做前向—伴随配对；合并 $z=-0.2587$ 与 $0.0829$，全部逐种子也满足 $|z|\le3$。因此该**代表性非裂变 P0 子域**获得数值正证据，但不足以把整个受限子域改判 A，也不抵消 W6。
- 部署 `10001.01m` 双 nubar 核修复前的群概率最大差为 $3.10\times10^{-5}$；Pearson 效应量 $w^2=1.07\times10^{-7}$，80% 功效近似需要 73,289,470 个已观测伴随裂变子代。W6 修复后源码 locator 与实表解析 oracle 证明运行时逐群核等于初始化 total 核，最大概率差为 0；10,000 历史动态重放产生 2,487 条 bank 后继并退出 0。动态频数不作为该小效应的证明。
- W7：已按粒子模式分别定位 neutron/photon 伴随能群上限。原 neutron-only `c5g7td` 输入从退出 11、0 条 source state 变为退出 0、10,000 个源历史和 12,487 条初始/后继粒子记录；既有伴随回归 1/1 通过，reference 哈希不变。
- W5 非均匀响应级验证：同组成 H2O 等体积内球/外壳采用 $(r_{inner},r_{outer})=(0.5,2.0)$ 与 $(2.0,0.5)$，交换空间源/响应和群 14↔15、20↔22。200k 批次因一个单种子 $z=-4.007$ 未通过预设严格总判据；完整保留后统一增至 1M/运行，四组合并 $z=1.106,-0.824,0.400,-0.367$，总体 $z=0.116$，全部 20 个单种子也通过。精度升级属于观察离群后的全量追加证据，不冒充事前独立重复。
- W6 可裂变响应级验证：部署 `10001.01m` 的 ACE `g6→g1` 裂变项为 `0.100120227799`，双向直接 P0 散射为 0。预冻结五组独立前向/伴随 RNG 流、每运行 1M histories；10/10 正常退出，0 异常，最大单组 $|z|=2.033$，逆方差合并 $R_F=0.2419981$、$R_A=0.2425594$、$z=-0.703$。

## Stage 2原则

- Audit 与 Repair 分离。
- 代码证据优先于函数名称和注释。
- 发现疑点只记录，不在审查任务中修改源码。
- 物理正确性不足时采用 Verify，而不是推测通过。
- 标准路径可达且数学后果确定的错误采用 Defect；Audit 结论不自动授权 Repair。

## 变更记录

- 2026-08-24：新增 F02-B 伴随物理正确性审查阶段，F02-A 与 F02-B 分离。
- 2026-08-24：F02-B 独立复核完成，确认非单位局部密度权重与双 nubar 裂变核两项 E 级缺陷；受限子域保持 C — Verify，状态转为待人工复核。
- 2026-08-25：完成 Claude 第二轮反驳再复核；由成员/getter 数据流、`xsdir` 登记和双 nubar 实表核差异确认原 E/C 分层结论不变。
- 2026-08-25：完成第一阶段 L4 数值验证：V0 smoke 通过、V2 数值确认 W5、V4 两个非裂变强非对称群对通过互易性判据；V3 量化部署双 nubar 数据功效并发现 W7 neutron-only MGACE 初始化崩溃。完整能力保持 E，受限子域仍不整体放行为 A。
- 2026-08-25：完成 W7 Stage 3 修复与验证；纯中子伴随初始化不再访问 photon 群，原崩溃输入正常完成。该时点 W5/W6 尚未修复，完整能力保持 E。
- 2026-08-25：完成 W5 Stage 3 修复与验证；局部密度在伴随权重比中正确抵消，三种密度首碰撞权重恢复为 $1:1:1$。W6 仍未修复，完整能力保持 E。
- 2026-08-25：完成 W5 非均匀双区域响应级互易性验证；1M 全量精度批次通过逐种子、分组与总体判据，代表性非裂变子域正证据增强；一般密度场与 W6 仍未放行，完整能力保持 E。
- 2026-08-25：完成 W6 Stage 3 修复；运行时伴随裂变前驱群抽样统一使用 total nubar getter，确定性核差为 0，双表动态路径完成 10,000 历史和 2,487 条 bank 后继。三项已知缺陷均闭合，F02-B 保守转为 C — Verify，不宣称 A。
- 2026-08-25：完成可裂变响应级互易性验证与 F02 阶段复核；`g6↔g1` 正式 10 个 1M-history 运行全部通过，五组及合并 $z$ 均在预设门槛内。因仅覆盖单材料/群对/几何，F02-B 保持 C — Verify，工作顺序进入 F03。
- 2026-08-25：任务 11 以私有 MGACE、独立 readback 和低光学厚度生产路径确认 W9 负单变量伴随角核支持域越界；F02-B 改判 E，A formal 停止，修复任务 12 进入待决策。
- 2026-08-25：任务 12 按人工批准的方案 A 修复 W9；三 seed 动态支持域/矩、五类资产 oracle、既有 CTest 和 reference 完整性均通过。F02-B 恢复 C — Verify，A 门禁仍保留。
- 2026-08-27：其余四类 MGACE 条件角表示完成 40/40 clean formal，40,000 个生产样本通过冻结分布门槛；旧“强 P1/P2”改按实际条件余弦表示解释。
- 2026-08-27：真实 HDF5 density mesh 完成 readback、位置依赖和 10/10 clean formal，合并 $z=0.0984$。
- 2026-08-27：部署 NNUBAR=1 纯材料和 NNUBAR=1 主导双裂变核混合材料完成 20/20 clean formal，合并 $z=0.9563/0.3748$。
- 2026-08-27：最终风险复核确认冻结需求和全部明确 C 门槛已闭合；F02-B 改为 A — Ready（有界、冻结工作树快照）。开放式“更多几何/边界”不再作为无终点门槛，未测边界机制与相邻功能继续明确排除。
- 2026-08-27：Claude 独立审核确认未发现新的已证实 RMC 物理缺陷，但指出 angular/density formal 未留存逐运行 raw transport 输出，且 angular checker 未强制逐 seed 接受门槛；原 A 结论下调为 C — Verify，建立 `20260827_04_f02-formal-evidence-recovery` 等待用户决定是否重跑恢复可审计证据。
- 2026-08-27：用户批准方案 A；在同一 frozen snapshot 重跑 40 angular + 10 density formal，逐运行 raw evidence、strict per-seed/aggregate checker 与 checksum manifest 均已归档。独立复核接受证据恢复，F02-B 恢复 A — Ready（有界）。
- 2026-08-27：Claude 继续审核发现 raw formal binary banner 为 `4d3e1...`，不同于声明 source snapshot 的 `6d208751...`；未发现新物理 defect，但 provenance 不闭合。F02-B 再次下调 C — Verify，等待 fresh-build identity recovery。
- 2026-08-27：任务 05 在全新隔离构建中捕获 `6d208751... + W9 diff 5eec...`，新 binary banner 与源码一致；其上重跑 angular 40/40、density 10/10，strict gates、fresh CTest 和 checksum 均通过。独立审计 ACCEPT，F02-B 恢复有界 A — Ready。
- 2026-08-28：独立审计指出 task 05 是 MPI-enabled one-rank execution，与“serial”标签存在歧义。用户采用严格 MPI-off 定义；task 01 显式 `-Dmpi=OFF` fresh build 的 banner 为 MPI OFF，完整 50 条 formal、strict gates、CTest、checksum 与独立审计均通过，F02-B 在严格 serial 范围保持有界 A — Ready。
- 2026-08-31：并行专项完成本机 Open MPI 4.1.6 的 `2×1/4×1/2×2/2×4` 条件角、响应与运行时矩阵；160/160 条角分布结构运行通过，四配置均 8/8 aggregate 主检验通过，独立 `4×1` 新 seed 40/40 未复现原诊断。用户接受该已验证并行范围为有界 A — Ready；原 `4×1` seed 41/rank 3 isotropic Holm 诊断拒绝保留，不外推至未测并行环境。
