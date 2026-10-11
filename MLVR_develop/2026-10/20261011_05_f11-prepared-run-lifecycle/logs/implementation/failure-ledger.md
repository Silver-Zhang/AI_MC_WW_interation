# 失败、修正与未修复边界

原始stdout/stderr/退出码均保留；本表不是用成功记录覆盖失败。最终验收只使用README §2所列的最终批次。

| 证据 | 事实及处理 |
|---|---|
| baseline-cases/ordinary-weight-variable | 未修改parser拒绝WEIGHT=D1（exit=1）；没有修改parser或把它算成输运正例。普通WEIGHT=2完成确定性回归；WEIGHT绑定前置拒绝与实际audit单测分列。 |
| stage2-build-01 | 非AIS构建引用AIS专用particle字段，编译失败；在owner reset内按原宏保护。 |
| stage2-build-07 | 输出FD校验编辑中出现pointer/bool比较，编译失败；修正为同一指针且FD有效且全部输出对象身份一致。 |
| pilot-01至05、smoke-01/02、stage2-build-02至09 | 初始源POINT存储误认p_vPosition，改为真实p_vPoints；源累计计数误当live bank，结束改查N；未启用统计器调用ReSize会新建空PDF存储，改为只对已启用bin调用。私有构建副本mtime复制曾导致旧driver对象未重编译，随后改用内容比较+copyfile，最终manifest逐源核对构建副本。 |
| implementation/ff-bt、baseline-scheck-energy | 能群cell SCHECK崩溃在未修改330f baseline复现。TallyCellByTL.cpp不在授权范围，未修复；prepared拒绝该组合。总通量cell诊断+全群mesh仍执行完整统计门禁。W13单独登记。GDB外层exit=0不代表SIGSEGV的inferior成功。 |
| gates-01 | GDB对typedef指针取element.sizeof时读成指针宽度，int数组误读尾部；WW的const int引用未解引用。观察器修正后重新采集；该批不作验收。 |
| gates-01/02、observer-termination.json | 高频FinishBreakpoint造成调试器长时开销，保留超时/主动终止证据。最终改用采样返回固定位置和实际WW动作入口，保留每次采样、查询及三界数据，没有降低N或抽查事件。 |
| observer-speed-01 | 在Finish.stop内删除当前断点导致GDB本身SIGSEGV，弃用该实现；不能解释为RMC崩溃。observer-speed-02与最终批次正常。 |
| ordinary-comparison-final | 122/123差异只有旧FoMBehaviourCheck的墙钟派生值。比较器移植遗漏了原test-plan §3.1已经列明的两项FOM check，补齐精确路径后重比较；最终ordinary-comparison-final-03为123/123。物理容差仍0。 |
| gates-03/ww和faf-ww/comparison-before-capacity-classification.json | 物理逐项已相等，但比较器将不同WW工作负载所需bank capacity增长当作污染。按原Gate6判据改为始终检查live bank为空/哨兵、身份/FD稳定；固定负载20轮warmup后capacity稳定及4MiB限制仍严格执行。保留原失败，未放宽物理容差或RSS门槛。 |
| exports-01 | 旧HDF writer不是完整覆盖式输出：第二次导出多10个旧条件字段，部分table保留旧值；本次实际生成的63/73个PDF均等fresh。仅测试driver清自己的旧Tally输出组，保持同一句柄，随后全HDF逐项比较；生产writer和统计公式未改。 |
| cutoffs | 额外检查发现Forward未启用的伴随max字段为spec的30而fresh默认20；实际输运已等价，但不符合恢复默认值约定。在已批准SetPreparedRun内恢复20，Adjoint从本次30MeV定位到群1；最终gates-04已包含字段级严格核对。 |
| implementation/g0-omp | 原CMake不允许OMP-on/MPI-off；不是prepared特有错误。改用既有允许的MPI+OMP配置检查target缺席。MPI/AIS/Python配置均未误注册prepared target，但未做这些配置的多轮数值验收。 |

未修复事项：W13旧scorer、旧writer完整覆盖语义均未修改生产实现；严格prepared源白名单外、非零裂变产生项和并行等仍未开放。不改reference、核数据库、冻结04或Task06原独立审查结论。
