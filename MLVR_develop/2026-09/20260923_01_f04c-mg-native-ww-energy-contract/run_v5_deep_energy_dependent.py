#!/usr/bin/env python3
"""Run the repaired energy-dependent deep-penetration adjoint WW regression."""

from __future__ import annotations

import math
import re
import shutil
import subprocess
from pathlib import Path

TASK = Path(__file__).resolve().parent
RMC = Path("/tmp/rmc-f08-cell-ww-build/bin/RMC")
DATA = "/home/silver/NucXS_Library/RMC_DATA"
SEEDS = (101, 103, 107, 109, 113)
POPULATION = 1_000_000
TOTAL = re.compile(r"^\s*Tot\s+([+\-]?\d\.\d+E[+\-]\d+)\s+([+\-]?\d\.\d+E[+\-]\d+)", re.I)
TIME = re.compile(r"Time in Fixed Source Calculation\s*=\s*([+\-0-9.Ee]+)\s+seconds")
SOURCE = re.compile(r"Source Number\s*:\s*(\d+)\.")

BASE = """UNIVERSE 0
CELL 1 1 & -2 & 21 & -22 & 23 & -24 MAT=1 IMP:N=1
CELL 2 2 & -3 & 21 & -22 & 23 & -24 MAT=1 IMP:N=1
CELL 3 3 & -4 & 21 & -22 & 23 & -24 MAT=1 IMP:N=1
CELL 4 4 & -5 & 21 & -22 & 23 & -24 MAT=1 IMP:N=1
CELL 5 5 & -6 & 21 & -22 & 23 & -24 MAT=1 IMP:N=1
CELL 6 6 & -7 & 21 & -22 & 23 & -24 MAT=1 IMP:N=1
CELL 7 7 & -8 & 21 & -22 & 23 & -24 MAT=1 IMP:N=1
CELL 8 8 & -9 & 21 & -22 & 23 & -24 MAT=1 IMP:N=1
CELL 9 9 & -10 & 21 & -22 & 23 & -24 MAT=1 IMP:N=1
CELL 10 10 & -11 & 21 & -22 & 23 & -24 MAT=1 IMP:N=1
CELL 21 -1 : -21 : 22 : -23 : 24 MAT=0 VOID=1 IMP:N=0
CELL 22 11 : -21 : 22 : -23 : 24 MAT=0 VOID=1 IMP:N=0

SURFACE
SURF 1 PX 0
SURF 2 PX 10
SURF 3 PX 20
SURF 4 PX 30
SURF 5 PX 40
SURF 6 PX 50
SURF 7 PX 60
SURF 8 PX 70
SURF 9 PX 80
SURF 10 PX 90
SURF 11 PX 100
SURF 21 PY -50
SURF 22 PY 50
SURF 23 PZ -50
SURF 24 PZ 50

MATERIAL
MAT 1 -1.0
    1001.50M 2.0
    8016.50M 1.0
MGACE ERGGRP=30 12

FIXEDSOURCE
PARTICLE POPULATION={population}
ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=30 30
RNG TYPE=2 SEED={seed} STRIDE=100000

EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=1 POINT=97.5 0 0 WEIGHT=1 ENERGY=2

{ww}TALLY
CELLTALLY 1 TYPE=1 PARTICLE=1 CELL=1 ENERGY=-1
"""

# Physical WWE boundary 1 MeV. Every mesh has a distinct low/high bin bound.
SPATIAL = (0.0009765625, 0.001953125, 0.00390625, 0.0078125, 0.015625,
           0.03125, 0.0625, 0.125, 0.25, 0.5)
WW = """WEIGHTWINDOW
WWE:N 1
WWMESH:N {bounds}
WWP:N 5 3 5
WEIGHTWINDOWMESH SCOPEX=10 BOUNDX=0 100 SCOPEY=1 BOUNDY=-50 50 SCOPEZ=1 BOUNDZ=-50 50

"""


def parse(path: Path) -> tuple[float, float, float]:
    tally = path / "inp.Tally"
    for line in tally.read_text().splitlines():
        hit = TOTAL.match(line)
        if hit:
            value, re_ = map(float, hit.groups())
            break
    else:
        raise RuntimeError(f"total tally missing: {tally}")
    stdout = (path / "stdout.log").read_text()
    sources = SOURCE.findall(stdout)
    time = TIME.findall(stdout)
    if sources != [str(POPULATION)] or len(time) != 1:
        raise RuntimeError(f"bad output {path}: sources={sources}, times={time}")
    return value, value * re_, float(time[0])


runs = TASK / "runs_v5"
if runs.exists():
    shutil.rmtree(runs)
records = []
for seed in SEEDS:
    for mode in ("analog", "ww"):
        directory = runs / f"{mode}_seed{seed}"
        directory.mkdir(parents=True)
        bounds = " ".join(f"{low * 0.5:.10g} {low:.10g}" for low in SPATIAL)
        ww = "" if mode == "analog" else WW.format(bounds=bounds)
        (directory / "inp").write_text(BASE.format(population=POPULATION, seed=seed, ww=ww))
        result = subprocess.run([str(RMC), "inp"], cwd=directory, text=True, capture_output=True,
                                env={"RMC_DATA_PATH": DATA}, check=False)
        (directory / "stdout.log").write_text(result.stdout)
        (directory / "stderr.log").write_text(result.stderr)
        if result.returncode:
            raise RuntimeError(f"{directory}: exit {result.returncode}\n{result.stdout}\n{result.stderr}")
        value, sigma, seconds = parse(directory)
        records.append({"seed": seed, "mode": mode, "value": value, "sigma": sigma, "seconds": seconds})


def combine(mode: str) -> dict[str, float]:
    rows = [row for row in records if row["mode"] == mode]
    value = sum(row["value"] for row in rows) / len(rows)
    sigma = math.sqrt(sum(row["sigma"] ** 2 for row in rows)) / len(rows)
    re_ = sigma / value
    seconds = sum(row["seconds"] for row in rows) / len(rows)
    return {"value": value, "sigma": sigma, "re": re_, "seconds": seconds,
            "fom": 1.0 / (re_ ** 2 * seconds)}

analog, ww = combine("analog"), combine("ww")
z = (ww["value"] - analog["value"]) / math.hypot(ww["sigma"], analog["sigma"])
summary = {"records": records, "analog": analog, "ww": ww, "z": z,
           "fom_ratio": ww["fom"] / analog["fom"], "pass": abs(z) < 3.0}
(TASK / "v5_results.json").write_text(__import__("json").dumps(summary, indent=2) + "\n")
print(__import__("json").dumps(summary, indent=2))
raise SystemExit(0 if summary["pass"] else 1)
