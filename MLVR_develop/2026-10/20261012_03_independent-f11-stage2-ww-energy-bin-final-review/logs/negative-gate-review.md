# 负例与生产 guard 复核

## Artifact verified

Task02 `negative-results.json` 记录 `78/78` 通过；本复核独立重算为 `26` 种 mutation × `3` phases：`bind`、首轮成功后 `after`、独立 `install`。

覆盖包括：outer empty/one、inner empty/one、duplicate、descending、NaN/Inf boundary、missing sentinel、wrong first endpoint、energy dimension、ragged/short mesh、参数 outer/inner shape、other particle、non-Cartesian、flat-count overflow。

每条保存记录均包含预期异常、`production_throw=true` 和 guard stack；例如 outer-empty 的 bind stack 经 `CDWeightWindow::ValidatePreparedNativeDefinition` → `CDCalMode::InitializePreparedFixedSourceRuns`，direct Install stack 经同一 validator → `CDWeightWindow::InstallPreparedNativeState`。

Bind 记录的计数为 initialize/prepare/CLEAR/execute/source `0/0/0/0/0`；after 记录保留第一轮 source/completed histories `100`，并标记 `REJECTED_RUN state_unchanged=1`；Install 记录标记 `REJECTED_INSTALL state_unchanged=1`。

## Limits and remaining gap

保存的 78 个 mutation 都是定义容器/拓扑/shape 类注入；并未覆盖 raw MG particle energy NaN/Inf 在 `GetErgValue()` 前的 transport 路径，也未覆盖仅 lower 数值非法而容器 shape 正确的 direct Install。它们是本复核 P1 的最小补测项。
