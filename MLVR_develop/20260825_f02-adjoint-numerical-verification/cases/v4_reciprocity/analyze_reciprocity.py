#!/usr/bin/env python3
"""Extract paired RMC tallies and evaluate forward-adjoint reciprocity."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path


TALLY_ROW = re.compile(
    r"^\s*(?P<group>\d+)\s+(?P<energy>[+\-0-9.Ee]+)\s+"
    r"(?P<average>[+\-0-9.Ee]+)\s+(?P<relative_error>[+\-0-9.Ee]+)\s*$"
)
ANOMALY = re.compile(r"warning:|error:|\bnan\b|\binf\b", re.IGNORECASE)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tally_value(path: Path, tally_group: int) -> tuple[float, float, float]:
    for line in path.read_text(encoding="utf-8").splitlines():
        match = TALLY_ROW.match(line)
        if match and int(match.group("group")) == tally_group:
            average = float(match.group("average"))
            relative_error = float(match.group("relative_error"))
            return average, relative_error, average * relative_error
    raise RuntimeError(f"tally group {tally_group} not found in {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--runs-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--anomalies-output", type=Path, required=True)
    arguments = parser.parse_args()

    manifest_path = arguments.root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows: list[dict[str, object]] = []
    anomalies: list[str] = []
    grouped: dict[tuple[str, int], dict[str, dict[str, object]]] = defaultdict(dict)

    for run in manifest["runs"]:
        directory = arguments.root / run["input"]
        directory = directory.parent
        exit_code = int((directory / "exit_code.txt").read_text().strip())
        average, relative_error, sigma = tally_value(directory / "inp.Tally", int(run["response_tally_group"]))
        output_row = {
            **run,
            "exit_code": exit_code,
            "average": average,
            "relative_error": relative_error,
            "sigma": sigma,
            "tally_sha256": sha256(directory / "inp.Tally"),
            "stdout_sha256": sha256(directory / "stdout.log"),
        }
        rows.append(output_row)
        grouped[(str(run["pair"]), int(run["seed"]))][str(run["mode"])] = output_row

        for name in ("stdout.log", "stderr.log", "inp.out"):
            path = directory / name
            if not path.exists():
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if ANOMALY.search(line) and "information" not in line.lower():
                    anomalies.append(f"{path.relative_to(arguments.root)}:{number}:{line}")

    arguments.runs_output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.runs_output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    pair_rows: list[dict[str, object]] = []
    for (pair, seed), modes in sorted(grouped.items()):
        if set(modes) != {"forward", "adjoint"}:
            raise RuntimeError(f"incomplete pair {pair}/seed_{seed}: {sorted(modes)}")
        forward = modes["forward"]
        adjoint = modes["adjoint"]
        denominator = math.hypot(float(forward["sigma"]), float(adjoint["sigma"]))
        z_score = (float(forward["average"]) - float(adjoint["average"])) / denominator
        pair_rows.append(
            {
                "pair": pair,
                "seed": seed,
                "R_F": forward["average"],
                "sigma_F": forward["sigma"],
                "RE_F": forward["relative_error"],
                "R_A": adjoint["average"],
                "sigma_A": adjoint["sigma"],
                "RE_A": adjoint["relative_error"],
                "z": z_score,
                "pass_abs_z_le_3": abs(z_score) <= 3.0,
            }
        )

    summary_rows: list[dict[str, object]] = []
    for pair in sorted({str(row["pair"]) for row in pair_rows}):
        selected = [row for row in pair_rows if row["pair"] == pair]
        inverse_variance_forward = [1.0 / float(row["sigma_F"]) ** 2 for row in selected]
        inverse_variance_adjoint = [1.0 / float(row["sigma_A"]) ** 2 for row in selected]
        combined_forward = sum(float(row["R_F"]) * weight for row, weight in zip(selected, inverse_variance_forward)) / sum(inverse_variance_forward)
        combined_adjoint = sum(float(row["R_A"]) * weight for row, weight in zip(selected, inverse_variance_adjoint)) / sum(inverse_variance_adjoint)
        combined_sigma_forward = 1.0 / math.sqrt(sum(inverse_variance_forward))
        combined_sigma_adjoint = 1.0 / math.sqrt(sum(inverse_variance_adjoint))
        combined_z = (combined_forward - combined_adjoint) / math.hypot(combined_sigma_forward, combined_sigma_adjoint)
        summary_rows.append(
            {
                "pair": pair,
                "independent_seeds": len(selected),
                "R_F": combined_forward,
                "sigma_F": combined_sigma_forward,
                "R_A": combined_adjoint,
                "sigma_A": combined_sigma_adjoint,
                "z": combined_z,
                "pass_abs_z_le_3": abs(combined_z) <= 3.0,
                "all_individual_abs_z_le_3": all(bool(row["pass_abs_z_le_3"]) for row in selected),
                "max_individual_abs_z": max(abs(float(row["z"])) for row in selected),
            }
        )

    with arguments.summary_output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)
    arguments.anomalies_output.write_text("\n".join(anomalies) + ("\n" if anomalies else ""), encoding="utf-8")

    print(f"manifest_sha256={sha256(manifest_path)}")
    print(f"run_count={len(rows)} paired_seed_count={len(pair_rows)} anomaly_lines={len(anomalies)}")
    print("per-seed:")
    for row in pair_rows:
        print(",".join(f"{key}={value}" for key, value in row.items()))
    print("combined:")
    for row in summary_rows:
        print(",".join(f"{key}={value}" for key, value in row.items()))
    passed = all(bool(row["pass_abs_z_le_3"]) for row in summary_rows)
    print(f"criterion=all combined |z| <= 3; pass={passed}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
