#!/usr/bin/env python3
"""Generate the frozen V2 local-density inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


BASE_DENSITY = 0.1004476876
CASES = (("r0.5", 0.5), ("r1", 1.0), ("r2", 2.0))

INPUT = """UNIVERSE 0
CELL 1 -1  MAT=1 DENS={cell_density:.10f}
CELL 2 1 MAT=0 VOID=1

SURFACE
SURF 1 SO 50.0

MATERIAL
MAT 1 {base_density:.10f}
    1001.50m 2.0
    8016.50m 1.0
MGACE ERGGRP=30 12

FIXEDSOURCE
PARTICLE POPULATION=128
ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=16 16
RNG TYPE=2 SEED=1 STRIDE=1000000

EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=1 POINT=0 0 0 WEIGHT=1 ENERGY=1.4

PRINT
SOURCE 1
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty {root}")
    root.mkdir(parents=True, exist_ok=True)

    manifest = {"population": 128, "rng_type": 2, "seed": 1, "stride": 1_000_000, "cases": []}
    for name, ratio in CASES:
        directory = root / name
        directory.mkdir()
        content = INPUT.format(cell_density=BASE_DENSITY * ratio, base_density=BASE_DENSITY)
        input_path = directory / "inp"
        input_path.write_text(content, encoding="ascii")
        manifest["cases"].append(
            {
                "name": name,
                "density_ratio": ratio,
                "input": str(input_path.relative_to(root)),
                "input_sha256": hashlib.sha256(content.encode("ascii")).hexdigest(),
            }
        )

    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"generated_cases={len(CASES)}")
    print(f"manifest={manifest_path}")
    print(f"manifest_sha256={hashlib.sha256(manifest_path.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
