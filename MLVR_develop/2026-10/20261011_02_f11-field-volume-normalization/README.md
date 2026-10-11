# F11 阶段0：Field 体积归一化最小验证

| 项目 | 内容 |
|---|---|
| 立项日期 | 2026-10-11 |
| 状态 | 已完成（最小数值验证；待独立复核） |
| 任务模式 | C — 深度物理研究与学习 |
| 类型 | 算法实验 / 物理接口验证 |
| 关联知识库条目 | F11，知识库04 §0/§7/§14；W11 |
| 证据等级 | E3；同一Agent执行和自验，未达独立复核E4 |
| 治理标签 | 可复现；边界已定义；原始证据已归档；结果待独立复核 |
| 源码修改/提交 | 无；不commit/push、不切分支、不reset；知识库04冻结正文未改；档案随 2026-10-11 根工作区提交入库 |

## 1. 目标与范围

以知识库04为唯一设计基线，回答uniform与heter Cartesian TL的Ave是否已除网格体积。只做阶段0，不重新设计F11、不按Task15/16开发、不进入固定源核心拆分。四配置standard MGACE中子固定源、MPI/OMP关闭、无WW、单位起始源权重；Normalize=0只诊断。

**物理解释**：bin内的群积分体积平均标量通量为所有源历史的加权真实路径长度总和除以N和V，单位为每单位起始源权重cm⁻²。N包括零得分历史；只平均命中历史会造成选择偏差。固定正比例体积转换不改变该bin的RE；TARGET体积积分先得到同一密度，再乘响应系数与体积。不能把多个bin的RE当作独立误差相加。

## 2. 做法与证据

### 实验与事前判据

运行前记录：`logs/pre-run-plan.md`；正式配置：`logs/config.json`；四输入：`inputs/`。预先允许候选表被反证：若uniform N1匹配phi_ref则否定其1/V补偿；若heter N1匹配L_ref则否定其c=1；均不匹配则不放行。

网格x=[0,2,4]、y=z=[0,2]，两个bin均V=8cm³。uniform用Scope/Bound，heter用ScopeX=1 1及BoundX=0 2 4，物理网格完全相同，并穿越heter coarse边界。六平面域x,y,z∈[-1,5]，y>4的水材料使用1001.50m/8016.50m（30中子群/12光子群standard MGACE）。两个源等概率选取x=-0.5,z=1，分别y=1或3，方向(+x)，0.6MeV，权重1；源和路径均不进入水。**核数据实际加载，轨迹在真空中，没有碰撞、散射或群变换**；不是对材料输运的数值验证。

正式N=200，RNG TYPE=1/SEED=17。四例源序列完全一致。RMC内部能群13对应Energy=-1文本升序第18行（群边界0.5–0.823MeV）；内部输运群与文本行号不能混用。本例未验证通用能群/轴映射。

容差在运行前冻结：Ave差≤5e-12+6e-6×|expected|；RE绝对差≤6e-5；零值必须为0。显式PRINT MESHTALLY 8，不在运行后放宽。3次输入校验失败（SURFACE不支持RPP、N必须>100、PRINT不接受等号）均未产生输运结果；保留pilot/pilot2/pilot3原始输入与输出。把盒改为等价六平面、N改200、PRINT语法修正均在正式输运前登记，判据不变。

### 当前真实计分链（仅相关路径）

源码原文和行号：`logs/source-evidence.txt`。

| 位置 | 证据 |
|---|---|
| `RMC/src/ReadMeshTallyCard.cpp:258–267,270–295` | Normalize解析为p_bUseVol；Scope/Bound设heter=false，ScopeX/Y/Z设heter=true |
| `RMC/src/MeshFun.cpp:270–385` | uniform生成真实段长度，不读p_bUseVol；同bin/跨bin均不除体积 |
| `RMC/src/MeshFun.cpp:455,479–485,540–546,611–617` | heter dMeshVol初始1，p_bUseVol为true时计算各bin体积并返回长度/V |
| `RMC/src/ScoreMeshTally.cpp:40–49,59–67,79–119` | 实际分派两条函数；Type=1得分=粒子权重×MeshTrack长度；群行及Tot同源累加 |
| `RMC/src/SumUpTally.cpp:130–132`、`TallyData.cpp:43–53` | 每源历史聚合Sum1/Sum2；未计分历史对和贡献0，不从分母剔除 |
| `RMC/src/InitialBatchSource.cpp:294–299` | 普通源的总起始权重字段在结束时取实际源历史数；本例单位权重时=N |
| `RMC/src/ProcessTally.cpp:364–365,389–393`、`TallyData.cpp:83–104` | 固定源M=p_dTotStartWgt，Div=1；Ave=Sum1/(M×Div)，RE用history二阶矩，无附加体积处理 |
| `RMC/src/OutputTally.cpp:247–260`、`SingleTally.cpp:981–1001` | 普通非MCNP文本直接打印Ave/RE，无再次体积转换；本例不使用AbsoluteValue/剂量/乘子 |

GDB动态确认四例：uniform仅CalcMeshTrck 200次，heter仅CalcHeterMeshTrck 200次；usevol分别0/1，heterflag分别0/1；DENOM=200,N=200；AVERAGING M=200,Div=1。每个正式输出Source Number=200。所有调用计数及分母见`logs/trace/<case>/stdout.txt`和`checks.json`。

Forward/Adjoint共链证据：`InitiateAll.cpp:130`设AceData伴随标志，`SampleNeutronSource.cpp:222`设粒子伴随角色；`CalcFixedSource.cpp`两角色使用同一TrackHistory和结束统计；`TrackHistory.cpp:164–230`→`RayTracking.cpp:257`→`TrackWithWeightWindow.cpp:33–35`→`TallyByTL.cpp:55–60`→同一ScoreMeshTally，mesh生成/平均/文本路径无Forward/Adjoint体积归一分支。**只确认体积计分链共用，不证明伴随源尺度或互易性**；按任务约定无差异故未补动态Adjoint。

### 独立参考与原始获取

最初四例`logs/formal/`退出0但PTRAC文件为空，不能作oracle。本任务没有为恢复PTRAC修改源码。改用只读GDB在TrackHistory入口获取每个源状态、在**进入网格切段之前的TallyByTL入口**获取真实物理段长（不是CDMesh返回值），保存原始stdout/stderr、退出码及完整200历史/200段；`tools/trace.gdb`不修改生产源码、二进制或目标进程变量。GDB pilot对C++ double&用printf产生无效段长，原样保留且未用于分析，正式改读按值double dTrackLen；获取调整不改变物理判据或容差。

`tools/analyze.py`使用独立slab线段-盒裁剪算法，从真实段起点、方向、长度和权重求各bin内路径。每历史段长5.5cm，命中每bin2cm；93历史命中、107历史避开，全部计入N=200。四例源/段记录逐字一致，SHA256=53936bd102ec7f9ba84a1c212cd8733cce5d17edd8dc530ee86032c90c1c20b5；普通运行与GDB重跑Tally逐字节一致。参考从轨迹构造，**不使用Ave倒推命中数或除体积生成参考**。

独立参考：ΣwL=186cm/bin，Σ(wL)²=372cm²/bin，L_ref=186/200=0.93cm；phi_ref=186/(200×8)=0.11625cm⁻²；RE_ref=sqrt((200×372/186²−1)/199)=0.07603680788149279。零得分群参考和输出均0。

### 环境、身份与复现

根仓库main/504c68be4541245c9459ce72f57e552fdca50572；RMC Neural_Network_WW_Iteration/5cfb0f771d0c5a2127c90d57e51ce672a4e3b616；开工两工作树干净，完整状态与子模块记录`logs/identity-before.json`。结束身份/不可变核验见`logs/final-verification.json`，RMC生产工作树保持干净。已有状态未reset/切分支/提交。

使用`/tmp/f11-volume-rmc-build-snapshot/bin/RMC`，SHA256=d69c87ef2e061418b34a72337582129bdbcc3e79b38a385fb197e88e141dd9a4。源码原样副本位于/tmp；3221文件SHA256与原RMC一致，包含src/include及使用的依赖（`logs/source-snapshot-sha256.json`）。独立构建不运行生产git submodule update。原始delivery/GITSHA为[blank git SHA]，保持不改；因此banner不是HEAD证明，身份由初始Git记录、逐文件hash、完整flags与构建日志、二进制hash共同约束。可执行文件/构建产物不存档，当前留在/tmp供复核。

数据库`/home/silver/NucXS_Library/RMC_DATA`；实际xsdir与mgxsnp的SHA256、大小、两个核素的记录位置见`logs/formal/identity.json`。未复制/修改数据库。mgxsnp SHA256=1d26fac6d32bfb84539d59d5549d809b70e9d5a4f9e34c58034cb9f6cba57001；xsdir SHA256=970e85ad3e7f365868dcba69d348c1626d82b2c127534622af7a43fb01c9f62b。

GCC13.3.0、CMake3.28.3、Python3.12.3、HDF5 1.10.10；更多依赖/链接/GDB/编译标志和CMakeCache见logs对应文件。MPI/OMP宏未定义，banner均OFF；-O2 -g -DNDEBUG，gnu++14。无AIMC训练，src/config.py dataclass、随机训练种子、CUDA/PyTorch/numpy不适用。

复现命令（工作区根目录）：

```bash
TASK=MLVR_develop/2026-10/20261011_02_f11-field-volume-normalization
bash "$TASK/tools/build.sh"
python3 "$TASK/tools/run.py" --label formal
python3 "$TASK/tools/trace.py"
python3 "$TASK/tools/analyze.py"
```

上面按全新任务证据目录重现；现有logs/formal、logs/trace已存在时脚本主动拒绝覆盖。独立复核可在干净副本按相同目录结构复现，或新label运行（分析默认使用formal/trace）。仅检查已归档原始记录：`python3 "$TASK/tools/analyze.py"`，不启动输运。每例精确cwd/命令保存在command.txt；configure/build/每例运行/分析均含stdout/stderr/退出码，失败材料也保留。构建先尝试loadmodules OFF缺HighFive，再尝试副本漏delivery，最终复制原delivery/GITSHA成功配置，所有失败日志保留。

真实分析输出（`logs/analyze.stdout`，退出0）：

```text
Independent reference: N= 200 hit= 93 zero= 107 V=8 cm^3
uniform_n0 Ave= 0.93 RE= 0.0760368079 phi_ref= 0.11625 converted_error= 0.0
uniform_n1 Ave= 0.93 RE= 0.0760368079 phi_ref= 0.11625 converted_error= 0.0
heter_n0 Ave= 0.93 RE= 0.0760368079 phi_ref= 0.11625 converted_error= 0.0
heter_n1 Ave= 0.11625 RE= 0.0760368079 phi_ref= 0.11625 converted_error= 0.0
Checks: 248 / 248 max Ave error= 0.0 max RE error= 1.8507209653684242e-11
```

## 3. 决策

**用户已直接授权**：记录实验方案和判据后直接执行，允许新测试输入/分析脚本、独立构建未修改RMC、小规模验证。不得修改生产源码、数据库、既有测试/reference，不实现F11，不commit/push。此授权覆盖五步流程的实施关口，不再提交待批准实验提案。

**人类理解确认**：用户已直接指定phi_ref=Σ(w×真实路径长度)/(N×V)、N包含零得分、候选表可被推翻，这是用户给定的问题定式与验伪要求。最终结果解释和可进入阶段1的判断尚待人/独立复核确认；不声称用户已接受本Agent的新结论。

| 变更卡 | 内容 |
|---|---|
| 问题与风险 | Normalize语义差异造成通量/响应差V倍 |
| 改动对象 | 任务内新输入、参考脚本、文档和入口；源码不改 |
| 预期因果链 | 网格类型/Normalize→长度或长度/V→单位权重score→全历史平均→Ave |
| 验证 | 四配置、8cm³、含零历史、独立盒裁剪、动态调用/分母、248数值行 |
| 回滚 | 只涉及本任务产物和文档；既有代码/参考不变 |

## 4. 结论与边界

**结果解释与结论（E3，待独立复核）**：KB04候选表两行都获最小动态证据支持，没有候选行被本例否定。uniform Normalize=1没有在当前计分链中除体积；heter Normalize=1已除体积。“Normalize=1一律意味着Ave就是通量密度”的泛化被本例反证。不能靠统一照抄Ave或统一再除V实现正确Field。

每个bin（1、2相同）的第18群实测如下；完整全部群与Tot、分母、体积、原始二阶矩、误差及判据见`logs/comparison.csv/json`：

| 路径 | Normalize | 实际N / 平均分母M×Div | V cm³ | Ave | RE | 独立phi_ref cm⁻² | 转换后偏差 |
|---|---:|---:|---:|---:|---:|---:|---:|
| uniform | 0 | 200 / 200×1 | 8 | 0.93 | 0.0760368079 | 0.11625 | 0 |
| uniform | 1 | 200 / 200×1 | 8 | 0.93 | 0.0760368079 | 0.11625 | 0 |
| heter | 0 | 200 / 200×1 | 8 | 0.93 | 0.0760368079 | 0.11625 | 0 |
| heter | 1 | 200 / 200×1 | 8 | 0.11625 | 0.0760368079 | 0.11625 | 0 |

**Field与TARGET共同转换表（当前源码）**：value_i,g=c_i Ave_i,g；history密度score_i,g=c_i raw_history_score_i,g。RE_i,g保持原RE。正向目标history分数X_h=Σ_i,g r_i,g V_i c_i raw_history_score_h,i,g，均值R=Σ_i,g r_i,g V_i value_i,g；RE_R必须由同一history的X_h统计，不能拼各bin的RE。

| 路径 | Normalize | Ave物理含义 | c_i | 适用 |
|---|---:|---|---|---|
| uniform Cartesian TL | 1 | 源归一化加权轨迹长度 | 1/V_i | F11 v1候选规则获本例支持 |
| heter Cartesian TL | 1 | 源归一化体积平均群积分通量密度 | 1 | F11 v1候选规则获本例支持 |
| uniform Cartesian TL | 0 | 源归一化加权轨迹长度 | 1/V_i | 仅诊断，未扩展首版范围 |
| heter Cartesian TL | 0 | 源归一化加权轨迹长度 | 1/V_i | 仅诊断，未扩展首版范围 |

作为转换关系的算术检查，若TARGET包括两个bin且r=1，则独立history响应=93×4/200=1.86；ΣV×value也为1.86；未补偿uniform N1直接当密度会给14.88，差8倍。**这是关系检查，不是已实现/测试F11 TARGET功能。**

**是否进入阶段1**：本阶段0的最小数值判据已满足；从本项前置条件看，可以在独立复核确认、用户另行授权后立项阶段1。当前状态为“最小验证已完成、待独立复核”，不是新接口Ready。生产实现未开始，本任务完成后停止。

**需单独处理的问题**：W11——普通uniform Cartesian TL的Normalize=1未除体积（未修复）；若后续修复通用scorer，须同步撤去F11 uniform补偿并验证reference影响，避免重复除V。当前按04 adapter方式可处理，不需为本验证改生产代码，也不把通用scorer修复混入阶段1拆分。另有本真空例PTRAC输出为空（观察已登记W12，根因未定位、未修复），本次以只读原始段记录完成oracle，不承诺PTRAC通用可用。

**仍未确定 / 未覆盖到的验证**：动态Adjoint、碰撞/散射/非单位或不等源权重、裂变、WW、非等体积异构bins、同bin短段分支、多维轴与边角/对角射线、MPI/OpenMP、Windows、GPU/大规模验证、F11 HDF5和多bin目标history实现均未验证。静态支持所有Cartesian bin按对应V取系数，动态证据只覆盖本例两等体积bin、多粗网格跨越。未以零得分的首/末群宣称非零首末群映射正确，未以2×1×1宣称完整3D展平正确。核数据加载但不验证其碰撞物理；无新基准/参考结果。

## 5. 过程

| 日期（按用户Asia/Shanghai上下文） | 过程 |
|---|---|
| 2026-10-11 | 读取AGENTS/STATUS/AGENT_CONTEXT/04 §0,7,14/工作流；建C任务并保留开工Git身份 |
| 2026-10-11 | 相关计分链定位，写事前方案；原样源码外部构建，保留两次配置失败和最终构建日志 |
| 2026-10-11 | 三次输入校验失败保留；等价六平面/N200/PRINT语法调整后执行四普通配置，退出均0 |
| 2026-10-11 | PTRAC为空，改只读GDB；修正引用参数调试记录，四次完整轨迹重跑并核对普通Tally不变 |
| 2026-10-11 | 248/248对独立参考比较通过；更新STATUS/INDEX/02速览/06问题及物理导读/交接指针，待独立复核；不进入阶段1 |

原始运行日志的时间字符串由运行环境生成，不替换或加工。changes.diff为任务脚本快照；RMC差异为空的不可变核验保存JSON，不造空changes.diff。

归档检查真实输出见`logs/archive-check.stdout`（退出0）：需处理0项、提示31项；提示为历史档案的12个空changes.diff及19个空目录，本任务未出现结构/台账问题，未自动修整历史档案。最终不可变核验退出0，3221文件原始/副本hash一致、核数据库/二进制未变、RMC状态/分支/HEAD与开工一致、04与HEAD逐字节一致；Python脚本AST和git diff --check通过。
