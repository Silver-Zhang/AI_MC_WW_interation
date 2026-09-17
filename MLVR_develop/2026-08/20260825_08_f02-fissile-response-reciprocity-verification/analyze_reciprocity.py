#!/usr/bin/env python3
"""Evaluate fissile forward-adjoint response reciprocity with independent streams."""

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
    r"^\s*(?:(?P<cell>\d+)\s+)?(?P<group>\d+)\s+(?P<energy>[+\-0-9.Ee]+)\s+"
    r"(?P<average>[+\-0-9.Ee]+)\s+(?P<relative_error>[+\-0-9.Ee]+)\s*$"
)
SOURCE_NUMBER = re.compile(r"Source Number\s*:\s*(?P<count>\d+)\.")
ANOMALY = re.compile(r"warning:|error:|segmentation fault|floating point exception|\bnan\b|\binf\b", re.IGNORECASE)


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


def source_number(path: Path) -> int:
    matches = SOURCE_NUMBER.findall(path.read_text(encoding="utf-8"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one Source Number in {path}, found {len(matches)}")
    return int(matches[0])


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    arguments = parser.parse_args()

    manifest_path = arguments.root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_population = int(manifest["population_per_run"])
    rows: list[dict[str, object]] = []
    anomalies: list[str] = []
    grouped: dict[int, dict[str, dict[str, object]]] = defaultdict(dict)

    for run in manifest["runs"]:
        directory = arguments.root / Path(run["input"]).parent
        exit_code = int((directory / "exit_code.txt").read_text().strip())
        observed_sources = source_number(directory / "stdout.log")
        average, relative_error, sigma = tally_value(directory / "inp.Tally", int(run["response_tally_group"]))
        finite_positive = all(math.isfinite(value) and value > 0.0 for value in (average, relative_error, sigma))
        output_row = {
            **run,
            "exit_code": exit_code,
            "source_number": observed_sources,
            "average": average,
            "relative_error": relative_error,
            "sigma": sigma,
            "finite_positive": finite_positive,
            "tally_sha256": sha256(directory / "inp.Tally"),
            "stdout_sha256": sha256(directory / "stdout.log"),
        }
        rows.append(output_row)
        grouped[int(run["pair_index"])][str(run["mode"])] = output_row

        for name in ("stdout.log", "stderr.log", "inp.out"):
            path = directory / name
            if not path.exists():
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if ANOMALY.search(line) and "information" not in line.lower():
                    anomalies.append(f"{path.relative_to(arguments.root)}:{number}:{line}")

    pair_rows: list[dict[str, object]] = []
    for pair_index, modes in sorted(grouped.items()):
        if set(modes) != {"forward", "adjoint"}:
            raise RuntimeError(f"incomplete pair {pair_index}: {sorted(modes)}")
        forward = modes["forward"]
        adjoint = modes["adjoint"]
        denominator = math.hypot(float(forward["sigma"]), float(adjoint["sigma"]))
        z_score = (float(forward["average"]) - float(adjoint["average"])) / denominator
        pair_rows.append(
            {
                "pair_index": pair_index,
                "forward_seed": forward["seed"],
                "adjoint_seed": adjoint["seed"],
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

    inverse_variance_forward = [1.0 / float(row["sigma_F"]) ** 2 for row in pair_rows]
    inverse_variance_adjoint = [1.0 / float(row["sigma_A"]) ** 2 for row in pair_rows]
    combined_forward = sum(float(row["R_F"]) * weight for row, weight in zip(pair_rows, inverse_variance_forward)) / sum(inverse_variance_forward)
    combined_adjoint = sum(float(row["R_A"]) * weight for row, weight in zip(pair_rows, inverse_variance_adjoint)) / sum(inverse_variance_adjoint)
    combined_sigma_forward = 1.0 / math.sqrt(sum(inverse_variance_forward))
    combined_sigma_adjoint = 1.0 / math.sqrt(sum(inverse_variance_adjoint))
    combined_z = (combined_forward - combined_adjoint) / math.hypot(combined_sigma_forward, combined_sigma_adjoint)

    execution_pass = all(
        int(row["exit_code"]) == 0
        and int(row["source_number"]) == expected_population
        and bool(row["finite_positive"])
        for row in rows
    )
    formal_statistics_pass = all(bool(row["pass_abs_z_le_3"]) for row in pair_rows) and abs(combined_z) <= 3.0
    stage = str(manifest["stage"])
    passed = execution_pass and not anomalies and (stage == "pilot" or formal_statistics_pass)
    summary_rows = [
        {
            "stage": stage,
            "run_count": len(rows),
            "independent_pair_count": len(pair_rows),
            "population_per_run": expected_population,
            "R_F": combined_forward,
            "sigma_F": combined_sigma_forward,
            "R_A": combined_adjoint,
            "sigma_A": combined_sigma_adjoint,
            "z": combined_z,
            "all_individual_abs_z_le_3": all(bool(row["pass_abs_z_le_3"]) for row in pair_rows),
            "max_individual_abs_z": max(abs(float(row["z"])) for row in pair_rows),
            "anomaly_lines": len(anomalies),
            "execution_pass": execution_pass,
            "formal_statistics_pass": formal_statistics_pass,
            "criterion_pass": passed,
        }
    ]

    arguments.results.mkdir(parents=True, exist_ok=True)
    write_csv(arguments.results / "runs.csv", rows)
    write_csv(arguments.results / "pairs.csv", pair_rows)
    write_csv(arguments.results / "summary.csv", summary_rows)
    (arguments.results / "anomalies.txt").write_text("\n".join(anomalies) + ("\n" if anomalies else ""), encoding="utf-8")

    print(f"stage={stage} manifest_sha256={sha256(manifest_path)}")
    print(f"run_count={len(rows)} paired_stream_count={len(pair_rows)} anomaly_lines={len(anomalies)}")
    print("per-pair:")
    for row in pair_rows:
        print(",".join(f"{key}={value}" for key, value in row.items()))
    print("combined:")
    print(",".join(f"{key}={value}" for key, value in summary_rows[0].items()))
    print(f"criterion={'execution/finite/clean for pilot; plus all individual and combined |z| <= 3 for formal'}; pass={passed}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())