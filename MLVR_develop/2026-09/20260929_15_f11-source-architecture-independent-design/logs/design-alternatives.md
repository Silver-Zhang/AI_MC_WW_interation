# 独立架构方案比较记录

本文件形成于源码阅读报告之后；其完成顺序见source-report-completed.txt。方案选择来自实际owner/call graph，不以Task 13 driver为模板。

| 方案 | 源码适配 | 改动代价 | 结论 |
|---|---|---|---|
| A：新src/MLVR subsystem与session/controller层 | 需要封装RunCalculation值参数与多个global；容易出现第二组owner | 较多public API/ownership迁移，可能重复fixed-source loop | v1不推荐；未来多执行后端才重新评估 |
| B：现有cpp内直接塞全部工作流 | 能复用owner，但CalcFixedSource已混合init/transport/output | 文件少，但状态和IPC依赖集中到大函数 | 可实现，审查和测试边界较弱 |
| C：现有类负责自身数据，六个新配置/实现文件 | 顺着CalMode分发、FixedSource run state、Tally/WW真实owner | 必要的生命周期抽取，新的IPC逻辑独立 | 推荐；唯一history/batch loop |

## 关键选择及依据

- iteration在CDCalMode::CalcMLVR内：已有RunCalculation分发FixedSource（RMC/src/RunCalculation.cpp:83-89），一次调用的局部owner存活（RMC/src/RunCalculation.cpp:6-13）。
- CDFixedSource持一个MLVRConfig值：现有N、role、bank/run配置均在此；OController实为hash/geometry控制（RMC/src/Control/Control.h:18-67）。配置值不承担调度。
- 拆CalcFixedSource而非原样重复调用：init含材料转换/tally注册（RMC/src/InitiateAll.cpp:130-156），transport本身已完整（RMC/src/CalcFixedSource.cpp:97-719）。
- 构造现有source而非新增类型：XYZ+discrete/bin已齐备（RMC/src/SourceDistribution.h:30-36；RMC/src/CheckAndInitiateParameters.cpp:65-72）。
- 独立Field文件而非改旧HDF5schema：MeshTally输出三维值，Result另有Mean/Re但缺全契约（RMC/src/MeshTallyHDF5.cpp:82-99；RMC/src/OutputTallyh5.cpp:52-83）。
- WW校验后直接装到runtime owner而非重读parser：运行时读取三界；ProcessWeightWindow已经生成三界（RMC/src/WeightWindows.cpp:45-101）。
- Field用显式volume converter：uniform track返回原始长度，heter可归一（RMC/src/MeshFun.cpp:296-304；RMC/src/MeshFun.cpp:474-484）。不改普通scorer基准。

## 没有选择的扩展

不创建general response、source proxy、model复制器、dynamic callback bus；不增加new batch输入；不以重建整个model替代owner reset；不把MC RE复制到ReconstructedField。需要人工确认的物理/统计口径见设计§15及Independent recommendation。
