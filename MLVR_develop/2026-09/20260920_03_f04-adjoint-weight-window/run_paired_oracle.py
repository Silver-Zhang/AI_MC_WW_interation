#!/usr/bin/env python3
"""Generate and evaluate paired native-WWMESH adjoint cases."""

from __future__ import annotations

import csv
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

SEEDS = (101, 103, 107, 109, 113)
POPULATION = 200_000
RESPONSE_GROUP = 16
DATA_PATH = Path("/home/silver/NucXS_Library/RMC_DATA")
RMC = Path("/tmp/rmc-f08-cell-ww-build/bin/RMC")
TALLY = re.compile(
    r"^\s*(?:(?P<cell>\d+)\s+)?(?P<group>\d+)\s+(?P<energy>[+\-0-9.Ee]+)\s+"
    r"(?P<average>[+\-0-9.Ee]+)\s+(?P<relative_error>[+\-0-9.Ee]+)\s*$"
)
SOURCE_COUNT = re.compile(r"Source Number\s*:\s*(?P<count>\d+)\.")
ANOMALY = re.compile(r"warning:|error:|segmentation fault|floating point exception|\bnan\b|\binf\b", re.I)

INPUT = """UNIVERSE 0
CELL 1 -1 MAT=1 DENS=0.1004476876
CELL 2 1 MAT=0 VOID=1

SURFACE
SURF 1 SO 5.0

MATERIAL
MAT 1 0.1004476876
    1001.50m 2.0
    8016.50m 1.0
MGACE ERGGRP=30 12

FIXEDSOURCE
PARTICLE POPULATION={population}
RNG TYPE=2 SEED={seed} STRIDE=1000000
ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=16 16

EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=1 CELL=1 WEIGHT=1 ENERGY=0.2435

{weight_window}TALLY
CELLTALLY 1 TYPE=1 ESTIMATOR=1 PARTICLE=1 CELL=1 ENERGY=-1
"""

WW_ON = """WEIGHTWINDOW
WWMESH:N 0.1
WWP:N 5 3 5
WEIGHTWINDOWMESH ScopeX=1 BoundX=-5 5 ScopeY=1 BoundY=-5 5 ScopeZ=1 BoundZ=-5 5

"""


def read_group(path: Path, group: int) -> tuple[float, float]:
    for line in path.read_text(encoding="utf-8").splitlines():
        match = TALLY.match(line)
        if match and int(match.group("group")) == group:
            value = float(match.group("average"))
            sigma = value * float(match.group("relative_error"))
            return value, sigma
    raise RuntimeError(f"group {group} missing from {path}")


def run_case(directory: Path, content: str) -> dict[str, object]:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "inp").write_text(content, encoding="utf-8")
    completed = subprocess.run(
        [str(RMC), "inp"], cwd=directory, text=True, capture_output=True, check=False,
        env={"RMC_DATA_PATH": str(DATA_PATH)},
    )
    (directory / "stdout.log").write_text(completed.stdout, encoding="utf-8")
    (directory / "stderr.log").write_text(completed.stderr, encoding="utf-8")
    text = completed.stdout + completed.stderr
    sources = SOURCE_COUNT.findall(text)
    if completed.returncode or len(sources) != 1 or int(sources[0]) != POPULATION:
        raise RuntimeError(f"run failed in {directory}: exit={completed.returncode}, sources={sources}")
    anomalies = [line for line in text.splitlines() if ANOMALY.search(line)]
    if anomalies:
        raise RuntimeError(f"anomaly in {directory}: {anomalies[0]}")
    value, sigma = read_group(directory / "inp.Tally", RESPONSE_GROUP)
    if not all(math.isfinite(number) and number > 0.0 for number in (value, sigma)):
        raise RuntimeError(f"non-positive response or uncertainty in {directory}: value={value}, sigma={sigma}")
    return {"value": value, "sigma": sigma}


def main() -> int:
    if not RMC.is_file() or not DATA_PATH.is_dir():
        raise RuntimeError("RMC executable or RMC_DATA_PATH unavailable")
    root = Path(__file__).resolve().parent / "runs"
    if root.exists():
        shutil.rmtree(root)
    records: list[dict[str, object]] = []
    for seed in SEEDS:
        analogue = run_case(root / f"seed_{seed}" / "ww_off", INPUT.format(
            population=POPULATION, seed=seed, weight_window=""
        ))
        weighted = run_case(root / f"seed_{seed}" / "ww_on", INPUT.format(
            population=POPULATION, seed=seed, weight_window=WW_ON
        ))
        denominator = math.hypot(float(analogue["sigma"]), float(weighted["sigma"]))
        records.append({
            "seed": seed,
            "adjoint_ww_off": analogue["value"],
            "sigma_off": analogue["sigma"],
            "adjoint_ww_on": weighted["value"],
            "sigma_on": weighted["sigma"],
            "z": (float(weighted["value"]) - float(analogue["value"])) / denominator,
        })
    inv_off = [1.0 / float(row["sigma_off"]) ** 2 for row in records]
    inv_on = [1.0 / float(row["sigma_on"]) ** 2 for row in records]
    mean_off = sum(float(row["adjoint_ww_off"]) * weight for row, weight in zip(records, inv_off)) / sum(inv_off)
    mean_on = sum(float(row["adjoint_ww_on"]) * weight for row, weight in zip(records, inv_on)) / sum(inv_on)
    sigma_off = 1.0 / math.sqrt(sum(inv_off))
    sigma_on = 1.0 / math.sqrt(sum(inv_on))
    combined_z = (mean_on - mean_off) / math.hypot(sigma_off, sigma_on)
    result = {
        "population_per_run": POPULATION,
        "seeds": SEEDS,
        "response_group": RESPONSE_GROUP,
        "per_seed": records,
        "combined": {
            "ww_off": mean_off,
            "sigma_off": sigma_off,
            "ww_on": mean_on,
            "sigma_on": sigma_on,
            "z": combined_z,
            "pass": abs(combined_z) <= 3.0 and all(abs(float(row["z"])) <= 3.0 for row in records),
        },
    }
    with (root.parent / "results.json").open("w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    with (root.parent / "results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps(result, indent=2))
    return 0 if result["combined"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
