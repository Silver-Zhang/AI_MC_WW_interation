# f02-binary-source-identity

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-08-27 |
| 状态 | 已完成（有界 A 证据链闭合） |
| 任务类型 | 验证基础设施 / 证据恢复 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F02 |
| 涉及文件 | 任务侧构建 provenance、formal 重跑与分类文档；`RMC/` 源码仅读 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `6d208751...` + W9 diff `5eec...`；不提交/推送 RMC |

---

## 1. 任务定义（① 立项 · Agent 填）

**目标**：闭合 Claude 独立审核发现的冻结源码—二进制身份断裂：formal raw output 的 executable SHA256 是 `8fff...`，但其 RMC banner 内嵌 Git commit 为 `4d3e1...`；因此现有证据不能严格归属为“base `6d208751...` + W9 diff”的执行结果。

**范围**：仅任务侧构建目录、输入、raw evidence、日志与文档。不得修改 RMC 源码、核数据、reference/benchmark，且不得提交/推送/切换 RMC 分支。

**验收标准**：若获准，创建全新隔离构建目录并明确把当前 `RMC/` 作为 source；确认新 binary banner 显示 `6d208751...`、构建 source/HEAD/diff SHA256 归档；用该 binary 重跑依赖 A 的 40 angular + 10 density formal，保存 raw outputs，strict checker 通过，独立复核身份闭环。

**原始材料**：用户提供的 Claude 审核结论；任务 04 已保存 raw formal 证据；本任务将保存 configure/build identity、banner、重跑 raw output 与哈希。

---

## 2. 调研与设计（② 设计/定位 · Agent 填）

**背景**：任务 04 的 raw evidence 和 strict statistical gates 已被独立复核接受，但同一 binary 的 banner 显示 `4d3e1...`，而当前 RMC HEAD 为 `6d208751...`。`CMAKE_HOME_DIRECTORY` 确认构建目录 source 是当前 RMC，却不能证明 configure 时对应哪一个 Git HEAD；重新 `cmake --build` 后二进制 SHA256 仍为 `8fff...`，说明 banner 由配置时生成的版本文件或定义决定，不能将当前 source identity倒推给历史 binary。

**证据链**：
| # | 位置 | 说明 |
|---|---|---|
| 1 | 任务 04 angular/density `stdout.log` | 两类 raw formal banner 均显示 `Git commit : 4d3e1...`。 |
| 2 | 当前 `git -C RMC rev-parse HEAD` | 当前 HEAD 是 `6d208751...`，唯一工作树 diff SHA256 是 `5eec...`。 |
| 3 | `/tmp/mlvr_f02_rmc_build/CMakeCache.txt` | 当前 cache source 指向 `RMC/`，但 cache 不包含配置时的完整 Git identity。 |
| 4 | Claude 审核（用户提供） | 正确裁定 raw evidence 仅可严格归属 binary `8fff...`，不能归属声明的 frozen source snapshot。 |

**影响面**：这是证据身份问题，不是新的 RMC 物理 defect。当前 F02 必须维持 C；只有在新 binary + source snapshot 被完整绑定且 formal 重跑通过后才可恢复 A。

**为什么之前没做/没发现**：此前把 binary SHA256 与当前 source directory 视为充分 provenance，忽略 banner 记录了不同 commit。该不一致必须优先于任何 A 结论处理。

---

## 3. 方案选项（② 设计/定位 · Agent 填，给 2~3 个）

| 方案 | 做法 | 代价 / 风险 | 推荐度 |
|---|---|---|---|
| A：fresh configure/build + formal 重跑 | 从当前 frozen worktree 新建独立 build，记录 configure output、banner、source HEAD/diff、binary hash；重跑 50 条 formal。 | 计算成本高，但唯一闭合 source—binary—run 归属的方法。 | ★推荐 |
| B：只记录当前 binary hash | 继续使用 `8fff...` 并解释 banner 过时。 | 无法证明它由 `6d208751 + diff` 构建，不能恢复 A。 | 不采用 |
| C：维持 C | 不重跑，只如实保留身份缺口。 | 无计算成本，但 F02 不能评 A。 | 可接受 |

---

## 4. 决策（③ · **人拍板**）

- **采纳方案**：A — fresh configure/build + formal 重跑。
- **决定人 / 日期**：用户 / 2026-08-27（“批准”）。
- **理由与约束**：不得修改 RMC；不得更新 reference/benchmark 或删除失败输出。fresh build 必须从当前 source snapshot 运行并保存 configure/build provenance；所有新运行必须以 banner/source snapshot 一致的 binary 执行并保留 raw evidence。

> 未填写本节前，Agent 不得改动 `../RMC` 下的任何文件。

---

## 5. 实施记录（④ · Agent 填，逐步流水账）

| # | 操作 | 命令 / 位置 | 结果 |
|---|---|---|---|
| 1 | 建档与身份审计 | 用户审核、banner、Git/CMake cache | 确认 `4d3e1...` banner 与 `6d208751...` source snapshot 不一致；当前不可维持 A。 |
| 2 | fresh configure/build | `/tmp/mlvr_f02_identity_build` | 全新构建的 configure 记录 `GIT SHA: 6d208751...`；运行时 banner 同为 `6d208751...`，新 binary SHA256 为 `e14928e2...`。 |
| 3 | angular formal 重跑 | `logs/angular_formal_fresh_20260827/` | 40/40 structural pass；全部 raw run 均绑定新 binary。strict checker 对每 seed 与 aggregate 均通过。 |
| 4 | density formal 重跑 | `logs/density_formal_fresh_20260827/` | 10/10 structural pass；五个前/伴随对及合并互易性均通过，合并 $z=0.0946746946$。 |
| 5 | 回归与完整性 | fresh CTest、`logs/SHA256SUMS.txt` | `test_fixed_source_adjoint` 1/1 passed；六项清单经 `sha256sum -c` 全部成功。 |
| 6 | 独立审计 | GPT poly-bridge | ACCEPT：source→binary→banner→50 条 raw formal→strict gates→checksum 链路闭合；无阻塞项。 |

**代码改动**：RMC 无改动。若获准，仅添加任务侧构建和重跑工具。

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
| source snapshot | `logs/source_snapshot.txt`、`changes.diff` | HEAD `6d208751...`，仅 W9 工作树差异；diff SHA256 `5eec92f9...c756`。 |
| fresh configure / banner | `logs/fresh_configure.txt`、`fresh_banner_probe.txt` | configure 和运行时 banner 都为 `6d208751...`；tag `v3.5.0-alpha.0-303-g6d208751`。 |
| angular raw + strict | task 05 angular runner/checker | 40/40 structural pass；八个 case/mode 的逐 seed 和 aggregate 统计门均通过。 |
| density raw + strict | task 05 density runner/checker | 10/10 structural pass；五对及合并均 $|z|\le3$，合并 $z=0.0946746946$。 |
| fresh fixed-source regression | `ctest --test-dir /tmp/mlvr_f02_identity_build -R '^test_fixed_source_adjoint$'` | 1/1 passed（1.21 s）。 |
| checksum manifest | `sha256sum -c logs/SHA256SUMS.txt` | raw reports、strict reports、W9 diff 和 fresh binary 共六项全部成功。 |

```
fresh binary SHA256: e14928e256b022d50f3b6ef3f61c3f9f109564c7ebcd3f9a2cbc4a4c392f009e
angular_raw_runs=40
density_raw_runs=10
independent_audit=ACCEPT
```

**实验设置（若选择 A）**：复用任务 04 已冻结的 seeds、population、私有资产、mesh 和 strict gates；新增确定的 fresh configure/build command、source snapshot SHA256 和 binary banner/hash。

**未覆盖到的验证**：本任务只恢复冻结范围的 F02 A；photon/耦合粒子、CE、AIS/HDF5 核数据、delayed、GPT、MPI/OpenMP、Windows、反射边界及 F03/F04/F06/F07 不在范围内。

---

## 7. 结论与遗留（⑤ 归档）

- **结论**：fresh source—binary identity 与 50 条 formal raw evidence 均已闭合；独立审计 ACCEPT。冻结范围的 F02-B 恢复为 **A — Ready（有界）**。
- **遗留问题 / 后续待办**：继续既有 F03 审查；范围外能力不继承 F02 A。
- **知识库同步**：已同步 F02 矩阵、上下文、问题台账、物理导读与 INDEX。
- **是否已提交**：未提交/推送；RMC 未修改。

---

## 8. 时间线

| 时间 | 事件 |
|---|---|
| 2026-08-27 21:39 | 立项 |
| 2026-08-27 | 用户授权持续按建议执行；fresh build、50 条 formal、strict gates、CTest 和独立审计完成。 |

---

## 9. 工作日志（逐步操作记录）

> 设计/定位与实施过程中 Agent 实际执行的每一步（查了什么、命令是什么、结论是什么）。
> 目的：人不用看聊天记录也能复盘"结论是怎么得出来的"。
> 排查中出现的**误判与修正**也要如实记录（例如"曾按 X 分析，后经取证纠正为 Y"）。

| # | 操作 | 工具/位置 | 结果 |
|---|---|---|---|
| 1 | 立项建档 | `new_task.sh` | 生成文件夹 + logs/ + 模板 |
| 2 | 核对 banner、HEAD、diff、binary 与 CMake cache | RMC、任务 04、`/tmp` build | 身份断裂属实；未修改 RMC。 |
| 3 | 用户授权方案 A 及后续建议 | 用户请求 | 获准 fresh build、formal 重跑、严格检查和独立审计。 |
| 4 | 新隔离 configure/build | `/tmp/mlvr_f02_identity_build` | 配置时捕获冻结 HEAD；build 成功，保留 configure/build 输出。 |
| 5 | banner probe | recovered formal input | 新 binary banner 为 `6d208751...`；probe 因故意无效的临时数据目录终止，但版本身份已在读取数据前输出。 |
| 6 | 50 条 fresh formal | task 05 raw runners | angular 40/40、density 10/10 structural pass，原始输入/输出/exit code 均保留。 |
| 7 | strict / CTest / SHA256 | task 05 logs | angular、density strict 均 passed；CTest 1/1 passed；六项 checksum 全部成功。 |
| 8 | 独立复核 | GPT poly-bridge | ACCEPT；确认无 provenance 或统计阻塞项，建议恢复冻结范围 A。 |

**可选**：若人机讨论较深入，另写一份 [会话纪要.md](会话纪要.md)
（Q&A 脉络 + 共识 + 未决事项）。**注意：原始聊天转储不要存仓库**——其中可能含
口令/token 等凭据，纪要必须脱敏。
