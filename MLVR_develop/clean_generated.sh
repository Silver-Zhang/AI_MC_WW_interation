#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
APPLY=false

if [[ ${1:-} == "--apply" ]]; then
    APPLY=true
elif [[ $# -gt 0 ]]; then
    echo "Usage: $0 [--apply]" >&2
    exit 2
fi

mapfile -d '' TARGETS < <(
    find "$ROOT" -mindepth 2 -maxdepth 2 -type d \( -name runs -o -name cases \) -print0
    find "$ROOT" -type d -name __pycache__ -print0
)

if [[ ${#TARGETS[@]} -eq 0 ]]; then
    echo "No generated task directories found."
    exit 0
fi

printf '%s\n' "Generated task directories:"
printf '  %s\n' "${TARGETS[@]}"

if [[ $APPLY == false ]]; then
    echo "Dry run only. Re-run with --apply to remove them."
    exit 0
fi

for target in "${TARGETS[@]}"; do
    rm -rf -- "$target"
done
printf 'Removed %d generated directories.\n' "${#TARGETS[@]}"
