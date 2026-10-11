#!/usr/bin/env bash
set -euo pipefail
task_dir="$(cd "$(dirname "$0")/.." && pwd)"
workspace_dir="$(cd "$task_dir/../../.." && pwd)"
source_dir=/tmp/f11-volume-rmc-source
build_dir=/tmp/f11-volume-rmc-build-snapshot
# Copy source bytes without Git metadata; all generated files remain outside RMC.
rsync -a --exclude=.git --exclude=docs --exclude=tests --exclude=RMC --exclude=delivery "$workspace_dir/RMC/" "$source_dir/"
mkdir -p "$source_dir/delivery"
cp "$workspace_dir/RMC/delivery/GITSHA" "$source_dir/delivery/GITSHA"
cmake -S "$source_dir" -B "$build_dir" -Dmpi=OFF -Dopenmp=OFF -Dloadmodules=ON -Dtest=OFF -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build "$build_dir" -j 8
# CMake's submodule attempts fail harmlessly on the Git-free copy; existing
# vendored dependencies are used. Preserve delivery/GITSHA, even when blank.
