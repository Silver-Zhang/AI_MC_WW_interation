# 项目状态（人只看这一页）

> **最后更新：2026-10-11**。当前科研主线：F11 v1设计冻结；阶段0最小验证已归档，**待独立复核**；生产实现未开始。
> [正式设计](MLVR_Knowledge/04_F11_v1_架构与实施设计.md) ｜ [阶段0档案](MLVR_develop/2026-10/20261011_02_f11-field-volume-normalization/README.md) ｜ [任务台账（85项）](MLVR_develop/INDEX.md) ｜ [Agent交接](MLVR_Knowledge/AGENT_CONTEXT.md)

## 1. 现在在哪一步

| 内容 | 当前状态 |
|---|---|
| F11 v1总体设计 | design frozen；production implementation not completed；知识库04为唯一基线 |
| 阶段0 Field体积归一化 | 最小数值判据满足（E3），待独立复核；结论/证据/边界见[档案§4](MLVR_develop/2026-10/20261011_02_f11-field-volume-normalization/README.md#4-结论与边界) |
| 本轮授权与执行 | 用户明确授权新输入/分析脚本、编译未修改RMC、小规模验证；已完成四配置与独立原始段参考 |
| 源码与基准 | 未修改RMC/AIMC、核数据库、既有测试/reference；未切分支/reset/commit/push |
| 阶段1–6 | 未开始；本任务到此停止 |

## 2. 下一步与授权

先独立复核阶段0档案及原始材料。结果解释的人类确认尚未填写，不把自验当独立复核。

| 阶段 | 工作 | 当前状态 |
|---|---|---|
| 0 | Field体积归一的最小验证 | 自验与归档完成，待独立复核 |
| 1 | 抽出唯一固定源执行核心 | 未开始，需另行授权/立项 |
| 2 | 正式reset与F→F/F→A→F/A→A | 未开始 |
| 3 | MLVR输入、TARGET伴随源/history响应 | 未开始 |
| 4 | Field/WW文件接口 | 未开始 |
| 5 | 外部调用及失败处理 | 未开始 |
| 6 | Bootstrap/K=1/K=3闭环 | 未开始 |

普通计分体积语义及本例PTRAC观察的单独问题指针见[06的W11/W12](MLVR_Knowledge/06_已知问题与改进建议.md)。阶段0不构成修改/提交团队RMC或更新参考结果的授权。

## 3. 文档优先级与证据边界

知识库04是唯一实施基线，冻结规则本轮未改。Task15/16保留为历史独立提案。设计入库见[20261011_01](MLVR_develop/2026-10/20261011_01_f11-design-freeze/README.md)，不能拿旧text/source出口验证替代新接口验收。

实际阶段0转换结论只看[档案§4](MLVR_develop/2026-10/20261011_02_f11-field-volume-normalization/README.md#4-结论与边界)及[02顶部速览](MLVR_Knowledge/02_RMC功能审查矩阵.md)；未覆盖的动态Adjoint、非等体积网格、碰撞/WW、多维轴、并行等不可写Ready。非零裂变连续切换门禁仍按04 §14。

## 4. 其他待办

RMC push 已完成（2026-10-11 用户拍板：5 个本地提交已推送，并合并远端 4 个提交 → `c3ef0934`，分支已与 origin 同步）；F04 扩展、历史台账及 AIMC/论文线不在本轮范围。

## 5. 维护方式

新任务读取本页/AGENT_CONTEXT/相关设计节；结论写档案§4与02速览，归档同步STATUS/INDEX。每阶段单独授权，设计冻结、自验和独立复核分开标注。
