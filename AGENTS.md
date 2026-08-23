# 工作区约定（所有 Agent 必须遵守）

> 本文件与 `CLAUDE.md` 内容一致，供不读 CLAUDE.md 的 Agent（Codex 等）加载。**修改时请同步两份。**

本工作区用于 RMC 机器学习减方差（ML-VR）框架与功能的开发。**开工前先读**
`MLVR_Knowledge/AGENT_CONTEXT.md`（一屏上下文），再按需查知识库专题文档与
`MLVR_develop/README.md` 工作流规范。

```
RMC/                 RMC 代码仓库（独立 git，团队共享，改动谨慎）
AIMC_WWiteration/    AI-MC 原型（独立 git，研究原型，改动较宽松）
MLVR_develop/        开发工作区：一任务一档，记录每次开发/修复全过程
MLVR_Knowledge/      知识库：架构、方法、接口、已知问题（长期沉淀）
```

## 硬规则

1. **任何开发任务 / 缺陷修复 / 算法实验，必须走 `MLVR_develop/README.md` 的五步流程**：
   立项 → 设计/定位 → ⛔ 人拍板 → 实施+自验 → 归档。
   用 `MLVR_develop/new_task.sh <任务短名> [KB编号]` 建档，原始材料（报错/数据/日志）
   **原样**存进任务文件夹的 `logs/`。

2. **未经用户在档案第 4 节"决策"里拍板，不得修改 `RMC/` 下任何文件。**
   只读排查、写 `MLVR_develop/` 与 `MLVR_Knowledge/` 下的记录不受此限。
   （`AIMC_WWiteration/` 为个人研究原型，改动更宽松，但仍建议按流程留痕。）

3. **改完必须生成改动快照**，让人能不翻代码就复核：
   `git -C RMC diff > MLVR_develop/<任务文件夹>/changes.diff`
   （改原型则 `git -C AIMC_WWiteration diff > ...`）

4. **不擅自更新基准结果 / 参考结果 / 基准模型**（如 benchmark 数据、已归档的 `.h5`
   模型权重、FOM/RE 参考值）。更新基准会掩盖真实回归，必须由用户明确同意并在档案中写明理由。

5. **不擅自对 `RMC/` 执行 commit / push / 切分支**。RMC 是团队共享仓库，
   何时提交、提交到哪个分支由用户决定。（`AIMC_WWiteration/` 可自行管理，但建议
   一任务一提交并关联档案文件夹名。）

6. **验证/实验记录要贴真实输出**，不能只写"通过"；本地或资源限制无法覆盖的验证
   （如 GPU 训练、大规模 RMC 算例、Windows 侧）要在档案里明确写出"未覆盖到的验证"。

7. **实验可复现性**：涉及训练/数值实验时，必须在档案中记录随机种子、配置快照
   （`src/config.py` dataclass 值）、依赖版本（CUDA / PyTorch / numpy 等）、运行命令。

8. **知识库要跟着变**：修复/实现了 `MLVR_Knowledge/06_已知问题与改进建议.md` 里的条目，
   在该条目下标注 `已修复 → MLVR_develop/<任务文件夹>`；发现新问题则补写进 06 文档；
   改动影响架构/接口/方法 → 同步更新对应专题文档的"变更记录"。

## 服务器使用

需要上服务器跑计算/验证时，先读根目录 [`server_guide.md`](server_guide.md)（通用操作指南：
选机/登录/传文件/长任务/ML·GPU），登录凭据见 [`sever_info.md`](sever_info.md)（**敏感**，勿入 git）。
服务器上的操作**同样受上述硬规则约束**：改 `RMC/` 代码须先拍板；更新基准/参考结果须用户授权；
验证贴真实输出。服务器工作目录按 `server_guide.md` 第 8 节规范（项目级入口 + 一任务一子目录）。

## 常用入口

- 开新任务：`cd MLVR_develop && ./new_task.sh <任务短名> [KB编号]`
- 查台账：`MLVR_develop/INDEX.md`
- 快速上下文：`MLVR_Knowledge/AGENT_CONTEXT.md`
- 服务器操作：`server_guide.md`（凭据 `sever_info.md`）
