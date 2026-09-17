# workspace-repo-hygiene

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-17 |
| 状态 | 已完成 |
| 任务类型 | 工作区治理 / 多仓库卫生 |
| 任务模式 | B — 工程协作（默认） |
| 报告人 | 用户 + Agent |
| 关联知识库条目 | 无 |
| 涉及文件 | `AIMC_WWiteration/.claude/worktrees/`、`MLVR_develop/20260904_01_…`、新建 `tools/repo-status.sh` |
| 分支 / 提交 | 根工作区 `main` ／ 待提交 |

---

## 0. 人类阅读摘要（模式 C 必填；A/B 按需）

（本任务为模式 B：清理 AI 工具遗留的 worktree，补录被遗漏的验证证据，并新增只读的多仓库状态脚本；详见第 7 节。）

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：整理工作区多仓库结构：清理 AI 工具遗留的 worktree 与游离副本，补录被遗漏的原始验证证据，并提供一条命令查看三个主仓库状态的只读脚本。RMC 自带的依赖 submodule 不做任何改动。

**范围**：`AIMC_WWiteration/.claude/worktrees/`（清理）、`MLVR_develop/2026-09/20260904_01_task01r-mesh-tally-repair-claude/`（证据补录与引用修正）、新建 `tools/repo-status.sh`。不修改 `RMC/`（含其 submodule 配置）与 AIMC 的代码或历史。

**验收标准**：
1. 两个遗留 worktree 目录清除，AIMC `git worktree list` 仅剩主工作区；
2. 未合入提交以 tag 形式保留，未被销毁；
3. task01r 的原始验证日志补录进正式档案并可追溯；
4. `tools/repo-status.sh` 可运行，正确显示三个仓库的分支/同步/工作区/未跟踪状态。

**原始材料**：无外部报错；依据为只读盘点输出（见证据链表）与用户 2026-09-17 的选择。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：工作区含 3 个独立仓库 + RMC 自带的 11 个依赖 submodule + AI 工具遗留的 worktree。用户询问“很多 subrepo 怎么处理”，盘点后确认三类来源，其中第三类需要清理。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `AIMC_WWiteration/.claude/worktrees/agent-a97cdf8e33723c40c` | 2026-06-05 注册的 worktree；分支落后主线 221 个提交；`git cherry` 判定其独有提交 `3c74a11` **未合入**主线；从未推送 |
| 2 | `AIMC_WWiteration/.claude/worktrees/MLVR_develop/` | 游离目录（非注册 worktree），内容为 task01r 工作副本；`diff -r` 显示与正式档案不一致 |
| 3 | 该副本 `logs/verify_exact_tally_output.txt`、`smoke_test_output.txt` | AIMC 工作区、AIMC 全部历史与正式档案中**均无同名文件** → 唯一副本，属有价值证据 |
| 4 | `MLVR_develop/20260904_01_…/README.md` | 引用的 `AIMC_WWiteration/docs/journal_revision/task01r_…` 路径实测不存在（AIMC 仅有 `task_01r_mesh_tally_repair_codex`） |
| 5 | `RMC/.gitmodules` | 11 个 submodule 来自团队 GitLab（分支 `RMC_depend`）；6 个已初始化、5 个未初始化 |
| 6 | 全工作区 `.git` 扫描 | 仅 3 个主仓库 + 6 个已初始化依赖 submodule + 1 个注册 worktree |

**影响面**：只涉及工作区形态与文档；不改变 RMC/AIMC 代码、基准或任何物理结论。AIMC 的 `.gitignore` 已忽略 `.claude/`，遗留目录从未进入版本控制。

**为什么之前没做/没发现**：worktree 由 AI 工具自动创建且无回收机制；task01r 的原始输出一直留在工作副本里，未被纳入档案。

---

## 2A. 物理解释与可证伪假设（模式 C 必填）

（本任务为模式 B，2A 节不适用：无物理结论或统计解释。）

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A（采纳） | tag 保留未合入提交 → 移除 worktree/分支/游离目录；补录缺失日志；新增只读状态脚本；不动 RMC submodule | 清理动作不可逆（但提交已由 tag 保留）；新增一个脚本文件 | ★推荐 |
| B | 只删游离副本，保留 worktree 与分支 | 遗留结构继续存在，状态脚本会持续提示 | |
| C（最小改动） | 只补录证据，不做任何清理 | worktree 与分支永久滞留，问题不解决 | |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：方案 A（用户 2026-09-17 指示“按照你建议的方案顺序执行”；方案顺序为：清理 worktree → 增加状态脚本 → RMC submodule 不动）。
- **决定人 / 日期**：用户 / 2026-09-17。
- **理由与约束**：worktree 里的 `3c74a11` 未合入主线，因此**不得直接销毁**——先打 tag 再清理；`RMC/` 及其 submodule 属团队资产，不修改；补录证据前必须确认其唯一性。

**人类理解确认（模式 C 必填，由人确认或转述后确认）**：（模式 B 不适用；本任务不含物理判断。）

**变更卡（模式 B/C 必填）**：
| 项 | 内容 |
|---|---|
| 问题与风险 | AI 工具遗留的 worktree 与游离副本造成仓库结构混乱；task01r 的原始验证日志被遗落，档案缺少可追溯证据 |
| 拟改动 / 不改动 | 清理 `.claude/worktrees/` 两个目录、打 tag 保留未合入提交、补录日志并修正档案引用、新增 `tools/repo-status.sh`；不改 RMC submodule 与 AIMC 代码 |
| 预期因果链 | 证据唯一性确认 → 先保留后删除 → 档案引用更新 → 状态脚本使三仓状态可一键核对，防止类似残留再次被忽略 |
| 验证与失败停止条件 | 若发现日志已有等价归档则不再补录；若 `git worktree remove` 报脏则停止并人工确认；脚本必须只读且不修改任何仓库 |
| 回滚方式（若适用） | 提交由 tag `archive/worktree-agent-a97cdf8e33723c40c` 保留，可随时恢复分支；日志为纯复制；脚本可整体删除 |

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 盘点仓库结构 | `find . -name .git`、`git worktree list`、`submodule status` | 确认 3 个主仓库 + 11 个 RMC submodule（5 个未初始化）+ 1 个注册 worktree |
| 2 | 判定 worktree 提交去留 | `git cherry`、`patch-id`、`diff` | `3c74a11` 未合入主线 → 采用“先 tag 后删除” |
| 3 | 补录唯一证据 | `cp` 两个日志到 task01r 档案 `logs/` | 日志为唯一副本，已纳入档案（SHA256 见第 6 节） |
| 4 | 修正档案引用 | `MLVR_develop/2026-09/20260904_01_…/README.md` | 标注补录来源与两个失效的 AIMC 路径 |
| 5 | 清理 worktree | `git tag` → `worktree remove` → `branch -D` → `rm -rf` → `worktree prune` | 仅剩主工作区 |
| 6 | 新增状态脚本 | `tools/repo-status.sh` | 三个仓库状态一键可查，只读 |

**代码改动**：见 [changes.diff](changes.diff)，摘要：
- 新增 `tools/repo-status.sh` —— 只读多仓库状态检查
- 更新 `MLVR_develop/2026-09/20260904_01_…/README.md` —— 证据引用修正
- 新增 `MLVR_develop/20260904_01_…/logs/` —— 补录的原始验证输出
- 未改动 RMC/AIMC 任何源码或历史

生成方式：本任务改动均在根仓库。

> `changes.diff` 只包含已跟踪文件的修改（`INDEX.md`、`20260904_01` 的 README）；新增的 `tools/repo-status.sh`、补录的 `logs/` 与本档案属未跟踪文件，不在 diff 中。
```bash
git -C ../../RMC diff > changes.diff
# 改原型则：
git -C ../../AIMC_WWiteration diff > changes.diff
```

---

## 6. 验证 / 实验记录（④ · Agent 填，要贴真实输出）

| 验证项 | 命令 | 结果 |
|---|---|---|
| worktree 清理 | `git -C AIMC_WWiteration worktree list` | 仅剩主工作区 |
| 提交保留 | `git -C AIMC_WWiteration tag -l 'archive/*'` | `archive/worktree-agent-a97cdf8e33723c40c` 指向 `3c74a11` |
| 证据唯一性 | 全仓 `find` + AIMC `git log --all` | 无其他副本；Claude 报告目录从未提交 |
| 补录日志 | `sha256sum logs/*.txt` | 两个文件哈希记录如下 |
| 状态脚本 | `bash -n` + 实际运行 | 三仓库均正确显示 |

```
=== AIMC worktree list（清理后）===
/home/workspace/AI_MC_WW_interation/AIMC_WWiteration  9d74929 [feature/3d-two-group]

=== tag 保留的未合入提交 ===
archive/worktree-agent-a97cdf8e33723c40c 实现 prior_residual_unet 及 FOM 有效响应门控

=== 补录日志 SHA256 ===
69538a482b56fae1a80334d5f001cbbf6c5616c58cc1735744e369542912ba51  logs/smoke_test_output.txt
18ece300aa2af2046d5012e8f19c47271c6d0a74b8654e0777ad9598aea30799  logs/verify_exact_tally_output.txt

=== tools/repo-status.sh（节选）===
── 根工作区（本仓库，GitLab + GitHub 双镜像）
   分支   : main
   同步   : 已同步  (origin/main)
── RMC（团队仓库，独立 git）
   分支   : Neural_Network_WW_Iteration
   Submodule: 11 个（未初始化 5，编译时才需要 update --init）
── AIMC_WWiteration（原型仓库，独立 git）
   分支   : feature/3d-two-group
   工作区 : 0 修改 / 1 未跟踪
     - article/成都会议/成都会议论文投稿版.pdf
```

**实验设置（算法实验必填）**：本任务为工作区治理，不涉及训练/数值实验，不适用。

**未覆盖到的验证**：未验证 AI 工具后续版本是否仍会在 `.claude/worktrees/` 下创建目录（脚本会提示 worktree 数量）；未处理 AIMC 中未跟踪的会议论文 PDF（属其自身仓库事务）。

---

## 6A. 结果解释卡（模式 C 必填）

| 问题 | 解释 |
|---|---|
| 结果支持/否定了哪个假设？ | （模式 B，不适用。） |
| 证据等级与治理标签及其依据？ | （模式 B，不适用。） |
| 通过/失败在物理或工程上分别意味着什么？ | （模式 B，不适用。） |
| 不可外推的边界是什么？ | （模式 B，不适用。） |
| 下一步是否需要升级范围或另立任务？ | （模式 B，不适用。） |

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：工作区仓库结构已理清：3 个主仓库保持独立（现状正确，不建议 submodule 化）；RMC 的 11 个依赖 submodule 保持不动（未初始化 5 个属正常）；AI 工具遗留的 worktree 与游离副本已清理，未合入提交以 tag 保留，唯一证据已补录进档案。新增 `tools/repo-status.sh` 供日常一键核查。
- **遗留问题 / 后续待办**：1) `20260904_01` 档案引用的 Claude 报告路径在 AIMC 缺失（仅有 Codex 版本），如需恢复应从会话转录或另存副本；2) AIMC 有 1 个未跟踪的会议论文 PDF，由其自身仓库决定是否纳入版本控制；3) `RMC/dependencies` 有 5 个未初始化 submodule，完整编译前需 `submodule update --init --recursive`。
- **知识库同步**：无需更新 `MLVR_Knowledge/`。
- **是否已提交**：待提交（根仓库 `main`）。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-09-17 19:17 | 立项 |
| 2026-09-17 | 完成多仓库盘点，确认三类来源 |
| 2026-09-17 | 用户指示按建议顺序执行 |
| 2026-09-17 | worktree 清理、证据补录、状态脚本完成并验证 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 多仓库盘点 | `find`、`worktree list`、`submodule status` | 识别 3 类来源 |
| 3 | worktree 提交判定 | `git cherry`、`patch-id` | `3c74a11` 未合入 → 先保留后清理 |
| 4 | 证据唯一性核查 | 全仓查找 + AIMC 历史 | 两个日志为唯一副本 → 补录而非删除 |
| 5 | 清理与补录 | tag / remove / branch -D / rm -rf / prune + cp | 完成 |
| 6 | 新增脚本并验证 | `tools/repo-status.sh` | 语法与运行均通过 |
| 7 | 归档 | INDEX + 本档案 | 待提交 |

**模式 C 必填；A/B 可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
