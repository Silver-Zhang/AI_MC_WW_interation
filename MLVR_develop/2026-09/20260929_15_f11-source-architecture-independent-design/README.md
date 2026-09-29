# F11 Source-Level Architecture Analysis and Independent Design

| 项目 | 内容 |
|---|---|
| 日期 | 2026-09-29 |
| 任务模式 | C：源码分析、物理/统计边界与独立设计 |
| 状态 | 已完成分析与设计；建议待人工拍板，未实现 |
| RMC基线 | 5cfb0f771d0c5a2127c90d57e51ce672a4e3b616 |

## 1. 目标与范围

按用户冻结的F11 v1流程，先读当前RMC源码，再独立提出production架构。仅在本目录保存产物；不修改RMC/AIMC/STATUS/INDEX/KB/Physics Guide，不commit/push。原始任务原样保存在[logs/user_task_original.txt](logs/user_task_original.txt)。

物理解释：TARGET先确定响应对空间/群通量的权重，再形成与之对应的伴随source概率。一次source history的全部descendants共同形成一次统计观察；不同bins的响应误差需要其共同history计分，不能拼接各bin的RE。跨half-run保留静态模型，清理运行统计与mode派生数据。

## 2. 做法与证据

先形成[源码阅读报告](RMC_F11_Source_Reading_Report.md)，再形成[独立架构设计](F11_Independent_Code_Architecture_Design.md)。源码报告覆盖A–H链；设计包含实际/拟新增函数边界、输入卡、TARGET、Field/WW、P1–P9、T1–T12，末尾Independent recommendation为七项简要建议。

- [当前调用图](logs/source-call-graph.md)
- [完整状态所有权与reset表](logs/source-state-ownership.md)
- [逐项源码证据索引](logs/source-evidence-index.md)及source-evidence-excerpts.txt
- [方案比较](logs/design-alternatives.md)
- [仓库起始状态](logs/repository-state.txt)、结束状态repository-state-end.txt
- [文档/写入范围检查](logs/validation.txt)、validation.json、source-reference-check.json

Task 13/14仅用于CLEAR/SET/REBUILD的动态证据，不使用其driver作生产模板。本轮只做只读源码与文档自检，没有编译或新增输运数据。空changes.diff表示RMC没有改动，不是缺失补丁。

## 3. 决策

用户已明确授权源码分析和设计；未授权实现。模式C的人类理解确认以本次明确需求为准：先读代码，再提独立方案，最后停在设计。**没有把AI建议写成人已批准的生产选择。**

推荐现有owner加少量新增实现文件的混合方案；需后续拍板的内容集中在设计§15及Independent recommendation：代码拆分边界；TARGET的空间体积平均/群积分求和；等权1、Type2、T12前拒绝fissile等首版边界；T_MC/FOM与交换文件契约。

用户明确禁止公共状态更新，优先于常规归档同步要求；new_task.sh会写INDEX，因此本任务手工建立指定目录。未调用自动台账更新；不读取或合并并行Task 16的设计。

## 4. 结论与边界

**结论**：推荐iteration放在新增CDCalMode::CalcMLVR，一次RunCalculation内保留实际owners；CalcFixedSource拆出full init、唯一execute loop与finalize；prepare由各owner清理/设置/重建。source、tally、WW沿用现有表示；新增的主要边界是简单TARGET转换、history级response统计、Field交换与外部执行。

**新增源码发现**：uniform Cartesian track-length路径返回原始长度，而heter路径按Normalize选择除体积；Field不能一律把Ave直接标成flux density。设计规定显式c_i转换，并以非单位体积的等几何uniform/heter测试作门禁。此项是源码推导，尚未动态验证，也未按本任务范围修复或写入KB。

**边界**：已有H2O repeated-run证据不覆盖nonzero adjoint fission。设计要求T12通过前不开放general MG adjoint/fissile声明。任意starting weights也未获当前denominator/RE路径支持；首版建议等权1并明确记录实际N、D、total starting weight。

**结果解释/未覆盖验证**：没有生产实现、性能提速结论或新的MC统计结果；P1–P9/T1–T12是实施计划。没有CE/coupled/MPI/OMP persistent、任意response、mapping或restart/recovery设计。所有归一化与TARGET的新增口径仍待人类确认。

## 5. 过程

1. 读取工作区上下文与本次任务，保存原文和root/RMC/AIMC状态；仅建立Task 15目录。
2. 按A–H定位读取源码，对照Task 13 reset契约和Task 14动态证据边界，先写阅读报告/调用图/状态表（时间记录source-report-completed.txt）。
3. 基于实际owner独立比较A/B/C，写推荐call graph、精确拆分范围、输入/统计/协议、阶段与门禁。
4. 核查行号范围与源码SHA-256、交付物/本地链接、原文一致性、公共文件起止hash及工作树；原始检查输出保存在logs。只读source没有code diff；不自动进入实施。
