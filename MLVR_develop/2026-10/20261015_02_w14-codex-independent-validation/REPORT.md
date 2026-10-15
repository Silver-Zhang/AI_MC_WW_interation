# W14 独立专项验证结论

**CONFIRMED · P1 · E3（预定义数值检查 + GDB 实际路径 + ASan 越界证据）。**

源初始化同时存在错误速度与越界读取。普通 RMC 的 standard MGACE neutron Forward / Adjoint 均复现，不是 F11 专有问题。建议作为 RMC 通用缺陷，在 Stage 3 生产实施前单独修复。没有修改生产代码，也没有证据据此否定全部历史稳态输运结果。

## 1. 身份、构建和边界

- 根仓库 `main / ee34bf130653e6265793a69294c3076ef47c654a`；RMC `Neural_Network_WW_Iteration / 4810694b7a99dfc3ad7d27f7d443814f511f4829`。开始/结束两者工作区均干净；2153 个归档文件与原工作树 SHA256 一致，见 `logs/identity-{before,after}.json`、`logs/source-sha256.json`。
- 由 `git archive HEAD` 导出源码到本目录 `src/`，复制已有依赖，不改原目录。GCC 13.3.0、CMake 3.28.3、GDB 15.1；新建 Debug/O0，MPI/OMP/AIS/Python OFF，catcherr OFF。完整构建普通 RMC，未复用旧 RMC 对象或 binary。HDF5 使用系统 serial 版本。
- 首次 `loadmodules=OFF` 配置因 HighFive 定位失败（退出 1），原始失败日志保留。重试开启 CMake 的本地依赖加载分支，使用 `scripts/git-readonly` 阻止自动 submodule 更新；依赖均已复制在临时源码树。未运行 checkout/reset/clean。`GIT_SHA` 配置变量未被项目采用，不能把 binary banner 当作提交身份证明；身份以 archive 和逐文件散列为准。
- 正常配置、全编译、三单元 sanitizer 编译和链接退出码均为 0；真实命令/输出见 `logs/configure-retry/`、`logs/build/`、`logs/sanitized-*/`。输入、分析/GDB脚本和全部输出均在本目录。
- 数据 `/home/silver/NucXS_Library/RMC_DATA`，standard ASCII `multigroup/mgxsnp`，1001.50m / 8016.50m，30 neutron groups / 12 photon groups。独立解析核素记录，核对两者群中心/边界一致；数据库文件未修改，身份见 `logs/database-identity.json`。
- 小规模 H2O 长方体固定源；101 histories，RNG Type2 seed17 stride100000，定点/定向/单位权重。6 个合法能量 × F/A，无 WW；另 1 个 native WW 后代观察，最终判定使用 13 个 GDB 运行；早期观察脚本调试运行另存、不计入判定。并做 4 个 targeted sanitizer 运行。未跑完整回归矩阵。

## 2. 确定的源码链与根因

以下行号均为上述当前 HEAD。

| 位置 | 实际行为与判断 |
|---|---|
| `RMC/src/SampleParticle.cpp:27,76,81–83` | 抽样变量后，把物理 MeV 的 `p_dEnergy` 原样写入粒子 `p_dErg`，立即调用 `GetNeuVelMg(p_dErg, G, centers)`。动态实参证实是 MeV。 |
| `RMC/src/GlobeFun.h:538–546` | 实际合同是 **内部 1-based、高能到低能群号**。计算 `k=G-int(arg+0.5)`，读取按低能到高能排列的 `centers[k]`；没有有限性、整数性或边界检查。vector 按值传入，本例副本 size=30，存储 240 bytes。 |
| `RMC/src/CheckMgAceBlock.cpp:38–49` | 从真实 MGACE 的中心和宽度构建低到高数组，lower=center−width/2。并非直接输入物理能量就能作为索引。 |
| `RMC/src/SampleNeutronSource.cpp:202,224–225,269–279` | 普通外源抽样后附加 adjoint 标志，269–270 才调用 `LocateMgErgGrp()`，277–279 更新群号缓存；**没有重算速度**。F/A 共用该链。 |
| `RMC/src/GetMgCs.cpp:263–278`；`GlobeFun.h:141–151` | 根据低到高下边界 upper_bound 定位，再返回 `G-index`。GDB 所有选定源的转换后群号均正确；故群号正确不能证明此前速度正确。 |
| `RMC/src/TrackHistory.cpp:163–215` | 进入 history 后没有先更新源速度，215 调用 RayTracking。 |
| `RMC/src/RayTracking.cpp:227,250–271` → `GetNextTrack.cpp:51–129` | 定位、取截面并抽样飞行距离，随后执行输运/计分。 |
| `RMC/src/TrackWithWeightWindow.cpp:32–37` → `ParticleStateFun.cpp:143–154` | 本例无 WW 时先 TL tally，再飞行；空间移动 `x += u L`，时间推进 `t += L/p_dVel`。GDB 确认首次读取的是未修正速度。 |
| `RMC/src/TrackHistory.cpp:275–292` → `ParticleStateFun.cpp:130–139` | 存活碰撞后，将出射群号写回并用 `GetNeuVelMg` 正确更新速度。但不回溯修正此前累计的错误时间。死亡/泄漏历史可能根本不到此更新。 |

合法 E<0.5 MeV 时，`int(E+0.5)=0`，因此 k=G=30，读取恰好越过向量尾端。此处整数转换本身是合法的；实际 UB 是越界读取。所测合法区间约 `[1.39e-10,17]` MeV 内没有 float-to-int 溢出。极大/非有限能量导致的转换风险仅有静态可能性，本轮未构造非法源，也不外推为动态已证实。

### 后代粒子不是全部自动安全

- 直接散射后继续跟踪的粒子：`UpdateNeuStateMg()` 使用正确群号；本轮各案例首个观察到的存活碰撞后速度都在预设相对容差 1e-12 内。
- **bank 出栈另有已复现的反向坐标错误**：`SaveSplitParticles.cpp:25–35` 保存内部群号；`SampleNeutronSource.cpp:310–317` 恢复后，无条件用连续能量 `GetNeuVel(p_dErg)`，把群号当 MeV。`SampleFromParticleBank():327–365` 不再重算；`CalcFixedSource.cpp:219–235` 直接开始后代 TrackHistory。
- native WW 运行实际观察：出栈 `p_dErg=14`，正确中心 0.4015 MeV、正确速度 **8.76144641452 cm/shake**；实际 **51.1828591292 cm/shake**，等于把 14 当 MeV；第一次后代飞行仍使用此错速。证据 `runs/gdb-final/F-WW-descendants/events.jsonl`。
- 同一 bank 恢复路径也承载裂变产生的中子：`TreatFission.cpp:206–211` → `GetFissionNeuState.cpp:721–736` 将 MG 出射群号入 bank。此适用关系是源码 E1；本轮 H2O 不验证裂变后代，不宣称其动态结果已复现。
- bank 日志还保留了 `p_nMultiGrpNumber=23`、`p_dErg=14` 的缓存不同步观察。当前截面 `ErgGrp()` 使用 `p_dErg`（`ParticleState.h:1357–1358`）；本轮不扩展审查该缓存对 filter 等功能的影响，也不把它当作已证明的稳态偏差。

## 3. 动态结果与独立参考

`make-inputs.py` 直接解析 MGACE 的中心/宽度，不调用被测函数。`analyze.py` 使用 Decimal 50 位计算：

`v_ref = c sqrt(Ec(Ec+2mc²))/(Ec+mc²)`，其中 `c=299.792458 cm/shake`、`mc²=939.56542052 MeV`，常数见 `RMC/src/Constants.h:128,132`；1 shake=1e-8 s。内部正确群号和索引精确比较；速度相对容差预先定为 1e-12，没有事后放宽。

| 源物理 E / MeV | 正确内部群号 | 实际速度数组索引 k | 实际初速 / cm·shake⁻¹ | 正确速度 / cm·shake⁻¹ |
|---:|---:|---:|---:|---:|
| 7.60695e-8（末群中心） | 30 | 30，越界 | 0（本次未插桩运行的表现） | 0.00381485002666 |
| 0.1258（中间群） | 16 | 30，越界 | 0 | 4.90533758686 |
| 0.6615 | 13 | 29，合法索引但选错群 | 54.6310903661 | 11.2436646336 |
| 16（首群中心） | 1 | 14，选错群 | 4.90533758686 | 54.6310903661 |
| 1.390001e-10（最低边界内侧） | 30 | 30，越界 | 0 | 0.00381485002666 |
| 17（最高边界） | 1 | 13，选错群 | 2.97287850139 | 54.6310903661 |

表中 F/A 都复现相同初始错速和索引，转换后的群号都正确。13 个最终 GDB 运行各完成 101 histories、退出 0，观察脚本无错误。**退出 0 不表示缺陷不存在。越界读到 0 也不是受保证的行为**。

0.6615 MeV 的首段实际 L=0.7570077226032348 cm；独立正确飞行时间 0.0673274903934 shake，而运行累计 0.0138567200019 shake。热群首段 L=0.1643847412446247 cm，正确时间 43.090748023 shake；错速为 0 导致 `p_dTime=inf`。存活碰撞后速度正确，`p_dTime` 仍为 inf。全部案例与后代记录见 `results.json`、`results-table.md`。

GDB 只读变量，不调用 inferior 计算函数、不赋值修复状态。先前观察脚本 v2 曾因 GDB Python API 名称错误漏记索引；保留在 `runs/gdb/` 和 `logs/observe-v2.py`。改正的是观察脚本，不是 RMC；最终判定只使用 `runs/gdb-final/` 的 13 条完整无 observer error 证据。

### 内存安全证据

对真正包含 MG 速度初始化/更新的 **SampleParticle.cpp、SampleNeutronSource.cpp、ParticleStateFun.cpp** 重新编译：`-O0 -g -fno-omit-frame-pointer -fsanitize=address,undefined,float-cast-overflow -fno-sanitize-recover=all`，替换独立新构建中的对应对象后重新链接。没有其他 RMC 生产修改。不是全程序 sanitizer 覆盖。

`logs/sanitized-helper-disassembly.txt` 验证最终实际链接的 `GetNeuVelMg` 含 `__asan_report_load8` 与 `__ubsan_handle_float_cast_overflow_abort` 检查，排除 inline/COMDAT 选中未插桩版本的疑问。

| 普通 executable 用例 | 退出码 | sanitizer 实际结果 |
|---|---:|---|
| F/A，7.60695e-8 MeV | 各 1 | 两者均 `heap-buffer-overflow`，READ of size 8，位于 240-byte region 后 0 bytes |
| F/A，0.6615 MeV | 各 0 | 未报 sanitizer 错误；仍有已验证的选错群/错速 |

调用栈两者均为 `GetNeuVelMg(GlobeFun.h:544) ← SampleParticle:82 ← SampleSourceParticle:347 ← SampleFixSource:202 ← ExecuteFixedSourcePrepared:182 ← 普通 CalcFixedSource:81`。完整证据分别在 `runs/asan/{F,A}-thermal_center/stderr`。没有观测到非法整数转换；低能案例在首次越界即终止，不能声称后续全部 UB 已排除。Leak sanitizer 关闭，未审查泄漏。

## 4. 物理影响：已证明与未验证

| 对象 | 结论与证据边界 |
|---|---|
| 源初速、首次飞行所用速度 | **已证明错误**，F/A 及普通入口；合法热群源同时触发内存越界。 |
| 飞行时间、累计粒子时间 | **已证明错误**，包含 inf；碰撞后不会补救过去时间。 |
| 首次飞行距离、碰撞/群截面 | 受检稳态路径 `SampleFreeFlyDist.cpp:7–53,64–96` 使用 `-ln(U)/Σt`，MG 截面按已经正确转换的 `ErgGrp()`，空间更新是 `u L`，没有直接依赖该错速。本轮**未证明这些量因 W14 错误**；也未运行修复前后 oracle。越界 UB 阻止作普遍安全保证。 |
| 普通空间通量/反应率 | `TallyByTL.cpp:11–17` 的 TL/collision 估计量分别用 wL、w/Σ；不直接乘源速度。本轮保留其 Ave/RE 原始输出，但没有独立整体通量/反应率真值，不宣称结果错误或已证明不受影响。 |
| 时间分箱、速度估计器/速度量 | 静态确认依赖：`ProcessBin.cpp:40–80`、`ProcessBinforCell.cpp:63`、`TallyCellByTL.cpp:228–238` 用 t、L/v；`TallyByTL.cpp:18–19` 的 VELOCITY 估计器用 wv；`CalNucMicroXS.cpp:67–68` 返回速度；`Filter.cpp:100–101` 读取速度；`ParticleStateFun.cpp:302–312` 的截止时间距离也用 v。**错误输入依赖已确定，但这些输出模式未实际运行，输出偏差 UNVERIFIED**。 |
| native WW 与 source-history 统计 | 已证明 WW 后代出栈错速；权窗选择/分裂权重直接基于位置、群中心能量、权重（`DoMeshWeightWindow.cpp:39–44`、`WeightWindows.cpp:147–182`）。同一源历史包含后代的循环未变。没有证据证明本轮 wL、WW 分裂计数或 RE 因速度改变；数值影响 UNVERIFIED。 |
| 正向—伴随响应 | 两者共用缺陷可以使双边互易检查对错速不敏感。**未证明既有稳态响应错误**，未重跑历史大矩阵；时间/速度响应不能继承稳态验收。 |
| 碰撞后继续运行 / 裂变后代 | 前者本例速度重算正确但累计时间仍坏；后者共用 bank 风险是源码证据，非本轮动态验证。CE、photon、coupled、MPI/OMP、AIS、Python 源、临界/动力学均未运行，不能外推。 |

## 5. F02/F03 为什么没发现，最小补证是什么

- **F02**：`20260824_05_f02-adjoint-physics-verification/README.md:37–43` 明确把源语义交给 F03；125–130 检查群号方向、碰撞算子和位置推进，没有源速度/首次时间 oracle。最终 `20260828_01_f02-mpi-off-serial-provenance/README.md:69–72,109,117` 验收的是 40 angular + 10 density formal、散射生产样本、互易性与 CTest；没有源速度、首次飞行速度或源向量内存边界门禁。不能把这些既有通过解释为 W14 已测。
- **F03**：`20260825_09_f03-adjoint-source-definition-audit/README.md:68–70` **确实阅读并列出了 SampleParticle 与稍后的 LocateMgErgGrp**，因此不是“源码完全不在范围内”；遗漏的是两者之间速度函数的表示合同。139–145 的动态门禁用 PRINT SOURCE 的 erg 确认最终群号，140/292–293 限定为无时间因子的稳态标量响应及源权重一阶矩。它能检查映射/抽样/归一化，却观察不到映射前的错误速度及越界；没有找到 sanitizer 或首次 v/t 核查证据。
- 只读 `git show b26a81a:...` 核对：历史 F03 所用快照的 **SampleParticle.cpp 与 GlobeFun.h 同当前文件 SHA256 完全相同**；bank 的 GetNeuVel 调用也已存在（历史315、当前317）。见 `logs/historical-source-check.json`。因此不能归因于 Stage 2 新增此源初始化缺陷；本轮没有假装重跑历史 binary。
- 结论应为 **F02 范围/观测量未覆盖，F03 相关源码审查遗漏且动态观察量不足**。保留原有有界算子和稳态响应证据，不自动全盘推翻 F02 A / F03 C–Verify；同时不能继续外推“源状态完整正确/内存安全”。
- 最小补证：本报告的低、中、高群 F/A 源 `E→g→v→首次Δt` oracle；低能源 ASan；一条 native WW bank 后代；若后续修复覆盖裂变 bank，增加一个裂变后代检查。修复后选一对既有 F02 代表性稳态互易案例和 F03 复合源权重/群映射案例作确定性/原统计判据回归。另加一条解析已知时间分箱例子，证明输出时间而不只是内部变量恢复。无需自动扩大成完整矩阵，不更新 reference。

## 6. 最小修复建议与停止点

**主缺陷首先应修在 `CDSource::SampleParticle()` 的 MG neutron 速度初始化分支**：取得由真实边界定位的内部群号，再传给 `GetNeuVelMg()`；保留 `p_dErg` 在既有 SampleFixSource 边界前仍是物理 MeV，避免随后二次转换已经是群号的量。可以复用既有 `LocateMgErgGrp` 在局部获得群号；实施设计须处理重复调用带来的重复警告，不能只为越界加 clamp，更不能只在稍后转换后重算而保留更早的 OOB。

**已复现的 bank 恢复错速还需在 `SampleFromParticleBank/PopParticleOutofStack` 链修正**：让该链取得现有 CDAceData 的 MG 信息，用恢复后的内部群号生成群中心速度，CE 保持物理能量速度。只改 SampleParticle 无法关闭后代风险。可加 `GetNeuVelMg` 合同检查（有限、有效群号、数组大小），但合法索引也能选错群，检查不能代替坐标修复。不建议在 Stage 3 新源层掩盖普通入口缺陷。

判为 **P1**：支持范围内的合法输入可稳定触发 OOB，且普通 F/A 首次速度/时间已错，应阻止相关 Stage 3 生产实施先行；本轮未证明全域稳态结果损坏或必须全面停用，故不升为 P0。主结论证据 E3；消费者/未跑分支仅 E1，sanitizer 最小路径 E2，不将未覆盖项提级。

本轮只验证，未写/应用生产补丁，未改共享 STATUS、INDEX、知识库、冻结04、测试、数据库或 reference。未读 Claude 本轮 W14 结论，未 commit/push 或开始 Stage 3。**到此停止，等待用户授权通用修复。**

二进制 SHA256：

- 普通新构建：`ad29fed64fe64ccdd2ca7634cb62adaa990022eb8265ff0e8758cefc199dca41`
- 定向插桩：`359fcec6d8ca8db14ac159eed87652ff3b0de88d0c6bc048e34da69ade24ba59`

最短复现（全部写入本临时目录）：

```bash
python3 /tmp/w14-codex-review/scripts/run-cases.py gdb-recheck F-thermal_center A-thermal_center F-inbounds_wrong A-inbounds_wrong
python3 /tmp/w14-codex-review/scripts/run-cases.py asan-recheck F-thermal_center A-thermal_center
```

完整逐次命令、cwd、退出码、stdout/stderr 在 `runs/<mode>/<case>/`；正常编译配置与插桩命令保存在 `logs/*/command.json`。以上复现使用新输出标签，保留本轮原始判定目录。
