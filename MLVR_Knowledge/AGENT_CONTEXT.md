# Agent 快速上下文卡片

> 后续 Agent 接手时先读本页；需要细节再翻对应专题文档（见 [README.md](README.md)）。

## 一句话概括

RMC 是清华 REAL 团队的蒙特卡罗中子输运程序（C++/CMake）。本工作区要做的
**机器学习减方差（ML-VR）** 是：把 `AIMC_WWiteration/` 里验证过的
**神经网络辅助权重窗口（WW）迭代**方法（通量预测 → WW 生成 → MC 反馈 → 重训练）
引入 RMC，替换/增强 RMC 现有（且效率不理想的）WW 生成机制，加速深穿透屏蔽等问题收敛。

## 两个仓库的关系

```
AIMC_WWiteration/  ← 研究原型（Python，分支 develop）
     │  提供：模型（6 变体）、训练/预测、迭代求解器、无偏性验证
     ▼
RMC/  ← 目标程序（C++，分支 Neural_Network_WW_Iteration）
     │  已有：WW 应用/生成/读写全链路、UFS、Python 接口
     ▼
ML-VR 框架：外部 Python 驱动 / RMC 内嵌 / 混合（架构待定，见 01 专题）
```

## 关键路径

```
# RMC 侧（WW 相关）
RMC/src/WeightWindow.h               # CDWeightWindow 类（WW 参数、能量/空间网格、WWG 状态）
RMC/src/DoWeightWindow.cpp           # WW 应用（分裂/轮盘赌）
RMC/src/DoMeshWeightWindow.cpp       # 网格 WW 入口
RMC/src/TrackWithWeightWindow.cpp    # 带 WW 的径迹处理
RMC/src/WeightWindowGenerator.cpp    # WWG（cell/mesh 基生成，ShieldRMC 遗留，效率问题）
RMC/src/ReadWeightWindow.cpp         # WW 块读入
RMC/src/ReadMCNPWeightWindowCard.cpp # MCNP WW 卡读入（含 WWG 卡）
RMC/src/ReadMCNPWwinpFile.cpp        # wwinp 文件读入
RMC/src/WriteWwoutFile.cpp           # wwout 写出
RMC/src/UFS.cpp                      # 均匀裂变源
RMC/src/PythonInterface/             # Python 接口（CInterfaceFunction.cpp 等）

# AIMC_WWiteration 侧（ML 核心，可直接复用）
AIMC_WWiteration/src/config.py       # 集中配置（ExperimentConfig dataclass）
AIMC_WWiteration/src/mc.py           # Numba 多群 MC 核（正向+伴随）
AIMC_WWiteration/src/models.py       # 模型工厂（6 变体）
AIMC_WWiteration/src/learning.py     # 训练数据构造/loss/训练/预测
AIMC_WWiteration/src/solver.py       # IterativeSolver 双向迭代主流程
AIMC_WWiteration/src/io.py           # HDF5 保存/读取
AIMC_WWiteration/scripts/check_unbiasedness.py  # WW 无偏性数值验证
AIMC_WWiteration/notes/              # 研究日志（按日期）
```

## 必须记住的 10 件事

1. **RMC 已有 WW 全链路**：应用（`DoWeightWindow`/`TrackWithWeightWindow`）、
   生成（`WeightWindowGenerator` WWG）、读写（`ReadWeightWindow`/`ReadMCNP*`/`WriteWwoutFile`）。
   ML-VR 是在此基础上**增强/替换生成端**，不必从零搭应用侧。
2. **WWG 是被放弃过的功能**：`WeightWindow.h` 头部注释明确写到——ShieldRMC 的 WWG
   因**效率差、计算内存过大可能卡死**，RMC 重构中放弃。这是 ML-VR 要解决的核心痛点，
   设计时务必把"生成开销与内存"作为约束。
3. **WWG 有两种空间基**：`CELL_BASE`（cell 平均）与 `MESH_BASE`（网格），
   能量分箱由 `p_vEnergyBinsForWWG` 定义；生成量含"进入权重"与"有效权重"两类统计。
4. **UFS（均匀裂变源）**：`UFS.cpp` 已存在，属于另一类减方差手段，可作对比基准。
5. **当前 RMC 分支 `Neural_Network_WW_Iteration`** 就是 ML-VR 开发分支，
   未拍板前不得改动 `RMC/` 下文件（见 `AGENTS.md` 硬规则）。
6. **AIMC 原型 6 变体**：`plain_dnn` / `feature_dnn` / `prior_residual_dnn` /
   `prior_residual_pinn` / `unet` / `prior_residual_unet`，用 `build_model()` 工厂注册。
7. **迭代循环**：伴随+正向 MC 积累多群通量 → NN（重）训练预测全空间通量 →
   转 WW → 偏置下一次 MC；FOM/RE 随迭代快速收敛（原型结论）。
8. **无偏性已有验证**：`AIMC_WWiteration/scripts/check_unbiasedness.py` +
   `docs/unbiasedness_check.md`（split/roulette 理论无偏 + z-score 数值判据）。
   RMC 侧接入新 WW 时同样要过无偏性检查。
9. **FOM gate 已修复**：原型曾出现深穿透 quick 模式下探测器响应为零污染 best-WW 的问题，
   已通过 `max_valid_re_for_best` + `require_nonzero_response_for_best` 门控解决——
   接入 RMC 时注意同样的问题。
10. **工作流硬规则**：一任务一档走五步流程；第 ③ 步人拍板；改动留 `changes.diff`；
    不擅自 commit/push/更新基准。详见根目录 `AGENTS.md`。

## 当前工作背景

- RMC 分支：`Neural_Network_WW_Iteration`；AIMC 分支：`develop`。
- ML-VR 耦合架构（外部 Python 驱动 / RMC 内嵌 / 混合）尚未拍板，见知识库 01 专题（规划中）。
- 本工作区（`MLVR_develop/` + `MLVR_Knowledge/`）于 2026-08-23 建立，
  设计参照 `/home/silver/workspace/RMC自动测试工作` 的 CI/CD 工作流模式。

## 近期重要事件（2026-08-23）

- 建立 ML-VR 开发工作区：`MLVR_develop/`（一任务一档 + 五步工作流）、
  `MLVR_Knowledge/`（知识库）、根目录 `AGENTS.md`/`CLAUDE.md`/`README.md`。
- 知识库 06 已登记首个已知问题：RMC WWG 效率/内存问题（ShieldRMC 遗留，RMC 重构放弃）。

## 动手前的自检

```bash
# 确认两个仓库分支与工作区状态
git -C RMC branch --show-current
git -C RMC status --short
git -C AIMC_WWiteration branch --show-current
git -C AIMC_WWiteration status --short
# 若涉及原型功能，先跑冒烟测试
python3 AIMC_WWiteration/tests/smoke_test.py
```
