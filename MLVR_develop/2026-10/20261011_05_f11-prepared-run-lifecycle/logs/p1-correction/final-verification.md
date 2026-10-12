# P1修复最终自验（2026-10-12）

**READY FOR INDEPENDENT RE-REVIEW。** 两个P1已修复并通过本轮自验；建议提交Claude最终复核。Task07原NEEDS CORRECTION报告保留，不能把本次自验代写为独立验收。

| 用户验收问题 | 回答与证据 |
|---|---|
| 1. Universe定义有效保护？ | 是，限定确定性CSG/矩形/六角lattice的稳定语义字段；填充、成员、邻居、变换、pitch/scope/hex派生数据逐字段序列化。真实矩形fill+变换模型2个Forward均等fresh；4个模型内容mutation均在CLEAR前命中definition guard，Universe数量始终4。随机/未覆盖Universe显式拒绝。见source-audit.md、logs/universe-01、logs/p1-negative-01。 |
| 2. WW参数校验完整？ | 对本次原生合同完整：WUPN>2、1<WSURVN<WUPN、MXSPLN为[2,INT_MAX]整数且三者有限；派生三界有限严格有序，MXSPLN×lower有限，单位源/跨窗ratio满足native int转换+1表示范围。普通parser/公式不变。 |
| 3. 负例命中生产guard？ | 是，51/51：21个绑定前参数负例、21个首轮后参数负例、4个派生负例、4个Universe mutation和1个随机Universe拒绝。WW错误明确为WUPN/WSURVN/MXSPLN或派生界限，不以definition拒绝代替。只读GDB证实绑定前InitializeModel/Prepare/CLEAR/Execute/source全0；首轮后维持1/1/1/1/100，只有1份receipt、state_unchanged=1。 |
| 4. 原G0/Gate1–7保持？ | 是，当前串行重编译/链接694共同TU选项相同、13单例各一次；10CTest、123普通比较、34原half-run、66原负例重新通过。CMake/macros未改，旧testOFF/不支持宏注册证据保留，本次未重跑这些配置的数值测试。 |
| 5. FF/FAF/AA/WW与fresh等价？ | 是，原34/34 +新增Universe2/2，共36对，每侧18000源历史，物理容差0。原34条全事件trace摘要与gates-04也完全相同。20轮复用预热后RSS+16KiB，FD测量19恒定；实际查窗三界、split/roulette/bank继续逐事件对照。 |
| 6. 普通RMC行为保持？ | 已测试范围保持，123/123确定性比较（包含Forward/Adjoint/nativeWW及已有其他粒子/RNG代表分支），10/10CTest。原623行core不变。本轮没有普通parser或输运函数修改。 |
| 7. 仍有验收阻塞问题？ | 本轮限定目标内未发现剩余P1或失败门禁；仍需独立最终复核。六角lattice定义字段已静态覆盖，但本轮新增动态Universe只验证矩形模型，不宣称一般几何/材料都已数值验证。原非裂变/串行/单位源、W11/W12/W13、legacy FOM/HDF等限制保留。 |
| 8. 建议Claude复核？ | 是，先看correction.diff、source-audit.md和新增负例命中证据，再查36run/普通回归及旧证据保护。此处不启动Claude、不进入Stage3。 |

## 实际代码范围与身份

本轮仅`src/PrepareFixedSourceRun.cpp`与`tests/prepared_fixed_source_lifecycle/driver.cpp`，属于原批准29文件。根main/19abdc943e2c0bf404cfd04d6c27f485e540bb4e；RMC Neural_Network_WW_Iteration/330f091eb0296e0d0124237ba7d9a22b81aee852。RMC改动仍未提交；本次未commit/push/reset/checkout/clean。修复前完整源码、全部修改SHA/已跟踪及新增补丁分别见pre-fix-source.tar.gz和pre-fix-manifest.json/pre-fix-*.diff。

新增数据、运行命令、cwd、stdout/stderr、真实退出码、receipt、GDB源/得分/RNG/原始矩/WW轨迹均保存于本目录。gdb自身exit=0与被测负例inferior_exit=2分别记录，不混用。当前binary/source/build/database身份见final-manifest.json，本轮交付文件哈希见delivery-manifest.json（Task05旧evidence-manifest/artifact-manifest仍是10月11日历史快照）；旧gates-04、Task07原报告、冻结04及原logs共11551个文件SHA保持不变。原核数据库SHA与Stage1冻结记录相同。

## 复现入口

```bash
# 完整configure/build命令：configure-01/command.json 与 build-01/command.json
# 验证脚本使用任务私有 /tmp/20261012-f11-stage2-p1；重跑请新建标签/目录，不覆盖本轮数据。
python3 tools/run_all_lifecycle.py NEW_LABEL
python3 tools/run_lifecycle.py universe --label NEW_UNIVERSE_LABEL --trace
python3 tools/run_lifecycle.py universe --label NEW_UNIVERSE_LABEL --trace --fresh
python3 tools/compare_lifecycle.py universe --label NEW_UNIVERSE_LABEL
python3 tools/run_p1_negatives.py NEW_NEGATIVE_LABEL
```

上述相对tools路径以本p1-correction目录为cwd。普通回归、CTest、导出比较等每项完整argv见各`*-command/command.json`，汇总见regression-command-results.json。逐轮数值见run-results.md及regression-results.json。增量correction.diff和Task05完整changes.diff/new-files.diff均通过git apply --check，未实际apply回工作树。

## 边界

参数合同采用现有用户手册严格值（WUPN>2），原parser只检查WUPN>1及survival关系；MXSPLN虽以double存储，实际用于整数粒子数，其整数和int表示检查属于prepared入口合同。未修改普通parser，也未开发新的split/roulette算法。比例表示检查覆盖单位源及现有窗界间跳转，不构成对任意增权物理或任意源的普遍保证；这些仍受Stage2原profile与验证范围限制。

旧StatisticsTester的process累计时间/FOM继续标为非本轮指标。FF全部实际PDF（63/73 bins）与HDF（2519/2859 datasets）通过，例外仍限原七个统计时间成员/五种HDF时间字段，没有整体跳过统计器。测试开销计入测量耗时，不据此宣称性能收益。

没有修改任何MC输运数学、Type2 RNG、旧HDF writer、W11/W12/W13、核数据库、reference或Task07历史结论。无Stage3开发。
