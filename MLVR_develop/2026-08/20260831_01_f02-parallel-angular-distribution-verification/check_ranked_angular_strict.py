#!/usr/bin/env python3
"""Apply frozen angular gates to every MPI rank, seed, and aggregate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "20260828_01_f02-mpi-off-serial-provenance"))
from check_angular_formal_strict import continuous_result, discrete_result, CONTINUOUS


def evaluate(case: str, values: list[float]) -> dict[str, object]:
    return continuous_result(case, values) if case in CONTINUOUS else discrete_result(values)


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
        per_seed, per_rank, all_values = [], [], []
        for run in runs:
            seed_values = []
            for rank_report in run["mulab_by_rank"]:
                values = list(rank_report["samples"])
                seed_values.extend(values)
                all_values.extend(values)
                per_rank.append({"seed": run["seed"], "rank": rank_report["rank"], **evaluate(case, values)})
            per_seed.append({"seed": run["seed"], **evaluate(case, seed_values)})
        aggregate = evaluate(case, all_values)
        results.append({"case": case, "mode": mode, "per_rank": per_rank, "per_seed": per_seed, "aggregate": aggregate, "per_rank_pass": all(item["pass"] for item in per_rank), "per_seed_pass": all(item["pass"] for item in per_seed), "aggregate_pass": aggregate["pass"]})
    passed = all(item["per_rank_pass"] and item["per_seed_pass"] and item["aggregate_pass"] for item in results)
    arguments.output.write_text(json.dumps({"status": "passed" if passed else "failed", "all_structural_pass": True, "results": results}, indent=2) + "\n", encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
