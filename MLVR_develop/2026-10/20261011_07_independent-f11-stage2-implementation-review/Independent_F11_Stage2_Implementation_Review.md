# independent-f11-stage2-implementation-review

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-10-11 |
| 状态 | 已完成（**NEEDS CORRECTION**；受限动态门禁通过，但保留两个 P1 API完整性缺口） |
| 任务类型 / 模式 | F11 Stage 2 实际生产实现与动态证据独立审核 / C |
| 报告人 | Claude |
| 审核对象 | RMC 当前 working tree；Task 05 实际补丁、测试程序与 `gates-04` 原始证据 |
| RMC 基线 | `330f091eb0296e0d0124237ba7d9a22b81aee852`，分支 `Neural_Network_WW_Iteration` |
| 审核档案 | 本任务；Task 06 的 `DESIGN REVIEW ONLY` 历史结论保留不覆盖 |

## 1. 目标与范围

独立审核 Stage 2 是否真实实现：一次模型初始化、同一进程内多次 Forward/Adjoint fixed-source half-run、每轮与独立 fresh-process oracle 严格一致。

本轮只读审核：不修改 RMC、Task 05、reference、核数据库、STATUS、知识库或 Stage 3；不 commit/push；不修复发现的问题。

**物理解释：** 每个 half-run 的统计量只能使用本轮源历史及后代，分母必须是本轮实际源权重和；Forward/Adjoint 切换必须清除并重建角色相关算子、cutoff、particle/cache 和 WW 派生界限。动态 acceptance 必须同时证明数值等价和状态没有跨轮污染。

## 2. 做法与证据

### 2.1 事前独立检查表

在读取 Task 05 最终 PASS 结论前写入 [logs/pre-implementation-review.md](logs/pre-implementation-review.md)，预先规定：

- 一次初始化 → 每轮 CLEAR/SET/REBUILD/CHECK → 唯一 Stage 1 execution core → 唯一 finalizer；
- FixedSource、Tally、ACE/Material、ParticleState、ExternalSource、RNG、WW、Timer/Output 的 owner 状态；
- 真实源权重 hook、W0/D/N、Type2 子流、WW 实际查窗与 fresh oracle；
- G0、Gate 1–7 的 PASS/FAIL/INCONCLUSIVE/NOT RUN 判定标准；
- H2O/非裂变结果不得外推为通用裂变连续 F/A。

### 2.2 源码审核产物

- [logs/source-diff-audit.md](logs/source-diff-audit.md)：当前真实 diff、29文件范围、public API、唯一 core、G0 链接所有权。
- [logs/state-ownership-review.md](logs/state-ownership-review.md)：逐 owner PASS/FAIL/NOT VERIFIED。
- [logs/risk-register.md](logs/risk-register.md)：独立确认的剩余 P1/P2 风险。

### 2.3 动态证据审核产物

- [logs/gates-verification.md](logs/gates-verification.md)：G0/Gate 1–7 矩阵、原始证据与独立复核等级。
- [logs/independent-numerical-comparison.md](logs/independent-numerical-comparison.md)：独立读取 FF、FAF、AA、WW 原始快照/receipt/trace 的结果。

Task 05 的实际源文件清单与当前 working tree 一致：24 个 tracked 修改、5 个 untracked 文件，共 29 个批准文件。RMC 当前仍为基线 commit 加未提交 Stage 2 改动；本审核没有修改它。

## 3. 关键独立结果

### 3.1 生产 API 与生命周期

**SOURCE FACT：PASS。** 当前存在正式 public API：

- `InitializePreparedFixedSourceRuns`
- `RunPreparedFixedSource`
- `FinishPreparedFixedSourceRuns`

它们在 `CalMode.h` 与 `PrepareFixedSourceRun.cpp` 中实现。`RunPreparedFixedSource` 调用 Stage 1 的 `ExecuteFixedSourcePrepared`，随后只调用一次 `FinalizeFixedSourceRun`；没有第二份 batch/history/descendant 输运 loop。[PrepareFixedSourceRun.cpp:257-275](../../../RMC/src/PrepareFixedSourceRun.cpp#L257-L275)

**SOURCE FACT：PASS。** ordinary `CalcFixedSource` 仍保留原 wrapper/core/finalizer，新增内容为 prepared-process 冲突保护；Task 05 的 29文件 diff 未重写输运算法。

**DYNAMIC EVIDENCE：PASS。** 当前 test driver 的 persistent 模式调用正式 public API，fresh 模式走普通 `RunCalculation`，不是把新 Prepare 当 fresh oracle。

### 3.2 三项 Task 06 修订专项审核

| 修订项 | 源码/证据判断 | 状态 |
|---|---|---|
| G0 全局对象唯一所有权 | test CMake 从 RMC source list 精确排除 `main.cpp`，加入 test-only `globals.cpp`；linkage result 记录694个共同生产 TU、每个 executable 一份 main/单例、编译选项一致；test OFF/ON 检查也存在。 | **PASS**（Linux serial） |
| 单位源权重与 W0 | `CheckPreparedSourceDefinition` 限制单一普通 neutron point source、无 distribution/transform/surface/fission source、unit source fields；`SampleFixSource` 在普通源抽样完成后、alive/geometry kill 前调用 owner hook；Run 在 Finalize 前核验 sampled=N、min=max=1、W0=N、completed=N、D=N。 | **PASS**（受限白名单） |
| 单轮计时与旧 FOM | receipt 使用局部 `steady_clock` 的 prepare/transport/tally-finalize 区间并校验 `mcSeconds`；旧 StatisticsTester 明确输出 `legacy_mixed_not_per_run`、`statisticsFomIsRunMetric=false`，比较器只允许封闭时间字段例外。 | **PASS with explicit limitation**；旧 FOM 不是新 prepared per-run metric |

### 3.3 独立 receipt 复算

未导入 Task 05 comparator 的 standalone 读取结果：

```text
rows=34 half_runs=34 histories=17500
all_N_D_W0=True
timing_scope_values=['legacy_mixed_not_per_run'] [False]
source_count_matches=True
finalize_once=True
roles=['A','F'] WW=['ww-0','ww-1','ww-2']
```

所有最终 receipt 行的请求 N、完成 N、ProcessTally denominator、采样次数、W0 和最小/最大初始权重一致；所有 source event 数量为 N；每轮 `FINALIZE_ENTRY=1`。

### 3.4 独立原始数值/状态复核

**DYNAMIC EVIDENCE：PASS（抽查 FF/FAF/AA/WW）。**

- FF comparator：exit 0，physical tolerance 0，errors 0；差异仅在事前允许的时间/FOM字段。
- FAF：exit 0，physical tolerance 0，errors 0；三轮 raw/final/derived/start/end 语义数据匹配 fresh。
- AA：exit 0，physical tolerance 0，errors 0；两轮 A 数据匹配 fresh。
- WW：exit 0，physical tolerance 0，errors 0；OFF→WW1→WW2→OFF 匹配 fresh。
- 抽查 persistent/fresh `1-raw.json` SHA256 均为：

```text
d7f444dd98fe6f55e57245834681d1b4dfc4c15d0dcdd8c656d6f867bd4d742b
```

- 独立解码 receipt denominator bit patterns 得到 `1000.0`、`1500.0`、`2000.0`，与对应 N 相等。
- WW1/WW2 raw trace 记录实际事件：

```text
WW1: SPLIT=2072, ROULETTE=3397, BANK=3975, WW_QUERY=42711
WW2: SPLIT=3313, ROULETTE=5675, BANK=7499, WW_QUERY=76808
```

- persistent/fresh identity 中的 ASLR 地址不作跨进程字节比较；语义状态、raw 数据和统计结果比较不受此影响。

## 4. Gate 判定

| Gate | 结果 | 独立审核说明 |
|---|---|---|
| G0 | **PASS** | 实际编译/link、globals/main 唯一性、test OFF/ON 与 compile options 证据可追溯。 |
| Gate 1 | **PASS** | `ordinary-comparison-final-03/results.json`：123/123，physical tolerance 0；最终 CTest：10/10，exit 0。未重新运行完整普通矩阵。 |
| Gate 2 FF | **PASS** | 真实 persistent/fresh raw、receipt、trace 与 comparator 抽查一致；允许的时间例外已列明。 |
| Gate 3 FAF | **PASS** | 三段 fresh 对照、role/cutoff、derived、raw/final 快照一致。 |
| Gate 4 AA | **PASS with limitation** | 两段 A 与 fresh 一致；只证明当前非裂变受限模型的派生清理，不证明 fissile F/A。 |
| Gate 5 WW | **PASS** | WW 三界、查询与真实 split/roulette/bank，OFF 回退 evidence 均存在。 |
| Gate 6 reuse | **PASS** | 20轮复用、一次 raw/tally 初始化、稳定 registry/FD；RSS增长84KiB，低于4MiB阈值。未重新测资源。 |
| Gate 7 negatives | **PASS** | final negative results 保留预期非零退出、无成功 receipt、state unchanged；source-weight selftest 7/7。未重新执行全部66 child process。 |

Gate 1–7 的 PASS 表示证据审核通过，不表示本轮重新执行了全部生产实验。

## 5. 剩余问题与严重性

### P1 — 模型定义指纹未覆盖 universe 内容

**SOURCE FACT：** [PrepareFixedSourceRun.cpp:46-89](../../../RMC/src/PrepareFixedSourceRun.cpp#L46-L89) 的 definition fingerprint 记录 `geometry.p_vUniverse.size()`，但没有序列化 universe 的 fill/transform 内容；Run 只在 definition 不变时接受绑定模型。[PrepareFixedSourceRun.cpp:225-227](../../../RMC/src/PrepareFixedSourceRun.cpp#L225-L227)

**影响：** caller 若在两轮之间修改 universe 内容而不改变 vector size，模型变更可能不触发 guard，后续输运会接受已变化的几何。

**性质：** 未在正向 gates 中发生；是 public API bound-model integrity 缺口。

**最小修正：** fingerprint 所有 transport-relevant universe/fill/transform 字段，或将绑定模型数据设为不可变。增加 negative mutation test：完成一轮后改 universe 字段，要求在 CLEAR 前拒绝且旧结果不被清除。

### P1 — WW 参数完整性验证不充分

**SOURCE FACT：** Run 检查 lower 及 lower×WUPN/WSURVN 的有限性，但没有显式要求 WUPN、WSURVN、MXSPLN 自身为 finite/positive/有效范围；native install 使用这些参数生成 survival/upper 和 splitting。[PrepareFixedSourceRun.cpp:243-255](../../../RMC/src/PrepareFixedSourceRun.cpp#L243-L255)，[WeightWindows.cpp:296-317](../../../RMC/src/WeightWindows.cpp#L296-L317)

**影响：** 手工构造或 caller mutation 的 prepared model 可绕过普通 parser 的参数校验，潜在产生零 survival、无效 roulette/splitting 或不符合 contract 的 WW 行为。

**性质：** 正向 WW 输入是合法的；该缺口尚未被正向门禁触发，属于 API 负例覆盖不足。

**最小修正：** 在 CLEAR 前对 WUPN/WSURVN/MXSPLN 做 finite、positive 和 contract-range 校验；新增 malformed-parameter negative case，确认无输运、无成功 receipt、旧结果不被清除。

### P2 — legacy StatisticsTester FOM 仍是 process-cumulative

**SOURCE FACT：** `StatisticsFunc.cpp:183-218` 使用全局 `OTimer[Total]`；Total 从 `OutputHeading` 启动，到 `OutputEnding` 才停止。Stage 2 已明确将其标为 `legacy_mixed_not_per_run`，且 `statisticsFomIsRunMetric=false`。

**影响：** 旧 FOM 不能解释成新的 per-half-run FOM；但这已是显式限制，不是隐含错误。

**最小修正：** 保持当前限制并禁止将旧 FOM用于MLVR指标，或未来另行批准并实现 run-scoped statistics timing，同时保持 ordinary path 不变。

## 6. 最终判断

```text
NEEDS CORRECTION
```

理由：

- 受限 Linux serial / standard MGACE / neutron fixed-source / Type2 / strict unit source whitelist / Cartesian TL / native WW profile 已真实实现；
- G0、Gate 1–7 的自验结果经独立源码、证据、receipt 和 FF/FAF/AA/WW 抽查后总体可信；
- 旧 Task 06 提出的三项设计修订已处理：G0 singleton 所有权已实现，源权重在实际采样控制流检查且 N=D=W0 有 receipt 证据，旧 FOM 被明确排除为新 per-run metric；
- 但 public prepared API 仍允许两类 bound-object 变更/非法 WW 参数绕过既有 guard，属于在接受更广泛生产使用前必须修正的 P1 完整性问题。

因此不能给出 `ACCEPT` 或 `ACCEPT WITH LIMITATIONS` 作为“当前实现无需修正”的结论。

## 7. 用户问题的直接回答

1. **是否真实实现同进程多次 fixed-source？** 是，在明确受限 profile 内。
2. **是否只完整初始化一次？** 是；动态计数、registry、raw identity 和复用 evidence 支持这一点。
3. **FF / FAF / AA 是否与 fresh 一致？** 是，已抽查的最终 raw/final/derived/trace/receipt 证据一致；FF仅时间/FOM例外。
4. **RNG、tally、source、WW、伴随截面是否污染？** 在受限正向 gates 中未发现污染；但模型 universe mutation 和 malformed WW parameter guard 仍有 API 缺口。
5. **普通 RMC 是否保持？** 现有证据支持：123/123 ordinary comparison，原9个CTest加source audit共10/10。
6. **G0、Gate 1–7 是否完成？** Task 05 的受限 G0/Gate1–7 已完成；本轮独立审核为全部 PASS，Gate4附非裂变限制，且并未重新运行全部门禁。
7. **物理/功能/并行限制？** 非零裂变、MPI/OpenMP/AIS/Python prepared numerical lifecycle、CE、耦合粒子、restart/surface source、复杂/任意加权分布源、完整 F11 Bootstrap/K/Field/TARGET/外部闭环仍未开放；W13与旧 writer 语义未修复。
8. **是否建议用户验收 Stage 2？** 不建议无条件验收当前 public API；应先修复两个 P1 integrity guard 并补负例，再验收受限 Stage 2。
9. **是否进入 Stage 3？** 否。Stage 2 目前需要 correction；不得自动开始 Stage 3。

## 8. 提交状态

本独立审核未修改 RMC、未修改 Task 05、未修改 reference/核数据库，未 commit/push。RMC 当前仍为 `330f091e` 加本地 Stage 2 working-tree 改动。Task 05 的 29文件 patch 和本审核档案均等待用户后续决定。

## 9. 过程记录

| 时间 | 事件 |
|---|---|
| 2026-10-11 | 读取工作流上下文、STATUS、AGENT_CONTEXT、KB04；确认 Task 05 已实施且 RMC 为330f基线加本地改动。 |
| 2026-10-11 | 建立 Task 07；在读取 Task 05最终 PASS摘要前写入独立 pre-implementation criteria。 |
| 2026-10-11 | 审核29文件实际diff/untracked文件、public API、唯一core、各owner reset/rebuild和G0 CMake/globals。 |
| 2026-10-11 | 审核 final gates-04、ordinary comparison、negative evidence、linkage、receipt、comparator selftest和失败台账。 |
| 2026-10-11 | 独立抽查 FF/FAF/AA/WW raw snapshots、trace、receipt，并独立复算 N/D/W0、seed/offset、事件与时间标签。 |
| 2026-10-11 | 发现并记录 universe fingerprint 与 WW parameter validation 两个 P1 integrity gaps；保留 P2 legacy FOM限制；停止等待用户决定。 |
