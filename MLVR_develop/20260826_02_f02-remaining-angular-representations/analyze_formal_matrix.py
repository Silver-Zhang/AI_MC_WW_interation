#!/usr/bin/env python3
"""Analyze the frozen formal angular matrix without changing its samples."""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path


CONTINUOUS = {
    "isotropic": (-1.0, 1.0, 0.0, 1.0 / 3.0),
    "one_variable_positive": (0.0, 1.0, 0.5, 1.0 / 12.0),
    "equiprobable_multi_bin": (-1.0, 1.0, -1.0 / 12.0, 17.0 / 48.0),
}
DISCRETE = {"discrete_cosine": ((-0.8, 0.0, 0.9), (0.2, 0.5, 0.3))}


def sample_variance(values: list[float]) -> float:
    return statistics.variance(values)


def mean_z(values: list[float], expected_mean: float, expected_variance: float) -> float:
    return (statistics.fmean(values) - expected_mean) / math.sqrt(expected_variance / len(values))


def bootstrap_variance_interval(case: str, n: int) -> tuple[float, float]:
    lower, upper, _, _ = CONTINUOUS[case]
    rng = random.Random(20260827)
    variances = []
    for _ in range(20_000):
        if case == "equiprobable_multi_bin":
            boundaries = (-1.0, -0.5, 0.25, 1.0)
            values = [boundaries[index := rng.randrange(3)] + rng.random() * (boundaries[index + 1] - boundaries[index]) for _ in range(n)]
        else:
            values = [rng.uniform(lower, upper) for _ in range(n)]
        variances.append(sample_variance(values))
    variances.sort()
    return variances[99], variances[19_899]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    report = json.loads(arguments.report.read_text(encoding="utf-8"))
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for run in report["runs"]:
        grouped[(run["case"], run["mode"])].append(run)
    results = []
    for (case, mode), runs in sorted(grouped.items()):
        all_samples = [value for run in runs for value in run["mulab"]["samples"]]
        seed_results = []
        if case in CONTINUOUS:
            lower, upper, expected_mean, expected_variance = CONTINUOUS[case]
            for run in runs:
                values = run["mulab"]["samples"]
                seed_results.append({"seed": run["seed"], "n": len(values), "min": min(values), "max": max(values), "mean": statistics.fmean(values), "variance": sample_variance(values), "support_ok": all(lower <= value <= upper for value in values), "mean_z": mean_z(values, expected_mean, expected_variance)})
            interval = bootstrap_variance_interval(case, len(all_samples))
            aggregate = {"n": len(all_samples), "min": min(all_samples), "max": max(all_samples), "mean": statistics.fmean(all_samples), "variance": sample_variance(all_samples), "support_ok": all(lower <= value <= upper for value in all_samples), "mean_z": mean_z(all_samples, expected_mean, expected_variance), "variance_interval_99": interval, "variance_ok": interval[0] <= sample_variance(all_samples) <= interval[1]}
        else:
            points, probabilities = DISCRETE[case]
            for run in runs:
                counts = Counter(run["mulab"]["samples"])
                observed = [counts[point] for point in points]
                expected = [len(run["mulab"]["samples"]) * probability for probability in probabilities]
                chi_square = sum((actual - target) ** 2 / target for actual, target in zip(observed, expected))
                seed_results.append({"seed": run["seed"], "n": len(run["mulab"]["samples"]), "counts": observed, "support_ok": all(value in points for value in run["mulab"]["samples"]), "chi_square": chi_square})
            counts = Counter(all_samples)
            observed = [counts[point] for point in points]
            expected = [len(all_samples) * probability for probability in probabilities]
            chi_square = sum((actual - target) ** 2 / target for actual, target in zip(observed, expected))
            aggregate = {"n": len(all_samples), "counts": observed, "support_ok": all(value in points for value in all_samples), "chi_square": chi_square, "critical_value": 9.210, "chi_square_ok": chi_square < 9.210}
        results.append({"case": case, "mode": mode, "per_seed": seed_results, "aggregate": aggregate})
    status = all(item["aggregate"].get("support_ok") and abs(item["aggregate"].get("mean_z", 0.0)) <= 3 and item["aggregate"].get("variance_ok", True) and item["aggregate"].get("chi_square_ok", True) for item in results)
    arguments.output.write_text(json.dumps({"status": "passed" if status else "failed", "results": results}, indent=2) + "\n", encoding="utf-8")
    for item in results:
        print(f"{item['case']} {item['mode']} {item['aggregate']}")
    return 0 if status else 1


if __name__ == "__main__":
    raise SystemExit(main())
