# W14 关键计算与结果文件

这里是用户要求保存的可入库文件集；没有 RMC 源码修复或新输运实验。

| 目录/文件 | 保存内容 |
|---|---|
| `scripts/` | 原实验的构建、插桩、输入生成、GDB观察、执行和数值分析脚本，逐字节保存 |
| `inputs/` | 合法热群源 F/A、0.6615 MeV Forward、native WW 后代四份代表输入 |
| `results/cases.json` | 全部13个用例的物理能量、群号及独立参考配置 |
| `results/results.json` | 全部13个用例的数值结果，含初速、首段时间、碰撞后速度和后代检查 |
| `results/gdb/` | 五条关键路径的原始 GDB JSONL，包括低能源 F/A、合法索引错速 F/A、WW 后代 |
| `results/asan/` | F/A 热群源的原始越界 stderr；实际链接 helper 的插桩反汇编证据 |
| `results/tally/` | 0.6615 MeV F/A 原始 tally 文件；仅留存结果，不能解释为已证明绝对物理正确 |
| `provenance.json` | 源码/核数据库/二进制身份、群结构、编译与执行命令、17个最终运行退出码及历史数凭据 |
| `recheck-results.py` | 从持久证据重算旧结果，只替换原分析脚本的数据根路径，不运行RMC或修改原始数据 |

完整原始证据仍保存在本任务 `logs/local-evidence/`，包括全部13份输入、全部最终与调试运行、真实命令/退出码以及新增保存的 CMakeCache、compile_commands、flags、link 命令。该目录不入Git；关键结论与上表文件可纳入未来提交。无需复制 4.5 GB 的源码快照、编译对象或可执行文件。

从本任务根目录复核既有结果：

```bash
python3 artifacts/recheck-results.py
sha256sum -c evidence-sha256.txt
```

复核只用持久目录中的原始 GDB 事件、历史数输出及数据库群结构记录，并要求再生成的 `results.json` / `results-table.md` 与原结果逐字节一致。

`scripts/` 是原实验脚本，保留当时的 `/tmp/w14-codex-review` 绝对路径。它们不是可不加准备就重跑输运的一键安装包：若将来获授权重跑，应使用 RMC 冻结提交4810694b及相同依赖/数据库，在独立工作目录按 `provenance.json` 的配置重建并绑定路径。`make-inputs.py` 的旧基准模板路径仅是历史记录；本档案已持久保存全部实际输入，重跑可以直接使用这些输入，不依赖那个历史临时模板。核数据库和生产仓库不随归档复制，也不应修改。

原 `REPORT.md` 为当时报告原文，其中临时路径用于辨认旧执行身份；临时目录清理情况见任务README与 `logs/tmp-cleanup.json`。未授权任何修复、提交或Stage3开发。
