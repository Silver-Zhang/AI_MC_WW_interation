# W14 — RMC 多群中子源速度修复独立审核（Claude）

| 项 | 内容 |
|---|---|
| 审核日期 | 2026-10-17 |
| 审核基线 | RMC `Neural_Network_WW_Iteration` / `4810694b7a99dfc3ad7d27f7d443814f511f4829`；候选8文件未提交差异 |
| 分类 | **NEEDS CORRECTION · P1**（MG spontaneous-fission source path regression / uncovered path） |
| 范围 | W14-A普通MG neutron fixed-source初始化，W14-B native fixed-source bank恢复；限定动态F/A、WW与裂变银行、CE旁路及type-5 spontaneous-fission源审查 |
| 实施状态 | 只读独立审核；未修改RMC、reference、核数据库或冻结KB04；未commit/push/reset/checkout/clean |

## 1. 独立结论

**整体 NEEDS CORRECTION · P1；不得将W14标为CLOSED。** 修复候选对已实际测试的普通MG fixed-energy Forward/Adjoint初始源速度路径、native WW neutron descendant bank恢复路径，以及一个普通Forward诱发裂变bank例，结果与物理群中心/首飞时间参考相符。但独立测试发现：修复实现只覆盖普通源抽样和固定源bank恢复，没有处理type-5 spontaneous-fission源在普通源采样之后再覆盖Watt物理能量的路径。该路径在未修改baseline可以完成；候选版则因非整数物理MeV进入要求内部整数群号的helper而异常退出。与此同时，速度仍是覆盖前普通源能量对应的旧速度。因此原补丁不只是漏测此路径，而且在此合法源类型下引入可复现回归。

该判定针对W14所称的MG fixed-source neutron common velocity repair范围，不否定本轮通过的ordinary fixed-energy/WW夹具，也不证明一般稳态flux或response存在系统偏差。Stage2受限冻结不扩展到连续非零裂变F/A；Stage3仍未实施。

## 2. 源码核查与状态合同

- 普通 `CDSource::SampleParticle()` 在[RMC/src/SampleParticle.cpp:79-88](../../../../RMC/src/SampleParticle.cpp)中，对物理MeV先调用`LocateMgErgGrp(..., false)`，将返回群号传给`GetNeuVelMg()`，同时保留`p_dErg`为MeV，供后续映射。
- [RMC/src/ExternalSource.cpp:481-499](../../../../RMC/src/ExternalSource.cpp)中的`SampleSimpleSpontaFissParticle()`先调用源`SampleParticle()`，之后用Watt抽样值覆盖`cParticleState.p_dErg`，没有同步重算`p_dVel`。多群普通固定源在[SampleNeutronSource.cpp:269-280](../../../../RMC/src/SampleNeutronSource.cpp)才将当前`p_dErg`转成MG group。
- 新helper [RMC/src/GlobeFun.h:539-550](../../../../RMC/src/GlobeFun.h)刻意校验输入是有限、精确整数的1..G群号；fixed-source普通bank恢复[SampleNeutronSource.cpp:316-321](../../../../RMC/src/SampleNeutronSource.cpp)把bank值直接传入此helper。
- 普通fixed-source的Watt后代在不同入口可能被转成MG群号，也可能以物理MeV存入初始bank；type-5当前源状态和多重后代均须明确区分物理能量阶段与内部群号阶段。不能假定所有bank写入都已是整数group。

## 3. 独立动态证据

### 3.1 ordinary fixed-energy source与首次飞行：通过（限定）

使用修复任务所记录的候选build-after正常binary，在隔离副本中以GDB于source函数返回、MG映射后和首次`FlyByLength()`读取状态。Forward与Adjoint均测0.2435、0.6615、16 MeV：

| 输入物理能量 | 映射群 | 观测速度 (cm/shake) | 首飞时间示例 (shake) |
|---:|---:|---:|---:|
| 0.2435 MeV | 15 | 6.8239725209087103 | 0.071183940753768882 |
| 0.6615 MeV | 13 | 11.243664633572111 | 0.067327490393381956 |
| 16 MeV | 1 | 54.63109036610188 | 0.066493963439012579 |

观测首飞距离逐例满足`Δt=L/v`。独立运行值为：

```text
F-0.2435: SAMPLED E=0.24349999999999999 V=6.8239725209087103
          FIRST_FLIGHT L=0.48575725563371247 V=6.8239725209087103 DT=0.071183940753768882
A-0.2435: same source velocity and first-flight delta-t
F-0.6615: V=11.243664633572111, first-flight delta-t=0.067327490393381956
A-0.6615: same source velocity and first-flight delta-t
F-16:     V=54.63109036610188, first-flight delta-t=0.066493963439012579
A-16:     same source velocity and first-flight delta-t
```

真实候选sanitizer binary SHA256 `4d4d41dcf590c46f0dc1e77976c34f1af55e7d45ae60fcb39b6d802e1e387aaa`。0.2435 MeV候选sanitizer Forward和Adjoint各重跑一次，均exit 0，无stderr sanitizer诊断。先前在另一个临时目录观察到的0.2435 ASan OOB不属于候选：当时编译副本`SampleParticle.cpp` SHA是`a13321b5...`，其内容仍旧把MeV直接传给velocity helper。核对源文件及binary身份后已将此旧OOB从候选修复结论中排除；原有Universe/StrideRNG UBSan信息亦非本次缺陷。

### 3.2 native WW bank及普通诱发裂变bank：通过（限定）

以候选build-after binary分别在普通MG Forward WW、Adjoint WW输入中观察bank出库；恢复状态中的`p_dErg`为MG群号，速度与群中心独立参考相符。Codex保存的精简验证记录为Forward 285次、Adjoint 54次出库；本轮独立GDB观察到了两条路径及正确的group/velocity状态。另一个普通Forward U-235诱发裂变后代bank夹具观察到3次bank出库，记录群号12对应中心1.088 MeV及速度约14.4148361982 cm/shake，与中心速度参考吻合。

这些测试是特定ordinary fixed-source native WW / induced-fission bank路径，不覆盖type-5 spontaneous-fission Watt源，也不开放Stage2连续非零裂变F/A。

### 3.3 type-5 spontaneous-fission源：候选失败（P1）

建立隔离输入：U-235 MG材料、`FIXEDSOURCE`、`FISSMULT ZAID=92235 SFNU=1.0 SFYIELD=1.0 WATT=0.988 2.249`、外源`PARTICLE=5`。未修改baseline binary（SHA256 `b7c3d1fcf1583a1ce7fdc4b61e324fc0d52835a6f2e510c1f018d33bbfe97e48`）对该输入正常结束、exit 0。候选正常binary（SHA256 `d96d97e92c3d23e7137a39ea1c37db47ddb2364cb60fcc15570c780f63ea524b`）同输入异常退出134。

候选GDB观察：

```text
ordinary_sample_return: E=0.6615 MeV, V=11.243664633572111 cm/shake
Watt replacement:      E=1.1358207724356031 MeV, V=11.243664633572111 cm/shake
ordinary MG mapping:   E=1.135820772435603 group 12, same stale V
later bank/helper:     dGroup=1.0694489269608258, G=30
throw: std::invalid_argument: MG neutron velocity: invalid internal group or center array
```

该bank值来自多重Watt源后代，仍是物理MeV，不是整数内部群号。候选的整数group guard避免把它误读/截断为群号，但没有将spontaneous-fission源路径在速度初始化和bank存储前正确映射/同步；输入因此在bank出库时报错。结合baseline同输入exit 0、候选exit 134，确认属于修复候选新增的受支持路径回归，而非单纯缺少性能/数值覆盖。

## 4. 归档证据与核验

在正式核对Codex结果前先独立检查候选diff和源路径。后续只用来复核既有证据的任务checker输出为：

```text
$ python3 MLVR_develop/2026-10/20261017_01_w14-mg-source-velocity-repair/scripts/recheck.py
raw evidence hashes: 1840 verified
velocity-results.json recomputed exactly
ordinary-comparison.json recomputed exactly
ff fresh-process comparisons rechecked
faf-ww fresh-process comparisons rechecked
No RMC execution or production modification performed.
```

身份：RMC branch `Neural_Network_WW_Iteration`、HEAD `4810694b7a99dfc3ad7d27f7d443814f511f4829`；8个已修改跟踪文件保持。普通候选binary SHA `d96d97e9...`，插桩binary SHA `4d4d41dc...`，baseline binary SHA `b7c3d1fc...`。冻结KB04 SHA256 `aeed2760f84427bdd8d139182d7bb3f4193c0c63f67decec1d42c7aad7a676b0`未改变。所有新增私有运行文件仅在`/tmp/w14-claude-review/`。

## 5. 判定与处置建议

1. **W14-A ordinary fixed-energy源初始化**：限定standard MGACE fixed-source neutron F/A输入下，通过本轮0.2435/0.6615/16 MeV速度与首飞时间检查；修复候选低能sanitizer复核通过。
2. **W14-B native WW bank恢复**：Forward/Adjoint测试子域和小型普通Forward诱发裂变bank通过，不覆盖所有bank生产者。
3. **整体W14**：**NEEDS CORRECTION · P1，保持OPEN**。type-5 spontaneous-fission Watt能量覆盖/扩展bank路径具有源速度陈旧与物理MeV进入group-helper的确定错误，修复候选在原baseline完成的输入上中止。
4. **修复前置条件**：后续修复需对Watt源每个初始/多重后代明确物理MeV→MG group映射、群中心速度更新和bank保存合同；用baseline/候选同一FISSMULT U-235小输入进行source状态、bank状态、首飞时间、sanitizer对照，再重跑必要ordinary路径。此建议不构成代码修改授权。
5. **不作的推论**：不撤销已测ordinary稳态空间Tally/RNG零差结果；不声明普遍steady-state flux/response偏差；不开放Stage2同进程非零裂变F/A；不启动Stage3。MPI/OMP/AIS/Python运行、kinetics完整source families、所有时间/velocity estimators和Windows均未覆盖。

**最终物理解释**：已测普通源路径的MeV→group→center velocity链和首飞时间正确；但type-5自发裂变在链中途换成Watt能量，当前实现没有同步速度或维持输入group helper契约，导致旧速度继续使用并在银行恢复拒绝新状态。因此修复具有真实进展，但尚未覆盖整个W14目标。用户对本轮G4解释尚未回复，不代填确认。
