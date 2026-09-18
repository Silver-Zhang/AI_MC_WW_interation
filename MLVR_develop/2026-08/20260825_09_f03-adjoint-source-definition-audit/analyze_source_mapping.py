#!/usr/bin/env python3
"""Validate F03 source support, MG group mapping, weighted moments and tallies."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path

STATE_RE = re.compile(r"C\s*=\s*(?P<collision>\d+),.*?r\s*=\s*\((?P<x>[^ ]+) (?P<y>[^ ]+) (?P<z>[^)]+)\),\s*erg\s*=\s*(?P<group>\d+),\s*w\s*=\s*(?P<weight>[+\-0-9.Ee]+)")
TALLY_RE = re.compile(r"^\s*(?P<group>\d+)\s+(?P<energy>[+\-0-9.Ee]+)\s+(?P<average>[+\-0-9.Ee]+)\s+(?P<re>[+\-0-9.Ee]+)\s*$")
ANOMALY_RE = re.compile(r"warning:|error:|\bnan\b|\binf\b", re.IGNORECASE)
KNOWN_WARNING = "particle energy larger than maximum energy group upper bound"
POSITION_TOLERANCE_CM = 1.0e-3


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_tally(path: Path, cell: int, group: int) -> tuple[float, float]:
    current_cell = None
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) >= 5 and fields[0].isdigit() and fields[1].isdigit():
            current_cell = int(fields[0])
            candidate_group = int(fields[1])
            candidate_average = float(fields[3])
            candidate_re = float(fields[4])
        else:
            match = TALLY_RE.match(line)
            if not match or current_cell is None:
                continue
            candidate_group = int(match["group"])
            candidate_average = float(match["average"])
            candidate_re = float(match["re"])
        if current_cell == cell and candidate_group == group:
            value = candidate_average
            relative_error = candidate_re
            if not math.isfinite(value) or value <= 0 or not math.isfinite(relative_error):
                raise RuntimeError(f"invalid tally {path}: {line}")
            return value, value * relative_error
    raise RuntimeError(f"missing tally group {group}: {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    output = arguments.output_dir.resolve()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    rows = []
    anomalies = []
    grouped = defaultdict(dict)
    for run in manifest["runs"]:
        directory = root / Path(run["input"]).parent
        exit_code = int((directory / "exit_code.txt").read_text(encoding="ascii").strip())
        if exit_code != 0:
            raise RuntimeError(f"nonzero exit code: {directory}")
        trace = directory / "inp.source"
        if not trace.exists():
            raise RuntimeError(f"missing source trace: {trace}")
        states = []
        for line in trace.read_text(encoding="utf-8").splitlines():
            match = STATE_RE.search(line)
            if match and int(match["collision"]) == 0:
                states.append({"x": float(match["x"]), "y": float(match["y"]), "z": float(match["z"]), "group": int(match["group"]), "weight": float(match["weight"])})
        if not states:
            raise RuntimeError(f"no C=0 source trace records: {trace}")
        expected_sources = (
            {14: 1}
            if run["mode"] == "forward"
            else {int(item["group"]): int(item["cell"]) for item in manifest["response_components"]}
        )
        outer_radius = float(manifest["geometry"]["outer_radius_cm"])
        middle_radius = float(manifest["geometry"]["middle_radius_cm"])
        inner_radius = float(manifest["geometry"]["inner_radius_cm"])
        invalid_states = []
        for state in states:
            radius = math.sqrt(state["x"] ** 2 + state["y"] ** 2 + state["z"] ** 2)
            expected_cell = expected_sources.get(state["group"])
            in_expected_cell = (
                expected_cell == 1 and radius <= inner_radius + POSITION_TOLERANCE_CM
            ) or (
                expected_cell == 2
                and inner_radius - POSITION_TOLERANCE_CM <= radius <= middle_radius + POSITION_TOLERANCE_CM
            ) or (
                expected_cell == 3
                and middle_radius - POSITION_TOLERANCE_CM <= radius <= outer_radius + POSITION_TOLERANCE_CM
            )
            if in_expected_cell and state["weight"] > 0 and math.isfinite(state["weight"]):
                continue
            invalid_states.append(state)
        if invalid_states:
            raise RuntimeError(f"source support/group/weight violation: {trace}")
        source_moment_checks = []
        if run["mode"] == "adjoint":
            expected_components = manifest["response_components"]
        else:
            expected_components = ({"name": "forward_source", "cell": 1, "group": 14, "strength_H": 1.0},)
        for component in expected_components:
            component_states = [
                state for state in states
                if state["group"] == int(component["group"])
                and (
                    (int(component["cell"]) == 1 and state["x"] ** 2 + state["y"] ** 2 + state["z"] ** 2 <= (inner_radius + POSITION_TOLERANCE_CM) ** 2)
                    or (int(component["cell"]) == 2 and (inner_radius - POSITION_TOLERANCE_CM) ** 2 <= state["x"] ** 2 + state["y"] ** 2 + state["z"] ** 2 <= (middle_radius + POSITION_TOLERANCE_CM) ** 2)
                    or (int(component["cell"]) == 3 and (middle_radius - POSITION_TOLERANCE_CM) ** 2 <= state["x"] ** 2 + state["y"] ** 2 + state["z"] ** 2 <= (outer_radius + POSITION_TOLERANCE_CM) ** 2)
                )
            ]
            contributions = [state["weight"] for state in component_states] + [0.0] * (len(states) - len(component_states))
            expected_strength = float(component["strength_H"])
            observed = statistics.fmean(contributions)
            standard_error = statistics.stdev(contributions) / math.sqrt(len(contributions)) if len(contributions) > 1 else math.inf
            z_score = (observed - expected_strength) / standard_error if standard_error > 0 else 0.0
            source_moment_checks.append({
                "name": component["name"],
                "sample_count": len(component_states),
                "sample_fraction": len(component_states) / len(states),
                "observed_weighted_mean": observed,
                "expected_strength_H": expected_strength,
                "standard_error": standard_error,
                "z": z_score,
            })
            if abs(z_score) > 3.0:
                raise RuntimeError(f"source weighted moment z-score exceeds 3: {trace}, component={component['name']}, z={z_score}")
        tally_values = [read_tally(directory / "inp.Tally", cell, GROUP) for cell, GROUP in zip(run["response_cells"], run["response_tally_groups"])]
        row = {"case": run["case"], "seed": run["seed"], "mode": run["mode"], "source_samples": len(states), "source_groups": ";".join(map(str, sorted({state["group"] for state in states}))), "source_weight_mean": sum(state["weight"] for state in states) / len(states), "source_moments": json.dumps(source_moment_checks, separators=(",", ":")), "tally_values": ";".join(f"{value:.17g}" for value, _ in tally_values), "tally_sigmas": ";".join(f"{sigma:.17g}" for _, sigma in tally_values), "exit_code": exit_code, "tally_sha256": sha256(directory / "inp.Tally")}
        rows.append(row)
        grouped[(run["case"], run["seed"])][run["mode"]] = {**run, **row, "tallies": tally_values}
        for name in ("stdout.log", "stderr.log", "inp.out"):
            path = directory / name
            if path.exists():
                for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if ANOMALY_RE.search(line) and "information" not in line.lower() and KNOWN_WARNING not in line.lower():
                        anomalies.append(f"{path.relative_to(root)}:{number}:{line}")
    output.mkdir(parents=True, exist_ok=True)
    with (output / "source_runs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "anomalies.log").write_text("\n".join(anomalies) + ("\n" if anomalies else ""), encoding="utf-8")
    print(f"manifest_sha256={sha256(manifest_path)}")
    print(f"run_count={len(rows)} anomaly_lines={len(anomalies)}")
    print(f"criterion=all source support/group/weight/tally checks pass; pass={not anomalies}")
    return 0 if not anomalies else 1


if __name__ == "__main__":
    raise SystemExit(main())
