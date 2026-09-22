#!/usr/bin/env python3
"""Generate independent MG-adjoint native-WWMESH verification cases."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent / "cases"
SEEDS = (211, 223, 227, 229, 233)
POPULATION = 200_000

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
WWE:N 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 2 3 4 5 6
WWMESH:N 0.02 0.03 0.04 0.05 0.06 0.07 0.08 0.09 0.10 0.11 0.12 0.13 0.14 0.15 0.16 0.17
WWP:N 5 3 5
WEIGHTWINDOWMESH ScopeX=1 BoundX=-5 5 ScopeY=1 BoundY=-5 5 ScopeZ=1 BoundZ=-5 5

"""

for seed in SEEDS:
    for mode, weight_window in (("analog", ""), ("ww", WW_ON)):
        directory = ROOT / f"seed_{seed}" / mode
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "inp").write_text(
            INPUT.format(population=POPULATION, seed=seed, weight_window=weight_window),
            encoding="utf-8",
        )
print(f"generated {len(SEEDS) * 2} cases under {ROOT}")
