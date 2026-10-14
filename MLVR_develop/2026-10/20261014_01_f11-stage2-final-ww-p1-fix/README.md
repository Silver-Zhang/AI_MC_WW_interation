# F11 Stage2 final WW P1 fix

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-10-14 |
| 状态 | 已完成（**READY FOR INDEPENDENT REVIEW**） |
| 任务类型 | 定向缺陷修复 / 验证 |
| 任务模式 | C — 深度物理研究与学习 |
| 关联知识库条目 | F11-lifecycle |
| RMC 分支 / HEAD | `Neural_Network_WW_Iteration` / `330f091eb0296e0d0124237ba7d9a22b81aee852` |
| 提交状态 | 未 commit、未 push、未切分支 |

---

## 1. 目标与范围（① 立项）

**要做什么**：按用户限定授权关闭 Task03 发现的两个 P1：MG native WW 原始粒子能量在整数能群转换前的安全拒绝，以及独立 `InstallPreparedNativeState()` 的 lower 数值验证。

**涉及什么**：仅当前 RMC 未提交 Stage2 工作树的 `src/WeightWindow.h`、`src/WeightWindows.cpp`、`src/PrepareFixedSourceRun.cpp` 和现有 lifecycle driver。未修改 `GetMgCs.cpp`、`DoMeshWeightWindow.cpp`、固定源核心循环、核数据、reference 或冻结设计。

**怎样算完成**：非法 raw MG energy 在调用 `GetErgValue()` 前拒绝；Run 与 enabled Install 使用同一无副作用 lower 校验并在 Install 写 state 前完成；聚焦 negative/sanitizer 与代表性零容差 persistent/fresh regression 通过。

**原始材料**：任务授权 prompt；Task02 energy-bin repair；Task03 final review；当前两仓库身份与 affected file 修复前 SHA256 记在本地 `/tmp/20261014_01_f11-stage2-final-ww-p1-fix/`。

**物理解释**：MG `p_dErg` 在 native WW 路径代表离散群号，合法群号必须先安全映射到物理群中心能量才可选权窗。WW lower 必须为正有限，且推导出的 survival/upper 和可分裂粒子数必须仍在数值/整数表示域内；否则不能让异常输入改写已经安装的权窗或输运阈值。

---

## 2. 做法与证据（② 设计 · ④ 实施）

**修改前确认**：根仓库 `main/0bdd63d` 干净；RMC 为 `Neural_Network_WW_Iteration/330f091e`，保留既有 24 tracked + 3 untracked Stage2 项。两个 P1 在 live source 中复现：`GetWeightWindowEnergy()` 直接进入 `GetErgValue()` 的 `int(dParticleErg + .5)`；Install 只检查 shape，而 lower/derived/split 规则只在 Run。

**方案选择**：

1. 在 `CDWeightWindow::GetWeightWindowEnergy()` 增加 native MG WW 局部 guard，先拒绝 NaN/±Inf 与不能安全转换为 `[1, group_count]` 的有限群坐标，再调用未改变的 `CDAceData::GetErgValue()`。不修改共享 `GetErgValue()`，避免影响 tally、速度和非 WW 调用者；合法群号的原有映射和物理群中心不变。
2. 在 `CDWeightWindow` 提取 `ValidatePreparedNativeLowerBounds()`，逐字复用 Run 中的 lower、derived survival/upper、`MXSPLN` 有限性和 cross-window ratio 合同。Run 和 enabled Install 均调用它；Install 仅在 definition/shape/lower 数值全通过后才写 mode、cutoff 或 WW 数据。

**实施要点**：

- `RMC/src/WeightWindow.h`：声明共享 lower validator。
- `RMC/src/WeightWindows.cpp`：增加 raw MG guard；实现无副作用 validator；Install 在任何 state mutation 前调用它，并保护 disabled WW 的 empty-lower 合同。
- `RMC/src/PrepareFixedSourceRun.cpp`：删除重复 per-lower loop，改调 owner helper，保留 role/identity/topology checks。
- `RMC/tests/prepared_fixed_source_lifecycle/driver.cpp`：增加 real native WW conversion-entry negative mode；补充 direct Install lower mutations、完整 WW/mode/cutoff state snapshot，以及先安装合法 WW 后再拒绝非法 Install 的路径。
- 精确增量见 `correction.diff`；最终 affected source SHA256 见 `source-sha256.txt`。

**验证输出（本次实际执行）**：

```text
Normal isolated build: RMC + RMCPreparedLifecycle exit 0
CTest prepared_source_weight_audit: 1/1 passed

Raw MG energy production entry guard:
  NaN, +Inf, -Inf, 0, group_count+1: 5/5 rejected
  reason=WW lookup: invalid multigroup particle energy

Direct Install lower negatives:
  NaN, +Inf, -Inf, 0, -1, denorm, 1e308, cross-window ratio: 8/8 rejected
  every case: REJECTED_INSTALL state_unchanged=1
  valid direct Install: INSTALL_SUCCESS, expected lower/survival/upper installed
  legal WW followed by NaN direct Install: state_unchanged=1

Targeted sanitizer (-fsanitize=address,undefined,float-cast-overflow,
_GLIBCXX_ASSERTIONS): same MG 5/5 and lower 8/8; no sanitizer diagnostic.

Persistent/fresh representative regression, physical tolerance 0:
  multi-energy WW OFF→1→2→OFF: passed=true, errors=[]
  FAF + WW: passed=true, errors=[]
```

Detailed raw commands, stdout/stderr, source copies, build products and snapshots remain local at `/tmp/20261014_01_f11-stage2-final-ww-p1-fix/`; selected hashes are in `evidence-manifest.json`.

**未覆盖到的验证**：未重跑完整 38-pair/20-run reuse matrix、ordinary before/after full matrix或全部历史 negatives；这些不受两个局部 guard 影响，Task02 保存证据仍为历史依据。未验证 MPI/OMP、CE、coupled particles、ordinary malformed parser、full-program/leak sanitizer、physical source at `1e22` 或 Stage3。sanitizer 是 focused lifecycle binary，leak detection disabled。

---

## 3. 决策记录（③ · 人拍板）

- **决定**：用户授权 prompt 明确允许仅修复 P1-WW-01 与 P1-WW-02，并规定最小文件范围、不得 commit/push/进入 Stage3。
- **决定人 / 日期**：用户 / 2026-10-14。
- **约束**：不改冻结设计、核数据、reference、输运物理公式、RNG/Tally/生命周期无关逻辑；不 reset/checkout/clean。

| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| shared converter 的正常 caller 被改变 | guard 仅在 native WW `GetWeightWindowEnergy()`；不改 `GetErgValue()` | 合法 group mapping + representative persistent/fresh 零容差 | 仅反向应用本档 `correction.diff` 的 P1 增量，保留既有 Stage2 改动 |
| Install/RUN 规则漂移 | owner 共用一个 no-mutation helper；不新建规则 | direct Install + Run path 负例，state unchanged | 同上 |

**人类理解确认**：本任务只关闭两个 API safety P1 并提交自验；Task03 仍需独立复核，用户决定最终 Stage2 验收和是否提交 RMC。

---

## 4. 结论与边界（⑤ 归档）

**结论：READY FOR INDEPENDENT REVIEW。**

- **P1-WW-01：CLOSED（本次自验范围）。** Native MG WW 在 raw group coordinate 转换前拒绝非有限、零/负和超出 `1..group_count` 的输入；合法 `GetErgValue()` 映射未改。
- **P1-WW-02：CLOSED（本次自验范围）。** Install 与 Run 共享 exact lower/derived/split validation；所有 direct invalid lower 在 WW、mode、cutoff 写入前失败，包含已装合法 WW 后的拒绝。
- **Stage2：READY FOR INDEPENDENT REVIEW。** 这不是 Stage2 final ACCEPT，也不是提交批准；须由独立复核确认 source/dynamic evidence 后再由用户技术验收。

**不能推出什么**：不代表完整 RMC API、ordinary parser、MPI/OMP、full-program sanitizer/leak、MCNP WW 或 Stage3 已验证；也不替代 Task02 的完整 container/endpoint 证据或 Task03 的最终独立判断。

**遗留 / 下一步**：提交独立复核；若复核发现实际调用边界或物理 regression 不符，停止并按新结论处理。不得自行开始 Stage3。

**提交状态**：RMC 和根仓库均未 commit/push；没有 reset、checkout、clean 或 reference/nuclear-data 修改。

**结果解释**：Guard 不改变任何合法粒子的群中心能量或 split/roulette 数学，只在原先可能进入未定义转换或非法状态写入的输入域提前中止。因此代表性 persistent/fresh 逐字段物理零容差通过支持“修复安全边界而不改合法输运”的假设，但不外推到未测 profile。

---

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-10-14 | 读取当前 shared RMC worktree、Task02/Task03；记录分支、SHA256 和已有未提交 Stage2 内容。 |
| 2026-10-14 | 证实两个 P1 仍在：MG integer cast 位于 lookup guard 前；Install 无 lower 独立验证。 |
| 2026-10-14 | 实施四个授权文件的最小增量；不改 shared converter 或 transport loop。 |
| 2026-10-14 | 私有 source/build 中 build、focused negative、float-cast-overflow sanitizer、CTest 与两组代表性 persistent/fresh 通过。 |
| 2026-10-14 | 提炼 patch/hash/结果，停止，等待独立复核与用户决定。 |

**证据等级**：本次 source inspection E1；focused dynamic execution E3；尚未独立复核为 E4。
