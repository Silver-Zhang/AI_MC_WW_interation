#!/usr/bin/env python3
"""Evaluate paired nonuniform-density forward/adjoint responses."""

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
KNOWN_WARNING = "particle energy larger than maximum energy group upper bound"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tally_value(path: Path, tally_group: int) -> tuple[float, float, float]:
    for line in path.read_text(encoding="utf-8").splitlines():
        match = TALLY_ROW.match(line)
        if match and int(match.group("group")) == tally_group:
            average = float(match.group("average"))
            relative_error = float(match.group("relative_error"))
            if not math.isfinite(average) or not math.isfinite(relative_error) or average <= 0.0:
                raise RuntimeError(f"invalid tally in {path}: average={average}, RE={relative_error}")
            return average, relative_error, average * relative_error
    raise RuntimeError(f"tally group {tally_group} not found in {path}")


def weighted_mean(values: list[tuple[float, float]]) -> tuple[float, float]:
    weights = [1.0 / sigma**2 for _, sigma in values]
    mean = sum(value * weight for (value, _), weight in zip(values, weights)) / sum(weights)
    return mean, 1.0 / math.sqrt(sum(weights))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--require-seeds", type=int)
    arguments = parser.parse_args()

    root = arguments.root.resolve()
    output_dir = arguments.output_dir.resolve()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    expected_run_count = len(manifest["density_cases"]) * len(manifest["pairs"]) * len(manifest["seeds"]) * 2
    if len(manifest["runs"]) != expected_run_count:
        raise RuntimeError(f"manifest has {len(manifest['runs'])} runs, expected {expected_run_count}")
    if arguments.require_seeds is not None and len(manifest["seeds"]) != arguments.require_seeds:
        raise RuntimeError(f"manifest has {len(manifest['seeds'])} seeds, expected {arguments.require_seeds}")
    if float(manifest["geometry"]["relative_volume_difference"]) > 1.0e-14:
        raise RuntimeError("inner and outer response volumes are not equal within tolerance")

    rows: list[dict[str, object]] = []
    anomalies: list[str] = []
    explained_warnings: list[str] = []
    grouped: dict[tuple[str, str, int], dict[str, dict[str, object]]] = defaultdict(dict)
    for run in manifest["runs"]:
        directory = (root / run["input"]).parent
        exit_code = int((directory / "exit_code.txt").read_text(encoding="ascii").strip())
        if exit_code != 0:
            raise RuntimeError(f"nonzero exit code {exit_code}: {directory.relative_to(root)}")
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
        grouped[(str(run["density_case"]), str(run["pair"]), int(run["seed"]))][str(run["mode"])] = output_row

        for name in ("stdout.log", "stderr.log", "inp.out"):
            path = directory / name
            if not path.exists():
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if not ANOMALY.search(line) or "information" in line.lower():
                    continue
                record = f"{path.relative_to(root)}:{number}:{line}"
                if KNOWN_WARNING in line.lower():
                    explained_warnings.append(record)
                else:
                    anomalies.append(record)

    pair_rows: list[dict[str, object]] = []
    for (density_case, pair, seed), modes in sorted(grouped.items()):
        if set(modes) != {"forward", "adjoint"}:
            raise RuntimeError(f"incomplete pair {density_case}/{pair}/seed_{seed}: {sorted(modes)}")
        forward = modes["forward"]
        adjoint = modes["adjoint"]
        delta = float(forward["average"]) - float(adjoint["average"])
        sigma_delta = math.hypot(float(forward["sigma"]), float(adjoint["sigma"]))
        z_score = delta / sigma_delta
        pair_rows.append(
            {
                "density_case": density_case,
                "pair": pair,
                "seed": seed,
                "R_F": forward["average"],
                "sigma_F": forward["sigma"],
                "RE_F": forward["relative_error"],
                "R_A": adjoint["average"],
                "sigma_A": adjoint["sigma"],
                "RE_A": adjoint["relative_error"],
                "delta": delta,
                "sigma_delta": sigma_delta,
                "z": z_score,
                "pass_abs_z_le_3": abs(z_score) <= 3.0,
            }
        )

    summary_rows: list[dict[str, object]] = []
    summary_keys = sorted({(str(row["density_case"]), str(row["pair"])) for row in pair_rows})
    for density_case, pair in summary_keys:
        selected = [
            row for row in pair_rows if row["density_case"] == density_case and row["pair"] == pair
        ]
        combined_forward, combined_sigma_forward = weighted_mean(
            [(float(row["R_F"]), float(row["sigma_F"])) for row in selected]
        )
        combined_adjoint, combined_sigma_adjoint = weighted_mean(
            [(float(row["R_A"]), float(row["sigma_A"])) for row in selected]
        )
        delta = combined_forward - combined_adjoint
        sigma_delta = math.hypot(combined_sigma_forward, combined_sigma_adjoint)
        combined_z = delta / sigma_delta
        summary_rows.append(
            {
                "density_case": density_case,
                "pair": pair,
                "independent_seeds": len(selected),
                "R_F": combined_forward,
                "sigma_F": combined_sigma_forward,
                "R_A": combined_adjoint,
                "sigma_A": combined_sigma_adjoint,
                "delta": delta,
                "sigma_delta": sigma_delta,
                "z": combined_z,
                "pass_abs_z_le_3": abs(combined_z) <= 3.0,
                "all_individual_abs_z_le_3": all(bool(row["pass_abs_z_le_3"]) for row in selected),
                "max_individual_abs_z": max(abs(float(row["z"])) for row in selected),
            }
        )

    overall_delta, overall_sigma = weighted_mean(
        [(float(row["delta"]), float(row["sigma_delta"])) for row in summary_rows]
    )
    overall_z = overall_delta / overall_sigma
    overall_row: dict[str, object] = {
        "independent_configurations": len(summary_rows),
        "delta": overall_delta,
        "sigma_delta": overall_sigma,
        "z": overall_z,
        "pass_abs_z_le_3": abs(overall_z) <= 3.0,
    }

    write_csv(output_dir / "runs.csv", rows)
    write_csv(output_dir / "paired_seeds.csv", pair_rows)
    write_csv(output_dir / "summary.csv", summary_rows)
    write_csv(output_dir / "overall.csv", [overall_row])
    (output_dir / "anomalies.log").write_text("\n".join(anomalies) + ("\n" if anomalies else ""), encoding="utf-8")
    (output_dir / "explained_warnings.log").write_text(
        "\n".join(explained_warnings) + ("\n" if explained_warnings else ""), encoding="utf-8"
    )

    print(f"manifest_sha256={sha256(manifest_path)}")
    print(f"run_count={len(rows)} paired_seed_count={len(pair_rows)}")
    print(f"anomaly_lines={len(anomalies)} explained_warning_lines={len(explained_warnings)}")
    print("per-seed:")
    for row in pair_rows:
        print(",".join(f"{key}={value}" for key, value in row.items()))
    print("combined:")
    for row in summary_rows:
        print(",".join(f"{key}={value}" for key, value in row.items()))
    print("overall:")
    print(",".join(f"{key}={value}" for key, value in overall_row.items()))
    passed = (
        not anomalies
        and all(bool(row["pass_abs_z_le_3"]) for row in pair_rows)
        and all(bool(row["pass_abs_z_le_3"]) for row in summary_rows)
        and bool(overall_row["pass_abs_z_le_3"])
    )
    print(f"criterion=no unexplained anomalies and all individual/combined/overall |z| <= 3; pass={passed}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())