# W14 最小设计与实施前判据

日期：2026-10-17。基线4810694b。用户G1回复原文：“请开始修复”。此文在生产修改和本轮运行前记录。

## 因果链与改动

物理源能量必须先按已有lower-bound群定位映射，再按中心算速度，粒子p_dErg保持MeV直到现有SampleFixSource转换。Bank存的是内部群号，恢复速度直接按中心计算。空间抽样、碰撞、权重、调度、RNG和history循环不改；速度、时间的变化是预期结果。

1. src/AceData.h、src/GetMgCs.cpp：LocateMgErgGrp增加默认true的警告开关，原调用保持警告行为；新源速度预定位传false避免重复警告。加有限物理能量及群数组有效尺寸检查，定位算法及边界归群不变。
2. src/SampleParticle.cpp：MG中子分支只用局部group定位、调用GetNeuVelMg，不覆盖p_dErg。
3. src/GlobeFun.h：GetNeuVelMg明确内部1..G整数合同，const vector引用；先检查finite/integer/range/size及中心能量再索引，拒绝不合法状态，不clamp。
4. src/FixedSource.h、src/SampleNeutronSource.cpp、src/CalcFixedSource.cpp：SampleFromParticleBank和PopParticleOutofStack传入现有const CDAceData引用；仅修改恢复速度的MG/CE分支及7处调用参数，不改Bank和输运循环。
5. src/PythonInterface/PythonInterface.cpp：同一原始源MeV误传路径采用同样局部定位（保持Python回传能量及CE分支）。属于相同W14-A入口的直接修正；Python运行没有代表fixture，不能据serial构建宣称动态验证。

p_nMultiGrpNumber缓存：Pop未更新；ErgGrp()和本修复使用p_dErg。Filter.cpp:75和ParticleTrack.cpp:343/363读缓存；缓存修复不影响本次速度的必要性，作为独立遗留，不改。

## 运行前门禁（G3记录）

- 构建：由实际HEAD fresh archive复制依赖到专用/tmp目录，原树不运行submodule命令。GCC Debug/O0，MPI/OMP/AIS/Python OFF，test ON，catcherr OFF；修复后同参数构建。记录命令/返回值/哈希。
- 独立参考：从真实1001.50m/8016.50m中心/宽度计算群号和50位Decimal相对论速度，c=299.792458 cm/shake、m=939.56542052 MeV。速度相对容差1e-12；首飞Δt采用abs误差≤1e-12*max(abs(t_before),abs(t_after),abs(L/v),1e-300)，包含浮点相减精度。群号/数组索引精确一致。GDB只读，不调用inferior函数。
- 低/中/高群F/A、首末边界，固定与离散谱；原始MeV保持、映射group、首次速度/时间、存活碰撞后速度均观察。任何错误群号/速度、重复新增警告或观察器错误均失败。
- 原热群F/A ASan/UBSan例必须无W14越界。定向插桩实际生产TU与helper链接身份；不以未插桩单元/全程序未知项冒充全覆盖。非法群号、NaN/inf、数组尺寸负例须在转换/索引前拒绝。
- 真实native WW split出库速度/首次飞行用相同独立参考，所有观察到的后代不得使用group-as-MeV速度；小型U235裂变bank如果现有材料可用则追加，不触碰prepared非零裂变禁限。
- 同seed/data/compiler的修复前后ordinary MG F/A（含WW、离散谱）、CE代表：空间位置/方向/能群/权重、RNG状态/消耗、Tally Ave/RE精确比较（容差0）；仅速度/累计时间和明确wall-clock/build字段列例外。存在差异不能用统计误差放行。
- Stage2 FF、FAF（含WW）与fresh-process oracle逐轮比较receipt非时间数据、tally快照和完整事件trace，时间字段仅逐项排除；原source audit与相关CTest运行。不扩展无限矩阵。
- 出现空间/RNG差异、guard拒绝合法源、错误路径、未证实ASan插桩即停止分析，不改reference/放宽容差。以上会推翻“只修正速度/时间且不改稳态行为”的限定预期。

## 交付与回滚

保存生产/测试实际patch、关键输入/脚本与结果摘要、一个身份清单；全run原始证据留本地ignored，构建只留/tmp位置。回滚只允许按本任务patch撤销本任务行，不执行reset/checkout、不覆盖期间用户修改。最终已实施/待独立审核，W14不自行CLOSED，Stage3不启动。
