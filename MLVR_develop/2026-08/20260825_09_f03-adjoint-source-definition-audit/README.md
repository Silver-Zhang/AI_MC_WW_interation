# f03-adjoint-source-definition-audit

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-25 |
| 状态 | 已完成（C — Verify，冻结子域） |
| 任务类型 | RMC 只读功能与语义审查 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F03 |
| 涉及文件 | `RMC/src/ReadFixedSourceBlock.cpp`、`ReadExternalSourceBlock.cpp`、`ReadSourceCard.cpp`、`ReadSourceDistributionCard.cpp`、`ExternalSource.cpp`、`SampleParticle.cpp`、`SampleVariableFromDistri.cpp`、`SampleNeutronSource.cpp`、Python Source API 及既有测试资产；本阶段只读 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `b26a81a26f6d43aea405b1c744f0c4cdf4fd8bdf`；审查时工作树 clean |

---

## 0. 人类阅读摘要（模式 C 必填）

**要回答的问题**：目标响应不是“打开伴随开关”本身，而是一个响应泛函。若正向响应写成
$R=\langle q^\dagger,\psi\rangle$，则正确的伴随问题是
$L^\dagger\psi^\dagger=q^\dagger$。本任务判断当前 RMC 是否会从第一版目标响应得到正确的
$q^\dagger$，以及是否能把该相空间源真正作为多群伴随粒子执行。

**当前判断与边界**：静态代码证据（E1）表明，RMC 能执行用户通过通用
`EXTERNALSOURCE/SOURCE/DISTRIBUTION` 或 Linux Python `SOURCESUB` 明确给出的相空间源；固定源采样结束后，程序才依据全局 adjoint 状态把粒子标记为伴随粒子。未发现 `ADJOINT` 卡、tally/response 对象或其他 standard fixed-source 路径自动生成 $q^\dagger$。因此：

1. **执行能力存在**：给定位置、方向、能量/群、粒子类型、权重等源状态后，RMC 可进入 F02 已审查的伴随输运链。
2. **响应到源的语义映射未内建**：必须由外部控制器、人工输入或 Python 脚本承担；当前也没有冻结的 response schema、映射规则或守恒/归一化契约。
3. **第一版责任边界已冻结**：由人/MLVR 外部控制器构造显式源，RMC 只执行采样、MG 群定位和伴随输运；动态验证完成前不宣称 Ready。
4. 结论只覆盖 standard MGACE、fixed-source neutron adjoint 与当前 checkout；不外推到 continuous-energy、photon/耦合粒子、GPT/AIS、任意角响应或 Windows `SOURCESUB`。

**人需要在什么关口确认理解**：上述系统边界、响应类别、失败条件和不可外推范围已由用户确认；动态实施仍必须遵守下方运行前冻结设计。

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：审查 RMC 是否能够把第一版 MLVR 的目标响应函数定义为可执行的 fixed-source adjoint source，区分“RMC 能输运用户给定的普通外源并标为伴随粒子”和“程序或接口能从目标响应正确构造伴随源”两种能力，给出 A–F 分类及可复核证据。

**范围**：只读审查 RMC standard MGACE、fixed-source neutron adjoint 的源输入、分布表达、采样、能群映射、权重与伴随标志传递；核对第一版需求中的目标响应类型。暂不审查伴随输运本体（F02 已完成）、伴随场/RE（F06/F07）、WW 组合（F04）或修改 RMC。

**验收标准**：

1. 写清响应泛函与伴随源的物理对应关系，以及第一版所需的空间、能量、方向、粒子类型和归一化表达能力。
2. 从输入卡到 `SampleFixSource()` 建立实际调用链，说明哪些源分布可直接表达、哪些需要外部预处理/Python API/代码扩展。
3. 至少复核一个现有伴随输入，确认外源参数如何成为伴随初始状态；若关键语义仅靠源码不足，设计最小动态 probe，但不在未决策前修改 RMC/reference。
4. 按审查规范给出 A–F 分类、证据边界、风险和下一步；不因 F02 的手工互易性输入已运行就推断 F03 已 Ready。

**原始材料**：

- `logs/source_static_inventory_20260918.txt`：当前 RMC branch/HEAD/clean 状态、通用源变量入口、源采样入口、Python `SOURCESUB` 入口，以及专用 response-to-adjoint-source 符号搜索的原始输出；SHA256 `4c335dba8bc6ae0bd81e3f28c024eaf9dd7061d2a598e14ab980c5b0543ef76f`。
- F02 已归档的 `isotropic/seed_59/adjoint/inp`：现有“伴随输入”实物例子，用于追踪显式外源如何成为伴随初始状态；本任务不复制或改写其原始资产。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：F02 已确认 RMC 能推进给定 fixed external source 的多群伴随历史，并完成阶段复核。F03 关注的是源是否由目标响应定义。现有 F02 数值案例由任务脚本人工交换源群/响应群，这证明可手工构造特定标量响应的伴随输入，不自动证明 RMC 具备一般响应到伴随源的定义接口。

**只读定位结论**：当前 standard fixed-source 路径复用通用 `EXTERNALSOURCE` 或 Python `SOURCESUB` 采样，随后只设置 `p_bIsAdjointParticle=true`；`ADJOINT` 卡本身仅启用模式和给出最大能量。通用源能表达第一版空间–能群源所需的基本初态，但“哪个 cell/群应有多大响应权重、方向如何处理、如何归一化”不是由目标 tally/response 自动推导。

**证据链**：
| # | 位置（基于 `b26a81a...`） | 说明 |
|---|---|---|
| 1 | `MLVR_Knowledge/01_双向迭代基础框架_方法与功能需求.md:274-276` | 冻结的原始需求仅写“能够根据目标响应定义并执行第一版所需的伴随源”，没有冻结责任边界。 |
| 2 | `RMC/src/ReadFixedSourceBlock.cpp:219-234` | `ADJOINT` 只读取 `ADJOINTCALCULATION` 与 `MAXADJOINTENERGY`；启用时设置全局 adjoint 状态，未绑定 tally/response。 |
| 3 | `RMC/src/ReadExternalSourceBlock.cpp:ReadExternalSourceBlock` → `ReadSourceCard.cpp:36-1434` | 通用源解析 `FRACTION/BIASFRAC/WEIGHT`、位置/几何、方向、`ENERGY`、`PARTICLE`、`CELL`、`TIME` 等；标量变量通常可直接给值或引用 `D<n>`。 |
| 4 | `RMC/src/Source.h:CDSource`；`ReadSourceDistributionCard.cpp:ReadSourceDistributionCard` | 分布支持离散、向量、cell vector、bin、分段线性、函数谱、子分布及 `DEPEND` 从属关系，足以表达较一般的外部相空间采样，但对象没有“响应泛函”语义。 |
| 5 | `RMC/src/ExternalSource.cpp:38-57,347` | 按 `BIASFRAC` 选择源，以 `FRACTION/BIASFRAC` 修正初始权重，再调用普通 `CDSource::SampleParticle()`。 |
| 6 | `RMC/src/SampleVariableFromDistri.cpp:6-282`；`SampleParticle.cpp:6-95` | 抽样空间、方向、能量、粒子、cell 等变量，累计偏倚权重，并写入粒子初态；此处不查询目标响应。 |
| 7 | `RMC/src/SampleNeutronSource.cpp:CDFixedSource::SampleFixSource:194-268` | 先走 Python/通用源采样（195/199/202），到 222 行才设置 `p_bIsAdjointParticle=true`，268 行将输入能量定位到 MG 群。调用顺序直接支持“先有普通源状态，后附加伴随输运属性”。 |
| 8 | `RMC/src/PythonInterface/PythonInterface.cpp:94-169`；`ReadSrcSubBlock.cpp:ReadSrcSubBlock` | `SOURCESUB` 可由同目录 Python `source(proc_id,num)` 返回 `[type,pos,dir,energy,weight,time,source_id]`，可承载外部映射；但仅在 `USE_PYTHON_API` 构建下存在，文档明确不支持 Windows。 |
| 9 | `RMC/tests/source_subroutine_neutron/source_neutron.py` | 现有测试证明 Python 能构造并偏倚抽样一般源，不证明其会从 RMC tally/response 自动构造伴随源。 |
| 10 | F02 formal 输入 `.../runs/isotropic/seed_59/adjoint/inp` | 输入显式写 `ADJOINTCALCULATION=1` 和 `SOURCE ... CELL=1 ... WEIGHT=1 ENERGY=3.0`；与对应 forward 输入相比仅打开伴随模式，源卡仍由任务侧直接给出。它证明“显式源可执行”，不证明“响应可自动翻译”。 |
| 11 | `logs/source_static_inventory_20260918.txt` | 在本次限定路径中未搜索到 `adjoint source` 或 `response to source` 构造符号。负搜索只作辅证，主结论来自上述实际调用链。 |

**影响面**：F03 结论决定 MLVR 控制器能否直接生成伴随输入，或是否需要外部响应到源的映射层/有限 RMC 扩展；也会约束后续 F06/F07 和 F04 的接口设计。只读审查不更新 reference/benchmark。

**为什么之前没做/没发现**：F02 有意排除了伴随源语义，只验证给定源后的输运算子；当前按功能依赖顺序在 F02 阶段复核后正式进入 F03。

---

## 2A. 物理解释与可证伪假设（模式 C 必填）

**问题定式**：设正向输运为 $L\psi=q$，目标响应为

$$
R=\langle h,\psi\rangle,
$$

则相容的伴随问题为

$$
L^\dagger\psi^\dagger=h.
$$

这里 $h(\mathbf r,E,\Omega,p,t)$（离散多群时为相应网格/群/方向/粒子分量）就是伴随源。RMC 源采样器需要的是一个可采样的初态分布与历史权重；目标响应给出的是物理核。两者之间必须有显式、可审计的转换：把 $h$ 分解成抽样概率 $p_s$ 与初始权重 $w=h/p_s$（离散情形还需计及约定的体积、能群宽度、角测度及响应归一化）。F03 成功不能只看程序是否运行，还要检查采样后的统计期望是否重构冻结的 $h$，且伴随响应与相应正向响应在误差内一致。

第一版当前已冻结 Field 仅为空间×能群，不包含角度；因此建议第一版 F03 也先冻结为**标量通量型、非负、空间–能群目标响应**。表面电流、强角依赖、符号变化、时间依赖、反应率中核素/截面因子等是否纳入，必须另行定义，不能由“通用源变量很多”自动推出支持。

**可证伪假设**：

| 假设 | 若正确应观察到 | 推翻条件 |
|---|---|---|
| H1：standard fixed-source RMC 没有内建“目标响应 → 伴随源”层 | `ADJOINT` 只切模式；采样链不访问 tally/response；源初态完全来自 `EXTERNALSOURCE`/`SOURCESUB` | 找到并追通一条当前可达路径，能从同一目标响应对象自动生成源的空间/群/方向/权重并由 fixed-source adjoint 消费 |
| H2：外部控制器可用通用源承载第一版离散空间–能群响应 | 冻结响应单元/群及强度可无歧义映射为 `SOURCE/DISTRIBUTION`；源样本的 cell/群频数和加权一阶矩与预期一致 | 必需的 cell/群联合关系、权重/归一化或几何抽样不能表达，或动态样本与期望显著不符 |
| H3：`SOURCESUB` 是更灵活但有条件的备用承载层 | Linux、`USE_PYTHON_API` 构建中可返回完整初态，随后同样被标记为伴随并定位 MG 群 | 伴随路径绕过/覆盖脚本返回值，或构建、并行/线程、所有权/异常行为使第一版无法可靠使用 |

**物理—代码因果图**：

```text
目标响应规范 h(r,g[,Ω,p,t])
	↓  当前缺失/未冻结：响应语义、离散测度、归一化与责任归属
外部映射器 / 人工输入 / SOURCESUB
	↓  ReadSourceCard + DISTRIBUTION，或 Python 返回 7 元初态
CDExternalSource::SampleSourceParticle / SampleParticle
	↓  位置、方向、能量、粒子类型、权重、时间
CDFixedSource::SampleFixSource
	↓  p_bIsAdjointParticle=true；LocateMgErgGrp
F02 多群伴随输运
	↓
伴随估计量；与匹配正向响应做统计互易性/期望检验
```

**证据等级与治理标签**：

- 当前判断：**E1（静态代码/文档证据）**。
- 治理标签：**未冻结**（F03 系统边界待人决策）、**部分可复现**（源码快照与静态 inventory 已归档，尚无本任务动态 probe）、**边界已定义**（见第 0 节）、**原始证据已归档**（静态 inventory；源码位置以 commit 固定）。
- 不得将 F02 的动态互易性证据升级为 F03 的 E2/E3：那些输入由任务侧手工构造，未验证一般“响应 → 源”转换。

### 2B. F03 动态验证运行前冻结（2026-09-18）

本节是本轮动态运行的预注册契约；运行后不得根据输出改变测度、源归一化、响应构型或接受门槛。

**响应 schema 与测度**：

| 字段 | 冻定内容 |
|---|---|
| `cell_id` | 几何中一个完整、均匀、可定位的物质 cell；空间响应在该 cell 内均匀 |
| `mg_group` | 1-based RMC 物理群号；输入使用该群的冻结代表中心能量，运行后用 `PRINT SOURCE 1` 的 `erg` 校验 |
| `h_i` | 非负标量、空间平均的响应系数；首版不含截面、核素、角、表面或时间因子 |
| `cell_volume_cm3` | 几何解析体积；首版响应为 cell 体积积分通量，因此源分量强度为 `H_i=h_i*cell_volume_cm3` |
| 空间测度 | `CELL` 源在 cell 内均匀抽样；cell tally 不写 `VOLUME`，保留 `weight*track_length` 的体积积分量 |
| 能量测度 | `ENERGY=-1` 使用 MGACE 群结构；每个群的 tally 是群积分量，不另除群宽；响应源使用该群代表中心能量 |
| 角测度 | 标量各向同性，方向密度为 $1/(4\pi)$；不验证角响应 |
| 粒子/模式 | neutron、standard MGACE、fixed-source、adjoint；Linux 串行，首版不启用 `SOURCESUB` |

**外部 response-to-source 映射**：对冻结响应分量集合 $i$，令

$$
H_i=h_iV_i,\qquad H=\sum_iH_i.
$$

在 RMC `EXTERNALSOURCE` 中使用 `FRACTION=H_i`，每个源对象使用同一个
`WEIGHT=H`；不写 `BIASFRAC` 时 RMC 令其等于 `FRACTION`。若启用有偏组件抽样，
另写严格为正的 `BIASFRAC=B_i`，预期 RMC 以归一化后的 $F_i/B_i$ 修正初始权重，
仍满足

$$
\mathbb E[w\,\mathbf 1_i]=H_i.
$$

因此复合伴随源的总强度由 `WEIGHT=H` 保留，而不是把 `FRACTION` 归一化误当成绝对响应。
`SOURCESUB` 仅保留为后续条件备用接口，本轮主验证不使用它。

**冻结动态构型**：使用三个等体积同心 H$_2$O 区域：内球半径 $4$ cm，第一壳层外半径
$4\sqrt[3]{2}$ cm，第二壳层外半径 $4\sqrt[3]{3}$ cm；三 cell 体积均为
$V=4\pi(4\,\mathrm{cm})^3/3$。正向源固定为 cell 1、group 14、单位强度；目标复合响应为

$$
h_2=0.7\quad\text{on (cell 2, group 15)},\qquad
h_3=1.3\quad\text{on (cell 3, group 20)}.
$$

正向运行同时 tally `(cell 2, group 15)` 与 `(cell 3, group 20)`；正向 CELL 源是在源 cell 内均匀抽样且总强度为 1，
因此体积积分 tally 还需乘源 cell 体积，比较量预注册为
$R_F=0.7VT_{2,15}+1.3VT_{3,20}$。伴随运行用两个源分量 `(cell 2, group 15, H_2)`、
`(cell 3, group 20, H_3)`，tally `(cell 1, group 14)`，比较量为 $R_A$；二者构成同一
双线性响应。除无偏映射外，另做固定同一响应的 `BIASFRAC` 映射，偏倚概率只改变抽样
频率，不改变 $R_A$ 的期望。

**冻结随机与统计门槛**：pilot 使用 seed `1`、每运行 `20,000` histories；formal 使用
seed `1,3,5,7,9`、每运行 `200,000` histories；RNG type `2`、stride `1,000,000`。
pilot 仅用于验证输入、支持域、群定位和量级，不升级最终证据；pilot 通过后才执行 formal。
正式结果要求：全部运行 exit code 为 0；所有 tally 有限且为正；`C=0` 源 trace 的每条
记录位置落在其声明 cell、群属于声明群集合、权重有限为正；无未解释 warning/error/NaN/Inf；
无偏/有偏两种映射的每个组件加权一阶矩相对 `H_i` 的 z-score 满足 $|z|\le3$；复合
响应的每个 seed 配对、五 seed 逆方差合并及总体合并均满足 $|z|\le3$。任一门槛失败即停止，
不删除 seed、不更新 reference、不调整冻结契约。

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A — 外部映射、RMC 执行 | 将第一版责任边界冻结为：MLVR 控制器持有 response schema，并把受限的空间–能群响应确定性转换为 RMC `SOURCE/DISTRIBUTION`（必要时才用 `SOURCESUB`）；RMC 只负责采样和伴随输运。决策后做不改 RMC 的最小动态 probe：源样本/群定位 + 一组响应级正伴随对照，并保存原始输出。 | 需要在 MLVR 层定义 response schema、体积/群宽/角测度和归一化契约；通用卡对大网格可能膨胀；复杂角/符号响应不在首版。优点是无 RMC 接口改动、与 Stage 1“框架层调度”一致。 | ★推荐 |
| B — RMC 内建 response-to-source 层 | 在后续 Stage 3/4 另立任务，为 RMC 设计显式 response 输入/对象和到 adjoint source 的转换，并加入一致性检查与测试；本审查当前可先判 F — Missing。 | 物理语义、输入兼容、tally 耦合、维护和验证成本最高；易把框架策略固化进 RMC。必须再次设计、拍板，不能在本审查中顺手实现。 | 条件推荐：仅当明确要求 RMC 单体完成转换 |
| C — 手工源、仅登记能力 | 第一版只允许用户手工给出少量点/cell/单群源，F03 记录为“显式源可执行”，不建立统一 response schema 或转换器。 | 最快但不可扩展、不可审计，容易把归一化/群映射错误带入后续 WW 闭环；不能充分满足“根据目标响应定义”。 | 不推荐 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：方案 A — 外部映射、RMC 执行。第一版允许先由人/MLVR 外部控制器把目标探测器的计数响应转换为显式 RMC 伴随源；RMC 保持现有功能，负责源采样与伴随输运。暂不采用方案 B，不要求 RMC 本体自动从 response/tally 对象生成伴随源。
- **决定人 / 日期**：用户 / 2026-09-18
- **理由与约束**：后续双向迭代需要把目标探测器的目标计数变成伴随源，经伴随输运得到用于评价正向输运的重要性；当前优先保持 RMC 现有功能，先允许人工转换。首版选择第 1 类响应：探测器 cell 内非负、标量、空间×能群的通量/计数型响应。不得修改 RMC、更新 benchmark/reference、commit、push 或切换 RMC 分支。

**人类理解确认（模式 C 必填，由人确认或转述后确认）**：
- 我理解本任务要判断/修复的物理关系是：用户明确表述，后续双向迭代要把“目标探测器的目标计数”变成伴随源并进行伴随输运，由此评估正向重要性。
- 我理解当前根因假设是：已确认采用外部/人工转换作为第一版责任边界；RMC 继续承担显式伴随源的执行，不要求其内建 response-to-source 转换。
- 若该假设错误，预期会看到：用户确认，若源的 cell/群支持域、加权期望、偏倚补偿、MG 群定位或匹配的正向—伴随响应对照失败，则方案 A 不能判 Ready。
- 本次即使验证通过，仍不能推出：用户确认，只能支持已冻结的受限响应和 standard MGACE fixed-source neutron adjoint，不能外推到反应率、角/表面/时间响应等范围。
- 我批准的范围，以及明确不批准的扩展：批准方案 A、保持 RMC 现有功能并先人工转换；首版采用第 1 类探测器 cell 通量/计数型响应，即非负、标量、空间×能群响应；明确暂不批准方案 B。角响应、表面电流、符号变化响应、时间响应、反应率响应及其余平台/粒子/能量模式不纳入本次首版验证。

**变更卡（模式 C 必填；待人拍板）**：
| 项 | 内容 |
|---|---|
| 问题与风险 | RMC 能执行显式伴随源，但 response-to-source 的责任、测度和归一化未冻结；直接进入迭代会造成“程序能跑但物理源不对应目标响应”的风险。 |
| 拟改动 / 不改动 | 方案 A：只新增/冻结 MLVR 侧 response schema、映射资产和验证；不改 RMC，不更新 benchmark/reference。方案 B：另立 RMC 扩展任务。 |
| 预期因果链 | 冻结响应 $h$ → 可审计转换 → RMC 初始样本的加权期望等于 $h$ → 伴随输运 → 匹配响应验证。 |
| 验证与失败停止条件 | 检查离散映射、源样本频数/权重/群定位和至少一组响应级对照；任何归一化歧义、支持域错误或预设统计门禁失败即停止，不以改 reference 消除差异。 |
| 回滚方式（若适用） | 方案 A 不改 RMC；删除未采纳的映射资产即可。若未来方案 B 改 RMC，须由独立任务保存 `changes.diff` 并按该任务回滚。 |

> 方案 A 与第 1 类首版响应已获批准；测度、归一化、动态 probe 构型和统计门槛须在运行前写入实施设计。方案 A 不需要改动 `../RMC`。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | | | |
| 2 | 冻结动态验证设计 | 本 README 第 2B 节、`会话纪要.md` | 已冻结 schema、体积积分测度、`H_i=h_iV_i` 映射、等体积三 cell 构型、seed/population 和 $|z|\le3$ 门槛；尚未运行。 |
| 3 | 生成并运行初版 pilot | `cases/pilot_v2/`、MPI-off RMC SHA256 `6ddb171479dffe2c8829461367410ae0a4b1ae16657b881e4e23f5cc5b959216` | 4/4 退出 1；真实错误为 `unknown input card EXTERNALSOURCE in FIXEDSOURCE block`。原始输入、stdout、stderr 和 exit code 已保留；该错误修正后未作为物理失败。 |
| 4 | 运行修正版 pilot | `cases/pilot_v3/`、`run_cases.py`、`analyze_source_mapping.py` | 4/4 退出 0；`run_count=4 anomaly_lines=0`，源支持域、MG 群、正权重和正有限 tally 检查通过。 |
| 5 | 修正并复核一阶矩门槛 | `analyze_source_mapping.py` | 曾误把组件均值目标写成 `H_i/H`，导致 `z=103.60`；按源码确认 RMC 的公共 `WEIGHT=H` 后改为 `E[w·1_i]=H_i`，复核输出仍为 `run_count=4 anomaly_lines=0`、`pass=True`。 |
| 6 | 运行 pilot 响应级对照 | `analyze_response.py`、`results/pilot_v3_response_v2/` | 无偏 `z=1.039`，有偏 `z=0.826`；`pair_count=2 anomaly_lines=0`，`criterion=no unexplained anomalies and all paired \|z\| <= 3; pass=True`。此前未乘源 cell 体积时分别为 `z=-32.104`、`-20.168`，该结果用于发现并修正测度错误，不作为结论。 |
| 7 | 生成并运行 formal | `cases/formal/`、20 runs、每运行 200,000 histories | 20/20 exit 0；manifest SHA256 `6f43f36f332188a213888640a57f0fd8c3fd8d802bf650a249568051ad571c29`；run summary SHA256 `f30117959d324bd26f96735e0296baac8feefde699c2a6b94c1d1c2a1e3d233b`。 |
| 8 | 分析 formal 源映射与响应 | `results/formal_source/`、`results/formal_response_v2/` | source：`run_count=20 anomaly_lines=0 pass=True`；response：10 个逐 seed 配对、2 个五 seed 合并、总体均通过，最终 `overall z=0.04968547644325037`、`criterion=... pass=True`。 |

**代码改动**：本任务未改 `RMC/`；本阶段只修改 F03 任务档案，暂无 RMC `changes.diff`。

生成方式：
```bash
git -C ../../RMC diff > changes.diff
# 改原型则：
git -C ../../AIMC_WWiteration diff > changes.diff
```

---

## 6. 验证 / 实验记录（④ · Agent 填，要贴真实输出）

| 验证项 | 命令 | 结果 |
|---|---|---|
| pilot 源映射 | `run_cases.py` + `analyze_source_mapping.py` | `manifest_sha256=ec78fa853e587fff7296059a4a350278f4d80a74aaa11addba78079f4df17920`；`run_count=4 anomaly_lines=0`；包含 `E[w·1_i]=H_i` 一阶矩 z-score 门槛，`criterion=all source support/group/weight/tally checks pass; pass=True`。 |
| pilot 响应级对照 | `analyze_response.py` | 无偏：`R_F=51.9974835375`、`R_A=50.152`、`z=1.03857426858`；有偏：`R_F=51.9974835375`、`R_A=49.843`、`z=0.826422258999`；两组均通过 $|z|\le3$。 |
| formal 响应级对照 | `analyze_response.py` | biased 合并 `z=-0.452530857928`；unbiased 合并 `z=0.326436110553`；总体 `R_F=52.2403766581`、`R_A=52.2299039717`、`z=0.0496854764433`；10/10 逐 seed、2/2 合并和总体均满足 $|z|\le3$。 |

```
（关键验证输出原文粘贴，不要只写"通过"；训练/实验需含：种子、配置、依赖版本、命令）
```

**实验设置（算法实验必填）**：
- 随机种子：RNG type `2`；pilot seed `1`、formal seeds `1,3,5,7,9`；stride `1,000,000`。
- 配置快照：30 群 H$_2$O；`cell_volume_cm3=268.08257310632899`；`H_2=187.6578011744303`、`H_3=348.5073450382277`、`H=536.165146212658`；population pilot `20,000`、formal `200,000`。
- 依赖/执行资产：Python `/usr/bin/python` 3.12.3；MPI-off/OMP-off RMC SHA256 `6ddb171479dffe2c8829461367410ae0a4b1ae16657b881e4e23f5cc5b959216`，版本输出 `3.5.0`，构建源码关键文件哈希与当前 RMC checkout 一致；候选源码提交 `eabfadc...` 的关键实现哈希与当前 `b26a81a...` checkout 一致，故记录为兼容执行资产而非当前 checkout 原生 build。
- 基准对比：本任务使用冻结 forward/adjoint 响应级统计 oracle，不更新 benchmark/reference。

**未覆盖到的验证**：（老实写，比如 GPU 训练、大规模 RMC 算例、Windows 侧无法本地验证）

- 已完成 F03 pilot 与 formal；未验证当前 checkout 直接重新构建的完整 build provenance，使用了关键实现文件哈希一致的 MPI-off/OMP-off 执行资产。
- 未验证 `SOURCESUB` 在当前 checkout 的实际构建可用性、MPI/OpenMP 线程安全或异常路径。
- 未验证大网格 `SOURCE/DISTRIBUTION` 输入规模、联合分布覆盖、任意方向/表面响应、符号响应、时间依赖和跨平台行为。

---

## 6A. 结果解释卡（模式 C 必填；实施/验证后填写）

| 问题 | 解释 |
|---|---|
| 结果支持/否定了哪个假设？ | pilot 与 formal 支持 H2：首版空间×MG 群响应可映射为显式源；支持 cell 支持域、MG 群定位、`E[w·1_i]=H_i` 一阶矩、无偏/有偏纠偏及复合响应级对照。H1 的“RMC 无内建 response-to-source 层”仍由静态调用链支持。 |
| 证据等级与治理标签及其依据？ | 提升为 E2（任务专用动态证据）：20/20 formal exit 0、source mapping 门槛通过、10/10 逐 seed、2/2 合并和总体响应 z 门槛通过；schema、原始输入/输出、SHA256 已归档。 |
| 通过/失败在物理或工程上分别意味着什么？ | 通过只说明冻结响应子域能被所选映射可靠执行；失败说明映射、源表达或执行链至少一处不满足，不得更新 reference 掩盖。 |
| 不可外推的边界是什么？ | 见第 0 节与未覆盖项。 |
| 下一步是否需要升级范围或另立任务？ | 若选 B 或动态 probe 暴露 RMC 缺口，须另立 Stage 3/4 任务。 |

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：在已冻结的首版子域内，方案 A 通过 F03 动态验证：外部 response-to-source 映射生成的非负标量、空间×MG 群 cell 通量/计数型响应，能够由 RMC 显式采样、定位 MG 群并执行 fixed-source neutron adjoint；无偏与有偏组件抽样均保持预期一阶矩，复合响应与匹配正向响应在预注册 $|z|\le3$ 门槛内一致。F03 当前分类为 **C — Verify（冻结子域已验证，非 RMC 内建自动转换）**，不是 Ready/A。
- **遗留问题 / 后续待办**：若要覆盖反应率、角、表面、时间、符号响应、continuous-energy、耦合粒子、SOURCESUB 或并行平台，必须另立任务并重新冻结/验证；RMC 内建 response/tally → adjoint source 仍是未实现边界。
- **知识库同步**：待人决策与动态证据后更新 `02_RMC功能审查矩阵.md`；当前不提前写入最终分类。若结论改变物理适用范围，再同步 `MLVR_Physics_Guide/`。
- **是否已提交**：未提交；未改 `RMC/`，RMC 审查快照为 `b26a81a...`。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-25 18:59 | 立项 |
| 2026-08-25 | 完成最小入口定位；确认 F03 与 F02 的能力边界，保持待设计，不预判分类 |
| 2026-09-18 | 升级为模式 C；完成通用源、分布、Python Source API 和既有伴随输入的只读调用链，形成物理定式、验伪条件和三方案，状态转为待决策 |
| 2026-09-18 | 用户选择方案 A：保持 RMC 现有功能，先人工/外部转换目标探测器计数响应为伴随源；方案 B 暂不采用。首版响应类型与归一化边界待确认。 |
| 2026-09-18 | 用户选择第 1 类首版响应：探测器 cell 内非负、标量、空间×能群的通量/计数型响应。 |
| 2026-09-18 | 用户确认动态失败条件与不可外推边界，授权开始方案 A 的实施与动态验证；状态转为实施中。 |
| 2026-09-18 | 读取 cell tally scoring、fixed-source normalization、source sampling 和 MG 定位实现；确认 cell track-length 默认不除体积，冻结第 2B 节的 response schema、`H_i=h_iV_i` 映射、等体积三 cell 构型和统计门槛。 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 修复建档序号阻塞 | `MLVR_develop/new_task.sh` | 原脚本将 `08` 按八进制解析而失败；显式使用十进制后实际创建 `09` 任务成功。 |
| 3 | 核对需求与 F02 边界 | F03 需求、F02 档案、物理导读 | F03 审查响应到源的定义，不重复审查伴随输运算子。 |
| 4 | 最小源码定位 | `ReadFixedSourceBlock.cpp`、`SampleNeutronSource.cpp` | `ADJOINT` 卡启用模式；通用外源先采样，随后粒子被标为伴随。尚未发现专用 `ADJOINTSOURCE`，需继续审查外源表达能力。 |
| 5 | 固定审查快照 | `git -C RMC rev-parse/status` | branch `Neural_Network_WW_Iteration`，HEAD `b26a81a...`，工作树 clean。纠正档案中的旧 SHA。 |
| 6 | 盘点通用源表达能力 | `ReadSourceCard.cpp`、`Source.h`、`ReadSourceDistributionCard.cpp`、`SampleVariableFromDistri.cpp`、`SampleParticle.cpp` | 可表达位置/几何、方向、能量、粒子、cell、时间和权重，并支持独立/从属分布与偏倚修正；未携带目标响应语义。 |
| 7 | 追踪实际伴随源调用链 | `ExternalSource.cpp`、`SampleNeutronSource.cpp` | 普通源先生成完整粒子初态，随后才设置伴随标志并定位 MG 群；确认“执行”与“响应构造”是两个层次。 |
| 8 | 审查 Python 备用接口 | `ReadSrcSubBlock.cpp`、`PythonInterface.cpp`、测试与用户手册 | `SOURCESUB` 可返回完整初态，但要求 `USE_PYTHON_API`、同目录脚本，文档限定 Linux；未发现其自动读取目标响应。 |
| 9 | 复核既有伴随输入 | F02 `isotropic/seed_59/adjoint/inp` 与 forward 输入 | 输入由任务侧显式给出同一 `SOURCE` 并打开 `ADJOINTCALCULATION`；只能证明显式源进入伴随输运。 |
| 10 | 归档静态原始证据 | `logs/source_static_inventory_20260918.txt` | 62 行；SHA256 `4c335d...ef76f`。专用 response-to-source 搜索为空，但最终判断以实际调用链为主。 |
| 11 | 形成模式 C 决策材料 | 本 README 第 0、2A、3、4 节 | 状态转为待决策；不填写人类理解确认，不修改 RMC。 |
| 12 | 记录人工方案决定 | 用户回复、本 README 第 4 节 | 用户批准方案 A，明确保持 RMC 现有功能并先人工转换；未把尚未确认的响应类型、验伪边界伪造为人类确认。 |
| 13 | 冻结首版响应类别 | 用户回复、本 README 第 4 节 | 用户选择第 1 类 cell 通量/计数型响应；首版限定为非负、标量、空间×能群。 |
| 14 | 完成人工理解关口 | 用户回复、本 README 第 4 节 | 用户确认支持域、加权期望、偏倚补偿、MG 群定位和响应级对照为失败条件，并确认结论不可外推边界；授权开始。 |
| 15 | 闭合 tally 测度与源归一化 | `RMC/src/TallyCellByTL.cpp`、`TallyType.cpp`、`ProcessTally.cpp`、`ExternalSource.cpp`、`SampleParticle.cpp`、`SampleNeutronSource.cpp` | Type=1 track-length 计数为 `weight*track_length`；仅显式 `VOLUME` 才除体积；fixed-source 按总起始权重归一；`FRACTION/BIASFRAC` 执行组件抽样纠偏，`WEIGHT` 保留绝对强度；采样后设置 adjoint 并定位 MG 群。 |
| 16 | 检查已有冻结可执行文件 | `/tmp/mlvr_f02_mpi_off_build/bin/RMC` | 当前路径不存在；不使用旧 checkout 二进制作为 F03 证据，后续需构建当前 checkout。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
