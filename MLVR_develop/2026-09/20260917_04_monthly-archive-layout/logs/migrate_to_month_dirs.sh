#!/usr/bin/env bash
# 一次性迁移：把 MLVR_develop 下的任务目录移入按月子目录（YYYY-MM/）。
# 留痕副本；执行时从 /tmp 运行以免受档案自身移动影响。
set -euo pipefail

ROOT="/home/workspace/AI_MC_WW_interation"
cd "$ROOT"

moved=0
for d in MLVR_develop/20[0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9]_*; do
    [ -d "$d" ] || continue
    name=$(basename "$d")
    month="${name:0:4}-${name:4:2}"
    mkdir -p "MLVR_develop/$month"
    git mv "$d" "MLVR_develop/$month/$name"
    moved=$((moved + 1))
done

echo "moved=$moved"
ls -d MLVR_develop/20[0-9][0-9]-[0-9][0-9]
