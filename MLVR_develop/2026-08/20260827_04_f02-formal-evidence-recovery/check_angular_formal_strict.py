#!/usr/bin/env python3
"""Independently enforce per-seed and aggregate angular acceptance gates."""

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
CRITICAL = 9.210
INTERVAL_CACHE: dict[tuple[str, int], tuple[float, float]] = {}


def variance(values: list[float]) -> float:
    return statistics.variance(values)


def mean_z(values: list[float], mean: float, expected_variance: float) -> float:
    return (statistics.fmean(values) - mean) / math.sqrt(expected_variance / len(values))


def interval(case: str, n: int) -> tuple[float, float]:
    key = (case, n)
    if key in INTERVAL_CACHE:
        return INTERVAL_CACHE[key]
    lower, upper, _, _ = CONTINUOUS[case]
    generator = random.Random(20260827 + n)
    values: list[float] = []
    variances: list[float] = []
    for _ in range(20_000):
        if case == "equiprobable_multi_bin":
            points = (-1.0, -0.5, 0.25, 1.0)
            values = [points[index := generator.randrange(3)] + generator.random() * (points[index + 1] - points[index]) for _ in range(n)]
        else:
            values = [generator.uniform(lower, upper) for _ in range(n)]
        variances.append(variance(values))
    variances.sort()
    INTERVAL_CACHE[key] = (variances[99], variances[19_899])
    return INTERVAL_CACHE[key]


def continuous_result(case: str, values: list[float]) -> dict[str, object]:
    lower, upper, expected_mean, expected_variance = CONTINUOUS[case]
    bounds = interval(case, len(values))
    result = {"n": len(values), "min": min(values), "max": max(values), "mean": statistics.fmean(values), "variance": variance(values), "support_ok": all(lower <= value <= upper for value in values), "mean_z": mean_z(values, expected_mean, expected_variance), "variance_interval_99": bounds}
    result["variance_ok"] = bounds[0] <= result["variance"] <= bounds[1]
    result["pass"] = result["support_ok"] and abs(result["mean_z"]) <= 3 and result["variance_ok"]
    return result


def discrete_result(values: list[float]) -> dict[str, object]:
    points, probabilities = DISCRETE["discrete_cosine"]
    counts = Counter(values)
    observed = [counts[point] for point in points]
    expected = [len(values) * probability for probability in probabilities]
    chi_square = sum((actual - target) ** 2 / target for actual, target in zip(observed, expected))
    result = {"n": len(values), "counts": observed, "support_ok": all(value in points for value in values), "chi_square": chi_square, "critical_value": CRITICAL}
    result["chi_square_ok"] = chi_square < CRITICAL
    result["pass"] = result["support_ok"] and result["chi_square_ok"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    report = json.loads(arguments.report.read_text(encoding="utf-8"))
    if not report["all_structural_pass"]:
        raise ValueError("raw transport structural gate failed")
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for run in report["runs"]:
        grouped[(str(run["case"]), str(run["mode"]))].append(run)
    results = []
    for (case, mode), runs in sorted(grouped.items()):
        per_seed = []
        all_values: list[float] = []
        for run in runs:
            values = list(run["mulab"]["samples"])
            all_values.extend(values)
            per_seed.append({"seed": run["seed"], **(continuous_result(case, values) if case in CONTINUOUS else discrete_result(values))})
        aggregate = continuous_result(case, all_values) if case in CONTINUOUS else discrete_result(all_values)
        results.append({"case": case, "mode": mode, "per_seed": per_seed, "aggregate": aggregate, "per_seed_pass": all(item["pass"] for item in per_seed), "aggregate_pass": aggregate["pass"]})
    passed = all(item["per_seed_pass"] and item["aggregate_pass"] for item in results)
    arguments.output.write_text(json.dumps({"status": "passed" if passed else "failed", "all_structural_pass": True, "results": results}, indent=2) + "\n", encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
