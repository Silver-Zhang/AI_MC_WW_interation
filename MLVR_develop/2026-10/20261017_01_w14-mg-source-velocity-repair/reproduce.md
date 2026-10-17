# 证据位置与复现

本任务目录记为 `$task_dir`；实际构建/运行工作根为 `/tmp/w14-repair-20261017`。它是本任务新建的隔离目录，未删除历史用户文件。逐run证据另已复制到本任务的 `logs/local-evidence/`，被 `.gitignore` 排除；Git候选仅精简文档、结果、脚本、三个代表输入、补丁和一个哈希清单。

## 身份及构建

- 开工文档main/50d9e0e、RMC指定分支/4810694b，均clean。最终8文件补丁见 changes.diff，无新增RMC未跟踪文件。
- `logs/baseline.json`、`evidence-manifest.json`分别给出开工与最终身份；后者记录测试源码/当前生产文件相同的SHA256，以及正常、prepared、sanitizer、guard binary和Python编译对象的SHA256。
- 原始环境/构建命令在 `logs/local-evidence/logs/{environment,configure,build,configure-after,build-after}/`，每项都有command.json、stdout、stderr、exitcode。完整CMakeCache/compile_commands/flags/link.txt在 `logs/local-evidence/build-metadata/`。
- 原始baseline取自 `git archive 4810694b`，dependencies由本机已有依赖复制，git-readonly只阻止临时副本的自动submodule命令。未checkout、reset或变更原依赖。
- 运行数据 `/home/silver/NucXS_Library/RMC_DATA`，standard `multigroup/mgxsnp`；独立原始中心/宽度解析在 analyze-velocity.py，涉及H1/O16/U235三个真实记录。数据散列已存。CE使用1001.71c和8016.71c。
- 两侧RMC均全新构建；prepared driver/globals按各自真实CMake命令编译，其生产对象复用同侧刚构建RMC对象，编译参数逐项精确相等。证明在 `logs/local-evidence/logs/prepared-build*/reused-objects.json`；不是重新实现输运循环。
- `scripts/build-baseline.py`是修改前实际执行版本，含开工clean及源码字节一致断言；当前RMC有本任务修改，不能直接再次执行该断言。重建基线应在新临时目录从冻结commit导出源码，再按记录的CMake参数配置。修复版使用相同基线加changes.diff；不要在共享RMC执行reset/checkout。

## 实际验证命令

下面命令使用仍保留的隔离目录；run.py以新目录保存输出，已有标签不会被覆盖。重跑需使用新标签或新隔离根，不删除原证据。

```bash
python3 /tmp/w14-repair-20261017/scripts/build-baseline.py
python3 /tmp/w14-repair-20261017/scripts/build-after.py
python3 /tmp/w14-repair-20261017/scripts/link-prepared.py build
python3 /tmp/w14-repair-20261017/scripts/link-prepared.py build-after
python3 /tmp/w14-repair-20261017/scripts/build-sanitized.py
python3 /tmp/w14-repair-20261017/scripts/build-sanitized.py link
python3 /tmp/w14-repair-20261017/scripts/analyze-velocity.py
python3 /tmp/w14-repair-20261017/scripts/compare-ordinary.py
```

这些是历史执行命令清单，构建脚本不是可覆盖式一键重跑器。所有最终输入已保存，避免依赖历史输入生成器的试错版本。

- 最终19速度例：`runs/after/velocity-final/<case>/`；command.json记录GDB完整命令，velocity.jsonl为逐source/Bank/首飞观察，exitcode均0。使用的准确脚本为当前 `scripts/velocity.gdb.py`（v3），亦在原始logs存了版本副本。额外 `velocity-ww-final` 是v4减少重复碰撞断点后的WW复查；不混入19例计数。
- 8组稳态比较：MG WW F/A 使用两侧 `trace-bank-final`；谱F/A使用 `trace-spectrum`；其余使用 `trace`。所有最终快照/trace hash/分母/RNG/文本Tally均由 compare-ordinary.py 选择并比较。
- 9个插桩最终运行：`runs/asan/plain/`中7例（热群F/A、0.6615 F/A、WW F/A、裂变），`plain-spectrum/`中2例。`plain`中早先谱解析失败不算通过。参数 `ASAN_OPTIONS=detect_leaks=0:halt_on_error=1`、`UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1`。相关TU与link命令在 `logs/sanitized-*/`，helper的实际插桩反汇编在 `logs/sanitized-helper-disassembly.txt`。
- helper边界测试：`scripts/velocity-guard.cpp`，真实compile命令/日志与run-noleak退出码在 `logs/velocity-guard/`。默认LeakSanitizer首次受沙箱限制失败的记录保留，不作为通过证据。
- FF：`lifecycle/logs/after/ff/`；FAF+WW最终：`lifecycle/logs/after-bank-final/faf-ww/`。每轮500或1000/2000源历史，不重叠子流的实际seed见receipt、lifecycle-plans.json和README§4。

```bash
python3 /tmp/w14-repair-20261017/lifecycle/tools/run_lifecycle.py ff --label after --trace
python3 /tmp/w14-repair-20261017/lifecycle/tools/run_lifecycle.py ff --label after --trace --fresh
python3 /tmp/w14-repair-20261017/lifecycle/tools/compare_lifecycle.py ff --label after
python3 /tmp/w14-repair-20261017/lifecycle/tools/run_lifecycle.py faf-ww --label after-bank-final --trace
python3 /tmp/w14-repair-20261017/lifecycle/tools/run_lifecycle.py faf-ww --label after-bank-final --trace --fresh
python3 /tmp/w14-repair-20261017/lifecycle/tools/compare_lifecycle.py faf-ww --label after-bank-final
RMC_DATA_PATH=/home/silver/NucXS_Library/RMC_DATA ctest --test-dir /tmp/w14-repair-20261017/build-after -R '^(test_fixed_source_adjoint|test_fixed_source_1|prepared_source_weight_audit)$' --output-on-failure
```

GDB必须具有正常ptrace权限；本次沙箱内首次启动被拒绝后，使用工具授权的调试执行环境重试，没有调整系统ptrace策略或写被调试粒子状态。

## 观察器与失败证据

源/Bank返回处的GDB引用读取最初有失效，旧记录在velocity-observer-v1/v2；v3改为函数内明确行号观察。旧Stage2 trace的Bank入口ORNG参数也读到了异常地址值，最终改为读Execute已经绑定的同一RNG对象；新的序列两侧完整重跑。不得把旧失败trace作为物理回归通过，也没有整体忽略Bank事件。两类观察器、输入卡试错和Python编译缺include的失败证据原样保留。

只豁免原Stage2已列出的StatisticsTester墙钟时间/FOM字段。稳态粒子事件刻意比较位置/方向/能群/权重，不用预期改变的速度/粒子累计时间作“保持”要求；后两者由独立速度与时间oracle逐条验证。CE样本同样要求独立物理速度正确，空间/RNG/文本Tally回归为精确比较。

## 不运行RMC的归档复核

在有本地原始证据和原数据库的机器执行：

```bash
python3 MLVR_develop/2026-10/20261017_01_w14-mg-source-velocity-repair/scripts/recheck.py
```

该脚本核验原始文件SHA256，重算19例速度/时间及8组稳态比较，并重验5轮prepared/fresh比较。输出写入临时分析目录，不覆盖原证据、不运行RMC。构建文件与可执行文件没有放入Git。
