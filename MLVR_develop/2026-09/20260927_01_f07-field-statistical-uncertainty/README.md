# f07-field-statistical-uncertainty

| 项 | 内容 |
|---|---|
| 立项日期 | 2026-09-27 |
| 状态 | 已完成（C — Verify，serial text-first Cartesian 子域） |
| 任务类型 | 只读功能审查 / 统计验证 |
| 任务模式 | C — 深度物理研究与学习 |
| 报告人 | GitHub Copilot |
| 关联知识库条目 | F07 |
| 涉及文件 | 只读 `RMC/src` tally/fixed-source/WW/adjoint/output 路径；任务目录运行脚本与原始输出 |
| 分支 / 提交 | 根工作区 `main`；随本档提交（2026-09-27）；RMC 未修改 |

---

## 1. 目标与范围（① 立项）

**要做什么**：只读审查 fixed-source neutron、standard MGACE、Cartesian Type=1 track-length mesh、`Energy=-1`、`Normalize=1` serial text 输出中的 per-space×group RE，并判断其能否作为第一版 MLVR 统计不确定度。

**涉及什么**：`ScoreMeshTally.cpp`、`TallyData.*`、`SumUpTally.cpp`、`ProcessTally.cpp`、`CalcFixedSource.cpp`、`TrackHistory.cpp`、`DoMeshWeightWindow.cpp`、`WeightWindows.cpp`、`FixedSource.h`、输出路径；任务目录 `run_f07_runtime.py` 与 `cases/`。

**怎样算完成**：闭合 track score→history sum→mean/RE→text 输出链；静态追踪 WW offspring；完成 N scaling、10-seed empirical scatter、zero-score 和 Normalize 对照；给出要求表与分类。

**原始材料**：原始运行 stdout/stderr 位于 `cases/*/`；汇总 CSV 和 `runtime_empirical_summary.txt` 位于任务根目录。运行使用 `/tmp/rmc-f08-cell-ww-build/bin/RMC`，banner 为 commit `b7d8a946...`、MPI/OMP OFF。

> **模式 C · 物理解释**：正确统计对象是每个 source history 的完整 bin 总贡献 $X_h(i,g)$；若历史独立且程序对均值使用 unbiased sample variance，则 RE 应为均值标准误差相对值。WW descendants 必须先合并到原始 history；否则 split 相关性会使 RE 偏乐观。零分数不能解释为零不确定度。

## 2. 做法与证据（② 设计 · ④ 实施）

### 2.1 静态统计链

- `ScoreMeshTally.cpp:9-118`：每条 track 子段形成 `dTallyAdd=dScore*track.p_dTrackLen`，并写入当前 mesh/energy pointer 的 `p_vScore`；Type=1 track-length 的 `dScore` 为当前粒子权重。
- `TallyData.cpp:37-80`：`SumTallyBin()` 在 history 结束时把当前 `p_vScore` 加入 `p_vSum1`，把当前 history 总分平方加入 `p_vSum2`，随后清零当前分数；`TallyData.h:20-33,96-125` 明确 fixed-source 按 particle history。
- `SumUpTally.cpp:112-151`：fixed-source 每个外部 source 粒子完成其 bank descendants 后调用 `SumTallyBin()`；`CalcFixedSource.cpp:167-207`：neutron history loop、bank pop 和每 history 收尾。
- `ProcessTally.cpp:330-405`：fixed-source 设置 `dM=cFixedSource.p_dTotStartWgt`、`dDiv=1` 后调用 `CalcAveRe()`；ordinary source 的 `InitialBatchSource.cpp:298-303` 将 `p_dTotStartWgt=p_llCurTotParNum`，因此当前子域源权重为 1 时 $M$ 等于 source population。
- `TallyData.cpp:83-106`：若 $M>1$，`Ave=Sum1/(M*Div)`，`RE=sqrt((Sum2/Sum1^2*M-1)/(M-1))`；若 `Sum1==0`，RE=0；若 `M==1`，RE=0。
- `OutputTally.cpp:245-275`：将 mesh `p_vAve` 和 `p_vRe` 传给 `meshTally.output()`；F06 的 text `inp.Tally` 显示 energy rows 和 `Tot` row。

### 2.2 精确统计公式

对一个 mesh track segment，`ScoreMeshTallyByTL()` 形成 $x_{h,k}(i,g)=w\ell$，并写入当前 source history 的 `p_vScore`。一个 history 完成后，记该 bin 的总贡献为 $X_h(i,g)$：

$$S_1=\sum_{h=1}^{M}X_h,\qquad S_2=\sum_{h=1}^{M}X_h^2.$$ 

当前 ordinary fixed-source serial 子域中，$M=p\_dTotStartWgt=p\_llCurTotParNum$；源权重为 1 时，$M$ 等于实际 source histories，不是 track event 数，也不是 batch/cycle 数。`p_vSum2` 是 per-history squares 的和，不是 $(\sum_hX_h)^2$。

当 $M>1$ 且 $S_1\ne0$：

$$\bar X=\frac{S_1}{M D},\quad s^2=\frac{1}{M-1}\left(\frac{S_2}{M}-\left(\frac{S_1}{M}\right)^2\right),$$
$$SE(\bar X)=\frac{s}{\sqrt{M}D},\quad RE=\frac{SE(\bar X)}{|\bar X|}=\sqrt{\frac{M S_2/S_1^2-1}{M-1}}.$$ 

这里 `D=dDiv`；ordinary fixed-source 使用 `D=1`。若路径使用非单位 `D`，mean 和 SE 同比例变化，RE 抵消 `D`。`M=1` 或 `S_1=0` 时代码输出 RE=0。

### 2.3 Forward / Adjoint

`ScoreMeshTallyByTL()` 和 `CalcAveRe()` 没有 tally-side adjoint 特殊分支。Forward 与 Adjoint 共用 `p_dWgt × track length` 统计路径；adjoint 只在输运上游改变粒子权重。因此两者 RE 数据结构和统计公式相同，但 mean 对应的物理 field 不同。

### 2.4 WW correlation audit

`pushSplitParticles()` 把 offspring 放入 `ParticleStack`，记录 `calculateTime`、`prevPos` 和可选 `HistoryPack`；`PopParticleOutofStack()` 恢复位置、能量、权重和粒子属性。`WeightWindows.cpp:DoWeightWindows()` 为 split 创建 `nNum-1` 个 bank copy，`DoMeshWeightWindow.cpp:1-62` 在每个 track segment 前执行 WW，再进行 tally。

固定源 neutron 的实际控制流进一步闭合了统计归属：`CalcFixedSource.cpp:167-207` 在一次外部 source particle 开始后，反复 `TrackHistory()` 并从 neutron bank pop，直到该 history 的 particle bank 清空；之后才在 `CalcFixedSource.cpp:199-202` 调用一次 `CTally.SumUpTally()`。因此 split descendants 的所有 `p_vScore` 贡献在同一个原始 source history 的 `SumTallyBin()` 中合并；它们没有被当作额外的独立 history。`prevPos/HistoryPack` 只用于 WWG 的历史权重记录，不是普通 tally 统计所必需的 ancestry key。该 frozen serial ordinary-source 子域的 WW history grouping 静态证据成立。

### 2.5 零分数

确定不可达 mesh 的运行输出为 `Ave=0`、`RE=0`、`Tot RE=0`。这是 `S_1==0` 的输出分支，不是“误差为零”的证明。下游不能将 RE=0 当作高可信度。当前 runtime suite 未另行建立低概率但非零 bin 的统计样本。

### 2.6 运行时验证

实际命令：

```text
python3 MLVR_develop/2026-09/20260927_01_f07-field-statistical-uncertainty/run_f07_runtime.py
```

真实输出摘要：

```text
scaling: N=50000 RE=0.019083; N=200000 RE=0.00954567; N=800000 RE=0.00476747
empirical: M=10, empirical SD=2.220895965346E-03,
           RMS reported sigma=3.109733584598E-03, ratio=0.714175637536
Normalize: raw Ave=0.32799 RE=0.0095026; normalized Ave=0.32799 RE=0.0095026
zero-score: Ave=0, RE=0, sigma=0, total RE=0
```

N scaling ratios 为 `1.9993` 和 `2.0023`，符合 $1/\sqrt N$。10-seed empirical ratio 为 `0.71418`；样本数有限，且该结果不是 WW 校准，不能据此宣称完整统计闭合。Normalize 对照使用了两个单位体积 bin，因此 Ave ratio 为 1；RE 相同，非单位体积缩放未在本次 runtime 中覆盖。

### 2.7 未覆盖到的验证

WW-on field-bin RE calibration 本任务未新跑；但复用 F04 已归档的五个 WW-on 独立 seed 响应行，计算得到 empirical SD `1.40178e-3`、RMS reported sigma `1.88172e-3`、ratio `0.74495`。这属于辅助 E3 证据；本任务已由 fixed-source bank-drain 控制流证明 ancestry grouping，但仍缺少本 F07 field-bin 的专门 WW-on calibration。MPI/OpenMP、surface source、裂变/自发源 weight 改变、batch estimator、CE/coupled transport 及其他 tally 类型未覆盖。

## 3. 决策记录（③ · 人拍板）

- **决定**：执行用户批准的 F07 C 模式只读审查；只写任务档案与运行证据，不改 RMC。
- **决定人 / 日期**：用户 / 2026-09-27。
- **约束**：禁止修改 RMC、benchmark/reference、zero-score 输出、Field parser、F09 或 Stage 4 接口。

**变更卡**：
| 风险 | 改动范围（含“不改什么”） | 验证与停止条件 | 回滚 |
|---|---|---|---|
| split descendants 可能被错误视为独立样本 | 只读追踪 fixed-source tally 和 native WW bank；不改 RMC | 必须证明每 history 先合并；若不能证明则不能判 A；运行验证仅限 analog | 无 RMC 改动 |

> **模式 C · 人类理解确认**：用户确认本任务只审 RE 统计语义，冻结 standard MGACE fixed-source neutron / Cartesian Type=1 / `Energy=-1` / `Normalize=1` / serial text 子域；不重开 F02/F03/F04/F06。

## 4. 结论与边界（⑤ 归档）

- **结论**：**C — Verify（限定 serial text-first Cartesian 子域）**。Analog 与 native track-mesh WW fixed-source 路径均按 source history 累加 per-bin score；RMC 的 RE 是该 history-level sample mean 的 unbiased sample-variance standard error relative to the mean。对非零 bin，可作为第一版统计不确定度的候选。不能判 A 的关键原因是 zero-score `RE=0` 是未定义情形的占位值，且本任务未完成 F07 field-bin 的 WW-on empirical calibration。
- **不能推出什么**：不能把 `RE=0` 解读为零不确定度；不能把 WW-on RE 直接视为已校准；不能外推至 MPI/OpenMP、batch/cycle、surface source、CE/coupled transport、其他 estimator 或所有 adjoint/WW 组合。
- **遗留 / 下一步**：人工决定是否继续专门 WW-on field-bin RE empirical calibration；下游如使用 RE，必须把 zero-score 语义作为未定义/待决策处理，但本任务不设计 mask。
- **后续证据更新（2026-09-27）**：上述“本任务未完成 WW-on field-bin 校准”是本档案执行时的范围记录；独立复核 `../20260927_02_independent-f07-field-re-review/README.md` 随后完成同一 field bin 的 10-seed native WW-on/PTRAC 校准，`Q=0.88769`。当前受限结论以 `MLVR_Knowledge/02_RMC功能审查矩阵.md` F07 速览为准；全 bins、非单位/不等源权重和并行仍未验证。
- **提交状态**：RMC 未修改、无 commit/push；任务档案与汇总 CSV/摘要随 2026-09-27 根工作区提交入库；原始运行 stdout/stderr 与 `cases/` 运行产物按体积规范不入库、仅保留本地。

> **模式 C · 结果解释**：源码和 runtime 支持“RE 对非零 field bin 是均值的 history-level Monte Carlo standard error”；$N$ 缩放符合 $1/\sqrt N$，Normalize 对照保持 RE 不变；固定源 bank drain 证明 WW descendants 在 SumTallyBin 前属于同一 source history。zero-score 语义和 field-bin WW-on 经验校准仍是边界。

## 5. 过程记录

| 时间 | 操作 / 事件 |
|---|---|
| 2026-09-27 02:52 | 立项 |
| 2026-09-27 | 完成静态统计链与 WW bank 相关性审查；完成 N scaling、M=10 empirical scatter、Normalize 和 zero-score 运行验证；发现首次 harness 解析列错位并修正，最终结果以修正后输出为准。 |
| 2026-09-27 | 从既有 F04 五个 WW-on 独立 seed 响应结果计算辅助比值：empirical SD `1.40178e-3` / RMS reported sigma `1.88172e-3` = `0.74495`；不视为本任务 field-bin WW 校准闭合。 |

**证据等级**：静态公式 E1；serial runtime E3（N scaling/empirical/zero-score/Normalize）；WW correlation E1，未闭合。

## 6. Requirement comparison

| Requirement | Existing behavior | Evidence | Gap |
|---|---|---|---|
| per space×group RE | yes, one data slot per mesh/energy row | `TallyData` arrays; F06 text output | limited to tested text path |
| exact statistical formula | confirmed for ordinary fixed source | `TallyData.cpp:83-106` | no separate WW proof |
| independent sample definition | source particle history; WW descendants drain before one `SumTallyBin()` | `TallyData.h:20-33`, `CalcFixedSource.cpp:167-207` | other source/batch modes out of scope |
| Normalize consistency | mean/variance use same `D`; RE invariant | formula + runtime | current test bin volume is 1; non-unit volume field-bin runtime not completed |
| Forward compatibility | same generic tally path | no adjoint branch | fixed-source serial only |
| Adjoint compatibility | same generic tally path after adjoint weight update | source + F06 output | WW-on statistical meaning open |
| WW splitting correlation handling | descendants are processed before the parent-history `SumTallyBin()` | `CalcFixedSource.cpp:167-207`, `SumUpTally.cpp:112-151` | no new field-bin WW calibration |
| zero-score semantics | returns RE=0 for `S_1==0` or `M==1` | `TallyData.cpp` + zero run | no validity flag |
| empirical calibration | analog compatible, limited M=10；复用 F04 WW-on M=5 ratio `0.74495` | F07 runtime summary；F04 `results.csv` | field-bin WW calibration 仍缺 |
| output recoverability | energy rows include Ave/RE; Tot separate | `OutputTally.cpp`, F06 `.Tally` | parser must ignore Tot for per-group field |

## 7. Final classification

**C — Verify**, scope: standard MGACE fixed-source neutron, Cartesian Type=1 track-length mesh, `Energy=-1`, `Normalize=1`, MPI-off/OpenMP-off serial, text `inp.Tally`; Forward and Adjoint use the same history-level tally statistic path, including native track-mesh WW descendants. This is not A because zero-score RE is semantically unsafe as a confidence value and field-bin WW-on calibration remains incomplete.
