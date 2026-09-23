#!/usr/bin/env python3
"""Exercise physical-energy WWE bin selection in MG forward and adjoint transport."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "runs"
RMC = Path("/tmp/rmc-f08-cell-ww-build/bin/RMC")
DATA = "/home/silver/NucXS_Library/RMC_DATA"
POPULATION = 100_000
COLLISIONS = re.compile(r"Neutron collisions per source particle:\s*([+\-0-9.Ee]+)")
SOURCES = re.compile(r"Source Number\s*:\s*(\d+)\.")

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
RNG TYPE=2 SEED=307 STRIDE=1000000
{adjoint}
EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=1 CELL=1 WEIGHT=1 ENERGY=0.2435

WEIGHTWINDOW
WWE:N {wwe_boundary}
WWMESH:N 0.1 0.4
WWP:N 5 3 5
WEIGHTWINDOWMESH ScopeX=1 BoundX=-5 5 ScopeY=1 BoundY=-5 5 ScopeZ=1 BoundZ=-5 5

TALLY
CELLTALLY 1 TYPE=1 ESTIMATOR=1 PARTICLE=1 CELL=1 ENERGY=-1
"""

CASES = (
    ("forward", "", "low", "0.2435", "0.3", "low", 0.1),
    ("forward", "", "low", "0.2435", "0.2", "high", 0.4),
    ("forward", "", "high", "0.4015", "0.3", "high", 0.4),
    ("forward", "", "high", "0.4015", "0.2", "high", 0.4),
    ("adjoint", "ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=16 16\n", "low", "0.2435", "0.3", "low", 0.1),
    ("adjoint", "ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=16 16\n", "low", "0.2435", "0.2", "high", 0.4),
    ("adjoint", "ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=16 16\n", "high", "0.4015", "0.3", "high", 0.4),
    ("adjoint", "ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=16 16\n", "high", "0.4015", "0.2", "high", 0.4),
)

if RUNS.exists():
    shutil.rmtree(RUNS)
records = []
for mode, adjoint, transport_group, source_energy, wwe_boundary, expected_bin, expected_lower in CASES:
    directory = RUNS / f"{mode}_{transport_group}_{expected_bin}_{wwe_boundary.replace('.', '_')}"
    directory.mkdir(parents=True)
    (directory / "inp").write_text(INPUT.format(
        population=POPULATION, adjoint=adjoint, wwe_boundary=wwe_boundary
    ), encoding="utf-8")
    completed = subprocess.run([str(RMC), "inp"], cwd=directory, text=True, capture_output=True,
                               env={"RMC_DATA_PATH": DATA}, check=False)
    (directory / "stdout.log").write_text(completed.stdout, encoding="utf-8")
    (directory / "stderr.log").write_text(completed.stderr, encoding="utf-8")
    collisions = COLLISIONS.findall(completed.stdout)
    sources = SOURCES.findall(completed.stdout)
    if completed.returncode != 0 or sources != [str(POPULATION)] or len(collisions) != 1:
        raise RuntimeError(f"{directory.name}: exit={completed.returncode}, sources={sources}, collisions={collisions}")
    records.append({
        "mode": mode,
        "transport_group": transport_group,
        "wwe_upper_boundary_MeV": float(wwe_boundary),
        "source_energy_MeV": float(source_energy),
        "expected_bin": expected_bin,
        "expected_lower_bound": expected_lower,
        "neutron_collisions_per_source": float(collisions[0]),
        "exit_code": completed.returncode,
    })

result = {"records": records}
for mode in ("forward", "adjoint"):
    low_group_low = next(item for item in records if item["mode"] == mode and item["transport_group"] == "low" and item["expected_bin"] == "low")
    low_group_high = next(item for item in records if item["mode"] == mode and item["transport_group"] == "low" and item["expected_bin"] == "high")
    high_group_high = next(item for item in records if item["mode"] == mode and item["transport_group"] == "high" and item["expected_bin"] == "high")
    ratio = low_group_low["neutron_collisions_per_source"] / low_group_high["neutron_collisions_per_source"]
    result[f"{mode}_same_group_bin_ratio_low_over_high"] = ratio
    result[f"{mode}_same_group_bin_selection_pass"] = ratio > 1.05
    result[f"{mode}_high_group_high_bin_collisions"] = high_group_high["neutron_collisions_per_source"]
result["pass"] = all(result[f"{mode}_same_group_bin_selection_pass"] for mode in ("forward", "adjoint"))
(ROOT / "bin_oracle_results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["pass"] else 1)
