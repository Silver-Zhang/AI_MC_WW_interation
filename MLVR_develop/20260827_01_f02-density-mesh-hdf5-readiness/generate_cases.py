#!/usr/bin/env python3
"""Generate paired two-region density-mesh fixed-source cases."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


INPUT = """UNIVERSE 0
CELL 1 1&-2&3&-4&5&-6 MAT=1 DENS=-1
CELL 2 2&-7&3&-4&5&-6 MAT=1 DENS=-1
CELL 3 ( -1 : 7 : -3 : 4 : -5 : 6 ) MAT=0 VOID=1

SURFACE
SURF 1 PX -5.0
SURF 2 PX 0.0
SURF 3 PY -5.0
SURF 4 PY 5.0
SURF 5 PZ -5.0
SURF 6 PZ 5.0
SURF 7 PX 5.0

MATERIAL
MAT 1 1.0
    10006.93m 1.0
MGACE ERGGRP=2

FIXEDSOURCE
PARTICLE POPULATION={population}
RNG TYPE=2 SEED={seed} STRIDE=1000000
{adjoint}

EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=1 CELL={source_cell} WEIGHT=1 ENERGY=3.0

TALLY
CELLTALLY 1 TYPE=1 ESTIMATOR=1 PARTICLE=1 CELL={response_cell} ENERGY=-1

MESH
MESHINFO 1 TYPE=1 FILENAME=density_mesh.h5 DATASETNAME=density
"""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--population", type=int, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    root.mkdir(parents=True, exist_ok=False)
    mesh = arguments.mesh.resolve()
    records = []
    for seed in arguments.seeds:
        for mode, source_cell, response_cell, adjoint in (
            ("forward", 1, 2, ""),
            ("adjoint", 2, 1, "ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=4 4\n"),
        ):
            directory = root / f"seed_{seed}" / mode
            directory.mkdir(parents=True)
            (directory / "density_mesh.h5").symlink_to(mesh)
            input_path = directory / "inp"
            input_path.write_text(INPUT.format(population=arguments.population, seed=seed, source_cell=source_cell, response_cell=response_cell, adjoint=adjoint), encoding="ascii")
            records.append({"seed": seed, "mode": mode, "input": str(input_path.relative_to(root)), "input_sha256": digest(input_path)})
    manifest = {"population": arguments.population, "seeds": arguments.seeds, "mesh_sha256": digest(mesh), "runs": records}
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"generated_runs={len(records)}")
    print(f"manifest_sha256={digest(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
