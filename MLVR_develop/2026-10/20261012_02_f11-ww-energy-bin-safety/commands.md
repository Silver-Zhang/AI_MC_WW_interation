# 实际执行与本地复核入口

工作目录 `/home/workspace/AI_MC_WW_interation`。以下简写用于阅读：

```bash
F11_ROOT=/tmp/20261012_02_f11-ww-energy-bin-safety
F11_EVIDENCE=$F11_ROOT/evidence
F11_TASK=MLVR_develop/2026-10/20261012_02_f11-ww-energy-bin-safety
```

真实完整argv、cwd、环境、stdout/stderr与退出码均在manifest列出的 `evidence/logs/**/command.json`；本地setup.py、run_gates.py、protect.py和summarize.py亦保留原文。源码私有副本来自上一轮精确匹配当前修复前源码的stage2-src，再覆盖本轮授权文件；保护结果验证了两套全部2,106个文件和旧binary SHA。

```bash
cmake -S "$F11_ROOT/stage2-src" -B "$F11_ROOT/stage2-build" \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo -Dmpi=OFF -Dopenmp=OFF -Dais=OFF \
  -Dpythonapi=OFF -Dpersonal=OFF -Dloadmodules=ON -Dtest=ON \
  -Dmpiproc=1 -Dompthrd=1 -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build "$F11_ROOT/stage2-build" --target RMC RMCPreparedLifecycle -j12
python3 "$F11_TASK/tools/run_energy_checks.py"
python3 "$F11_ROOT/run_gates.py"
python3 "$F11_TASK/tools/targeted_sanitizer.py" compile
python3 "$F11_TASK/tools/targeted_sanitizer.py" run
```

构建由本地run_command.py包装记录。最终补齐已安装四槽/非中子窗口拒绝后重建记录为 `logs/build-final`，所有最终门禁均使用该binary。sanitizer链接为独立binary，未替换正常对象或库，`ASAN_OPTIONS=detect_leaks=0:abort_on_error=1`、`UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`；插桩编译/链接argv同样已记录。

普通WW专用脚本分别调用修复前 `/tmp/20261012-f11-stage2-p1/stage2-build/bin/RMC` 和最终新RMC，500历史、seed17、Type2 stride100000。新多窗WWE=[0.1,1.0]，原生实际边界=[0,0.1,1,1e22]，4空间格、12个mesh-major lower。三界和实际能量区间通过生产lookup→DoWeightWindows观察；每个half-run的N、offset、派生seed在regression-results与本地lifecycle-plans.json。

```bash
python3 "$F11_TASK/tools/run_ww_regressions.py" --action setup
python3 "$F11_TASK/tools/run_ww_regressions.py" --action ordinary
python3 "$F11_TASK/tools/run_ww_regressions.py" --action multi
```

setup只在首次生成本地输入/复制的比较器时执行一次。运行目录拒绝覆写，独立复跑应使用新label/新工作目录并保留现有证据；勿直接重复原命令覆盖manifest所绑定的现场。普通文本采用原Task05预设的时间/构建身份规范化；tally文本逐字节、HDF全部数据17位比较、内存与轨迹IEEE逐位比较。prepared的7项时间字段只豁免值、仍检查形状/数值类别；完整名单及本轮实际例外在本地compare_lifecycle.py和归档JSON。

核数据只读：`/home/silver/NucXS_Library/RMC_DATA`；30-group H2O（1001.50m、8016.50m），库身份见manifest。CTest额外覆盖既有伴随、WW、photon/electron/coupled/restart和source-weight audit，真实10项输出见 `evidence/logs/ctest-command/stdout.txt`。

复核保护与补丁（只检查、不应用）：

```bash
git -C RMC apply --reverse --check "$PWD/$F11_TASK/correction.diff"
bash tools/check-archives.sh
```

完整Stage2快照位于 `evidence/final/changes.diff` 与 `new-files.diff`；本轮入库correction.diff按修复前文件逐个比较生成，包含两个原untracked文件的增量，避免git diff漏档。
