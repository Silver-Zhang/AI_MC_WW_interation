#!/usr/bin/env bash
# 一条命令查看工作区内各仓库的同步状态（只读，不修改任何仓库）。
#
# 用法: bash tools/repo-status.sh
#
# 覆盖三个主仓库；RMC/dependencies/* 属于 RMC 自带的 submodule，只统计不管理。
set -u

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

report() {
    local name="$1" dir="$2"
    printf '\n── %s\n' "$name"

    if ! git -C "$dir" rev-parse --git-dir >/dev/null 2>&1; then
        printf '   ⚠ 不是 git 仓库: %s\n' "$dir"
        return
    fi

    local branch upstream sync counts ahead behind dirty untracked last
    branch=$(git -C "$dir" rev-parse --abbrev-ref HEAD 2>/dev/null)
    upstream=$(git -C "$dir" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)

    if [ -n "$upstream" ]; then
        counts=$(git -C "$dir" rev-list --left-right --count "$upstream...HEAD" 2>/dev/null || echo "? ?")
        behind=$(printf '%s' "$counts" | awk '{print $1}')
        ahead=$(printf '%s' "$counts" | awk '{print $2}')
        sync="领先 $ahead / 落后 $behind  ($upstream)"
        if [ "$ahead" = "0" ] && [ "$behind" = "0" ]; then
            sync="已同步  ($upstream)"
        fi
    else
        sync="无上游分支"
    fi

    dirty=$(git -C "$dir" status --porcelain --untracked-files=no 2>/dev/null | wc -l)
    untracked=$(git -C "$dir" -c core.quotepath=false ls-files --others --exclude-standard 2>/dev/null | wc -l)
    last=$(git -C "$dir" log -1 --format='%h %ad %s' --date=short 2>/dev/null)

    printf '   路径   : %s\n' "$dir"
    printf '   分支   : %s\n' "$branch"
    printf '   同步   : %s\n' "$sync"
    printf '   工作区 : %s 修改 / %s 未跟踪\n' "$dirty" "$untracked"
    printf '   最近   : %s\n' "$last"

    if [ "$untracked" != "0" ]; then
        printf '   未跟踪 :\n'
        git -C "$dir" -c core.quotepath=false ls-files --others --exclude-standard 2>/dev/null | head -5 | sed 's/^/     - /'
        if [ "$untracked" -gt 5 ]; then
            printf '     … 共 %s 项\n' "$untracked"
        fi
    fi

    local wt
    wt=$(git -C "$dir" worktree list 2>/dev/null | wc -l)
    if [ "$wt" -gt 1 ]; then
        printf '   Worktree: %s 个（含主工作区；多余的是工具遗留，见 MLVR_develop/README.md）\n' "$wt"
    fi

    if [ -f "$dir/.gitmodules" ]; then
        local total missing
        total=$(grep -c '^\[submodule' "$dir/.gitmodules" 2>/dev/null || true)
        missing=$(git -C "$dir" submodule status 2>/dev/null | grep -c '^-' || true)
        printf '   Submodule: %s 个（未初始化 %s，编译时才需要 update --init）\n' "$total" "$missing"
    fi
}

report '根工作区（本仓库，GitLab + GitHub 双镜像）' "$ROOT"
report 'RMC（团队仓库，独立 git）' "$ROOT/RMC"
report 'AIMC_WWiteration（原型仓库，独立 git）' "$ROOT/AIMC_WWiteration"

printf '\n提示: 需要完整编译 RMC 时执行 git -C RMC submodule update --init --recursive\n'
