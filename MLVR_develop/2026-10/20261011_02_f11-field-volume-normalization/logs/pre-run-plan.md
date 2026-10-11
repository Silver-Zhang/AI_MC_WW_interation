# 运行前方案与判据（2026-10-11，正式数值运行前写入）
目的：验伪 KB04 §7 的候选表，限阶段0。已获用户直接执行授权。
两条真空束 x=-0.5→5，方向(1,0,0)，源权重1，能量0.6 MeV；y=1命中、y=3不命中，z=1。水材料位于y>4，真实standard MGACE加载但轨迹不碰撞。独立参考来自完整PTRAC源/出口记录及独立线段-盒裁剪，无随机核数据库修改。
网格 x=[0,2,4], y=z=[0,2]，每bin V=8 cm³，命中历史每bin长2 cm。N=100包括所有零得分历史；命中数m从实际完整PTRAC计数。phi_ref=m*2/(100*8)，而未除体积的源均值L_ref=m*2/100。RE_ref=sqrt((100/m-1)/99)。未使用Ave构造参考。
候选可被推翻：uniform N0/N1预测Ave=L_ref；heter N0预测L_ref、N1预测phi_ref。若uniform N1匹配phi_ref，则否定候选uniform 1/V；若heter N1匹配L_ref，则否定候选heter 1。若两者均不匹配则不得放行，调查路径和分母，不改源码。
文本Ave常规%e打印：采用abs(diff)<=5e-12+6e-6*abs(expected)；RE采用绝对6e-5（须在源码确认打印位数不足时重新设计而非事后放宽）；零值必须打印0。所有组、所有bin均检验；初始与结束记录数量、方向、权重、能群、无碰撞、同种子四例源抽样一致；运行出口0、实际历史100。Normalize=0仅诊断。
运行时使用GDB只读断点验证被调用的两条Calc函数、p_bUseVol与ProcessTally分母。GDB不改二进制和源码，单独目录执行，正式四例以普通运行输出为准。
Adjoint仅核查共用链，存在实质差异时才补最小验证。不改冻结规则，不实现F11，不进入阶段1。

打印精度检查：默认MESHTALLY小数4位，正式输入显式PRINT MESHTALLY=8；事前容差保持不变，不运行后放宽。

Pilot输入语法修正：RPP不属于SURFACE卡支持类型，改为完全等价的六平面盒；物理几何/判据/容差不变，失败原始日志保留logs/pilot。后续显式-d锁定数据库路径。

Pilot2仅输入校验失败：RMC要求POPULATION>100（ReadFixedSourceBlock.cpp:55）。正式N改为200，phi_ref=m*2/(200*8), L_ref=m*2/200, RE_ref=sqrt((200/m-1)/199)；包括所有零得分历史，容差不变，改动发生在任何有效输运结果之前。

Pilot3仅PRINT解析失败：PRINT中的MESHTALLY 8不使用等号（ReadPrintBlock.cpp:20），正式输入语法修正；未产生输运结果，不改变物理设置和容差。

数据获取调整（普通四例后、独立比较前）：logs/formal四例退出0但PTRAC为空，无法作为oracle；改用只读GDB函数入口记录SOURCE及实际SEGMENT（段起点/方向/权重/群/真实飞行长度），在相同输入/种子下重跑并核对Tally逐字节一致。不修改源码/内存/二进制；仍用独立线段-盒裁剪计算参考，不使用Ave回推。判据/容差不变。空PTRAC原因只作覆盖限制，不扩成修复任务。

GDB pilot仅调试记录适配：printf传递C++ double& dTracklength未解引用，得到无效值（gdb-pilot原样保留，不用于参考）；改在TallyByTL入口记录按值double dTrackLen（尚未进入网格切段/体积处理）。这个量是送入计分的真实物理输运长度，无Ave或网格score依赖。
