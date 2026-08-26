#!/usr/bin/env python3
"""Generate two-group forward and adjoint angular pilot inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


INPUT = """UNIVERSE 0
CELL 1 -1 MAT=1 DENS={density}
CELL 2 1 MAT=0 VOID=1

SURFACE
SURF 1 SO 5.0

MATERIAL
MAT 1 1.0
    10006.93m 1.0
MGACE ERGGRP=2

FIXEDSOURCE
PARTICLE POPULATION={population}
RNG TYPE=2 SEED={seed} STRIDE=1000000
{adjoint_card}
EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=1 CELL=1 POINT=0 0 0 WEIGHT=1 ENERGY=3.0

PTRAC NEU=1 SRC=1 COL=1 SUR=1 MAX=500000 MEPH=1000 WRITE=1 CELL=1 2 GRP=1

TALLY
CELLTALLY 1 TYPE=1 ESTIMATOR=1 PARTICLE=1 CELL=1 ENERGY=-1
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--population", type=int, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--density", type=float, required=True)
    arguments = parser.parse_args()
    if arguments.population < 100:
        raise ValueError("population must be >= 100")
    if arguments.density <= 0.0:
        raise ValueError("density must be positive")
    assets = arguments.assets.resolve()
    asset_manifest = json.loads((assets / "manifest.json").read_text(encoding="ascii"))
    root = arguments.root.resolve()
    if root.exists():
        raise FileExistsError(root)
    runs = []
    for case in asset_manifest["cases"]:
        xsdir = assets / str(case["xsdir"])
        for seed in arguments.seeds:
            for mode in ("forward", "adjoint"):
                directory = root / str(case["name"]) / f"seed_{seed}" / mode
                directory.mkdir(parents=True)
                content = INPUT.format(
                    population=arguments.population,
                    seed=seed,
                    density=arguments.density,
                    adjoint_card="ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=4 4\n" if mode == "adjoint" else "",
                )
                input_path = directory / "inp"
                input_path.write_text(content, encoding="ascii")
                runs.append({
                    "case": case["name"],
                    "mode": mode,
                    "seed": seed,
                    "input": str(input_path.relative_to(root)),
                    "input_sha256": sha256(input_path),
                    "data_index": str(xsdir.parent),
                    "xsdir_sha256": sha256(xsdir),
                    "asset_table_sha256": case["table_sha256"],
                })
    manifest = {
        "purpose": "two-group remaining angular representations pilot",
        "population": arguments.population,
        "density_1e24_per_cm3": arguments.density,
        "seeds": arguments.seeds,
        "asset_manifest_sha256": sha256(assets / "manifest.json"),
        "runs": runs,
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"generated_runs={len(runs)}")
    print(f"manifest_sha256={sha256(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
