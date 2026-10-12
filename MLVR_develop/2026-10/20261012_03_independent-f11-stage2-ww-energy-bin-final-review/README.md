# independent-f11-stage2-ww-energy-bin-final-review

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-10-12 |
| 状态 | 已完成（**NEEDS CORRECTION**；不建议最终验收/冻结/提交） |
| 任务类型 | 独立最终技术复核 / 文档 |
| 任务模式 | C — 深度物理研究与学习 |
| 关联知识库条目 | F11 |
| 涉及文件 | `RMC/src/WeightWindows.cpp`、`RMC/src/DoMeshWeightWindow.cpp`、`RMC/src/GetMgCs.cpp`、`RMC/src/PrepareFixedSourceRun.cpp`；仅只读 |
| 分支 / 提交 | RMC `Neural_Network_WW_Iteration` / `330f091e`；Stage2 为未提交本地工作树 |

---

## 1. 目标与范围（① 立项）

**要做什么**：对 Task02 的 native WW energy-bin P1 定向修复进行独立最终复核，判断容器合同、有限哨兵、端点索引、prepared 生命周期放置、动态证据和剩余 P1 是否允许 Stage2 技术验收。

**涉及什么**：当前共享 RMC 工作树及 Task02 提炼证据；不改 RMC、核数据、reference、冻结设计或历史审核。

**怎样算完成**：预先写下判据后，对真实源码和归档证据分别标注 SOURCE VERIFIED / ARTIFACT VERIFIED / INDEPENDENTLY RECOMPUTED / NOT INDEPENDENTLY RERUN / NOT VERIFIED，并给出唯一分类。

**原始材料**：`logs/pre-review-criteria.md` 为接收 Task02 READY 摘要前写下的独立判据；Task02 的 `README.md`、`source-audit.md`、`negative-results.json`、`regression-results.json`、`evidence-manifest.json` 为只读输入。

**物理解释**：B 个能量边界只代表 B−1 个权窗区间；末界不能产生第 B 个访问。`1e22` 是本代码的有限 native 哨兵，不是可外推的物理源能量。非法容器、非有限能量和非法权窗下界必须在它们可改变输运状态或参与数组/整数转换前受控拒绝。

---

## 2. 做法与证据（② 设计 · ④ 复核）

**设计 / 定位**：先冻结容器、端点、所有权和负例判据；再直接检查 live RMC 的 validator、bind/Run/Install、lookup、MG energy conversion 及 Task02 结果/manifest。详见 `logs/source-audit.md`、`logs/negative-gate-review.md`、`logs/regression-review.md`、`logs/independent-comparison.md`。

**方案选择**：只读复核，未运行构建或输运。保存的 Task02 动态结果只作 artifact evidence；不把它表述为本轮独立重跑。

**实施要点**：无生产代码改动；新增本任务的判据、源码/负例/回归/风险复核记录和轻量 evidence manifest。

**验证输出**：

```text
Task02 archived results, independently regrouped:
  malformed definition negatives: 78/78 = 26 mutations × bind/after/install
  production owner lookup: 15/15
  targeted ASan/UBSan: 80/80 (3 translation units, leaks disabled)
  persistent/fresh comparisons: 38 = 2+3+2+4+3+20+4; physical tolerance 0
  CTest: 10/10

Current source review:
  Prepared definition/endpoint/container repair: PASS in its restricted native profile
  P1-WW-01 raw MG NaN/Inf conversion before finite lookup guard: OPEN
  P1-WW-02 direct Install lower-value validation independent of Run: OPEN
```

**未覆盖到的验证**：本轮没有重新编译、CTest、输运、sanitizer 或 fresh-process 比较；MPI/OMP、普通 parser/MCNP WW、全程序 sanitizer/leak、物理 `1e22` 源、Stage3 仍未验证。详见 `logs/regression-review.md`。

---

## 3. 决策记录（③ · 人拍板）

- **决定**（采纳什么方案）：仅执行独立只读最终复核；不修复、不提交、不进入 Stage3。
- **决定人 / 日期**：用户授权的 final review 范围；2026-10-12。
- **约束**：不得修改 RMC 生产源码、Codex 原始数据/结果、核数据库、reference 或冻结设计；不得 reset/checkout/clean、commit/push 或启动 Stage3。

**变更卡（C 模式）**：
| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| 复核误把自验当独立重跑 | 只写 Task03 档案；不改 RMC/基准 | 区分证据等级；有 P1 即 NEEDS CORRECTION 并停止 | 删除本任务文档即可，不触碰 RMC |

**人类理解确认**：本轮结论只决定是否建议验收；实际修复、提交和 Stage3 都需要用户另行决定。

---

## 4. 结论与边界（⑤ 归档）

**结论：NEEDS CORRECTION。**

Task02 已实质关闭上一轮的 prepared native WW definition container 与末界索引缺口：outer shape 在 neutron 索引前检查，有限 `1e22` 哨兵及 B−1 区间形状受校验，bind/Run/Install 放置正确，lookup 将末界夹到最后合法区间。Task02 保存的 78/78 定义负例、15/15 lookup、80/80 targeted sanitizer、38 persistent/fresh pair、ordinary single/multi WW 和 10/10 CTest 在归档内一致；但本轮未重跑。

最终验收仍被两个最小 P1 阻断：

1. **P1-WW-01**：MG transport 对 raw particle NaN/Inf 会在 lookup finite guard 前执行 `int(dParticleErg + 0.5)` 及群中心索引；direct lookup 测试不覆盖此转换前路径。
2. **P1-WW-02**：可单独调用的 `InstallPreparedNativeState()` 只验证 lower 长度，不验证 lower 的 finite/positive、派生 upper/survival 或 split-ratio 可表示性；这些只在 Run 检查，故 direct Install 可变更状态并写入非法窗口。

**不能推出什么（边界）**：不能据此否定 Task02 对定义容器和端点 bug 的修复；也不能声称完整 RMC、MPI/OMP、普通 MCNP WW、parser、安全、full-program sanitizer/leaks 或 `1e22` 物理输运已验证。MPI shared lookup 的 index/shape 残余为 out-of-profile P2，另行处置。

**遗留 / 下一步**：如用户另行授权，只需两项定向修复与相应 production negative/sanitizer 证据：raw MG energy 在转换前受控拒绝；将 existing lower/derived/split 校验抽为 Run 与 enabled Install 共用的无副作用 guard。修复后须再做独立复核。不得直接开始 Stage3。

**提交状态**：本轮未 commit/push；未修改 RMC。是否接受后续修复或将已存在 RMC 改动独立提交，均由用户决定。

**结果解释**：权窗将每个空间×能量区间中的粒子权重导向合适尺度，故 B 个界只允许 B−1 个窗。Task02 的末界夹取维持这一关系；但若非有限物理能量先被误当作群号，或独立安装者能写入非物理的下界，后续 split/roulette 就没有受控的物理输入域，不能以合法算例的确定性一致外推为 API 安全。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-10-12 14:01 | 建档并在接收 Task02 READY 摘要前写入 pre-review criteria。 |
| 2026-10-12 | 只读检查 live RMC 工作树、Task02 JSON/manifest/命令摘要；重算 78 与 38 的分组。 |
| 2026-10-12 | 定位 MG raw energy conversion 在 lookup guard 前，以及 direct Install lower 值验证不独立；判定 NEEDS CORRECTION。 |
| 2026-10-12 | 写入提炼报告、风险清单与证据等级说明；未改 RMC，停止。 |

**证据等级**：源代码路径为 E1（SOURCE VERIFIED）；Task02 留存动态日志/JSON 为 E3（ARTIFACT VERIFIED）；本轮未取得 E4 独立重跑。
