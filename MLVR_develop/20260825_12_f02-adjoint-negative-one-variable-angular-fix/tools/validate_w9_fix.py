#!/usr/bin/env python3
"""Validate W9 forward/adjoint angular reports against the qualified kernel."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


EXPECTED_SUPPORT = [-1.0, 0.0]
EXPECTED_MEAN = -0.5
EXPECTED_VARIANCE = 1.0 / 12.0
MAX_ABS_Z = 3.0


def load_samples(report_path: Path) -> tuple[list[float], dict[str, object]]:
    report = json.loads(report_path.read_text(encoding="ascii"))
    runs = {run["mode"]: run for run in report["runs"]}
    if set(runs) != {"forward", "adjoint"}:
        raise AssertionError(f"{report_path}: expected forward and adjoint runs")

    samples_by_mode: dict[str, list[float]] = {}
    for mode, run in runs.items():
        if run["expected_support"] != EXPECTED_SUPPORT:
            raise AssertionError(f"{report_path}: unexpected {mode} support")
        if run["support_violation_count"] != 0:
            raise AssertionError(f"{report_path}: {mode} has support violations")
        samples = [sample["mu"] for sample in run["reconstructed_samples"]]
        if not samples:
            raise AssertionError(f"{report_path}: {mode} has no reconstructed samples")
        samples_by_mode[mode] = samples

    forward = samples_by_mode["forward"]
    adjoint = samples_by_mode["adjoint"]
    if forward != adjoint:
        raise AssertionError(f"{report_path}: forward and adjoint samples differ")

    mean = math.fsum(adjoint) / len(adjoint)
    standard_error = math.sqrt(EXPECTED_VARIANCE / len(adjoint))
    z_score = (mean - EXPECTED_MEAN) / standard_error
    if abs(z_score) > MAX_ABS_Z:
        raise AssertionError(f"{report_path}: mean z={z_score} exceeds {MAX_ABS_Z}")

    result = {
        "report": str(report_path.resolve()),
        "report_sha256": report_path_sha256(report_path),
        "sample_count": len(adjoint),
        "mean": mean,
        "mean_z": z_score,
        "support_violation_count": 0,
        "paired_samples_equal": True,
    }
    return adjoint, result


def report_path_sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()

    all_samples: list[float] = []
    results: list[dict[str, object]] = []
    for report_path in arguments.reports:
        samples, result = load_samples(report_path)
        all_samples.extend(samples)
        results.append(result)

    combined_mean = math.fsum(all_samples) / len(all_samples)
    combined_standard_error = math.sqrt(EXPECTED_VARIANCE / len(all_samples))
    combined_z = (combined_mean - EXPECTED_MEAN) / combined_standard_error
    if abs(combined_z) > MAX_ABS_Z:
        raise AssertionError(f"combined mean z={combined_z} exceeds {MAX_ABS_Z}")

    output = {
        "status": "passed",
        "expected_support": EXPECTED_SUPPORT,
        "expected_mean": EXPECTED_MEAN,
        "max_abs_z": MAX_ABS_Z,
        "reports": results,
        "combined": {
            "sample_count": len(all_samples),
            "mean": combined_mean,
            "mean_z": combined_z,
        },
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(output, indent=2) + "\n", encoding="ascii")

    for result in results:
        print(
            f"samples={result['sample_count']} mean={result['mean']:.12g} "
            f"z={result['mean_z']:.6g} paired_equal=true violations=0"
        )
    print(
        f"combined_samples={len(all_samples)} combined_mean={combined_mean:.12g} "
        f"combined_z={combined_z:.6g} status=passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())