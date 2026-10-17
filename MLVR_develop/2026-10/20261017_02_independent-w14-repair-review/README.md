# independent-w14-repair-review

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-10-17 |
| 状态 | 已完成（**NEEDS CORRECTION · P1**） |
| 任务类型 | 独立源码审核与限定动态复核 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | Claude，独立审核 |
| 关联知识库条目 | W14 |
| 涉及文件 | RMC 只读；修复任务档案、STATUS、INDEX、知识库06、物理导读 |
| RMC 分支 / HEAD | `Neural_Network_WW_Iteration` / `4810694b7a99dfc3ad7d27f7d443814f511f4829`；保留既有8文件未提交差异 |

---

## 1. 目标与范围（① 立项）

**要做什么**：独立审核 Codex 已实施的 W14 多群中子速度修复，核实普通固定源、bank后代、CE旁路及代表性Stage2回归，并检查修复前后源路径是否有新退化。

**涉及什么**：只读检查RMC候选diff及其独立构建；在`/tmp/w14-claude-review/`做低/中/高能F/A、首飞时间、sanitizer、WW bank、裂变bank与 spontaneous-fission 源路径复核。只更新本工作区审核档案和状态指针。

**怎样算完成**：形成独立判定和复核证据，明确已通过部分、阻塞缺陷与未验证边界；同步修复任务及看板。不得修改RMC、KB04、核数据库或reference；不提交推送，不开始Stage3。

**原始材料**：独立GDB/运行产物、输入和输出留在`/tmp/w14-claude-review/`。已复核的修复任务原始材料仍留在`20261017_01`的ignored `logs/local-evidence/`；本档案只保留报告和摘要。

> **物理解释**：普通MG源和Bank后代的能量状态以离散群号存储，速度必须由对应MGACE群中心计算；type-5自发裂变源先初始化普通源状态，之后又以Watt谱物理MeV覆盖能量。若覆盖后速度未同步，首飞时间仍与该物理MeV不一致；若原始MeV进入只接受整数群号的Bank恢复接口，还会被拒绝。若修复完整，type-5路径也应保持能量、速度、群号合同且可完成输运；若基线可完成而修复版在该路径中止，则推翻“所有MG固定源路径均已修复”的主张，但不否定已单独验证的ordinary fixed-energy与WW路径。

---

## 2. 做法与证据（②设计 / ④复核）

**设计 / 定位**：首先检查RMC实际branch/HEAD/diff，再独立读源码；形成对普通源、Bank恢复和spontaneous-fission能量覆盖的因果链后，才查阅修复档案和摘要。直接运行修复任务离线复核脚本，并以独立GDB观察器和私有type-5输入验证关键边界。

**身份**：RMC branch `Neural_Network_WW_Iteration`，HEAD `4810694b7a99dfc3ad7d27f7d443814f511f4829`。差异为8个已跟踪文件：`AceData.h`、`CalcFixedSource.cpp`、`FixedSource.h`、`GetMgCs.cpp`、`GlobeFun.h`、`PythonInterface/PythonInterface.cpp`、`SampleNeutronSource.cpp`、`SampleParticle.cpp`。RMC diff `51 insertions(+), 30 deletions(-)`；审核期间未修改或覆盖这些改动。KB04 SHA256为`aeed2760f84427bdd8d139182d7bb3f4193c0c63f67decec1d42c7aad7a676b0`。

**普通W14-A证据**：修复任务精确源码SHA与修复构建副本相同。独立GDB在Forward/Adjoint分别观察0.2435、0.6615、16 MeV源样本、能群映射和首次`FlyByLength`。各速度为6.8239725209、11.2436646336、54.6310903661 cm/shake；首飞`Δt=L/v`与观察值相符。0.2435 MeV在修复sanitizer候选binary中Forward、Adjoint重跑均退出0，无ASan/UBSan诊断。独立WW Forward/Adjoint银行分别观察285和54次出库，恢复能量为整数群号且速度对应群中心；小型普通Forward裂变后代3次出库通过。这些只覆盖具体ordinary源及bank夹具。

**先前ASan OOB事件的更正**：最初临时目录中被称为修复版的ASan binary，实际源码副本`SampleParticle.cpp` SHA为`a13321b5...`，内容仍是旧的直接把MeV传入helper的代码；它不是候选patch。不能把该OOB归因于修复版。随后使用修复任务记录的插桩binary SHA `4d4d41dc...`、精确测试输入重跑0.2435 F/A，均退出0且无sanitizer诊断。无关旧UBSan信息不作为W14结果。

**P1反例：type-5 spontaneous-fission来源**：读取`ExternalSource.cpp`可见`SampleSimpleSpontaFissParticle()`调用普通源抽样后，于Watt谱抽样把`cParticleState.p_dErg`改写为物理MeV；此处没有重算速度。后续普通固定源通用转换再把该值改成MG群号。用隔离的U-235 `FISSMULT`/`PARTICLE=5`输入，未修改baseline binary完成（exit 0）；修复候选binary中止（exit 134，`std::invalid_argument: MG neutron velocity: invalid internal group or center array`）。只读GDB捕获：Watt物理能量`1.1358207724356031 MeV`，仍沿用普通源0.6615 MeV的速度`11.243664633572111 cm/shake`；转换后群号为12，但扩展初始bank中的相邻Watt样本值`1.0694489269608258`以非整数传入新的整数群helper，触发拒绝。此为原始候选修复未覆盖的MG spontaneous-fission源/扩展bank路径；不以同一轮普通induced fission bank成功替代。

**归档证据独立复核命令及输出**：

```text
$ python3 MLVR_develop/2026-10/20261017_01_w14-mg-source-velocity-repair/scripts/recheck.py
raw evidence hashes: 1840 verified
velocity-results.json recomputed exactly
ordinary-comparison.json recomputed exactly
ff fresh-process comparisons rechecked
faf-ww fresh-process comparisons rechecked
No RMC execution or production modification performed.
```

**方案选择**：独立结论按已验证的调用族拆分，不因ordinary/WW/普通诱发裂变通过而扩大到所有源构造器。spontaneous-fission反例达到P1停止条件：候选修复使同一输入从baseline可完成变为异常退出，且源速度未随Watt物理能量更新。由用户/实施者另立修复或明确收窄支持范围；本审核不修改代码。

**实施要点**：无RMC实施；无生产代码修改；本档案包含独立审核报告`Independent_W14_Repair_Review.md`。

**未覆盖到的验证**：未覆盖MPI/OMP/AIS、全Python源运行、全 spontaneous-fission谱/类型、kinetics完整源与bank矩阵、MG光子/耦合粒子、完整Stage2裂变F/A、所有time tally/velocity estimator、一般稳态响应偏差、全程序sanitizer及Windows。没有运行正式F02/F03/F04完整矩阵。

---

## 3. 决策记录（③）

- **决定**：依用户已授权的独立审核和正式归档范围继续；只读RMC并同步审核档案/状态，不实施修复。
- **决定人 / 日期**：用户 / 2026-10-17（先前授权原文及停止条件见修复任务`logs/user-authorization.md`）。
- **约束**：不改RMC、冻结KB04、数据库、reference；不commit/push/reset/checkout/clean；不开始Stage3；保留所有既有未提交修改。

**变更卡**：
| 风险 | 改动范围 | 验证与停止条件 | 回滚 |
|---|---|---|---|
| 审核结论若未区分构源和bank阶段，会把局部通过外推成全路径关闭 | 仅新建报告并同步修复任务与状态指针；绝不触碰候选RMC改动 | 按源码和baseline/候选同输入的动态对照判断；发现候选新增异常即维持W14 open，不宣告关闭 | 文档仅增量修改；不改或撤销其他Agent内容 |

> **C关口记录**：本次为已完成修复的独立审核与归档，并非新的物理方案实施授权。当前对话没有用户针对G1–G4的新回复；不代填人类理解确认。仅引用修复任务已记录的用户授权与此前答复，不将其冒充本次审核结果确认。

---

## 4. 结论与边界（⑤）

- **结论：NEEDS CORRECTION · P1（限定standard MG fixed-source neutron source族）**。W14-A普通固定能量源初始化及W14-B native WW银行恢复，在本轮测试的Forward/Adjoint低/中/高能范围和明确覆盖的ordinary诱发Bank范围内得到独立支持；但type-5 spontaneous-fission Watt源覆盖能量后仍保留旧速度，并将非整数物理MeV带入MG银行恢复helper，修复候选相较baseline导致可复现异常退出。W14整体不得标记CLOSED。
- **不能推出什么**：不能据此说已验证的ordinary低/中/高源或native WW bank结果错误；不能推出所有稳态通量/响应存在偏差；不能开放Stage2非零裂变连续F/A；不能认为其余kinetics/spontaneous构造器都已验证。Stage2原受限冻结结论保持，Stage3设计仍为NEEDS REVISION且未实施。
- **遗留 / 下一步**：W14实施者需处理或明确排除type-5 MG spontaneous-fission源族，更新测试并重新进行独立审核；在此之前保留P1/open。此归档不批准后续RMC修改。
- **提交状态**：RMC branch/HEAD未变，8文件差异仍未提交；根仓库文档未提交、未推送；KB04未改。

> **G4结果解释**：旧MeV/group速度混用在已测ordinary路径上已纠正，速度、首飞时间及所测稳态事件保持均通过；但FISSMULT/Watt源会在初始速度计算后替换能量，候选代码既没有同步速度，也没有保持物理MeV到MG group的阶段合同，最终被严格group输入校验拒绝。该证据否定“所有相关MG neutron source路径已经修好”，不否定限定ordinary与WW结果。当前没有用户对本轮G4解释的回复，因此记录为待用户确认；审核结论仍为NEEDS CORRECTION。

---

## 5. 过程记录

| 日期 | 操作 / 事件 |
|---|---|
| 2026-10-17 | 先检查候选RMC branch/HEAD/status/diff；确认保留未提交8文件修改，KB04 checksum未变。 |
| 2026-10-17 | 先独立读源码后核对修复报告；查明先前OOB sanitizer binary实际编译的是旧源码副本，使用manifest所指修复binary重新跑低能F/A，通过。 |
| 2026-10-17 | 独立GDB确认ordinary 0.2435/0.6615/16 MeV Forward/Adjoint速度与首飞时间；native WW F/A Bank和普通Forward诱发裂变bank通过。 |
| 2026-10-17 | 独立建立私有U-235 type-5 spontaneous-fission输入；baseline退出0、修复版exit 134。GDB确认Watt物理能量覆盖后速度未更新，并确认非整数MeV抵达MG bank helper；判定P1 NEEDS CORRECTION。 |
| 2026-10-17 | 运行修复任务离线证据checker：1,840个raw hashes、19 velocity cases、8 ordinary pairs、FF/FAF fresh-process comparisons全部复核一致；不执行生产输运。 |
| 2026-10-17 | 将结论同步到修复任务与状态指针；RMC仍未改、未提交推送，KB04/reference/数据库不变。 |

**证据等级**：限定动态对照与源码交叉核验（E3）；结论只适用于本档案列明的source路径。
