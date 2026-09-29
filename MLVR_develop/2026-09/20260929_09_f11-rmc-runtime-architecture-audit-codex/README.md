# F11 前置：RMC 运行生命周期与可复用执行能力独立审查

模式：**C（物理/统计接口边界审查）**。日期：2026-09-29。状态：**独立源码报告完成，等待两个审查统一归档；未决定 F11 架构，未实现 F11。**

## 1. 目标与范围

按用户原始任务调查当前 RMC 的完整程序生命周期、初始化复用、固定源重复执行、F/A 切换、source/WW/tally/MG 能群边界、MPI/OpenMP、全局状态、错误处理及 AIMC 当前调用链。

仅允许写本目录。原始材料原样保存在 [user_task_original.txt](logs/user_task_original.txt)。RMC 与 AIMC 只读；禁止切分支、改源码/参考结果、动态实验、commit/push、更新 STATUS/INDEX/KB 或阅读 Claude 任务目录。最新任务的这些限制优先于默认公共归档同步规则。

物理解释：复用模型数据不改变每轮必须有独立源历史、统计累计与归一化记录的要求；F/A 角色还决定核数据派生量和粒子碰撞路径，不能只切一个配置标签。这里只调查这些关系，不重做已有物理验证或选迭代算法。

## 2. 做法与证据

1. 按工作区要求先读 STATUS、AGENT_CONTEXT，定为模式 C；按用户指定路径手动建档。`new_task.sh` 会更新 INDEX，因此没有调用。
2. 记录两个仓库实际 branch/HEAD/status/log -10；RMC 为指定分支，AIMC 实际为 `feature/3d-two-group`，未擅自切为 develop。
3. 先核读当前入口和关键生命周期源码并保存 [source-only 初步结论](logs/preliminary-source-only-conclusion.md)。此后仍未读取历史 F02–F10 档案或 Claude 目录作为补充证据。
4. 沿调用路径调查 reset、归一化、MG mapping、MPI、失败路径及原型的实际 MC 入口；分别记录源码事实、推断和未知。
5. 形成 [主报告](RMC_Runtime_Architecture_Audit_Codex.md)、[状态表](logs/source-state-map.md)、[源码导航及证据摘录](logs/source-navigation.txt)。

复核输出：

- [仓库开始快照](logs/repository-state-start.txt) / [结束快照](logs/repository-state-end.txt)：真实 git 输出。
- [文档和范围自检](logs/document-verification.txt)：必需章节、15 项矩阵、source citation 文件/行号、原始材料一致性、开始/结束仓库状态比较。
- [RMC 改动快照](logs/rmc-changes.diff) / [AIMC 改动快照](logs/aimc-changes.diff)：tracked diff 均为空；AIMC 已有未跟踪 PDF 保留。
- [产物清单及哈希](logs/artifact-manifest.sha256)：本次文档交付快照。

未运行 RMC、未编译、未训练、未创建实验 harness、未改 benchmark/reference。验证从简，集中于文档证据可定位及仓库只读状态。

## 3. 决策

用户已直接授权本次源码调查和指定目录内报告写入；因此实施只读审查无需再申请 RMC 修改批准。本任务没有获得或使用修改 RMC 的授权。

采用模式 C，并将人类拍板范围限定为用户已下达的审查任务。人类理解确认：用户明确将最终架构决定留到两个独立审查完成后；本报告末节只列下一步待决定问题，不代替用户确认新的物理结论。

范围处理：AIMC 分支不符时仍审实际工作树，报告限制；不切分支，不通过历史文档假定 develop 的行为。先前会话 F10/F07 文档修正不混入本任务受限目录之外的写入。

## 4. 结论与边界

**结论**：当前有模型数据、tally 数组和 WW 更新的内部基础，但没有可直接重复调用的完整 fixed-source session 边界。主要障碍是完成计数/flags、bank、角色传播、伴随派生缓存的非幂等构造、混合初始化与全局 IO/timing 生命周期。完整证据及能力分类见主报告 §5–§17。

**可用能力**：value/RE 可以从归约后的内存数组取得；完整 physical G+1 能群边界可以从有效 MGACE 的 centre/width 提取并校验；固定 native WW 定义下有运行间替换数值的具体落点。

**边界**：只做静态源码调查。未证明 F→F、F→A→F、热更新 WW、MPI 多轮、失败恢复、性能收益或所有编译组合正确；主报告 §19 给出最小后续实验，全部未执行。当前 AIMC 结论仅适用于实际 `feature/3d-two-group` revision；它直接运行 Numba MC，不能当作已有 RMC 外部执行层证据。

结果解释：source history 是 RE 的统计单位；WW descendants 属于同一 history。普通源路径的实际 denominator 来自 history 计数，不应把变量名泛化为任意源权重实测总和。角色/归一化/统计边界需要在 F11 设计前明确。

## 5. 过程

| 步骤 | 本次记录 |
|---|---|
| 立项 | 指定目录手动建档，模式 C；原始任务原样保存 |
| 设计 | 入口→初始化→history loop→归约/输出→cleanup；以源码证据表和 15 项矩阵组织 |
| 人拍板 | 采用用户本次直接指令，仅授权审查和报告；架构及实验决策保留 |
| 实施+自验 | 只读源码、先保存初步结论、完成报告/状态表/导航、执行文档与仓库状态检查 |
| 归档 | 本目录交付完成；按用户要求等待统一归档，未更新公共 STATUS/INDEX/KB |

停止条件已遵守：到源码报告为止，不进入 controller/API/persistent session 或 F11 实现。
