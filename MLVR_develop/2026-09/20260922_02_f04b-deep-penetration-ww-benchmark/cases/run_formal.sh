#!/usr/bin/env bash
set -euo pipefail
TASK_DIR=$(cd "$(dirname "$0")/.." && pwd)
EXE="$TASK_DIR/runs/build/bin/RMC"
POPULATION=1000000
SEEDS=(101 103 107 109 113)
for seed in "${SEEDS[@]}"; do
  for case in analog ww; do
    run="$TASK_DIR/runs/formal_${case}_seed${seed}"
    rm -rf "$run"
    mkdir -p "$run"
    python3 "$TASK_DIR/cases/make_case.py" --case "$case" --seed "$seed" --population "$POPULATION" --out "$run/inp"
    (cd "$run" && /usr/bin/time -p "$EXE" > stdout.log 2> stderr.log)
  done
done
