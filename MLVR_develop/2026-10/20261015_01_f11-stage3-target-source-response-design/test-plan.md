# Stage 3 最小验收设计（全部未运行）

本计划与 [stage3-design.md](stage3-design.md) 一起审批。只定义实现后的门禁；本轮没有新增RMC测试、构建或输运。预设统计容差在取得结果前固定，失败不改reference、不事后放宽。测试driver调用真实生产API，不包含history/batch/descendant输运循环；抽样单测可重复调用现有源抽样函数，不复制其内核。

## 1. 基线与证据要求

- frozen oracle源码为`4810694b7a99dfc3ad7d27f7d443814f511f4829`，只在独立临时目录展开并构建；普通/Stage2对照必须来自已知HEAD和相同编译器、flags、核数据库。
- 新TARGET功能没有旧实现oracle：使用**候选源码的fresh process与persistent process配对**验证reset/角色；再用独立代数、几何段积分与解析答案验证物理，不能只以new-vs-new证明正确。
- 记录compiler/CMake/C++标准、MPI/OMP/AIS/Python状态、binary/source/data SHA256、输入、根seed/stride/history offset、actual N/D/W0、退出码、stderr。绝对路径数据身份从实际库读取；不复制或修改库。
- fresh/persistent确定性比较：同binary、同数据、同spec和effective Type2子流，N/D/W0、群/源样本、RNG、S1/S2、Ave/RE、TARGET状态与结果逐值相等。时间/构建身份是列名白名单例外，旧StatisticsTester非时间统计全部比较。Stage3-bound F与旧unbound路径比较时，仅新增policy及其对应源速度/飞行时间允许按预期修正对照物理oracle；此例外不适用于同候选源码的fresh/persistent比较，tally/RE/RNG仍精确核对。
- 首版新测试target沿用生产SOURCES与编译宏、复用现有测试globals；检查源列表中main排除一次、全部extern定义唯一、链接map无重复。serial构建成功、运行成功、数值验收分别记录。

## 2. 六组必要门禁

| 门禁 | 最小测试 | 必须观察到的结果 / 推翻条件 |
|---|---|---|
| T1 输入与绑定 | MLVR在相关block前后各一份；大小写/带空格路径；重复重叠区间；不同mesh ID；坏整数/seed/索引及显式卡冲突 | 正例解析结果一致；去重I×J；保留路径原字节；坏例在输运前明确拒绝；禁止静默退普通fixed-source |
| T2 源概率、群和权重 | 3×2×2非对称heter mesh，至少两种体积；所选群包含最低、最高和一个非相邻群；100000次实际source抽样 | 每样本处于相应完整box，g映射/单位方向/速度正确；联合概率Vi/(VTm)、空间均匀与各向同性符合下述预设界；每样本w严格1；实际prepared run另验N=D=W0，不能把纯抽样计数充当统计分母；canonical不变 |
| T3 独立解析R与代数RE | 真空定向束、等物理网格uniform/heter配对；独立非等体积heter；已知四history相关得分fixture；合法零得分 | 转换后R与独立长度/体积参考吻合；四history S1/S2/N精确；共享边际但不同相关性的RE不同；零得分不标为精确 |
| T4 完整history动态oracle | 一个小非裂变MG散射模型，analog/WW-on各500 histories；只读GDB段记录并独立盒裁剪 | 至少一个跨bin且跨所选群history；WW侧至少一次split及真实后代；全N历史包括零段/零得分；独立R/RE吻合；不满足覆盖就标未覆盖，不凭名称放行 |
| T5 生命周期及原回归 | 5-run串F,F,A,A,F（含WW OFF→ON→OFF；500/run）逐run与fresh匹配；原Stage2点源FF/FAF/AA、普通F/A/nativeWW及一个photon代表例 | TARGET在F启用、A为NotApplicable、再F无残留；模型/registry/canonical稳定；逐run非时间量严格相等；普通/未绑定TARGET的Stage2对4810694b严格回归；Stage3-bound F的速度/飞行时间修正单列物理oracle |
| T6 负例与内存安全 | 身份/role/source/CDF/概率/权重篡改、几何孔/越界、非法score与统计矩、最低物理中心E<0.5及最高群 | 静态非法在CLEAR前拒绝且旧结果不丢；执行中异常进入Failed且无成功receipt；低群/末群无越界、实际群及速度正确；原source profile行为不变 |

这里的F/F/A/A/F是测试序列，不实现生产迭代控制；Stage2原FF/FAF/AA采用已有小型验收驱动/输入，不要求重跑所有历史矩阵或20轮资源实验。新增配置/profile若发生资源、RNG、reset失败再针对性扩查。

## 3. 独立参考与事前数值标准

### T2 抽样与尺度

100000次频数单测重复调用真实生产工厂与源抽样函数，使用独立固定的Type2流；它只验证抽样，不产生统计分母D。N=D=W0及原SampleFixSource内实际群转换由T5真正prepared运行逐history核验，覆盖首末群必须有实际样本。固定Type2根seed=12345、stride=100000（若预算校验不满足则输入先拒绝，不能静默换seed）。至少100000实际history样本，取联合期望计数均≥100的选择；频数预设`|n-Np| <= 6*sqrt(Np(1-p))+1`，联合(i,g)和各边际都检验。盒内标准化坐标u∈[0,1]按4等宽区间检查同一6σ频数界，均值0.5与二阶矩1/3分别用已知方差1/12、4/45的6σ界。

方向每轴均值0、二阶矩1/3，各自6σ界分别用方差1/3、4/45；另检μ分箱和方位角分箱，单位范数误差≤1e−12。单个g/空间分量结果不能替代联合概率；确定性范围/群映射/有限性/单位权重检查无统计容差。

每个能群逐样本核对：物理中心来自独立读出的MGACE群表，内部group=G−g+1，速度按相同物理常数从中心能量独立计算，相对误差≤1e−13；绝不把物理MeV作为内部group。定向专项覆盖E<0.5及最高group，sanitizer/bounds开启且无诊断。原点源对照使用Stage2已支持的能量范围；Stage3-bound F另外测试最低/最高及一个不等于群中心的固定物理E，速度应取映射群中心而非输入E。该绑定入口的速度/相关飞行时间预期修正，须与物理oracle一致；tally/RNG仍严格验证，不把旧普通低能错误当可靠oracle。

独立直接积分源密度：每box×group×solid angle总概率应为Vi/(VTm)，总和1。用手选不等的f(i,g)核对`m E_p[f]=(1/VT)ΣViΣg f(i,g)`，容差≤1e−12相对/绝对；若f依赖方向，角积分明确用dΩ/(4π)。Q=m和角密度分别核验。该恒等式验证源/响应尺度约定，**不声称验证了绝对输运互易性或绝对伴随重要性**；用户要求的独立物理参考由T3解析响应和T4真实段积分提供。

### T3 解析响应、群相关性和零得分

- 真空内定向、单位权重点源，所选群包含源群。两个heter bins的x宽1、3，y宽2、z宽3，体积6、18 cm³；束线穿过各bin长度1、3 cm，整个TARGET严格置于有效真空cell内部。`R=(1+3)/(6+18)=1/6 cm^-2`，真实history方差0。另保留相同物理等体积grid的uniform/heter配对，不能用uniform伪造非等体积。
- 选另一条仍在有效域内但束不经过的TARGET作为合法零得分；R=0、hasRE=false、ZERO_SCORE。未选源群亦可作群零得分正例。
- 原始double与高精度参考R预设`|diff| <= 1e−13 + 1e−12*|reference|`。数学零方差的计算RE允许预设上界`sqrt(64*epsilon(long double)/(N-1))`；此项只用于解析oracle，fresh/persistent仍逐值相等。文本比较使用实际输出最后一位的半个单位，不把打印舍入误判物理偏差。
- 代数fixture使用两空间bin V=[1,3]、两群，heter ci=1、α=[1/4,3/4]，四history的`[bin1g1,bin1g2,bin2g1,bin2g2]`依次：`[4,4,0,0]`、`[0,0,4,4]`、`[4,0,4,0]`、`[0,0,0,0]`。独立手算rh=[2,6,4,0]、S1=12、S2=56、N=4、R=3、RE=sqrt(5/27)。整数/可精确表示的矩严格相等，RE绝对差≤1e−14。首history由两份后代score先累成上述向量再调用生产SumUpTally，证明不能各后代平方。
- 保持各bin边际矩不变，改变同history配对得到rh=[1,3]与[4,0]；两者mean=2，RE分别0.5和1。若新统计给相同RE，说明丢失跨bin/群相关性，失败。
- 对上述同一物理fixture构造uniform原score（相应乘Vi）再聚合，应同结果。禁止用各bin RE合成参考。

### T4 只读段记录

在真实 `ScoreMeshTallyByTL` 入口记录**原始**段长、段起点、方向、权重、内部群号；源history开始/结束断点建立完整N行清单，所有split后代继承当前rootHistory。不能取已按网格体积处理的MeshTrack长度，也不能调用被测转换helper当参考。独立脚本从原始几何盒边界做线段裁剪，累加w×真实bin内长度/(VT)，再按history独立形成S1/S2/R/RE；群映射依据独立读出的MGACE表。

固定500历史小模型，独立积分使用高精度算术；moment预设相对容差1e−10、绝对容差1e−12（S1与S2各自量纲），R相同。RE用moment容差传播成区间，S1正且不靠近零时可要求绝对1e−8；近零方差只按事前moment区间验收，不事后扩大RE容差。若区间过宽无法判定，结论为未确定，改善oracle精度而非放行。

GDB必须只读，不改粒子/RNG，不重新抽样；traced/untraced同binary同seed非时间输出逐值相等。已有PTRAC在prepared profile中拒绝，且阶段0存在空输出边界，故不以PTRAC替代。GDB缺失/某history无记录/无实际cross-group或split均标未覆盖；不能退化成Ave除体积“独立参考”。

## 4. 负例最小集合

1. 解析：缺必填key、重复key、混合其它计算模式block、坏元组/闭区间、空TARGET、mesh不存在、G+1越界、整数溢出、偶seed/总stride周期越界、同时出现POPULATION/SEED/两种ADJOINT、静态WW/WWE/WWN；顺序互换也拒绝。
2. 绑定：未初始化/首run后/重复绑定、错owner、target或model内容改动、wrongrole或外部source对象、伪造profile/identity。拒绝前后旧tally/receipt和RNG位置相同。
3. 源：改变fraction或bias、WEIGHT-variable、相关/依赖分布、CELL/transform、CDF尾/单调性、伪造物理中心。检测必须验证实物结构而非字符串。
4. 几何：有效内部真空正例；半箱外域、importance0、隐藏孔/其它rootcell交叠、无法证明的复杂曲面、跨cell箱、边界裕量不足（含距面小于实际GetZeroSenseDistance）、绑定后sense容差被修改均拒绝，不裁剪或重采样。
5. 统计：r/score NaN/Inf/负值、累计溢出、N/D/W0不等、N=0、N=1、S1=0但S2>0、超过预定容差的负delta失败；[-tau,0)夹0且记录标志，微小正delta不随意归零。代数异常直接用合法测试接口注入，不对生产对象使用friend或绕过生命周期的token。
6. 运行异常：合法preflight后注入非单位实际权重/定位异常，仅用于错误路径验收；断言Failed、无成功receipt、不得续跑或复用已消费RNG段。生产验证不允许这种注入入口；测试可用只读验证器fixture直接检错或debugger测试故障注入，故障运行与只读物理oracle明确分开。

## 5. 拟执行命令及产物（审批后才编写driver并运行）

新目录计划包含 `CMakeLists.txt`、`driver.cpp`、`compare.py`，输入为`fixtures/analytic_uniform.inp`、`analytic_heter.inp`、`scatter_ww.inp`和`history-oracle.json`。新driver选项拟定为`--case parser|sampling|analytic|history|sequence|negative`；CTest名统一`mlvr_target_*`。解析/负例变体生成到测试临时目录，不产生大量入库文件。

```bash
# 独立候选构建；最终编译器/依赖参数需与fresh baseline完全一致并归档
cmake -S RMC -B /tmp/f11-stage3-candidate-build \
  -Dmpi=OFF -Dopenmp=OFF -Dais=OFF -Dpythonapi=OFF \
  -Dtest=ON -DO0=ON -Dloadmodules=OFF -DCMAKE_BUILD_TYPE=Debug
cmake --build /tmp/f11-stage3-candidate-build --target RMC RMCPreparedLifecycle RMCMLVRTarget -j 2
ctest --test-dir /tmp/f11-stage3-candidate-build -R '^mlvr_target_' --output-on-failure
ctest --test-dir /tmp/f11-stage3-candidate-build -R '^(fixed_source_adjoint|prepared_source_weight_audit)$' --output-on-failure
# 新比较器：逐run非时间严格匹配 + 独立解析/段积分检查；参数名作为实现合同
python3 RMC/tests/mlvr_target/compare.py --baseline /tmp/f11-stage3-results/baseline \
  --candidate /tmp/f11-stage3-results/candidate --output /tmp/f11-stage3-results/comparison.json
```

运行前检查实际CTest清单，匹配为空不能记通过；普通F/nativeWW/photon代表例沿现有测试命令，实际名称按当时`ctest -N`记录。不填虚构已执行命令/退出码。baseline在git archive导出的独立源码目录按同配置编译；数据库路径和依赖按当前实际环境绑定，不擅自拉库/改库。

GDB段脚本及sanitizer专项在实施档案中保存命令/真实输出，完整插桩涉及的新源、统计及调用单元，明确其它单元是否复用。Stage2未验证的全程序sanitizer、Windows、MPI/OMP、任意源或裂变能力不因Stage3通过而自动扩大。

最终只入库README §4、设计/测试摘要、实际补丁（含新增文件）、一份源码/证据哈希清单和判定结果；逐run输入副本/stdout/stderr/debugger段记录留本地并给路径。完成后停止，交独立审查，不启动Stage4。
