#!/usr/bin/env python3
"""Independently enforce density-mesh reciprocity gates from raw transport records."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    report = json.loads(arguments.report.read_text(encoding="utf-8"))
    if not report["all_structural_pass"]:
        raise ValueError("raw transport structural gate failed")
    grouped: dict[int, dict[str, dict[str, object]]] = {}
    for run in report["runs"]:
        grouped.setdefault(int(run["seed"]), {})[str(run["mode"])] = run
    per_seed = []
    weights_forward = []
    weights_adjoint = []
    for seed, modes in sorted(grouped.items()):
        if set(modes) != {"forward", "adjoint"}:
            raise ValueError(f"seed {seed} lacks a complete forward/adjoint pair")
        forward, adjoint = modes["forward"], modes["adjoint"]
        sigma_forward = float(forward["response"]) * float(forward["relative_error"])
        sigma_adjoint = float(adjoint["response"]) * float(adjoint["relative_error"])
        sigma = math.hypot(sigma_forward, sigma_adjoint)
        z = (float(forward["response"]) - float(adjoint["response"])) / sigma
        per_seed.append({"seed": seed, "forward": forward["response"], "adjoint": adjoint["response"], "sigma": sigma, "z": z, "pass_abs_z_le_3": abs(z) <= 3})
        weights_forward.append((float(forward["response"]), 1.0 / sigma_forward**2))
        weights_adjoint.append((float(adjoint["response"]), 1.0 / sigma_adjoint**2))
    def combine(values: list[tuple[float, float]]) -> tuple[float, float]:
        total_weight = sum(weight for _, weight in values)
        return sum(value * weight for value, weight in values) / total_weight, math.sqrt(1.0 / total_weight)
    forward, sigma_forward = combine(weights_forward)
    adjoint, sigma_adjoint = combine(weights_adjoint)
    combined_z = (forward - adjoint) / math.hypot(sigma_forward, sigma_adjoint)
    result = {"all_structural_pass": True, "per_seed": per_seed, "per_seed_pass": all(item["pass_abs_z_le_3"] for item in per_seed), "combined": {"forward": forward, "sigma_forward": sigma_forward, "adjoint": adjoint, "sigma_adjoint": sigma_adjoint, "z": combined_z, "pass_abs_z_le_3": abs(combined_z) <= 3}}
    result["status"] = "passed" if result["per_seed_pass"] and result["combined"]["pass_abs_z_le_3"] else "failed"
    arguments.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
