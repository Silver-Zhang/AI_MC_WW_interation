# 日志索引

本目录只保留不可由源码和命令替代的原始验证记录。可重建的 RMC `runs/`、`cases/`、STATE、输出文件和 Python 缓存不归档。

| 目录 | 内容 | 证据地位 |
|---|---|---|
| `request/` | 用户原始请求 | 任务来源 |
| `final/` | 最终验收报告、CTest、diff 与哈希记录 | 主结论入口 |
| `clean_two_group/` | 两群资产资格报告、6 份零警告整程日志、9 份生产采样日志 | photon/secondary 整程主证据 |
| `one_group_legacy/` | 一群三种子矩阵、配对和含能群 warning 的完整日志 | 辅助证据，不称为干净成功 |
| `defect_probes/` | 两处分支修复前/后生产函数探针 | 缺陷动态确认 |
| `qualification_history/` | 私有资产与 smoke 迭代的资格报告 | 构造与排错历史 |

主入口：`final/two_group_clean_validation_report.json`。该报告可由 `tools/analyze_two_group_clean_validation.py --logs logs --output logs/final/two_group_clean_validation_report.json` 从 `clean_two_group/` 原始日志重建。
