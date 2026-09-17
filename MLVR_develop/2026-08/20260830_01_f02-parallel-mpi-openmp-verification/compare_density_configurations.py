#!/usr/bin/env python3
"""Compare independently sampled formal response reports across configurations."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def paired_z(reference: dict[str, object], candidate: dict[str, object]) -> list[dict[str, object]]:
    reference_runs = {(str(run["mode"]), int(run["seed"])): run for run in reference["runs"]}
    rows = []
    for run in candidate["runs"]:
        key = (str(run["mode"]), int(run["seed"]))
        other = reference_runs[key]
        value, other_value = float(run["response"]), float(other["response"])
        sigma = math.hypot(value * float(run["relative_error"]), other_value * float(other["relative_error"]))
        z = (value - other_value) / sigma
        rows.append({"mode": key[0], "seed": key[1], "reference": other_value, "candidate": value, "z": z, "pass_abs_z_le_3": abs(z) <= 3.0})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--reports", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    reference = json.loads(arguments.reference.read_text(encoding="utf-8"))
    result = {"reference": str(arguments.reference), "comparisons": []}
    for path in arguments.reports:
        candidate = json.loads(path.read_text(encoding="utf-8"))
        rows = paired_z(reference, candidate)
        result["comparisons"].append({"report": str(path), "all_abs_z_le_3": all(row["pass_abs_z_le_3"] for row in rows), "max_abs_z": max(abs(float(row["z"])) for row in rows), "rows": rows})
    result["status"] = "passed" if all(item["all_abs_z_le_3"] for item in result["comparisons"]) else "failed"
    arguments.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
