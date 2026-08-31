#!/usr/bin/env python3
"""Apply the approved aggregate angular test with Holm-adjusted rank diagnostics."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "20260828_01_f02-mpi-off-serial-provenance"))
from check_angular_formal_strict import CONTINUOUS, continuous_result, discrete_result


ALPHA = 0.05


def evaluate(case: str, values: list[float]) -> dict[str, object]:
    return continuous_result(case, values) if case in CONTINUOUS else discrete_result(values)


def p_value(result: dict[str, object]) -> float:
    if "mean_z" in result:
        return math.erfc(abs(float(result["mean_z"])) / math.sqrt(2.0))
    return math.exp(-float(result["chi_square"]) / 2.0)


def holm(items: list[dict[str, object]]) -> None:
    ordered = sorted(items, key=lambda item: float(item["p_value"]))
    rejected = True
    count = len(ordered)
    for index, item in enumerate(ordered):
        threshold = ALPHA / (count - index)
        item["holm_threshold"] = threshold
        item["holm_reject"] = rejected and float(item["p_value"]) <= threshold
        rejected = bool(item["holm_reject"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    report = json.loads(arguments.report.read_text(encoding="utf-8"))
    if not report["all_structural_pass"]:
        raise ValueError("raw transport structural gate failed")
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for run in report["runs"]:
        grouped.setdefault((str(run["case"]), str(run["mode"])), []).append(run)
    results = []
    for (case, mode), runs in sorted(grouped.items()):
        aggregate_values: list[float] = []
        diagnostics = []
        for run in runs:
            for rank_report in run["mulab_by_rank"]:
                values = list(rank_report["samples"])
                aggregate_values.extend(values)
                diagnostic = {"seed": run["seed"], "rank": rank_report["rank"], **evaluate(case, values)}
                diagnostic["p_value"] = p_value(diagnostic)
                diagnostics.append(diagnostic)
        holm(diagnostics)
        aggregate = evaluate(case, aggregate_values)
        results.append({"case": case, "mode": mode, "aggregate": aggregate, "aggregate_pass": aggregate["pass"], "rank_seed_diagnostics": diagnostics, "holm_any_reject": any(item["holm_reject"] for item in diagnostics)})
    passed = all(item["aggregate_pass"] for item in results)
    arguments.output.write_text(json.dumps({"status": "passed" if passed else "failed", "alpha": ALPHA, "main_test": "aggregate rank×seed samples", "diagnostic_test": "Holm-Bonferroni rank×seed family", "all_structural_pass": True, "results": results}, indent=2) + "\n", encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
