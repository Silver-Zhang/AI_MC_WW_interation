# RMC 机器学习减方差（ML-VR）开发工作区

> 工作区导航总入口。本工作区用于 **RMC 机器学习减方差（Machine Learning Variance
> Reduction，ML-VR）框架与功能** 的开发——将神经网络辅助的权重窗口（WW）迭代方法
> 引入 RMC 蒙特卡罗输运程序，加速深穿透屏蔽等问题的收敛。

## 目录结构

| 目录 | 内容 | Git |
|---|---|---|
| [`RMC/`](RMC/) | RMC 蒙特卡罗程序代码仓库（团队共享，改动谨慎） | 独立 git，分支 `Neural_Network_WW_Iteration` |
| [`AIMC_WWiteration/`](AIMC_WWiteration/) | AI-MC 权重窗口**研究原型**（DNN/PINN/U-Net × 多群 MC 迭代，6 种学习变体） | 独立 git，分支 `develop` |
| [`MLVR_develop/`](MLVR_develop/) | **ML-VR 开发工作区**：一任务一档，记录从立项到归档全过程 | 本仓库 |
| [`MLVR_Knowledge/`](MLVR_Knowledge/) | **知识库**：RMC WW 架构、ML 方法、接口规格、已知问题（长期沉淀） | 本仓库 |
| [`server_guide.md`](server_guide.md) | **服务器操作通用指南**（组内共享，选机/登录/传文件/长任务/ML·GPU 操作） | 本仓库 |
| [`sever_info.md`](sever_info.md) | 服务器登录信息（**含凭据，敏感**，已被 `.gitignore` 排除） | 不入 git |

## 从哪读起

- **人机协作硬规则**（所有 Agent 开工前必读） → [`AGENTS.md`](AGENTS.md)（`CLAUDE.md` 同内容）
- **一屏上下文**（快速建立认知） → [`MLVR_Knowledge/AGENT_CONTEXT.md`](MLVR_Knowledge/AGENT_CONTEXT.md)
- **要开一个新开发任务** → [`MLVR_develop/README.md`](MLVR_develop/README.md)（五步工作流）+ `./new_task.sh <任务短名>`
- **想知道有哪些坑** → [`MLVR_Knowledge/06_已知问题与改进建议.md`](MLVR_Knowledge/06_已知问题与改进建议.md)
- **看历史怎么开发的** → [`MLVR_develop/INDEX.md`](MLVR_develop/INDEX.md)
- **要上服务器跑东西** → [`server_guide.md`](server_guide.md)（登录凭据另见 [`sever_info.md`](sever_info.md)）

## 使用方式

```
AI_MC_WW_interation/
  RMC/                  RMC 代码仓库（独立 git）
  AIMC_WWiteration/     AI-MC 原型（独立 git）
  MLVR_develop/         开发工作区：一任务一档
  MLVR_Knowledge/       知识库：架构 / 方法 / 接口 / 已知问题
  server_guide.md       服务器操作通用指南（选机 / 登录 / 传文件 / 长任务 / ML·GPU）
  sever_info.md         ⚠️ 服务器登录凭据（敏感，勿入 git）
```

```bash
# 遇到新开发任务 / 缺陷，建档
cd MLVR_develop && ./new_task.sh <任务短名> [知识库条目编号]
```

## 维护约定

- 任何开发任务/缺陷修复走 [`MLVR_develop/README.md`](MLVR_develop/README.md) 的**五步流程**，
  **决策节点由人拍板**，代码改动落成 `changes.diff` 供复核。
- 改动 RMC 或知识库后，同步更新对应文档并在文末"变更记录"追加一行。
- **`sever_info.md` 含登录凭据，敏感**：已被 `.gitignore` 排除，禁止手动加入提交。
- **本仓库远程（双镜像，`git push origin main` 同时推送两边）**：
  - GitLab（主）：`https://gitlab.reallab.org.cn/zhangjunxiao/AI_MC_WW_interation.git`
  - GitHub（镜像）：`git@github.com:Silver-Zhang/AI_MC_WW_interation.git`
  分支 `main`，2026-08-23 建立，均私有。`RMC/` 与 `AIMC_WWiteration/` 为独立仓库
  不纳入本仓库；如需在克隆环境中引用，可后续用 git submodule 关联。
