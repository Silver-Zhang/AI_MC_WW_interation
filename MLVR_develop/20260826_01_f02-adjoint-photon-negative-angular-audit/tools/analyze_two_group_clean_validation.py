#!/usr/bin/env python3
"""Enforce warning-free two-group photon angular validation criteria."""

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


def read_sample_report(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = REPORT_PATTERN.search(text)
    if match is None:
        raise ValueError(f"missing sample report in {path}")
    if "Warning:" in text or "Error:" in text:
        raise ValueError(f"warning or error in {path}")
    return json.loads(match.group(1))


def z_score(mean: float, count: int) -> float:
    return (mean - THEORETICAL_MEAN) / math.sqrt(THEORETICAL_VARIANCE / count)


def full_run_result(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    warnings = len(re.findall(r"^Warning:", text, re.MULTILINE))
    errors = len(re.findall(r"^Error:", text, re.MULTILINE))
    finishes = len(re.findall(r"^RMC Calculation Finish\.$", text, re.MULTILINE))
    passed = warnings == 0 and errors == 0 and finishes == 1
    return {"warnings": warnings, "errors": errors, "finish_markers": finishes,
            "passed": passed, "log": str(path), "log_sha256": sha256(path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    logs = arguments.logs.resolve()
    clean_logs = logs / "clean_two_group" if (logs / "clean_two_group").is_dir() else logs
    overall_pass = True
    full_runs = []
    ordinary_cases = []
    secondary_cases = []
    pair_cases = []

    for seed in (17, 23, 41):
        for branch in ("photon", "secondary"):
            run = full_run_result(clean_logs / f"{branch}_two_group_seed{seed}_full_run.txt")
            run.update({"branch": branch, "seed": seed})
            full_runs.append(run)
            overall_pass = overall_pass and bool(run["passed"])

        forward_path = clean_logs / f"photon_two_group_forward_seed{seed}_gdb.txt"
        adjoint_path = clean_logs / f"photon_two_group_adjoint_seed{seed}_gdb.txt"
        secondary_path = clean_logs / f"secondary_two_group_adjoint_seed{seed}_gdb.txt"
        forward = read_sample_report(forward_path)
        adjoint = read_sample_report(adjoint_path)
        secondary = read_sample_report(secondary_path)

        pair_pass = (forward["sample_count"] == adjoint["sample_count"]
                     and forward["sample_sha256"] == adjoint["sample_sha256"])
        pair_cases.append({"seed": seed, "sample_count": forward["sample_count"],
                           "sample_sha256": forward["sample_sha256"], "passed": pair_pass})
        overall_pass = overall_pass and pair_pass

        for target, report, path in ((ordinary_cases, adjoint, adjoint_path),
                                     (secondary_cases, secondary, secondary_path)):
            count = int(report["sample_count"])
            score = z_score(float(report["mean"]), count)
            passed = int(report["support_violation_count"]) == 0 and abs(score) <= 3.0
            target.append({"seed": seed, "sample_count": count,
                           "observed_min": report["observed_min"], "observed_max": report["observed_max"],
                           "mean": report["mean"], "z_score": score,
                           "support_violation_count": report["support_violation_count"],
                           "passed": passed, "log_sha256": sha256(path)})
            overall_pass = overall_pass and passed

    branches = {}
    for name, cases in (("ordinary_photon", ordinary_cases), ("photon_to_neutron", secondary_cases)):
        count = sum(int(case["sample_count"]) for case in cases)
        mean = sum(float(case["mean"]) * int(case["sample_count"]) for case in cases) / count
        combined = {
            "sample_count": count,
            "observed_min": min(float(case["observed_min"]) for case in cases),
            "observed_max": max(float(case["observed_max"]) for case in cases),
            "mean": mean,
            "z_score": z_score(mean, count),
            "support_violation_count": sum(int(case["support_violation_count"]) for case in cases),
        }
        combined["passed"] = combined["support_violation_count"] == 0 and abs(combined["z_score"]) <= 3.0
        overall_pass = overall_pass and bool(combined["passed"])
        branches[name] = {"cases": cases, "combined": combined}

    report = {
        "status": "passed" if overall_pass else "failed",
        "criteria": [
            "all six full runs contain exactly one finish marker and zero warnings/errors",
            "all nine GDB logs contain zero warnings/errors",
            "support violations = 0 and abs(z) <= 3 for every seed and combined",
            "ordinary forward and adjoint packed sample SHA256 values are equal",
        ],
        "full_runs": full_runs,
        "branches": branches,
        "ordinary_forward_adjoint_pairs": pair_cases,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(f"status={report['status']}")
    print(f"full_runs={len(full_runs)} clean={sum(bool(run['passed']) for run in full_runs)}")
    for name, branch in branches.items():
        combined = branch["combined"]
        print(f"branch={name} n={combined['sample_count']} min={combined['observed_min']:.12g} "
              f"max={combined['observed_max']:.12g} mean={combined['mean']:.12g} "
              f"z={combined['z_score']:.6f} violations={combined['support_violation_count']}")
    print(f"paired_seeds={len(pair_cases)} equal={sum(bool(pair['passed']) for pair in pair_cases)}")
    print(f"report={arguments.output.resolve()}")
    print(f"report_sha256={sha256(arguments.output)}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
