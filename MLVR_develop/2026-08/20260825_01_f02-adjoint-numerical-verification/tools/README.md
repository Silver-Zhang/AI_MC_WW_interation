# Reproduction tools

本目录保存不可由运行产物替代的输入生成器和分析器。生成的 `cases/`、`runs/`
以及 `__pycache__/` 不归档，可由 `MLVR_develop/clean_generated.sh --apply` 清理。

## V2：局部密度

```bash
python3 tools/generate_v2_density_cases.py --root /tmp/mlvr_v2_cases
# 分别在 /tmp/mlvr_v2_cases/r*/ 中运行 RMC，生成 inp.source 后：
python3 tools/analyze_source_trace.py \
  --root /tmp/mlvr_v2_cases \
  --output /tmp/mlvr_v2_analysis.csv
```

三份冻结输入的 SHA256 见 `../logs/v2_evidence.txt`。

## V3：双 nubar

```bash
python3 tools/analyze_double_nubar.py \
  --xsdir /home/silver/NucXS_Library/RMC_DATA/xsdir \
  --zaid 10001.01m \
  --output /tmp/mlvr_v3_kernel.csv
```

动态可达性最小输入保存在 `../assets/v3_reachability.inp`；其 SHA256 为
`ecc35caf3f52ec38d5f9c393afef379e65644ad97a2e5224abe18fdd0fa08106`。

## V4：前向-伴随互易性

```bash
python3 tools/screen_mgace_pairs.py \
  --xsdir /home/silver/NucXS_Library/RMC_DATA/xsdir \
  --component 1001.50m:2 --component 8016.50m:1 \
  --output /tmp/mlvr_v4_candidates.csv
python3 tools/generate_reciprocity_cases.py \
  --root /tmp/mlvr_v4_runs --population 200000
# 运行 manifest 中的 20 个输入并写入 exit_code.txt/stdout.log/stderr.log 后：
python3 tools/analyze_reciprocity.py \
  --root /tmp/mlvr_v4_runs \
  --runs-output /tmp/mlvr_v4_runs.csv \
  --summary-output /tmp/mlvr_v4_summary.csv \
  --anomalies-output /tmp/mlvr_v4_anomalies.log
```

工具只读部署核库；输出应写入临时目录，归档证据以 `../logs/` 为准。