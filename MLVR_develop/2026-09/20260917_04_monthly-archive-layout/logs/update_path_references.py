#!/usr/bin/env python3
"""把仓库内 .md 文档里的任务路径引用更新为按月子目录形式。

- 处理：MLVR_develop/YYYYMMDD_NN_name → MLVR_develop/YYYY-MM/YYYYMMDD_NN_name
- 处理：相对链接 (YYYYMMDD_NN_name/README.md) → (YYYY-MM/YYYYMMDD_NN_name/README.md)
- 跳过：RMC/、AIMC_WWiteration/（独立仓库）、.git/、任何 logs/ 目录（原始证据）、非 .md 文件
"""
import re
import pathlib

ROOT = pathlib.Path("/home/workspace/AI_MC_WW_interation")
SKIP_DIRS = {".git", "logs", "RMC", "AIMC_WWiteration"}
NAME = r"_([0-9]{2})_([A-Za-z0-9][A-Za-z0-9_.\-]*)"
pat_prefixed = re.compile(r"MLVR_develop/(20\d{6})" + NAME)
pat_link = re.compile(r"\((20\d{6})" + NAME + r"/README\.md\)")


def month(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}"


def rewrite(text: str):
    count = 0

    def rep1(m):
        nonlocal count
        count += 1
        return f"MLVR_develop/{month(m.group(1))}/{m.group(1)}_{m.group(2)}_{m.group(3)}"

    def rep2(m):
        nonlocal count
        count += 1
        return f"({month(m.group(1))}/{m.group(1)}_{m.group(2)}_{m.group(3)}/README.md)"

    text = pat_prefixed.sub(rep1, text)
    text = pat_link.sub(rep2, text)
    return text, count


total = 0
files = 0
for path in sorted(ROOT.rglob("*.md")):
    if any(part in SKIP_DIRS for part in path.parts):
        continue
    raw = path.read_text(encoding="utf-8", errors="replace")
    new, n = rewrite(raw)
    if n:
        path.write_text(new, encoding="utf-8")
        print(f"{path.relative_to(ROOT)}: {n} 处")
        total += n
        files += 1

print(f"--- 共 {files} 个文件，{total} 处引用")
