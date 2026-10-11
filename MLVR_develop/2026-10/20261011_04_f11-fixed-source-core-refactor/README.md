# F11阶段1：固定源执行核心重构

| 项目 | 内容 |
|---|---|
| 立项日期 | 2026-10-11（new_task.sh自动分配04） |
| 状态 | 待决策（分析/方案完成，等待RMC源码修改批准） |
| 任务模式 | C — 深度物理研究与学习 |
| 类型 | 最小结构重构 / 设计与回归计划 |
| 关联知识库条目 | F11，知识库04 §3.3/§5/§14 |
| 当前验收判定 | BLOCKED — 人工审批关口；尚未实施，不是技术故障判定 |
| 改动与提交 | 本轮RMC未修改，无commit/push/分支切换/reset，无reference/核数据库更新；档案随 2026-10-11 根工作区提交入库 |

## 1. 目标与范围

从普通CalcFixedSource抽出完整初始化、唯一prepared execution core及一次最终统计；原wrapper保留入口、源副本、计时、可选功能和输出。只做阶段1；目前授权覆盖源码分析、建档、具体设计，**不覆盖源码修改**。

**模式C物理解释**：结构重构不应改变任一源历史抽到的随机数、真实后代处理顺序、粒子权重/输运、history级得分或其分母。普通Forward/Adjoint/WW和其它粒子模式应在固定种子下得到确定性一致的物理结果。实际耗时会变化，但计时起止和输出顺序不能变。prepared入口只是明确的调用边界，不代表缺失的reset已经实现。

不做CalcMLVR、MLVR解析、TARGET/Field/HDF5、外部重构、CLEAR/SET/REBUILD、同进程F→F/F→A→F；不修W11/W12，不修改阶段0实验结果。

## 2. 做法与证据

- [source-map.md](source-map.md)：当前HEAD真实调用图、行号、模型/RNG/source/tally/particle/WW/timer生命周期。
- [refactor-design.md](refactor-design.md)：两文件范围、具体C++签名、原97–719行移动范围、拟修改调用图、风险和回滚。
- [test-plan.md](test-plan.md)：审批后先current-HEAD fresh baseline再实施；六粒子分支及MG analog/native WW/adjoint、multi-batch、接续与原CTest；完全一致判据和命令。
- [proposed-refactor.diff](proposed-refactor.diff)：可审查但**未应用**的拟议补丁；不是生产changes.diff。
- logs/source-evidence.txt及两源文件原样快照：本轮定位证据，不照抄历史行号。

### 仓库及环境

开工根仓库main/6152c7f0e70d4dadc4ecaddf5c95dc4b3e443ee8；RMC Neural_Network_WW_Iteration/c3ef093497ea42c54569a87ed3696642c8b42931；两工作树干净，无可能冲突修改。相对RMC本地tracking ref origin/Neural_Network_WW_Iteration：0 ahead/0 behind，无未推送本地提交。只读本地ref，没有fetch，以记录时本地upstream为界。

原始git查询（含全部diff、未跟踪项、submodules、未推送log和exitcode）见logs/repository-state.json；该文件区分建档前观察和建档后查询，root后者含本任务自己的INDEX/档案。848个RMC/src文件hash见logs/production-source-before.sha256.json；实际修改前必须再次检查，不覆盖期间他人修改。

GCC13.3.0、CMake/CTest3.28.3、Python3.12.3、HDF51.10.10；h5dump/mpicxx/PyYAML可用，系统Python无h5py/numpy。环境原始stdout/stderr/exitcode和数据库身份见logs/对应文件。existing-stage0-CMakeCache/flags是旧5cfb...构建调查，不是当前HEAD baseline；本轮**没有configure/build/transport/CTest**。审批后用独立新目录建立同参数fresh基线，不使用身份不清的旧binary。无AIMC训练，src/config.py/CUDA/PyTorch不适用。

阶段0独立正文Independent_F11_Field_Volume_Review.md判定ACCEPT WITH LIMITATIONS（review任务README仍未定稿）；用户本次已接受限定结论可供后续开发。本轮保留其全部实验/源码/归一化边界；不把其Stage1建议中的Field/目标实现扩入当前结构任务。

### 当前静态核查输出

`git -C RMC apply --check <task>/proposed-refactor.diff`退出0，stdout/stderr为空；执行的是只检查操作，没有应用。logs/proposal-integrity.json真实记录：

```text
base_HEAD: c3ef093497ea42c54569a87ed3696642c8b42931
execution_range: 97–719
execution_lines: 623
execution_body_sha256: 65828f852a7fb5b8cf34332970257ac795702cf84a1a51503f3b54ca98a42173
original_wrapper_signature_preserved: true
execution_body_appears_once_in_proposal: true
init_original_body_preserved: true
ordinary_tail_preserved: true
proposed_ProcessTally_call_count: 1
```

计划输入已保存inputs及logs/planned-inputs.json，均未运行。普通源的按值形参保留，core引用它的工作副本；CBurnup保留wrapper原寿命；6个已有粒子分支整体只移一份；完整初始化/统计以明确函数边界区分，统计之后原输出/可选资源收尾仍在wrapper。

## 3. 决策

**待审批决定**：是否批准按refactor-design.md与proposed-refactor.diff，仅修改RMC/src/CalMode.h、RMC/src/CalcFixedSource.cpp，并先建立fresh-process基线，再执行test-plan.md回归？若审批时HEAD/树变化须重新核查；新增范围要另报，不自行扩大。

本Prompt第六节明确要求：“完成源码分析和具体修改方案后，先停止，等待用户批准RMC源码修改。”当前没有收到该批准。AGENTS.md第2条和工作流同样禁止未拍板修改RMC，故在此停下。

**人类理解确认（待填写）**：用户已给出结构目标和确定性回归要求；本Agent没有把自己的方案当成人已接受。待确认：原循环仅移位、外源仍是wrapper局部副本、每次ProcessTally只一次、完整初始化不作reset、计时范围/普通收尾保留。验伪：任何固定N/同种子物理或RNG差异、源改动外泄、registry重复、后代归属改变均否定本次重构。

| 变更卡 | 内容 |
|---|---|
| 问题与风险 | 当前完整初始化/执行/结束混在普通入口；不谨慎抽取会改RNG、计数、对象寿命或输出 |
| 拟改对象 | 仅CalMode.h及CalcFixedSource.cpp；3个CDCalMode成员函数 |
| 不改什么 | 物理算法、source sampling、tally/WW数学、RunCalculation混合传参、reference、核数据及阶段0 |
| 因果链 | 同对象/同语句顺序/同source工作副本→同history/RNG/统计→确定性fresh回归 |
| 验证 | 先旧HEAD基线，后新程序；逐字/IEEE完全一致及既有CTest，绝不扩大容差 |
| 回滚 | 保存两文件hash/原文；确认没有他人后改后仅反向应用本任务补丁，不reset |

## 4. 结论与边界

**当前判定BLOCKED：等待人工审批。** 分析、可应用提案和事前回归方案已完成；生产实现、编译/运行/数值验证均未完成，不能验收为ACCEPT。

**模式C结果解释**：静态拆分证明提案没有复制原执行体、没有缩短CBurnup寿命或改变外层source复制边界；尚不能证明编译、随机序列/输出实际等价。这些必须以批准后的fresh baseline和确定性数值回归验收。没有新的物理结论，不改变阶段0限定结果或冻结设计。

| 最终验收问题 | 本轮状态 |
|---|---|
| 普通CalcFixedSource正常工作？ | 当前源码未改；拟议版本未编译/运行，待验证 |
| 实际执行代码仅一份？ | 提案保留一份原6模式623行body，生产实施后还须复核 |
| 初始化/执行/统计职责清楚？ | 方案清楚：Initialize→ExecutePrepared→Finalize；普通收尾留wrapper |
| Forward/MG Adjoint/native WW回归？ | 未执行，事前计划已给 |
| 数值与输出保持？ | 未验证；计划完全一致，时间值单独处理 |
| 阶段2有prepared入口？ | 已提出确切接口，未写入生产/未证明reset能力 |
| 哪些对象缺正式reset？ | source-map末节列FixedSource/source/tally/AceData/particle/RNG/WW/timer/output owner清单；均留阶段2 |

changes.diff当前不存在，因为RMC没有实际修改。批准并实施后必须用实际RMC diff生成；若出现新增未跟踪生产文件，另保存new-files.patch并登记，不能漏过git diff。本方案不新增生产文件。Windows、并行数值、时间截止/Python源/WWG/共享WW等未覆盖情况在最终验收如实记录，不能以serial或编译通过替代。

## 5. 过程

| 日期（Asia/Shanghai） | 记录 |
|---|---|
| 2026-10-11 | 读取指定入口、04相关节/工作流、阶段0及独立报告；核查current HEAD及无冲突状态 |
| 2026-10-11 | new_task.sh自动建C模式04；保存仓库状态、环境与源hash |
| 2026-10-11 | 定位750行CalcFixedSource及真实owner/调用链；写source-map |
| 2026-10-11 | 形成三方法两文件提案，原623行执行体整块保留；只读apply-check通过 |
| 2026-10-11 | 编写refactor-design/test-plan、预设新输入及manifest；同步STATUS/INDEX/交接，停在源码审批关口 |

本轮交接自检真实输出：归档检查退出0，需处理0项/历史提示31项；git diff --check退出0；848个生产src文件、RMC分支/HEAD和04正文保持不变。计划命令仅bash -n语法检查退出0，未执行；logs/final-check.*与planned-commands-syntax-check.*保留证据。
