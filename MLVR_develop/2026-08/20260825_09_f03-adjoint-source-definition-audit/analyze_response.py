#!/usr/bin/env python3
"""Evaluate F03 forward composite response against adjoint response."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path

TALLY_RE = re.compile(r"^\s*(?P<group>\d+)\s+(?P<energy>[+\-0-9.Ee]+)\s+(?P<average>[+\-0-9.Ee]+)\s+(?P<re>[+\-0-9.Ee]+)\s*$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tally(path: Path, cell: int, group: int) -> tuple[float, float]:
    current_cell = None
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) >= 5 and fields[0].isdigit() and fields[1].isdigit():
            current_cell = int(fields[0])
            candidate_group, value, relative_error = int(fields[1]), float(fields[3]), float(fields[4])
        else:
            match = TALLY_RE.match(line)
            if not match or current_cell is None:
                continue
            candidate_group, value, relative_error = int(match["group"]), float(match["average"]), float(match["re"])
        if current_cell == cell and candidate_group == group:
            if not math.isfinite(value) or value <= 0 or not math.isfinite(relative_error):
                raise RuntimeError(f"invalid tally: {path}: {line}")
            return value, abs(value * relative_error)
    raise RuntimeError(f"missing tally cell={cell}, group={group}: {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    output = arguments.output_dir.resolve()
    manifest = json.loads((root / "manifest.json").read_text(encoding="ascii"))
    components = manifest["response_components"]
    grouped = defaultdict(dict)
    anomalies = []
    rows = []
    for run in manifest["runs"]:
        directory = root / Path(run["input"]).parent
        if int((directory / "exit_code.txt").read_text(encoding="ascii").strip()) != 0:
            raise RuntimeError(f"nonzero run: {directory}")
        if run["mode"] == "forward":
            values = [tally(directory / "inp.Tally", int(component["cell"]), 31 - int(component["group"])) for component in components]
            response = sum(float(component["strength_H"]) * value for component, (value, _) in zip(components, values))
            sigma = math.sqrt(sum((float(component["strength_H"]) * error) ** 2 for component, (_, error) in zip(components, values)))
        else:
            value, sigma = tally(directory / "inp.Tally", 1, 31 - 14)
            response = value
        record = {"case": run["case"], "seed": run["seed"], "mode": run["mode"], "response": response, "sigma": sigma, "relative_error": sigma / response, "tally_sha256": sha256(directory / "inp.Tally")}
        rows.append(record)
        grouped[(run["case"], run["seed"])][run["mode"]] = record
        for name in ("stdout.log", "stderr.log", "inp.out"):
            path = directory / name
            if path.exists():
                for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    lowered = line.lower()
                    if ("warning:" in lowered or "error:" in lowered or "nan" in lowered or "inf" in lowered) and "information" not in lowered and "particle energy larger than maximum energy group upper bound" not in lowered:
                        anomalies.append(f"{path.relative_to(root)}:{number}:{line}")
    pairs = []
    for (case, seed), modes in sorted(grouped.items()):
        if set(modes) != {"forward", "adjoint"}:
            raise RuntimeError(f"incomplete pair {case}/{seed}")
        forward, adjoint = modes["forward"], modes["adjoint"]
        sigma_delta = math.hypot(forward["sigma"], adjoint["sigma"])
        pairs.append({"case": case, "seed": seed, "R_F": forward["response"], "sigma_F": forward["sigma"], "R_A": adjoint["response"], "sigma_A": adjoint["sigma"], "z": (forward["response"] - adjoint["response"]) / sigma_delta, "pass_abs_z_le_3": abs((forward["response"] - adjoint["response"]) / sigma_delta) <= 3})
    summaries = []
    for case in sorted({row["case"] for row in pairs}):
        selected = [row for row in pairs if row["case"] == case]
        forward_weights = [1.0 / row["sigma_F"] ** 2 for row in selected]
        adjoint_weights = [1.0 / row["sigma_A"] ** 2 for row in selected]
        forward_mean = sum(row["R_F"] * weight for row, weight in zip(selected, forward_weights)) / sum(forward_weights)
        adjoint_mean = sum(row["R_A"] * weight for row, weight in zip(selected, adjoint_weights)) / sum(adjoint_weights)
        forward_sigma = 1.0 / math.sqrt(sum(forward_weights))
        adjoint_sigma = 1.0 / math.sqrt(sum(adjoint_weights))
        z_score = (forward_mean - adjoint_mean) / math.hypot(forward_sigma, adjoint_sigma)
        summaries.append({"case": case, "independent_seeds": len(selected), "R_F": forward_mean, "sigma_F": forward_sigma, "R_A": adjoint_mean, "sigma_A": adjoint_sigma, "z": z_score, "pass_abs_z_le_3": abs(z_score) <= 3.0, "all_individual_abs_z_le_3": all(row["pass_abs_z_le_3"] for row in selected), "max_individual_abs_z": max(abs(row["z"]) for row in selected)})
    overall_forward_weights = [1.0 / row["sigma_F"] ** 2 for row in summaries]
    overall_adjoint_weights = [1.0 / row["sigma_A"] ** 2 for row in summaries]
    overall_forward = sum(row["R_F"] * weight for row, weight in zip(summaries, overall_forward_weights)) / sum(overall_forward_weights)
    overall_adjoint = sum(row["R_A"] * weight for row, weight in zip(summaries, overall_adjoint_weights)) / sum(overall_adjoint_weights)
    overall_sigma_forward = 1.0 / math.sqrt(sum(overall_forward_weights))
    overall_sigma_adjoint = 1.0 / math.sqrt(sum(overall_adjoint_weights))
    overall_z = (overall_forward - overall_adjoint) / math.hypot(overall_sigma_forward, overall_sigma_adjoint)
    overall = {"independent_cases": len(summaries), "R_F": overall_forward, "sigma_F": overall_sigma_forward, "R_A": overall_adjoint, "sigma_A": overall_sigma_adjoint, "z": overall_z, "pass_abs_z_le_3": abs(overall_z) <= 3.0}
    output.mkdir(parents=True, exist_ok=True)
    for filename, data in (("runs.csv", rows), ("paired_seeds.csv", pairs), ("summary.csv", summaries), ("overall.csv", [overall])):
        with (output / filename).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    (output / "anomalies.log").write_text("\n".join(anomalies) + ("\n" if anomalies else ""), encoding="utf-8")
    print(f"manifest_sha256={sha256(root / 'manifest.json')}")
    print(f"pair_count={len(pairs)} anomaly_lines={len(anomalies)}")
    for row in pairs:
        print(",".join(f"{key}={value}" for key, value in row.items()))
    print("combined:")
    for row in summaries:
        print(",".join(f"{key}={value}" for key, value in row.items()))
    print("overall:")
    print(",".join(f"{key}={value}" for key, value in overall.items()))
    passed = not anomalies and all(row["pass_abs_z_le_3"] for row in pairs) and all(row["pass_abs_z_le_3"] and row["all_individual_abs_z_le_3"] for row in summaries) and overall["pass_abs_z_le_3"]
    print(f"criterion=no unexplained anomalies and all individual/combined/overall |z| <= 3; pass={passed}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
