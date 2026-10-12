# 定向源码依据与预设验收

修复前完整源码和SHA见本地manifest的before；当前RMC HEAD为330f091e，Stage2为未提交工作树。不得把HEAD视为已包含Stage2。

- Constants.h:197：INFINITY_ENERGY=1e22，有限double。
- WeightWindow.h构造：四类粒子的起始边界均为0；ReadWeightWindow.cpp:56–82读取WWE，419–427追加有限哨兵；ProcessWeightWindow按mesh-major/energy-minor保存B−1区间。
- GlobeFun.h:141–151：首界及以下返回0，内部等值归右，末界及以上返回B−1。旧WeightWindows.cpp:45–66只在大于末界时纠正，等值越界。
- 旧PrepareFixedSourceRun.cpp:63–75只校验WWP，187、264调用；286提前下标访问energy outer。旧Install:310同样无自身形状防线。
- MeshFun.cpp:133–135的GetTotMeshNum仅返回p_nTotMeshNum，因此const owner验证读取该成员等价。
- MCNP reader不追加同一native哨兵；本轮不对普通MCNP强加native端点合同。

选择：增加`size_t CDWeightWindow::ValidatePreparedNativeDefinition() const`，不改数据布局。验证Cartesian native、正mesh数、外层neutron存在、2≤B≤INT_MAX、全部有限且严格递增、首0/末INFINITY_ENERGY、WWP形状及既有三个标量合同、int计数容量、已安装mesh×energy维度。CLEAR只清值不改形状，故不要求已清零的旧窗为正；新lower的数值仍走原Run门禁。

绑定时、Run的definition fingerprint/CLEAR之前、enabled Install的任何neutron下标及状态修改之前调用同一owner方法。未声明WW且OFF仍按原profile运行。Run使用owner返回flat数避免独立下标；Install独立复核，不能依赖caller。

共享查询仅补容器大小、有限查询能量和串行已安装维度检查，并将GetIntpltPos结果上限夹到B−2。不改通用算法、split/roulette、RNG或模型数学。低于首界仍选0；内部等值仍选右；末界等值/更高有限值均选B−2。MPI分支保持既有路径，未扩大prepared支持。原全局energy引用改为同一owner自身表，与被查询的mesh data一致；正常全局OWeightWindow调用不变。

预设判据：12个有限查询（包含nextafter两侧）精确返回预先写定的三个权重界，3个NaN/±Inf拒绝。owner级不冒充MC源能量1e22测试。26种容器/数值/形状错误分别绑定前、第一轮F后、独立Install，GDB必须看到Validate生产抛错；前两类CLEAR/source计数为0/0、1/100，旧状态不变，receipt0/1。独立Install拒绝也不改模式/截断权重。已有标量WW/Universe负例继续执行。FF/FAF/AA/WW/FAFWW及20-run资源测试、普通单窗/多窗WW均物理零容差，例外沿用Task05封闭的时间字段清单，不豁免整个StatisticsTester。多窗独立检查每次实际三界，必须观察真实split、roulette。

授权内实际文件：PrepareFixedSourceRun.cpp（调用门禁）、WeightWindows.cpp（owner实现和lookup边界）、WeightWindow.h（声明）、driver.cpp（仅公开容器/生产API测试）。无额外生产文件。

初始化实际会遍历neutron至electron的mesh容器槽位（旧WeightWindows.cpp:184–207）。因此installed mesh outer必须保留四槽，且受限neutron入口禁止其他粒子存在非空窗；新增outer-two/other-particle负例。此检查仍归同一owner，不修改InitiateWeightWindow。

## 最终工作树位置

| 文件/位置 | 作用 |
|---|---|
| WeightWindow.h:64–70 | owner校验声明；返回lower元素数 |
| WeightWindows.cpp:48–80 | 真实lookup；第60行夹取B−2，有限能量和形状guard |
| WeightWindows.cpp:307–347 | 统一topology/energy/WWP/installed-shape校验 |
| WeightWindows.cpp:354–371 | 独立Install第357行先验证，随后才修改状态及访问neutron |
| PrepareFixedSourceRun.cpp:174 | 初始化模型前bind校验 |
| PrepareFixedSourceRun.cpp:251–254 | Run在fingerprint与CLEAR之前校验 |
| PrepareFixedSourceRun.cpp:273–275 | 使用validated lower count/WWP，保留既有派生值验证 |
| driver.cpp | 公开容器异常注入、独立Install、生产lookup 15项、多窗spec；没有复制transport loop |

上述位置对应最终未提交工作树，不是330f091e本身的文件内容。对应源码SHA在manifest/protection记录。共享MPI分支未新做编译/运行验收；非native MCNP不会被此prepared方法接纳，也未对其普通parser追加1e22约束。
