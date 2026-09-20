#!/usr/bin/env python3
"""Check that a fixed-source neutron WW split bank restores adjoint state."""

from __future__ import annotations

import subprocess
from pathlib import Path

RMC_ROOT = Path("/home/workspace/AI_MC_WW_interation/RMC")
BUILD = Path("/tmp/rmc-f08-cell-ww-build")
SOURCE = RMC_ROOT / "src" / "SampleNeutronSource.cpp"
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
PARTICLE POPULATION=1000
RNG TYPE=2 SEED=127 STRIDE=1000000
ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=16 16

EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=1 CELL=1 WEIGHT=1 ENERGY=0.2435

WEIGHTWINDOW
WWMESH:N 0.1
WWP:N 5 3 5
WEIGHTWINDOWMESH ScopeX=1 BoundX=-5 5 ScopeY=1 BoundY=-5 5 ScopeZ=1 BoundZ=-5 5

TALLY
CELLTALLY 1 TYPE=1 ESTIMATOR=1 PARTICLE=1 CELL=1 ENERGY=-1
"""


def main() -> int:
    if not BUILD.is_dir() or not SOURCE.is_file():
        raise RuntimeError("expected F04 RMC build or source unavailable")
    source = SOURCE.read_text(encoding="utf-8")
    old = """    cParticleState.p_eParticleType = particleType;
    cParticleState.p_dErg = particleStackTop.p_dErg;
    cParticleState.p_dWgt = particleStackTop.p_dWgt;
"""
    new = """    cParticleState.p_eParticleType = particleType;
    cParticleState.p_bIsAdjointParticle = false;
    cParticleState.p_dErg = particleStackTop.p_dErg;
    cParticleState.p_dWgt = particleStackTop.p_dWgt;
"""
    if source.count(old) != 1:
        raise RuntimeError("expected PopParticleOutofStack context not found uniquely")
    SOURCE.write_text(source.replace(old, new), encoding="utf-8")
    try:
        build = subprocess.run(
            ["cmake", "--build", str(BUILD), "--target", "RMC", "--parallel", "4"],
            cwd=RMC_ROOT, text=True, capture_output=True, check=False,
        )
        if build.returncode:
            raise RuntimeError(build.stdout + build.stderr)
        run_dir = Path(__file__).resolve().parent / "state_probe_run"
        run_dir.mkdir(exist_ok=True)
        (run_dir / "inp").write_text(INPUT, encoding="utf-8")
        run = subprocess.run(
            [str(BUILD / "bin" / "RMC"), "inp"], cwd=run_dir, text=True, capture_output=True,
            env={"RMC_DATA_PATH": "/home/silver/NucXS_Library/RMC_DATA"}, check=False,
        )
        (run_dir / "stdout.log").write_text(run.stdout, encoding="utf-8")
        (run_dir / "stderr.log").write_text(run.stderr, encoding="utf-8")
        print(f"mutated_exit={run.returncode}")
        print((run.stdout + run.stderr)[-4000:])
        return 0 if run.returncode != 0 else 1
    finally:
        SOURCE.write_text(source, encoding="utf-8")
        restore = subprocess.run(
            ["cmake", "--build", str(BUILD), "--target", "RMC", "--parallel", "4"],
            cwd=RMC_ROOT, text=True, capture_output=True, check=False,
        )
        if restore.returncode:
            raise RuntimeError("failed to restore F04 RMC binary\n" + restore.stdout + restore.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
