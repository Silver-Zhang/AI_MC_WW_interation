# MLVR设计决策记录

本文件记录已经冻结的重要设计决定。原则：只追加，不覆盖历史决定。

## D001

日期：2026-08-23

决定：建立MLVR项目级开发流程与知识库体系，作为后续Agent协作和代码溯源基础。

状态：Frozen

## D002

日期：2026-08-23

决定：第一版基础框架目标为方法无关的双向迭代WW框架，不直接绑定高级机器学习算法。

状态：Frozen

## D003

日期：2026-08-23

决定：第一版场数据包含MC估计场及其统计误差RE。

状态：Frozen

## D004

日期：2026-08-23

决定：第一版伴随输运从多群模型开始，不考虑连续能量伴随输运。

状态：Frozen

## D005

日期：2026-08-23

决定：第一版不实现跨iteration历史场累计，先完成单轮闭环框架。

状态：Frozen

## D006

日期：2026-08-24

决定：第一版 Field 只定义为空间网格 × 能群上的统计场，不包含角度、时间、高阶角通量矩或机器学习特征；每个位置至少包含 mean field 与 RE。

状态：Frozen

## D007

日期：2026-08-24

决定：Forward Field 与 Adjoint Field 采用统一的数据维度与基本统计信息规范，但物理语义和生命周期必须严格区分；具体 C++ 数据结构留到接口设计阶段决定。

状态：Frozen

## D008

日期：2026-08-24

决定：第一版双向迭代采用用户给定的固定 iteration 次数，不实现 RE/FOM 自动收敛停止、patience 或其他自适应终止策略。

状态：Frozen

## D009

日期：2026-08-24

决定：正式双向迭代前增加独立 Bootstrap Stage，用于生成第一轮伴随权重窗 WW_A(1)；Bootstrap 不属于正式 iteration 编号。

状态：Frozen

## D010

日期：2026-08-24

决定：第一版 Bootstrap 采用真实物理问题下的低粒子数 Analog Forward MC，不使用权重窗、不修改密度或构造辅助物理问题。

状态：Frozen

## D011

日期：2026-08-24

决定：Bootstrap 输出至少包含 forward field + RE，经 Field Reconstruction 后生成 WW_A(1)；Bootstrap 数据不参与正式 FOM 比较、跨 iteration 历史累计或最终物理结果。

状态：Frozen

## D012

日期：2026-08-24

决定：第一版 Bootstrap 与正式 iteration 使用相同的空间 Field mesh 和能群结构，不引入 mesh mapping 或 energy-group mapping。

状态：Frozen

## D013

日期：2026-08-24

决定：Bootstrap 策略保留后续可扩展性；降密度、辅助减方差、外部场、多阶段初始化等仅作为后续研究方向，第一版不实现。

状态：Frozen

## D014

日期：2026-08-24

决定：Stage 2 的 RMC 功能审查统一采用 `Requirement → Existence → Actual Behavior → Requirement Match → Integration Compatibility → Targeted Verification → Classification` 的证据链。

状态：Frozen

## D015

日期：2026-08-24

决定：Stage 2 采用 A–F 六类结论：A Ready、B Extend、C Verify、D Integration issue、E Defect、F Missing。

状态：Frozen

## D016

日期：2026-08-24

决定：严格区分 Audit 与 Repair。Stage 2 发现缺口、缺陷或兼容性问题后只记录证据和分类，不在同一任务中修改 RMC；需要代码改动的事项进入 Stage 3 后重新立项并由用户拍板。

状态：Frozen

## D017

日期：2026-08-24

决定：Stage 2 每次只审查一个逻辑功能，首项正式审查为 F02 多群 Adjoint transport；第一轮以只读源码审查为主，若静态证据不足则提出最小验证方案，不以推测替代验证。

状态：Frozen

## D018

日期：2026-08-24

决定：F02 不仅进行功能存在性审查，还需要独立进行伴随输运物理正确性审查（F02-B）。重点验证多群散射转置、碰撞抽样与权重修正、角分布处理、伴随裂变以及离散算子互易性。代码机制明确但缺少关键数值验证时，不升级为 Ready。

状态：Frozen
