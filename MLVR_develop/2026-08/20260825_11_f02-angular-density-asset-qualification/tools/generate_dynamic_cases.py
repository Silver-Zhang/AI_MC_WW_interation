#!/usr/bin/env python3
"""Generate standard-path RMC runs for qualified private angular MGACE assets."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


INPUT = """UNIVERSE 0
CELL 1 -1 MAT=1 TMP=300
CELL 2 1 MAT=0 VOID=1

SURFACE
SURF 1 SO 5.0

MATERIAL
MAT 1 {density:.12g}
    10006.91m 1.0
MGACE ERGGRP=1

FIXEDSOURCE
PARTICLE POPULATION={population}
RNG TYPE=2 SEED={seed} STRIDE=1000000
{adjoint_card}
EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=1 CELL=1 POINT=0 0 0 WEIGHT=1 ENERGY=1.0

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
    parser.add_argument("--case", action="append", dest="cases")
    parser.add_argument("--mode", choices=("forward", "adjoint"), action="append", dest="modes")
    parser.add_argument("--population", type=int, default=200)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--density", type=float, default=1.0)
    arguments = parser.parse_args()
    if arguments.population <= 100:
        raise ValueError("RMC fixed-source population must exceed 100")
    if arguments.density <= 0.0:
        raise ValueError("material atom density must be positive")

    assets = arguments.assets.resolve()
    source_manifest_path = assets / "manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="ascii"))
    available = {str(case["name"]): case for case in source_manifest["cases"]}
    selected_cases = arguments.cases or list(available)
    selected_modes = arguments.modes or ["forward", "adjoint"]
    unknown = set(selected_cases) - set(available)
    if unknown:
        raise ValueError(f"unknown cases: {sorted(unknown)}")

    root = arguments.root.resolve()
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        raise FileExistsError(f"refusing to overwrite {manifest_path}")
    runs: list[dict[str, object]] = []
    for case_name in selected_cases:
        asset_case = available[case_name]
        data_index = (assets / str(asset_case["xsdir"])).parent
        for mode in selected_modes:
            run_directory = root / case_name / mode
            run_directory.mkdir(parents=True)
            adjoint_card = "ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=2 2\n" if mode == "adjoint" else ""
            content = INPUT.format(
                population=arguments.population,
                seed=arguments.seed,
                density=arguments.density,
                adjoint_card=adjoint_card,
            )
            input_path = run_directory / "inp"
            input_path.write_text(content, encoding="ascii")
            runs.append(
                {
                    "case": case_name,
                    "mode": mode,
                    "seed": arguments.seed,
                    "population": arguments.population,
                    "atom_density_1e24_per_cm3": arguments.density,
                    "input": str(input_path.relative_to(root)),
                    "input_sha256": sha256(input_path),
                    "data_index": str(data_index),
                    "xsdir_sha256": sha256(data_index / "xsdir"),
                    "table_sha256": asset_case["table_sha256"],
                }
            )

    manifest = {
        "source_manifest": str(source_manifest_path),
        "source_manifest_sha256": sha256(source_manifest_path),
        "geometry": "5 cm sphere, pure one-group self scattering, isotropic point source at origin",
        "atom_density_1e24_per_cm3": arguments.density,
        "observation": "PTRAC collision and surface-crossing direction vectors",
        "runs": runs,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"generated_runs={len(runs)}")
    print(f"manifest={manifest_path}")
    print(f"manifest_sha256={sha256(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())