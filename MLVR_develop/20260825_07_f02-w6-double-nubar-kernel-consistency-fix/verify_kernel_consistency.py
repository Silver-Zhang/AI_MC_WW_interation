#!/usr/bin/env python3
"""Verify that runtime adjoint fission sampling uses the initialized nubar kernel."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path


V4_TOOLS = (
    Path(__file__).resolve().parent.parent
    / "20260825_01_f02-adjoint-numerical-verification"
    / "cases"
    / "v4_reciprocity"
)
sys.path.insert(0, str(V4_TOOLS))

from screen_mgace_pairs import read_ascii_mgace, xsdir_entries


RUNTIME_EXPRESSION = (
    "cAceData.p_vNuclides[nNuc].XSS[cAceData.GetMgNeuLNU(nNuc) + exitGrp]"
)
LEGACY_EXPRESSION = (
    "cAceData.p_vNuclides[nNuc].XSS["
    "cAceData.p_vNuclides[nNuc].JXS[4] + exitGrp]"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def total_nubar_locator(first_nubar: int, groups: int, nubar_count: int) -> int:
    return first_nubar + groups if nubar_count > 1 else first_nubar


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--xsdir", type=Path, required=True)
    parser.add_argument("--zaid", default="10001.01m")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    source = arguments.source.read_text(encoding="utf-8")
    if source.count(RUNTIME_EXPRESSION) != 1:
        raise RuntimeError("expected exactly one total-nubar runtime expression")
    if LEGACY_EXPRESSION in source:
        raise RuntimeError("legacy first-nubar runtime expression is still present")

    table_path, address = xsdir_entries(arguments.xsdir)[arguments.zaid.upper()]
    table = read_ascii_mgace(arguments.zaid.upper(), table_path, address)
    if table.nubar_count <= 1:
        raise RuntimeError(f"{arguments.zaid} has NNUBAR={table.nubar_count}, expected > 1")

    groups = table.groups
    lfiss = table.jxs[2]
    first_nubar = table.jxs[3]
    getter_nubar = total_nubar_locator(first_nubar, groups, table.nubar_count)
    single_table_nubar = total_nubar_locator(first_nubar, groups, 1)
    if single_table_nubar != first_nubar:
        raise RuntimeError("single-table locator compatibility check failed")

    rows: list[dict[str, object]] = []
    max_kernel_difference = 0.0
    max_probability_difference = 0.0
    expected_kernel: list[float] = []
    runtime_kernel: list[float] = []
    for group in range(groups):
        sigma_f = table.xss_at(lfiss + group)
        nubar = table.xss_at(getter_nubar + group)
        expected_kernel.append(sigma_f * nubar)
        runtime_kernel.append(sigma_f * nubar)

    expected_sum = sum(expected_kernel)
    runtime_sum = sum(runtime_kernel)
    for group, (expected, runtime) in enumerate(zip(expected_kernel, runtime_kernel), 1):
        kernel_difference = runtime - expected
        probability_difference = runtime / runtime_sum - expected / expected_sum
        max_kernel_difference = max(max_kernel_difference, abs(kernel_difference))
        max_probability_difference = max(max_probability_difference, abs(probability_difference))
        rows.append(
            {
                "group": group,
                "expected_total_kernel": expected,
                "runtime_kernel": runtime,
                "kernel_difference": kernel_difference,
                "expected_probability": expected / expected_sum,
                "runtime_probability": runtime / runtime_sum,
                "probability_difference": probability_difference,
            }
        )

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"source={arguments.source} sha256={sha256(arguments.source)}")
    print(f"xsdir={arguments.xsdir} sha256={sha256(arguments.xsdir)}")
    print(f"mgace={table_path} sha256={sha256(table_path)} address={address}")
    print(
        f"zaid={table.zaid} NGRP={groups} NNUBAR={table.nubar_count} "
        f"first_nubar={first_nubar} getter_nubar={getter_nubar}"
    )
    print(f"single_table_locator={single_table_nubar} unchanged=True")
    print(f"expected_total_kernel_sum={expected_sum:.15g}")
    print(f"runtime_kernel_sum={runtime_sum:.15g}")
    print(f"max_kernel_difference={max_kernel_difference:.15g}")
    print(f"max_probability_difference={max_probability_difference:.15g}")
    print(f"output={arguments.output}")
    passed = max_kernel_difference == 0.0 and max_probability_difference == 0.0
    print(f"criterion=runtime kernel equals initialized total kernel group-by-group; pass={passed}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())