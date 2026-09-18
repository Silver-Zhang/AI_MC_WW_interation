#!/usr/bin/env bash
# 归档健康检查（只读）：扫描 MLVR_develop 下的任务档案与 INDEX 台账，列出不一致项。
#
# 用法: bash tools/check-archives.sh
#
# 检查项:
#   1. 未填写的空白模板
#   2. 档案状态与 INDEX 台账不一致
#   3. 台账未登记 / 缺 README.md
#   4. 台账悬空（登记了但目录不存在）
#   5. 模式 C 档案缺三要素（结论 / 证据 / 边界，提示级）
#   6. changes.diff 为空文件
#   7. logs/ 或 assets/ 是空目录
set -u

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
DEV="$ROOT/MLVR_develop"
IDX="$DEV/INDEX.md"

blank=(); mismatch=(); unlisted=(); dangling=(); struct_c=(); emptydiff=(); emptydir=()

# 状态只比较所属类别（如“已完成（限定范围）”与“已完成”视为一致）。
state_key() {
    case "$1" in
        *已完成*) printf '已完成' ;;
        *待设计*) printf '待设计' ;;
        *待决策*) printf '待决策' ;;
        *实施中*) printf '实施中' ;;
        *待验证*) printf '待验证' ;;
        *已关闭*) printf '已关闭' ;;
        *) printf '%s' "$1" ;;
    esac
}

for d in "$DEV"/20[0-9][0-9]-[0-9][0-9]/20[0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9]_*; do
    [ -d "$d" ] || continue
    name=$(basename "$d")
    f="$d/README.md"

    if [ ! -f "$f" ]; then
        unlisted+=("$name（缺 README.md）")
        continue
    fi

    if grep -q '用非代码语言说明本任务要判断' "$f" 2>/dev/null; then
        blank+=("$name")
    fi

    arch_state=$(grep -m1 '^| 状态 |' "$f" | sed 's/^| 状态 | //; s/ |$//')
    row_line=$(grep -F "$name" "$IDX" | head -1)
    if [ -z "$row_line" ]; then
        unlisted+=("$name（台账无此行）")
    else
        idx_state=$(printf '%s' "$row_line" | awk -F'|' '{gsub(/^[ \t]+|[ \t]+$/,"",$5); print $5}')
        if [ -n "$arch_state" ] && [ "$(state_key "$arch_state")" != "$(state_key "$idx_state")" ]; then
            mismatch+=("$name：档案[$arch_state] ≠ 台账[$idx_state]")
        fi
    fi

    if grep -q '^| 任务模式 | C' "$f" 2>/dev/null; then
        # 异极结构（含英文档案）只要求结论 / 证据 / 边界三要素
        miss=""
        grep -qE '结论|[Cc]lassification|[Cc]onclusion|[Vv]erdict' "$f" || miss="$miss 结论"
        grep -qE '证据|验证|[Vv]erif|[Ee]vidence|[Vv]alidat' "$f" || miss="$miss 证据"
        grep -qE '边界|范围外|局限|[Rr]estriction|[Ll]imit|[Ss]cope' "$f" || miss="$miss 边界"
        [ -n "$miss" ] && struct_c+=("$name：缺$miss（模式 C 三要素）")
    fi

    if [ -f "$d/changes.diff" ] && [ ! -s "$d/changes.diff" ]; then
        emptydiff+=("$name")
    fi

    for sub in logs assets; do
        if [ -d "$d/$sub" ] && [ -z "$(ls -A "$d/$sub" 2>/dev/null)" ]; then
            emptydir+=("$name/$sub")
        fi
    done
done

while IFS= read -r target; do
    [ -e "$DEV/$target" ] || dangling+=("$target")
done < <(grep -oE '\(20[0-9]{6}_[0-9]{2}_[^)]+/README\.md\)' "$IDX" | tr -d '()' | sed 's#/README.md$##' | sort -u)

section() {
    local title="$1"
    shift
    printf '\n%s (%s)\n' "$title" "$#"
    local item
    for item in "$@"; do printf '  - %s\n' "$item"; done
}

printf 'MLVR_develop 归档检查 — %s\n' "$(date '+%Y-%m-%d %H:%M')"
section '空白模板（未填写）' ${blank[@]+"${blank[@]}"}
section '状态与台账不一致' ${mismatch[@]+"${mismatch[@]}"}
section '台账未登记 / 缺 README.md' ${unlisted[@]+"${unlisted[@]}"}
section '台账悬空（目录不存在）' ${dangling[@]+"${dangling[@]}"}
section '提示：changes.diff 为空（确认无代码改动后可删除该文件）' ${emptydiff[@]+"${emptydiff[@]}"}
section '提示：空的 logs/ 或 assets/' ${emptydir[@]+"${emptydir[@]}"}
section '提示：模式 C 结构缺失（模板档案缺章节，或异极档案缺三要素）' ${struct_c[@]+"${struct_c[@]}"}

blocking=$(( ${#blank[@]} + ${#mismatch[@]} + ${#unlisted[@]} + ${#dangling[@]} ))
hints=$(( ${#emptydiff[@]} + ${#emptydir[@]} + ${#struct_c[@]} ))
printf '\n汇总: 需处理 %s 项；提示 %s 项\n' "$blocking" "$hints"
