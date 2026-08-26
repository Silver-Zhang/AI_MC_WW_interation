#!/usr/bin/env python3
"""Summarize multi-seed GDB MuLab reports and enforce acceptance criteria."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path


REPORT_PATTERN = re.compile(r"MLVR_MULAB_REPORT=(\{.*\})")
THEORETICAL_MEAN = -0.5
THEORETICAL_VARIANCE = 1.0 / 12.0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_report(path: Path) -> dict[str, object]:
    match = REPORT_PATTERN.search(path.read_text(encoding="utf-8", errors="replace"))
    if match is None:
        raise ValueError(f"missing MuLab report in {path}")
    return json.loads(match.group(1))


def z_score(mean: float, count: int) -> float:
    return (mean - THEORETICAL_MEAN) / math.sqrt(THEORETICAL_VARIANCE / count)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    logs = arguments.logs.resolve()

    paths: list[tuple[str, int, Path]] = []
    for branch, prefix in (("ordinary_photon", "photon"), ("photon_to_neutron", "secondary")):
        for seed in (17, 23, 41):
            paths.append((branch, seed, logs / f"{prefix}_postfix_seed{seed}_gdb.txt"))

    branches: dict[str, object] = {}
    overall_pass = True
    for branch in ("ordinary_photon", "photon_to_neutron"):
        cases = []
        weighted_sum = 0.0
        total_count = 0
        combined_min = math.inf
        combined_max = -math.inf
        combined_violations = 0
        for current_branch, seed, path in paths:
            if current_branch != branch:
                continue
            report = read_report(path)
            count = int(report["sample_count"])
            mean = float(report["mean"])
            score = z_score(mean, count)
            violations = int(report["support_violation_count"])
            passed = violations == 0 and abs(score) <= 3.0
            overall_pass = overall_pass and passed
            cases.append({
                "seed": seed,
                "sample_count": count,
                "observed_min": report["observed_min"],
                "observed_max": report["observed_max"],
                "mean": mean,
                "z_score": score,
                "support_violation_count": violations,
                "passed": passed,
                "log": str(path),
                "log_sha256": sha256(path),
            })
            weighted_sum += mean * count
            total_count += count
            combined_min = min(combined_min, float(report["observed_min"]))
            combined_max = max(combined_max, float(report["observed_max"]))
            combined_violations += violations
        combined_mean = weighted_sum / total_count
        combined_z = z_score(combined_mean, total_count)
        combined_pass = combined_violations == 0 and abs(combined_z) <= 3.0
        overall_pass = overall_pass and combined_pass
        branches[branch] = {
            "cases": cases,
            "combined": {
                "sample_count": total_count,
                "observed_min": combined_min,
                "observed_max": combined_max,
                "mean": combined_mean,
                "z_score": combined_z,
                "support_violation_count": combined_violations,
                "passed": combined_pass,
            },
        }

    output = {
        "status": "passed" if overall_pass else "failed",
        "acceptance": "support violations = 0 and abs(z) <= 3 for every seed and combined",
        "expected_support": [-1.0, 0.0],
        "theoretical_mean": THEORETICAL_MEAN,
        "theoretical_variance": THEORETICAL_VARIANCE,
        "branches": branches,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(output, indent=2) + "\n", encoding="ascii")
    print(f"status={output['status']}")
    for branch, branch_report in branches.items():
        combined = branch_report["combined"]
        print(
            f"branch={branch} n={combined['sample_count']} min={combined['observed_min']:.12g} "
            f"max={combined['observed_max']:.12g} mean={combined['mean']:.12g} "
            f"z={combined['z_score']:.6f} violations={combined['support_violation_count']}"
        )
    print(f"report={arguments.output.resolve()}")
    print(f"report_sha256={sha256(arguments.output)}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
