#!/usr/bin/env python3
"""Audit deployed C5G7 double-nubar data and quantify V3 test power.

This is a read-only nuclear-data analysis. It follows the same ASCII MGACE
NXS/JXS/XSS indexing used by RMC and does not synthesize or alter data.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "v4_reciprocity"))
from screen_mgace_pairs import read_ascii_mgace, sha256, xsdir_entries


def chi_square_divergence(observed: list[float], null: list[float]) -> float:
    return sum((left - right) ** 2 / right for left, right in zip(observed, null) if right > 0.0)


def required_samples_for_power(effect: float, alpha: float = 0.05, power: float = 0.80) -> int:
    # One-degree-of-freedom normal approximation. It is intentionally labeled
    # as an estimate; the exact multinomial test would need a SciPy dependency.
    z_alpha = 1.959963984540054
    z_power = 0.8416212335729143
    return math.ceil((z_alpha + z_power) ** 2 / effect)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xsdir", type=Path, required=True)
    parser.add_argument("--zaid", default="10001.01m")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    entries = xsdir_entries(arguments.xsdir)
    path, address = entries[arguments.zaid.upper()]
    table = read_ascii_mgace(arguments.zaid.upper(), path, address)
    groups = table.groups
    if table.nubar_count <= 1:
        raise RuntimeError(f"{arguments.zaid} has NNUBAR={table.nubar_count}, expected > 1")

    # RMC stores JXS with a sentinel at index 0.  The parser omits that
    # sentinel, so C++ JXS[3]/[4]/[5] map to tuple indices 2/3/4.
    lfiss = table.jxs[2]
    lnu_first = table.jxs[3]
    lnu_second = lnu_first + groups
    lchi = table.jxs[4]
    sigma_f = [table.xss_at(lfiss + group) for group in range(groups)]
    nubar_first = [table.xss_at(lnu_first + group) for group in range(groups)]
    nubar_second = [table.xss_at(lnu_second + group) for group in range(groups)]
    chi = [table.xss_at(lchi + group) for group in range(groups)]
    kernel_first = [sigma * nu for sigma, nu in zip(sigma_f, nubar_first)]
    kernel_second = [sigma * nu for sigma, nu in zip(sigma_f, nubar_second)]
    sum_first = sum(kernel_first)
    sum_second = sum(kernel_second)
    probabilities_first = [value / sum_first for value in kernel_first]
    probabilities_second = [value / sum_second for value in kernel_second]

    # The runtime loop exits at the last group even if its first-block kernel
    # cannot exhaust the second-block proposal threshold.  Therefore the exact
    # implementation distribution uses first-block masses for groups 1..G-1
    # and assigns the residual to group G.
    probabilities_runtime_exact = [value / sum_second for value in kernel_first[:-1]]
    probabilities_runtime_exact.append(1.0 - sum(probabilities_runtime_exact))

    effect = chi_square_divergence(probabilities_runtime_exact, probabilities_second)
    samples_80 = required_samples_for_power(effect)
    max_probability_difference = max(
        abs(left - right) for left, right in zip(probabilities_runtime_exact, probabilities_second)
    )
    max_nubar_relative_difference = max(
        abs(left - right) / right for left, right in zip(nubar_first, nubar_second) if right != 0.0
    )

    rows = []
    for group in range(groups):
        rows.append(
            {
                "group": group + 1,
                "sigma_f": sigma_f[group],
                "nubar_first": nubar_first[group],
                "nubar_second": nubar_second[group],
                "kernel_first": kernel_first[group],
                "kernel_second": kernel_second[group],
                "prob_first_normalized": probabilities_first[group],
                "prob_second_expected": probabilities_second[group],
                "prob_runtime_exact": probabilities_runtime_exact[group],
                "runtime_minus_expected": probabilities_runtime_exact[group] - probabilities_second[group],
                "chi": chi[group],
            }
        )

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"xsdir={arguments.xsdir} sha256={sha256(arguments.xsdir)}")
    print(f"mgace={path} sha256={sha256(path)} address={address}")
    print(
        f"zaid={table.zaid} NGRP={groups} NNUBAR={table.nubar_count} "
        f"LFISS={lfiss} JXS5_first_nubar={lnu_first} getter_second_nubar={lnu_second} LCHI={lchi}"
    )
    print(f"sum_first_nubar_sigma_f={sum_first:.15g}")
    print(f"sum_second_nubar_sigma_f={sum_second:.15g}")
    print(f"kernel_sum_difference={sum_second - sum_first:.15g}")
    print(f"max_nubar_relative_difference={max_nubar_relative_difference:.15g}")
    print(f"max_runtime_probability_difference={max_probability_difference:.15g}")
    print(f"pearson_effect_w2={effect:.15g}")
    print(f"estimated_samples_for_80pct_power_alpha_0.05={samples_80}")
    print("power_method=normal approximation N=(z_0.975+z_0.8)^2/w^2; exact multinomial not evaluated")
    print(f"output={arguments.output}")
    for row in rows:
        print(",".join(f"{key}={value}" for key, value in row.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
