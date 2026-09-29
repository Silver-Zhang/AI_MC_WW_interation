# F11 Persistent Session Minimal Experiments E0–E4

日期：2026-09-29 · 模式 **C** · 当前关口：**设计完成，实验补丁待批准**。

## 1. 目标与范围

通过 E0 时间分解、E1 F→F、E2 F→A→F、E3 WW 更新、E4 tally reset/内存提取，检验最小同进程执行合同。限定 standard MGACE、中子固定源、Cartesian Type=1/Energy=-1/Normalize=1、native track-mesh WW、Linux 串行。

**物理解释**：同进程的第二轮仍必须代表一个独立的 MC 样本集。复用几何/核数据不能带入上一轮历史、统计矩、归一化分母或伴随角色。改变 WW 后应由真实粒子轨迹读到新窗；内存 Ave/RE 应在最终归一化完成后读取。fresh-process 对照负责检验这些关系，程序正常退出不足以证明成立。

按用户最新任务只写本目录；原始要求见 [原文](logs/user_task_original.txt)。正式 F11 实现与架构选择不在范围内。

## 2. 做法与证据

- [实验报告](F11_Persistent_Session_Minimal_Experiments.md)：14 项报告内容及逐项 BLOCKED 状态。
- [预先固定的实验协议](logs/experiment-plan-frozen.md)：算例、seed、N、WW、reset 合同、exact oracle 和时间质量门；未运行后调参。
- [Proposed Experimental Patch](Proposed_Experimental_Patch.md)：P0 观测 + P1 显式实验入口开关，附可审查 diff；**未应用**。
- [开始仓库状态](logs/repository-state-start.txt)、[结束仓库状态](logs/repository-state-end.txt)、[源码定位](logs/source-navigation.txt)、[数据来源哈希](logs/fixture-provenance.json)。
- [静态自检实际输出](logs/preparation-check.txt)：仅检查 diff 上下文、宏关闭后的文本等价及基线哈希，不是编译/实验验证。
- [机器可读汇总](logs/experiment-summary.json) 与 `verification/E0/` 至 `verification/E4/` 的独立状态记录。

当前调用边界确认：`CalcFixedSource` 每次调用完整 `InitiateAll`；现有 timer 不能给出要求的纯 history-loop 分段。为复用真实 loop，需要审批局部源码插桩及初始化 gate。定位后依用户第4、7、16节停止，未构建 binary，未执行任何 RMC run/fresh oracle。

## 3. 决策

| 变更卡 | 内容 |
|---|---|
| 问题与风险 | 现有入口重复全初始化；直接跳过又可能漏清状态。计时/查窗需要内部观测 |
| 拟改动对象 | 批准后仅在本目录私有源码快照中修改 8 个源文件，另建 test driver；详见提案 |
| 不改什么 | 共享 RMC、基准结果、正式 F11 API、STATUS/INDEX/KB |
| 预期因果链 | 局部观测 + 明示 reset/rebuild → 原 history loop → fresh exact comparison → 有限范围的实验结论 |
| 验证 | 先检查 observer 对 fresh 结果无扰动，再按 frozen gates 检查 E0–E4；失败保留证据，不即时修复 |
| 回滚 | 实验修改限定任务内私有快照/build；共享仓库无须回滚 |

**已获授权**：只读审查、协议/patch 设计、任务内文档和验证脚本。

**待人拍板**：是否批准提案中的 P0 probes、P1 gate 及任务内 test driver。此记录不代替批准。

**人类理解确认（模式 C）**：尚未取得。待确认“PASS 只说明声明的 test-only CLEAR/REBUILD 合同满足本模型的 oracle，并不代表当前生产入口已支持 persistent，也不代表架构已选定”。

## 4. 结论与边界

**结论**：E0–E4 全部 **BLOCKED / not run**。遇到用户定义的源码修改停止点，已交付具体实验补丁提案，等待决定；没有动态 PASS/FAIL、启动耗时占比或可复用状态的实验证明。

**证据**：本基线的入口/timer/WW/tally 源码定位、未应用 patch、静态自检及仓库前后状态。动态结果均为空，不使用旧档案结果充当本任务 oracle。

**结果解释**：BLOCKED 表示所选实验方法缺少批准的入口/观测改动，不能据此判断 persistent 可行或不可行。共享物理结论、基准和设计冻结状态均未变更。

**未覆盖到的验证**：编译/链接、全部 E0–E4、fresh oracle、性能/开销、内存 vs 文本、G+1 实际提取；MPI/OpenMP/CE/photon 等本来就在范围外。当前只固定预定 N/seed，binary/compiler/dependency/build flags 尚无本次构建记录；无 ML 训练配置。

## 5. 过程

1. 立项：采用 C 模式；保存任务原文和 root/RMC 状态。用户固定目录并禁止公共台账更新，因此手工建档，未调用会更新 INDEX 的 `new_task.sh`。
2. 设计：参考两份已完成审查，抽查当前源码；固定 E0–E4 判据和 H2O 派生小模型，生成未应用 patch。
3. 人拍板：**待批准，停在此步**。
4. 实施+自验：只完成任务内提案与静态文件自检；生产源码修改和数值实验未实施。`changes.diff` 是实际 RMC diff（预期为空），不是拟议 patch。
5. 归档：本目录交付待审核；依用户第15节暂不更新 STATUS/INDEX/KB，未 commit/push，未切分支/reset/clean。
