# MLVR 知识库 —— RMC 双向迭代权重窗开发

> 长期沉淀 RMC 双向迭代 WW / ML-VR 开发所需的事实、方法、审查结论、接口设计与已知问题。
> 开发任务过程记录在 [`MLVR_develop/`](../MLVR_develop/)（一任务一档），本知识库存放沉淀后的长期结论。
> 面向懂物理但不要求懂代码的解释性文档按物理专题放在 [`MLVR_Physics_Guide/`](../MLVR_Physics_Guide/)。

## 当前文档地图

| 文档 | 状态 | 内容 |
|---|---|---|
| [AGENT_CONTEXT.md](AGENT_CONTEXT.md) | 🟢 Active | Agent 开工的一屏上下文与当前任务 |
| [00_开发总纲与阶段路线.md](00_开发总纲与阶段路线.md) | 🟢 Active | 项目目标、Stage 路线、当前阶段与进入/退出逻辑 |
| [01_双向迭代基础框架_方法与功能需求.md](01_双向迭代基础框架_方法与功能需求.md) | 🟢 Frozen v1 | 第一版算法流程、Field/Bootstrap/iteration 功能需求边界 |
| [02_RMC功能审查矩阵.md](02_RMC功能审查矩阵.md) | 🟢 Active | F01–F12 功能台账、状态和 A–F 审查分类 |
| [03_RMC功能审查规范.md](03_RMC功能审查规范.md) | 🟢 Active | Stage 2 Audit Protocol、证据标准、统一输出模板和审查顺序 |
| [DECISIONS.md](DECISIONS.md) | 🟢 Active | 已冻结设计决策，只追加不覆盖 |
| [06_已知问题与改进建议.md](06_已知问题与改进建议.md) | 🟢 Active | 已知坑、改进想法、后续储备 |

## 面向物理读者的入口

[`MLVR_Physics_Guide/`](../MLVR_Physics_Guide/) 不替代本知识库的证据台账，而是把稳定的代码审查结论翻译成物理语言，并按物理功能组织。当前首个专题为 [`RMC 多群伴随输运`](../MLVR_Physics_Guide/01_RMC多群伴随输运/README.md)，包括：

- 当前能力、适用边界和验证结论；
- 从输入到 tally 的物理逻辑、流程图和时序图；
- W5、W6、W7 三项已确认缺陷的物理含义、结果风险和当前修复验证状态。

## 后续专题文档（按阶段需要再建立）

以下内容暂不提前创建空文档，避免在功能审查前臆造接口和架构：

- RMC / Field Reconstruction 接口设计规范；
- WW 数据交换与格式规范；
- 双向迭代 controller / lifecycle 设计；
- 测试与验证基准；
- 简单回归与后续高级 ML 方法；
- 项目专用实验环境与资源说明。

只有当前一 Stage 的证据足以支撑下一阶段设计时，再新增相应专题文档。

## 从哪读起

Agent 推荐读取顺序：

```text
AGENTS.md
  ↓
MLVR_Knowledge/AGENT_CONTEXT.md
  ↓
MLVR_Knowledge/00_开发总纲与阶段路线.md
  ↓
MLVR_Knowledge/DECISIONS.md
  ↓
当前 Stage 的专题文档
  ↓
MLVR_develop/<当前任务>/README.md
  ↓
再读取 RMC / AIMC_WWiteration 代码
```

当前 Stage 2 还必须阅读：

- `02_RMC功能审查矩阵.md`
- `03_RMC功能审查规范.md`

## 维护约定

- 新增专题文档时在“当前文档地图”登记。
- 每次形成稳定结论后，在对应专题文档文末“变更记录”追加日期、简述和关联任务。
- 关键设计变化必须同步追加到 `DECISIONS.md`，不得静默覆盖旧决策。
- 功能审查状态同步更新 `02_RMC功能审查矩阵.md` 与 `MLVR_develop/INDEX.md`。
- 审查、修复或验证改变物理结论时，同步更新 `MLVR_Physics_Guide/` 中对应的人类可读文档。
- Stage 2 审查发现的问题不得直接在同一任务中修复；进入 Stage 3 后重新立项。
