# 定向源码复核

- **SOURCE VERIFIED — 修复容器合同。** `INFINITY_ENERGY` 为有限 `1.0E+22`（`RMC/src/Constants.h:197`）。`ValidatePreparedNativeDefinition()` 先验证 `p_vEnergyBins` 是否含 neutron entry，才取该 entry；随后验证 `B>=2`、有限严格递增边界、首 `0`、末 `INFINITY_ENERGY`、参数和已安装 mesh×interval 形状（`RMC/src/WeightWindows.cpp:307-346`）。
- **SOURCE VERIFIED — 生命周期位置。** enabled WW 在 bind 时于模型初始化前验证（`RMC/src/PrepareFixedSourceRun.cpp:171-175`）；每次 prepared Run 在 definition fingerprint 与 CLEAR 前验证（`:248-253`）；enabled Install 在任何 neutron energy-bin 访问及 mode/cutoff 写入前验证（`RMC/src/WeightWindows.cpp:354-366`）。WW-OFF 的 Install 路径在 energy-bin 访问前返回。
- **SOURCE VERIFIED — 末界。** `GetIntpltPos()` 对末界及以上返回 `B-1`（`RMC/src/GlobeFun.h:141-151`），直接 lookup 将其夹至 `B-2`（`RMC/src/WeightWindows.cpp:48-60`）。
- **P1 — MG 非有限物理能量。** transport 调用 `GetWeightWindowEnergy()` 后才进入 lookup（`RMC/src/DoMeshWeightWindow.cpp:17-18,42-43`）；MG 路径在 `GetErgValue()` 中先做 `int(dParticleErg + 0.5)`（`RMC/src/GetMgCs.cpp:247-253`）。因此 lookup 的 `std::isfinite(erg)` guard（`WeightWindows.cpp:57`）不能保证 raw NaN/Inf 在转换/索引前受控拒绝。
- **P1 — 独立 Install 的 lower 内容。** `InstallPreparedNativeState()` 只验证 lower 长度后即重置状态并 `ProcessWeightWindow()`（`RMC/src/WeightWindows.cpp:354-370`）。lower 的 finite/positive、派生上下界与可表示 split ratio 检查只在 Run（`RMC/src/PrepareFixedSourceRun.cpp:269-285`）。故单独调用 Install 可写入非法 lower。
- **Out-of-profile residual。** MPI shared branch 没有 serial branch 的 mesh-index/shape 检查（`RMC/src/WeightWindows.cpp:62-78`）；prepared profile 不支持 MPI，未升格为本次 prepared P1。
