# root-legacy-assets-cleanup

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-17 |
| 状态 | 已完成 |
| 任务类型 | 工作区治理 / 遗留资产清理 |
| 任务模式 | B — 工程协作（默认） |
| 报告人 | 用户 + Agent |
| 关联知识库条目 | 无 |
| 涉及文件 | 根目录三份 `task*/` 遗留资产、根 `.gitignore`、`MLVR_develop/INDEX.md` |
| 分支 / 提交 | 根工作区 `main` ／ 未提交 |

---

## 0. 人类阅读摘要（模式 C 必填；A/B 按需）

（本任务为模式 B：删除根目录三份已被取代的遗留实验资产，并加入防误提交的忽略规则；工程结论见第 7 节。）

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：清理仓库根目录三份脱离工作流的实验资产备份（共 50 个文件、约 45.7 MB），并增加只作用于仓库根目录的防御性忽略规则，消除二进制被误提交的风险。

**范围**：仅根目录 `task08a_legacy_backup_20260905_WLxgxZ/`、`task08b_archive/`、`task08b_formal_archive_pre_r3_20260906T085153Z/` 与根 `.gitignore`；不修改 `RMC/`、`AIMC_WWiteration/`、基准、模型或任何已发布结论。

**验收标准**：
1. 三份遗留目录从根目录移除；
2. 删除前生成 SHA256 清单并留存轻量聚合证据；
3. 根 `.gitignore` 新增 `/task*/`（锚定仓库根目录），不影响 `MLVR_develop/` 下的任务档案；
4. `git status` 不再出现这些未跟踪目录。

**原始材料**：无报错日志；依据为用户 2026-09-17 的“方案1”决策与本轮只读取证输出。删除前清单存于 `logs/removed-assets/inventory-sha256.txt`。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：三个目录均在仓库根目录、未被跟踪、未被忽略、无任何档案引用；内容为 AIMC 原型 task08a/task08b 阶段的实验运行产物（`.h5` 结果、manifest、run.log）。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | `task08a_legacy_backup_20260905_WLxgxZ/task08_corrected/` | 41 文件 44 MB；15 个 `manifest.json` + 15 个 `result.h5` + 9 个 `run.log` + 2 个 csv；manifest 命令为 `scripts/main.py --variant … --pilot`，输出路径 `results/task08_corrected/…` |
| 2 | `AIMC_WWiteration/docs/journal_revision/task_08av_experiment_freeze_codex/task_08av_followup_review.md`（提交 `cf6e392`，2026-09-05 15:22） | 评审指出 `results/task08_corrected/` 下共 15 个 manifest 目录为 legacy 产物，fail-closed 收集器拒绝其中 13 个；本备份即该目录，于当日 15:49 移出 AIMC |
| 3 | `AIMC_WWiteration/docs/journal_revision/task_08ar2_formal_harness_codex/final_closure_report.md`（提交 `82d759d`，2026-09-05 19:05） | 原文：“Existing legacy `results/task08_corrected/` outputs are excluded from the R2 formal authority set.”；并要求 Task08B 不得复用 legacy corrected 产物 |
| 4 | `AIMC_WWiteration/results/task08b_formal/`（2026-09-06 17:14–17:24） | 当前权威正式数据（8 个方法），由 `scripts/task08/run_corrected_baseline.py` 生成 |
| 5 | `task08b_archive/20260906T024753Z/`、`task08b_formal_archive_pre_r3_20260906T085153Z/` | J0/J1 早期正式快照；实测 SHA256 与当前权威数据均不同（`4c38be…`、`d48ac0…`、`3dc889…`、`5d5f3c…` 对比当前 `af8c7b…`、`a7d835…`），属被取代的中间版本 |
| 6 | 全库检索 | 无任何任务档案或 AIMC 已跟踪代码引用这三个目录；AIMC 仅收集器默认路径与测试 fixture 提及 `task08_corrected` 路径名 |

**影响面**：只改变工作区形态与忽略规则；不影响 RMC/AIMC 代码、基准、模型与已发布结论。

**为什么之前没做/没发现**：task08a 线对应的任务档案 `20260905_03_task08a-experiment-freeze-harness` 至今仍是空白模板，其产物没有归属地，被临时移到根目录后一直未回收。

---

## 2A. 物理解释与可证伪假设（模式 C 必填）

（本任务为模式 B，2A 节不适用：无物理结论或统计解释。）

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A（采纳） | 确认已被取代后删除三目录，并新增根级 `/task*/` 防护规则；删除前留 SHA256 清单与聚合证据 | 删除后 legacy 产物不可再本地复查（其评审结论已固化在 AIMC 提交文档中） | ★推荐 |
| B | 仅删除 `.h5` 二进制，保留全部文本 | 目录仍留在根目录，仍需忽略规则，治理问题保留 | |
| C（最小改动） | 只加忽略规则、不删除 | 约 45.7 MB 二进制继续驻留 | |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：方案 A（用户 2026-09-17 明确选择“方案1”）。
- **决定人 / 日期**：用户 / 2026-09-17。
- **理由与约束**：三项独立证据表明数据已被取代——R2 正式收口报告把 legacy corrected 产物排除出权威集、fail-closed 收集器拒绝其中 13/15、当前 `results/task08b_formal/` 为更新且完整的权威数据；删除前必须留可追溯清单；不得触碰 `AIMC_WWiteration/` 与 `RMC/` 仓库内容。

**人类理解确认（模式 C 必填，由人确认或转述后确认）**：（模式 B 不适用；本任务不含物理判断。）

**变更卡（模式 B/C 必填）**：
| 项 | 内容 |
|---|---|
| 问题与风险 | 仓库根目录存在约 45.7 MB 未跟踪、未忽略的实验资产，任何 `git add -A` 都可能把二进制误提交进主仓库 |
| 拟改动 / 不改动 | 删除三份根目录遗留资产 + 在根 `.gitignore` 新增 `/task*/`；不改 RMC/AIMC 仓库、基准与结论 |
| 预期因果链 | 取证确认已被取代 → 留 SHA256 清单与聚合 csv → 删除 → 忽略规则阻止再次混入提交 |
| 验证与失败停止条件 | 若检索到任何档案或代码引用这些数据则停止删除；验证 `git check-ignore` 命中根级 `task*/` 且不误伤 `MLVR_develop/` 内路径 |
| 回滚方式（若适用） | 数据可由 manifest 记录的步骤重跑（旧管线，不保证与 R2 后管线一致）；忽略规则为单行，可直接撤销 |

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 删除前取证 | `sha256sum` 全量文件 + `du` 统计 | 约 45.7 MB / 50 个文件；清单存 `logs/removed-assets/inventory-sha256.txt`（61 行，含 50 条哈希） |
| 2 | 留存轻量证据 | 复制 `summary.csv`、`pairwise_response_consistency.csv` | 存 `logs/removed-assets/`，共 8 KB |
| 3 | 删除三份遗留资产 | `rm -rf task08a_legacy_backup_20260905_WLxgxZ task08b_archive task08b_formal_archive_pre_r3_20260906T085153Z` | 根目录 `ls` 已无 `task*` |
| 4 | 新增防护规则 | 根 `.gitignore` 末尾追加 `/task*/` | 规则仅锚定仓库根目录 |

**代码改动**：见 [changes.diff](changes.diff)，摘要：
- `.gitignore` —— 新增根级 `/task*/` 忽略规则，防止根目录再次混入实验资产
- `MLVR_develop/INDEX.md` —— 登记本任务行
- 未改动 `RMC/` 与 `AIMC_WWiteration/`，故不生成其 diff 快照

> `changes.diff` 是根仓库当前全部未提交差异（含 `MLVR_develop/INDEX.md` 中 2026-09-03 起其他任务的既有未提交登记行），不限于本任务的改动。

生成方式：
```bash
git -C ../../RMC diff > changes.diff
# 改原型则：
git -C ../../AIMC_WWiteration diff > changes.diff
```

---

## 6. 验证 / 实验记录（④ · Agent 填，要贴真实输出）

| 验证项 | 命令 | 结果 |
|---|---|---|
| 规则命中 | `git check-ignore -v task08x_probe/` | `.gitignore:52:/task*/   task08x_probe/` —— 命中 |
| 误伤检查 | `git check-ignore -v MLVR_develop/2026-09/20260905_03_task08a-experiment-freeze-harness/task_08a_experiment_freeze_claude/` | 未命中，未误伤任务档案 |
| 删除结果 | `ls -1` / `ls -d task*` | 根目录只剩既有文档与仓库；无 `task*` |
| 追踪状态 | `git status --short` | 不再出现三份遗留目录 |

```
=== 规则命中测试（根目录 task* 应被忽略）===
.gitignore:52:/task*/   task08x_probe/
=== 误伤测试（MLVR_develop 内 task_ 目录应不受影响）===
未命中 → 不误伤，符合预期
=== 残留检查 ===
根目录已无 task* 目录
```

**实验设置（算法实验必填）**：本任务为工作区清理，不涉及训练/数值实验，不适用。

**未覆盖到的验证**：未验证 AIMC 侧是否会在未来重跑旧管线再次生成 `results/task08_corrected/`；未检查服务器或其他机器上是否存在同类副本。

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

- **结论**：三份根目录遗留实验资产已删除，并以 SHA256 清单与聚合证据留痕。删除依据为：R2 正式收口把 legacy `results/task08_corrected/` 排除出权威集、fail-closed 收集器拒绝其中 13/15 产物、当前 `results/task08b_formal/` 为其后续权威数据。根 `.gitignore` 现以 `/task*/` 阻止根目录再次堆放实验资产。
- **遗留问题 / 后续待办**：1) `20260905_03_task08a-experiment-freeze-harness` 档案仍为空白模板，建议补齐或正式关闭；2) 建议在 `MLVR_develop/README.md` 明示“实验产物不得存放在仓库根目录”；3) 2026-09-03 起共 11 个任务档案尚未提交；4) 观察到 `20260904_01`/`20260904_02` 的档案已写“已完成”但 `INDEX.md` 仍记“待设计”，建议由对应任务复核台账。
- **知识库同步**：无需更新 `MLVR_Knowledge/`（未触及 RMC 能力与物理结论）。
- **是否已提交**：未提交；改动文件为 `.gitignore`、`MLVR_develop/INDEX.md` 与本档案。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-09-17 18:02 | 立项 |
| 2026-09-17 | 用户确认目标为 `task08a_legacy_backup_20260905_WLxgxZ` 及其同类目录，选择“方案1”（删除 + 忽略规则） |
| 2026-09-17 | 只读取证完成；保留 SHA256 清单；删除三目录并新增忽略规则；验证通过并归档 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 定位目录来源 | `manifest.json`、`summary.csv`、时间戳 | 确认是 AIMC `results/task08_corrected/` 的运行产物，2026-09-05 15:49 被移出 AIMC |
| 3 | 交叉核对 AIMC 文档 | `git grep task08_corrected` | 找到 task08av 评审与 R2 收口报告，明确 legacy 产物被排除出权威集 |
| 4 | 哈希比对 | `sha256sum` | 两份额外快照与其当前权威数据的哈希均不同 → 已被取代 |
| 5 | 引用检查 | 全库检索 | 无档案/代码引用 → 删除不影响可追溯性 |
| 6 | 执行清理并留证 | `rm -rf` 三目录 + `.gitignore` 追加规则 + 清单归档 | 完成，验证通过 |

**模式 C 必填；A/B 可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
