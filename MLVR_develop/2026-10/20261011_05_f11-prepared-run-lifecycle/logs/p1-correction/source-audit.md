# P1源码核查与选择（修复前330f+Stage2工作树）

- PrepareFixedSourceRun.cpp:46–89/225–227：Universe只有size，definition比较在CLEAR前。
- Universe.h:664起CDUniverse：contain cell count、两种fill索引、neighbor列表、origin/rotation和启用标志、lattice type/pitch/scope/fill/filled count、hex派生sin/cos/height是稳定几何定义。
- LocateParticle.cpp:31–172：按lattice fill或cell membership定位，调用TranUnivCoord；TranCoord.cpp:13–28/41–74：变换标志和实际矩阵/位移控制物理坐标。FindNeighborCell.cpp:121/145–149读取fill和邻居表。
- BuildNeiCellsList.cpp:6–45一次构建邻居列表，是稳定派生模型而非逐history缓存；FindLatIndex.cpp:14–20/30–123、CalcDistToLat.cpp、MonveToOriginLat.cpp读取lattice定义与hex派生几何。OverviewGeometry.cpp:28–49以fill生成cell-vector索引。
- 方案：逐字段带分隔符/长度序列化上述Universe定义；递归vector保留顺序和shape。不散列原始内存/地址，不序列化particle位置、随机介质动态状态；未验证随机/CLS/PBS/RSA/ODR/DEM/非1,2lattice显式拒绝。补充cell变换启用标志，使已记录的fill变换数值不能被旁路。
- ReadWeightWindow.cpp:279–287只验证1<WSURVN<WUPN，漏掉finite/MXSPLN；WeightWindow.h:176–193为vector<double>存储，MXSPLN语义最大分裂数；用户手册减方差.rst:73–76/117–119更明确规定WUPN>2、1<WSURVN<WUPN、MXSPLN>1。prepared采用文档严格合同WUPN>2，普通parser不改；显式记录parser/手册差异。
- WeightWindows.cpp:130–156：roulette使用min(MXSPLN*lower,survival)，split把ratio转int、随机加1，再以MXSPLN截断。因此MXSPLN必须有限、整数、>1且能装入int；派生三界必须有限严格递增，MXSPLN*lower有限。单位源和不同窗之间max(1,maxupper)/minsurvival须满足int转换加1的表示界限；这是实现类型边界而非经验阈值。一般任意权重源仍拒绝，不改native数学。
- 参数helper在Initialize前和每次Run的definition比较前调用；因此非法参数测试可直接命中WW guard，合法参数变更仍由固定definition合同拒绝。所有检查在CLEAR之前。

新增测试预定：WUPN 0/-1/NaN/Inf/1/2、WSURVN 0/-1/NaN/Inf/1/等于或超过upper；MXSPLN 0/-1/NaN/Inf/1/1.5/超int；组合3,4,5；派生非有限、舍入导致三界重合、过大比值。每项分别检查具体错误而非只看非零退出。

动态几何fixture检查：未修改Stage1程序运行合法；仅分别改变origin、rotation、lattice fill的独立输入，三个输出tally均改变，见universe-physical-effect.json，证明不是备用字段。原始输入与结果分别保存。

修复后定位：PrepareFixedSourceRun.cpp:47 Universe定义；63参数helper；132–136受限Universe；187初始化前参数检查；264每轮检查；266固定定义拒绝；291–301派生三界及表示范围检查。新模型使用Type1矩形lattice；Type2六角形的定义覆盖由上述读路径静态确认，本轮不外推六角形输运数值验收。
