#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import os
import re
import shutil
import subprocess
from pathlib import Path
from statistics import mean, stdev

ROOT = Path(__file__).resolve().parent
CASES = ROOT / "cases"
RMC = Path("/tmp/rmc-f08-cell-ww-build/bin/RMC")
DATA = "/home/silver/NucXS_Library/RMC_DATA"
GROUP = 18
ROW_RE = re.compile(r"^\s*(\d+)\s+([+\-0-9.Ee]+)\s+([+\-0-9.Ee]+)\s+([+\-0-9.Ee]+)\s*$")
TOTAL_RE = re.compile(r"^\s*Tot\s+([+\-0-9.Ee]+)\s+([+\-0-9.Ee]+)\s*$")

BASE = """UNIVERSE 0
CELL 1 -1 MAT=1
CELL 2 1&-2 MAT=1
CELL 3 2&-3 MAT=0 VOID=0
CELL 4 3 MAT=0 VOID=1

SURFACE
SURF 1 SO 20.0
SURF 2 SO 30.0
SURF 3 SO 50.0

MATERIAL
MAT 1 -1.0
    1001.50m 2.0
    8016.50m 1.0
MGACE ERGGRP=30 12

FIXEDSOURCE
PARTICLE POPULATION={population}
RNG TYPE=2 SEED={seed} STRIDE=1000000
ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=30 30

EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=1 POINT=0 0 45 WEIGHT=1 ENERGY=0.6

TALLY
MESHTALLY 1 TYPE=1 PARTICLE=1 ENERGY=-1 NORMALIZE={normalize} SCOPE=1 1 2 BOUND=-20 20 -20 20 0 50
"""

ZERO = BASE.replace(
    "SCOPE=1 1 2 BOUND=-20 20 -20 20 0 50",
    "SCOPE=1 1 1 BOUND=100 101 100 101 100 101",
)


def parse_tally(path: Path) -> tuple[float, float, float, float]:
    rows = []
    totals = []
    for line in path.read_text(errors="replace").splitlines():
        row = ROW_RE.match(line)
        if row and int(row.group(1)) == GROUP:
            rows.append(tuple(float(x) for x in row.groups()[1:]))
        total = TOTAL_RE.match(line)
        if total:
            totals.append(tuple(float(x) for x in total.groups()))
    if not rows:
        raise RuntimeError(f"group {GROUP} missing in {path}")
    _, mean_value, re_value = rows[0]
    total_value, total_re = totals[0] if totals else (math.nan, math.nan)
    return mean_value, re_value, abs(mean_value) * re_value, total_re


def run_case(name: str, population: int, seed: int, normalize: int, template: str = BASE) -> dict:
    directory = CASES / name
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    (directory / "inp").write_text(template.format(population=population, seed=seed, normalize=normalize))
    env = os.environ.copy()
    env["RMC_DATA_PATH"] = DATA
    completed = subprocess.run([str(RMC), "inp"], cwd=directory, env=env, text=True,
                               capture_output=True, check=False)
    (directory / "stdout.log").write_text(completed.stdout)
    (directory / "stderr.log").write_text(completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError(f"{name}: exit {completed.returncode}\n{completed.stdout}\n{completed.stderr}")
    value, re_value, sigma, total_re = parse_tally(directory / "inp.Tally")
    return {"name": name, "population": population, "seed": seed, "normalize": normalize,
            "value": value, "re": re_value, "sigma": sigma, "total_re": total_re}


def write_rows(name: str, rows: list[dict]) -> None:
    if not rows:
        return
    with (ROOT / f"{name}.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


scaling = [run_case(f"scaling_N{n}_seed{s}", n, s, 1)
           for n in (50000, 200000, 800000) for s in (11, 13, 17)]
write_rows("runtime_scaling", scaling)
scaling_summary = []
for n in (50000, 200000, 800000):
    values = [r for r in scaling if r["population"] == n]
    scaling_summary.append({"population": n, "mean_re": mean(r["re"] for r in values),
                            "sd_re": stdev(r["re"] for r in values),
                            "mean_sigma": mean(r["sigma"] for r in values)})
write_rows("runtime_scaling_summary", scaling_summary)

empirical = [run_case(f"empirical_seed{s}", 200000, s, 1) for s in (101, 103, 107, 109, 113, 127, 131, 137, 139, 149)]
write_rows("runtime_empirical", empirical)
empirical_mean = mean(r["value"] for r in empirical)
empirical_sd = stdev(r["value"] for r in empirical)
typical_sigma = math.sqrt(mean(r["sigma"] ** 2 for r in empirical))
(ROOT / "runtime_empirical_summary.txt").write_text(
    f"M={len(empirical)}\nmean={empirical_mean:.12E}\nempirical_sd={empirical_sd:.12E}\n"
    f"rms_reported_sigma={typical_sigma:.12E}\nratio={empirical_sd / typical_sigma:.12E}\n"
)

raw = run_case("normalize_raw", 200000, 31, 0)
norm = run_case("normalize_norm", 200000, 31, 1)
write_rows("runtime_normalize", [raw, norm])

zero = run_case("zero_score", 200000, 41, 1, ZERO)
write_rows("runtime_zero_score", [zero])

print("scaling", scaling_summary)
print("empirical", {"mean": empirical_mean, "sd": empirical_sd, "rms_sigma": typical_sigma,
                     "ratio": empirical_sd / typical_sigma})
print("normalize", raw, norm, "raw_over_norm", raw["value"] / norm["value"] if norm["value"] else math.nan,
      "re_difference", raw["re"] - norm["re"])
print("zero", zero)
