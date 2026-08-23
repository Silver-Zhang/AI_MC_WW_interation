# 服务器操作通用指南（组内共享）

> **用途**：给本工作区及组内其他开发任务提供**通用**的服务器操作指引——选服务器、登录、
> 传文件、跑长任务、环境与工具链、ML/GPU 操作、故障排查。任何 Agent 开工需要上服务器时
> 先读本文；本指南也可单独拷贝到其他项目工作区复用。
>
> **登录信息（用户/密码/个人目录）一律以 [`sever_info.md`](sever_info.md) 为准**，本文不重复密码。
> **实时状态**（是否在线、资源占用）以各服务器实际为准；本文只保证**环境事实**（路径/版本/硬件）。
>
> 更新日期：2026-08-23

---

## 1. 一分钟速查（按任务选服务器）

| 你要做什么 | 用哪台 | 怎么做 | 详情 |
|---|---|---|---|
| Linux 跑计算 / 构建 / 回归 | **21**（推荐主力）或 16 / 27 | `ssh realpub@192.168.9.21` | 第 4 节 |
| Windows 侧验证 | 14（串行/PE）或 32（MPI） | `ssh Administrator@192.168.9.14` / `ssh realpub@192.168.9.32` | 第 5 节 |
| 传文件（本机 ↔ 服务器） | 目标服务器 | `rsync` / `scp` | 3.2 |
| 后台跑长任务（训练/大算例） | 任意 | `tmux` / `nohup` | 3.3 |
| GPU 训练 | （GPU 服务器清单待补充） | `nvidia-smi` 确认后训练 | 7.2 |
| Python 环境隔离 | 任意 | `conda create` | 7.1 |
| GitLab 站点 / Pages 排查 | 74 | `ssh websites@192.168.9.74`（**只读**） | 6.1 |
| 公共服务器做一般开发 | 29 | `ssh zhangjunxiao@192.168.9.29`（⚠️ 24.04 工具链） | 6.2 |
| 看服务器状态 / 磁盘 | 目标服务器 | `nvidia-smi` / `df -h` / `free -h` | 3.4 |

---

## 2. 服务器总览

| 服务器 | IP | 系统 | SSH | 角色 / 用途 | 状态提示 |
|---|---|---|---|---|---|
| Server 16 | 192.168.9.16 | Ubuntu 18.04 | ✅ | Linux 计算/测试机 | 在线 |
| Server 18 | 192.168.9.18 | Ubuntu 18.04 | ✅ | Linux 计算/测试机 | 在线 |
| Server 21 | 192.168.9.21 | Ubuntu 18.04 | ✅ | **★ 推荐 Linux 主力**（128 核 / 251G） | 在线 |
| Server 22 | 192.168.9.22 | Ubuntu 18.04 | ✅* | Linux 计算/测试机 | ⚠️ 近期离线 |
| Server 27 | 192.168.9.27 | Ubuntu 18.04 | ✅ | Linux 计算/测试机 | 在线 |
| GitLab 服务器 | 192.168.9.74 | Ubuntu 22.04 | ✅ | 基础设施：生产 GitLab + Pages | 在线 |
| 服务器 29 | 192.168.9.29 | Ubuntu 24.04 | ✅ | **公共服务器**（个人用户/目录下工作）；⚠️ 工具链较新 | 在线 |
| server_14_ci | 192.168.9.14 | Windows 10 | ✅ | Windows 串行 / PE | 在线 |
| server_32_ci | 192.168.9.32 | Server 2019 | ✅ | Windows MPI | 在线 |

> `*`：22 号近段时间处于关机/离线状态，**安排任务前先确认它已开机**。
> 其余"在线"指 SSH 可达；资源是否空闲以实际占用为准。

---

## 3. 通用操作基础（所有服务器适用）

### 3.1 SSH 登录

```bash
ssh realpub@192.168.9.21        # 密码见 sever_info.md
```

- 常用参数：`ssh -p <端口>`（默认 22）、`ssh -o ServerAliveInterval=60`（长任务防断连）
- **免密建议**：`ssh-copy-id` 上传公钥后免密登录，避免每次输密码（也避免密码进日志）

### 3.2 文件传输（本机 ↔ 服务器）

```bash
# 上传 / 下载（推荐 rsync：断点续传、增量、保留权限）
rsync -avz --progress 本地文件   realpub@192.168.9.21:/home/realpub/workspace/zhangjx/xxx/
rsync -avz --progress realpub@192.168.9.21:/home/realpub/workspace/zhangjx/xxx/result.h5  ./

# scp（简单场景）
scp 本地文件 realpub@192.168.9.21:/目标路径/
scp realpub@192.168.9.21:/目标路径/文件  ./
```

- **大体积/长传输**：在 tmux 里跑（见 3.3），防 SSH 断开中断
- Windows 服务器：路径用 `/e/zhangjx/...`（Git Bash 风格），或用 SFTP 工具

### 3.3 长任务后台运行（训练 / 大算例必备）

```bash
# 方式一：tmux（推荐，可随时回来查看）
tmux new -s train01            # 新建会话
... 跑你的命令 ...
Ctrl+b d                        # 脱离会话（任务继续跑）
tmux attach -t train01         # 回来查看
tmux ls                        # 列出会话

# 方式二：nohup + 日志（一次性任务）
nohup python train.py > train.log 2>&1 &
tail -f train.log              # 跟进日志
```

### 3.4 服务器状态速查

```bash
nvidia-smi        # GPU 占用（有 GPU 的机器）
df -h             # 磁盘空间
free -h           # 内存
uptime            # 负载
ps aux | grep <你的进程>   # 找自己跑的进程
```

---

## 4. Linux 计算/测试机（16 / 18 / 21 / 22 / 27）

### 4.1 登录与环境

```bash
ssh realpub@192.168.9.21        # ★ 推荐主力：21（128 核 / 251G）；16/27 也可（已有仓库）
```

统一环境（与 CI 一致）：

| 项 | 路径 |
|---|---|
| 个人工作目录 | `/home/realpub/workspace/zhangjx` |
| MPI_DIR | `$HOME/mpich_install`（MPICH 3.2） |
| HDF5_ROOT | `$HOME/hdf5_install` |
| RMC_DATA | `/home/realpub/workspace/RMC_DATA`（核数据库，57~60 GB，RMC 算例用） |

### 4.2 每台差异速查

| 服务器 | CPU | 核 | 内存 | 磁盘提示 | 现成 RMC 仓库 |
|---|---|---|---|---|---|
| 16 | Xeon Gold 6130 | 64 | 62.6G | 正常 | ✅ `zhangjx/RMC` |
| 18 | Xeon Gold 6140 | 72 | 46.8G | ⚠️ workspace 95% | ❌ 需 clone |
| 21 | Threadripper 3990X | 128 | 251.6G | `/` 86% | ❌ 需 clone |
| 22 | （未探） | 128 | ~251G | — | ❌ 需 clone（离线⚠️） |
| 27 | Xeon Gold 6140 | 72 | 46.8G | 正常 | ✅ `zhangjx/RMC` |

- **★ 21 是推荐 Linux 主力**（配置最好）；16/27 有现成仓库可省 clone
- 大体积构建优先 16 或 21；18 的 workspace 仅剩约 176G
- 每台都有多人 `workspace/<人名>/...`，**只动自己的 `zhangjx/`**

### 4.3 RMC 构建 / 测试（如涉及）

```bash
cd /home/realpub/workspace/zhangjx/RMC
export MAKE_PROCS=8 TEST_PROCS=8
python3 scripts/ci/build_rmc.py
python3 scripts/ci/test_rmc.py
```

> RMC 具体构建/测试/运维流程见知识库 [`MLVR_Knowledge/07_实验环境与资源.md`](MLVR_Knowledge/07_实验环境与资源.md)（规划中）。

---

## 5. Windows 服务器（192.168.9.14 / .32）

```bash
ssh Administrator@192.168.9.14     # 14：串行 / PE，个人目录 F:\zjx
ssh realpub@192.168.9.32           # 32：MPI，个人目录 E:\zhangjx（注意用户是 realpub）
```

| 项 | 14（Windows 10） | 32（Server 2019） |
|---|---|---|
| 个人目录 | `F:\zjx` | `E:\zhangjx` |
| RMC_DATA_PATH | `D:\RMC_DATA` | `F:\RMC_DATA` |
| MPI | MS-MPI 8.0 | MS-MPI 10.1 |
| HDF5 | 1.10.6 | 1.10.8 |

- RDP 图形界面：`xfreerdp3 /v:192.168.9.32 /u:realpub /cert:ignore /dynamic-resolution +clipboard`
  （**不要把 `/p:<密码>` 写进命令行**，会进 shell 历史与进程列表）
- Windows 侧验证结果无法在 Linux 本地复现，须在 Windows 服务器实测（归档时写明"未覆盖到的验证"）

---

## 6. 其他服务器

### 6.1 GitLab 服务器（192.168.9.74）——生产基础设施

- `ssh websites@192.168.9.74`（有 sudo）；Ubuntu 22.04，32 核 / 31G
- **无计算环境**（无 MPI/HDF5/RMC_DATA），**不要跑计算任务**
- ⚠️ **生产环境：只做只读取证与用户明确授权的操作**；容器除 gitlab 系列与 Proxy 外勿动

### 6.2 服务器 29（192.168.9.29）——公共服务器，个人用户/目录下工作

- `ssh zhangjunxiao@192.168.9.29`；Ubuntu 24.04，128 核 / 125G
- 个人目录 `/home/zhangjunxiao/workspace`
- ⚠️ **Ubuntu 24.04 工具链较新**（cmake 3.28 / gcc 13.3 / python3 3.12），与 18.04 测试机
  （cmake 3.10 / gcc 7.5）**不一致，可能导致数值/行为差异**——跨系统对比结果前先确认环境

---

## 7. ML / 数据开发通用操作

> 本节为通用 ML 开发操作，任何项目可用；GPU 服务器清单待补充（登记见第 9 节维护约定）。

### 7.1 Python 环境隔离（conda / venv）

```bash
# conda（服务器可能已预装；未装则用 Miniconda 安装到个人目录）
conda create -n mlvr python=3.10 -y
conda activate mlvr
pip install -r requirements.txt        # 或按需装 torch/numpy/numba 等

# 或 venv
python3 -m venv .venv && source .venv/bin/activate
```

- **不要用系统 python 直接装包**，避免污染公共环境；个人项目一律建独立环境

### 7.2 GPU 查看与 PyTorch

```bash
nvidia-smi                 # 确认 GPU 型号 / 显存 / 占用
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

- 训练前确认目标 GPU 空闲（`nvidia-smi` 看占用），多任务抢占 GPU 用 `CUDA_VISIBLE_DEVICES=<id>`

### 7.3 训练任务后台化 + 日志

```bash
tmux new -s train01
conda activate mlvr
CUDA_VISIBLE_DEVICES=0 nohup python train.py --seed 42 > train.log 2>&1 &
tail -f train.log
```

- **可复现性**：训练命令里带上 `--seed`、配置文件；归档时记录配置快照与依赖版本
  （见工作流规范 `MLVR_develop/README.md` 补充约定 4）

### 7.4 环境差异注意事项

- 18.04（gcc 7.5 / cmake 3.10）vs 24.04（gcc 13.3 / cmake 3.28）：编译产物与数值可能不同
- Python 版本差异（3.6 vs 3.12）会导致依赖不兼容——先在目标机 `python --version` 确认
- RMC 数值结果跨系统对比前，先确认两机工具链一致

---

## 8. 服务器工作目录规范

> 目的：服务器个人目录保持整洁、可追溯，且**按项目隔离**——个人目录可能承载多个项目的
> Agent 协作工作，各项目入口不能占用个人目录根部。

1. **项目级唯一入口**：每个项目在个人目录下使用独立入口目录
   （如 `rmc_ci_agent_work/`、`mlvr_agent_work/`，各项目各自立入口，互不混用）。
2. **一次任务一个子目录**：`<入口>/<YYYYMMDD_任务短名>/`，按需再分 `src/`、`results/`、
   `build_*/` 等；任务短名与本地任务档案文件夹对应。
3. **收尾**：关键产物（结果/日志/差异）拉回本地归档；服务器保留轻量痕迹（`任务说明.md`，
   含任务、基线、做了什么、结论、本地档案位置、清理时间）；删除可再生成的重资产前经用户确认。
4. **边界**：只动自己的个人目录与项目入口，**绝不碰其他成员的目录**。

---

## 9. 维护约定

1. **登录信息**只在 [`sever_info.md`](sever_info.md) 维护（含凭据，建议 gitignore）；
   本文档不出现密码。
2. **服务器事实变化**（新增服务器、系统/版本变更、离线等）→ 更新本文档并在此追加变更记录。
3. **GPU 服务器清单待补充**：有 GPU 资源后在本节登记（IP / 型号 / 显存 / 登录方式）。
4. **跨项目复用**：本文档为通用指南，可整体拷贝到其他项目工作区；拷贝时同步拷贝
   `sever_info.md` 并注意权限。

## 变更记录

- 2026-08-23 · 建立本文档：同步自 `RMC自动测试工作/server_quickstart.md` 的服务器事实，
  泛化为组内通用指南（新增通用操作基础、ML/GPU 操作、服务器工作目录规范）
